"""Schema for O365 Integration."""

import datetime
from collections.abc import Callable
from itertools import groupby
from typing import Any

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.components.notify import (
    ATTR_DATA,
    ATTR_MESSAGE,
    ATTR_TARGET,
    ATTR_TITLE,
)
from homeassistant.const import CONF_EMAIL, CONF_ENABLED, CONF_NAME
from homeassistant.util import dt as dt_util
from O365.calendar import (  # pylint: disable=no-name-in-module
    AttendeeType,
    EventSensitivity,
    EventShowAs,
)
from O365.mailbox import (  # pylint: disable=no-name-in-module, import-error
    ExternalAudience,
)
from O365.teams import (  # pylint: disable=import-error, no-name-in-module
    Activity,
    Availability,
    PreferredAvailability,
)
from O365.utils import ImportanceLevel  # pylint: disable=no-name-in-module

from .const import (
    ATTR_ACTIVITY,
    ATTR_ATTACHMENTS,
    ATTR_ATTENDEES,
    ATTR_AVAILABILITY,
    ATTR_BODY,
    ATTR_CATEGORIES,
    ATTR_CHAT_ID,
    ATTR_COMPLETED,
    ATTR_CONTENT_TYPE,
    ATTR_DESCRIPTION,
    ATTR_DUE,
    ATTR_EMAIL,
    ATTR_END,
    ATTR_EVENT_ID,
    ATTR_EXPIRATIONDURATION,
    ATTR_EXTERNAL_AUDIENCE,
    ATTR_EXTERNALREPLY,
    ATTR_IMPORTANCE,
    ATTR_INTERNALREPLY,
    ATTR_IS_ALL_DAY,
    ATTR_LOCATION,
    ATTR_MESSAGE_IS_HTML,
    ATTR_PHOTOS,
    ATTR_REMINDER,
    ATTR_RESPONSE,
    ATTR_SEND_RESPONSE,
    ATTR_SENDER,
    ATTR_SENSITIVITY,
    ATTR_SHOW_AS,
    ATTR_START,
    ATTR_SUBJECT,
    ATTR_TODO_ID,
    ATTR_TYPE,
    ATTR_ZIP_ATTACHMENTS,
    ATTR_ZIP_NAME,
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
    CONF_DEVICE_ID,
    CONF_DOWNLOAD_ATTACHMENTS,
    CONF_DUE_HOURS_BACKWARD_TO_GET,
    CONF_DUE_HOURS_FORWARD_TO_GET,
    CONF_EMAIL_SENSORS,
    CONF_ENABLE_CALENDAR,
    CONF_ENABLE_UPDATE,
    CONF_ENTITIES,
    CONF_EXCLUDE,
    CONF_GROUPS,
    CONF_HAS_ATTACHMENT,
    CONF_HOURS_BACKWARD_TO_GET,
    CONF_HOURS_FORWARD_TO_GET,
    CONF_HTML_BODY,
    CONF_IMPORTANCE,
    CONF_IS_UNREAD,
    CONF_MAIL_FOLDER,
    CONF_MAIL_FROM,
    CONF_MAX_ITEMS,
    CONF_MAX_RESULTS,
    CONF_QUERY_SENSORS,
    CONF_SEARCH,
    CONF_SHARED_MAILBOX,
    CONF_SHOW_BODY,
    CONF_SHOW_COMPLETED,
    CONF_STATUS_SENSORS,
    CONF_SUBJECT_CONTAINS,
    CONF_SUBJECT_IS,
    CONF_TODO_SENSORS,
    CONF_TRACK,
    CONF_TRACK_NEW,
    CONF_TRACK_NEW_CALENDAR,
    CONF_URL,
    CONF_YAML_TASK_LIST_ID,
    CONTENT_TYPES,
    EventResponse,
)


def _has_consistent_timezone(*keys: Any) -> Callable[[dict[str, Any]], dict[str, Any]]:
    """Verify that all datetime values have a consistent timezone."""

    def validate(obj: dict[str, Any]) -> dict[str, Any]:
        """Test that all keys that are datetime values have the same timezone."""
        tzinfos = []
        for key in keys:
            if not (value := obj.get(key)) or not isinstance(value, datetime.datetime):
                return obj
            tzinfos.append(value.tzinfo)
        uniq_values = groupby(tzinfos)
        if len(list(uniq_values)) > 1:
            raise vol.Invalid("Expected all values to have the same timezone")
        return obj

    return validate


