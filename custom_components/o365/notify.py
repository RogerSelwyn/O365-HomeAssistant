"""Notification processing."""
import logging
import os

from homeassistant.components.notify import BaseNotificationService

from .const import (ATTR_ATTACHMENTS, ATTR_DATA, ATTR_MESSAGE_IS_HTML,
                    ATTR_PHOTOS, ATTR_TARGET, ATTR_TITLE, ATTR_ZIP_ATTACHMENTS,
                    ATTR_ZIP_NAME, CONF_ACCOUNT, CONF_ACCOUNT_NAME, DOMAIN,
                    NOTIFY_BASE_SCHEMA, PERM_MAIL_SEND, PERM_MINIMUM_SEND)
from .utils import (build_token_filename, get_ha_filepath, get_permissions,
                    validate_minimum_permission, zip_files)

_LOGGER = logging.getLogger(__name__)


async def async_get_service(
    hass, config, discovery_info=None
):  # pylint: disable=unused-argument
    """Get the service."""
    if discovery_info is None:
        return
    account_name = discovery_info[CONF_ACCOUNT_NAME]
    conf = hass.data[DOMAIN][account_name]
    account = conf[CONF_ACCOUNT]
    is_authenticated = account.is_authenticated
    if not is_authenticated:
        return
    return O365EmailService(account, hass, conf)


class O365EmailService(BaseNotificationService):
    """Implement the notification service for O365."""

    def __init__(self, account, hass, config):
        """Initialize the service."""
        self.account = account
        self._permissions = get_permissions(hass, filename=build_token_filename(config))
        self._cleanup_files = []
        self._hass = hass
        if account_name := config.get(CONF_ACCOUNT_NAME, None):
            account_name = f"_{account_name}"
        self._account_name = account_name

    @property
    def targets(self):
        """Targets property."""
        return {f"_email{self._account_name}": ""}

    def send_message(self, message="", **kwargs):
        """Send a message to a user."""
        if not validate_minimum_permission(PERM_MINIMUM_SEND, self._permissions):
            _LOGGER.error(
                "Not authorisied to send mail - requires permission: %s", PERM_MAIL_SEND
            )
            return

        self._cleanup_files = []
        data = kwargs.get(ATTR_DATA)
        if data is None:
            kwargs.pop(ATTR_DATA)

        NOTIFY_BASE_SCHEMA(kwargs)

        title = kwargs.get(ATTR_TITLE, "Notification from Home Assistant")

        if data and data.get(ATTR_TARGET, None):
            target = data.get(ATTR_TARGET)
        else:
            target = self.account.get_current_user().mail

        new_message = self.account.new_message()
        message = self._build_message(data, message, new_message.attachments)
        self._build_attachments(data, new_message.attachments)
        new_message.to.add(target)
        new_message.subject = title
        new_message.body = message
        new_message.send()

        self._cleanup()

    def _build_message(self, data, message, new_message_attachments):
        is_html = False
        photos = []
        if data:
            is_html = data.get(ATTR_MESSAGE_IS_HTML, False)
            photos = data.get(ATTR_PHOTOS, [])
        if is_html or photos:
            message = f"""
                <html>
                    <body>
                        {message}"""
            message += self._build_photo_content(photos, new_message_attachments)
            message += "</body></html>"

        return message

    def _build_photo_content(self, photos, new_message_attachments):
        if isinstance(photos, str):
            photos = [photos]

        photos_content = ""
        for photo in photos:
            if photo.startswith("http"):
                photos_content += f'<br><img src="{photo}">'
            else:
                photo = get_ha_filepath(self._hass, photo)
                new_message_attachments.add(photo)
                att = new_message_attachments[-1]
                att.is_inline = True
                att.content_id = "1"
                photos_content += f'<br><img src="cid:{photo}">'

        return photos_content

    def _build_attachments(self, data, new_message_attachments):

        attachments = []
        zip_attachments = False
        zip_name = None
        if data:
            attachments = data.get(ATTR_ATTACHMENTS, [])
            zip_attachments = data.get(ATTR_ZIP_ATTACHMENTS, False)
            zip_name = data.get(ATTR_ZIP_NAME, None)

        attachments = [get_ha_filepath(self._hass, x) for x in attachments]
        if attachments and zip_attachments:
            z_file = zip_files(attachments, zip_name)
            new_message_attachments.add(z_file)
            self._cleanup_files.append(z_file)

        else:
            for attachment in attachments:
                new_message_attachments.add(attachment)

    def _cleanup(self):
        for filename in self._cleanup_files:
            os.remove(filename)
