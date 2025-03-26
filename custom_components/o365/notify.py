"""Notification processing."""

import logging
import os
import zipfile
from pathlib import Path

from homeassistant.components.notify import (
    ATTR_DATA,
    ATTR_TARGET,
    ATTR_TITLE,
    BaseNotificationService,
)

from .const import (
    ATTR_ATTACHMENTS,
    ATTR_IMPORTANCE,
    ATTR_MESSAGE_IS_HTML,
    ATTR_PHOTOS,
    ATTR_SENDER,
    ATTR_ZIP_ATTACHMENTS,
    ATTR_ZIP_NAME,
    CONF_ACCOUNT,
    CONF_ACCOUNT_NAME,
    CONF_IS_AUTHENTICATED,
    CONF_PERMISSIONS,
    DOMAIN,
    LEGACY_ACCOUNT_NAME,
    PERM_MAIL_SEND,
)
from .schema import NOTIFY_SERVICE_BASE_SCHEMA

_LOGGER = logging.getLogger(__name__)


async def async_get_service(hass, config, discovery_info=None):  # pylint: disable=unused-argument
    """Get the service."""
    if discovery_info is None:
        return
    account_name = discovery_info[CONF_ACCOUNT_NAME]
    conf = hass.data[DOMAIN][account_name]
    account = conf[CONF_ACCOUNT]
    is_authenticated = conf[CONF_IS_AUTHENTICATED]
    if is_authenticated and conf[CONF_PERMISSIONS].validate_authorization(
        PERM_MAIL_SEND
    ):
        _LOGGER.warning(
            "The O365 Notify service is now deprecated - please migrate to MS365 Mail "
            + "- for more details on how to do this see "
            + "https://rogerselwyn.github.io/O365-HomeAssistant/migration.html"
        )
        return O365EmailService(account, hass, conf)

    return


class O365EmailService(BaseNotificationService):
    """Implement the notification service for O365."""

    def __init__(self, account, hass, config):
        """Initialize the service."""
        self.account = account
        self._config = config
        self._cleanup_files = []
        self._hass = hass
        self._account_name = config.get(CONF_ACCOUNT_NAME, None)
        if self._account_name:
            if self._account_name == LEGACY_ACCOUNT_NAME:
                self._account_name = ""
            else:
                self._account_name = f"_{self._account_name}"

    @property
    def targets(self):
        """Targets property."""
        return {f"_email{self._account_name}": ""}

    def send_message(self, message="", **kwargs):
        """Send a message to a user."""
        _LOGGER.warning("Non async send_message unsupported")

    async def async_send_message(self, message="", **kwargs):
        """Send an async message to a user."""
        if not self._config[CONF_PERMISSIONS].validate_authorization(PERM_MAIL_SEND):
            _LOGGER.error(
                "Not authorised to send mail - requires permission: %s", PERM_MAIL_SEND
            )
            return

        self._cleanup_files = []
        data = kwargs.get(ATTR_DATA)
        if data is None:
            kwargs.pop(ATTR_DATA)

        NOTIFY_SERVICE_BASE_SCHEMA(kwargs)

        title = kwargs.get(ATTR_TITLE, "Notification from Home Assistant")

        if data and data.get(ATTR_TARGET, None):
            target = data.get(ATTR_TARGET)
        else:
            resp = await self.hass.async_add_executor_job(self.account.get_current_user)
            target = resp.mail

        new_message = await self.hass.async_add_executor_job(self.account.new_message)
        message = self._build_message(data, message, new_message.attachments)
        self._build_attachments(data, new_message.attachments)
        new_message.to.add(target)
        if data:
            if data.get(ATTR_SENDER, None):
                new_message.sender = data.get(ATTR_SENDER)
            if data.get(ATTR_IMPORTANCE, None):
                new_message.importance = data.get(ATTR_IMPORTANCE)
        new_message.subject = title
        new_message.body = message
        await self.hass.async_add_executor_job(new_message.send)

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
        for i, photo in enumerate(photos, start=1):
            if photo.startswith("http"):
                photos_content += f'<br><img src="{photo}">'
            else:
                photo = self._get_ha_filepath(photo)
                new_message_attachments.add(photo)
                att = new_message_attachments[-1]
                att.is_inline = True
                att.content_id = str(i)
                photos_content += f'<br><img src="cid:{att.content_id}">'

        return photos_content

    def _build_attachments(self, data, new_message_attachments):
        attachments = []
        zip_attachments = False
        zip_name = None
        if data:
            attachments = data.get(ATTR_ATTACHMENTS, [])
            zip_attachments = data.get(ATTR_ZIP_ATTACHMENTS, False)
            zip_name = data.get(ATTR_ZIP_NAME, None)

        attachments = [self._get_ha_filepath(x) for x in attachments]
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

    def _get_ha_filepath(self, filepath):
        """Get the file path."""
        _filepath = Path(filepath)
        if _filepath.parts[0] == "/" and _filepath.parts[1] == "config":
            _filepath = os.path.join(self._hass.config.config_dir, *_filepath.parts[2:])

        if not os.path.isfile(_filepath):
            if not os.path.isfile(filepath):
                raise ValueError(f"Could not access file {filepath} at {_filepath}")
            return filepath
        return _filepath


def zip_files(filespaths, zip_name):
    """Zip the files."""
    if not zip_name:
        zip_name = "archive.zip"
    if Path(zip_name).suffix != ".zip":
        zip_name += ".zip"

    with zipfile.ZipFile(zip_name, mode="w") as zip_file:
        for file_path in filespaths:
            zip_file.write(file_path, os.path.basename(file_path))
    return zip_name
