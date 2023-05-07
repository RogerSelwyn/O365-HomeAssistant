"""Schema for O365 Integration."""

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.components.notify import (
    ATTR_DATA,
    ATTR_MESSAGE,
    ATTR_TARGET,
    ATTR_TITLE,
)
from homeassistant.const import CONF_ENABLED, CONF_NAME

from O365.calendar import AttendeeType  # pylint: disable=no-name-in-module
from O365.calendar import EventSensitivity  # pylint: disable=no-name-in-module
from O365.calendar import EventShowAs  # pylint: disable=no-name-in-module
from O365.mailbox import ExternalAudience  # pylint: disable=no-name-in-module
from O365.utils import ImportanceLevel  # pylint: disable=no-name-in-module

from .const import (  # CONF_DUE_HOURS_BACKWARD_TO_GET,; CONF_DUE_HOURS_FORWARD_TO_GET,
    ATTR_ATTACHMENTS,
    ATTR_ATTENDEES,
    ATTR_BODY,
    ATTR_CATEGORIES,
    ATTR_COMPLETED,
    ATTR_DESCRIPTION,
    ATTR_DUE,
    ATTR_EMAIL,
    ATTR_END,
    ATTR_EVENT_ID,
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
    ATTR_TASK_ID,
    ATTR_TYPE,
    ATTR_ZIP_ATTACHMENTS,
    ATTR_ZIP_NAME,
    CONF_ACCOUNT_NAME,
    CONF_ACCOUNTS,
    CONF_ALT_AUTH_METHOD,
    CONF_AUTO_REPLY_SENSORS,
    CONF_BODY_CONTAINS,
    CONF_CAL_ID,
    CONF_CHAT_SENSORS,
    CONF_CLIENT_ID,
    CONF_CLIENT_SECRET,
    CONF_DEVICE_ID,
    CONF_DOWNLOAD_ATTACHMENTS,
    CONF_EMAIL_SENSORS,
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
    CONF_SHOW_COMPLETED,
    CONF_STATUS_SENSORS,
    CONF_SUBJECT_CONTAINS,
    CONF_SUBJECT_IS,
    CONF_TASK_LIST_ID,
    CONF_TODO_SENSORS,
    CONF_TRACK,
    CONF_TRACK_NEW,
    CONF_TRACK_NEW_CALENDAR,
    CONF_URL,
    EventResponse,
)

EMAIL_SENSOR = vol.Schema(
    {
        vol.Required(CONF_NAME): cv.string,
        vol.Optional(CONF_MAIL_FOLDER): cv.string,
        vol.Optional(CONF_MAX_ITEMS, default=5): int,
        vol.Optional(CONF_IS_UNREAD): bool,
        vol.Optional(CONF_DOWNLOAD_ATTACHMENTS, default=True): bool,
        vol.Optional(CONF_HTML_BODY, default=False): bool,
    }
)
STATUS_SENSOR = vol.Schema(
    {
        vol.Required(CONF_NAME): cv.string,
    }
)
CHAT_SENSOR = vol.Schema(
    {
        vol.Required(CONF_NAME): cv.string,
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
    }
)
TODO_SENSOR = vol.Schema(
    {
        vol.Required(CONF_ENABLED, default=False): bool,
        vol.Optional(CONF_TRACK_NEW, default=True): bool,
        vol.Optional(CONF_ENABLE_UPDATE, default=False): bool,
    }
)

