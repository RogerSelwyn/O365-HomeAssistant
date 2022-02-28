"""Main initialisation code."""
import logging
import warnings
from functools import partial

from aiohttp import web_response
from homeassistant.components.http import HomeAssistantView
from homeassistant.core import callback
from homeassistant.helpers import discovery
from homeassistant.helpers.network import get_url
from O365 import Account, FileSystemTokenBackend

from .const import (
    AUTH_CALLBACK_NAME,
    AUTH_CALLBACK_PATH,
    AUTH_CALLBACK_PATH_ALT,
    CONF_ALT_CONFIG,
    CONF_CALENDARS,
    CONF_CLIENT_ID,
    CONF_CLIENT_SECRET,
    CONF_EMAIL_SENSORS,
    CONF_QUERY_SENSORS,
    CONF_STATUS_SENSORS,
    CONF_TRACK_NEW,
    CONFIG_SCHEMA,
    CONFIGURATOR_DESCRIPTION,
    CONFIGURATOR_LINK_NAME,
    CONFIGURATOR_SUBMIT_CAPTION,
    DEFAULT_CACHE_PATH,
    DEFAULT_NAME,
    DOMAIN,
    TOKEN_FILENAME,
)
from .utils import (
    build_config_file_path,
    build_minimum_permissions,
    build_requested_permissions,
    validate_permissions,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup(hass, config):
    """Set up the O365 platform."""
    # validate_permissions(hass)
    conf = config.get(DOMAIN, {})
    CONFIG_SCHEMA(conf)
    credentials = (conf.get(CONF_CLIENT_ID), conf.get(CONF_CLIENT_SECRET))
    alt_config = conf.get(CONF_ALT_CONFIG)
    if alt_config:
        callback_url = AUTH_CALLBACK_PATH_ALT
    else:
        callback_url = f"{get_url(hass, prefer_external=True)}{AUTH_CALLBACK_PATH}"
    token_path = build_config_file_path(hass, DEFAULT_CACHE_PATH)
    token_backend = FileSystemTokenBackend(
        token_path=token_path, token_filename=TOKEN_FILENAME
    )

    account = Account(credentials, token_backend=token_backend, timezone="UTC")
    is_authenticated = account.is_authenticated
    minimum_permissions = build_minimum_permissions(conf)
    permissions = validate_permissions(hass, minimum_permissions)
    if is_authenticated and permissions:
        do_setup(hass, conf, account)
    else:
        scope = build_requested_permissions(conf)
        url, state = account.con.get_authorization_url(
            requested_scopes=scope, redirect_uri=callback_url
        )
        _LOGGER.info("no token; requesting authorization")
        callback_view = O365AuthCallbackView(
            conf, None, account, state, callback_url, hass
        )
        hass.http.register_view(callback_view)
        if alt_config:
            request_configuration_alt(hass, url, callback_view)
        else:
            request_configuration(hass, url, callback_view)

    return True


def do_setup(hass, config, account):
    """Run the setup after we have everything configured."""
    if config.get(CONF_CALENDARS, None):
        _LOGGER.warning(
            "Configuring calendars through configuration.yaml has been deprecated, "
            "and will be removed in a future release. Please see the docs for how "
            "to proceed:"
            "\nhttps://github.com/PTST/O365-HomeAssistant/tree/master#calendar-configuration"
        )
        warnings.warn(
            "Configuring calendars through configuration.yaml has been deprecated, "
            "and will be removed in a future release. Please see the docs for how to proceed",
            FutureWarning,
        )
    email_sensors = config.get(CONF_EMAIL_SENSORS, [])
    query_sensors = config.get(CONF_QUERY_SENSORS, [])
    status_sensors = config.get(CONF_STATUS_SENSORS, [])

    hass.data[DOMAIN] = {
        "account": account,
        CONF_EMAIL_SENSORS: email_sensors,
        CONF_QUERY_SENSORS: query_sensors,
        CONF_STATUS_SENSORS: status_sensors,
        CONF_TRACK_NEW: config.get(CONF_TRACK_NEW, True),
    }
    hass.async_create_task(
        discovery.async_load_platform(hass, "calendar", DOMAIN, {}, config)
    )
    hass.async_create_task(
        discovery.async_load_platform(hass, "notify", DOMAIN, {}, config)
    )
    if len(email_sensors) > 0 or len(query_sensors) > 0 or len(status_sensors) > 0:
        hass.async_create_task(
            discovery.async_load_platform(hass, "sensor", DOMAIN, {}, config)
        )


def request_configuration(hass, url, callback_view):
    """Request the config."""
    configurator = callback_view.configurator
    hass.data[DOMAIN] = configurator.async_request_config(
        DEFAULT_NAME,
        lambda _: None,
        link_name=CONFIGURATOR_LINK_NAME,
        link_url=url,
        description=CONFIGURATOR_DESCRIPTION,
        submit_caption=CONFIGURATOR_SUBMIT_CAPTION,
    )


def request_configuration_alt(hass, url, callback_view):
    """Request the alternate config."""
    configurator = callback_view.configurator
    hass.data[DOMAIN] = configurator.async_request_config(
        f"{DEFAULT_NAME} - Alternative configuration",
        callback_view.alt_callback,
        link_name=CONFIGURATOR_LINK_NAME,
        link_url=url,
        fields=[{"id": "token", "name": "Returned Url", "type": "token"}],
        description="Complete the configuration and copy the complete url "
        "into this field afterwards and submit",
        submit_caption="Submit",
    )


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
    async def get(self, request):
        """Receive authorization token."""
        url = str(request.url)
        if url[:5].lower() == "http:":
            url = f"https:{url[5:]}"
        if "code" not in url:
            return web_response.Response(
                headers={"content-type": "text/html"},
                text="<script>window.close()</script>Error, the "
                "originating url does not seem to be a valid microsoft redirect",
            )
        await self._hass.async_add_executor_job(
            partial(
                self.account.con.request_token,
                url,
                state=self.state,
                redirect_uri=self.callback,
            )
        )
        domain_data = self._hass.data[DOMAIN]
        do_setup(self._hass, self.config, self.account)
        self.configurator.async_request_done(domain_data)

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
        domain_data = self._hass.data[DOMAIN]
        do_setup(self._hass, self.config, self.account)
        self.configurator.async_request_done(domain_data)
        return
