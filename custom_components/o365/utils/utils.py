"""Utilities processes."""
import logging
from datetime import datetime, timedelta

from bs4 import BeautifulSoup
from homeassistant.helpers.entity import async_generate_entity_id

from ..const import DATETIME_FORMAT, SENSOR_ENTITY_ID_FORMAT

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
        "start": get_hass_date(event.start, event.is_all_day),
        "end": get_hass_date(get_end_date(event), event.is_all_day),
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


def get_hass_date(obj, is_all_day):
    """Get the date."""
    return obj if isinstance(obj, datetime) and not is_all_day else obj.date()


def get_end_date(obj):
    """Get the end date."""
    if hasattr(obj, "end"):
        return obj.end

    if hasattr(obj, "duration"):
        return obj.start + obj.duration.value

    return obj.start + timedelta(days=1)


def get_start_date(obj):
    """Get the start date."""
    return obj.start


def build_entity_id(hass, name):
    """Build and entity ID."""
    return async_generate_entity_id(
        SENSOR_ENTITY_ID_FORMAT,
        name,
        hass=hass,
    )
