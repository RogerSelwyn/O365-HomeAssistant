"""Sensor processing."""
import datetime
import functools as ft
import logging
from operator import itemgetter

import voluptuous as vol
from homeassistant.const import CONF_ENABLED, CONF_NAME
from homeassistant.helpers import entity_platform
from homeassistant.helpers.entity import Entity, generate_entity_id
from homeassistant.util import dt
from requests.exceptions import HTTPError

from .const import (
    ATTR_ALL_TASKS,
    ATTR_CHAT_ID,
    ATTR_CONTENT,
    ATTR_DUE,
    ATTR_FROM_DISPLAY_NAME,
    ATTR_IMPORTANCE,
    ATTR_OVERDUE_TASKS,
    ATTR_SUBJECT,
    ATTR_SUMMARY,
    CONF_ACCOUNT,
    CONF_ACCOUNT_NAME,
    CONF_BODY_CONTAINS,
    CONF_CHAT_SENSORS,
    CONF_DOWNLOAD_ATTACHMENTS,
    CONF_EMAIL_SENSORS,
    CONF_ENABLE_UPDATE,
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
    CONF_TASK_LIST_ID,
    CONF_TODO_SENSORS,
    CONF_TRACK,
    CONF_TRACK_NEW,
    DOMAIN,
    SENSOR_ENTITY_ID_FORMAT,
    YAML_TASK_LISTS,
)
from .schema import NEW_TASK_SCHEMA, TASK_LIST_SCHEMA
from .utils import (
    build_config_file_path,
    build_yaml_filename,
    get_email_attributes,
    load_yaml_file,
    update_task_list_file,
)

_LOGGER = logging.getLogger(__name__)

PARALLEL_UPDATES = 6


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
    await _async_todo_sensors(hass, account, add_entities, conf)
    await _async_setup_register_services(hass, conf)

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


async def _async_todo_sensors(hass, account, add_entities, conf):
    todo_sensors = conf.get(CONF_TODO_SENSORS)
    if todo_sensors and todo_sensors.get(CONF_ENABLED):
        sensor_services = SensorServices(hass)
        await sensor_services.async_scan_for_task_lists(None)

        yaml_filename = build_yaml_filename(conf, YAML_TASK_LISTS)
        yaml_filepath = build_config_file_path(hass, yaml_filename)
        task_dict = load_yaml_file(yaml_filepath, CONF_TASK_LIST_ID, TASK_LIST_SCHEMA)
        task_lists = list(task_dict.values())
        tasks = account.tasks()
        for task in task_lists:
            name = task.get(CONF_NAME)
            track = task.get(CONF_TRACK)
            task_list_id = task.get(CONF_TASK_LIST_ID)
            entity_id = _build_entity_id(hass, name, conf)
            if not track:
                continue
            todo = await hass.async_add_executor_job(  # pylint: disable=no-member
                ft.partial(
                    tasks.get_folder,
                    folder_id=task_list_id,
                )
            )
            todo_sensor = O365TodoSensor(todo, name, entity_id)
            add_entities([todo_sensor], True)


def _build_entity_id(hass, name, conf):
    return generate_entity_id(
        SENSOR_ENTITY_ID_FORMAT,
        f"{name}_{conf[CONF_ACCOUNT_NAME]}",
        hass=hass,
    )


async def _async_setup_register_services(hass, conf):
    todo_sensors = conf.get(CONF_TODO_SENSORS)
    if not todo_sensors or not todo_sensors.get(CONF_ENABLED):
        return

    platform = entity_platform.async_get_current_platform()
    if conf.get(CONF_ENABLE_UPDATE):
        platform.async_register_entity_service(
            "new_task",
            NEW_TASK_SCHEMA,
            "new_task",
        )

    sensor_services = SensorServices(hass)
    hass.services.async_register(
        DOMAIN, "scan_for_task_lists", sensor_services.async_scan_for_task_lists
    )


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
    def icon(self):
        """Entity icon."""
        return "mdi:microsoft-outlook"

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

        attrs = await self.hass.async_add_executor_job(  # pylint: disable=no-member
            self._get_attributes, data
        )

        attrs.sort(key=itemgetter("received"), reverse=True)
        self._state = len(attrs)
        self._attributes = {"data": attrs}

    def _get_attributes(self, data):
        return [get_email_attributes(x, self._download_attachments) for x in data]


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

        self._build_query()

    def _build_query(self):
        if (
            self._body_contains is not None
            or self._subject_contains is not None
            or self._subject_is is not None
            or self._has_attachment is not None
            or self._importance is not None
            or self._email_from is not None
            or self._is_unread is not None
        ):
            self._add_to_query("ge", "receivedDateTime", datetime.datetime(1900, 5, 1))
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
    def icon(self):
        """Entity icon."""
        return "mdi:microsoft-teams"

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


