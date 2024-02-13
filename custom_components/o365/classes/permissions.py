"""Permissions processes."""
import json
import logging
import os

from homeassistant.const import CONF_EMAIL, CONF_ENABLED

from ..const import (
    CONF_ACCOUNT_NAME,
    CONF_AUTO_REPLY_SENSORS,
    CONF_BASIC_CALENDAR,
    CONF_CAL_ID,
    CONF_CHAT_SENSORS,
    CONF_EMAIL_SENSORS,
    CONF_ENABLE_UPDATE,
    CONF_ENTITIES,
    CONF_GROUPS,
    CONF_QUERY_SENSORS,
    CONF_SHARED_MAILBOX,
    CONF_STATUS_SENSORS,
    CONF_TODO_SENSORS,
    CONF_TRACK,
    CONST_CONFIG_TYPE_LIST,
    CONST_GROUP,
    O365_STORAGE_TOKEN,
    PERM_CALENDARS_READ,
    PERM_CALENDARS_READBASIC,
    PERM_CALENDARS_READWRITE,
    PERM_CHAT_READ,
    PERM_CHAT_READWRITE,
    PERM_GROUP_READ_ALL,
    PERM_GROUP_READWRITE_ALL,
    PERM_MAIL_READ,
    PERM_MAIL_SEND,
    PERM_MAILBOX_SETTINGS,
    PERM_MINIMUM_CALENDAR,
    PERM_MINIMUM_CHAT,
    PERM_MINIMUM_GROUP,
    PERM_MINIMUM_MAIL,
    PERM_MINIMUM_MAILBOX_SETTINGS,
    PERM_MINIMUM_PRESENCE,
    PERM_MINIMUM_PRESENCE_ALL,
    PERM_MINIMUM_TASKS,
    PERM_MINIMUM_USER,
    PERM_OFFLINE_ACCESS,
    PERM_PRESENCE_READ,
    PERM_PRESENCE_READ_ALL,
    PERM_PRESENCE_READWRITE,
    PERM_SHARED,
    PERM_TASKS_READ,
    PERM_TASKS_READWRITE,
    PERM_USER_READ,
    TOKEN_FILE_MISSING,
    TOKEN_FILENAME,
    YAML_CALENDARS_FILENAME,
)
from ..schema import YAML_CALENDAR_DEVICE_SCHEMA
from ..utils.filemgmt import build_config_file_path, build_yaml_filename, load_yaml_file

_LOGGER = logging.getLogger(__name__)


