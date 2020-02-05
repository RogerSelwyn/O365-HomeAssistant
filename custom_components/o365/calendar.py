import logging
from datetime import timedelta, datetime
from operator import itemgetter
from homeassistant.helpers.entity import Entity
from homeassistant.util.dt import utcnow
from .const import (
    DOMAIN,
    CALENDAR_SCHEMA,
    CONF_CALENDARS,
    CONF_NAME,
    CONF_CALENDAR_NAME,
    CONF_HOURS_FORWARD_TO_GET,
    CONF_HOURS_BACKWARD_TO_GET,
    DATETIME_FORMAT,
    CALENDAR_SERVICE_CREATE_SCHEMA,
    CALENDAR_SERVICE_MODIFY_SCHEMA,
    CALENDAR_SERVICE_REMOVE_SCHEMA,
    CALENDAR_SERVICE_RESPOND_SCHEMA,
)
from .utils import clean_html, add_call_data_to_event

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
    if len(calendars) < 1:
        calendars = [CALENDAR_SCHEMA({})]
    for calendar in calendars:
        name = calendar.get(CONF_NAME)
        calendar_name = calendar.get(CONF_CALENDAR_NAME)
        hours_forward = calendar.get(CONF_HOURS_FORWARD_TO_GET, 24)
        hours_backward = calendar.get(CONF_HOURS_BACKWARD_TO_GET, 0)
        cal = O365Calendar(
            account, hass, name, calendar_name, hours_forward, hours_backward
        )
        add_devices([cal], True)
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


class O365Calendar(Entity):
    def __init__(
        self, account, hass, name, calendar_name, hours_forward, hours_backward
    ):
        self.account = account
        self.hass = hass
        self._state = None
        self._name = name
        self.calendar_name = calendar_name
        self.hours_forward = hours_forward
        self.hours_backward = hours_backward
        self.schedule = self.account.schedule()
        if self.calendar_name != "" and self.calendar_name != "default_calendar":
            self.calendar = self.schedule.get_calendar(calendar_name=self.calendar_name)
        else:
            self.calendar = self.schedule.get_default_calendar()
        if self.calendar is None:
            raise ValueError(f"Could not find calendar called {self.calendar_name}")
        if not self._name:
            self._name = self.calendar.name
        self._attributes = {}
        # self.get_calendar_events(None)

    @property
    def name(self):
        return self._name

    @property
    def state(self):
        return self._state

    @property
    def device_state_attributes(self):
        return self._attributes

    def update(self):
        self._attributes = self.update_attributes()
        self._state = self.device_state_attributes.get("event_active", False)

    def update_attributes(self):
        attributes = {}
        start_date = datetime.now() + timedelta(hours=self.hours_backward)
        end_date = datetime.now() + timedelta(hours=self.hours_forward)
        query = self.calendar.new_query("start").greater_equal(start_date)
        query.chain("and").on_attribute("end").less_equal(end_date)
        data = []
        now = utcnow()

        for event in self.calendar.get_events(
            limit=999, query=query, include_recurring=True
        ):
            data.append(
                {
                    "subject": event.subject,
                    "body": clean_html(event.body),
                    "location": event.location["displayName"],
                    "categories": event.categories,
                    "sensitivity": event.sensitivity.name,
                    "show_as": event.show_as.name,
                    "is_all_day": event.is_all_day,
                    "attendees": [
                        {"email": x.address, "type": x.attendee_type.value}
                        for x in event.attendees._Attendees__attendees
                    ],
                    "start": event.start.strftime(DATETIME_FORMAT),
                    "end": event.end.strftime(DATETIME_FORMAT),
                    "event_active": event.start <= now and event.end >= now,
                    "event_id": event.object_id,
                    "calendar_id": self.calendar.calendar_id,
                }
            )
        data.sort(key=itemgetter("start"))
        # attributes["data_str_repr"] = json.dumps(data, indent=2)
        attributes["data"] = data
        attributes["calendar_id"] = self.calendar.calendar_id
        attributes["event_active"] = len([x for x in data if x["event_active"]]) > 0
        return attributes


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
