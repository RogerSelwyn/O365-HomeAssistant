"""Main initialisation code."""
import functools as ft
import logging

from aiohttp import web_response
from homeassistant.components import configurator
from homeassistant.components.http import HomeAssistantView
from homeassistant.core import callback
from homeassistant.helpers import discovery
from homeassistant.helpers.network import get_url

from O365 import Account, FileSystemTokenBackend

from .const import (
    AUTH_CALLBACK_NAME,
    AUTH_CALLBACK_PATH_ALT,
    AUTH_CALLBACK_PATH_DEFAULT,
    CONF_ACCOUNT,
    CONF_ACCOUNT_NAME,
    CONF_ACCOUNTS,
    CONF_ALT_AUTH_FLOW,
    CONF_ALT_AUTH_METHOD,
    CONF_CHAT_SENSORS,
    CONF_CLIENT_ID,
    CONF_CLIENT_SECRET,
    CONF_CONFIG_TYPE,
    CONF_EMAIL_SENSORS,
    CONF_ENABLE_UPDATE,
    CONF_QUERY_SENSORS,
    CONF_STATUS_SENSORS,
    CONF_TRACK_NEW,
    CONFIGURATOR_DESCRIPTION_ALT,
    CONFIGURATOR_DESCRIPTION_DEFAULT,
    CONFIGURATOR_FIELDS,
    CONFIGURATOR_LINK_NAME,
    CONFIGURATOR_SUBMIT_CAPTION,
    CONST_CONFIG_TYPE_DICT,
    CONST_CONFIG_TYPE_LIST,
    CONST_PRIMARY,
    DEFAULT_CACHE_PATH,
    DEFAULT_NAME,
    DOMAIN,
)
from .schema import LEGACY_SCHEMA, MULTI_ACCOUNT_SCHEMA
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
    if CONF_ACCOUNTS not in conf:
        accounts = [LEGACY_SCHEMA(conf)]
        conf_type = CONST_CONFIG_TYPE_DICT
    else:
        accounts = MULTI_ACCOUNT_SCHEMA(conf)[CONF_ACCOUNTS]
        conf_type = CONST_CONFIG_TYPE_LIST

    for account in accounts:
        await _async_setup_account(hass, account, conf_type)

    return True


async def _async_setup_account(hass, account_conf, conf_type):
    credentials = (
        account_conf.get(CONF_CLIENT_ID),
        account_conf.get(CONF_CLIENT_SECRET),
    )
    account_name = account_conf.get(CONF_ACCOUNT_NAME, CONST_PRIMARY)

    token_path = build_config_file_path(hass, DEFAULT_CACHE_PATH)
    token_file = build_token_filename(account_conf, conf_type)
    token_backend = await hass.async_add_executor_job(
        ft.partial(
            FileSystemTokenBackend, token_path=token_path, token_filename=token_file
        )
    )

    account = await hass.async_add_executor_job(
        ft.partial(Account, credentials, token_backend=token_backend, timezone="UTC")
    )
    is_authenticated = account.is_authenticated
    minimum_permissions = build_minimum_permissions(hass, account_conf, conf_type)
    permissions = validate_permissions(hass, minimum_permissions, filename=token_file)
    if is_authenticated and permissions:
        do_setup(hass, account_conf, account, account_name, conf_type)
    else:
        _request_authorization(hass, account_conf, account, account_name, conf_type)


def do_setup(hass, config, account, account_name, conf_type):
    """Run the setup after we have everything configured."""
    _get_auth_method(config, account_name)
    email_sensors = config.get(CONF_EMAIL_SENSORS, [])
    query_sensors = config.get(CONF_QUERY_SENSORS, [])
    status_sensors = config.get(CONF_STATUS_SENSORS, [])
    chat_sensors = config.get(CONF_CHAT_SENSORS, [])
    enable_update = config.get(CONF_ENABLE_UPDATE, True)

    account_config = {
        CONF_ACCOUNT: account,
        CONF_EMAIL_SENSORS: email_sensors,
        CONF_QUERY_SENSORS: query_sensors,
        CONF_STATUS_SENSORS: status_sensors,
        CONF_CHAT_SENSORS: chat_sensors,
        CONF_ENABLE_UPDATE: enable_update,
        CONF_TRACK_NEW: config.get(CONF_TRACK_NEW, True),
        CONF_ACCOUNT_NAME: config.get(CONF_ACCOUNT_NAME, ""),
        CONF_CONFIG_TYPE: conf_type,
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
        or len(account_config[CONF_CHAT_SENSORS]) > 0
    ):
        hass.async_create_task(
            discovery.async_load_platform(
                hass, "sensor", DOMAIN, {CONF_ACCOUNT_NAME: account_name}, config
            )
        )


def _request_configuration_alt(hass, url, callback_view, account_name):
    """Request the config."""
    if DOMAIN not in hass.data:
        hass.data[DOMAIN] = {}

    request_content = _create_request_content_alt(
        hass, url, callback_view, account_name
    )
    hass.data[DOMAIN][account_name] = request_content


def _request_configuration_default(hass, url, callback_view, account_name):
    """Request the alternate config."""
    if DOMAIN not in hass.data:
        hass.data[DOMAIN] = {}

    request_content = _create_request_content_default(
        hass, url, callback_view, account_name
    )
    hass.data[DOMAIN][account_name] = request_content


