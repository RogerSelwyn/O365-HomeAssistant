"""Sensor processing."""
import functools as ft
import logging
from datetime import datetime, timedelta
from operator import itemgetter

from homeassistant.const import CONF_ENABLED, CONF_NAME, CONF_UNIQUE_ID
from homeassistant.helpers.entity import async_generate_entity_id
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.util import dt
from requests.exceptions import HTTPError

from .classes.mailsensor import O365AutoReplySensor, O365EmailSensor, O365QuerySensor
from .classes.taskssensor import O365TasksSensorSensorServices
from .classes.teamssensor import O365TeamsChatSensor, O365TeamsStatusSensor
from .const import (
    ATTR_ATTRIBUTES,
    ATTR_AUTOREPLIESSETTINGS,
    ATTR_CHAT_ID,
    ATTR_CHAT_TYPE,
    ATTR_CONTENT,
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
    CONF_DUE_HOURS_BACKWARD_TO_GET,
    CONF_DUE_HOURS_FORWARD_TO_GET,
    CONF_EMAIL_SENSORS,
    CONF_ENABLE_UPDATE,
    CONF_ENTITY_KEY,
    CONF_ENTITY_TYPE,
    CONF_MAIL_FOLDER,
    CONF_QUERY_SENSORS,
    CONF_STATUS_SENSORS,
    CONF_TASK_LIST,
    CONF_TASK_LIST_ID,
    CONF_TODO,
    CONF_TODO_SENSORS,
    CONF_TRACK,
    DOMAIN,
    EVENT_HA_EVENT,
    LEGACY_ACCOUNT_NAME,
    SENSOR_AUTO_REPLY,
    SENSOR_ENTITY_ID_FORMAT,
    SENSOR_MAIL,
    SENSOR_TEAMS_CHAT,
    SENSOR_TEAMS_STATUS,
    SENSOR_TODO,
    YAML_TASK_LISTS,
)
from .schema import TASK_LIST_SCHEMA
from .utils.filemgmt import build_config_file_path, build_yaml_filename, load_yaml_file
from .utils.utils import get_email_attributes

