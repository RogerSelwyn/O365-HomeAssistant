from enum import Enum
from datetime import timedelta
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


ATTR_ATTACHMENTS = "attachments"
ATTR_ATTENDEES = "attendees"
ATTR_BODY = "body"
ATTR_CALENDAR_ID = "calendar_id"
ATTR_CATEGORIES = "categories"
ATTR_EMAIL = "email"
ATTR_END = "end"
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
CONF_ALIASES = "aliases"
CONF_ALT_CONFIG = "alt_auth_flow"
CONF_CACHE_PATH = "cache_path"
CONF_CALENDAR_NAME = "calendar_name"
CONF_CALENDARS = "calendars"
CONF_CLIENT_ID = "client_id"
CONF_CLIENT_SECRET = "client_secret"
CONF_DEVICE_ID = "device_id"
CONF_EMAIL_SENSORS = "email_sensor"
CONF_IGNORE_AVAILABILITY = "ignore_availability"
CONF_OFFSET = "offset"
CONF_SEARCH = "search"
CONF_TRACK = "track"
CONF_MAX_RESULTS = "max_results"
CONF_CAL_ID = "cal_id"
CONF_ENTITIES = "entities"

CONF_HAS_ATTACHMENT = "has_attachment"
CONF_HOURS_BACKWARD_TO_GET = "start_offset"
CONF_HOURS_FORWARD_TO_GET = "end_offset"
CONF_IS_UNREAD = "is_unread"
CONF_MAIL_FOLDER = "folder"
CONF_MAIL_FROM = "from"
CONF_MAX_ITEMS = "max_items"
CONF_QUERY_SENSORS = "query_sensors"
CONF_SUBJECT_CONTAINS = "subject_contains"
CONF_SUBJECT_IS = "subject_is"
CONF_TRACK_NEW = "track_new_calendar"
CONFIG_BASE_DIR = get_default_config_dir()
CONFIGURATOR_DESCRIPTION = (
    "To link your O365 account, click the link, login, and authorize:"
)
CONFIGURATOR_LINK_NAME = "Link O365 account"
CONFIGURATOR_SUBMIT_CAPTION = "I authorized successfully"
DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%S%z"
DEFAULT_CACHE_PATH = ".O365-token-cache"
DEFAULT_HOURS_BACKWARD_TO_GET = 0
DEFAULT_HOURS_FORWARD_TO_GET = 24
DEFAULT_NAME = "O365"
DOMAIN = "o365"
ICON = "mdi:office"
MIN_TIME_BETWEEN_UPDATES = timedelta(minutes=15)
DEFAULT_OFFSET = "!!"
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
MINIMUM_REQUIRED_SCOPES = [
    "User.Read",
    "Calendars.ReadWrite",
    "Mail.ReadWrite",
    "Mail.Send",
]
TOKEN_BACKEND = FileSystemTokenBackend(
    token_path=DEFAULT_CACHE_PATH, token_filename="o365.token"
)
YAML_CALENDARS = f"{DOMAIN}_calendars.yaml"

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
                vol.Optional(CONF_TRACK_NEW, default=True): bool,
                vol.Optional(CONF_ALT_CONFIG, default=False): bool,
                vol.Optional(CONF_CALENDARS, default=[]): [CALENDAR_SCHEMA],
                vol.Optional(CONF_EMAIL_SENSORS): [EMAIL_SENSOR],
                vol.Optional(CONF_QUERY_SENSORS): [QUERY_SENSOR],
            },
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
    {vol.Required(ATTR_EVENT_ID): cv.string, vol.Required(ATTR_CALENDAR_ID): cv.string,}
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
