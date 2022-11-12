"""Sensor processing."""
import datetime as dt
import functools as ft
import logging
from operator import itemgetter

from homeassistant.const import CONF_NAME
from homeassistant.helpers.entity import Entity

from .const import (
    ATTR_CHAT_ID,
    ATTR_CONTENT,
    ATTR_FROM_DISPLAY_NAME,
    ATTR_IMPORTANCE,
    ATTR_SUBJECT,
    ATTR_SUMMARY,
    CONF_ACCOUNT,
    CONF_ACCOUNT_NAME,
    CONF_BODY_CONTAINS,
    CONF_CHAT_SENSORS,
    CONF_DOWNLOAD_ATTACHMENTS,
    CONF_EMAIL_SENSORS,
    CONF_HAS_ATTACHMENT,
    CONF_IMPORTANCE,
    CONF_IS_UNREAD,
    CONF_MAIL_FOLDER,
    CONF_MAIL_FROM,
    CONF_MAX_ITEMS,
    CONF_QUERY_SENSORS,
    CONF_STATUS_SENSORS,
    CONF_SUBJECT_CONTAINS,
    CONF_SUBJECT_IS,
    DOMAIN,
)
from .utils import get_email_attributes

_LOGGER = logging.getLogger(__name__)


async def async_setup_platform(
    hass, config, add_entities, discovery_info=None
):  # pylint: disable=unused-argument
    """O365 platform definition."""
    if discovery_info is None:
        return None

    account_name = discovery_info[CONF_ACCOUNT_NAME]
    conf = hass.data[DOMAIN][account_name]
    account = conf[CONF_ACCOUNT]

    is_authenticated = account.is_authenticated
    if not is_authenticated:
        return False

    await _async_email_sensors(hass, account, add_entities, conf)
    await _async_query_sensors(hass, account, add_entities, conf)
    _status_sensors(account, add_entities, conf)
    _chat_sensors(account, add_entities, conf)

    return True


async def _async_email_sensors(hass, account, add_entities, conf):
    email_sensors = conf.get(CONF_EMAIL_SENSORS, [])
    _LOGGER.debug("Email sensor setup: %s ", conf[CONF_ACCOUNT_NAME])
    for sensor_conf in email_sensors:
        _LOGGER.debug(
            "Email sensor setup: %s, %s",
            conf[CONF_ACCOUNT_NAME],
            sensor_conf[CONF_NAME],
        )
        if mail_folder := await hass.async_add_executor_job(
            _get_mail_folder, account, sensor_conf, CONF_EMAIL_SENSORS
        ):
            inboxsensor = O365InboxSensor(sensor_conf, mail_folder)
            _LOGGER.debug(
                "Email sensor added: %s, %s",
                conf[CONF_ACCOUNT_NAME],
                sensor_conf[CONF_NAME],
            )
            add_entities([inboxsensor], True)


async def _async_query_sensors(hass, account, add_entities, conf):
    query_sensors = conf.get(CONF_QUERY_SENSORS, [])
    for sensor_conf in query_sensors:
        if mail_folder := await hass.async_add_executor_job(
            _get_mail_folder, account, sensor_conf, CONF_QUERY_SENSORS
        ):
            querysensor = O365QuerySensor(sensor_conf, mail_folder)
            add_entities([querysensor], True)


def _status_sensors(account, add_entities, conf):
    status_sensors = conf.get(CONF_STATUS_SENSORS, [])
    for sensor_conf in status_sensors:
        teams_status_sensor = O365TeamsStatusSensor(account, sensor_conf)
        add_entities([teams_status_sensor], True)


def _chat_sensors(account, add_entities, conf):
    chat_sensors = conf.get(CONF_CHAT_SENSORS, [])
    for sensor_conf in chat_sensors:
        teams_chat_sensor = O365TeamsChatSensor(account, sensor_conf)
        add_entities([teams_chat_sensor], True)


def _get_mail_folder(account, sensor_conf, sensor_type):
    """Get the configured folder."""
    mailbox = account.mailbox()
    _LOGGER.debug("Get mail folder: %s", sensor_conf.get(CONF_NAME))
    if mail_folder_conf := sensor_conf.get(CONF_MAIL_FOLDER):
        return _get_configured_mail_folder(mail_folder_conf, mailbox, sensor_type)

    return mailbox.inbox_folder()


def _get_configured_mail_folder(mail_folder_conf, mailbox, sensor_type):
    mail_folder = None
    for i, folder in enumerate(mail_folder_conf.split("/")):
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

    return mail_folder


class O365MailSensor:
    """O365 generic Sensor class."""

    def __init__(self, conf, mail_folder):
        """Initialise the O365 Sensor."""
        self._mail_folder = mail_folder
        self._name = conf.get(CONF_NAME)
        self._download_attachments = conf.get(CONF_DOWNLOAD_ATTACHMENTS, True)
        self._max_items = conf.get(CONF_MAX_ITEMS, 5)
        self._state = 0
        self._attributes = {}
        self._query = None

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

    async def async_update(self):
        """Update code."""
        data = await self.hass.async_add_executor_job(  # pylint: disable=no-member
            ft.partial(
                self._mail_folder.get_messages,
                limit=self._max_items,
                query=self._query,
                download_attachments=self._download_attachments,
            )
        )
        attrs = [get_email_attributes(x, self._download_attachments) for x in data]
        attrs.sort(key=itemgetter("received"), reverse=True)
        self._state = len(attrs)
        self._attributes = {"data": attrs}