_LOGGER = logging.getLogger(__name__)


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
        self._keys = []
        self._data = {}
        self._zero_date = datetime(1, 1, 1, 0, 0, 0, tzinfo=dt.DEFAULT_TIME_ZONE)
        self._chat_members = {}

    async def async_setup_entries(self):
        """Do the initial setup of the entities."""
        email_entities = await self._async_email_sensors()
        query_entities = await self._async_query_sensors()
        status_entities = self._status_sensors()
        chat_entities = self._chat_sensors()
        todo_entities, todo_keys = await self._async_todo_sensors()
        auto_reply_entities = await self._async_auto_reply_sensors()
        self._entities = (
            email_entities
            + query_entities
            + status_entities
            + chat_entities
            + todo_entities
            + auto_reply_entities
        )
        self._keys = todo_keys
        return self._entities, self._keys

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
                entity_id = self._build_entity_id(name)
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
                entity_id = self._build_entity_id(name)
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
            entity_id = self._build_entity_id(name)
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
            entity_id = self._build_entity_id(name)
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
        keys = []
        if todo_sensors and todo_sensors.get(CONF_ENABLED):
            sensor_services = O365TasksSensorSensorServices(self.hass)
            await sensor_services.async_scan_for_task_lists(None)

            yaml_filename = build_yaml_filename(self._config, YAML_TASK_LISTS)
            yaml_filepath = build_config_file_path(self.hass, yaml_filename)
            task_dict = load_yaml_file(
                yaml_filepath, CONF_TASK_LIST_ID, TASK_LIST_SCHEMA
            )
            task_lists = list(task_dict.values())
            entities, keys = await self._async_todo_entities(task_lists)

        return entities, keys

    async def _async_todo_entities(self, task_lists):
        entities = []
        keys = []
        tasks = self._account.tasks()
        for tasklist in task_lists:
            track = tasklist.get(CONF_TRACK)
            if not track:
                continue

            task_list_id = tasklist.get(CONF_TASK_LIST_ID)
            if self._account_name != LEGACY_ACCOUNT_NAME:
                name = f"{tasklist.get(CONF_NAME)} {self._account_name}"
            else:
                name = tasklist.get(CONF_NAME)
            try:
                todo = (
                    await self.hass.async_add_executor_job(  # pylint: disable=no-member
                        ft.partial(
                            tasks.get_folder,
                            folder_id=task_list_id,
                        )
                    )
                )
                entity_id = self._build_entity_id(name)
                unique_id = f"{task_list_id}_{self._account_name}"

                new_key = {
                    CONF_ENTITY_KEY: entity_id,
                    CONF_UNIQUE_ID: unique_id,
                    CONF_TODO: todo,
                    CONF_NAME: name,
                    CONF_TASK_LIST: tasklist,
                    CONF_ENTITY_TYPE: SENSOR_TODO,
                }

                keys.append(new_key)
            except HTTPError:
                _LOGGER.warning(
                    "Task list not found for: %s - Please remove from O365_tasks_%s.yaml",
                    name,
                    self._account_name,
                )
        return entities, keys

    async def _async_auto_reply_sensors(self):
        auto_reply_sensors = self._config.get(CONF_AUTO_REPLY_SENSORS, [])
        entities = []
        for sensor_conf in auto_reply_sensors:
            name = sensor_conf.get(CONF_NAME)
            entity_id = self._build_entity_id(name)
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

        for key in self._keys:
            if key[CONF_ENTITY_TYPE] == SENSOR_TODO:
                await self._async_todos_update(key)

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
            ATTR_ATTRIBUTES: {ATTR_DATA: attrs},
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

    async def _async_todos_update(self, key):
        """Update state."""
        entity_key = key["entity_key"]
        if entity_key in self._data:
            error = self._data[entity_key][ATTR_ERROR]
        else:
            self._data[entity_key] = {ATTR_TASKS: {}, ATTR_STATE: 0}
            error = False
        data, error = await self._async_todos_update_query(key, error)
        if not error:
            tasks = list(data)
            self._data[entity_key][ATTR_TASKS] = tasks
            self._data[entity_key][ATTR_STATE] = len(tasks)

        self._data[entity_key][ATTR_ERROR] = error

    async def _async_todos_update_query(self, key, error):
        data = None
        todo = key[CONF_TODO]
        full_query = self._create_todo_query(key, todo)
        name = key[CONF_NAME]

        try:
            data = await self.hass.async_add_executor_job(  # pylint: disable=no-member
                ft.partial(todo.get_tasks, batch=100, query=full_query)
            )
            if error:
                _LOGGER.info("Task list reconnected for: %s", name)
                error = False
        except HTTPError:
            if not error:
                _LOGGER.error(
                    "Task list not found for: %s - Has it been deleted?",
                    name,
                )
                error = True

        return data, error

    def _create_todo_query(self, key, todo):
        task = key[CONF_TASK_LIST]
        show_completed = task["show_completed"]
        query = todo.new_query()
        if not show_completed:
            query = query.on_attribute("status").unequal("completed")
        start_offset = task.get(CONF_DUE_HOURS_BACKWARD_TO_GET)
        end_offset = task.get(CONF_DUE_HOURS_FORWARD_TO_GET)
        if start_offset:
            start = dt.utcnow() + timedelta(hours=start_offset)
            query.chain("and").on_attribute("due").greater_equal(
                start.strftime("%Y-%m-%dT%H:%M:%S")
            )
        if end_offset:
            end = dt.utcnow() + timedelta(hours=end_offset)
            query.chain("and").on_attribute("due").less_equal(
                end.strftime("%Y-%m-%dT%H:%M:%S")
            )
        return query

    async def _async_auto_reply_update(self, entity):
        """Update state."""
        if data := await self.hass.async_add_executor_job(entity.mailbox.get_settings):
            self._data[entity.entity_key] = {
                ATTR_STATE: data.automaticrepliessettings.status.value,
                ATTR_AUTOREPLIESSETTINGS: data.automaticrepliessettings,
            }

    def _build_entity_id(self, name):
        """Build and entity ID."""
        return async_generate_entity_id(
            SENSOR_ENTITY_ID_FORMAT,
            name,
            hass=self.hass,
        )

    def _raise_event(self, event_type, task_id, time_type, task_datetime):
        self.hass.bus.fire(
            f"{DOMAIN}_{event_type}",
            {ATTR_TASK_ID: task_id, time_type: task_datetime, EVENT_HA_EVENT: False},
        )
        _LOGGER.debug("%s - %s - %s", event_type, task_id, task_datetime)