class O365TodoSensor(Entity):
    """O365 Teams sensor processing."""

    def __init__(self, todo, name, entity_id):
        """Initialise the Teams Sensor."""
        self._todo = todo
        self._query = self._todo.new_query("status").unequal("completed")
        self._id = todo.folder_id
        self._name = name
        self.entity_id = entity_id
        self._tasks = []
        self._error = False

    @property
    def name(self):
        """Sensor name."""
        return self._name

    @property
    def state(self):
        """Sensor state."""
        return len(self._tasks)

    @property
    def icon(self):
        """Entity icon."""
        return "mdi:clipboard-check-outline"

    @property
    def extra_state_attributes(self):
        """Extra state attributes."""
        all_tasks = []
        overdue_tasks = []
        for item in self._tasks:
            task = {ATTR_SUBJECT: item.subject}
            if item.due:
                task[ATTR_DUE] = item.due
                if item.due < dt.utcnow():
                    overdue_tasks.append(
                        {ATTR_SUBJECT: item.subject, ATTR_DUE: item.due}
                    )

            all_tasks.append(task)

        extra_attributes = {ATTR_ALL_TASKS: all_tasks}
        if overdue_tasks:
            extra_attributes[ATTR_OVERDUE_TASKS] = overdue_tasks
        return extra_attributes

    async def async_update(self):
        """Update state."""
        try:
            data = await self.hass.async_add_executor_job(  # pylint: disable=no-member
                ft.partial(self._todo.get_tasks, batch=100, query=self._query)
            )
            if self._error:
                _LOGGER.info("Task list reconnected for: %s", self._name)
                self._error = False
            self._tasks = list(data)
        except HTTPError:
            if not self._error:
                _LOGGER.error(
                    "Task list not found for: %s - Has it been deleted?",
                    self._name,
                )
                self._error = True

    def new_task(self, subject, description=None, due=None, reminder=None):
        """Create a new task for this task list."""
        new_task = self._todo.new_task(subject=subject)
        if description:
            new_task.body = description
        if due:
            try:
                if len(due) > 10:
                    new_task.due = dt.parse_datetime(due).date()
                else:
                    new_task.due = dt.parse_date(due)
            except ValueError:
                error = f"Due date {due} is not in valid format YYYY-MM-DD"
                raise vol.Invalid(error)  # pylint: disable=raise-missing-from

        if reminder:
            new_task.reminder = reminder

        new_task.save()
        return True


class SensorServices:
    """Sensor Services."""

    def __init__(self, hass):
        """Initialise the sensor services."""
        self._hass = hass

    async def async_scan_for_task_lists(self, call):  # pylint: disable=unused-argument
        """Scan for new task lists."""
        for config in self._hass.data[DOMAIN]:
            config = self._hass.data[DOMAIN][config]
            todo_sensor = config.get(CONF_TODO_SENSORS)
            if todo_sensor and CONF_ACCOUNT in config and todo_sensor.get(CONF_ENABLED):
                todos = config[CONF_ACCOUNT].tasks()

                todolists = await self._hass.async_add_executor_job(todos.list_folders)
                track = todo_sensor.get(CONF_TRACK_NEW)
                for todo in todolists:
                    update_task_list_file(
                        build_yaml_filename(config, YAML_TASK_LISTS),
                        todo,
                        self._hass,
                        track,
                    )
