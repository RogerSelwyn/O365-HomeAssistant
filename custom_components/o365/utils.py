import os
import json
import zipfile
from datetime import datetime
from pathlib import Path
from bs4 import BeautifulSoup
from .const import (
    DEFAULT_CACHE_PATH,
    MINIMUM_REQUIRED_SCOPES,
    CONFIG_BASE_DIR,
    DATETIME_FORMAT,
    CALENDAR_DEVICE_SCHEMA,
    CONF_CAL_ID,
    CONF_ENTITIES,
    CONF_TRACK,
    CONF_NAME,
    CONF_DEVICE_ID,
)
from O365.calendar import Attendee
from homeassistant.util import dt
import logging
from O365.calendar import EventSensitivity
import yaml
from voluptuous.error import Error as VoluptuousError

_LOGGER = logging.getLogger(__name__)


def clean_html(html):
    soup = BeautifulSoup(html, features="html.parser")
    body = soup.find("body")
    if body:
        return soup.find("body").get_text(" ", strip=True)
    else:
        return html


def validate_permissions(token_path=DEFAULT_CACHE_PATH, token_filename="o365.token"):
    full_token_path = os.path.join(token_path, token_filename)
    if not os.path.exists(full_token_path) or not os.path.isfile(full_token_path):
        _LOGGER.warning(f"Could not loacte token at {full_token_path}")
        return False
    with open(full_token_path, "r", encoding="UTF-8") as fh:
        raw = fh.read()
        permissions = json.loads(raw)["scope"]
    scope = [x for x in MINIMUM_REQUIRED_SCOPES]
    all_permissions_granted = all([x in permissions for x in scope])
    if not all_permissions_granted:
        _LOGGER.warning(f"All permissions granted: {all_permissions_granted}")
    return all_permissions_granted


def get_ha_filepath(filepath):
    _filepath = Path(filepath)
    if _filepath.parts[0] == "/" and _filepath.parts[1] == "config":
        _filepath = os.path.join(CONFIG_BASE_DIR, *_filepath.parts[2:])

    if not os.path.isfile(_filepath):
        if not os.path.isfile(filepath):
            raise ValueError(f"Could not access file {filepath}")
        else:
            return filepath
    return _filepath


def zip_files(filespaths, zip_name="archive.zip"):
    if Path(zip_name).suffix != ".zip":
        zip_name += ".zip"

    with zipfile.ZipFile(zip_name, mode="w") as zf:
        for f in filespaths:
            zf.write(f, os.path.basename(f))
    return zip_name


def get_email_attributes(mail):
    return {
        "subject": mail.subject,
        "body": clean_html(mail.body),
        "received": mail.received.strftime(DATETIME_FORMAT),
        "to": [x.address for x in mail.to],
        "cc": [x.address for x in mail.cc],
        "bcc": [x.address for x in mail.bcc],
        "sender": mail.sender.address,
        "has_attachments": mail.has_attachments,
        "attachments": [x.name for x in mail.attachments],
    }


def format_event_data(event, calendar_id):
    data = {
        "summary": event.subject,
        "description": clean_html(event.body),
        "location": event.location["displayName"],
        "categories": event.categories,
        "sensitivity": event.sensitivity.name,
        "show_as": event.show_as.name,
        "is_all_day": event.is_all_day,
        "attendees": [
            {"email": x.address, "type": x.attendee_type.value}
            for x in event.attendees._Attendees__attendees
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
    subject = event_data.get("subject")
    if subject:
        event.subject = subject

    body = event_data.get("body")
    if body:
        event.body = body

    location = event_data.get("location")
    if location:
        event.location = location

    categories = event_data.get("categories")
    if categories:
        event.categories = categories

    show_as = event_data.get("show_as")
    if show_as:
        event.show_as = show_as

    attendees = event_data.get("attendees")
    if attendees:
        event.attendees.clear()
        event.attendees.add(
            [
                Attendee(x["email"], attendee_type=x["type"], event=event)
                for x in attendees
            ]
        )

    start = event_data.get("start")
    if start:
        event.start = dt.parse_datetime(start)

    end = event_data.get("end")
    if end:
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

    sensitivity = event_data.get("sensitivity")
    if sensitivity:
        event.sensitivity = EventSensitivity(sensitivity.lower())
    return event


def load_calendars(path):
    """Load the o365_calendar_devices.yaml."""
    calendars = {}
    try:
        with open(path) as file:
            data = yaml.safe_load(file)
            if data is None:
                return {}
            for calendar in data:
                try:
                    calendars.update(
                        {calendar[CONF_CAL_ID]: CALENDAR_DEVICE_SCHEMA(calendar)}
                    )
                except VoluptuousError as exception:
                    # keep going
                    _LOGGER.warning("Calendar Invalid Data: %s", exception)
    except FileNotFoundError:
        # When YAML file could not be loaded/did not contain a dict
        return {}

    return calendars


def get_calendar_info(hass, calendar, track_new_devices):
    """Convert data from O365 into DEVICE_SCHEMA."""
    calendar_info = CALENDAR_DEVICE_SCHEMA(
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
    return calendar_info


def update_calendar_file(path, calendar, hass, track_new_devices):
    existing_calendars = load_calendars(path)
    cal = get_calendar_info(hass, calendar, track_new_devices)
    if cal[CONF_CAL_ID] in existing_calendars:
        return
    with open(path, "a", encoding="UTF8") as out:
        out.write("\n")
        yaml.dump([cal], out, default_flow_style=False, encoding="UTF8")
