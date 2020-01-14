from datetime import timedelta, datetime
from operator import itemgetter
import logging
import json
from O365 import Account, FileSystemTokenBackend
from bs4 import BeautifulSoup
import voluptuous as vol
import homeassistant.helpers.config_validation as cv
from homeassistant.components.http import HomeAssistantView
from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import CONF_HOST, CONF_NAME, CONF_PORT, CONF_SSL
from homeassistant.helpers.entity import Entity
from homeassistant.core import callback
from homeassistant.util.dt import utcnow


_LOGGER = logging.getLogger(__name__)

DEFAULT_NAME = "O365 Calendar"

AUTH_CALLBACK_NAME = "api:o365"
AUTH_CALLBACK_PATH = "/api/o365"

AUTH_CALLBACK_PATH_ALT = "https://login.microsoftonline.com/common/oauth2/nativeclient"

CONF_ALIASES = "aliases"
CONF_CACHE_PATH = "cache_path"
CONF_CLIENT_ID = "client_id"
CONF_CLIENT_SECRET = "client_secret"
CONF_CALENDAR_NAME = "calendar_name"
CONF_HOURS_FORWARD_TO_GET = "end_offset"
CONF_HOURS_BACKWARD_TO_GET = "start_offset"
CONF_ALT_CONFIG = "alt_auth_flow"

CONFIGURATOR_DESCRIPTION = (
    "To link your O365 account, click the link, login, and authorize:"
)
CONFIGURATOR_LINK_NAME = "Link O365 account"
CONFIGURATOR_SUBMIT_CAPTION = "I authorized successfully"

DEFAULT_CACHE_PATH = ".O365-token-cache"
DEFAULT_NAME = "O365 Calendar"
DOMAIN = "office365calendar"

ICON = "mdi:office"

SCOPE = ["offline_access", "User.Read", "Calendars.Read", "Calendars.Read.Shared"]

TOKEN_BACKEND = FileSystemTokenBackend(
    token_path=DEFAULT_CACHE_PATH, token_filename="o365.token"
)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
        vol.Optional(CONF_CALENDAR_NAME, default=""): cv.string,
        vol.Optional(CONF_ALT_CONFIG, default=False): bool,
        vol.Optional(CONF_HOURS_FORWARD_TO_GET, default=24): int,
        vol.Optional(CONF_HOURS_BACKWARD_TO_GET, default=0): int,
        vol.Required(CONF_CLIENT_ID): cv.string,
        vol.Required(CONF_CLIENT_SECRET): cv.string,
    }
)


def setup_platform(hass, config, add_devices, discovery_info=None):
    """Set up the O365 platform."""

    credentials = (config.get(CONF_CLIENT_ID), config.get(CONF_CLIENT_SECRET))
    name = config.get(CONF_NAME)
    calendar_name = config.get(CONF_CALENDAR_NAME)
    hours_forward = config.get(CONF_HOURS_FORWARD_TO_GET)
    hours_backward = config.get(CONF_HOURS_BACKWARD_TO_GET)
    alt_config = config.get(CONF_ALT_CONFIG)
    if not alt_config:
        callback_url = f"{hass.config.api.base_url}{AUTH_CALLBACK_PATH}"
    else:
        callback_url = AUTH_CALLBACK_PATH_ALT
    account = Account(credentials, token_backend=TOKEN_BACKEND)
    is_authenticated = account.is_authenticated
    if not is_authenticated:
        url, state = account.con.get_authorization_url(
            requested_scopes=SCOPE, redirect_uri=callback_url
        )
        _LOGGER.info("no token; requesting authorization")
        callback_view = O365AuthCallbackView(
            config, add_devices, account, state, callback_url, hass
        )
        hass.http.register_view(callback_view)
        if alt_config:
            request_configuration_alt(hass, config, url, callback_view)
        else:
            request_configuration(hass, config, url, callback_view)
        return
    if hass.data.get(DOMAIN):
        configurator = hass.components.configurator
        configurator.request_done(hass.data.get(DOMAIN))
        del hass.data[DOMAIN]
    cal = O365Calendar(
        account, hass, name, calendar_name, hours_forward, hours_backward
    )
    add_devices([cal], True)
    hass.services.register(DOMAIN, f"get_calendar_events", cal.get_calendar_events)
    hass.services.register(DOMAIN, f"list_calendars", cal.list_calendars)


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
        # self.get_calendar_events(None)

    @property
    def name(self):
        return self._name

    @property
    def state(self):
        return self._state

    @property
    def device_state_attributes(self):
        attributes = {}
        start_date = datetime.now() + timedelta(hours=self.hours_backward)
        end_date = datetime.now() + timedelta(hours=self.hours_forward)
        _LOGGER.debug(
            start_date.strftime("%Y-%m-%dT%H:%M:%S")
            + " - "
            + end_date.strftime("%Y-%m-%dT%H:%M:%S")
        )
        schedule = self.account.schedule()
        if self.calendar_name != "":
            calendar = schedule.get_calendar(calendar_name=self.calendar_name)
        else:
            calendar = schedule.get_default_calendar()
        query = calendar.new_query("start").greater_equal(start_date)
        query.chain("and").on_attribute("end").less_equal(end_date)
        data = []
        now = utcnow()

        for event in calendar.get_events(
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
                        x.address for x in event.attendees._Attendees__attendees
                    ],
                    "start": event.start.strftime("%Y-%m-%dT%H:%M:%S%z"),
                    "end": event.end.strftime("%Y-%m-%dT%H:%M:%S%z"),
                    "event_active": event.start <= now and event.end >= now,
                }
            )
        data.sort(key=itemgetter("start"))
        attributes["data_str_repr"] = json.dumps(data, indent=2)
        attributes["data"] = data
        attributes["event_active"] = len([x for x in data if x["event_active"]]) > 0
        return attributes

    def list_calendars(self, call):
        schedule = self.account.schedule()
        data = []
        for x in schedule.list_calendars():
            data.append(x.name)
        self.hass.states.set(
            f"{DOMAIN}.available_calendars", "", {"data": json.dumps(data, indent=2)},
        )

    def get_calendar_events(self, call):
        try:
            data = call.data
        except AttributeError:
            data = {}
        call_start_time = data.get(
            "start",
            datetime.now()
            .replace(hour=0, minute=0, second=0)
            .strftime("%Y-%m-%dT%H:%M:%S"),
        )
        start_date = datetime.strptime(call_start_time, "%Y-%m-%dT%H:%M:%S")

        call_end_time = data.get(
            "end",
            datetime.now()
            .replace(hour=23, minute=59, second=59)
            .strftime("%Y-%m-%dT%H:%M:%S"),
        )
        end_date = datetime.strptime(call_end_time, "%Y-%m-%dT%H:%M:%S")

        calendar_name = data.get("calendar_name", None)
        schedule = self.account.schedule()

        if calendar_name:
            calendar = schedule.get_calendar(calendar_name=calendar_name)
        else:
            calendar = schedule.get_default_calendar()

        query = calendar.new_query("start").greater_equal(start_date)
        query.chain("and").on_attribute("end").less_equal(end_date)

        data = []
        now = utcnow()

        for event in calendar.get_events(
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
                        x.address for x in event.attendees._Attendees__attendees
                    ],
                    "start": event.start.strftime("%Y-%m-%dT%H:%M:%S%z"),
                    "end": event.end.strftime("%Y-%m-%dT%H:%M:%S%z"),
                    "event_active": event.start <= now and event.end >= now,
                }
            )
        data.sort(key=itemgetter("start"))
        self.hass.states.set(
            f"{DOMAIN}.calendar_events",
            f"{call_start_time}-{call_end_time}",
            {"data_repr_str": json.dumps(data, indent=2), "data": data},
        )
        return

    def update(self):
        # self.account.connection.refresh_token()
        self._state = self.device_state_attributes["event_active"]


