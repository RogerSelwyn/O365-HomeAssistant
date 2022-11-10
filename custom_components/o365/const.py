"""Constantants."""
from datetime import timedelta
from enum import Enum


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
ATTR_CHAT_ID = "chat_id"
ATTR_CONTENT = "content"
ATTR_EMAIL = "email"
ATTR_END = "end"
ATTR_ENTITY_ID = "entity_id"
ATTR_EVENT_ID = "event_id"
ATTR_FROM_DISPLAY_NAME = "from_display_name"
ATTR_GROUP = "group"
ATTR_IS_ALL_DAY = "is_all_day"
ATTR_IMPORTANCE = "importance"
ATTR_LOCATION = "location"
ATTR_MESSAGE_IS_HTML = "message_is_html"
ATTR_PHOTOS = "photos"
ATTR_RESPONSE = "response"
ATTR_SENDER = "sender"
ATTR_SEND_RESPONSE = "send_response"
ATTR_SENSITIVITY = "sensitivity"
ATTR_SHOW_AS = "show_as"
ATTR_START = "start"
ATTR_SUBJECT = "subject"
ATTR_SUMMARY = "summary"
ATTR_TYPE = "type"
ATTR_ZIP_ATTACHMENTS = "zip_attachments"
ATTR_ZIP_NAME = "zip_name"
AUTH_CALLBACK_NAME = "api:o365"
AUTH_CALLBACK_PATH_ALT = "/api/o365"
AUTH_CALLBACK_PATH_DEFAULT = (
    "https://login.microsoftonline.com/common/oauth2/nativeclient"
)
CALENDAR_DOMAIN = "calendar"
CALENDAR_ENTITY_ID_FORMAT = CALENDAR_DOMAIN + ".{}"
CONF_ACCOUNT = "account"
CONF_ACCOUNTS = "accounts"
CONF_ACCOUNT_NAME = "account_name"
CONF_ALIASES = "aliases"
CONF_ALT_AUTH_FLOW = "alt_auth_flow"
CONF_ALT_AUTH_METHOD = "alt_auth_method"
CONF_BODY_CONTAINS = "body_contains"
CONF_CACHE_PATH = "cache_path"
CONF_CALENDAR_NAME = "calendar_name"
CONF_CAL_IDS = "cal_ids"
CONF_CLIENT_ID = "client_id"
CONF_CLIENT_SECRET = "client_secret"  # nosec
CONF_CONFIG_TYPE = "config_type"
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
CONF_GROUPS = "groups"
CONF_HAS_ATTACHMENT = "has_attachment"
CONF_HOURS_BACKWARD_TO_GET = "start_offset"
CONF_HOURS_FORWARD_TO_GET = "end_offset"
CONF_IMPORTANCE = "importance"
CONF_IS_UNREAD = "is_unread"
CONF_MAIL_FOLDER = "folder"
CONF_MAIL_FROM = "from"
CONF_MAX_ITEMS = "max_items"
CONF_CHAT_SENSORS = "chat_sensors"
CONF_STATUS_SENSORS = "status_sensors"
CONF_QUERY_SENSORS = "query_sensors"
CONF_SUBJECT_CONTAINS = "subject_contains"
CONF_SUBJECT_IS = "subject_is"
CONF_TRACK_NEW = "track_new_calendar"
CONFIGURATOR_DESCRIPTION_ALT = (
    "To link your O365 account, click the link, login, and authorize:"
)
CONFIGURATOR_DESCRIPTION_DEFAULT = (
    "Complete the configuration and copy the complete url into "
    + "this field afterwards and submit"
)
CONFIGURATOR_FIELDS = [{"id": "token", "name": "Returned Url", "type": "token"}]
CONFIGURATOR_LINK_NAME = "Link O365 account"
CONFIGURATOR_SUBMIT_CAPTION = "I authorized successfully"
CONST_CONFIG_TYPE_DICT = "dict"
CONST_CONFIG_TYPE_LIST = "list"
CONST_GROUP = "group:"
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
O365_STORAGE = "o365_storage"
DEFAULT_OFFSET = "!!"
PERM_CALENDARS_READ = "Calendars.Read"
PERM_CALENDARS_READ_SHARED = "Calendars.Read.Shared"
PERM_CALENDARS_READWRITE = "Calendars.ReadWrite"
PERM_CALENDARS_READWRITE_SHARED = "Calendars.ReadWrite.Shared"
PERM_CHAT_READ = "Chat.Read"
PERM_GROUP_READ_ALL = "Group.Read.All"
PERM_GROUP_READWRITE_ALL = "Group.ReadWrite.All"
PERM_MAIL_READ = "Mail.Read"
PERM_MAIL_READ_SHARED = "Mail.Read.Shared"
PERM_MAIL_READWRITE = "Mail.ReadWrite"
PERM_MAIL_READWRITE_SHARED = "Mail.ReadWrite.Shared"
PERM_MAIL_SEND = "Mail.Send"
PERM_MAIL_SEND_SHARED = "Mail.Send.Shared"
PERM_OFFLINE_ACCESS = "offline_access"
PERM_PRESENCE_READ = "Presence.Read"
PERM_USER_READ = "User.Read"
PERM_MINIMUM_CHAT = [PERM_CHAT_READ, []]
PERM_MINIMUM_GROUP = [PERM_GROUP_READ_ALL, [PERM_GROUP_READWRITE_ALL]]
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

YAML_CALENDARS = "{0}_calendars{1}.yaml"
