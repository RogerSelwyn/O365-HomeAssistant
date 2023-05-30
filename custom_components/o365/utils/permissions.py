"""Permissions processes."""
import json
import logging
import os

from homeassistant.const import CONF_ENABLED

from ..const import (
    CONF_AUTO_REPLY_SENSORS,
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
    TOKEN_FILENAME,
    YAML_CALENDARS,
)
from ..schema import CALENDAR_DEVICE_SCHEMA
from .filemgmt import build_config_file_path, build_yaml_filename, load_yaml_file

_LOGGER = logging.getLogger(__name__)


def build_minimum_permissions(hass, config, conf_type):
    """Build the minimum permissions required to operate."""
    email_sensors = config.get(CONF_EMAIL_SENSORS, [])
    query_sensors = config.get(CONF_QUERY_SENSORS, [])
    status_sensors = config.get(CONF_STATUS_SENSORS, [])
    chat_sensors = config.get(CONF_CHAT_SENSORS, [])
    todo_sensors = config.get(CONF_TODO_SENSORS, [])
    auto_reply_sensors = config.get(CONF_AUTO_REPLY_SENSORS, [])
    shared = PERM_SHARED if config.get(CONF_SHARED_MAILBOX) else None
    minimum_permissions = [
        PERM_MINIMUM_USER,
        _add_shared(PERM_MINIMUM_CALENDAR, shared),
    ]
    if len(email_sensors) > 0 or len(query_sensors) > 0:
        minimum_permissions.append(_add_shared(PERM_MINIMUM_MAIL, shared))
    if len(status_sensors) > 0:
        minimum_permissions.append(PERM_MINIMUM_PRESENCE)
    if len(chat_sensors) > 0:
        minimum_permissions.append(PERM_MINIMUM_CHAT)
    if len(todo_sensors) > 0 and todo_sensors.get(CONF_ENABLED, False):
        minimum_permissions.append(PERM_MINIMUM_TASKS)
    if len(auto_reply_sensors) > 0:
        minimum_permissions.append(PERM_MINIMUM_MAILBOX_SETTINGS)

    if group_permissions_required(hass, config, conf_type):
        minimum_permissions.append(PERM_MINIMUM_GROUP)

    return minimum_permissions


def _add_shared(minimum_permissions, shared):
    if not shared:
        return minimum_permissions

    if shared not in minimum_permissions[0]:
        minimum_permissions[0] = minimum_permissions[0] + shared
    alt_permissions = []
    for permission in minimum_permissions[1]:
        if shared not in permission:
            permission = permission + shared
        if permission not in alt_permissions:
            alt_permissions.append(permission)

    minimum_permissions[1] = alt_permissions
    return minimum_permissions


def build_requested_permissions(config):
    """Build the requested permissions for the scope."""
    email_sensors = config.get(CONF_EMAIL_SENSORS, [])
    query_sensors = config.get(CONF_QUERY_SENSORS, [])
    status_sensors = config.get(CONF_STATUS_SENSORS, [])
    chat_sensors = config.get(CONF_CHAT_SENSORS, [])
    todo_sensors = config.get(CONF_TODO_SENSORS, [])
    enable_update = config.get(CONF_ENABLE_UPDATE, True)
    groups = config.get(CONF_GROUPS, False)
    auto_reply_sensors = config.get(CONF_AUTO_REPLY_SENSORS, [])
    scope = [PERM_OFFLINE_ACCESS, PERM_USER_READ]
    shared = PERM_SHARED if config.get(CONF_SHARED_MAILBOX) else ""
    if enable_update:
        scope.extend((PERM_MAIL_SEND + shared, PERM_CALENDARS_READWRITE + shared))
    else:
        scope.append(PERM_CALENDARS_READ + shared)
    if groups:
        if enable_update:
            scope.append(PERM_GROUP_READWRITE_ALL)
        else:
            scope.append(PERM_GROUP_READ_ALL)
    if len(email_sensors) > 0 or len(query_sensors) > 0:
        scope.append(PERM_MAIL_READ + shared)
    if len(auto_reply_sensors) > 0:
        scope.append(PERM_MAILBOX_SETTINGS)
    if len(status_sensors) > 0:
        scope.append(PERM_PRESENCE_READ)
    if len(chat_sensors) > 0:
        if chat_sensors[0][CONF_ENABLE_UPDATE]:
            scope.append(PERM_CHAT_READWRITE)
        else:
            scope.append(PERM_CHAT_READ)
    if todo_sensors and todo_sensors.get(CONF_ENABLED, False):
        if todo_sensors[CONF_ENABLE_UPDATE]:
            scope.append(PERM_TASKS_READWRITE)
        else:
            scope.append(PERM_TASKS_READ)

    return scope


def group_permissions_required(hass, config, conf_type):
    """Return if group permissions are required."""
    yaml_filename = build_yaml_filename(config, YAML_CALENDARS, conf_type)
    calendars = load_yaml_file(
        build_config_file_path(hass, yaml_filename), CONF_CAL_ID, CALENDAR_DEVICE_SCHEMA
    )
    for cal_id, calendar in calendars.items():
        if cal_id.startswith(CONST_GROUP):
            for entity in calendar.get(CONF_ENTITIES):
                if entity[CONF_TRACK]:
                    return True
    return False


def validate_permissions(
    hass, minimum_permissions, token_path=DEFAULT_CACHE_PATH, filename=TOKEN_FILENAME
):
    """Validate the permissions."""
    permissions = get_permissions(hass, token_path=token_path, filename=filename)
    if not permissions:
        return False, None

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
        return []
    with open(full_token_path, "r", encoding="UTF-8") as file_handle:
        raw = file_handle.read()
        permissions = json.loads(raw)["scope"]

    return permissions
