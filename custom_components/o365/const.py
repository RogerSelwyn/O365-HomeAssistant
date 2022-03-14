"""Constantants."""
from datetime import timedelta
from enum import Enum

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.components.notify import (
    ATTR_DATA,
    ATTR_MESSAGE,
    ATTR_TARGET,
    ATTR_TITLE,
)
from homeassistant.const import CONF_NAME
from O365.calendar import AttendeeType  # pylint: disable=no-name-in-module
from O365.calendar import EventSensitivity  # pylint: disable=no-name-in-module
from O365.calendar import EventShowAs  # pylint: disable=no-name-in-module


class EventResponse(Enum):
    """Event response."""

    Accept = "accept"  # pylint: disable=invalid-name
    Tentative = "tentative"  # pylint: disable=invalid-name
    Decline = "decline"  # pylint: disable=invalid-name


ATTR_ATTACHMENTS = "attachments"
ATTR_ATTENDEES = "attendees"
ATTR_BODY = "body"
ATTR_CALENDAR_ID = "calendar_id"
ATTR_CATEGORIES = "categories"
ATTR_EMAIL = "email"
ATTR_END = "end"
ATTR_ENTITY_ID = "entity_id"
ATTR_EVENT_ID = "event_id"
ATTR_IS_ALL_DAY = "is_all_day"
ATTR_LOCATION = "location"
ATTR_MESSAGE_IS_HTML = "message_is_html"
ATTR_PHOTOS = "photos"
ATTR_RESPONSE = "response"
ATTR_SEND_RESPONSE = "send_response"
ATTR_SENSITIVITY = "sensitivity"
ATTR_SHOW_AS = "show_as"
ATTR_START = "start"
ATTR_SUBJECT = "subject"
ATTR_TYPE = "type"
ATTR_ZIP_ATTACHMENTS = "zip_attachments"
ATTR_ZIP_NAME = "zip_name"
AUTH_CALLBACK_NAME = "api:o365"
AUTH_CALLBACK_PATH = "/api/o365"
AUTH_CALLBACK_PATH_ALT = "https://login.microsoftonline.com/common/oauth2/nativeclient"
CALENDAR_DOMAIN = "calendar"
CALENDAR_ENTITY_ID_FORMAT = CALENDAR_DOMAIN + ".{}"
CONF_ACCOUNT_NAME = "account_name"
CONF_ALIASES = "aliases"
CONF_ALT_CONFIG = "alt_auth_flow"
CONF_CACHE_PATH = "cache_path"
CONF_CALENDAR_NAME = "calendar_name"
CONF_CLIENT_ID = "client_id"
CONF_CLIENT_SECRET = "client_secret"  # nosec
CONF_DEVICE_ID = "device_id"
CONF_DOWNLOAD_ATTACHMENTS = "download_attachments"
CONF_EMAIL_SENSORS = "email_sensor"
CONF_IGNORE_AVAILABILITY = "ignore_availability"
CONF_OFFSET = "offset"
CONF_SEARCH = "search"
CONF_TRACK = "track"
CONF_MAX_RESULTS = "max_results"
CONF_CAL_ID = "cal_id"
CONF_ENABLE_UPDATE = "enable_update"
CONF_ENTITIES = "entities"

