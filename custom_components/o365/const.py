"""Constantants."""
from datetime import timedelta
from enum import Enum


class EventResponse(Enum):
    """Event response."""

    Accept = "accept"  # pylint: disable=invalid-name
    Tentative = "tentative"  # pylint: disable=invalid-name
    Decline = "decline"  # pylint: disable=invalid-name


ATTR_ALL_TASKS = "all_tasks"
ATTR_ATTACHMENTS = "attachments"
ATTR_ATTRIBUTES = "attributes"
ATTR_ATTENDEES = "attendees"
ATTR_AUTOREPLIESSETTINGS = "autorepliessettings"
ATTR_BODY = "body"
ATTR_CALENDAR_ID = "calendar_id"
ATTR_CATEGORIES = "categories"
ATTR_CHAT_ID = "chat_id"
ATTR_COMPLETED = "completed"
ATTR_CREATED = "created"
ATTR_CONTENT = "content"
ATTR_DESCRIPTION = "description"
ATTR_DUE = "due"
ATTR_EMAIL = "email"
ATTR_END = "end"
ATTR_ERROR = "error"
ATTR_EVENT_ID = "event_id"
ATTR_EXTERNAL_AUDIENCE = "external_audience"
ATTR_EXTERNALREPLY = "external_reply"
ATTR_FROM_DISPLAY_NAME = "from_display_name"
ATTR_GROUP = "group"
ATTR_IS_ALL_DAY = "is_all_day"
ATTR_IMPORTANCE = "importance"
ATTR_INTERNALREPLY = "internal_reply"
ATTR_LOCATION = "location"
ATTR_MESSAGE_IS_HTML = "message_is_html"
ATTR_OVERDUE_TASKS = "overdue_tasks"
ATTR_PHOTOS = "photos"
ATTR_REMINDER = "reminder"
ATTR_RESPONSE = "response"
ATTR_SENDER = "sender"
ATTR_SEND_RESPONSE = "send_response"
ATTR_SENSITIVITY = "sensitivity"
ATTR_SHOW_AS = "show_as"
ATTR_START = "start"
ATTR_STATE = "state"
ATTR_SUBJECT = "subject"
ATTR_SUMMARY = "summary"
ATTR_TASKS = "tasks"
ATTR_TASK_ID = "task_id"
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
CONF_ALT_AUTH_METHOD = "alt_auth_method"
CONF_AUTO_REPLY_SENSORS = "auto_reply_sensors"
CONF_BODY_CONTAINS = "body_contains"
CONF_CACHE_PATH = "cache_path"
CONF_CALENDAR_NAME = "calendar_name"
CONF_CAL_ID = "cal_id"
CONF_CAL_IDS = "cal_ids"
CONF_CHAT_SENSORS = "chat_sensors"
CONF_CLIENT_ID = "client_id"
CONF_CLIENT_SECRET = "client_secret"  # nosec
CONF_CONFIG_TYPE = "config_type"
CONF_DEVICE_ID = "device_id"
CONF_DOWNLOAD_ATTACHMENTS = "download_attachments"
CONF_EMAIL_SENSORS = "email_sensor"
CONF_ENABLE_UPDATE = "enable_update"
CONF_ENTITIES = "entities"
CONF_EXCLUDE = "exclude"
CONF_GROUPS = "groups"
CONF_HAS_ATTACHMENT = "has_attachment"
CONF_HOURS_BACKWARD_TO_GET = "start_offset"
CONF_HOURS_FORWARD_TO_GET = "end_offset"
CONF_HTML_BODY = "html_body"
CONF_IGNORE_AVAILABILITY = "ignore_availability"
CONF_IMPORTANCE = "importance"
CONF_IS_UNREAD = "is_unread"
CONF_MAIL_FOLDER = "folder"
CONF_MAIL_FROM = "from"
CONF_MAX_ITEMS = "max_items"
CONF_MAX_RESULTS = "max_results"
CONF_OFFSET = "offset"
CONF_QUERY_SENSORS = "query_sensors"
CONF_SEARCH = "search"
CONF_SHOW_COMPLETED = "show_completed"
CONF_STATUS_SENSORS = "status_sensors"
CONF_SUBJECT_CONTAINS = "subject_contains"
CONF_SUBJECT_IS = "subject_is"
CONF_TODO_SENSORS = "todo_sensors"
CONF_TRACK = "track"
CONF_TRACK_NEW_CALENDAR = "track_new_calendar"
CONF_TRACK_NEW = "track_new"
CONF_TASK_LIST_ID = "task_list_id"
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
CONST_UTC_TIMEZONE = "UTC"
DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%S%z"
DEFAULT_CACHE_PATH = ".O365-token-cache"
DEFAULT_HOURS_BACKWARD_TO_GET = 0
DEFAULT_HOURS_FORWARD_TO_GET = 24
DEFAULT_NAME = "O365"
DEFAULT_OFFSET = "!!"
DOMAIN = "o365"

