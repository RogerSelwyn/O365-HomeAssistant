"""Main calendar processing."""
import functools as ft
import logging
from copy import deepcopy
from datetime import datetime, timedelta
from operator import attrgetter, itemgetter

from homeassistant.components.calendar import CalendarEventDevice, is_offset_reached

try:
    from homeassistant.components.calendar import calculate_offset
except ImportError:
    from homeassistant.components.calendar import extract_offset

from homeassistant.const import CONF_NAME
from homeassistant.helpers.entity import generate_entity_id
from homeassistant.util import Throttle, dt
from requests.exceptions import HTTPError

from .const import (
    ATTR_CALENDAR_ID,
    ATTR_ENTITY_ID,
    CALENDAR_ENTITY_ID_FORMAT,
    CALENDAR_SERVICE_CREATE_SCHEMA,
    CALENDAR_SERVICE_MODIFY_SCHEMA,
    CALENDAR_SERVICE_REMOVE_SCHEMA,
    CALENDAR_SERVICE_RESPOND_SCHEMA,
    CONF_ACCOUNT,
    CONF_ACCOUNT_NAME,
    CONF_CAL_IDS,
    CONF_CONFIG_TYPE,
    CONF_DEVICE_ID,
    CONF_ENABLE_UPDATE,
    CONF_ENTITIES,
    CONF_HOURS_BACKWARD_TO_GET,
    CONF_HOURS_FORWARD_TO_GET,
    CONF_MAX_RESULTS,
    CONF_SEARCH,
    CONF_TRACK,
    CONF_TRACK_NEW,
    CONST_CONFIG_TYPE_LIST,
    DEFAULT_OFFSET,
    DOMAIN,
    MIN_TIME_BETWEEN_UPDATES,
    PERM_CALENDARS_READWRITE,
    PERM_MINIMUM_CALENDAR_WRITE,
)
from .utils import (
    add_call_data_to_event,
    build_config_file_path,
    build_token_filename,
    build_yaml_filename,
    clean_html,
    format_event_data,
    get_permissions,
    load_calendars,
    update_calendar_file,
    validate_minimum_permission,
)

_LOGGER = logging.getLogger(__name__)


def setup_platform(
    hass, config, add_entities, discovery_info=None
):  # pylint: disable=unused-argument
    """Set up the O365 platform."""
    if discovery_info is None:
        return None

    account_name = discovery_info[CONF_ACCOUNT_NAME]
    conf = hass.data[DOMAIN][account_name]
    account = conf[CONF_ACCOUNT]
    if not account.is_authenticated:
        return False

    cal_ids = _setup_add_entities(hass, account, add_entities, conf)
    hass.data[DOMAIN][account_name][CONF_CAL_IDS] = cal_ids
    _setup_register_services(hass, conf)

    return True


def _setup_add_entities(hass, account, add_entities, conf):
    yaml_filename = build_yaml_filename(conf)
    calendars = load_calendars(build_config_file_path(hass, yaml_filename))
    cal_ids = {}

    for cal_id, calendar in calendars.items():
        for entity in calendar.get(CONF_ENTITIES):
            if not entity[CONF_TRACK]:
                continue
            entity_id = _build_entity_id(hass, entity, conf)
            # _LOGGER.debug("Connecting to calendar: %s", cal_id)
            try:
                cal = O365CalendarEventDevice(account, cal_id, entity, entity_id)
            except HTTPError:
                _LOGGER.warning(
                    "No permission for calendar, please remove - Name: %s; Device: %s;",
                    entity[CONF_NAME],
                    entity[CONF_DEVICE_ID],
                )
                continue

            cal_ids[entity_id] = cal_id
            add_entities([cal], True)
    return cal_ids


def _build_entity_id(hass, entity, conf):
    entity_suffix = (
        f"_{conf[CONF_ACCOUNT_NAME]}"
        if (conf[CONF_CONFIG_TYPE] == CONST_CONFIG_TYPE_LIST)
        else ""
    )

    return generate_entity_id(
        CALENDAR_ENTITY_ID_FORMAT,
        f"{entity.get(CONF_DEVICE_ID)}{entity_suffix}",
        hass=hass,
    )