class O365QuerySensor(O365MailSensor, Entity):
    """O365 Query sensor processing."""

    def __init__(self, conf, mail_folder):
        """Initialise the O365 Query."""
        super().__init__(conf, mail_folder)

        self._body_contains = conf.get(CONF_BODY_CONTAINS)
        self._subject_contains = conf.get(CONF_SUBJECT_CONTAINS)
        self._subject_is = conf.get(CONF_SUBJECT_IS)
        self._has_attachment = conf.get(CONF_HAS_ATTACHMENT)
        self._importance = conf.get(CONF_IMPORTANCE)
        self._email_from = conf.get(CONF_MAIL_FROM)
        self._is_unread = conf.get(CONF_IS_UNREAD)
        self._query = self._mail_folder.new_query()
        self._query.order_by("receivedDateTime", ascending=False)

        if (
            self._body_contains is not None
            or self._subject_contains is not None
            or self._subject_is is not None
            or self._has_attachment is not None
            or self._importance is not None
            or self._email_from is not None
            or self._is_unread is not None
        ):
            self._add_to_query("ge", "receivedDateTime", dt.datetime(1900, 5, 1))
        self._add_to_query("contains", "body", self._body_contains)
        self._add_to_query("contains", "subject", self._subject_contains)
        self._add_to_query("equals", "subject", self._subject_is)
        self._add_to_query("equals", "hasAttachments", self._has_attachment)
        self._add_to_query("equals", "from", self._email_from)
        self._add_to_query("equals", "IsRead", not self._is_unread, self._is_unread)
        self._add_to_query("equals", "importance", self._importance)

    def _add_to_query(self, qtype, attribute_name, attribute_value, check_value=True):
        if attribute_value is None or check_value is None:
            return

        if qtype == "ge":
            self._query.chain("and").on_attribute(attribute_name).greater_equal(
                attribute_value
            )
        if qtype == "contains":
            self._query.chain("and").on_attribute(attribute_name).contains(
                attribute_value
            )
        if qtype == "equals":
            self._query.chain("and").on_attribute(attribute_name).equals(
                attribute_value
            )


class O365InboxSensor(O365MailSensor, Entity):
    """O365 Inbox processing."""

    def __init__(self, conf, mail_folder):
        """Initialise the O365 Inbox."""
        super().__init__(conf, mail_folder)

        is_unread = conf.get(CONF_IS_UNREAD)

        self._query = None
        if is_unread is not None:
            self._query = self._mail_folder.new_query()
            self._query.chain("and").on_attribute("IsRead").equals(not is_unread)


class O365TeamsStatusSensor(Entity):
    """O365 Teams sensor processing."""

    def __init__(self, account, conf):
        """Initialise the Teams Sensor."""
        self._teams = account.teams()
        self._name = conf.get(CONF_NAME)
        self._state = None

    @property
    def name(self):
        """Sensor name."""
        return self._name

    @property
    def state(self):
        """Sensor state."""
        return self._state

    @property
    def icon(self):
        """Entity icon."""
        return "mdi:microsoft-teams"

    async def async_update(self):
        """Update state."""
        data = await self.hass.async_add_executor_job(self._teams.get_my_presence)
        self._state = data.activity


class O365TeamsChatSensor(Entity):
    """O365 Teams Chat sensor processing."""

    def __init__(self, account, conf):
        """Initialise the Teams Chat Sensor."""
        self._teams = account.teams()
        self._name = conf.get(CONF_NAME)
        self._state = None
        self._from_display_name = None
        self._content = None
        self._chat_id = None
        self._importance = None
        self._subject = None
        self._summary = None

    @property
    def name(self):
        """Sensor name."""
        return self._name

    @property
    def state(self):
        """Sensor state."""
        return self._state

    @property
    def extra_state_attributes(self):
        """Return entity specific state attributes."""
        attributes = {
            ATTR_FROM_DISPLAY_NAME: self._from_display_name,
            ATTR_CONTENT: self._content,
            ATTR_CHAT_ID: self._chat_id,
            ATTR_IMPORTANCE: self._importance,
        }
        if self._subject:
            attributes[ATTR_SUBJECT] = self._subject
        if self._summary:
            attributes[ATTR_SUMMARY] = self._summary
        return attributes

    async def async_update(self):
        """Update state."""
        state = None
        chats = await self.hass.async_add_executor_job(self._teams.get_my_chats)
        for chat in chats:
            messages = await self.hass.async_add_executor_job(
                ft.partial(chat.get_messages, limit=10)
            )
            for message in messages:
                if not state and message.content != "<systemEventMessage/>":
                    state = message.created_date
                    self._from_display_name = message.from_display_name
                    self._content = message.content
                    self._chat_id = message.chat_id
                    self._importance = message.importance
                    self._subject = message.subject
                    self._summary = message.summary
                    break
            if state:
                break
        self._state = state
