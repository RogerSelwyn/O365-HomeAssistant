"""Ntoification processing."""
import logging
import os

from homeassistant.components.notify import BaseNotificationService

from .const import (
    ATTR_ATTACHMENTS,
    ATTR_DATA,
    ATTR_MESSAGE_IS_HTML,
    ATTR_PHOTOS,
    ATTR_TARGET,
    ATTR_TITLE,
    ATTR_ZIP_ATTACHMENTS,
    ATTR_ZIP_NAME,
    DOMAIN,
    NOTIFY_BASE_SCHEMA,
)
from .utils import get_ha_filepath, zip_files

_LOGGER = logging.getLogger(__name__)


async def async_get_service(hass, config, discovery_info=None):
    """Get the service."""
    if discovery_info is None:
        return
    account = hass.data[DOMAIN]["account"]
    is_authenticated = account.is_authenticated
    if not is_authenticated:
        return
    return O365EmailService(account)


class O365EmailService(BaseNotificationService):
    """Implement the notification service for O365."""

    def __init__(self, account):
        """Initialize the service."""
        self.account = account

    @property
    def targets(self):
        """Targets property."""
        return {"_email": ""}

    def send_message(self, message="", **kwargs):
        """Send a message to a user."""
        cleanup_files = []
        account = self.account
        NOTIFY_BASE_SCHEMA(kwargs)
        title = kwargs.get(ATTR_TITLE, "Notification from Home Assistant")

        data = kwargs.get(ATTR_DATA)
        if data and data.get(ATTR_TARGET, None):
            target = data.get(ATTR_TARGET)
        else:
            target = account.get_current_user().mail

        is_html = False
        photos = []
        attachments = []
        zip_attachments = False
        zip_name = None
        if data:
            is_html = data.get(ATTR_MESSAGE_IS_HTML, False)
            photos = data.get(ATTR_PHOTOS, [])
            attachments = data.get(ATTR_ATTACHMENTS, [])
            zip_attachments = data.get(ATTR_ZIP_ATTACHMENTS, False)
            zip_name = data.get(ATTR_ZIP_NAME, None)

        if isinstance(photos, str):
            photos = [photos]

        m = account.new_message()
        if is_html or photos:
            message = f"""
                <html>
                    <body>
                        {message}"""
            for photo in photos:
                if photo.startswith("http"):
                    message += f'<br><img src="{photo}">'
                else:
                    photo = get_ha_filepath(photo)
                    m.attachments.add(photo)
                    att = m.attachments[-1]
                    att.is_inline = True
                    att.content_id = "1"
                    message += f'<br><img src="cid:{1}">'
            message += "</body></html>"

        attachments = [get_ha_filepath(x) for x in attachments]
        if attachments and zip_attachments:
            z_file = zip_files(attachments, zip_name)
            m.attachments.add(z_file)
            cleanup_files.append(z_file)

        else:
            for attachment in attachments:
                m.attachments.add(attachment)

        m.to.add(target)
        m.subject = title
        m.body = message
        m.send()
        for x in cleanup_files:
            os.remove(x)
