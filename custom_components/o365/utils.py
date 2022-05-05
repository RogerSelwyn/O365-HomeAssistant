"""urility processes."""
import json
import logging
import os
import zipfile
from datetime import datetime
from pathlib import Path

import yaml
from bs4 import BeautifulSoup
from homeassistant.const import CONF_NAME
from homeassistant.util import dt
from O365.calendar import Attendee  # pylint: disable=no-name-in-module)
from O365.calendar import EventSensitivity  # pylint: disable=no-name-in-module)
from voluptuous.error import Error as VoluptuousError

from .const import (
    CONF_ACCOUNT_NAME,
    CONF_CAL_ID,
    CONF_CONFIG_TYPE,
    CONF_DEVICE_ID,
    CONF_EMAIL_SENSORS,
    CONF_ENABLE_UPDATE,
    CONF_ENTITIES,
    CONF_QUERY_SENSORS,
    CONF_STATUS_SENSORS,
    CONF_TRACK,
    CONST_CONFIG_TYPE_LIST,
    DATETIME_FORMAT,
    DEFAULT_CACHE_PATH,
    DOMAIN,
    PERM_CALENDARS_READ,
    PERM_CALENDARS_READWRITE,
    PERM_MAIL_READ,
    PERM_MAIL_SEND,
    PERM_MINIMUM_CALENDAR,
    PERM_MINIMUM_MAIL,
    PERM_MINIMUM_PRESENCE,
    PERM_MINIMUM_USER,
    PERM_OFFLINE_ACCESS,
    PERM_PRESENCE_READ,
    PERM_USER_READ,
    TOKEN_FILENAME,
    YAML_CALENDARS,
)
from .schema import CALENDAR_DEVICE_SCHEMA

_LOGGER = logging.getLogger(__name__)


def clean_html(html):
    """Clean the HTML."""
    soup = BeautifulSoup(html, features="html.parser")
    if body := soup.find("body"):
        return body.get_text(" ", strip=True)

    return html


def build_minimum_permissions(config):
    """Build the minimum permissions required to operate."""
    email_sensors = config.get(CONF_EMAIL_SENSORS, [])
    query_sensors = config.get(CONF_QUERY_SENSORS, [])
    status_sensors = config.get(CONF_STATUS_SENSORS, [])
    minimum_permissions = [PERM_MINIMUM_USER, PERM_MINIMUM_CALENDAR]
    if len(email_sensors) > 0 or len(query_sensors) > 0:
        minimum_permissions.append(PERM_MINIMUM_MAIL)
    if len(status_sensors) > 0:
        minimum_permissions.append(PERM_MINIMUM_PRESENCE)

    return minimum_permissions


def build_requested_permissions(config):
    """Build the requested permissions for the scope."""
    email_sensors = config.get(CONF_EMAIL_SENSORS, [])
    query_sensors = config.get(CONF_QUERY_SENSORS, [])
    status_sensors = config.get(CONF_STATUS_SENSORS, [])
    enable_update = config.get(CONF_ENABLE_UPDATE, True)
    scope = [
        PERM_OFFLINE_ACCESS,
        PERM_USER_READ,
    ]
    if enable_update:
        scope.extend((PERM_MAIL_SEND, PERM_CALENDARS_READWRITE))
    else:
        scope.append(PERM_CALENDARS_READ)
    if len(email_sensors) > 0 or len(query_sensors) > 0:
        scope.append(PERM_MAIL_READ)
    if len(status_sensors) > 0:
        scope.append(PERM_PRESENCE_READ)

    return scope


def validate_permissions(
    hass, minimum_permissions, token_path=DEFAULT_CACHE_PATH, filename=TOKEN_FILENAME
):
    """Validate the permissions."""
    permissions = get_permissions(hass, token_path=token_path, filename=filename)
    if not permissions:
        return False

    for minimum_perm in minimum_permissions:
        permission_granted = validate_minimum_permission(minimum_perm, permissions)
        if not permission_granted:
            _LOGGER.warning(
                "Minimum required permissions not granted: %s", minimum_perm
            )
            return False

    return True


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
        _filepath = build_config_file_path(hass, *_filepath.parts[2:])

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


