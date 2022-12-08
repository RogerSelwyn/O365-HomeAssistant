"""O365 mail sensors."""
import datetime

from homeassistant.helpers.entity import Entity

from ..const import (
    ATTR_ATTRIBUTES,
    CONF_BODY_CONTAINS,
    CONF_DOWNLOAD_ATTACHMENTS,
    CONF_HAS_ATTACHMENT,
    CONF_IMPORTANCE,
    CONF_IS_UNREAD,
    CONF_MAIL_FROM,
    CONF_MAX_ITEMS,
    CONF_SUBJECT_CONTAINS,
    CONF_SUBJECT_IS,
    SENSOR_MAIL,
)
from .sensorentity import O365Sensor


class O365MailSensor(O365Sensor):
    """O365 generic Mail Sensor class."""

    def __init__(self, coordinator, conf, mail_folder, name, entity_id):
        """Initialise the O365 Sensor."""
        super().__init__(coordinator, name, entity_id, SENSOR_MAIL)
        self.mail_folder = mail_folder
        self.download_attachments = conf.get(CONF_DOWNLOAD_ATTACHMENTS, True)
        self.max_items = conf.get(CONF_MAX_ITEMS, 5)
        self.query = None

    @property
    def icon(self):
        """Entity icon."""
        return "mdi:microsoft-outlook"

    @property
    def extra_state_attributes(self):
        """Device state attributes."""
        return self.coordinator.data[self.entity_id][ATTR_ATTRIBUTES]


class O365QuerySensor(O365MailSensor, Entity):
    """O365 Query sensor processing."""

    def __init__(self, coordinator, conf, mail_folder, name, entity_id):
        """Initialise the O365 Query."""
        super().__init__(coordinator, conf, mail_folder, name, entity_id)

        self.query = self.mail_folder.new_query()
        self.query.order_by("receivedDateTime", ascending=False)

        self._build_query(conf)

    def _build_query(self, conf):
        body_contains = conf.get(CONF_BODY_CONTAINS)
        subject_contains = conf.get(CONF_SUBJECT_CONTAINS)
        subject_is = conf.get(CONF_SUBJECT_IS)
        has_attachment = conf.get(CONF_HAS_ATTACHMENT)
        importance = conf.get(CONF_IMPORTANCE)
        email_from = conf.get(CONF_MAIL_FROM)
        is_unread = conf.get(CONF_IS_UNREAD)
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

    def __init__(self, coordinator, conf, mail_folder, name, entity_id):
        """Initialise the O365 Email sensor."""
        super().__init__(coordinator, conf, mail_folder, name, entity_id)

        is_unread = conf.get(CONF_IS_UNREAD)

        self.query = None
        if is_unread is not None:
            self.query = self.mail_folder.new_query()
            self.query.chain("and").on_attribute("IsRead").equals(not is_unread)
