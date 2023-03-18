"""urility processes."""
import json
import logging
import os
import shutil
import zipfile
from datetime import datetime
from pathlib import Path

import yaml
from bs4 import BeautifulSoup
from homeassistant.const import CONF_ENABLED, CONF_NAME
from homeassistant.helpers.network import get_url
from voluptuous.error import Error as VoluptuousError

from O365.calendar import Attendee  # pylint: disable=no-name-in-module)

from .const import (
    AUTH_CALLBACK_PATH_ALT,
    AUTH_CALLBACK_PATH_DEFAULT,
    CONF_ACCOUNT_NAME,
    CONF_AUTO_REPLY_SENSORS,
    CONF_CAL_ID,
    CONF_CHAT_SENSORS,
    CONF_CONFIG_TYPE,
    CONF_DEVICE_ID,
    CONF_EMAIL_SENSORS,
    CONF_ENABLE_UPDATE,
    CONF_ENTITIES,
    CONF_GROUPS,
    CONF_QUERY_SENSORS,
    CONF_STATUS_SENSORS,
    CONF_TASK_LIST_ID,
    CONF_TODO_SENSORS,
    CONF_TRACK,
    CONST_CONFIG_TYPE_LIST,
    CONST_GROUP,
    DATETIME_FORMAT,
    DAYS,
    DEFAULT_CACHE_PATH,
    DOMAIN,
    INDEXES,
    O365_STORAGE,
    PERM_CALENDARS_READ,
    PERM_CALENDARS_READWRITE,
    PERM_CHAT_READ,
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
    PERM_TASKS_READ,
    PERM_TASKS_READWRITE,
    PERM_USER_READ,
    TOKEN_FILENAME,
    YAML_CALENDARS,
)
from .schema import CALENDAR_DEVICE_SCHEMA, TASK_LIST_SCHEMA

_LOGGER = logging.getLogger(__name__)


def clean_html(html):
    """Clean the HTML."""
    soup = BeautifulSoup(html, features="html.parser")
    if body := soup.find("body"):
        # get text
        text = body.get_text()

        # break into lines and remove leading and trailing space on each
        lines = (line.strip() for line in text.splitlines())
        # break multi-headlines into a line each
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        # drop blank lines
        text = "\n".join(chunk for chunk in chunks if chunk)
        return text.replace("\xa0", " ")

    return html


def safe_html(html):
    """Make the HTML safe."""
    soup = BeautifulSoup(html, features="html.parser")
    if soup.find("body"):
        blacklist = ["script", "style"]
        for tag in soup.findAll():
            if tag.name.lower() in blacklist:
                # blacklisted tags are removed in their entirety
                tag.extract()
        return str(soup.find("body"))
    return html


def build_minimum_permissions(hass, config, conf_type):
    """Build the minimum permissions required to operate."""
    email_sensors = config.get(CONF_EMAIL_SENSORS, [])
    query_sensors = config.get(CONF_QUERY_SENSORS, [])
    status_sensors = config.get(CONF_STATUS_SENSORS, [])
    chat_sensors = config.get(CONF_CHAT_SENSORS, [])
    todo_sensors = config.get(CONF_TODO_SENSORS, [])
    auto_reply_sensors = config.get(CONF_AUTO_REPLY_SENSORS, [])
    minimum_permissions = [PERM_MINIMUM_USER, PERM_MINIMUM_CALENDAR]
    if len(email_sensors) > 0 or len(query_sensors) > 0:
        minimum_permissions.append(PERM_MINIMUM_MAIL)
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
    if enable_update:
        scope.extend((PERM_MAIL_SEND, PERM_CALENDARS_READWRITE))
    else:
        scope.append(PERM_CALENDARS_READ)
    if groups:
        if enable_update:
            scope.append(PERM_GROUP_READWRITE_ALL)
        else:
            scope.append(PERM_GROUP_READ_ALL)
    if len(email_sensors) > 0 or len(query_sensors) > 0:
        scope.append(PERM_MAIL_READ)
    if len(auto_reply_sensors) > 0:
        scope.append(PERM_MAILBOX_SETTINGS)
    if len(status_sensors) > 0:
        scope.append(PERM_PRESENCE_READ)
    if len(chat_sensors) > 0:
        scope.append(PERM_CHAT_READ)
    if todo_sensors and todo_sensors.get(CONF_ENABLED, False):
        if enable_update:
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
        return False

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