CONF_HAS_ATTACHMENT = "has_attachment"
CONF_HOURS_BACKWARD_TO_GET = "start_offset"
CONF_HOURS_FORWARD_TO_GET = "end_offset"
CONF_IMPORTANCE = "importance"
CONF_IS_UNREAD = "is_unread"
CONF_MAIL_FOLDER = "folder"
CONF_MAIL_FROM = "from"
CONF_MAX_ITEMS = "max_items"
CONF_STATUS_SENSORS = "status_sensors"
CONF_QUERY_SENSORS = "query_sensors"
CONF_SECONDARY_ACCOUNTS = "secondary_accounts"
CONF_SUBJECT_CONTAINS = "subject_contains"
CONF_SUBJECT_IS = "subject_is"
CONF_TRACK_NEW = "track_new_calendar"
CONFIGURATOR_DESCRIPTION = (
    "To link your O365 account, click the link, login, and authorize:"
)
CONFIGURATOR_LINK_NAME = "Link O365 account"
CONFIGURATOR_SUBMIT_CAPTION = "I authorized successfully"
CONST_PRIMARY = "$o365-primary$"
DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%S%z"
DEFAULT_CACHE_PATH = ".O365-token-cache"
TOKEN_FILENAME = "o365{0}.token"  # nosec
DEFAULT_HOURS_BACKWARD_TO_GET = 0
DEFAULT_HOURS_FORWARD_TO_GET = 24
DEFAULT_NAME = "O365"
DOMAIN = "o365"
ICON = "mdi:office"
MIN_TIME_BETWEEN_UPDATES = timedelta(minutes=15)
DEFAULT_OFFSET = "!!"
PERM_CALENDARS_READ = "Calendars.Read"
PERM_CALENDARS_READ_SHARED = "Calendars.Read.Shared"
PERM_CALENDARS_READWRITE = "Calendars.ReadWrite"
PERM_CALENDARS_READWRITE_SHARED = "Calendars.ReadWrite.Shared"
PERM_MAIL_READ = "Mail.Read"
PERM_MAIL_READ_SHARED = "Mail.Read.Shared"
PERM_MAIL_READWRITE = "Mail.ReadWrite"
PERM_MAIL_READWRITE_SHARED = "Mail.ReadWrite.Shared"
PERM_MAIL_SEND = "Mail.Send"
PERM_MAIL_SEND_SHARED = "Mail.Send.Shared"
PERM_OFFLINE_ACCESS = "offline_access"
PERM_PRESENCE_READ = "Presence.Read"
PERM_USER_READ = "User.Read"
PERM_MINIMUM_PRESENCE = [PERM_PRESENCE_READ, []]
PERM_MINIMUM_USER = [PERM_USER_READ, []]
PERM_MINIMUM_MAIL = [
    PERM_MAIL_READ,
    [PERM_MAIL_READ_SHARED, PERM_MAIL_READWRITE, PERM_MAIL_READWRITE_SHARED],
]
PERM_MINIMUM_CALENDAR = [
    PERM_CALENDARS_READ,
    [
        PERM_CALENDARS_READ_SHARED,
        PERM_CALENDARS_READWRITE,
        PERM_CALENDARS_READWRITE_SHARED,
    ],
]
PERM_MINIMUM_CALENDAR_WRITE = [
    PERM_CALENDARS_READWRITE,
    [
        PERM_CALENDARS_READWRITE_SHARED,
    ],
]
PERM_MINIMUM_SEND = [
    PERM_MAIL_SEND,
    [PERM_MAIL_SEND_SHARED],
]

YAML_CALENDARS = "{0}{1}_calendars.yaml"

EMAIL_SENSOR = vol.Schema(
    {
        vol.Required(CONF_NAME): cv.string,
        vol.Optional(CONF_MAIL_FOLDER): cv.string,
        vol.Optional(CONF_MAX_ITEMS, default=5): int,
        vol.Optional(CONF_IS_UNREAD): bool,
        vol.Optional(CONF_DOWNLOAD_ATTACHMENTS): bool,
    }
)
STATUS_SENSOR = vol.Schema(
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
        vol.Exclusive(CONF_SUBJECT_CONTAINS, "subject_*"): cv.string,
        vol.Exclusive(CONF_SUBJECT_IS, "subject_*"): cv.string,
        vol.Optional(CONF_DOWNLOAD_ATTACHMENTS): bool,
    }
)
DOMAIN_SCHEMA = {
    vol.Required(CONF_CLIENT_ID): cv.string,
    vol.Required(CONF_CLIENT_SECRET): cv.string,
    vol.Optional(CONF_TRACK_NEW, default=True): bool,
    vol.Optional(CONF_ENABLE_UPDATE, default=True): bool,
    vol.Required(CONF_ACCOUNT_NAME, ""): cv.string,
    vol.Optional(CONF_ALT_CONFIG, default=False): bool,
    vol.Optional(CONF_EMAIL_SENSORS): [EMAIL_SENSOR],
    vol.Optional(CONF_QUERY_SENSORS): [QUERY_SENSOR],
    vol.Optional(CONF_STATUS_SENSORS): [STATUS_SENSOR],
}
PRIMARY_SCHEMA = dict(DOMAIN_SCHEMA)
PRIMARY_SCHEMA[vol.Optional(CONF_SECONDARY_ACCOUNTS)] = [DOMAIN_SCHEMA]
PRIMARY_SCHEMA.pop(vol.Required(CONF_ACCOUNT_NAME, ""))
CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            PRIMARY_SCHEMA,
        )
    },
    extra=vol.ALLOW_EXTRA,
)
NOTIFY_DATA_SCHEMA = vol.Schema(
    {
        vol.Optional(ATTR_MESSAGE_IS_HTML, default=False): bool,
        vol.Optional(ATTR_TARGET): cv.string,
        vol.Optional(ATTR_ZIP_ATTACHMENTS, default=False): bool,
        vol.Optional(ATTR_ZIP_NAME): cv.string,
        vol.Optional(ATTR_PHOTOS, default=[]): [cv.string],
        vol.Optional(ATTR_ATTACHMENTS, default=[]): [cv.string],
    }
)