def _setup_register_services(hass, conf):
    calendar_services = CalendarServices(hass)
    calendar_services.scan_for_calendars(None)

    if conf[CONF_ENABLE_UPDATE]:
        hass.services.register(
            DOMAIN, "modify_calendar_event", calendar_services.modify_calendar_event
        )
        hass.services.register(
            DOMAIN, "create_calendar_event", calendar_services.create_calendar_event
        )
        hass.services.register(
            DOMAIN, "remove_calendar_event", calendar_services.remove_calendar_event
        )
        hass.services.register(
            DOMAIN, "respond_calendar_event", calendar_services.respond_calendar_event
        )
    hass.services.register(
        DOMAIN, "scan_for_calendars", calendar_services.scan_for_calendars
    )


class O365CalendarEventDevice(CalendarEventDevice):
    """O365 Calendar Event Processing."""

    def __init__(self, account, calendar_id, entity, entity_id):
        """Initialise the O365 Calendar Event."""
        self._start_offset = entity.get(CONF_HOURS_BACKWARD_TO_GET)
        self._end_offset = entity.get(CONF_HOURS_FORWARD_TO_GET)
        self._event = {}
        self._name = f"{entity.get(CONF_NAME)}"
        self.entity_id = entity_id
        self._offset_reached = False
        self._data_attribute = []

        self.data = self._init_data(account, calendar_id, entity)

    def _init_data(self, account, calendar_id, entity):
        max_results = entity.get(CONF_MAX_RESULTS)
        search = entity.get(CONF_SEARCH)
        # _LOGGER.debug("Initialising calendar: %s", calendar_id)
        return O365CalendarData(
            account,
            calendar_id,
            search,
            max_results,
        )

    @property
    def extra_state_attributes(self):
        """Device state property."""
        if self._event:
            return {
                "all_day": self._event.get("all_day", False)
                if self.data.event is not None
                else False,
                "offset_reached": self._offset_reached,
                "data": self._data_attribute,
            }

        return {
            "data": self._data_attribute,
        }

    @property
    def event(self):
        """Event property."""
        return self._event

    @property
    def name(self):
        """Name property."""
        return self._name

    async def async_get_events(self, hass, start_date, end_date):
        """Get events."""
        return await self.data.async_get_events(hass, start_date, end_date)

    async def async_update(self):
        """Do the update."""
        await self.data.async_update(self.hass)
        event = deepcopy(self.data.event)
        if event:
            try:
                event = calculate_offset(event, DEFAULT_OFFSET)
                self._offset_reached = is_offset_reached(event)
            except NameError:
                event["summary"], offset = extract_offset(
                    event.get("summary", ""), DEFAULT_OFFSET
                )
                start = O365CalendarData.get_date_utc(event["start"])
                self._offset_reached = is_offset_reached(start, offset)
        events = list(
            await self.data.async_o365_get_events(
                self.hass,
                dt.utcnow() + timedelta(hours=self._start_offset),
                dt.utcnow() + timedelta(hours=self._end_offset),
            )
        )
        self._data_attribute = [
            format_event_data(x, self.data.calendar.calendar_id) for x in events
        ]
        self._data_attribute.sort(key=itemgetter("start"))
        self._event = event


