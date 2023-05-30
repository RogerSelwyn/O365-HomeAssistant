"""Utilities processes."""
import logging
from datetime import datetime, timedelta

from bs4 import BeautifulSoup
from homeassistant.helpers.entity import async_generate_entity_id
from O365.calendar import Attendee  # pylint: disable=no-name-in-module)

from ..const import DATETIME_FORMAT, DAYS, INDEXES, SENSOR_ENTITY_ID_FORMAT

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
    event.subject = _add_attribute(subject, event.subject)
    event.body = _add_attribute(body, event.body)
    event.location = _add_attribute(location, event.location)
    event.categories = _add_attribute(categories, event.categories)
    event.show_as = _add_attribute(show_as, event.show_as)
    event.start = _add_attribute(start, event.start)
    event.end = _add_attribute(end, event.end)
    event.sensitivity = _add_attribute(sensitivity, event.sensitivity)
    _add_attendees(attendees, event)
    _add_all_day(is_all_day, event)

    if rrule:
        _rrule_processing(event, rrule)
    return event


def _add_attribute(attribute, event_attribute):
    return attribute or event_attribute


def _add_attendees(attendees, event):
    if attendees:
        event.attendees.clear()
        event.attendees.add(
            [
                Attendee(x["email"], attendee_type=x["type"], event=event)
                for x in attendees
            ]
        )


def _add_all_day(is_all_day, event):
    if is_all_day is not None:
        event.is_all_day = is_all_day
        if event.is_all_day:
            event.start = datetime(
                event.start.year, event.start.month, event.start.day, 0, 0, 0
            )
            event.end = datetime(
                event.end.year, event.end.month, event.end.day, 0, 0, 0
            )


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


def build_entity_id(hass, name):
    """Build and entity ID."""
    return async_generate_entity_id(
        SENSOR_ENTITY_ID_FORMAT,
        name,
        hass=hass,
    )
