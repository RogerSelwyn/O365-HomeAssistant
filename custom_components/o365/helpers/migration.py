"""Migration services."""

import logging
from enum import StrEnum

from homeassistant.config_entries import SOURCE_IMPORT
from homeassistant.const import CONF_EMAIL, CONF_ENABLED, CONF_NAME
from homeassistant.core import HomeAssistant

from ..const import (
    CONF_ACCOUNT_NAME,
    CONF_ACCOUNTS,
    CONF_ALT_AUTH_METHOD,
    CONF_AUTO_REPLY_SENSORS,
    CONF_BASIC_CALENDAR,
    CONF_BODY_CONTAINS,
    CONF_CAL_ID,
    CONF_CHAT_SENSORS,
    CONF_CLIENT_ID,
    CONF_CLIENT_SECRET,
    CONF_DOWNLOAD_ATTACHMENTS,
    CONF_EMAIL_SENSORS,
    CONF_ENABLE_CALENDAR,
    CONF_ENABLE_UPDATE,
    CONF_GROUPS,
    CONF_HAS_ATTACHMENT,
    CONF_HTML_BODY,
    CONF_IMPORTANCE,
    CONF_IS_UNREAD,
    CONF_MAIL_FROM,
    CONF_MAX_ITEMS,
    CONF_QUERY_SENSORS,
    CONF_SHARED_MAILBOX,
    CONF_SHOW_BODY,
    CONF_STATUS_SENSORS,
    CONF_SUBJECT_CONTAINS,
    CONF_SUBJECT_IS,
    CONF_TODO_SENSORS,
    CONF_TRACK_NEW,
    CONF_TRACK_NEW_CALENDAR,
    CONF_YAML_TASK_LIST_ID,
    CONST_CONFIG_TYPE_LIST,
    CONST_PRIMARY,
    YAML_CALENDARS_FILENAME,
    YAML_TASK_LISTS_FILENAME,
)
from ..schema import YAML_CALENDAR_DEVICE_SCHEMA, YAML_TASK_LIST_SCHEMA
from ..utils.filemgmt import build_config_file_path, build_yaml_filename, load_yaml_file
from ..utils.utils import build_account_config

CONF_ALTERNATE_EMAIL = "alternate_email"
CONF_CHAT_ENABLE = "chat_enable"
CONF_ENABLE_AUTOREPLY = "enable_autoreply"
CONF_ENTITY_NAME = "entity_name"
CONF_FOLDER = "folder"
CONF_STATUS_ENABLE = "status_enable"
CONF_YAML_TODO_LIST_ID = "todo_list_id"
_LOGGER = logging.getLogger(__name__)


class Unread(StrEnum):
    """Mail Unread."""

    TRUE = "Unread Only"
    FALSE = "Read Only"
    NONE = "All"


class Attachment(StrEnum):
    """Mail Attachment."""

    TRUE = "Has attachment"
    FALSE = "Does not have attachment"
    NONE = "All"


class ImportanceLevel(StrEnum):
    """Mail Importance Level."""

    NORMAL = "Normal"
    LOW = "Low"
    HIGH = "High"
    NONE = "All"


class EnableOptions(StrEnum):
    """Teams sensors enablement."""

    DISABLED = "Disabled"
    READ = "Read"
    UPDATE = "Update"


