"""Sensor processing."""
import functools as ft
import logging
from copy import deepcopy
from datetime import datetime, timedelta
from operator import itemgetter

from homeassistant.const import CONF_ENABLED, CONF_NAME
from homeassistant.helpers import entity_platform
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.util import dt
from requests.exceptions import HTTPError

from .classes.mailsensor import O365AutoReplySensor, O365EmailSensor, O365QuerySensor
from .classes.taskssensor import O365TasksSensor
from .classes.teamssensor import O365TeamsChatSensor, O365TeamsStatusSensor
from .const import (
    ATTR_ATTRIBUTES,
    ATTR_AUTOREPLIESSETTINGS,
    ATTR_CHAT_ID,
    ATTR_CHAT_TYPE,
    ATTR_COMPLETED,
    ATTR_CONTENT,
    ATTR_CREATED,
    ATTR_DATA,
    ATTR_ERROR,
    ATTR_FROM_DISPLAY_NAME,
    ATTR_IMPORTANCE,
    ATTR_MEMBERS,
    ATTR_STATE,
    ATTR_SUBJECT,
    ATTR_SUMMARY,
    ATTR_TASK_ID,
    ATTR_TASKS,
    ATTR_TOPIC,
    CONF_ACCOUNT,
    CONF_ACCOUNT_NAME,
    CONF_AUTO_REPLY_SENSORS,
    CONF_CHAT_SENSORS,
    CONF_CONFIG_TYPE,
    CONF_EMAIL_SENSORS,
    CONF_ENABLE_UPDATE,
    CONF_MAIL_FOLDER,
    CONF_QUERY_SENSORS,
    CONF_STATUS_SENSORS,
    CONF_TASK_LIST_ID,
    CONF_TODO_SENSORS,
    CONF_TRACK,
    CONF_TRACK_NEW,
    DOMAIN,
    EVENT_COMPLETED_TASK,
    EVENT_HA_EVENT,
    EVENT_NEW_TASK,
    LEGACY_ACCOUNT_NAME,
    PERM_MINIMUM_CHAT_WRITE,
    PERM_MINIMUM_MAILBOX_SETTINGS,
    PERM_MINIMUM_TASKS_WRITE,
    SENSOR_AUTO_REPLY,
    SENSOR_MAIL,
    SENSOR_TEAMS_CHAT,
    SENSOR_TEAMS_STATUS,
    SENSOR_TODO,
    YAML_TASK_LISTS,
)
from .schema import (
    AUTO_REPLY_SERVICE_DISABLE_SCHEMA,
    AUTO_REPLY_SERVICE_ENABLE_SCHEMA,
    CHAT_SERVICE_SEND_MESSAGE_SCHEMA,
    TASK_LIST_SCHEMA,
    TASK_SERVICE_COMPLETE_SCHEMA,
    TASK_SERVICE_DELETE_SCHEMA,
    TASK_SERVICE_NEW_SCHEMA,
    TASK_SERVICE_UPDATE_SCHEMA,
)
from .utils.filemgmt import (
    build_config_file_path,
    build_token_filename,
    build_yaml_filename,
    load_yaml_file,
    update_task_list_file,
)
from .utils.permissions import get_permissions, validate_minimum_permission
from .utils.utils import build_entity_id, get_email_attributes

_LOGGER = logging.getLogger(__name__)