LEGACY_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_CLIENT_ID): cv.string,
        vol.Required(CONF_CLIENT_SECRET): cv.string,
        vol.Optional(CONF_TRACK_NEW_CALENDAR, default=True): bool,
        vol.Optional(CONF_ENABLE_UPDATE, default=True): bool,
        vol.Optional(CONF_ALT_AUTH_METHOD, default=False): bool,
        vol.Optional(CONF_EMAIL_SENSORS): [EMAIL_SENSOR],
        vol.Optional(CONF_QUERY_SENSORS): [QUERY_SENSOR],
        vol.Optional(CONF_STATUS_SENSORS): [STATUS_SENSOR],
        vol.Optional(CONF_CHAT_SENSORS): [CHAT_SENSOR],
        vol.Optional(CONF_AUTO_REPLY_SENSORS): [AUTO_REPLY_SENSOR],
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
                    vol.Optional(CONF_ENABLE_UPDATE, default=False): bool,
                    vol.Optional(CONF_GROUPS, default=False): bool,
                    vol.Required(CONF_ACCOUNT_NAME, ""): cv.string,
                    vol.Optional(CONF_ALT_AUTH_METHOD, default=False): bool,
                    vol.Optional(CONF_EMAIL_SENSORS): [EMAIL_SENSOR],
                    vol.Optional(CONF_QUERY_SENSORS): [QUERY_SENSOR],
                    vol.Optional(CONF_STATUS_SENSORS): [STATUS_SENSOR],
                    vol.Optional(CONF_CHAT_SENSORS): [CHAT_SENSOR],
                    vol.Optional(CONF_TODO_SENSORS): TODO_SENSOR,
                    vol.Optional(CONF_AUTO_REPLY_SENSORS): [AUTO_REPLY_SENSOR],
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

CALENDAR_SERVICE_CREATE_SCHEMA = {
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


CALENDAR_SERVICE_MODIFY_SCHEMA = {
    vol.Required(ATTR_EVENT_ID): cv.string,
    vol.Optional(ATTR_START): cv.datetime,
    vol.Optional(ATTR_END): cv.datetime,
    vol.Required(ATTR_SUBJECT): cv.string,
    vol.Optional(ATTR_BODY): cv.string,
    vol.Optional(ATTR_LOCATION): cv.string,
    vol.Optional(ATTR_CATEGORIES): [cv.string],
    vol.Optional(ATTR_SENSITIVITY): vol.Coerce(EventSensitivity),
    vol.Optional(ATTR_SHOW_AS): vol.Coerce(EventShowAs),
    vol.Optional(ATTR_IS_ALL_DAY): bool,
    vol.Optional(ATTR_ATTENDEES): [CALENDAR_SERVICE_ATTENDEE_SCHEMA],
}


CALENDAR_SERVICE_REMOVE_SCHEMA = {
    vol.Required(ATTR_EVENT_ID): cv.string,
}


TASK_SERVICE_NEW_SCHEMA = {
    vol.Required(ATTR_SUBJECT): cv.string,
    vol.Optional(ATTR_DESCRIPTION): cv.string,
    vol.Optional(ATTR_DUE): cv.string,
    vol.Optional(ATTR_REMINDER): cv.datetime,
}

TASK_SERVICE_UPDATE_SCHEMA = {
    vol.Required(ATTR_TASK_ID): cv.string,
    vol.Optional(ATTR_SUBJECT): cv.string,
    vol.Optional(ATTR_DESCRIPTION): cv.string,
    vol.Optional(ATTR_DUE): cv.string,
    vol.Optional(ATTR_REMINDER): cv.datetime,
}

TASK_SERVICE_DELETE_SCHEMA = {
    vol.Required(ATTR_TASK_ID): cv.string,
}
TASK_SERVICE_COMPLETE_SCHEMA = {
    vol.Required(ATTR_TASK_ID): cv.string,
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


CALENDAR_ENTITY_SCHEMA = vol.Schema(
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

CALENDAR_DEVICE_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_CAL_ID): cv.string,
        vol.Required(CONF_ENTITIES, None): vol.All(
            cv.ensure_list, [CALENDAR_ENTITY_SCHEMA]
        ),
    },
    extra=vol.ALLOW_EXTRA,
)

TASK_LIST_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_TASK_LIST_ID): cv.string,
        vol.Required(CONF_NAME): cv.string,
        vol.Optional(CONF_TRACK, default=True): cv.boolean,
        vol.Optional(CONF_SHOW_COMPLETED, default=False): cv.boolean,
        # vol.Optional(CONF_DUE_HOURS_FORWARD_TO_GET): int,
        # vol.Optional(CONF_DUE_HOURS_BACKWARD_TO_GET): int,
    }
)

REQUEST_AUTHORIZATION_DEFAULT_SCHEMA = {vol.Required(CONF_URL): cv.string}