class O365CalendarData:
    """O365 Calendar Data."""

    def __init__(
        self,
        account,
        calendar_id,
        search=None,
        limit=999,
    ):
        """Initialise the O365 Calendar Data."""
        self._limit = limit
        schedule = account.schedule()
        self._calendar_id = calendar_id
        self.calendar = schedule.get_calendar(calendar_id=calendar_id)
        self._search = search
        self.event = None

    async def async_o365_get_events(self, hass, start_date, end_date):
        """Get the events."""
        query = self.calendar.new_query("start").greater_equal(start_date)
        query.chain("and").on_attribute("end").less_equal(end_date)
        if self._search is not None:
            query.chain("and").on_attribute("subject").contains(self._search)
        # _LOGGER.debug("get events: %s", self._calendar_id)
        return await hass.async_add_executor_job(
            ft.partial(
                self.calendar.get_events,
                limit=self._limit,
                query=query,
                include_recurring=True,
            )
        )

    async def async_get_events(self, hass, start_date, end_date):
        """Get the via async."""
        vevent_list = list(await self.async_o365_get_events(hass, start_date, end_date))
        vevent_list.sort(key=attrgetter("start"))
        event_list = []
        for event in vevent_list:
            data = format_event_data(event, self.calendar.calendar_id)
            data["start"] = self.get_hass_date(data["start"], event.is_all_day)
            data["end"] = self.get_hass_date(data["end"], event.is_all_day)
            event_list.append(data)

        return event_list

    @Throttle(MIN_TIME_BETWEEN_UPDATES)
    async def async_update(self, hass):
        """Do the update."""
        start_of_day_utc = dt.as_utc(dt.start_of_local_day())
        results = await self.async_o365_get_events(
            hass,
            start_of_day_utc,
            start_of_day_utc + timedelta(days=1),
        )
        results = list(results)
        results.sort(key=lambda x: self.to_datetime(x.start))

        vevent = self._get_root_event(results)

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
            "start": self.get_hass_date(vevent.start, vevent.is_all_day),
            "end": self.get_hass_date(self.get_end_date(vevent), vevent.is_all_day),
            "location": vevent.location,
            "description": clean_html(vevent.body),
            "all_day": vevent.is_all_day,
        }

    def _get_root_event(self, results):
        started_event = None
        not_started_event = None
        all_day_event = None
        for event in results:
            if event.is_all_day:
                if not all_day_event and not self.is_finished(event):
                    all_day_event = event
                continue
            if self.is_started(event) and not self.is_finished(event):
                if not started_event:
                    started_event = event
                continue
            if (
                not self.is_finished(event)
                and not event.is_all_day
                and not not_started_event
            ):
                not_started_event = event
        vevent = None
        if started_event:
            vevent = started_event
        elif all_day_event:
            vevent = all_day_event
        elif not_started_event:
            vevent = not_started_event

        return vevent

    @staticmethod
    def is_all_day(vevent):
        """Is it all day."""
        return vevent.is_all_day

    @staticmethod
    def is_started(vevent):
        """Is it over."""
        return dt.utcnow() >= O365CalendarData.to_datetime(
            O365CalendarData.get_start_date(vevent)
        )

    @staticmethod
    def is_finished(vevent):
        """Is it over."""
        return dt.utcnow() >= O365CalendarData.to_datetime(
            O365CalendarData.get_end_date(vevent)
        )

    @staticmethod
    def get_hass_date(obj, is_all_day):
        """Get the date."""
        if isinstance(obj, datetime) and not is_all_day:
            return {"dateTime": obj.isoformat()}

        return {"date": obj.date().isoformat()}

    @staticmethod
    def to_datetime(obj):
        """To datetime."""
        if isinstance(obj, datetime):
            date_obj = (
                obj.replace(tzinfo=dt.DEFAULT_TIME_ZONE) if obj.tzinfo is None else obj
            )
        else:
            date_obj = dt.as_local(dt.dt.datetime.combine(obj, dt.dt.time.min))
        return dt.as_utc(date_obj)

    @staticmethod
    def get_date_utc(date):
        """Get the dateTime from date or dateTime as a local."""
        if "date" in date:
            date_obj = dt.start_of_local_day(
                dt.dt.datetime.combine(dt.parse_date(date["date"]), dt.dt.time.min)
            )
        else:
            date_obj = dt.as_local(dt.parse_datetime(date["dateTime"]))
        return dt.as_utc(date_obj)

    @staticmethod
    def get_end_date(obj):
        """Get the end date."""
        if hasattr(obj, "end"):
            return obj.end

        if hasattr(obj, "duration"):
            return obj.start + obj.duration.value

        return obj.start + timedelta(days=1)

    @staticmethod
    def get_start_date(obj):
        """Get the start date."""
        return obj.start