def _create_request_content_alt(hass, url, callback_view, account_name):
    o365configurator = callback_view.configurator

    display_name = f" - {account_name}" if account_name != CONST_PRIMARY else ""
    view_name = f"{DEFAULT_NAME}{display_name} - Alternative configuration"
    return o365configurator.async_request_config(
        hass,
        view_name,
        lambda _: None,
        link_name=CONFIGURATOR_LINK_NAME,
        link_url=url,
        description=CONFIGURATOR_DESCRIPTION_ALT,
        submit_caption=CONFIGURATOR_SUBMIT_CAPTION,
    )


def _create_request_content_default(hass, url, callback_view, account_name):
    o365configurator = callback_view.configurator
    display_name = f" - {account_name}" if account_name != CONST_PRIMARY else ""
    view_name = f"{DEFAULT_NAME}{display_name}"
    return o365configurator.async_request_config(
        hass,
        view_name,
        callback_view.default_callback,
        link_name=CONFIGURATOR_LINK_NAME,
        link_url=url,
        fields=CONFIGURATOR_FIELDS,
        description=CONFIGURATOR_DESCRIPTION_DEFAULT,
        submit_caption="Submit",
    )


def _request_authorization(hass, conf, account, account_name, conf_type):
    alt_config = _get_auth_method(conf, account_name)
    callback_url = _get_callback_url(hass, alt_config)
    scope = build_requested_permissions(conf)
    url, state = account.con.get_authorization_url(
        requested_scopes=scope, redirect_uri=callback_url
    )
    message = (
        "No token, or token doesn't have all required permissions;"
        + f" requesting authorization for account: {account_name}"
    )
    _LOGGER.warning(message)
    callback_view = O365AuthCallbackView(
        conf, account, state, callback_url, hass, account_name, conf_type
    )
    hass.http.register_view(callback_view)
    if alt_config:
        _request_configuration_alt(hass, url, callback_view, account_name)
    else:
        _request_configuration_default(hass, url, callback_view, account_name)


def _get_callback_url(hass, alt_config):
    if alt_config:
        return f"{get_url(hass, prefer_external=True)}{AUTH_CALLBACK_PATH_ALT}"

    return AUTH_CALLBACK_PATH_DEFAULT


def _get_auth_method(conf, account_name):
    alt_flow = conf.get(CONF_ALT_AUTH_FLOW)
    alt_method = conf.get(CONF_ALT_AUTH_METHOD)
    if alt_flow is None and alt_method is None:
        _auth_deprecated_message(account_name, True)
        return False
    if alt_flow:
        _auth_deprecated_message(account_name, False)
    if alt_flow is False:
        _auth_deprecated_message(account_name, True)
        return True
    return alt_method is True


def _auth_deprecated_message(account_name, method_value):
    message = (
        f"Use of '{CONF_ALT_AUTH_FLOW}' configuration variable is deprecated."
        + f" Please set '{CONF_ALT_AUTH_METHOD}' to {method_value}"
        + f" and remove '{CONF_ALT_AUTH_FLOW}' if present from your config"
        + f" to retain existing authentication method for account: {account_name}."
        + " See https://github.com/RogerSelwyn/O365-HomeAssistant/#authentication"
        + " for more details."
    )
    _LOGGER.warning(message)


class O365AuthCallbackView(HomeAssistantView):
    """O365 Authorization Callback View."""

    requires_auth = False
    url = AUTH_CALLBACK_PATH_ALT
    name = AUTH_CALLBACK_NAME

    def __init__(
        self, config, account, state, callback_url, hass, account_name, conf_type
    ):
        """Initialize."""
        self._config = config
        self._account = account
        self._state = state
        self._callback = callback_url
        self._hass = hass
        self._account_name = account_name
        self.configurator = configurator
        self._conf_type = conf_type

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
            ft.partial(
                self._account.con.request_token,
                url,
                state=self._state,
                redirect_uri=self._callback,
            )
        )
        account_data = self._hass.data[DOMAIN][self._account_name]
        do_setup(
            self._hass, self._config, self._account, self._account_name, self._conf_type
        )
        self.configurator.async_request_done(self._hass, account_data)

        self._log_authenticated(self._account_name)
        return web_response.Response(
            headers={"content-type": "text/html"},
            text="<script>window.close()</script>Success! This window can be closed",
        )

    def default_callback(self, data):
        """Receive authorization token."""
        url = data.get("token") or [v for k, v in data.items()][0]

        result = self._account.con.request_token(
            url, state=self._state, redirect_uri=AUTH_CALLBACK_PATH_DEFAULT
        )
        if not result:
            self.configurator.notify_errors(
                self._hass,
                self._hass.data[DOMAIN][self._account_name],
                "Error while authenticating, please see logs for more info.",
            )
            return

        account_data = self._hass.data[DOMAIN][self._account_name]
        do_setup(
            self._hass, self._config, self._account, self._account_name, self._conf_type
        )
        self.configurator.async_request_done(self._hass, account_data)

        self._log_authenticated(self._account_name)
        return

    def _log_authenticated(self, account_name):
        _LOGGER.info("Succesfully authenticated for account: %s", account_name)
