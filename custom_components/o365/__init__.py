"""Main initialisation code."""
import logging
from copy import deepcopy
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
    CONF_ACCOUNT,
    CONF_ACCOUNT_NAME,
    CONF_ALT_CONFIG,
    CONF_CLIENT_ID,
    CONF_CLIENT_SECRET,
    CONF_EMAIL_SENSORS,
    CONF_ENABLE_UPDATE,
    CONF_QUERY_SENSORS,
    CONF_SECONDARY_ACCOUNTS,
    CONF_STATUS_SENSORS,
    CONF_TRACK_NEW,
    CONFIG_SCHEMA,
    CONFIGURATOR_DESCRIPTION,
    CONFIGURATOR_LINK_NAME,
    CONFIGURATOR_SUBMIT_CAPTION,
    CONST_PRIMARY,
    DEFAULT_CACHE_PATH,
    DEFAULT_NAME,
    DOMAIN,
)
from .utils import (
    build_config_file_path,
    build_minimum_permissions,
    build_requested_permissions,
    build_token_filename,
    validate_permissions,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup(hass, config):
    """Set up the O365 platform."""
    # validate_permissions(hass)
    conf = config.get(DOMAIN, {})
    CONFIG_SCHEMA(conf)

    primary_credentials = (
        conf.get(CONF_CLIENT_ID),
        conf.get(CONF_CLIENT_SECRET),
    )
    _setup_account(hass, conf, CONST_PRIMARY, primary_credentials)
    if CONF_SECONDARY_ACCOUNTS in conf:
        for account_conf in conf[CONF_SECONDARY_ACCOUNTS]:
            _setup_account(
                hass, account_conf, account_conf[CONF_ACCOUNT_NAME], primary_credentials
            )
    return True


def _setup_account(hass, account_conf, account_name, primary_credentials):
    if CONF_CLIENT_ID in account_conf and CONF_CLIENT_SECRET in account_conf:
        credentials = (
            account_conf.get(CONF_CLIENT_ID),
            account_conf.get(CONF_CLIENT_SECRET),
        )
    else:
        credentials = deepcopy(primary_credentials)

    token_path = build_config_file_path(hass, DEFAULT_CACHE_PATH)
    token_file = build_token_filename(account_conf)
    token_backend = FileSystemTokenBackend(
        token_path=token_path, token_filename=token_file
    )

    account = Account(credentials, token_backend=token_backend, timezone="UTC")
    is_authenticated = account.is_authenticated
    minimum_permissions = build_minimum_permissions(account_conf)
    permissions = validate_permissions(hass, minimum_permissions, filename=token_file)
    if is_authenticated and permissions:
        do_setup(hass, account_conf, account, account_name)
    else:
        _request_authorization(hass, account_conf, account, account_name)


def do_setup(hass, config, account, account_name):
    """Run the setup after we have everything configured."""
    email_sensors = config.get(CONF_EMAIL_SENSORS, [])
    query_sensors = config.get(CONF_QUERY_SENSORS, [])
    status_sensors = config.get(CONF_STATUS_SENSORS, [])
    enable_update = config.get(CONF_ENABLE_UPDATE, True)

    account_config = {
        CONF_ACCOUNT: account,
        CONF_EMAIL_SENSORS: email_sensors,
        CONF_QUERY_SENSORS: query_sensors,
        CONF_STATUS_SENSORS: status_sensors,
        CONF_ENABLE_UPDATE: enable_update,
        CONF_TRACK_NEW: config.get(CONF_TRACK_NEW, True),
        CONF_ACCOUNT_NAME: config.get(CONF_ACCOUNT_NAME, ""),
    }
    if DOMAIN not in hass.data:
        hass.data[DOMAIN] = {}
    hass.data[DOMAIN][account_name] = account_config

    _load_platforms(hass, account_name, config, account_config)


def _load_platforms(hass, account_name, config, account_config):
    hass.async_create_task(
        discovery.async_load_platform(
            hass, "calendar", DOMAIN, {CONF_ACCOUNT_NAME: account_name}, config
        )
    )
    if account_config[CONF_ENABLE_UPDATE]:
        hass.async_create_task(
            discovery.async_load_platform(
                hass, "notify", DOMAIN, {CONF_ACCOUNT_NAME: account_name}, config
            )
        )
    if (
        len(account_config[CONF_EMAIL_SENSORS]) > 0
        or len(account_config[CONF_QUERY_SENSORS]) > 0
        or len(account_config[CONF_STATUS_SENSORS]) > 0
    ):
        hass.async_create_task(
            discovery.async_load_platform(
                hass, "sensor", DOMAIN, {CONF_ACCOUNT_NAME: account_name}, config
            )
        )


def request_configuration(hass, url, callback_view, account_name):
    """Request the config."""
    configurator = callback_view.configurator
    if DOMAIN not in hass.data:
        hass.data[DOMAIN] = {}
    hass.data[DOMAIN][account_name] = configurator.async_request_config(
        f"{DEFAULT_NAME} - {account_name}",
        lambda _: None,
        link_name=CONFIGURATOR_LINK_NAME,
        link_url=url,
        description=CONFIGURATOR_DESCRIPTION,
        submit_caption=CONFIGURATOR_SUBMIT_CAPTION,
    )


def request_configuration_alt(hass, url, callback_view, account_name):
    """Request the alternate config."""
    configurator = callback_view.configurator
    if DOMAIN not in hass.data:
        hass.data[DOMAIN] = {}
    hass.data[DOMAIN][account_name] = configurator.async_request_config(
        f"{DEFAULT_NAME} - {account_name} - Alternative configuration",
        callback_view.alt_callback,
        link_name=CONFIGURATOR_LINK_NAME,
        link_url=url,
        fields=[{"id": "token", "name": "Returned Url", "type": "token"}],
        description="Complete the configuration and copy the complete url "
        "into this field afterwards and submit",
        submit_caption="Submit",
    )


def _request_authorization(hass, conf, account, account_name):
    alt_config = conf.get(CONF_ALT_CONFIG)
    if alt_config:
        callback_url = AUTH_CALLBACK_PATH_ALT
    else:
        callback_url = f"{get_url(hass, prefer_external=True)}{AUTH_CALLBACK_PATH}"
    scope = build_requested_permissions(conf)
    url, state = account.con.get_authorization_url(
        requested_scopes=scope, redirect_uri=callback_url
    )
    _LOGGER.info(
        "No token, or token doesn't have all required permissions; requesting authorization"
    )
    callback_view = O365AuthCallbackView(
        conf, None, account, state, callback_url, hass, account_name
    )
    hass.http.register_view(callback_view)
    if alt_config:
        request_configuration_alt(hass, url, callback_view, account_name)
    else:
        request_configuration(hass, url, callback_view, account_name)


class O365AuthCallbackView(HomeAssistantView):
    """O365 Authorization Callback View."""

    requires_auth = False
    url = AUTH_CALLBACK_PATH
    name = AUTH_CALLBACK_NAME

    def __init__(
        self, config, add_devices, account, state, callback_url, hass, account_name
    ):
        """Initialize."""
        self.config = config
        self.add_devices = add_devices
        self.account = account
        self.state = state
        self.callback = callback_url
        self._hass = hass
        self._account_name = account_name
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
        account_data = self._hass.data[DOMAIN][self._account_name]
        do_setup(self._hass, self.config, self.account, self._account_name)
        self.configurator.async_request_done(account_data)

        return web_response.Response(
            headers={"content-type": "text/html"},
            text="<script>window.close()</script>Success! This window can be closed",
        )

    def alt_callback(self, data):
        """Receive authorization token."""
        url = data.get("token") or [v for k, v in data.items()][0]

        result = self.account.con.request_token(
            url, state=self.state, redirect_uri=AUTH_CALLBACK_PATH_ALT
        )
        if not result:
            self.configurator.notify_errors(
                self._hass.data[DOMAIN][self._account_name],
                "Error while authenticating, please see logs for more info.",
            )
            return
        account_data = self._hass.data[DOMAIN][self._account_name]
        do_setup(self._hass, self.config, self.account, self._account_name)
        self.configurator.async_request_done(account_data)
        return