class CalendarServices:
    """Calendar Services."""

    def __init__(self, hass):
        """Initialise the calendar services."""
        self._hass = hass

    def modify_calendar_event(self, call):
        """Modify the event."""
        config = self._get_config(call.data)

        if not self._validate_permissions("modify", config):
            return

        event_data = self._setup_event_data(call.data, config)
        CALENDAR_SERVICE_MODIFY_SCHEMA(event_data)
        event = self._get_event_from_calendar(config, event_data)
        event = add_call_data_to_event(event, call.data)
        event.save()

    def create_calendar_event(self, call):
        """Create the event."""
        config = self._get_config(call.data)

        if not self._validate_permissions("create", config):
            return

        event_data = self._setup_event_data(call.data, config)
        if not event_data:
            return
        CALENDAR_SERVICE_CREATE_SCHEMA(event_data)
        schedule = config[CONF_ACCOUNT].schedule()
        calendar = schedule.get_calendar(
            calendar_id=event_data.get(ATTR_CALENDAR_ID, None)
        )
        event = calendar.new_event()
        event = add_call_data_to_event(event, call.data)
        event.save()

    def remove_calendar_event(self, call):
        """Remove the event."""
        config = self._get_config(call.data)

        if not self._validate_permissions("delete", config):
            return

        event_data = self._setup_event_data(call.data, config)
        CALENDAR_SERVICE_REMOVE_SCHEMA(event_data)
        event = self._get_event_from_calendar(config, event_data)
        event.delete()

    def respond_calendar_event(self, call):
        """Respond to calendar event."""
        config = self._get_config(call.data)
        if not self._validate_permissions("respond to", config):
            return

        event_data = self._setup_event_data(call.data, config)
        CALENDAR_SERVICE_RESPOND_SCHEMA(event_data)
        event = self._get_event_from_calendar(config, event_data)
        response = event_data.get("response")
        _validate_response(response)
        _send_response(event, event_data, response)

    def scan_for_calendars(self, call):  # pylint: disable=unused-argument
        """Scan for new calendars."""
        for config in self._hass.data[DOMAIN]:
            config = self._hass.data[DOMAIN][config]
            if CONF_ACCOUNT in config:
                schedule = config[CONF_ACCOUNT].schedule()
                calendars = schedule.list_calendars()
                track = config.get(CONF_TRACK_NEW, True)
                for calendar in calendars:
                    update_calendar_file(
                        build_yaml_filename(config),
                        calendar,
                        self._hass,
                        track,
                    )

    def _get_event_from_calendar(self, config, event_data):
        schedule = config[CONF_ACCOUNT].schedule()
        calendar = schedule.get_calendar(
            calendar_id=event_data.get(ATTR_CALENDAR_ID, None)
        )

        return calendar.get_event(event_data["event_id"])

    def _validate_permissions(self, error_message, config):
        permissions = get_permissions(
            self._hass,
            filename=build_token_filename(config, config.get(CONF_CONFIG_TYPE)),
        )
        if not validate_minimum_permission(PERM_MINIMUM_CALENDAR_WRITE, permissions):
            _LOGGER.error(
                "Not authorisied to %s calendar event - requires permission: %s",
                error_message,
                PERM_CALENDARS_READWRITE,
            )
            return False
        return True

    def _setup_event_data(self, call_data, config):
        event_data = dict(call_data.items())
        if entity_id := call_data.get(ATTR_ENTITY_ID, None):
            calendar_id = config.get(CONF_CAL_IDS).get(entity_id)
            event_data[ATTR_CALENDAR_ID] = calendar_id
        elif config[CONF_CONFIG_TYPE] == CONST_CONFIG_TYPE_LIST:
            event_data[ATTR_CALENDAR_ID] = None
            _LOGGER.error("Must use entity_id for service calls to calendars.")
            raise ValueError("Must use entity_id for service calls to calendars.")
        else:
            _LOGGER.warning(
                "Use of calendar_id for service calls has been deprecated and will be "
                "removed in a future release. Please use entity_id instead."
            )

        return event_data

    def _get_config(self, event_data):
        for config in self._hass.data[DOMAIN]:
            config_data = self._hass.data[DOMAIN][config]
            if entity_id := event_data.get(ATTR_ENTITY_ID, None):
                if entity_id in config_data[CONF_CAL_IDS]:
                    return config_data
            else:
                for cal in config_data[CONF_CAL_IDS]:
                    if config_data[CONF_CAL_IDS][cal] == event_data.get(
                        ATTR_CALENDAR_ID, None
                    ):
                        return config_data
        _LOGGER.error(
            "Invalid Entity_ID (%s) or Calendar_ID (%s)",
            event_data.get(ATTR_ENTITY_ID, None),
            event_data.get(ATTR_CALENDAR_ID, None),
        )
        return None


def _validate_response(response):
    responses = ["accept", "tentative", "decline"]
    if response is None:
        raise ValueError("response not set")
    if response.lower() not in responses:
        raise ValueError(f"response must be one of {', '.join(responses)}")


def _send_response(event, event_data, response):
    send_response = event_data.get("send_response", True)
    if response.lower() == "accept":
        event.accept_event(event_data.get("message"), send_response=send_response)

    elif response.lower() == "tentative":
        event.accept_event(
            event_data.get("message"), tentatively=True, send_response=send_response
        )

    elif response.lower() == "decline":
        event.decline_event(event_data.get("message"), send_response=send_response)
