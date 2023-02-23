"""O365 mail sensors."""
import datetime

import voluptuous as vol
from homeassistant.components.sensor import SensorEntity

from O365.mailbox import ExternalAudience  # pylint: disable=no-name-in-module

from ..const import (
    ATTR_ATTRIBUTES,
    ATTR_AUTOREPLIESSETTINGS,
    ATTR_END,
    ATTR_EXTERNAL_AUDIENCE,
    ATTR_EXTERNALREPLY,
    ATTR_INTERNALREPLY,
    ATTR_START,
    CONF_ACCOUNT,
    CONF_BODY_CONTAINS,
    CONF_CONFIG_TYPE,
    CONF_DOWNLOAD_ATTACHMENTS,
    CONF_HAS_ATTACHMENT,
    CONF_HTML_BODY,
    CONF_IMPORTANCE,
    CONF_IS_UNREAD,
    CONF_MAIL_FROM,
    CONF_MAX_ITEMS,
    CONF_SUBJECT_CONTAINS,
    CONF_SUBJECT_IS,
    DATETIME_FORMAT,
    PERM_MAILBOX_SETTINGS,
    PERM_MINIMUM_MAILBOX_SETTINGS,
    SENSOR_AUTO_REPLY,
    SENSOR_MAIL,
)
from ..utils import (
    build_token_filename,
    clean_html,
    get_permissions,
    validate_minimum_permission,
)
from .sensorentity import O365Sensor


class O365MailSensor(O365Sensor):
    """O365 generic Mail Sensor class."""

    def __init__(
        self, coordinator, config, sensor_conf, mail_folder, name, entity_id, unique_id
    ):
        """Initialise the O365 Sensor."""
        super().__init__(coordinator, name, entity_id, SENSOR_MAIL, unique_id)
        self.mail_folder = mail_folder
        self.download_attachments = sensor_conf.get(CONF_DOWNLOAD_ATTACHMENTS)
        self.html_body = sensor_conf.get(CONF_HTML_BODY)
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
        return self.coordinator.data[self.entity_key][ATTR_ATTRIBUTES]


class O365QuerySensor(O365MailSensor, SensorEntity):
    """O365 Query sensor processing."""

    def __init__(
        self, coordinator, config, sensor_conf, mail_folder, name, entity_id, unique_id
    ):
        """Initialise the O365 Query."""
        super().__init__(
            coordinator, config, sensor_conf, mail_folder, name, entity_id, unique_id
        )

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


class O365EmailSensor(O365MailSensor, SensorEntity):
    """O365 Email sensor processing."""

    def __init__(
        self, coordinator, config, sensor_conf, mail_folder, name, entity_id, unique_id
    ):
        """Initialise the O365 Email sensor."""
        super().__init__(
            coordinator, config, sensor_conf, mail_folder, name, entity_id, unique_id
        )

        is_unread = sensor_conf.get(CONF_IS_UNREAD)

        self.query = None
        if is_unread is not None:
            self.query = self.mail_folder.new_query()
            self.query.chain("and").on_attribute("IsRead").equals(not is_unread)


class O365AutoReplySensor(O365Sensor, SensorEntity):
    """O365 Auto Reply sensor processing."""

    def __init__(self, coordinator, name, entity_id, config, unqique_id):
        """Initialise the Auto reply Sensor."""
        super().__init__(coordinator, name, entity_id, SENSOR_AUTO_REPLY, unqique_id)
        self._config = config
        account = self._config[CONF_ACCOUNT]
        self.mailbox = account.mailbox()

    @property
    def icon(self):
        """Entity icon."""
        return "mdi:reply-all"

    @property
    def extra_state_attributes(self):
        """Return entity specific state attributes."""
        ars = self.coordinator.data[self.entity_key][ATTR_AUTOREPLIESSETTINGS]
        return {
            ATTR_INTERNALREPLY: clean_html(ars.internal_reply_message),
            ATTR_EXTERNALREPLY: clean_html(ars.external_reply_message),
            ATTR_EXTERNAL_AUDIENCE: ars.external_audience.value,
            ATTR_START: ars.scheduled_startdatetime.strftime(DATETIME_FORMAT),
            ATTR_END: ars.scheduled_enddatetime.strftime(DATETIME_FORMAT),
        }

    def auto_reply_enable(
        self,
        external_reply,
        internal_reply,
        start=None,
        end=None,
        external_audience=ExternalAudience.ALL,
    ):
        """Enable out of office autoreply."""
        if not self._validate_permissions():
            return

        self.mailbox.set_automatic_reply(
            internal_reply, external_reply, start, end, external_audience
        )

    def auto_reply_disable(self):
        """Disable out of office autoreply."""
        if not self._validate_permissions():
            return

        self.mailbox.set_disable_reply()

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
