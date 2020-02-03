from datetime import timedelta

from homeassistant.const import CONF_NAME
from homeassistant.components.notify import (
    ATTR_DATA,
    ATTR_TARGET,
    ATTR_TITLE,
)
import voluptuous as vol
import homeassistant.helpers.config_validation as cv

from homeassistant.config import get_default_config_dir

from O365 import FileSystemTokenBackend


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
    "Calendars.Read",
    "Calendars.Read.Shared",
    "Mail.ReadWrite",
    "Mail.ReadWrite.Shared",
    "Mail.Send",
    "Mail.Send.Shared",
]

TOKEN_BACKEND = FileSystemTokenBackend(
    token_path=DEFAULT_CACHE_PATH, token_filename="o365.token"
)

CALENDAR_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_CALENDAR_NAME): cv.string,
        vol.Optional(CONF_NAME, default="o365"): cv.string,
        vol.Optional(CONF_HOURS_FORWARD_TO_GET, default=24): int,
        vol.Optional(CONF_HOURS_BACKWARD_TO_GET, default=0): int,
    }
)

EMAIL_SENSOR = vol.Schema(
    {
        vol.Required(CONF_NAME): cv.string,
        vol.Optional(CONF_MAIL_FOLDER, default=None): vol.Any(cv.string, None),
        vol.Optional(CONF_MAX_ITEMS, default=5): int,
        vol.Optional(CONF_IS_UNREAD, default=None): vol.Any(bool, None),
    }
)

QUERY_SENSOR = vol.Schema(
    {
        vol.Required(CONF_NAME): cv.string,
        vol.Optional(CONF_MAIL_FOLDER, default=None): vol.Any(cv.string, None),
        vol.Optional(CONF_MAIL_FROM, default=None): vol.Any(cv.string, None),
        vol.Optional(CONF_MAX_ITEMS, default=5): int,
        vol.Optional(CONF_HAS_ATTACHMENT, default=None): vol.Any(bool, None),
        vol.Optional(CONF_IS_UNREAD, default=None): vol.Any(bool, None),
        vol.Exclusive(CONF_SUBJECT_CONTAINS, "subject_*"): vol.Any(cv.string, None),
        vol.Exclusive(CONF_SUBJECT_IS, "subject_*"): vol.Any(cv.string, None),
    }
)

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Required(CONF_CLIENT_ID): cv.string,
                vol.Required(CONF_CLIENT_SECRET): cv.string,
                vol.Optional(CONF_ALT_CONFIG, default=False): bool,
                vol.Optional(CONF_CALENDARS, default=None): vol.All(
                    cv.ensure_list, [CALENDAR_SCHEMA]
                ),
                vol.Optional(CONF_EMAIL_SENSORS, default=None): vol.All(
                    cv.ensure_list, [EMAIL_SENSOR]
                ),
                vol.Optional(CONF_QUERY_SENSORS, default=None): vol.All(
                    cv.ensure_list, [QUERY_SENSOR]
                ),
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
        vol.Optional(ATTR_TARGET, default=None): vol.Any(cv.string, None),
        vol.Optional(ATTR_ZIP_ATTACHMENTS, default=False): bool,
        vol.Optional(ATTR_ZIP_NAME, default=None): vol.Any(cv.string, None),
        vol.Optional(ATTR_PHOTOS, default=[]): [cv.string],
        vol.Optional(ATTR_ATTACHMENTS, default=[]): [cv.string],
    }
)

NOTIFY_BASE_SCHEMA = vol.Schema(
    {
        vol.Optional(ATTR_TARGET, default=""): vol.All(cv.ensure_list, [cv.string]),
        vol.Optional(ATTR_TITLE, default=""): cv.string,
        vol.Optional(ATTR_DATA, default=None): vol.Any(NOTIFY_DATA_SCHEMA, None),
    }
)

MIN_TIME_BETWEEN_UPDATES = timedelta(minutes=5)

DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%S%z"
