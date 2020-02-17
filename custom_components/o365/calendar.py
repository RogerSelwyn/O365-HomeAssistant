import logging
import copy
from operator import attrgetter, itemgetter
from datetime import timedelta, datetime
from homeassistant.util import Throttle, dt
from homeassistant.components.calendar import (
    CalendarEventDevice,
    calculate_offset,
    is_offset_reached,
)
from .const import (
    CALENDAR_SCHEMA,
    CONF_CALENDARS,
    CONF_NAME,
    CONF_CALENDAR_NAME,
    CONF_HOURS_FORWARD_TO_GET,
    CONF_HOURS_BACKWARD_TO_GET,
    CALENDAR_SERVICE_CREATE_SCHEMA,
    CALENDAR_SERVICE_MODIFY_SCHEMA,
    CALENDAR_SERVICE_REMOVE_SCHEMA,
    CALENDAR_SERVICE_RESPOND_SCHEMA,
    MIN_TIME_BETWEEN_UPDATES,
    OFFSET,
    DOMAIN,
)
from .utils import clean_html, add_call_data_to_event, format_event_data

_LOGGER = logging.getLogger(__name__)


def setup_platform(hass, config, add_devices, discovery_info=None):
    """Set up the O365 platform."""
    if discovery_info is None:
        return

    account = hass.data[DOMAIN]["account"]
    is_authenticated = account.is_authenticated
    if not is_authenticated:
        return False

    calendars = hass.data[DOMAIN].get(CONF_CALENDARS, [])
    devices = []
    if len(calendars) < 1:
        calendars = [CALENDAR_SCHEMA({})]
    for calendar in calendars:
        name = calendar.get(CONF_NAME)
        calendar_name = calendar.get(CONF_CALENDAR_NAME)
        hours_forward = calendar.get(CONF_HOURS_FORWARD_TO_GET, 24)
        hours_backward = calendar.get(CONF_HOURS_BACKWARD_TO_GET, 0)
        cal = O365CalendarEventDevice(
            account, name, calendar_name, hours_backward, hours_forward,
        )
        devices.append(cal)
    add_devices(devices, True)
    calendar_services = CalendarServices(account)
    hass.services.register(
        DOMAIN, f"modify_calendar_event", calendar_services.modify_calendar_event
    )
    hass.services.register(
        DOMAIN, f"create_calendar_event", calendar_services.create_calendar_event
    )
    hass.services.register(
        DOMAIN, f"remove_calendar_event", calendar_services.remove_calendar_event
    )
    hass.services.register(
        DOMAIN, f"respond_calendar_event", calendar_services.respond_calendar_event
    )
    return True


class O365CalendarEventDevice(CalendarEventDevice):
    def __init__(self, account, name, calendar_name, start_offset, end_offset):
        self.data = O365CalendarData(account, calendar_name)
        self.start_offset = start_offset
        self.end_offset = end_offset
        self._event = None
        self._name = name
        if self._name is None:
            self._name = self.data.calendar.name
        self._offset_reached = False
        self._data_attribute = []

    @property
    def device_state_attributes(self):
        return {"offset_reached": self._offset_reached, "data": self._data_attribute}

    @property
    def event(self):
        return self._event

    @property
    def name(self):
        return self._name

    async def async_get_events(self, hass, start_date, end_date):
        return await self.data.async_get_events(hass, start_date, end_date)

    async def async_update(self):
        self.data.update()
        event = copy.deepcopy(self.data.event)
        if event is None:
            self._event = event
            return
        event = calculate_offset(event, OFFSET)
        self._offset_reached = is_offset_reached(event)
        events = list(
            self.data.o365_get_events(
                datetime.now() + timedelta(hours=self.start_offset),
                datetime.now() + timedelta(hours=self.end_offset),
            )
        )
        self._data_attribute = [
            format_event_data(x, self.data.calendar.calendar_id) for x in events
        ]
        self._data_attribute.sort(key=itemgetter("start"))
        self._event = event