NOTIFY_BASE_SCHEMA = vol.Schema(
    {
        vol.Optional(ATTR_TARGET, default=[]): [cv.string],
        vol.Optional(ATTR_TITLE, default=""): cv.string,
        vol.Optional(ATTR_DATA): NOTIFY_DATA_SCHEMA,
    }
)

CALENDAR_SERVICE_RESPOND_SCHEMA = vol.Schema(
    {
        vol.Optional(ATTR_ENTITY_ID): cv.string,
        vol.Required(ATTR_EVENT_ID): cv.string,
        vol.Required(ATTR_CALENDAR_ID): cv.string,
        vol.Optional(ATTR_RESPONSE, None): cv.enum(EventResponse),
        vol.Optional(ATTR_SEND_RESPONSE, True): bool,
        vol.Optional(ATTR_MESSAGE, None): cv.string,
    }
)

ATTENDEE_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_EMAIL): cv.string,
        vol.Required(ATTR_TYPE): cv.enum(AttendeeType),
    }
)

CALENDAR_SERVICE_CREATE_SCHEMA = vol.Schema(
    {
        vol.Optional(ATTR_ENTITY_ID): cv.string,
        vol.Required(ATTR_CALENDAR_ID): cv.string,
        vol.Required(ATTR_START): cv.datetime,
        vol.Required(ATTR_END): cv.datetime,
        vol.Required(ATTR_SUBJECT): cv.string,
        vol.Optional(ATTR_BODY): cv.string,
        vol.Optional(ATTR_LOCATION): cv.string,
        vol.Optional(ATTR_CATEGORIES): [cv.string],
        vol.Optional(ATTR_SENSITIVITY): cv.enum(EventSensitivity),
        vol.Optional(ATTR_SHOW_AS): cv.enum(EventShowAs),
        vol.Optional(ATTR_IS_ALL_DAY): bool,
        vol.Optional(ATTR_ATTENDEES): [ATTENDEE_SCHEMA],
    }
)

CALENDAR_SERVICE_MODIFY_SCHEMA = vol.Schema(
    {
        vol.Optional(ATTR_ENTITY_ID): cv.string,
        vol.Required(ATTR_EVENT_ID): cv.string,
        vol.Required(ATTR_CALENDAR_ID): cv.string,
        vol.Optional(ATTR_START): cv.datetime,
        vol.Optional(ATTR_END): cv.datetime,
        vol.Required(ATTR_SUBJECT): cv.string,
        vol.Optional(ATTR_BODY): cv.string,
        vol.Optional(ATTR_LOCATION): cv.string,
        vol.Optional(ATTR_CATEGORIES): [cv.string],
        vol.Optional(ATTR_SENSITIVITY): cv.enum(EventSensitivity),
        vol.Optional(ATTR_SHOW_AS): cv.enum(EventShowAs),
        vol.Optional(ATTR_IS_ALL_DAY): bool,
        vol.Optional(ATTR_ATTENDEES): [ATTENDEE_SCHEMA],
    }
)


CALENDAR_SERVICE_REMOVE_SCHEMA = vol.Schema(
    {
        vol.Optional(ATTR_ENTITY_ID): cv.string,
        vol.Required(ATTR_EVENT_ID): cv.string,
        vol.Required(ATTR_CALENDAR_ID): cv.string,
    }
)

SINGLE_CALSEARCH_CONFIG = vol.Schema(
    {
        vol.Required(CONF_NAME): cv.string,
        vol.Required(CONF_DEVICE_ID): cv.string,
        vol.Optional(CONF_HOURS_FORWARD_TO_GET, default=24): int,
        vol.Optional(CONF_HOURS_BACKWARD_TO_GET, default=0): int,
        vol.Optional(CONF_SEARCH): cv.string,
        vol.Optional(CONF_TRACK): cv.boolean,
        vol.Optional(CONF_MAX_RESULTS): cv.positive_int,
    }
)

CALENDAR_DEVICE_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_CAL_ID): cv.string,
        vol.Required(CONF_ENTITIES, None): vol.All(
            cv.ensure_list, [SINGLE_CALSEARCH_CONFIG]
        ),
    },
    extra=vol.ALLOW_EXTRA,
)
