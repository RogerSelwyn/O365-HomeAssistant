"""urility processes."""
import json
import logging
import os
import zipfile
from datetime import datetime
from pathlib import Path

import yaml
from bs4 import BeautifulSoup
from homeassistant.util import dt
from O365.calendar import Attendee  # pylint: disable=no-name-in-module)
from O365.calendar import \
    EventSensitivity  # pylint: disable=no-name-in-module)
from voluptuous.error import Error as VoluptuousError

from .const import (CALENDAR_DEVICE_SCHEMA, CONF_CAL_ID, CONF_DEVICE_ID,
                    CONF_ENTITIES, CONF_NAME, CONF_TRACK, CONFIG_BASE_DIR,
                    DATETIME_FORMAT, DEFAULT_CACHE_PATH,
                    MINIMUM_REQUIRED_SCOPES, TOKEN_FILENAME)

_LOGGER = logging.getLogger(__name__)


def clean_html(html):
    """Clean the HTML."""
    soup = BeautifulSoup(html, features="html.parser")
    if body := soup.find("body"):
        return body.get_text(" ", strip=True)

    return html


def validate_permissions(hass, token_path=DEFAULT_CACHE_PATH, filename=TOKEN_FILENAME):
    """Validate the permissions."""
    config_path = build_config_file_path(hass, token_path)
    full_token_path = os.path.join(config_path, filename)
    if not os.path.exists(full_token_path) or not os.path.isfile(full_token_path):
        _LOGGER.warning("Could not locate token at %s", full_token_path)
        return False
    with open(full_token_path, "r", encoding="UTF-8") as file_handle:
        raw = file_handle.read()
        permissions = json.loads(raw)["scope"]
    scope = list(MINIMUM_REQUIRED_SCOPES)
    all_permissions_granted = all(x in permissions for x in scope)
    if not all_permissions_granted:
        _LOGGER.warning("All permissions granted: %s", all_permissions_granted)
    return all_permissions_granted


def get_ha_filepath(filepath):
    """Get the file path."""
    _filepath = Path(filepath)
    if _filepath.parts[0] == "/" and _filepath.parts[1] == "config":
        _filepath = os.path.join(CONFIG_BASE_DIR, *_filepath.parts[2:])

    if not os.path.isfile(_filepath):
        if not os.path.isfile(filepath):
            raise ValueError(f"Could not access file {filepath}")
        return filepath
    return _filepath


def zip_files(filespaths, zip_name="archive.zip"):
    """Zip the files."""
    if Path(zip_name).suffix != ".zip":
        zip_name += ".zip"

    with zipfile.ZipFile(zip_name, mode="w") as zip_file:
        for file_path in filespaths:
            zip_file.write(file_path, os.path.basename(file_path))
    return zip_name


def get_email_attributes(mail, download_attachments = True):
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
    data = {
        "summary": event.subject,
        "description": clean_html(event.body),
        "location": event.location["displayName"],
        "categories": event.categories,
        "sensitivity": event.sensitivity.name,
        "show_as": event.show_as.name,
        "all_day": event.is_all_day,
        "attendees": [
            {"email": x.address, "type": x.attendee_type.value}
            for x in event.attendees._Attendees__attendees  # pylint: disable=protected-access
        ],
        "start": event.start,
        "end": event.end,
        "uid": event.object_id,
        "calendar_id": calendar_id,
    }
    data["subject"] = data["summary"]
    data["body"] = data["description"]
    return data


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
    existing_calendars = load_calendars(build_config_file_path(hass, path))
    cal = get_calendar_info(calendar, track_new_devices)
    if cal[CONF_CAL_ID] in existing_calendars:
        return
    with open(path, "a", encoding="UTF8") as out:
        out.write("\n")
        yaml.dump([cal], out, default_flow_style=False, encoding="UTF8")


def build_config_file_path(hass, filename):
    """Create filename in config path."""
    root = hass.config.config_dir

    return os.path.join(root, filename)