class O365CalendarData:
    def __init__(self, account, calendar_name):
        self.account = account
        self.calendar_name = calendar_name
        self.schedule = self.account.schedule()
        if self.calendar_name != "" and self.calendar_name != "default_calendar":
            self.calendar = self.schedule.get_calendar(calendar_name=self.calendar_name)
        else:
            self.calendar = self.schedule.get_default_calendar()
        if self.calendar is None:
            raise ValueError(f"Could not find calendar called {self.calendar_name}")

        self.event = None

    def o365_get_events(self, start_date, end_date):
        query = self.calendar.new_query("start").greater_equal(start_date)
        query.chain("and").on_attribute("end").less_equal(end_date)
        return self.calendar.get_events(limit=999, query=query, include_recurring=True)

    async def async_get_events(self, hass, start_date, end_date):
        vevent_list = list(
            await hass.async_add_job(self.o365_get_events, start_date, end_date)
        )
        vevent_list.sort(key=attrgetter("start"))
        event_list = []
        for event in vevent_list:
            data = format_event_data(event, self.calendar.calendar_id)
            data["start"] = self.get_hass_date(data["start"])
            data["end"] = self.get_hass_date(data["end"])
            event_list.append(data)

        return event_list

    @Throttle(MIN_TIME_BETWEEN_UPDATES)
    def update(self):
        results = self.o365_get_events(
            dt.start_of_local_day(), dt.start_of_local_day() + timedelta(days=1)
        )
        results = list(results)
        results.sort(key=lambda x: self.to_datetime(x.start))

        vevent = next((event for event in results if not self.is_over(event)), None,)

        if vevent is None:
            _LOGGER.debug(
                "No matching event found in the %d results for %s",
                len(results),
                self.calendar.name,
            )
            self.event = None
            return

        self.event = {
            "summary": vevent.subject,
            "start": self.get_hass_date(vevent.start),
            "end": self.get_hass_date(self.get_end_date(vevent)),
            "location": vevent.location,
            "description": clean_html(vevent.body),
        }

    @staticmethod
    def is_all_day(vevent):
        return vevent.is_all_day

    @staticmethod
    def is_over(vevent):
        return dt.now() >= O365CalendarData.to_datetime(
            O365CalendarData.get_end_date(vevent)
        )

    @staticmethod
    def get_hass_date(obj):
        if isinstance(obj, datetime):
            return {"dateTime": obj.isoformat()}

        return {"date": obj.isoformat()}

    @staticmethod
    def to_datetime(obj):
        if isinstance(obj, datetime):
            if obj.tzinfo is None:
                return obj.replace(tzinfo=dt.DEFAULT_TIME_ZONE)
            return obj
        return dt.as_local(dt.dt.datetime.combine(obj, dt.dt.time.min))

    @staticmethod
    def get_end_date(obj):
        if hasattr(obj, "end"):
            enddate = obj.end

        elif hasattr(obj, "duration"):
            enddate = obj.start + obj.duration.value

        else:
            enddate = obj.start + timedelta(days=1)

        return enddate


class CalendarServices:
    def __init__(self, account):
        self.account = account
        self.schedule = self.account.schedule()

    def modify_calendar_event(self, call):
        event_data = call.data
        CALENDAR_SERVICE_MODIFY_SCHEMA({k: v for k, v in event_data.items()})
        calendar = self.schedule.get_calendar(calendar_id=event_data.get("calendar_id"))
        event = calendar.get_event(event_data["event_id"])
        event = add_call_data_to_event(event, call.data)
        event.save()
        return

    def create_calendar_event(self, call):
        event_data = call.data
        CALENDAR_SERVICE_CREATE_SCHEMA({k: v for k, v in event_data.items()})
        calendar = self.schedule.get_calendar(calendar_id=event_data.get("calendar_id"))
        event = calendar.new_event()
        event = add_call_data_to_event(event, call.data)
        event.save()
        return

    def remove_calendar_event(self, call):
        event_data = call.data
        CALENDAR_SERVICE_REMOVE_SCHEMA({k: v for k, v in event_data.items()})
        calendar = self.schedule.get_calendar(calendar_id=event_data.get("calendar_id"))
        event = calendar.get_event(event_data["event_id"])
        event.delete()
        return

    def respond_calendar_event(self, call):
        event_data = call.data
        CALENDAR_SERVICE_RESPOND_SCHEMA({k: v for k, v in event_data.items()})
        calendar = self.schedule.get_calendar(calendar_id=event_data.get("calendar_id"))
        event = calendar.get_event(event_data["event_id"])
        response = event_data.get("response")

        responses = ["accept", "tentative", "decline"]
        if response is None:
            raise ValueError("response not set")
        if response.lower() not in responses:
            raise ValueError(f"response must be one of {', '.join(responses)}")

        send_response = event_data.get("send_response", True)
        if response.lower() == "accept":
            event.accept_event(event_data.get("message"), send_response=send_response)

        elif response.lower() == "tentative":
            event.accept_event(
                event_data.get("message"), tentatively=True, send_response=send_response
            )

        elif response.lower() == "decline":
            event.decline_event(event_data.get("message"), send_response=send_response)

        return