EVENT_HA_EVENT = "ha_event"
EVENT_COMPLETED_TASK = "completed_task"
EVENT_DELETE_TASK = "delete_task"
EVENT_NEW_TASK = "new_task"
EVENT_UPDATE_TASK = "update_task"

EVENT_CREATE_CALENDAR_EVENT = "create_calendar_event"
EVENT_MODIFY_CALENDAR_EVENT = "modify_calendar_event"
EVENT_REMOVE_CALENDAR_EVENT = "remove_calendar_event"
EVENT_RESPOND_CALENDAR_EVENT = "respond_calendar_event"

ICON = "mdi:office"
LEGACY_ACCOUNT_NAME = "converted"
MIN_TIME_BETWEEN_UPDATES = timedelta(minutes=15)
O365_STORAGE = "o365_storage"
PERM_CALENDARS_READ = "Calendars.Read"
PERM_CALENDARS_READ_SHARED = "Calendars.Read.Shared"
PERM_CALENDARS_READWRITE = "Calendars.ReadWrite"
PERM_CALENDARS_READWRITE_SHARED = "Calendars.ReadWrite.Shared"
PERM_CHAT_READ = "Chat.Read"
PERM_GROUP_READ_ALL = "Group.Read.All"
PERM_GROUP_READWRITE_ALL = "Group.ReadWrite.All"
PERM_MAILBOX_SETTINGS = "MailboxSettings.ReadWrite"
PERM_MAIL_READ = "Mail.Read"
PERM_MAIL_READ_SHARED = "Mail.Read.Shared"
PERM_MAIL_READWRITE = "Mail.ReadWrite"
PERM_MAIL_READWRITE_SHARED = "Mail.ReadWrite.Shared"
PERM_MAIL_SEND = "Mail.Send"
PERM_MAIL_SEND_SHARED = "Mail.Send.Shared"
PERM_OFFLINE_ACCESS = "offline_access"
PERM_PRESENCE_READ = "Presence.Read"
PERM_TASKS_READ = "Tasks.Read"
PERM_TASKS_READWRITE = "Tasks.ReadWrite"
PERM_USER_READ = "User.Read"
PERM_MINIMUM_CHAT = [PERM_CHAT_READ, []]
PERM_MINIMUM_GROUP = [PERM_GROUP_READ_ALL, [PERM_GROUP_READWRITE_ALL]]
PERM_MINIMUM_PRESENCE = [PERM_PRESENCE_READ, []]
PERM_MINIMUM_TASKS = [PERM_TASKS_READ, [PERM_TASKS_READWRITE]]
PERM_MINIMUM_TASKS_WRITE = [PERM_TASKS_READWRITE, []]
PERM_MINIMUM_USER = [PERM_USER_READ, []]
PERM_MINIMUM_MAILBOX_SETTINGS = [PERM_MAILBOX_SETTINGS, []]
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

SENSOR_AUTO_REPLY = "auto_reply"
SENSOR_DOMAIN = "sensor"
SENSOR_ENTITY_ID_FORMAT = SENSOR_DOMAIN + ".{}"
SENSOR_MAIL = "inbox"
SENSOR_TEAMS_STATUS = "teams_status"
SENSOR_TEAMS_CHAT = "teams_chat"
SENSOR_TODO = "todo"
TOKEN_FILENAME = "o365{0}.token"  # nosec
YAML_CALENDARS = "{0}_calendars{1}.yaml"
YAML_TASK_LISTS = "{0}_tasks{1}.yaml"