def get_ha_filepath(hass, filepath):
    """Get the file path."""
    _filepath = Path(filepath)
    if _filepath.parts[0] == "/" and _filepath.parts[1] == "config":
        _filepath = os.path.join(hass.config.config_dir, *_filepath.parts[2:])

    if not os.path.isfile(_filepath):
        if not os.path.isfile(filepath):
            raise ValueError(f"Could not access file {filepath} at {_filepath}")
        return filepath
    return _filepath


def zip_files(filespaths, zip_name):
    """Zip the files."""
    if not zip_name:
        zip_name = "archive.zip"
    if Path(zip_name).suffix != ".zip":
        zip_name += ".zip"

    with zipfile.ZipFile(zip_name, mode="w") as zip_file:
        for file_path in filespaths:
            zip_file.write(file_path, os.path.basename(file_path))
    return zip_name


def get_email_attributes(mail, download_attachments, html_body):
    """Get the email attributes."""
    data = {
        "subject": mail.subject,
        "received": mail.received.strftime(DATETIME_FORMAT),
        "to": [x.address for x in mail.to],
        "cc": [x.address for x in mail.cc],
        "sender": mail.sender.address,
        "has_attachments": mail.has_attachments,
        "importance": mail.importance.value,
        "is_read": mail.is_read,
    }
    data["body"] = safe_html(mail.body) if html_body else clean_html(mail.body)
    if download_attachments:
        data["attachments"] = [x.name for x in mail.attachments]

    return data


def format_event_data(event):
    """Format the event data."""
    return {
        "summary": event.subject,
        "start": event.start,
        "end": event.end,
        "all_day": event.is_all_day,
        "description": clean_html(event.body),
        "location": event.location["displayName"],
        "categories": event.categories,
        "sensitivity": event.sensitivity.name,
        "show_as": event.show_as.name,
        "attendees": [
            {"email": x.address, "type": x.attendee_type.value}
            for x in event.attendees._Attendees__attendees  # pylint: disable=protected-access
        ],
        "uid": event.object_id,
    }


def add_call_data_to_event(
    event,
    subject,
    start,
    end,
    body,
    location,
    categories,
    sensitivity,
    show_as,
    is_all_day,
    attendees,
    rrule,
):
    """Add the call data."""
    if subject:
        event.subject = subject

    if body:
        event.body = body

    if location:
        event.location = location

    if categories:
        event.categories = categories

    if show_as:
        event.show_as = show_as

    if attendees:
        event.attendees.clear()
        event.attendees.add(
            [
                Attendee(x["email"], attendee_type=x["type"], event=event)
                for x in attendees
            ]
        )

    if start:
        event.start = start

    if end:
        event.end = end

    if is_all_day is not None:
        event.is_all_day = is_all_day
        if event.is_all_day:
            event.start = datetime(
                event.start.year, event.start.month, event.start.day, 0, 0, 0
            )
            event.end = datetime(
                event.end.year, event.end.month, event.end.day, 0, 0, 0
            )

    if sensitivity:
        event.sensitivity = sensitivity
    if rrule:
        _rrule_processing(event, rrule)
    return event


def _rrule_processing(event, rrule):
    rules = {}
    for item in rrule.split(";"):
        keys = item.split("=")
        rules[keys[0]] = keys[1]

    kwargs = {}
    if "COUNT" in rules:
        kwargs["occurrences"] = int(rules["COUNT"])
    if "UNTIL" in rules:
        end = datetime.strptime(rules["UNTIL"], "%Y%m%dT%H%M%S")
        end.replace(tzinfo=event.start.tzinfo)
        kwargs["end"] = end
    interval = int(rules["INTERVAL"]) if "INTERVAL" in rules else 1
    if "BYDAY" in rules:
        days, index = _process_byday(rules["BYDAY"])
        kwargs["days_of_week"] = days
        if index:
            kwargs["index"] = index

    if rules["FREQ"] == "YEARLY":
        kwargs["day_of_month"] = event.start.day
        event.recurrence.set_yearly(interval, event.start.month, **kwargs)

    if rules["FREQ"] == "MONTHLY":
        if "BYDAY" not in rules:
            kwargs["day_of_month"] = event.start.day
        event.recurrence.set_monthly(interval, **kwargs)

    if rules["FREQ"] == "WEEKLY":
        kwargs["first_day_of_week"] = "sunday"
        event.recurrence.set_weekly(interval, **kwargs)

    if rules["FREQ"] == "DAILY":
        event.recurrence.set_daily(interval, **kwargs)


