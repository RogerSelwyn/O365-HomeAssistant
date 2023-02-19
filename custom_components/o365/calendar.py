"""Main calendar processing."""
import functools as ft
import logging
import re
from copy import deepcopy
from datetime import date, datetime, timedelta
from operator import attrgetter, itemgetter

import voluptuous as vol
from homeassistant.components.calendar import (
    CalendarEntity,
    CalendarEvent,
    extract_offset,
    is_offset_reached,
)
from homeassistant.const import CONF_NAME
from homeassistant.helpers import entity_platform, entity_registry
from homeassistant.helpers.entity import generate_entity_id
from homeassistant.util import dt
from requests.exceptions import HTTPError, RetryError

from .const import (
    ATTR_EVENT_ID,
    CALENDAR_ENTITY_ID_FORMAT,
    CONF_ACCOUNT,
    CONF_ACCOUNT_NAME,
    CONF_CAL_ID,
    CONF_CAL_IDS,
    CONF_CONFIG_TYPE,
    CONF_DEVICE_ID,
    CONF_ENABLE_UPDATE,
    CONF_ENTITIES,
    CONF_EXCLUDE,
    CONF_HOURS_BACKWARD_TO_GET,
    CONF_HOURS_FORWARD_TO_GET,
    CONF_MAX_RESULTS,
    CONF_SEARCH,
    CONF_TRACK,
    CONF_TRACK_NEW_CALENDAR,
    CONST_CONFIG_TYPE_LIST,
    CONST_GROUP,
    DEFAULT_OFFSET,
    DOMAIN,
    EVENT_CREATE_CALENDAR_EVENT,
    EVENT_HA_EVENT,
    EVENT_MODIFY_CALENDAR_EVENT,
    EVENT_REMOVE_CALENDAR_EVENT,
    EVENT_RESPOND_CALENDAR_EVENT,
    LEGACY_ACCOUNT_NAME,
    PERM_CALENDARS_READWRITE,
    PERM_MINIMUM_CALENDAR_WRITE,
    YAML_CALENDARS,
    EventResponse,
)
from .schema import (
    CALENDAR_DEVICE_SCHEMA,
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
    check_file_location,
    clean_html,
    format_event_data,
    get_permissions,
    load_yaml_file,
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
    yaml_filename = build_yaml_filename(conf, YAML_CALENDARS)
    yaml_filepath = build_config_file_path(hass, yaml_filename)
    check_file_location(hass, yaml_filename, yaml_filepath)
    calendars = load_yaml_file(yaml_filepath, CONF_CAL_ID, CALENDAR_DEVICE_SCHEMA)
    cal_ids = {}

    for cal_id, calendar in calendars.items():
        for entity in calendar.get(CONF_ENTITIES):
            if not entity[CONF_TRACK]:
                continue
            entity_id = _build_entity_id(hass, entity, conf)

            device_id = entity["device_id"]
            try:
                cal = O365CalendarEntity(
                    account, cal_id, entity, entity_id, device_id, conf
                )
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
    account_name = conf[CONF_ACCOUNT_NAME]
    entity_suffix = (
        f"_{account_name}"
        if (
            conf[CONF_CONFIG_TYPE] == CONST_CONFIG_TYPE_LIST
            and account_name != LEGACY_ACCOUNT_NAME
        )
        else ""
    )

    return generate_entity_id(
        CALENDAR_ENTITY_ID_FORMAT,
        f"{entity.get(CONF_DEVICE_ID)}{entity_suffix}",
        hass=hass,
    )


async def _async_setup_register_services(hass, conf):
    platform = entity_platform.async_get_current_platform()
    calendar_services = CalendarServices(hass)
    await calendar_services.async_scan_for_calendars(None)

    permissions = get_permissions(
        hass,
        filename=build_token_filename(conf, conf.get(CONF_CONFIG_TYPE)),
    )
    if conf[CONF_ENABLE_UPDATE] and validate_minimum_permission(
        PERM_MINIMUM_CALENDAR_WRITE, permissions
    ):
        platform.async_register_entity_service(
            "create_calendar_event",
            CALENDAR_SERVICE_CREATE_SCHEMA,
            "create_calendar_event",
        )
        platform.async_register_entity_service(
            "modify_calendar_event",
            CALENDAR_SERVICE_MODIFY_SCHEMA,
            "modify_calendar_event",
        )
        platform.async_register_entity_service(
            "remove_calendar_event",
            CALENDAR_SERVICE_REMOVE_SCHEMA,
            "remove_calendar_event",
        )
        platform.async_register_entity_service(
            "respond_calendar_event",
            CALENDAR_SERVICE_RESPOND_SCHEMA,
            "respond_calendar_event",
        )

    hass.services.async_register(
        DOMAIN, "scan_for_calendars", calendar_services.async_scan_for_calendars
    )


class O365CalendarEntity(CalendarEntity):
    """O365 Calendar Event Processing."""

    def __init__(self, account, calendar_id, entity, entity_id, device_id, config):
        """Initialise the O365 Calendar Event."""
        self._config = config
        self._account = account
        self._start_offset = entity.get(CONF_HOURS_BACKWARD_TO_GET)
        self._end_offset = entity.get(CONF_HOURS_FORWARD_TO_GET)
        self._event = {}
        self._name = f"{entity.get(CONF_NAME)}"
        self.entity_id = entity_id
        self._offset_reached = False
        self._data_attribute = []
        self.data = self._init_data(account, calendar_id, entity)
        self._calendar_id = calendar_id
        self._device_id = device_id
        self._uid_checked = False

    def _init_data(self, account, calendar_id, entity):
        max_results = entity.get(CONF_MAX_RESULTS)
        search = entity.get(CONF_SEARCH)
        exclude = entity.get(CONF_EXCLUDE)
        # _LOGGER.debug("Initialising calendar: %s", calendar_id)
        return O365CalendarData(
            account,
            self.entity_id,
            calendar_id,
            search,
            exclude,
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

    @property
    def unique_id(self):
        """Entity unique id."""
        unique_id = (
            f"{self._calendar_id}_{self._config[CONF_ACCOUNT_NAME]}_{self._device_id}"
        )
        if not self._uid_checked:
            self._check_unique_id(unique_id)
        return unique_id

    # Can be removed by start of 2024 at latest, temporary fudge to correct wrong UIDs
    def _check_unique_id(self, unique_id):
        ent_reg = entity_registry.async_get(self.hass)
        entry = ent_reg.async_get(self.entity_id)
        if entry and entry.unique_id != unique_id:
            ent_reg.async_update_entity(self.entity_id, new_unique_id=unique_id)
            self._uid_checked = True

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
        self._data_attribute = [format_event_data(x) for x in events]
        self._data_attribute.sort(key=itemgetter("start"))
        self._event = event

    def create_calendar_event(
        self,
        subject,
        start,
        end,
        body=None,
        location=None,
        categories=None,
        sensitivity=None,
        show_as=None,
        is_all_day=False,
        attendees=None,
    ):
        """Create the event."""
        if categories is None:
            categories = []
        if attendees is None:
            attendees = []
        if not self._validate_permissions("create"):
            return

        calendar = self.data.calendar

        event = calendar.new_event()
        event = add_call_data_to_event(
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
        )
        event.save()
        self._raise_event(EVENT_CREATE_CALENDAR_EVENT, event.object_id)

    def modify_calendar_event(
        self,
        event_id,
        subject=None,
        start=None,
        end=None,
        body=None,
        location=None,
        categories=None,
        sensitivity=None,
        show_as=None,
        is_all_day=False,
        attendees=None,
    ):
        """Modify the event."""
        if categories is None:
            categories = []
        if attendees is None:
            attendees = []

        if not self._validate_permissions("modify"):
            return

        if self.data.group_calendar:
            _group_calendar_log(self.entity_id)
            return

        event = self._get_event_from_calendar(event_id)
        event = add_call_data_to_event(
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
        )
        event.save()
        self._raise_event(EVENT_MODIFY_CALENDAR_EVENT, event_id)

    def remove_calendar_event(self, event_id):
        """Remove the event."""
        if not self._validate_permissions("delete"):
            return

        if self.data.group_calendar:
            _group_calendar_log(self.entity_id)
            return

        event = self._get_event_from_calendar(event_id)
        event.delete()
        self._raise_event(EVENT_REMOVE_CALENDAR_EVENT, event_id)

    def respond_calendar_event(
        self, event_id, response, send_response=True, message=None
    ):
        """Respond to calendar event."""
        if not self._validate_permissions("respond to"):
            return

        if self.data.group_calendar:
            _group_calendar_log(self.entity_id)
            return

        self._send_response(event_id, response, send_response, message)
        self._raise_event(EVENT_RESPOND_CALENDAR_EVENT, event_id)

    def _send_response(self, event_id, response, send_response, message):
        event = self._get_event_from_calendar(event_id)
        if response == EventResponse.Accept:
            event.accept_event(message, send_response=send_response)

        elif response == EventResponse.Tentative:
            event.accept_event(message, tentatively=True, send_response=send_response)

        elif response == EventResponse.Decline:
            event.decline_event(message, send_response=send_response)

    def _get_event_from_calendar(self, event_id):
        calendar = self.data.calendar
        return calendar.get_event(event_id)

    def _validate_permissions(self, error_message):
        permissions = get_permissions(
            self.hass,
            filename=build_token_filename(
                self._config, self._config.get(CONF_CONFIG_TYPE)
            ),
        )
        if not validate_minimum_permission(PERM_MINIMUM_CALENDAR_WRITE, permissions):
            raise vol.Invalid(
                f"Not authorisied to {PERM_CALENDARS_READWRITE} calendar event "
                + f"- requires permission: {error_message}"
            )

        return True

    def _raise_event(self, event_type, event_id):
        self.hass.bus.fire(
            f"{DOMAIN}_{event_type}",
            {ATTR_EVENT_ID: event_id, EVENT_HA_EVENT: True},
        )


class O365CalendarData:
    """O365 Calendar Data."""

    def __init__(
        self,
        account,
        entity_id,
        calendar_id,
        search=None,
        exclude=None,
        limit=999,
    ):
        """Initialise the O365 Calendar Data."""
        self._limit = limit
        self.group_calendar = calendar_id.startswith(CONST_GROUP)
        self.calendar_id = calendar_id
        if self.group_calendar:
            self._schedule = None
            self.calendar = account.schedule(resource=self.calendar_id)
        else:
            self._schedule = account.schedule()
            self.calendar = None
        self._search = search
        self._exclude = exclude
        self.event = None
        self._entity_id = entity_id

    async def _async_get_calendar(self, hass):
        self.calendar = await hass.async_add_executor_job(
            ft.partial(self._schedule.get_calendar, calendar_id=self.calendar_id)
        )

    async def async_o365_get_events(self, hass, start_date, end_date):
        """Get the events."""
        if not self.calendar:
            await self._async_get_calendar(hass)

        events = await self._async_calendar_schedule_get_events(
            hass, self.calendar, start_date, end_date
        )

        return self._filter_events(events) or events

    def _filter_events(self, events):
        if not events:
            return None
        if not self._exclude:
            return None
        lst_events = list(events)
        rtn_events = []
        for event in lst_events:
            include = True
            for exclude in self._exclude:
                if re.search(exclude, event.subject):
                    include = False
            if include:
                rtn_events.append(event)

        return rtn_events

    async def _async_calendar_schedule_get_events(
        self, hass, calendar_schedule, start_date, end_date
    ):
        """Get the events for the calendar."""
        query = calendar_schedule.new_query("start").greater_equal(start_date)
        query.chain("and").on_attribute("end").less_equal(end_date)
        if self._search is not None:
            query.chain("and").on_attribute("subject").contains(self._search)
        # As at March 2023 not contains is not supported by Graph API
        # if self._exclude is not None:
        #     query.chain("and").on_attribute("subject").negate().contains(self._exclude)
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

    async def async_scan_for_calendars(self, call):  # pylint: disable=unused-argument
        """Scan for new calendars."""
        for config in self._hass.data[DOMAIN]:
            config = self._hass.data[DOMAIN][config]
            if CONF_ACCOUNT in config:
                schedule = config[CONF_ACCOUNT].schedule()
                calendars = await self._hass.async_add_executor_job(
                    schedule.list_calendars
                )
                track = config.get(CONF_TRACK_NEW_CALENDAR, True)
                for calendar in calendars:
                    update_calendar_file(
                        build_yaml_filename(config, YAML_CALENDARS),
                        calendar,
                        self._hass,
                        track,
                    )


def _group_calendar_log(entity_id):
    raise vol.Invalid(
        "O365 Python does not have capability "
        + f"to update/respond to group calendar events: {entity_id}"
    )
