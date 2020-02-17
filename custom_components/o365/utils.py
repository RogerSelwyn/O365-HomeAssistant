import os
import json
import zipfile
from datetime import datetime
from pathlib import Path
from bs4 import BeautifulSoup
from .const import DEFAULT_CACHE_PATH, SCOPE, CONFIG_BASE_DIR, DATETIME_FORMAT
from O365.calendar import Attendee
from homeassistant.util import dt
import logging
from O365.calendar import EventSensitivity

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
        return False
    with open(full_token_path, "r", encoding="UTF-8") as fh:
        raw = fh.read()
        permissions = json.loads(raw)["scope"]
    scope = [x for x in SCOPE if x != "offline_access"]
    return all([x in permissions for x in scope])


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