def _process_byday(byday):
    days = []
    for item in byday.split(","):
        if len(item) > 2:
            days.append(DAYS[item[2:4]])
            index = INDEXES[item[:2]]
        else:
            days.append(DAYS[item[:2]])
            index = None
    return days, index


def load_yaml_file(path, item_id, item_schema):
    """Load the o365 yaml file."""
    items = {}
    try:
        with open(path, encoding="utf8") as file:
            data = yaml.safe_load(file)
            if data is None:
                return {}
            for item in data:
                try:
                    items[item[item_id]] = item_schema(item)
                except VoluptuousError as exception:
                    # keep going
                    _LOGGER.warning("Invalid Data: %s", exception)
    except FileNotFoundError:
        # When YAML file could not be loaded/did not contain a dict
        return {}

    return items


def get_calendar_info(calendar, track_new_devices):
    """Convert data from O365 into DEVICE_SCHEMA."""
    return CALENDAR_DEVICE_SCHEMA(
        {
            CONF_CAL_ID: calendar.calendar_id,
            CONF_ENTITIES: [
                {
                    CONF_TRACK: track_new_devices,
                    CONF_NAME: calendar.name,
                    CONF_DEVICE_ID: calendar.name,
                }
            ],
        }
    )


def update_calendar_file(path, calendar, hass, track_new_devices):
    """Update the calendar file."""
    yaml_filepath = build_config_file_path(hass, path)
    existing_calendars = load_yaml_file(
        yaml_filepath, CONF_CAL_ID, CALENDAR_DEVICE_SCHEMA
    )
    cal = get_calendar_info(calendar, track_new_devices)
    if cal[CONF_CAL_ID] in existing_calendars:
        return
    with open(yaml_filepath, "a", encoding="UTF8") as out:
        out.write("\n")
        yaml.dump([cal], out, default_flow_style=False, encoding="UTF8")
        out.close()


def get_task_list_info(task_list, track_new_devices):
    """Convert data from O365 into DEVICE_SCHEMA."""
    return TASK_LIST_SCHEMA(
        {
            CONF_TASK_LIST_ID: task_list.folder_id,
            CONF_NAME: task_list.name,
            CONF_TRACK: track_new_devices,
        }
    )


def update_task_list_file(path, task_list, hass, track_new_devices):
    """Update the calendar file."""
    yaml_filepath = build_config_file_path(hass, path)
    existing_task_lists = load_yaml_file(
        yaml_filepath, CONF_TASK_LIST_ID, TASK_LIST_SCHEMA
    )
    task_list = get_task_list_info(task_list, track_new_devices)
    if task_list[CONF_TASK_LIST_ID] in existing_task_lists:
        return
    with open(yaml_filepath, "a", encoding="UTF8") as out:
        out.write("\n")
        yaml.dump([task_list], out, default_flow_style=False, encoding="UTF8")
        out.close()


def build_config_file_path(hass, filepath):
    """Create config path."""
    root = hass.config.config_dir

    return os.path.join(root, O365_STORAGE, filepath)


def build_token_filename(conf, conf_type):
    """Create the token file name."""
    config_file = (
        f"_{conf.get(CONF_ACCOUNT_NAME)}" if conf_type == CONST_CONFIG_TYPE_LIST else ""
    )
    return TOKEN_FILENAME.format(config_file)


def build_yaml_filename(conf, filename, conf_type=None):
    """Create the token file name."""
    if conf_type:
        config_file = f"_{conf.get(CONF_ACCOUNT_NAME)}"
    else:
        config_file = (
            f"_{conf.get(CONF_ACCOUNT_NAME)}"
            if conf.get(CONF_CONFIG_TYPE) == CONST_CONFIG_TYPE_LIST
            else ""
        )
    return filename.format(DOMAIN, config_file)


def check_file_location(hass, filepath, newpath):
    """Check if file has been moved. If not move it. This function to be removed 2023/05/30."""
    root = hass.config.config_dir
    oldpath = os.path.join(
        root,
        filepath,
    )
    if os.path.exists(oldpath):
        shutil.move(oldpath, newpath)


def get_callback_url(hass, alt_config):
    """Get the callback URL."""
    if alt_config:
        return f"{get_url(hass, prefer_external=True)}{AUTH_CALLBACK_PATH_ALT}"

    return AUTH_CALLBACK_PATH_DEFAULT