async def async_setup_platform(
    hass, config, async_add_entities, discovery_info=None
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

    coordinator = O365SensorCordinator(hass, conf)
    entities = await coordinator.async_setup_entries()
    await coordinator.async_config_entry_first_refresh()
    async_add_entities(entities, False)
    await _async_setup_register_services(hass, conf)

    return True


class O365SensorCordinator(DataUpdateCoordinator):
    """O365 sensor data update coordinator."""

    def __init__(self, hass, config):
        """Initialize my coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            # Name of the data. For logging purposes.
            name="O365 Sensors",
            # Polling interval. Will only be polled if there are subscribers.
            update_interval=timedelta(seconds=30),
        )
        self._config = config
        self._account = config[CONF_ACCOUNT]
        self._account_name = config[CONF_ACCOUNT_NAME]
        self._entities = []
        self._data = {}
        self._zero_date = datetime(1, 1, 1, 0, 0, 0, tzinfo=dt.DEFAULT_TIME_ZONE)
        self._chat_members = {}

    async def async_setup_entries(self):
        """Do the initial setup of the entities."""
        email_entities = await self._async_email_sensors()
        query_entities = await self._async_query_sensors()
        status_entities = self._status_sensors()
        chat_entities = self._chat_sensors()
        todo_entities = await self._async_todo_sensors()
        auto_reply_entities = await self._async_auto_reply_sensors()
        self._entities = (
            email_entities
            + query_entities
            + status_entities
            + chat_entities
            + todo_entities
            + auto_reply_entities
        )
        return self._entities

    async def _async_email_sensors(self):
        email_sensors = self._config.get(CONF_EMAIL_SENSORS, [])
        entities = []
        _LOGGER.debug("Email sensor setup: %s ", self._account_name)
        for sensor_conf in email_sensors:
            name = sensor_conf[CONF_NAME]
            _LOGGER.debug(
                "Email sensor setup: %s, %s",
                self._account_name,
                name,
            )
            if mail_folder := await self._async_get_mail_folder(
                sensor_conf, CONF_EMAIL_SENSORS
            ):
                entity_id = build_entity_id(self.hass, name)
                unique_id = f"{mail_folder.folder_id}_{self._account_name}"
                emailsensor = O365EmailSensor(
                    self,
                    self._config,
                    sensor_conf,
                    mail_folder,
                    name,
                    entity_id,
                    unique_id,
                )
                _LOGGER.debug(
                    "Email sensor added: %s, %s",
                    self._account_name,
                    name,
                )
                entities.append(emailsensor)
        return entities

    async def _async_query_sensors(self):
        query_sensors = self._config.get(CONF_QUERY_SENSORS, [])
        entities = []
        for sensor_conf in query_sensors:
            if mail_folder := await self._async_get_mail_folder(
                sensor_conf, CONF_QUERY_SENSORS
            ):
                name = sensor_conf.get(CONF_NAME)
                entity_id = build_entity_id(self.hass, name)
                unique_id = f"{mail_folder.folder_id}_{self._account_name}"
                querysensor = O365QuerySensor(
                    self,
                    self._config,
                    sensor_conf,
                    mail_folder,
                    name,
                    entity_id,
                    unique_id,
                )
                entities.append(querysensor)
        return entities

    def _status_sensors(self):
        status_sensors = self._config.get(CONF_STATUS_SENSORS, [])
        entities = []
        for sensor_conf in status_sensors:
            name = sensor_conf.get(CONF_NAME)
            entity_id = build_entity_id(self.hass, name)
            unique_id = f"{name}_{self._account_name}"
            teams_status_sensor = O365TeamsStatusSensor(
                self, self._account, name, entity_id, self._config, unique_id
            )
            entities.append(teams_status_sensor)
        return entities

    def _chat_sensors(self):
        chat_sensors = self._config.get(CONF_CHAT_SENSORS, [])
        entities = []
        for sensor_conf in chat_sensors:
            name = sensor_conf.get(CONF_NAME)
            enable_update = sensor_conf.get(CONF_ENABLE_UPDATE)
            entity_id = build_entity_id(self.hass, name)
            unique_id = f"{name}_{self._account_name}"
            teams_chat_sensor = O365TeamsChatSensor(
                self,
                self._account,
                name,
                entity_id,
                self._config,
                unique_id,
                enable_update,
            )
            entities.append(teams_chat_sensor)
        return entities

    async def _async_todo_sensors(self):
        todo_sensors = self._config.get(CONF_TODO_SENSORS)
        entities = []
        if todo_sensors and todo_sensors.get(CONF_ENABLED):
            sensor_services = SensorServices(self.hass)
            await sensor_services.async_scan_for_task_lists(None)

            yaml_filename = build_yaml_filename(self._config, YAML_TASK_LISTS)
            yaml_filepath = build_config_file_path(self.hass, yaml_filename)
            task_dict = load_yaml_file(
                yaml_filepath, CONF_TASK_LIST_ID, TASK_LIST_SCHEMA
            )
            task_lists = list(task_dict.values())
            entities = await self._async_todo_entities(task_lists, self._config)

        return entities

    async def _async_todo_entities(self, task_lists, config):
        entities = []
        tasks = self._account.tasks()
        for task in task_lists:
            track = task.get(CONF_TRACK)
            if not track:
                continue

            task_list_id = task.get(CONF_TASK_LIST_ID)
            if self._account_name != LEGACY_ACCOUNT_NAME:
                name = f"{task.get(CONF_NAME)} {self._account_name}"
            else:
                name = task.get(CONF_NAME)
            try:
                todo = (
                    await self.hass.async_add_executor_job(  # pylint: disable=no-member
                        ft.partial(
                            tasks.get_folder,
                            folder_id=task_list_id,
                        )
                    )
                )
                entity_id = build_entity_id(self.hass, name)
                unique_id = f"{task_list_id}_{self._account_name}"
                todo_sensor = O365TasksSensor(
                    self, todo, name, task, config, entity_id, unique_id
                )
                entities.append(todo_sensor)
            except HTTPError:
                _LOGGER.warning(
                    "Task list not found for: %s - Please remove from O365_tasks_%s.yaml",
                    name,
                    self._account_name,
                )
        return entities

    async def _async_auto_reply_sensors(self):
        auto_reply_sensors = self._config.get(CONF_AUTO_REPLY_SENSORS, [])
        entities = []
        for sensor_conf in auto_reply_sensors:
            name = sensor_conf.get(CONF_NAME)
            entity_id = build_entity_id(self.hass, name)
            unique_id = f"{name}_{self._account_name}"
            auto_reply_sensor = O365AutoReplySensor(
                self, name, entity_id, self._config, unique_id
            )
            entities.append(auto_reply_sensor)
        return entities

    async def _async_get_mail_folder(self, sensor_conf, sensor_type):
        """Get the configured folder."""
        mailbox = self._account.mailbox()
        _LOGGER.debug("Get mail folder: %s", sensor_conf.get(CONF_NAME))
        if mail_folder_conf := sensor_conf.get(CONF_MAIL_FOLDER):
            return await self._async_get_configured_mail_folder(
                mail_folder_conf, mailbox, sensor_type
            )

        return mailbox.inbox_folder()

    async def _async_get_configured_mail_folder(
        self, mail_folder_conf, mailbox, sensor_type
    ):
        mail_folder = mailbox
        for folder in mail_folder_conf.split("/"):
            mail_folder = await self.hass.async_add_executor_job(
                ft.partial(
                    mail_folder.get_folder,
                    folder_name=folder,
                )
            )
            if not mail_folder:
                _LOGGER.error(
                    "Folder - %s - not found from %s config entry - %s - entity not created",
                    folder,
                    sensor_type,
                    mail_folder_conf,
                )
                return None

        return mail_folder

    async def _async_update_data(self):
        _LOGGER.debug("Doing sensor update for: %s", self._account_name)
        for entity in self._entities:
            if entity.entity_type == SENSOR_MAIL:
                await self._async_email_update(entity)
            elif entity.entity_type == SENSOR_TEAMS_STATUS:
                await self._async_teams_status_update(entity)
            elif entity.entity_type == SENSOR_TEAMS_CHAT:
                await self._async_teams_chat_update(entity)
            elif entity.entity_type == SENSOR_TODO:
                await self._async_todos_update(entity)
            elif entity.entity_type == SENSOR_AUTO_REPLY:
                await self._async_auto_reply_update(entity)

        return self._data

    async def _async_email_update(self, entity):
        """Update code."""
        data = await self.hass.async_add_executor_job(  # pylint: disable=no-member
            ft.partial(
                entity.mail_folder.get_messages,
                limit=entity.max_items,
                query=entity.query,
                download_attachments=entity.download_attachments,
            )
        )
        attrs = await self.hass.async_add_executor_job(  # pylint: disable=no-member
            self._get_attributes, data, entity
        )
        attrs.sort(key=itemgetter("received"), reverse=True)
        self._data[entity.entity_key] = {
            ATTR_STATE: len(attrs),
            ATTR_ATTRIBUTES: {"data": attrs},
        }

    def _get_attributes(self, data, entity):
        return [
            get_email_attributes(x, entity.download_attachments, entity.html_body)
            for x in data
        ]

    async def _async_teams_status_update(self, entity):
        """Update state."""
        if data := await self.hass.async_add_executor_job(entity.teams.get_my_presence):
            self._data[entity.entity_key] = {ATTR_STATE: data.activity}

    async def _async_teams_chat_update(self, entity):
        """Update state."""
        state = None
        data = []
        self._data[entity.entity_key] = {}
        extra_attributes = {}
        chats = await self.hass.async_add_executor_job(
            ft.partial(entity.teams.get_my_chats, limit=20)
        )
        for chat in chats:
            if chat.chat_type == "unknownFutureValue":
                continue
            if not state:
                messages = await self.hass.async_add_executor_job(
                    ft.partial(chat.get_messages, limit=10)
                )
                state, extra_attributes = self._process_chat_messages(messages)

            if not entity.enable_update:
                if state:
                    break
                continue

            memberlist = await self._async_get_memberlist(chat)
            chatitems = {
                ATTR_CHAT_ID: chat.object_id,
                ATTR_CHAT_TYPE: chat.chat_type,
                ATTR_MEMBERS: ",".join(memberlist),
            }
            if chat.chat_type == "group":
                chatitems[ATTR_TOPIC] = chat.topic

            data.append(chatitems)

        self._data[entity.entity_key] = (
            {ATTR_STATE: state} | extra_attributes | {ATTR_DATA: data}
        )

    def _process_chat_messages(self, messages):
        state = None
        extra_attributes = {}
        for message in messages:
            if not state and message.content != "<systemEventMessage/>":
                state = message.created_date
                extra_attributes = {
                    ATTR_FROM_DISPLAY_NAME: message.from_display_name,
                    ATTR_CONTENT: message.content,
                    ATTR_CHAT_ID: message.chat_id,
                    ATTR_IMPORTANCE: message.importance,
                    ATTR_SUBJECT: message.subject,
                    ATTR_SUMMARY: message.summary,
                }
                break
        return state, extra_attributes

    async def _async_get_memberlist(self, chat):
        if chat.object_id in self._chat_members and chat.chat_type != "oneOnOne":
            return self._chat_members[chat.object_id]
        members = await self.hass.async_add_executor_job(chat.get_members)
        memberlist = [member.display_name for member in members]
        self._chat_members[chat.object_id] = memberlist
        return memberlist

    async def _async_todos_update(self, entity):
        """Update state."""
        if entity.entity_key in self._data:
            error = self._data[entity.entity_key][ATTR_ERROR]
        else:
            self._data[entity.entity_key] = {ATTR_TASKS: {}, ATTR_STATE: 0}
            error = False
        data, error = await self._async_todos_update_query(entity, error)
        if not error:
            tasks = list(data)
            self._data[entity.entity_key][ATTR_TASKS] = tasks
            self._data[entity.entity_key][ATTR_STATE] = len(tasks)
            task_last_completed = self._zero_date
            task_last_created = self._zero_date
            for task in tasks:
                if task.completed and task.completed > entity.task_last_completed:
                    self._raise_event(
                        EVENT_COMPLETED_TASK,
                        task.task_id,
                        ATTR_COMPLETED,
                        task.completed,
                    )
                    if task.completed > task_last_completed:
                        task_last_completed = task.completed
                if task.created and task.created > entity.task_last_created:
                    self._raise_event(
                        EVENT_NEW_TASK, task.task_id, ATTR_CREATED, task.created
                    )
                    if task.created > task_last_created:
                        task_last_created = task.created

            if task_last_completed > self._zero_date:
                entity.task_last_completed = task_last_completed
            if task_last_created > self._zero_date:
                entity.task_last_created = task_last_created

        self._data[entity.entity_key][ATTR_ERROR] = error

    async def _async_todos_update_query(self, entity, error):
        data = None
        full_query = deepcopy(entity.query)
        if entity.start_offset:
            start = dt.utcnow() + timedelta(hours=entity.start_offset)
            full_query.chain("and").on_attribute("due").greater_equal(
                start.strftime("%Y-%m-%dT%H:%M:%S")
            )
        if entity.end_offset:
            end = dt.utcnow() + timedelta(hours=entity.end_offset)
            full_query.chain("and").on_attribute("due").less_equal(
                end.strftime("%Y-%m-%dT%H:%M:%S")
            )

        try:
            data = await self.hass.async_add_executor_job(  # pylint: disable=no-member
                ft.partial(entity.todo.get_tasks, batch=100, query=full_query)
            )
            if error:
                _LOGGER.info("Task list reconnected for: %s", entity.name)
                error = False
        except HTTPError:
            if not error:
                _LOGGER.error(
                    "Task list not found for: %s - Has it been deleted?",
                    entity.name,
                )
                error = True

        return data, error

    async def _async_auto_reply_update(self, entity):
        """Update state."""
        if data := await self.hass.async_add_executor_job(entity.mailbox.get_settings):
            self._data[entity.entity_key] = {
                ATTR_STATE: data.automaticrepliessettings.status.value,
                ATTR_AUTOREPLIESSETTINGS: data.automaticrepliessettings,
            }

    def _raise_event(self, event_type, task_id, time_type, task_datetime):
        self.hass.bus.fire(
            f"{DOMAIN}_{event_type}",
            {ATTR_TASK_ID: task_id, time_type: task_datetime, EVENT_HA_EVENT: False},
        )
        _LOGGER.debug("%s - %s - %s", event_type, task_id, task_datetime)


async def _async_setup_register_services(hass, config):
    await _async_setup_task_services(hass, config)
    await _async_setup_chat_services(hass, config)
    await _async_setup_mailbox_services(hass, config)


async def _async_setup_task_services(hass, config):
    todo_sensors = config.get(CONF_TODO_SENSORS)
    if (
        not todo_sensors
        or not todo_sensors.get(CONF_ENABLED)
        or not todo_sensors.get(CONF_ENABLE_UPDATE)
    ):
        return

    sensor_services = SensorServices(hass)
    hass.services.async_register(
        DOMAIN, "scan_for_task_lists", sensor_services.async_scan_for_task_lists
    )

    permissions = get_permissions(
        hass,
        filename=build_token_filename(config, config.get(CONF_CONFIG_TYPE)),
    )
    platform = entity_platform.async_get_current_platform()
    if validate_minimum_permission(PERM_MINIMUM_TASKS_WRITE, permissions):
        platform.async_register_entity_service(
            "new_task",
            TASK_SERVICE_NEW_SCHEMA,
            "new_task",
        )
        platform.async_register_entity_service(
            "update_task",
            TASK_SERVICE_UPDATE_SCHEMA,
            "update_task",
        )
        platform.async_register_entity_service(
            "delete_task",
            TASK_SERVICE_DELETE_SCHEMA,
            "delete_task",
        )
        platform.async_register_entity_service(
            "complete_task",
            TASK_SERVICE_COMPLETE_SCHEMA,
            "complete_task",
        )


async def _async_setup_chat_services(hass, config):
    chat_sensors = config.get(CONF_CHAT_SENSORS)
    if not chat_sensors:
        return
    chat_sensor = chat_sensors[0]
    if not chat_sensor or not chat_sensor.get(CONF_ENABLE_UPDATE):
        return

    permissions = get_permissions(
        hass,
        filename=build_token_filename(config, config.get(CONF_CONFIG_TYPE)),
    )
    platform = entity_platform.async_get_current_platform()
    if validate_minimum_permission(PERM_MINIMUM_CHAT_WRITE, permissions):
        platform.async_register_entity_service(
            "send_chat_message",
            CHAT_SERVICE_SEND_MESSAGE_SCHEMA,
            "send_chat_message",
        )


async def _async_setup_mailbox_services(hass, config):
    if not config.get(CONF_ENABLE_UPDATE):
        return

    if not config.get(CONF_AUTO_REPLY_SENSORS):
        return

    permissions = get_permissions(
        hass,
        filename=build_token_filename(config, config.get(CONF_CONFIG_TYPE)),
    )
    platform = entity_platform.async_get_current_platform()
    if validate_minimum_permission(PERM_MINIMUM_MAILBOX_SETTINGS, permissions):
        platform.async_register_entity_service(
            "auto_reply_enable",
            AUTO_REPLY_SERVICE_ENABLE_SCHEMA,
            "auto_reply_enable",
        )
        platform.async_register_entity_service(
            "auto_reply_disable",
            AUTO_REPLY_SERVICE_DISABLE_SCHEMA,
            "auto_reply_disable",
        )


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
