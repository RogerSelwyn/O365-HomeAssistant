"""Permissions processes."""
import json
import logging
import os

from homeassistant.const import CONF_ENABLED

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
    CONST_GROUP,
    DEFAULT_CACHE_PATH,
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
    PERM_MINIMUM_TASKS,
    PERM_MINIMUM_USER,
    PERM_OFFLINE_ACCESS,
    PERM_PRESENCE_READ,
    PERM_SHARED,
    PERM_TASKS_READ,
    PERM_TASKS_READWRITE,
    PERM_USER_READ,
    TOKEN_FILE_MISSING,
    TOKEN_FILENAME,
    YAML_CALENDARS,
)
from ..schema import CALENDAR_DEVICE_SCHEMA
from .filemgmt import build_config_file_path, build_yaml_filename, load_yaml_file

_LOGGER = logging.getLogger(__name__)


def build_minimum_permissions(hass, config, conf_type):
    """Build the minimum permissions required to operate."""
    scope = MinumumPermissions(hass, config, conf_type).scope
    return scope


def build_requested_permissions(config):
    """Build the requested permissions for the scope."""
    scope = RequiredPermissions(config).scope
    return scope


def validate_permissions(
    hass, minimum_permissions, token_path=DEFAULT_CACHE_PATH, filename=TOKEN_FILENAME
):
    """Validate the permissions."""
    permissions = get_permissions(hass, token_path=token_path, filename=filename)
    if permissions == TOKEN_FILE_MISSING:
        return TOKEN_FILE_MISSING, None

    failed_permissions = []
    for minimum_perm in minimum_permissions:
        permission_granted = validate_minimum_permission(minimum_perm, permissions)
        if not permission_granted:
            failed_permissions.append(minimum_perm[0])

    if failed_permissions:
        _LOGGER.warning(
            "Minimum required permissions not granted: %s",
            ", ".join(failed_permissions),
        )
        return False, failed_permissions

    return True, None


def validate_minimum_permission(minimum_perm, permissions):
    """Validate the minimum permissions."""
    if minimum_perm[0] in permissions:
        return True

    return any(alternate_perm in permissions for alternate_perm in minimum_perm[1])


def get_permissions(hass, token_path=DEFAULT_CACHE_PATH, filename=TOKEN_FILENAME):
    """Get the permissions from the token file."""
    config_path = build_config_file_path(hass, token_path)
    full_token_path = os.path.join(config_path, filename)
    if not os.path.exists(full_token_path) or not os.path.isfile(full_token_path):
        _LOGGER.warning("Could not locate token at %s", full_token_path)
        return TOKEN_FILE_MISSING
    with open(full_token_path, "r", encoding="UTF-8") as file_handle:
        raw = file_handle.read()
        permissions = json.loads(raw)["scope"]

    return permissions