class MigrationServices:
    """Migration Services."""

    def __init__(self, hass: HomeAssistant, config):
        """Initialise the migration services."""
        self._hass = hass
        self._config = config
        self._auto_reply_sensors = []

    async def async_migrate_config(self, call):  # pylint: disable=unused-argument
        """Service to migrate config entries."""
        for account in self._config[CONF_ACCOUNTS]:
            account_config = build_account_config(
                account, None, None, CONST_CONFIG_TYPE_LIST, None
            )
            account_config[CONF_ALT_AUTH_METHOD] = account[CONF_ALT_AUTH_METHOD]
            account_config[CONF_CLIENT_SECRET] = account[CONF_CLIENT_SECRET]
            account_config[CONF_BASIC_CALENDAR] = account[CONF_BASIC_CALENDAR]
            account_config[CONF_GROUPS] = account[CONF_GROUPS]

            await self._async_migrate_account(account_config)

    async def _async_migrate_account(self, config):
        base_config_entry = self._setup_base(config)
        await self._async_migrate_calendar(config, base_config_entry)
        await self._async_migrate_mail(config, base_config_entry)
        await self._async_migrate_teams(config, base_config_entry)
        await self._async_migrate_todos(config, base_config_entry)

    async def _async_migrate_calendar(self, config, base_config_entry):
        if not config.get(CONF_ENABLE_CALENDAR, True):
            return
        migrate_domain = "ms365_calendar"
        if not self._integration_installed(migrate_domain):
            return
        entry = {}
        entry[CONF_ENTITY_NAME] = config.get(CONF_ACCOUNT_NAME, CONST_PRIMARY)
        self._add_attribute(config, entry, CONF_ENABLE_UPDATE)
        self._add_attribute(config, entry, CONF_BASIC_CALENDAR)
        self._add_attribute(config, entry, CONF_GROUPS)
        self._add_attribute(config, entry, CONF_SHARED_MAILBOX)
        full_entry = base_config_entry | entry

        options = {}
        self._add_attribute(config, options, CONF_TRACK_NEW_CALENDAR)
        yaml_filename = build_yaml_filename(config, YAML_CALENDARS_FILENAME)
        yaml_filepath = build_config_file_path(self._hass, yaml_filename)
        calendars = await self._hass.async_add_executor_job(
            load_yaml_file, yaml_filepath, CONF_CAL_ID, YAML_CALENDAR_DEVICE_SCHEMA
        )

        await self._async_create_entry(
            migrate_domain, full_entry, options, calendars=calendars
        )

    async def _async_migrate_mail(self, config, base_config_entry):
        email_sensors = config.get(CONF_EMAIL_SENSORS, [])
        query_sensors = config.get(CONF_QUERY_SENSORS, [])
        self._auto_reply_sensors = config.get(CONF_AUTO_REPLY_SENSORS, [])
        if not email_sensors and not query_sensors and not self._auto_reply_sensors:
            return

        migrate_domain = "ms365_mail"
        if not self._integration_installed(migrate_domain):
            return
        await self._async_mail_sensors(
            config, migrate_domain, base_config_entry, email_sensors
        )
        await self._async_mail_sensors(
            config, migrate_domain, base_config_entry, query_sensors
        )
        for sensor in self._auto_reply_sensors:
            entry = {}
            entry[CONF_ENTITY_NAME] = sensor[CONF_NAME]
            full_entry = base_config_entry | entry

            options = {}

            await self._async_create_entry(migrate_domain, full_entry, options)

    async def _async_migrate_teams(self, config, base_config_entry):
        chat_sensors = config.get(CONF_CHAT_SENSORS, [])
        status_sensors = config.get(CONF_STATUS_SENSORS, [])

        if not chat_sensors and not status_sensors:
            return

        migrate_domain = "ms365_teams"
        if not self._integration_installed(migrate_domain):
            return
        entry = {}
        entry[CONF_ENTITY_NAME] = config.get(CONF_ACCOUNT_NAME, CONST_PRIMARY)
        entry[CONF_CHAT_ENABLE] = EnableOptions.DISABLED
        entry[CONF_STATUS_ENABLE] = EnableOptions.DISABLED
        for chat_sensor in chat_sensors:
            enable_update = chat_sensor.get(CONF_ENABLE_UPDATE, False)
            if enable_update:
                entry[CONF_CHAT_ENABLE] = EnableOptions.UPDATE
            else:
                entry[CONF_CHAT_ENABLE] = EnableOptions.READ

        for status_sensor in status_sensors:
            email = status_sensor.get(CONF_EMAIL, None)
            if email:
                await self._async_create_alternate_email_status(
                    migrate_domain, base_config_entry, status_sensor
                )
                continue

            enable_update = status_sensor.get(CONF_ENABLE_UPDATE, False)
            if enable_update:
                entry[CONF_STATUS_ENABLE] = EnableOptions.UPDATE
            else:
                entry[CONF_STATUS_ENABLE] = EnableOptions.READ

        if (
            entry[CONF_CHAT_ENABLE] == EnableOptions.DISABLED
            and entry[CONF_STATUS_ENABLE] == EnableOptions.DISABLED
        ):
            return

        full_entry = base_config_entry | entry

        options = {}

        await self._async_create_entry(migrate_domain, full_entry, options)

    async def _async_migrate_todos(self, config, base_config_entry):
        todo_sensors = config.get(CONF_TODO_SENSORS, {})
        if not todo_sensors or not todo_sensors.get(CONF_ENABLED, False):
            return
        migrate_domain = "ms365_todo"
        if not self._integration_installed(migrate_domain):
            return
        entry = {}
        entry[CONF_ENTITY_NAME] = config.get(CONF_ACCOUNT_NAME, CONST_PRIMARY)
        self._add_attribute(todo_sensors, entry, CONF_ENABLE_UPDATE)
        full_entry = base_config_entry | entry

        options = {}
        self._add_attribute(todo_sensors, options, CONF_TRACK_NEW)
        yaml_filename = build_yaml_filename(config, YAML_TASK_LISTS_FILENAME)
        yaml_filepath = build_config_file_path(self._hass, yaml_filename)
        todos = await self._hass.async_add_executor_job(
            load_yaml_file, yaml_filepath, CONF_YAML_TASK_LIST_ID, YAML_TASK_LIST_SCHEMA
        )
        for value in todos.values():
            value["todo_list_id"] = value[CONF_YAML_TASK_LIST_ID]
            del value[CONF_YAML_TASK_LIST_ID]

        await self._async_create_entry(migrate_domain, full_entry, options, todos=todos)

    async def _async_create_alternate_email_status(
        self, migrate_domain, base_config_entry, status_sensor
    ):
        entry = {}
        entry[CONF_ENTITY_NAME] = status_sensor[CONF_NAME]
        entry[CONF_ALTERNATE_EMAIL] = status_sensor.get(CONF_EMAIL, None)
        enable_update = status_sensor.get(CONF_ENABLE_UPDATE, False)
        if enable_update:
            entry[CONF_STATUS_ENABLE] = EnableOptions.UPDATE
        else:
            entry[CONF_STATUS_ENABLE] = EnableOptions.READ
        entry[CONF_CHAT_ENABLE] = EnableOptions.DISABLED
        full_entry = base_config_entry | entry

        options = {}

        await self._async_create_entry(migrate_domain, full_entry, options)

    async def _async_mail_sensors(
        self,
        config,
        migrate_domain,
        base_config_entry,
        mail_sensors,
    ):
        for sensor in mail_sensors:
            entry = {}
            entry[CONF_ENTITY_NAME] = sensor[CONF_NAME]
            self._add_attribute(config, entry, CONF_ENABLE_UPDATE)
            self._add_attribute(config, entry, CONF_SHARED_MAILBOX)
            if self._auto_reply_sensors:
                entry[CONF_ENABLE_AUTOREPLY] = True
                self._auto_reply_sensors = []
            else:
                entry[CONF_ENABLE_AUTOREPLY] = False
            full_entry = base_config_entry | entry

            options = {}
            self._add_attribute(sensor, options, CONF_FOLDER)
            self._add_attribute(sensor, options, CONF_MAIL_FROM)
            self._add_attribute(sensor, options, CONF_MAX_ITEMS)

            attachments = sensor.get(CONF_HAS_ATTACHMENT, None)
            if attachments is True:
                options[CONF_HAS_ATTACHMENT] = Attachment.TRUE
            elif attachments is False:
                options[CONF_HAS_ATTACHMENT] = Attachment.FALSE

            importance = sensor.get(CONF_IMPORTANCE, None)
            if importance == "low":
                options[CONF_IMPORTANCE] = ImportanceLevel.LOW
            elif importance == "normal":
                options[CONF_IMPORTANCE] = ImportanceLevel.NORMAL
            elif importance == "high":
                options[CONF_IMPORTANCE] = ImportanceLevel.HIGH

            is_unread = sensor.get(CONF_HAS_ATTACHMENT, None)
            if is_unread is True:
                options[CONF_IS_UNREAD] = Unread.TRUE
            elif is_unread is False:
                options[CONF_IS_UNREAD] = Unread.FALSE

            self._add_attribute(sensor, options, CONF_BODY_CONTAINS)
            self._add_attribute(sensor, options, CONF_SUBJECT_CONTAINS)
            self._add_attribute(sensor, options, CONF_SUBJECT_IS)
            self._add_attribute(sensor, options, CONF_DOWNLOAD_ATTACHMENTS)
            self._add_attribute(sensor, options, CONF_HTML_BODY)
            self._add_attribute(sensor, options, CONF_SHOW_BODY)

            await self._async_create_entry(migrate_domain, full_entry, options)

    async def _async_create_entry(
        self, migrate_domain, data, options, calendars=None, todos=None
    ):
        entry = {"data": data, "options": options}
        if calendars:
            entry["calendars"] = calendars
        if todos:
            entry["todos"] = todos
        await self._hass.config_entries.flow.async_init(
            migrate_domain,
            context={"source": SOURCE_IMPORT},
            data=entry,
        )

    def _integration_installed(self, migrate_domain):
        installed = migrate_domain in self._hass.data["custom_components"]
        if not installed:
            _LOGGER.warning(
                "%s not installed. Install via HACS and try again.", migrate_domain
            )
        return installed

    def _setup_base(self, config):
        entry = {
            CONF_CLIENT_ID: config.get(CONF_CLIENT_ID),
            CONF_CLIENT_SECRET: config.get(CONF_CLIENT_SECRET),
        }
        self._add_attribute(config, entry, CONF_ALT_AUTH_METHOD)
        return entry

    def _add_attribute(self, config, entry, attribute_name):
        attribute = config.get(attribute_name)
        if attribute is not None:
            entry[attribute_name] = attribute