def _as_local_timezone(*keys: Any) -> Callable[[dict[str, Any]], dict[str, Any]]:
    """Convert all datetime values to the local timezone."""

    def validate(obj: dict[str, Any]) -> dict[str, Any]:
        """Convert all keys that are datetime values to local timezone."""
        for k in keys:
            if (value := obj.get(k)) and isinstance(value, datetime.datetime):
                obj[k] = dt_util.as_local(value)
        return obj

    return validate


EMAIL_SENSOR = vol.Schema(
    {
        vol.Required(CONF_NAME): cv.string,
        vol.Optional(CONF_MAIL_FOLDER): cv.string,
        vol.Optional(CONF_MAX_ITEMS, default=5): int,
        vol.Optional(CONF_IS_UNREAD): bool,
        vol.Optional(CONF_DOWNLOAD_ATTACHMENTS, default=True): bool,
        vol.Optional(CONF_HTML_BODY, default=False): bool,
        vol.Optional(CONF_SHOW_BODY, default=True): bool,
    }
)
STATUS_SENSOR = vol.Schema(
    vol.All(
        {
            vol.Required(CONF_NAME): cv.string,
            vol.Optional(CONF_ENABLE_UPDATE, None): bool,
            vol.Optional(CONF_EMAIL, None): cv.string,
        },
        cv.has_at_most_one_key(CONF_ENABLE_UPDATE, CONF_EMAIL),
    )
)
CHAT_SENSOR = vol.Schema(
    {
        vol.Required(CONF_NAME): cv.string,
        vol.Optional(CONF_ENABLE_UPDATE, default=False): bool,
    }
)
AUTO_REPLY_SENSOR = vol.Schema(
    {
        vol.Required(CONF_NAME): cv.string,
    }
)
QUERY_SENSOR = vol.Schema(
    {
        vol.Required(CONF_NAME): cv.string,
        vol.Optional(CONF_MAIL_FOLDER): cv.string,
        vol.Optional(CONF_MAIL_FROM): cv.string,
        vol.Optional(CONF_MAX_ITEMS, default=5): int,
        vol.Optional(CONF_HAS_ATTACHMENT): bool,
        vol.Optional(CONF_IMPORTANCE): cv.string,
        vol.Optional(CONF_IS_UNREAD): bool,
        vol.Exclusive(CONF_BODY_CONTAINS, "body_*"): cv.string,
        vol.Exclusive(CONF_SUBJECT_CONTAINS, "subject_*"): cv.string,
        vol.Exclusive(CONF_SUBJECT_IS, "subject_*"): cv.string,
        vol.Optional(CONF_DOWNLOAD_ATTACHMENTS, default=True): bool,
        vol.Optional(CONF_HTML_BODY, default=False): bool,
        vol.Optional(CONF_SHOW_BODY, default=True): bool,
    }
)
TODO_SENSOR = vol.Schema(
    {
        vol.Required(CONF_ENABLED, default=False): bool,
        vol.Optional(CONF_TRACK_NEW, default=True): bool,
        vol.Optional(CONF_ENABLE_UPDATE, default=False): bool,
    }
)

MULTI_ACCOUNT_SCHEMA = vol.Schema(
    {
        CONF_ACCOUNTS: vol.Schema(
            [
                {
                    vol.Required(CONF_CLIENT_ID): cv.string,
                    vol.Required(CONF_CLIENT_SECRET): cv.string,
                    vol.Optional(CONF_TRACK_NEW_CALENDAR, default=True): bool,
                    vol.Optional(CONF_ENABLE_CALENDAR, default=True): bool,
                    vol.Optional(CONF_ENABLE_UPDATE, default=False): bool,
                    vol.Optional(CONF_GROUPS, default=False): bool,
                    vol.Required(CONF_ACCOUNT_NAME, ""): cv.string,
                    vol.Optional(CONF_ALT_AUTH_METHOD, default=False): bool,
                    vol.Optional(CONF_BASIC_CALENDAR, default=False): bool,
                    vol.Optional(CONF_EMAIL_SENSORS): [EMAIL_SENSOR],
                    vol.Optional(CONF_QUERY_SENSORS): [QUERY_SENSOR],
                    vol.Optional(CONF_STATUS_SENSORS): [STATUS_SENSOR],
                    vol.Optional(CONF_CHAT_SENSORS): [CHAT_SENSOR],
                    vol.Optional(CONF_TODO_SENSORS): TODO_SENSOR,
                    vol.Optional(CONF_AUTO_REPLY_SENSORS): [AUTO_REPLY_SENSOR],
                    vol.Optional(CONF_SHARED_MAILBOX, None): cv.string,
                }
            ]
        )
    }
)

