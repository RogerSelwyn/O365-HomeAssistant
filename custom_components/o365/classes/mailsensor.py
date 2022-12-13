"""O365 mail sensors."""
import datetime

import voluptuous as vol
from homeassistant.helpers.entity import Entity
from homeassistant.util.dt import as_utc

from ..const import (
    ATTR_ATTRIBUTES,
    CONF_ACCOUNT,
    CONF_BODY_CONTAINS,
    CONF_CONFIG_TYPE,
    CONF_DOWNLOAD_ATTACHMENTS,
    CONF_HAS_ATTACHMENT,
    CONF_IMPORTANCE,
    CONF_IS_UNREAD,
    CONF_MAIL_FROM,
    CONF_MAX_ITEMS,
    CONF_SUBJECT_CONTAINS,
    CONF_SUBJECT_IS,
    PERM_MAILBOX_SETTINGS,
    PERM_MINIMUM_MAILBOX_SETTINGS,
    SENSOR_MAIL,
)
from ..utils import build_token_filename, get_permissions, validate_minimum_permission
from .sensorentity import O365Sensor


class O365MailSensor(O365Sensor):
    """O365 generic Mail Sensor class."""

    def __init__(self, coordinator, config, sensor_conf, mail_folder, name, entity_id):
        """Initialise the O365 Sensor."""
        super().__init__(coordinator, name, entity_id, SENSOR_MAIL)
        self.mail_folder = mail_folder
        self.download_attachments = sensor_conf.get(CONF_DOWNLOAD_ATTACHMENTS, True)
        self.max_items = sensor_conf.get(CONF_MAX_ITEMS, 5)
        self.query = None
        self._config = config

    @property
    def icon(self):
        """Entity icon."""
        return "mdi:microsoft-outlook"

    @property
    def extra_state_attributes(self):
        """Device state attributes."""
        return self.coordinator.data[self.entity_id][ATTR_ATTRIBUTES]

    def auto_reply_enable(
        self,
        external_reply,
        internal_reply,
        start=None,
        end=None,
        external_audience=None,
    ):
        """Enable out of office autoreply."""
        if not self._validate_permissions():
            return

        account = self._config[CONF_ACCOUNT]
        mailbox = account.mailbox()
        mailbox.set_automatic_reply(
            internal_reply, external_reply, start, end, external_audience
        )

    def auto_reply_disable(self):
        """Disable out of office autoreply."""
        if not self._validate_permissions():
            return

        account = self._config[CONF_ACCOUNT]
        mailbox = account.mailbox()
        mailbox.set_disable_reply()

    def _validate_permissions(self):
        permissions = get_permissions(
            self.hass,
            filename=build_token_filename(
                self._config, self._config.get(CONF_CONFIG_TYPE)
            ),
        )
        if not validate_minimum_permission(PERM_MINIMUM_MAILBOX_SETTINGS, permissions):
            raise vol.Invalid(
                "Not authorisied to update auto reply - requires permission: "
                + f"{PERM_MAILBOX_SETTINGS}"
            )

        return True


class O365QuerySensor(O365MailSensor, Entity):
    """O365 Query sensor processing."""

    def __init__(self, coordinator, config, sensor_conf, mail_folder, name, entity_id):
        """Initialise the O365 Query."""
        super().__init__(coordinator, config, sensor_conf, mail_folder, name, entity_id)

        self.query = self.mail_folder.new_query()
        self.query.order_by("receivedDateTime", ascending=False)

        self._build_query(sensor_conf)

    def _build_query(self, sensor_conf):
        body_contains = sensor_conf.get(CONF_BODY_CONTAINS)
        subject_contains = sensor_conf.get(CONF_SUBJECT_CONTAINS)
        subject_is = sensor_conf.get(CONF_SUBJECT_IS)
        has_attachment = sensor_conf.get(CONF_HAS_ATTACHMENT)
        importance = sensor_conf.get(CONF_IMPORTANCE)
        email_from = sensor_conf.get(CONF_MAIL_FROM)
        is_unread = sensor_conf.get(CONF_IS_UNREAD)
        if (
            body_contains is not None
            or subject_contains is not None
            or subject_is is not None
            or has_attachment is not None
            or importance is not None
            or email_from is not None
            or is_unread is not None
        ):
            self._add_to_query("ge", "receivedDateTime", datetime.datetime(1900, 5, 1))
        self._add_to_query("contains", "body", body_contains)
        self._add_to_query("contains", "subject", subject_contains)
        self._add_to_query("equals", "subject", subject_is)
        self._add_to_query("equals", "hasAttachments", has_attachment)
        self._add_to_query("equals", "from", email_from)
        self._add_to_query("equals", "IsRead", not is_unread, is_unread)
        self._add_to_query("equals", "importance", importance)

    def _add_to_query(self, qtype, attribute_name, attribute_value, check_value=True):
        if attribute_value is None or check_value is None:
            return

        if qtype == "ge":
            self.query.chain("and").on_attribute(attribute_name).greater_equal(
                attribute_value
            )
        if qtype == "contains":
            self.query.chain("and").on_attribute(attribute_name).contains(
                attribute_value
            )
        if qtype == "equals":
            self.query.chain("and").on_attribute(attribute_name).equals(attribute_value)


class O365EmailSensor(O365MailSensor, Entity):
    """O365 Email sensor processing."""

    def __init__(self, coordinator, config, sensor_conf, mail_folder, name, entity_id):
        """Initialise the O365 Email sensor."""
        super().__init__(coordinator, config, sensor_conf, mail_folder, name, entity_id)

        is_unread = sensor_conf.get(CONF_IS_UNREAD)

        self.query = None
        if is_unread is not None:
            self.query = self.mail_folder.new_query()
            self.query.chain("and").on_attribute("IsRead").equals(not is_unread)
