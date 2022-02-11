"""Sensor processing."""
import datetime as dt
import logging
from operator import itemgetter

from homeassistant.helpers.entity import Entity

from .const import (
    CONF_EMAIL_SENSORS,
    CONF_HAS_ATTACHMENT,
    CONF_IMPORTANCE,
    CONF_IS_UNREAD,
    CONF_MAIL_FOLDER,
    CONF_MAIL_FROM,
    CONF_MAX_ITEMS,
    CONF_NAME,
    CONF_QUERY_SENSORS,
    CONF_SUBJECT_CONTAINS,
    CONF_SUBJECT_IS,
    DOMAIN,
)
from .utils import get_email_attributes

_LOGGER = logging.getLogger(__name__)


def setup_platform(
    hass, config, add_devices, discovery_info=None
):    # pylint: disable=unused-argument
    """O365 platform definition."""
    if discovery_info is None:
        return

    account = hass.data[DOMAIN]["account"]
    is_authenticated = account.is_authenticated
    if not is_authenticated:
        return False

    unread_sensors = hass.data[DOMAIN].get(CONF_EMAIL_SENSORS, [])
    for conf in unread_sensors:
        if mail_folder := _get_mail_folder(account, conf, CONF_EMAIL_SENSORS):
            sensor = O365InboxSensor(conf, mail_folder)
            add_devices([sensor], True)

    query_sensors = hass.data[DOMAIN].get(CONF_QUERY_SENSORS, [])
    for conf in query_sensors:
        if mail_folder := _get_mail_folder(account, conf, CONF_QUERY_SENSORS):
            sensor = O365QuerySensor(conf, mail_folder)
            add_devices([sensor], True)


def _get_mail_folder(account, conf, sensor_type):
    """Get the configured folder."""
    mailbox = account.mailbox()
    mail_folder = None
    if mail_folder_conf := conf.get(CONF_MAIL_FOLDER):
        for i, folder in enumerate(mail_folder_conf.split("/")):
            _LOGGER.debug(
                "Processing folder - %s - from %s config entry - %s ",
                folder,
                sensor_type,
                mail_folder_conf,
            )
            if i == 0:
                mail_folder = mailbox.get_folder(folder_name=folder)
            else:
                mail_folder = mail_folder.get_folder(folder_name=folder)

            if not mail_folder:
                _LOGGER.error(
                    "Folder - %s - not found from %s config entry - %s - entity not created",
                    folder,
                    sensor_type,
                    mail_folder_conf,
                )
                return None

            # _LOGGER.debug(f"Got folder id - {mail_folder.folder_id}")

    else:
        mail_folder = mailbox.inbox_folder()

    return mail_folder


class O365Sensor:
    """O365 generic Sensor class."""

    def __init__(self, conf, mail_folder):
        """Initialise the O365 Sensor."""
        self.mail_folder = mail_folder
        self._name = conf.get(CONF_NAME)
        self.max_items = conf.get(CONF_MAX_ITEMS, 5)
        self._state = 0
        self._attributes = {}
        self.query = None

    @property
    def name(self):
        """Name property."""
        return self._name

    @property
    def state(self):
        """State property."""
        return self._state

    @property
    def extra_state_attributes(self):
        """Device state attributes."""
        return self._attributes

    def update(self):
        """Update code."""
        mails = list(
            self.mail_folder.get_messages(
                limit=self.max_items, query=self.query, download_attachments=True
            )
        )
        attrs = [get_email_attributes(x) for x in mails]
        attrs.sort(key=itemgetter("received"), reverse=True)
        self._state = len(mails)
        # self._attributes = {"data": attrs, "data_str_repr": json.dumps(attrs)}
        self._attributes = {"data": attrs}


class O365QuerySensor(O365Sensor, Entity):
    """O365 Query sensor processing."""

    def __init__(self, conf, mail_folder):
        """Initialise the O365 Query."""
        super().__init__(conf, mail_folder)

        self.subject_contains = conf.get(CONF_SUBJECT_CONTAINS)
        self.subject_is = conf.get(CONF_SUBJECT_IS)
        self.has_attachment = conf.get(CONF_HAS_ATTACHMENT)
        self.importance = conf.get(CONF_IMPORTANCE)
        self.email_from = conf.get(CONF_MAIL_FROM)
        self.is_unread = conf.get(CONF_IS_UNREAD)
        self.query = self.mail_folder.new_query()
        self.query.order_by("receivedDateTime", ascending=False)

        if (
            self.subject_contains is not None
            or self.subject_is is not None
            or self.has_attachment is not None
            or self.importance is not None
            or self.email_from is not None
            or self.is_unread is not None
        ):
            self._add_to_query("ge", "receivedDateTime", dt.datetime(1900, 5, 1))
        self._add_to_query("contains", "subject", self.subject_contains)
        self._add_to_query("equals", "subject", self.subject_is)
        self._add_to_query("equals", "hasAttachments", self.has_attachment)
        self._add_to_query("equals", "from", self.email_from)
        self._add_to_query("equals", "IsRead", not self.is_unread, self.is_unread)
        self._add_to_query("equals", "importance", self.importance)

        # _LOGGER.debug(self.query)

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


class O365InboxSensor(O365Sensor, Entity):
    """O365 Inboox processing."""

    def __init__(self, conf, mail_folder):
        """Initialise the O365 Inbox."""
        super().__init__(conf, mail_folder)

        self.is_unread = conf.get(CONF_IS_UNREAD)

        self.query = None
        if self.is_unread is not None:
            self.query = self.mail_folder.new_query()
            self.query.chain("and").on_attribute("IsRead").equals(not self.is_unread)