NOTIFY_SERVICE_DATA_SCHEMA = vol.Schema(
    {
        vol.Optional(ATTR_MESSAGE_IS_HTML, default=False): bool,
        vol.Optional(ATTR_TARGET): cv.string,
        vol.Optional(ATTR_SENDER): cv.string,
        vol.Optional(ATTR_ZIP_ATTACHMENTS, default=False): bool,
        vol.Optional(ATTR_ZIP_NAME): cv.string,
        vol.Optional(ATTR_PHOTOS, default=[]): [cv.string],
        vol.Optional(ATTR_ATTACHMENTS, default=[]): [cv.string],
        vol.Optional(ATTR_IMPORTANCE): vol.Coerce(ImportanceLevel),
    }
)

NOTIFY_SERVICE_BASE_SCHEMA = vol.Schema(
    {
        vol.Optional(ATTR_TARGET, default=[]): [cv.string],
        vol.Optional(ATTR_TITLE, default=""): cv.string,
        vol.Optional(ATTR_DATA): NOTIFY_SERVICE_DATA_SCHEMA,
    }
)

CALENDAR_SERVICE_RESPOND_SCHEMA = {
    vol.Required(ATTR_EVENT_ID): cv.string,
    vol.Required(ATTR_RESPONSE, None): cv.enum(EventResponse),
    vol.Optional(ATTR_SEND_RESPONSE, True): bool,
    vol.Optional(ATTR_MESSAGE, None): cv.string,
}

CALENDAR_SERVICE_ATTENDEE_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_EMAIL): cv.string,
        vol.Required(ATTR_TYPE): cv.enum(AttendeeType),
    }
)

CALENDAR_SERVICE_CREATE_SCHEMA = vol.All(
    cv.make_entity_service_schema(
        {
            vol.Required(ATTR_SUBJECT): cv.string,
            vol.Required(ATTR_START): cv.datetime,
            vol.Required(ATTR_END): cv.datetime,
            vol.Optional(ATTR_BODY): cv.string,
            vol.Optional(ATTR_LOCATION): cv.string,
            vol.Optional(ATTR_CATEGORIES): [cv.string],
            vol.Optional(ATTR_SENSITIVITY): vol.Coerce(EventSensitivity),
            vol.Optional(ATTR_SHOW_AS): vol.Coerce(EventShowAs),
            vol.Optional(ATTR_IS_ALL_DAY): bool,
            vol.Optional(ATTR_ATTENDEES): [CALENDAR_SERVICE_ATTENDEE_SCHEMA],
        }
    ),
    _has_consistent_timezone(ATTR_START, ATTR_END),
    _as_local_timezone(ATTR_START, ATTR_END),
)

CALENDAR_SERVICE_MODIFY_SCHEMA = vol.All(
    cv.make_entity_service_schema(
        {
            vol.Required(ATTR_EVENT_ID): cv.string,
            vol.Optional(ATTR_START): cv.datetime,
            vol.Optional(ATTR_END): cv.datetime,
            vol.Optional(ATTR_SUBJECT): cv.string,
            vol.Optional(ATTR_BODY): cv.string,
            vol.Optional(ATTR_LOCATION): cv.string,
            vol.Optional(ATTR_CATEGORIES): [cv.string],
            vol.Optional(ATTR_SENSITIVITY): vol.Coerce(EventSensitivity),
            vol.Optional(ATTR_SHOW_AS): vol.Coerce(EventShowAs),
            vol.Optional(ATTR_IS_ALL_DAY): bool,
            vol.Optional(ATTR_ATTENDEES): [CALENDAR_SERVICE_ATTENDEE_SCHEMA],
        }
    ),
    _has_consistent_timezone(ATTR_START, ATTR_END),
    _as_local_timezone(ATTR_START, ATTR_END),
)