class RequiredPermissions:
    """Class in support of building required permssions."""

    def __init__(self, config):
        """Initialise the class."""
        self._config = config
        self._enable_update = self._config.get(CONF_ENABLE_UPDATE, False)
        self._scope = [PERM_OFFLINE_ACCESS, PERM_USER_READ]
        self._shared = PERM_SHARED if self._config.get(CONF_SHARED_MAILBOX) else ""

    @property
    def scope(self):
        """Return the required scope."""
        self._build_calendar_permissions()
        self._build_group_permissions()
        self._build_email_permissions()
        self._build_autoreply_permissions()
        self._build_status_permissions()
        self._build_chat_permissions()
        self._build_todo_permissions()
        return self._scope

    def _build_calendar_permissions(self):
        if self._config.get(CONF_BASIC_CALENDAR, False):
            if self._enable_update:
                _LOGGER.warning(
                    "'enable_update' should not be true when 'basic_calendar' is true ."
                    + "for account: %s ReadBasic used. ",
                    self._config[CONF_ACCOUNT_NAME],
                )
            self._scope.append(PERM_CALENDARS_READBASIC + self._shared)
        elif self._enable_update:
            self._scope.extend(
                (PERM_MAIL_SEND + self._shared, PERM_CALENDARS_READWRITE + self._shared)
            )
        else:
            self._scope.append(PERM_CALENDARS_READ + self._shared)

    def _build_group_permissions(self):
        if self._config.get(CONF_GROUPS, False):
            if self._enable_update:
                self._scope.append(PERM_GROUP_READWRITE_ALL)
            else:
                self._scope.append(PERM_GROUP_READ_ALL)

    def _build_email_permissions(self):
        email_sensors = self._config.get(CONF_EMAIL_SENSORS, [])
        query_sensors = self._config.get(CONF_QUERY_SENSORS, [])
        if len(email_sensors) > 0 or len(query_sensors) > 0:
            self._scope.append(PERM_MAIL_READ + self._shared)

    def _build_autoreply_permissions(self):
        auto_reply_sensors = self._config.get(CONF_AUTO_REPLY_SENSORS, [])
        if len(auto_reply_sensors) > 0:
            self._scope.append(PERM_MAILBOX_SETTINGS)

    def _build_status_permissions(self):
        status_sensors = self._config.get(CONF_STATUS_SENSORS, [])
        if len(status_sensors) > 0:
            self._scope.append(PERM_PRESENCE_READ)

    def _build_chat_permissions(self):
        chat_sensors = self._config.get(CONF_CHAT_SENSORS, [])
        if len(chat_sensors) > 0:
            if chat_sensors[0][CONF_ENABLE_UPDATE]:
                self._scope.append(PERM_CHAT_READWRITE)
            else:
                self._scope.append(PERM_CHAT_READ)

    def _build_todo_permissions(self):
        todo_sensors = self._config.get(CONF_TODO_SENSORS, [])
        if todo_sensors and todo_sensors.get(CONF_ENABLED, False):
            if todo_sensors[CONF_ENABLE_UPDATE]:
                self._scope.append(PERM_TASKS_READWRITE)
            else:
                self._scope.append(PERM_TASKS_READ)


class MinumumPermissions:
    """Class in support of building minimum permssions."""

    def __init__(self, hass, config, conf_type):
        """Initialise the class."""
        self._hass = hass
        self._config = config
        self._conf_type = conf_type

        self._shared = PERM_SHARED if config.get(CONF_SHARED_MAILBOX) else None
        self._minimum_permissions = [
            PERM_MINIMUM_USER,
            self._add_shared(PERM_MINIMUM_CALENDAR),
        ]

    @property
    def scope(self):
        """Return the required scope."""
        self._build_email_permissions()
        self._build_status_permissions()
        self._build_chat_permissions()
        self._build_todo_permissions()
        self._build_autoreply_permissions()
        self._build_group_permssions()
        return self._minimum_permissions

    def _build_email_permissions(self):
        email_sensors = self._config.get(CONF_EMAIL_SENSORS, [])
        query_sensors = self._config.get(CONF_QUERY_SENSORS, [])
        if len(email_sensors) > 0 or len(query_sensors) > 0:
            self._minimum_permissions.append(self._add_shared(PERM_MINIMUM_MAIL))

    def _build_status_permissions(self):
        status_sensors = self._config.get(CONF_STATUS_SENSORS, [])
        if len(status_sensors) > 0:
            self._minimum_permissions.append(PERM_MINIMUM_PRESENCE)

    def _build_chat_permissions(self):
        chat_sensors = self._config.get(CONF_CHAT_SENSORS, [])
        if len(chat_sensors) > 0:
            self._minimum_permissions.append(PERM_MINIMUM_CHAT)

    def _build_todo_permissions(self):
        todo_sensors = self._config.get(CONF_TODO_SENSORS, [])
        if len(todo_sensors) > 0 and todo_sensors.get(CONF_ENABLED, False):
            self._minimum_permissions.append(PERM_MINIMUM_TASKS)

    def _build_autoreply_permissions(self):
        auto_reply_sensors = self._config.get(CONF_AUTO_REPLY_SENSORS, [])
        if len(auto_reply_sensors) > 0:
            self._minimum_permissions.append(PERM_MINIMUM_MAILBOX_SETTINGS)

    def _build_group_permssions(self):
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
            self._config, YAML_CALENDARS, self._conf_type
        )
        calendars = load_yaml_file(
            build_config_file_path(self._hass, yaml_filename),
            CONF_CAL_ID,
            CALENDAR_DEVICE_SCHEMA,
        )
        for cal_id, calendar in calendars.items():
            if cal_id.startswith(CONST_GROUP):
                for entity in calendar.get(CONF_ENTITIES):
                    if entity[CONF_TRACK]:
                        return True
        return False
