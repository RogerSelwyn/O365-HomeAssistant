import re
from enum import Enum
from homeassistant.const import CONF_NAME
from homeassistant.components.notify import (
    ATTR_DATA,
    ATTR_TARGET,
    ATTR_TITLE,
    ATTR_MESSAGE,
)
import voluptuous as vol
import homeassistant.helpers.config_validation as cv

from homeassistant.config import get_default_config_dir

from O365 import FileSystemTokenBackend
from O365.calendar import AttendeeType, EventSensitivity, EventShowAs


class EventResponse(Enum):
    Accept = "accept"
    Tentative = "tentative"
    Decline = "decline"


CONFIG_BASE_DIR = get_default_config_dir()

DEFAULT_NAME = "O365"

AUTH_CALLBACK_NAME = "api:o365"
AUTH_CALLBACK_PATH = "/api/o365"

AUTH_CALLBACK_PATH_ALT = "https://login.microsoftonline.com/common/oauth2/nativeclient"

CONF_ALIASES = "aliases"
CONF_CACHE_PATH = "cache_path"
CONF_CLIENT_ID = "client_id"
CONF_CLIENT_SECRET = "client_secret"
CONF_CALENDAR_NAME = "calendar_name"
CONF_HOURS_FORWARD_TO_GET = "end_offset"
DEFAULT_HOURS_FORWARD_TO_GET = 24
CONF_HOURS_BACKWARD_TO_GET = "start_offset"
DEFAULT_HOURS_BACKWARD_TO_GET = 0
CONF_ALT_CONFIG = "alt_auth_flow"
CONF_CALENDARS = "calendars"
CONF_EMAIL_SENSORS = "email_sensor"
CONF_MAIL_FOLDER = "folder"
CONF_QUERY_SENSORS = "query_sensors"
CONF_MAX_ITEMS = "max_items"
CONF_HAS_ATTACHMENT = "has_attachment"
CONF_SUBJECT_CONTAINS = "subject_contains"
CONF_SUBJECT_IS = "subject_is"
CONF_MAIL_FROM = "from"
CONF_IS_UNREAD = "is_unread"

CONFIGURATOR_DESCRIPTION = (
    "To link your O365 account, click the link, login, and authorize:"
)
CONFIGURATOR_LINK_NAME = "Link O365 account"
CONFIGURATOR_SUBMIT_CAPTION = "I authorized successfully"

DEFAULT_CACHE_PATH = ".O365-token-cache"
DOMAIN = "o365"

ICON = "mdi:office"

SCOPE = [
    "offline_access",
    "User.Read",
    "Calendars.ReadWrite",
    "Calendars.ReadWrite.Shared",
    "Mail.ReadWrite",
    "Mail.ReadWrite.Shared",
    "Mail.Send",
    "Mail.Send.Shared",
]

DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%S%z"

TOKEN_BACKEND = FileSystemTokenBackend(
    token_path=DEFAULT_CACHE_PATH, token_filename="o365.token"
)

CALENDAR_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_CALENDAR_NAME): cv.string,
        vol.Optional(CONF_NAME): cv.string,
        vol.Optional(CONF_HOURS_FORWARD_TO_GET, default=24): int,
        vol.Optional(CONF_HOURS_BACKWARD_TO_GET, default=0): int,
    }
)

EMAIL_SENSOR = vol.Schema(
    {
        vol.Required(CONF_NAME): cv.string,
        vol.Optional(CONF_MAIL_FOLDER): cv.string,
        vol.Optional(CONF_MAX_ITEMS, default=5): int,
        vol.Optional(CONF_IS_UNREAD): bool,
    }
)

QUERY_SENSOR = vol.Schema(
    {
        vol.Required(CONF_NAME): cv.string,
        vol.Optional(CONF_MAIL_FOLDER): cv.string,
        vol.Optional(CONF_MAIL_FROM): cv.string,
        vol.Optional(CONF_MAX_ITEMS, default=5): int,
        vol.Optional(CONF_HAS_ATTACHMENT): bool,
        vol.Optional(CONF_IS_UNREAD): bool,
        vol.Exclusive(CONF_SUBJECT_CONTAINS, "subject_*"): cv.string,
        vol.Exclusive(CONF_SUBJECT_IS, "subject_*"): cv.string,
    }
)

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Required(CONF_CLIENT_ID): cv.string,
                vol.Required(CONF_CLIENT_SECRET): cv.string,
                vol.Optional(CONF_ALT_CONFIG, default=False): bool,
                vol.Optional(CONF_CALENDARS, default=[]): [CALENDAR_SCHEMA],
                vol.Optional(CONF_EMAIL_SENSORS): [EMAIL_SENSOR],
                vol.Optional(CONF_QUERY_SENSORS): [QUERY_SENSOR],
            },
        )
    },
    extra=vol.ALLOW_EXTRA,
)

ATTR_ATTACHMENTS = "attachments"
ATTR_PHOTOS = "photos"
ATTR_MESSAGE_IS_HTML = "message_is_html"
ATTR_ZIP_ATTACHMENTS = "zip_attachments"
ATTR_ZIP_NAME = "zip_name"


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

ATTR_EVENT_ID = "event_id"
ATTR_CALENDAR_ID = "calendar_id"
ATTR_RESPONSE = "response"
ATTR_SEND_RESPONSE = "send_response"
ATTR_SUBJECT = "subject"
ATTR_BODY = "body"
ATTR_START = "start"
ATTR_END = "end"
ATTR_LOCATION = "location"
ATTR_CATEGORIES = "categories"
ATTR_SENSITIVITY = "sensitivity"
ATTR_SHOW_AS = "show_as"
ATTR_IS_ALL_DAY = "is_all_day"
ATTR_ATTENDEES = "attendees"
ATTR_EMAIL = "email"
ATTR_TYPE = "type"

datetime_regex = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\+|-)\d{4}")


CALENDAR_SERVICE_RESPOND_SCHEMA = vol.Schema(
    {
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
        vol.Required(ATTR_CALENDAR_ID): cv.string,
        vol.Required(ATTR_START): cv.matches_regex(datetime_regex),
        vol.Required(ATTR_END): cv.matches_regex(datetime_regex),
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
        vol.Required(ATTR_EVENT_ID): cv.string,
        vol.Required(ATTR_CALENDAR_ID): cv.string,
        vol.Optional(ATTR_START): cv.matches_regex(datetime_regex),
        vol.Optional(ATTR_END): cv.matches_regex(datetime_regex),
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
    {vol.Required(ATTR_EVENT_ID): cv.string, vol.Required(ATTR_CALENDAR_ID): cv.string,}
)