def get_email_attributes(mail, download_attachments):
    """Get the email attributes."""
    data = {
        "subject": mail.subject,
        "body": clean_html(mail.body),
        "received": mail.received.strftime(DATETIME_FORMAT),
        "to": [x.address for x in mail.to],
        "cc": [x.address for x in mail.cc],
        "bcc": [x.address for x in mail.bcc],
        "sender": mail.sender.address,
        "has_attachments": mail.has_attachments,
        "importance": mail.importance.value,
        "is_read": mail.is_read,
    }
    if download_attachments:
        data["attachments"] = [x.name for x in mail.attachments]

    return data


def format_event_data(event, calendar_id):
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
        "calendar_id": calendar_id,
    }


def add_call_data_to_event(event, event_data):
    """Add the call data."""
    if subject := event_data.get("subject"):
        event.subject = subject

    if body := event_data.get("body"):
        event.body = body

    if location := event_data.get("location"):
        event.location = location

    if categories := event_data.get("categories"):
        event.categories = categories

    if show_as := event_data.get("show_as"):
        event.show_as = show_as

    if attendees := event_data.get("attendees"):
        event.attendees.clear()
        event.attendees.add(
            [
                Attendee(x["email"], attendee_type=x["type"], event=event)
                for x in attendees
            ]
        )

    if start := event_data.get("start"):
        event.start = dt.parse_datetime(start)

    if end := event_data.get("end"):
        event.end = dt.parse_datetime(end)

    is_all_day = event_data.get("is_all_day")
    if is_all_day is not None:
        event.is_all_day = is_all_day
        if event.is_all_day:
            event.start = datetime(
                event.start.year, event.start.month, event.start.day, 0, 0, 0
            )
            event.end = datetime(
                event.end.year, event.end.month, event.end.day, 0, 0, 0
            )

    if sensitivity := event_data.get("sensitivity"):
        event.sensitivity = EventSensitivity(sensitivity.lower())
    return event


def load_calendars(path):
    """Load the o365_calendar_devices.yaml."""
    calendars = {}
    try:
        with open(path, encoding="utf8") as file:
            data = yaml.safe_load(file)
            if data is None:
                return {}
            for calendar in data:
                try:
                    calendars[calendar[CONF_CAL_ID]] = CALENDAR_DEVICE_SCHEMA(calendar)
                except VoluptuousError as exception:
                    # keep going
                    _LOGGER.warning("Calendar Invalid Data: %s", exception)
    except FileNotFoundError:
        # When YAML file could not be loaded/did not contain a dict
        return {}

    return calendars


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
    existing_calendars = load_calendars(yaml_filepath)
    cal = get_calendar_info(calendar, track_new_devices)
    if cal[CONF_CAL_ID] in existing_calendars:
        return
    with open(yaml_filepath, "a", encoding="UTF8") as out:
        out.write("\n")
        yaml.dump([cal], out, default_flow_style=False, encoding="UTF8")
        out.close()


def build_config_file_path(hass, filename):
    """Create filename in config path."""
    root = hass.config.config_dir

    return os.path.join(root, filename)


def build_token_filename(conf, conf_type):
    """Create the token file name."""
    config_file = (
        f"_{conf.get(CONF_ACCOUNT_NAME)}" if conf_type == CONST_CONFIG_TYPE_LIST else ""
    )
    return TOKEN_FILENAME.format(config_file)


def build_yaml_filename(conf):
    """Create the token file name."""
    config_file = (
        f"_{conf.get(CONF_ACCOUNT_NAME)}"
        if conf.get(CONF_CONFIG_TYPE) == CONST_CONFIG_TYPE_LIST
        else ""
    )
    return YAML_CALENDARS.format(DOMAIN, config_file)
