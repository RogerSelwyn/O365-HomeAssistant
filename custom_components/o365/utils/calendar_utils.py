"""Calendar utilities processes."""

import logging
from datetime import datetime, timedelta

from O365.calendar import Attendee  # pylint: disable=no-name-in-module)

from ..const import (
    ATTR_ATTENDEES,
    ATTR_BODY,
    ATTR_CATEGORIES,
    ATTR_IS_ALL_DAY,
    ATTR_LOCATION,
    ATTR_RRULE,
    ATTR_SENSITIVITY,
    ATTR_SHOW_AS,
    DAYS,
    INDEXES,
)
from .utils import clean_html

_LOGGER = logging.getLogger(__name__)


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


def add_call_data_to_event(event, subject, start, end, **kwargs):
    """Add the call data."""
    event.subject = _add_attribute(subject, event.subject)
    event.body = _add_attribute(kwargs.get(ATTR_BODY, None), event.body)
    event.location = _add_attribute(kwargs.get(ATTR_LOCATION, None), event.location)
    event.categories = _add_attribute(kwargs.get(ATTR_CATEGORIES, []), event.categories)
    event.show_as = _add_attribute(kwargs.get(ATTR_SHOW_AS, None), event.show_as)
    event.start = _add_attribute(start, event.start)
    event.end = _add_attribute(end, event.end)
    event.sensitivity = _add_attribute(
        kwargs.get(ATTR_SENSITIVITY, None), event.sensitivity
    )
    _add_attendees(kwargs.get(ATTR_ATTENDEES, []), event)
    _add_all_day(kwargs.get(ATTR_IS_ALL_DAY, False), event)

    if kwargs.get(ATTR_RRULE, None):
        _rrule_processing(event, kwargs[ATTR_RRULE])
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