class O365AuthCallbackView(HomeAssistantView):
    """O365 Authorization Callback View."""

    requires_auth = False
    url = AUTH_CALLBACK_PATH
    name = AUTH_CALLBACK_NAME

    def __init__(self, config, add_devices, account, state, callback_url, hass):
        """Initialize."""
        self.config = config
        self.add_devices = add_devices
        self.account = account
        self.state = state
        self.callback = callback_url
        self._hass = hass
        self.configurator = self._hass.components.configurator

    @callback
    def get(self, request):
        from aiohttp import web_response

        """Receive authorization token."""
        hass = request.app["hass"]
        url = str(request.url)
        if url[:5].lower() == "http:":
            url = f"https:{url[5:]}"
        if "code" not in url:
            return web_response.Response(
                headers={"content-type": "text/html"},
                text="<script>window.close()</script>Error, the originating url does not seem to be a valid microsoft redirect",
            )
        result = self.account.con.request_token(
            url, state=self.state, redirect_uri=self.callback
        )
        hass.async_add_job(setup_platform, hass, self.config, self.add_devices)

        return web_response.Response(
            headers={"content-type": "text/html"},
            text="<script>window.close()</script>Success! This window can be closed",
        )

    def alt_callback(self, data):
        """Receive authorization token."""
        url = data.get("token")
        if not url:
            url = [v for k, v in data.items()][0]

        result = self.account.con.request_token(
            url, state=self.state, redirect_uri=AUTH_CALLBACK_PATH_ALT
        )
        if not result:
            self.configurator.notify_errors(
                self._hass.data[DOMAIN],
                "Error while authenticating, please see logs for more info.",
            )
            return
        self._hass.async_add_job(
            setup_platform, self._hass, self.config, self.add_devices
        )


def clean_html(html):
    soup = BeautifulSoup(html, features="html.parser")
    body = soup.find("body")
    if body:
        return soup.find("body").get_text(" ", strip=True)
    else:
        return html


def request_configuration(hass, config, url, callback_view):

    configurator = callback_view.configurator
    hass.data[DOMAIN] = configurator.async_request_config(
        DEFAULT_NAME,
        lambda _: None,
        link_name=CONFIGURATOR_LINK_NAME,
        link_url=url,
        description=CONFIGURATOR_DESCRIPTION,
        submit_caption=CONFIGURATOR_SUBMIT_CAPTION,
    )


def request_configuration_alt(hass, config, url, callback_view):
    configurator = callback_view.configurator
    hass.data[DOMAIN] = configurator.async_request_config(
        f"{DEFAULT_NAME} - Alternative configuration",
        callback_view.alt_callback,
        link_name=CONFIGURATOR_LINK_NAME,
        link_url=url,
        fields=[{"id": "token", "name": "Returned Url", "type": "token"}],
        description="Complete the configuration and copy the complete url into this field afterwards and submit",
        submit_caption="Submit",
    )