class Permissions:
    """Class in support of building permssion sets."""

    def __init__(self, hass, config, conf_type):
        """Initialise the class."""
        self._hass = hass
        self._config = config
        self._conf_type = conf_type

        self._shared = PERM_SHARED if config.get(CONF_SHARED_MAILBOX) else ""
        self._enable_update = self._config.get(CONF_ENABLE_UPDATE, False)
        self._minimum_permissions = []
        self._requested_permissions = []
        self.token_filename = self._build_token_filename()
        self.token_path = build_config_file_path(self._hass, O365_STORAGE_TOKEN)
        self._permissions = []

    @property
    def minimum_permissions(self):
        """Return the required scope."""
        if not self._minimum_permissions:
            self._minimum_permissions = [
                PERM_MINIMUM_USER,
                self._add_shared(PERM_MINIMUM_CALENDAR),
            ]
            self._build_email_min_permissions()
            self._build_status_min_permissions()
            self._build_chat_min_permissions()
            self._build_todo_min_permissions()
            self._build_autoreply_min_permissions()
            self._build_group_min_permssions()
        return self._minimum_permissions

    @property
    def requested_permissions(self):
        """Return the required scope."""
        if not self._requested_permissions:
            self._requested_permissions = [PERM_OFFLINE_ACCESS, PERM_USER_READ]
            self._build_calendar_permissions()
            self._build_group_permissions()
            self._build_email_permissions()
            self._build_autoreply_permissions()
            self._build_status_permissions()
            self._build_chat_permissions()
            self._build_todo_permissions()
        return self._requested_permissions

    @property
    def permissions(self):
        """Return the permission set."""
        if not self._permissions:
            self._permissions = self._get_permissions()

        return self._permissions

    def validate_permissions(self):
        """Validate the permissions."""
        if self.permissions == TOKEN_FILE_MISSING:
            return TOKEN_FILE_MISSING, None

        failed_permissions = []
        for minimum_perm in self.minimum_permissions:
            permission_granted = self.validate_minimum_permission(minimum_perm)
            if not permission_granted:
                failed_permissions.append(minimum_perm[0])

        if failed_permissions:
            _LOGGER.warning(
                "Minimum required permissions not granted: %s",
                ", ".join(failed_permissions),
            )
            return False, failed_permissions

        return True, None

    def validate_minimum_permission(self, minimum_perm):
        """Validate the minimum permissions."""
        if minimum_perm[0] in self.permissions:
            return True

        return any(
            alternate_perm in self.permissions for alternate_perm in minimum_perm[1]
        )

    def report_perms(self):
        """Report on permissions status."""
        for permission in self.requested_permissions:
            if permission == PERM_OFFLINE_ACCESS:
                continue
            if permission not in self.permissions:
                _LOGGER.warning(
                    "O365 config requests permission: '%s'. Not available in token '%s' for account '%s'.",
                    permission,
                    self.token_filename,
                    self._config[CONF_ACCOUNT_NAME],
                )

    def _build_token_filename(self):
        """Create the token file name."""
        config_file = (
            f"_{self._config.get(CONF_ACCOUNT_NAME)}"
            if self._conf_type == CONST_CONFIG_TYPE_LIST
            else ""
        )
        return TOKEN_FILENAME.format(config_file)

    def _get_permissions(self):
        """Get the permissions from the token file."""
        full_token_path = os.path.join(self.token_path, self.token_filename)
        if not os.path.exists(full_token_path) or not os.path.isfile(full_token_path):
            _LOGGER.warning("Could not locate token at %s", full_token_path)
            return TOKEN_FILE_MISSING
        with open(full_token_path, "r", encoding="UTF-8") as file_handle:
            raw = file_handle.read()
            permissions = json.loads(raw)["scope"]

        return permissions

    def _build_email_min_permissions(self):
        email_sensors = self._config.get(CONF_EMAIL_SENSORS, [])
        query_sensors = self._config.get(CONF_QUERY_SENSORS, [])
        if len(email_sensors) > 0 or len(query_sensors) > 0:
            self._minimum_permissions.append(self._add_shared(PERM_MINIMUM_MAIL))

    def _build_status_min_permissions(self):
        status_sensors = self._config.get(CONF_STATUS_SENSORS, [])
        if len(status_sensors) > 0:
            if any(status_sensor.get(CONF_EMAIL) for status_sensor in status_sensors):
                self._minimum_permissions.append(PERM_MINIMUM_PRESENCE_ALL)
            if any(
                status_sensor.get(CONF_EMAIL) is None
                for status_sensor in status_sensors
            ):
                self._minimum_permissions.append(PERM_MINIMUM_PRESENCE)

    def _build_chat_min_permissions(self):
        chat_sensors = self._config.get(CONF_CHAT_SENSORS, [])
        if len(chat_sensors) > 0:
            self._minimum_permissions.append(PERM_MINIMUM_CHAT)

    def _build_todo_min_permissions(self):
        todo_sensors = self._config.get(CONF_TODO_SENSORS, [])
        if len(todo_sensors) > 0 and todo_sensors.get(CONF_ENABLED, False):
            self._minimum_permissions.append(PERM_MINIMUM_TASKS)

    def _build_autoreply_min_permissions(self):
        auto_reply_sensors = self._config.get(CONF_AUTO_REPLY_SENSORS, [])
        if len(auto_reply_sensors) > 0:
            self._minimum_permissions.append(PERM_MINIMUM_MAILBOX_SETTINGS)

    def _build_group_min_permssions(self):
        if self._group_permissions_required():
            self._minimum_permissions.append(PERM_MINIMUM_GROUP)

    def _add_shared(self, minimum_permissions):
        if not self._shared:
            return minimum_permissions

        if self._shared not in minimum_permissions[0]:
            minimum_permissions[0] = minimum_permissions[0] + self._shared
        alt_permissions = []
        for permission in minimum_permissions[1]:
            if self._shared not in permission:
                permission = permission + self._shared
            if permission not in alt_permissions:
                alt_permissions.append(permission)

        minimum_permissions[1] = alt_permissions
        return minimum_permissions

    def _group_permissions_required(self):
        """Return if group permissions are required."""
        yaml_filename = build_yaml_filename(
            self._config, YAML_CALENDARS_FILENAME, self._conf_type
        )
        calendars = load_yaml_file(
            build_config_file_path(self._hass, yaml_filename),
            CONF_CAL_ID,
            YAML_CALENDAR_DEVICE_SCHEMA,
        )
        for cal_id, calendar in calendars.items():
            if cal_id.startswith(CONST_GROUP):
                for entity in calendar.get(CONF_ENTITIES):
                    if entity[CONF_TRACK]:
                        return True
        return False

    def _build_calendar_permissions(self):
        if self._config.get(CONF_BASIC_CALENDAR, False):
            if self._enable_update:
                _LOGGER.warning(
                    "'enable_update' should not be true when 'basic_calendar' is true ."
                    + "for account: %s ReadBasic used. ",
                    self._config[CONF_ACCOUNT_NAME],
                )
            self._requested_permissions.append(PERM_CALENDARS_READBASIC + self._shared)
        elif self._enable_update:
            self._requested_permissions.extend(
                (PERM_MAIL_SEND + self._shared, PERM_CALENDARS_READWRITE + self._shared)
            )
        else:
            self._requested_permissions.append(PERM_CALENDARS_READ + self._shared)

    def _build_group_permissions(self):
        if self._config.get(CONF_GROUPS, False):
            if self._enable_update:
                self._requested_permissions.append(PERM_GROUP_READWRITE_ALL)
            else:
                self._requested_permissions.append(PERM_GROUP_READ_ALL)

    def _build_email_permissions(self):
        email_sensors = self._config.get(CONF_EMAIL_SENSORS, [])
        query_sensors = self._config.get(CONF_QUERY_SENSORS, [])
        if len(email_sensors) > 0 or len(query_sensors) > 0:
            self._requested_permissions.append(PERM_MAIL_READ + self._shared)

    def _build_autoreply_permissions(self):
        auto_reply_sensors = self._config.get(CONF_AUTO_REPLY_SENSORS, [])
        if len(auto_reply_sensors) > 0:
            self._requested_permissions.append(PERM_MAILBOX_SETTINGS)

    def _build_status_permissions(self):
        status_sensors = self._config.get(CONF_STATUS_SENSORS, [])
        if len(status_sensors) > 0:
            if any(
                status_sensor.get(CONF_ENABLE_UPDATE)
                for status_sensor in status_sensors
            ):
                self._requested_permissions.append(PERM_PRESENCE_READWRITE)
            else:
                self._requested_permissions.append(PERM_PRESENCE_READ)
            if any(status_sensor.get(CONF_EMAIL) for status_sensor in status_sensors):
                self._requested_permissions.append(PERM_PRESENCE_READ_ALL)

    def _build_chat_permissions(self):
        chat_sensors = self._config.get(CONF_CHAT_SENSORS, [])
        if len(chat_sensors) > 0:
            if chat_sensors[0][CONF_ENABLE_UPDATE]:
                self._requested_permissions.append(PERM_CHAT_READWRITE)
            else:
                self._requested_permissions.append(PERM_CHAT_READ)

    def _build_todo_permissions(self):
        todo_sensors = self._config.get(CONF_TODO_SENSORS, [])
        if todo_sensors and todo_sensors.get(CONF_ENABLED, False):
            if todo_sensors[CONF_ENABLE_UPDATE]:
                self._requested_permissions.append(PERM_TASKS_READWRITE)
            else:
                self._requested_permissions.append(PERM_TASKS_READ)