CALENDAR_SERVICE_REMOVE_SCHEMA = {
    vol.Required(ATTR_EVENT_ID): cv.string,
}

STATUS_SERVICE_UPDATE_USER_STATUS_SCHEMA = {
    vol.Required(ATTR_AVAILABILITY): vol.Coerce(Availability),
    vol.Required(ATTR_ACTIVITY): vol.Coerce(Activity),
    vol.Optional(ATTR_EXPIRATIONDURATION): cv.string,
}

STATUS_SERVICE_UPDATE_USER_PERERRED_STATUS_SCHEMA = {
    vol.Required(ATTR_AVAILABILITY): vol.Coerce(PreferredAvailability),
    vol.Optional(ATTR_EXPIRATIONDURATION): cv.string,
}

TODO_SERVICE_NEW_SCHEMA = {
    vol.Required(ATTR_SUBJECT): cv.string,
    vol.Optional(ATTR_DESCRIPTION): cv.string,
    vol.Optional(ATTR_DUE): cv.date,
    vol.Optional(ATTR_REMINDER): vol.Any(cv.date, cv.datetime),
}

TODO_SERVICE_UPDATE_SCHEMA = {
    vol.Required(ATTR_TODO_ID): cv.string,
    vol.Optional(ATTR_SUBJECT): cv.string,
    vol.Optional(ATTR_DESCRIPTION): cv.string,
    vol.Optional(ATTR_DUE): cv.date,
    vol.Optional(ATTR_REMINDER): vol.Any(cv.date, cv.datetime),
}

TODO_SERVICE_DELETE_SCHEMA = {
    vol.Required(ATTR_TODO_ID): cv.string,
}
TODO_SERVICE_COMPLETE_SCHEMA = {
    vol.Required(ATTR_TODO_ID): cv.string,
    vol.Required(ATTR_COMPLETED): bool,
}

AUTO_REPLY_SERVICE_ENABLE_SCHEMA = {
    vol.Required(ATTR_EXTERNALREPLY): cv.string,
    vol.Required(ATTR_INTERNALREPLY): cv.string,
    vol.Optional(ATTR_START): cv.datetime,
    vol.Optional(ATTR_END): cv.datetime,
    vol.Optional(ATTR_EXTERNAL_AUDIENCE): vol.Coerce(ExternalAudience),
}

AUTO_REPLY_SERVICE_DISABLE_SCHEMA = {}


YAML_CALENDAR_ENTITY_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_NAME): cv.string,
        vol.Required(CONF_DEVICE_ID): cv.string,
        vol.Optional(CONF_HOURS_FORWARD_TO_GET, default=24): int,
        vol.Optional(CONF_HOURS_BACKWARD_TO_GET, default=0): int,
        vol.Optional(CONF_SEARCH): cv.string,
        vol.Optional(CONF_EXCLUDE): [cv.string],
        vol.Optional(CONF_TRACK): cv.boolean,
        vol.Optional(CONF_MAX_RESULTS): cv.positive_int,
    }
)

YAML_CALENDAR_DEVICE_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_CAL_ID): cv.string,
        vol.Required(CONF_ENTITIES, None): vol.All(
            cv.ensure_list, [YAML_CALENDAR_ENTITY_SCHEMA]
        ),
    },
    extra=vol.ALLOW_EXTRA,
)

YAML_TASK_LIST_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_YAML_TASK_LIST_ID): cv.string,
        vol.Required(CONF_NAME): cv.string,
        vol.Optional(CONF_TRACK, default=True): cv.boolean,
        vol.Optional(CONF_SHOW_COMPLETED, default=False): cv.boolean,
        vol.Optional(CONF_DUE_HOURS_FORWARD_TO_GET): int,
        vol.Optional(CONF_DUE_HOURS_BACKWARD_TO_GET): int,
    }
)

REQUEST_AUTHORIZATION_DEFAULT_SCHEMA = {vol.Required(CONF_URL): cv.string}

CHAT_SERVICE_SEND_MESSAGE_SCHEMA = {
    vol.Required(ATTR_CHAT_ID): cv.string,
    vol.Required(ATTR_MESSAGE): cv.string,
    vol.Optional(ATTR_CONTENT_TYPE, default="text"): vol.In(CONTENT_TYPES),
}
