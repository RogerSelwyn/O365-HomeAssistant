from datetime import timedelta, datetime
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

CONF_ALIASES = "aliases"
CONF_CACHE_PATH = "cache_path"
CONF_CLIENT_ID = "client_id"
CONF_CLIENT_SECRET = "client_secret"

CONFIGURATOR_DESCRIPTION = (
    "To link your O365 account, click the link, login, and authorize:"
)
CONFIGURATOR_LINK_NAME = "Link O365 account"
CONFIGURATOR_SUBMIT_CAPTION = "I authorized successfully"

DEFAULT_CACHE_PATH = ".O365-token-cache"
DEFAULT_NAME = "Office 365 Calendar"
DOMAIN = "office365calendar"

ICON = "mdi:office"

SCOPE = ["offline_access", "User.Read", "Calendars.Read", "Calendars.Read.Shared"]

TOKEN_BACKEND = FileSystemTokenBackend(
    token_path=DEFAULT_CACHE_PATH, token_filename="o365.token"
)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
        vol.Required(CONF_CLIENT_ID): cv.string,
        vol.Required(CONF_CLIENT_SECRET): cv.string,
    }
)


def setup_platform(hass, config, add_devices, discovery_info=None):
    """Set up the Spotify platform."""

    callback_url = f"{hass.config.api.base_url}{AUTH_CALLBACK_PATH}"
    credentials = (config.get(CONF_CLIENT_ID), config.get(CONF_CLIENT_SECRET))
    account = Account(credentials, token_backend=TOKEN_BACKEND)
    is_authenticated = account.is_authenticated
    if not is_authenticated:
        url, state = account.con.get_authorization_url(
            requested_scopes=SCOPE, redirect_uri=callback_url
        )
        _LOGGER.info("no token; requesting authorization")
        hass.http.register_view(
            O365AuthCallbackView(config, add_devices, account, state, callback_url)
        )
        request_configuration(hass, config, url, callback_url)
        return
    if hass.data.get(DOMAIN):
        configurator = hass.components.configurator
        configurator.request_done(hass.data.get(DOMAIN))
        del hass.data[DOMAIN]
    cal = O365Calendar(account, hass)
    add_devices([cal], True)
    hass.services.register(DOMAIN, "get_calendar_events", cal.get_calendar_events)


class O365Calendar(Entity):
    def __init__(self, account, hass):
        self.account = account
        self.hass = hass
        self._state = None
        # self.get_calendar_events(None)

    @property
    def name(self):
        return "O365 Calendar"

    @property
    def state(self):
        return self._state

    @property
    def device_state_attributes(self):
        attributes = {}
        start_date = datetime.now().replace(hour=0, minute=0, second=0)
        end_date = datetime.now().replace(hour=23, minute=59, second=59)
        schedule = self.account.schedule()
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
        attributes["data"] = json.dumps(data, indent=2)
        attributes["event_active"] = len([x for x in data if x["event_active"]]) > 0
        return attributes

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

        self.hass.states.set(
            f"{DOMAIN}.calendar_events",
            f"{call_start_time}-{call_end_time}",
            {"data": json.dumps(data, indent=2)},
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

    def __init__(self, config, add_devices, account, state, callback_url):
        """Initialize."""
        self.config = config
        self.add_devices = add_devices
        self.account = account
        self.state = state
        self.callback = callback_url

    @callback
    def get(self, request):
        """Receive authorization token."""
        hass = request.app["hass"]
        url = str(request.url)
        if url[:5].lower() == "http:":
            url = f"https:{url[5:]}"
        result = self.account.con.request_token(
            url, state=self.state, redirect_uri=self.callback
        )
        hass.async_add_job(setup_platform, hass, self.config, self.add_devices)


def clean_html(html):
    soup = BeautifulSoup(html, features="html.parser")
    return soup.find("body").get_text(" ", strip=True)


def request_configuration(hass, config, url, callback_url):

    configurator = hass.components.configurator
    hass.data[DOMAIN] = configurator.request_config(
        DEFAULT_NAME,
        lambda _: None,
        link_name=CONFIGURATOR_LINK_NAME,
        link_url=url,
        description=CONFIGURATOR_DESCRIPTION,
        submit_caption=CONFIGURATOR_SUBMIT_CAPTION,
    )
