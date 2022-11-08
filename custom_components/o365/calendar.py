"""Main calendar processing."""
import functools as ft
import logging
from copy import deepcopy
from datetime import date, datetime, timedelta
from operator import attrgetter, itemgetter

from homeassistant.components.calendar import (
    CalendarEntity,
    CalendarEvent,
    extract_offset,
    is_offset_reached,
)
from homeassistant.const import CONF_NAME
from homeassistant.helpers.entity import generate_entity_id
from homeassistant.util import dt
from requests.exceptions import HTTPError, RetryError

from .const import (
    ATTR_CALENDAR_ID,
    ATTR_ENTITY_ID,
    CALENDAR_ENTITY_ID_FORMAT,
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
    CONST_GROUP,
    DEFAULT_OFFSET,
    DOMAIN,
    PERM_CALENDARS_READWRITE,
    PERM_MINIMUM_CALENDAR_WRITE,
)
from .schema import (
    CALENDAR_SERVICE_CREATE_SCHEMA,
    CALENDAR_SERVICE_MODIFY_SCHEMA,
    CALENDAR_SERVICE_REMOVE_SCHEMA,
    CALENDAR_SERVICE_RESPOND_SCHEMA,
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


async def async_setup_platform(
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
    await _async_setup_register_services(hass, conf)

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
                cal = O365CalendarEntity(account, cal_id, entity, entity_id)
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


async def _async_setup_register_services(hass, conf):
    calendar_services = CalendarServices(hass)
    await calendar_services.async_scan_for_calendars(None)

    if conf[CONF_ENABLE_UPDATE]:
        hass.services.async_register(
            DOMAIN, "modify_calendar_event", calendar_services.modify_calendar_event
        )
        hass.services.async_register(
            DOMAIN, "create_calendar_event", calendar_services.create_calendar_event
        )
        hass.services.async_register(
            DOMAIN, "remove_calendar_event", calendar_services.remove_calendar_event
        )
        hass.services.async_register(
            DOMAIN, "respond_calendar_event", calendar_services.respond_calendar_event
        )
    hass.services.async_register(
        DOMAIN, "scan_for_calendars", calendar_services.async_scan_for_calendars
    )


class O365CalendarEntity(CalendarEntity):
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
            self.entity_id,
            calendar_id,
            search,
            max_results,
        )

    @property
    def extra_state_attributes(self):
        """Extra state attributes."""
        if self._event:
            return {
                "all_day": self._event.all_day
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
            event.summary, offset = extract_offset(event.summary, DEFAULT_OFFSET)
            start = O365CalendarData.to_datetime(event.start)
            self._offset_reached = is_offset_reached(start, offset)
        results = await self.data.async_o365_get_events(
            self.hass,
            dt.utcnow() + timedelta(hours=self._start_offset),
            dt.utcnow() + timedelta(hours=self._end_offset),
        )
        if results:
            events = list(results)
        elif self._event:
            return
        else:
            events = []
        self._data_attribute = [
            format_event_data(x, self.data.calendar_id) for x in events
        ]
        self._data_attribute.sort(key=itemgetter("start"))
        self._event = event


class O365CalendarData:
    """O365 Calendar Data."""

    def __init__(
        self,
        account,
        entity_id,
        calendar_id,
        search=None,
        limit=999,
    ):
        """Initialise the O365 Calendar Data."""
        self._limit = limit
        self._group_calendar = calendar_id.startswith(CONST_GROUP)
        if self._group_calendar:
            self._schedule = account.schedule(resource=calendar_id)
        else:
            self._schedule = account.schedule()
        self.calendar_id = calendar_id
        self.calendar = None
        self._search = search
        self.event = None
        self._entity_id = entity_id

    async def _async_get_calendar(self, hass):
        self.calendar = await hass.async_add_executor_job(
            ft.partial(self._schedule.get_calendar, calendar_id=self.calendar_id)
        )

    async def async_o365_get_events(self, hass, start_date, end_date):
        """Get the events."""
        if self._group_calendar:
            return await self._async_calendar_schedule_get_events(
                hass, self._schedule, start_date, end_date
            )

        if not self.calendar:
            await self._async_get_calendar(hass)

        return await self._async_calendar_schedule_get_events(
            hass, self.calendar, start_date, end_date
        )

    async def _async_calendar_schedule_get_events(
        self, hass, calendar_schedule, start_date, end_date
    ):
        """Get the events for the calendar."""
        query = calendar_schedule.new_query("start").greater_equal(start_date)
        query.chain("and").on_attribute("end").less_equal(end_date)
        if self._search is not None:
            query.chain("and").on_attribute("subject").contains(self._search)
        # _LOGGER.debug("get events: %s", self._calendar_id)
        try:
            return await hass.async_add_executor_job(
                ft.partial(
                    calendar_schedule.get_events,
                    limit=self._limit,
                    query=query,
                    include_recurring=True,
                )
            )
        except RetryError:
            _LOGGER.warning("Retry error getting calendar events")
            return None

    async def async_get_events(self, hass, start_date, end_date):
        """Get the via async."""
        results = await self.async_o365_get_events(hass, start_date, end_date)
        if not results:
            return
        vevent_list = list(results)
        vevent_list.sort(key=attrgetter("start"))
        event_list = []
        for vevent in vevent_list:
            event = CalendarEvent(
                self.get_hass_date(vevent.start, vevent.is_all_day),
                self.get_hass_date(self.get_end_date(vevent), vevent.is_all_day),
                vevent.subject,
                clean_html(vevent.body),
                vevent.location["displayName"],
            )
            event_list.append(event)

        return event_list

    async def async_update(self, hass):
        """Do the update."""
        start_of_day_utc = dt.as_utc(dt.start_of_local_day())
        results = await self.async_o365_get_events(
            hass,
            start_of_day_utc,
            start_of_day_utc + timedelta(days=1),
        )
        if not results:
            return

        results = list(results)
        results.sort(key=lambda x: self.to_datetime(x.start))

        vevent = self._get_root_event(results)

        if vevent is None:
            _LOGGER.debug(
                "No matching event found in the %d results for %s",
                len(results),
                self._entity_id,
            )
            self.event = None
            return

        self.event = CalendarEvent(
            self.get_hass_date(vevent.start, vevent.is_all_day),
            self.get_hass_date(self.get_end_date(vevent), vevent.is_all_day),
            vevent.subject,
            clean_html(vevent.body),
            vevent.location["displayName"],
        )

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
        return obj if isinstance(obj, datetime) and not is_all_day else obj.date()

    @staticmethod
    def to_datetime(obj):
        """To datetime."""
        if isinstance(obj, datetime):
            date_obj = (
                obj.replace(tzinfo=dt.DEFAULT_TIME_ZONE) if obj.tzinfo is None else obj
            )
        elif isinstance(obj, date):
            date_obj = dt.start_of_local_day(
                dt.dt.datetime.combine(obj, dt.dt.time.min)
            )
        elif "date" in obj:
            date_obj = dt.start_of_local_day(
                dt.dt.datetime.combine(dt.parse_date(obj["date"]), dt.dt.time.min)
            )
        else:
            date_obj = dt.as_local(dt.parse_datetime(obj["dateTime"]))
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

    def create_calendar_event(self, call):
        """Create the event."""
        config = self._get_config(call.data)

        if not self._validate_permissions("create", config):
            return

        event_data, group_calendar = self._setup_event_data(call.data, config)
        if not event_data:
            return
        CALENDAR_SERVICE_CREATE_SCHEMA(event_data)

        calendar_id = event_data.get(ATTR_CALENDAR_ID, None)
        if group_calendar:
            calendar = config[CONF_ACCOUNT].schedule(resource=calendar_id)
        else:
            schedule = config[CONF_ACCOUNT].schedule()
            calendar = schedule.get_calendar(calendar_id=calendar_id)
        event = calendar.new_event()
        event = add_call_data_to_event(event, call.data)
        event.save()

    def modify_calendar_event(self, call):
        """Modify the event."""
        config = self._get_config(call.data)

        if not self._validate_permissions("modify", config):
            return

        event_data, group_calendar = self._setup_event_data(call.data, config)
        if group_calendar:
            _group_calendar_log(event_data.get(ATTR_ENTITY_ID, None))
            return

        CALENDAR_SERVICE_MODIFY_SCHEMA(event_data)
        event = self._get_event_from_calendar(
            config,
            event_data,
        )
        event = add_call_data_to_event(event, call.data)
        event.save()

    def remove_calendar_event(self, call):
        """Remove the event."""
        config = self._get_config(call.data)

        if not self._validate_permissions("delete", config):
            return

        event_data, group_calendar = self._setup_event_data(call.data, config)
        if group_calendar:
            _group_calendar_log(event_data.get(ATTR_ENTITY_ID, None))
            return

        CALENDAR_SERVICE_REMOVE_SCHEMA(event_data)
        event = self._get_event_from_calendar(config, event_data)
        event.delete()

    def respond_calendar_event(self, call):
        """Respond to calendar event."""
        config = self._get_config(call.data)
        if not self._validate_permissions("respond to", config):
            return

        event_data, group_calendar = self._setup_event_data(call.data, config)
        if group_calendar:
            _group_calendar_log(event_data.get(ATTR_ENTITY_ID, None))
            return

        CALENDAR_SERVICE_RESPOND_SCHEMA(event_data, group_calendar)
        event = self._get_event_from_calendar(config, event_data)
        response = event_data.get("response")
        _validate_response(response)
        _send_response(event, event_data, response)

    async def async_scan_for_calendars(self, call):  # pylint: disable=unused-argument
        """Scan for new calendars."""
        for config in self._hass.data[DOMAIN]:
            config = self._hass.data[DOMAIN][config]
            if CONF_ACCOUNT in config:
                schedule = config[CONF_ACCOUNT].schedule()
                calendars = await self._hass.async_add_executor_job(
                    schedule.list_calendars
                )
                track = config.get(CONF_TRACK_NEW, True)
                for calendar in calendars:
                    update_calendar_file(
                        build_yaml_filename(config),
                        calendar,
                        self._hass,
                        track,
                    )

    def _get_event_from_calendar(self, config, event_data):
        calendar_id = event_data.get(ATTR_CALENDAR_ID, None)
        schedule = config[CONF_ACCOUNT].schedule()
        calendar = schedule.get_calendar(calendar_id=calendar_id)
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
        group_calendar = False
        if entity_id := call_data.get(ATTR_ENTITY_ID, None):
            calendar_id = config.get(CONF_CAL_IDS).get(entity_id)
            group_calendar = calendar_id.startswith(CONST_GROUP)
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

        return event_data, group_calendar

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


def _group_calendar_log(entity_id):
    _LOGGER.error(
        "O365 Python does not have capability to update/respond to group calendar events: %s",
        entity_id,
    )
