"""Sensor processing."""

import functools as ft
import logging
from datetime import datetime, timedelta

from homeassistant.const import CONF_EMAIL, CONF_ENABLED, CONF_NAME, CONF_UNIQUE_ID
from homeassistant.helpers import entity_registry
from homeassistant.helpers.entity import async_generate_entity_id
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.util import dt as dt_util
from requests.exceptions import HTTPError

from O365.utils.query import (  # pylint: disable=no-name-in-module, import-error  # pylint: disable=no-name-in-module, import-error
    QueryBuilder,
)

from ..classes.mailsensor import async_build_inbox_query, async_build_query_query
from ..const import (
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
    ATTR_TODOS,
    ATTR_TOPIC,
    CONF_ACCOUNT,
    CONF_ACCOUNT_NAME,
    CONF_AUTO_REPLY_SENSORS,
    CONF_CHAT_SENSORS,
    CONF_DOWNLOAD_ATTACHMENTS,
    CONF_EMAIL_ACCOUNT,
    CONF_EMAIL_SENSORS,
    CONF_ENABLE_UPDATE,
    CONF_ENTITY_KEY,
    CONF_ENTITY_TYPE,
    CONF_MAIL_FOLDER,
    CONF_MAX_ITEMS,
    CONF_O365_MAIL_FOLDER,
    CONF_O365_TASK_FOLDER,
    CONF_QUERY,
    CONF_QUERY_SENSORS,
    CONF_SENSOR_CONF,
    CONF_STATUS_SENSORS,
    CONF_TODO_SENSORS,
    CONF_TRACK,
    CONF_YAML_TASK_LIST,
    CONF_YAML_TASK_LIST_ID,
    DOMAIN,
    ENTITY_ID_FORMAT_SENSOR,
    ENTITY_ID_FORMAT_TODO,
    LEGACY_ACCOUNT_NAME,
    SENSOR_AUTO_REPLY,
    SENSOR_EMAIL,
    SENSOR_TEAMS_CHAT,
    SENSOR_TEAMS_STATUS,
    TODO_TODO,
    YAML_TASK_LISTS_FILENAME,
)
from ..schema import YAML_TASK_LIST_SCHEMA
from ..todo import O365TodoEntityServices, async_build_todo_query
from ..utils.filemgmt import build_config_file_path, build_yaml_filename, load_yaml_file

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
        self._keys = []
        self._data = {}
        self._zero_date = datetime(
            1, 1, 1, 0, 0, 0, tzinfo=dt_util.get_default_time_zone()
        )
        self._chat_members = {}
        self._ent_reg = entity_registry.async_get(hass)
        self._builder = QueryBuilder(protocol=self._account.protocol)

    async def async_setup_entries(self):
        """Do the initial setup of the entities."""
        status_keys = await self._async_status_sensors()
        chat_keys = self._chat_sensors()
        todo_keys = await self._async_todo_sensors()
        auto_reply_entities = await self._async_auto_reply_sensors()
        self._keys = chat_keys + status_keys + todo_keys + auto_reply_entities
        return self._keys

    async def _async_status_sensors(self):
        status_sensors = self._config.get(CONF_STATUS_SENSORS, [])
        keys = []
        for sensor_conf in status_sensors:
            name = sensor_conf.get(CONF_NAME)
            new_key = {
                CONF_ENTITY_KEY: _build_entity_id(
                    self.hass, ENTITY_ID_FORMAT_SENSOR, name
                ),
                CONF_UNIQUE_ID: f"{name}_{self._account_name}",
                CONF_NAME: name,
                CONF_ENTITY_TYPE: SENSOR_TEAMS_STATUS,
                CONF_EMAIL: sensor_conf.get(CONF_EMAIL),
            }
            if sensor_conf.get(CONF_EMAIL):
                email_account = await self.hass.async_add_executor_job(
                    self._account.directory().get_user,
                    sensor_conf.get(CONF_EMAIL),
                )
                new_key[CONF_EMAIL_ACCOUNT] = email_account.object_id

            keys.append(new_key)
        return keys

    def _chat_sensors(self):
        chat_sensors = self._config.get(CONF_CHAT_SENSORS, [])
        keys = []
        for sensor_conf in chat_sensors:
            name = sensor_conf.get(CONF_NAME)
            new_key = {
                CONF_ENTITY_KEY: _build_entity_id(
                    self.hass, ENTITY_ID_FORMAT_SENSOR, name
                ),
                CONF_UNIQUE_ID: f"{name}_{self._account_name}",
                CONF_NAME: name,
                CONF_ENTITY_TYPE: SENSOR_TEAMS_CHAT,
                CONF_ENABLE_UPDATE: sensor_conf.get(CONF_ENABLE_UPDATE),
            }

            keys.append(new_key)
        return keys

    async def _async_todo_sensors(self):
        todo_sensors = self._config.get(CONF_TODO_SENSORS)
        keys = []
        if todo_sensors and todo_sensors.get(CONF_ENABLED):
            sensor_services = O365TodoEntityServices(self.hass)
            await sensor_services.async_scan_for_todo_lists(None)

            yaml_filename = build_yaml_filename(self._config, YAML_TASK_LISTS_FILENAME)
            yaml_filepath = build_config_file_path(self.hass, yaml_filename)
            o365_task_dict = await self.hass.async_add_executor_job(
                load_yaml_file,
                yaml_filepath,
                CONF_YAML_TASK_LIST_ID,
                YAML_TASK_LIST_SCHEMA,
            )
            o365_task_lists = list(o365_task_dict.values())
            keys = await self._async_todo_entities(o365_task_lists)

        return keys

    async def _async_todo_entities(self, o365_task_lists):
        keys = []
        o365_tasks = await self.hass.async_add_executor_job(self._account.tasks)
        for o365_tasklist in o365_task_lists:
            track = o365_tasklist.get(CONF_TRACK)
            if not track:
                continue

            o365_task_list_id = o365_tasklist.get(CONF_YAML_TASK_LIST_ID)
            if self._account_name != LEGACY_ACCOUNT_NAME:
                name = f"{o365_tasklist.get(CONF_NAME)} {self._account_name}"
            else:
                name = o365_tasklist.get(CONF_NAME)
            try:
                o365_task = await self.hass.async_add_executor_job(  # pylint: disable=no-member
                    ft.partial(
                        o365_tasks.get_folder,
                        folder_id=o365_task_list_id,
                    )
                )
                unique_id = f"{o365_task_list_id}_{self._account_name}"
                new_key = {
                    CONF_ENTITY_KEY: _build_entity_id(
                        self.hass, ENTITY_ID_FORMAT_TODO, name
                    ),
                    CONF_UNIQUE_ID: unique_id,
                    CONF_O365_TASK_FOLDER: o365_task,
                    CONF_NAME: name,
                    CONF_YAML_TASK_LIST: o365_tasklist,
                    CONF_ENTITY_TYPE: TODO_TODO,
                }

                keys.append(new_key)
                # To be deleted in mid 2024 after majority have migrated
                # to HA 2023.11 and O365 version 4.5
                await _async_delete_redundant_sensors(self._ent_reg, unique_id)

            except HTTPError:
                _LOGGER.warning(
                    "O365 Task list not found for: %s - Please remove from O365_tasks_%s.yaml",
                    name,
                    self._account_name,
                )
        return keys

    async def _async_auto_reply_sensors(self):
        auto_reply_sensors = self._config.get(CONF_AUTO_REPLY_SENSORS, [])
        keys = []
        for sensor_conf in auto_reply_sensors:
            name = sensor_conf.get(CONF_NAME)
            new_key = {
                CONF_ENTITY_KEY: _build_entity_id(
                    self.hass, ENTITY_ID_FORMAT_SENSOR, name
                ),
                CONF_UNIQUE_ID: f"{name}_{self._account_name}",
                CONF_NAME: name,
                CONF_ENTITY_TYPE: SENSOR_AUTO_REPLY,
            }

            keys.append(new_key)
        return keys

    async def _async_update_data(self):
        _LOGGER.debug(
            "Doing %s sensor update(s) for: %s", len(self._keys), self._account_name
        )

        for key in self._keys:
            entity_type = key[CONF_ENTITY_TYPE]
            _LOGGER.debug("%s for: %s", entity_type, self._account_name)
            if entity_type == TODO_TODO:
                await self._async_todos_update(key)
            elif entity_type == SENSOR_TEAMS_CHAT:
                await self._async_teams_chat_update(key)
            elif entity_type == SENSOR_TEAMS_STATUS:
                await self._async_teams_status_update(key)
            elif entity_type == SENSOR_AUTO_REPLY:
                await self._async_auto_reply_update(key)

        return self._data

    async def _async_teams_status_update(self, key):
        """Update state."""
        entity_key = key[CONF_ENTITY_KEY]
        email_account = key.get(CONF_EMAIL_ACCOUNT)
        if not email_account:
            if data := await self.hass.async_add_executor_job(
                self._account.teams().get_my_presence
            ):
                self._data[entity_key] = {ATTR_STATE: data.activity}
            return
        if data := await self.hass.async_add_executor_job(
            self._account.teams().get_user_presence, email_account
        ):
            self._data[entity_key] = {ATTR_STATE: data.activity}

    async def _async_teams_chat_update(self, key):
        entity_key = key[CONF_ENTITY_KEY]
        state = None
        data = []
        self._data[entity_key] = {}
        extra_attributes = {}
        chats = await self.hass.async_add_executor_job(
            ft.partial(self._account.teams().get_my_chats, limit=20)
        )
        for chat in chats:
            if chat.chat_type == "unknownFutureValue":
                continue
            if not state:
                messages = await self.hass.async_add_executor_job(
                    ft.partial(chat.get_messages, limit=10)
                )
                state, extra_attributes = self._process_chat_messages(messages)

            if not key[CONF_ENABLE_UPDATE]:
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

        self._data[entity_key] = (
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
        memberlist = []
        for member in members:
            if member.display_name:
                memberlist.append(member.display_name)
            elif member.email:
                memberlist.append(member.email)
            else:
                memberlist.append("Name Unknown")
        self._chat_members[chat.object_id] = memberlist
        return memberlist

    async def _async_todos_update(self, key):
        """Update state."""
        entity_key = key[CONF_ENTITY_KEY]
        if entity_key in self._data:
            error = self._data[entity_key][ATTR_ERROR]
        else:
            self._data[entity_key] = {ATTR_TODOS: {}, ATTR_STATE: 0}
            error = False
        data, error = await self._async_todos_update_query(key, error)
        if not error:
            self._data[entity_key][ATTR_DATA] = await self.hass.async_add_executor_job(
                list, data
            )

        self._data[entity_key][ATTR_ERROR] = error

    async def _async_todos_update_query(self, key, error):
        data = None
        o365_task = key[CONF_O365_TASK_FOLDER]
        full_query = await async_build_todo_query(self._builder, key)
        name = key[CONF_NAME]

        try:
            data = await self.hass.async_add_executor_job(  # pylint: disable=no-member
                ft.partial(o365_task.get_tasks, batch=100, query=full_query)
            )
            if error:
                _LOGGER.info("O365 Task list reconnected for: %s", name)
                error = False
        except HTTPError:
            if not error:
                _LOGGER.error(
                    "O365 Task list not found for: %s - Has it been deleted?",
                    name,
                )
                error = True

        return data, error

    async def _async_auto_reply_update(self, key):
        """Update state."""
        entity_key = key[CONF_ENTITY_KEY]
        if data := await self.hass.async_add_executor_job(
            self._account.mailbox().get_settings
        ):
            self._data[entity_key] = {
                ATTR_STATE: data.automaticrepliessettings.status.value,
                ATTR_AUTOREPLIESSETTINGS: data.automaticrepliessettings,
            }


class O365EmailCordinator(DataUpdateCoordinator):
    """O365 email data update coordinator."""

    def __init__(self, hass, config):
        """Initialize my coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            # Name of the data. For logging purposes.
            name="O365 Email",
            # Polling interval. Will only be polled if there are subscribers.
            update_interval=timedelta(seconds=30),
        )
        self._hass = hass
        self._config = config
        self._account = config[CONF_ACCOUNT]
        self._account_name = config[CONF_ACCOUNT_NAME]
        self._keys = []
        self._data = {}
        self._zero_date = datetime(
            1, 1, 1, 0, 0, 0, tzinfo=dt_util.get_default_time_zone()
        )
        self._chat_members = {}
        self._ent_reg = entity_registry.async_get(hass)
        self._builder = QueryBuilder(protocol=self._account.protocol)

    async def async_setup_entries(self):
        """Do the initial setup of the entities."""
        email_keys = await self._async_email_sensors()
        query_keys = await self._async_query_sensors()
        self._keys = email_keys + query_keys
        return self._keys

    async def _async_email_sensors(self):
        email_sensors = self._config.get(CONF_EMAIL_SENSORS, [])
        keys = []
        for sensor_conf in email_sensors:
            name = sensor_conf[CONF_NAME]
            if mail_folder := await self._async_get_mail_folder(
                sensor_conf, CONF_EMAIL_SENSORS
            ):
                new_key = {
                    CONF_ENTITY_KEY: _build_entity_id(
                        self.hass, ENTITY_ID_FORMAT_SENSOR, name
                    ),
                    CONF_UNIQUE_ID: f"{mail_folder.folder_id}_{self._account_name}_{name}",
                    CONF_SENSOR_CONF: sensor_conf,
                    CONF_O365_MAIL_FOLDER: mail_folder,
                    CONF_NAME: name,
                    CONF_ENTITY_TYPE: SENSOR_EMAIL,
                    CONF_QUERY: await async_build_inbox_query(
                        sensor_conf, self._builder
                    ),
                }

                # Renames unique id to ensure uniqueness - To be deleted in early 2025
                entity = self._ent_reg.async_get(new_key[CONF_ENTITY_KEY])
                if (
                    entity
                    and entity.unique_id
                    == f"{mail_folder.folder_id}_{self._account_name}"
                ):
                    self._ent_reg.async_update_entity(
                        new_key[CONF_ENTITY_KEY], new_unique_id=new_key[CONF_UNIQUE_ID]
                    )

                keys.append(new_key)
        return keys

    async def _async_query_sensors(self):
        query_sensors = self._config.get(CONF_QUERY_SENSORS, [])
        keys = []
        for sensor_conf in query_sensors:
            if mail_folder := await self._async_get_mail_folder(
                sensor_conf, CONF_QUERY_SENSORS
            ):
                name = sensor_conf.get(CONF_NAME)
                new_key = {
                    CONF_ENTITY_KEY: _build_entity_id(
                        self.hass, ENTITY_ID_FORMAT_SENSOR, name
                    ),
                    CONF_UNIQUE_ID: f"{mail_folder.folder_id}_{self._account_name}_{name}",
                    CONF_SENSOR_CONF: sensor_conf,
                    CONF_O365_MAIL_FOLDER: mail_folder,
                    CONF_NAME: name,
                    CONF_ENTITY_TYPE: SENSOR_EMAIL,
                    CONF_QUERY: await async_build_query_query(
                        sensor_conf, self._builder
                    ),
                }

                # Renames unique id to ensure uniqueness - To be deleted in early 2025
                entity = self._ent_reg.async_get(new_key[CONF_ENTITY_KEY])
                if (
                    entity
                    and entity.unique_id
                    == f"{mail_folder.folder_id}_{self._account_name}"
                ):
                    self._ent_reg.async_update_entity(
                        new_key[CONF_ENTITY_KEY], new_unique_id=new_key[CONF_UNIQUE_ID]
                    )

                keys.append(new_key)
        return keys

    async def _async_get_mail_folder(self, sensor_conf, sensor_type):
        """Get the configured folder."""
        mailbox = await self.hass.async_add_executor_job(self._account.mailbox)
        _LOGGER.debug("Get mail folder: %s", sensor_conf.get(CONF_NAME))
        if mail_folder_conf := sensor_conf.get(CONF_MAIL_FOLDER):
            return await self._async_get_configured_mail_folder(
                mail_folder_conf, mailbox, sensor_type
            )

        return await self.hass.async_add_executor_job(mailbox.inbox_folder)

    async def _async_get_configured_mail_folder(
        self, mail_folder_conf, mailbox, sensor_type
    ):
        mail_folder = mailbox
        _LOGGER.debug("Get folder %s - start", mail_folder_conf)

        for folder in mail_folder_conf.split("/"):
            mail_folder = await self.hass.async_add_executor_job(
                ft.partial(
                    mail_folder.get_folder,
                    folder_name=folder,
                )
            )
            _LOGGER.debug("Get folder %s - process - %s", mail_folder_conf, mail_folder)
            if not mail_folder:
                _LOGGER.error(
                    "Folder - %s - not found from %s config entry - %s - entity not created",
                    folder,
                    sensor_type,
                    mail_folder_conf,
                )
                return None

        _LOGGER.debug("Get folder %s - finish ", mail_folder_conf)
        return mail_folder

    async def _async_update_data(self):
        _LOGGER.debug(
            "Doing %s email update(s) for: %s", len(self._keys), self._account_name
        )

        for key in self._keys:
            await self._async_email_update(key)

        return self._data

    async def _async_email_update(self, key):
        """Update code."""

        sensor_conf = key[CONF_SENSOR_CONF]
        download_attachments = sensor_conf.get(CONF_DOWNLOAD_ATTACHMENTS)
        max_items = sensor_conf.get(CONF_MAX_ITEMS, 5)
        mail_folder = key[CONF_O365_MAIL_FOLDER]
        entity_key = key[CONF_ENTITY_KEY]
        query = key[CONF_QUERY]

        data = await self.hass.async_add_executor_job(  # pylint: disable=no-member
            ft.partial(
                mail_folder.get_messages,
                limit=max_items,
                query=query,
                download_attachments=download_attachments,
            )
        )
        self._data[entity_key] = {
            ATTR_DATA: await self.hass.async_add_executor_job(list, data)
        }


def _build_entity_id(hass, entity_id_format, name):
    """Build and entity ID."""
    return async_generate_entity_id(
        entity_id_format,
        name,
        hass=hass,
    )


async def _async_delete_redundant_sensors(ent_reg, unique_id):
    if entity_id := ent_reg.async_get_entity_id("sensor", DOMAIN, unique_id):
        ent_reg.async_remove(entity_id)
