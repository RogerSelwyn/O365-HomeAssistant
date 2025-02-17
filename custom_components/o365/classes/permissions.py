"""Permissions processes."""

import json
import logging
import os
from copy import deepcopy

from homeassistant.const import CONF_EMAIL, CONF_ENABLED

from ..const import (
    CONF_ACCOUNT_NAME,
    CONF_AUTO_REPLY_SENSORS,
    CONF_BASIC_CALENDAR,
    CONF_CHAT_SENSORS,
    CONF_EMAIL_SENSORS,
    CONF_ENABLE_CALENDAR,
    CONF_ENABLE_UPDATE,
    CONF_GROUPS,
    CONF_QUERY_SENSORS,
    CONF_SHARED_MAILBOX,
    CONF_STATUS_SENSORS,
    CONF_TODO_SENSORS,
    CONST_CONFIG_TYPE_LIST,
    O365_STORAGE_TOKEN,
    PERM_BASE_PERMISSIONS,
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
    PERM_PRESENCE_READ,
    PERM_PRESENCE_READ_ALL,
    PERM_PRESENCE_READWRITE,
    PERM_SHARED,
    PERM_TASKS_READ,
    PERM_TASKS_READWRITE,
    PERM_USER_READBASIC_ALL,
    TOKEN_FILE_CORRUPTED,
    TOKEN_FILE_MISSING,
    TOKEN_FILE_OUTDATED,
    TOKEN_FILE_PERMISSIONS,
    TOKEN_FILENAME,
)
from ..utils.filemgmt import build_config_file_path

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
        self._requested_permissions = []
        self.token_filename = self._build_token_filename()
        self.token_path = build_config_file_path(self._hass, O365_STORAGE_TOKEN)
        self._permissions = []

    @property
    def requested_permissions(self):
        """Return the required scope."""
        if not self._requested_permissions:
            self._requested_permissions = deepcopy(PERM_BASE_PERMISSIONS)
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
        return self._permissions

    async def async_check_authorizations(self):
        """Report on permissions status."""
        self._permissions = await self._hass.async_add_executor_job(
            self._get_permissions
        )

        if self._permissions in [
            TOKEN_FILE_MISSING,
            TOKEN_FILE_CORRUPTED,
            TOKEN_FILE_OUTDATED,
        ]:
            return self._permissions, None
        failed_permissions = []
        for permission in self.requested_permissions:
            if not self.validate_authorization(permission):
                failed_permissions.append(permission)

        if failed_permissions:
            _LOGGER.warning(
                "Minimum required permissions: '%s'. Not available in token '%s' for account '%s'.",
                ", ".join(failed_permissions),
                self.token_filename,
                self._config[CONF_ACCOUNT_NAME],
            )
            return TOKEN_FILE_PERMISSIONS, failed_permissions

        return True, None

    def validate_authorization(self, permission):
        """Validate higher permissions."""
        if permission in self.permissions:
            return True

        if self._check_higher_permissions(permission):
            return True

        resource = permission.split(".")[0]
        constraint = permission.split(".")[1] if len(permission) == 3 else None

        # If Calendar or Mail Resource then permissions can have a constraint of .Shared
        # which includes base as well. e.g. Calendar.Read is also enabled by Calendar.Read.Shared
        if not constraint and resource in ["Calendar", "Mail"]:
            sharedpermission = f"{deepcopy(permission)}.Shared"
            return self._check_higher_permissions(sharedpermission)
        # If Presence Resource then permissions can have a constraint of .All
        # which includes base as well. e.g. Presencedar.Read is also enabled by Presence.Read.All
        if not constraint and resource in ["Presence"]:
            allpermission = f"{deepcopy(permission)}.All"
            return self._check_higher_permissions(allpermission)

        return False

    def _check_higher_permissions(self, permission):
        operation = permission.split(".")[1]
        # If Operation is ReadBasic then Read or ReadWrite will also work
        # If Operation is Read then ReadWrite will also work
        newops = [operation]
        if operation == "ReadBasic":
            newops = newops + ["Read", "ReadWrite"]
        elif operation == "Read":
            newops = newops + ["ReadWrite"]

        for newop in newops:
            newperm = deepcopy(permission).replace(operation, newop)
            if newperm in self.permissions:
                return True

        return False

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
        try:
            with open(full_token_path, "r", encoding="UTF-8") as file_handle:
                raw = file_handle.read()
                permissions = next(iter(json.loads(raw)["AccessToken"].values()))[
                    "target"
                ].split()
        except json.decoder.JSONDecodeError as err:
            _LOGGER.warning("Token corrupted at %s - %s", full_token_path, err)
            return TOKEN_FILE_CORRUPTED
        except KeyError:
            _LOGGER.warning(
                "Legacy token found at %s, it has been deleted", full_token_path
            )
            self.delete_token()
            return TOKEN_FILE_OUTDATED
        return permissions

    def _build_calendar_permissions(self):
        if not self._config.get(CONF_ENABLE_CALENDAR, True):
            return

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
                self._requested_permissions.append(PERM_USER_READBASIC_ALL)

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

    def delete_token(self):
        """Delete the token."""
        full_token_path = os.path.join(self.token_path, self.token_filename)
        if os.path.exists(full_token_path):
            os.remove(full_token_path)
