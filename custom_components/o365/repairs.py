"""Repair flows."""
from __future__ import annotations

import functools as ft

import voluptuous as vol
from aiohttp import web_response
from homeassistant import data_entry_flow
from homeassistant.components.http import HomeAssistantView
from homeassistant.components.repairs import RepairsFlow  # ConfirmRepairFlow,
from homeassistant.core import HomeAssistant, callback

from .const import (
    AUTH_CALLBACK_NAME,
    AUTH_CALLBACK_PATH_ALT,
    CONF_ACCOUNT,
    CONF_ACCOUNT_CONF,
    CONF_ACCOUNT_NAME,
    CONF_ALT_AUTH_METHOD,
    CONF_AUTH_URL,
    CONF_CONFIG_TYPE,
    CONF_FAILED_PERMISSIONS,
    CONF_URL,
)
from .schema import REQUEST_AUTHORIZATION_DEFAULT_SCHEMA
from .setup import do_setup
from .utils import (
    build_minimum_permissions,
    build_requested_permissions,
    build_token_filename,
    get_callback_url,
    validate_permissions,
)


class AuthorizationRepairFlow(RepairsFlow):
    """Handler for an issue fixing flow."""

    def __init__(
        self,
        hass,
        data,
    ):
        """Initialise the repair flow."""
        self._data = data
        self._conf = data.get(CONF_ACCOUNT_CONF)
        self._account = data.get(CONF_ACCOUNT)
        self._failed_permissions = data.get(CONF_FAILED_PERMISSIONS)
        self._conf_type = data.get(CONF_CONFIG_TYPE)
        self._alt_config = self._conf.get(CONF_ALT_AUTH_METHOD)
        self._account_name = self._conf.get(CONF_ACCOUNT_NAME)
        self._callback_url = get_callback_url(hass, self._alt_config)
        scope = build_requested_permissions(self._conf)
        self._url, self._state = self._account.con.get_authorization_url(
            requested_scopes=scope, redirect_uri=self._callback_url
        )
        self._callback_view = None

    async def async_step_init(
        self,
        user_input: dict[str, str] | None = None,  # pylint: disable=unused-argument
    ) -> data_entry_flow.FlowResult:
        """Handle the first step of a fix flow."""
        if self._alt_config:
            return await self.async_step_request_alt()

        return await self.async_step_request_default()

    async def async_step_request_default(
        self, user_input: dict[str, str] | None = None
    ) -> data_entry_flow.FlowResult:
        """Handle the confirm step of a fix flow."""
        errors = {}
        if user_input is not None:
            errors = await self._async_validate_response(user_input)
            if not errors:
                return self.async_create_entry(title="", data={})

        failed_permissions = None
        if self._failed_permissions:
            failed_permissions = f"\n\n {', '.join(self._failed_permissions)}"
        return self.async_show_form(
            step_id="request_default",
            data_schema=vol.Schema(REQUEST_AUTHORIZATION_DEFAULT_SCHEMA),
            description_placeholders={
                CONF_AUTH_URL: self._url,
                CONF_ACCOUNT_NAME: self._account_name,
                CONF_FAILED_PERMISSIONS: failed_permissions,
            },
            errors=errors,
        )

    async def async_step_request_alt(
        self, user_input: dict[str, str] | None = None
    ) -> data_entry_flow.FlowResult:
        """Handle the confirm step of a fix flow."""
        errors = {}
        if user_input is not None:
            errors = await self._async_validate_response(user_input)
            if not errors:
                return self.async_create_entry(title="", data={})

        if not self._callback_view:
            self._callback_view = O365AuthCallbackView()
            self.hass.http.register_view(self._callback_view)

        failed_permissions = None
        if self._failed_permissions:
            failed_permissions = f"\n\nMissing - {', '.join(self._failed_permissions)}"

        return self.async_show_form(
            step_id="request_alt",
            description_placeholders={
                CONF_AUTH_URL: self._url,
                CONF_ACCOUNT_NAME: self._account_name,
                CONF_FAILED_PERMISSIONS: failed_permissions,
            },
            errors=errors,
        )

    async def _async_validate_response(self, user_input):
        errors = {}
        if not self._alt_config:
            url = user_input[CONF_URL]
        else:
            url = self._callback_view.token_url

        if url[:5].lower() == "http:":
            url = f"https:{url[5:]}"
        if "code" not in url:
            errors[CONF_URL] = "invalid_url"
            return errors

        await self.hass.async_add_executor_job(
            ft.partial(
                self._account.con.request_token,
                url,
                state=self._state,
                redirect_uri=self._callback_url,
            )
        )

        token_file = build_token_filename(self._conf, self._conf_type)
        minimum_permissions = build_minimum_permissions(
            self.hass, self._conf, self._conf_type
        )
        permissions, self._failed_permissions = validate_permissions(
            self.hass, minimum_permissions, filename=token_file
        )
        if not permissions:
            errors[CONF_URL] = "minimum_permissions"

        do_setup(
            self.hass, self._conf, self._account, self._account_name, self._conf_type
        )

        return errors


async def async_create_fix_flow(
    hass: HomeAssistant,
    issue_id: str,
    data: dict[str, str | int | float | None] | None,
) -> RepairsFlow:
    """Create flow."""
    if issue_id == "authorization":
        return AuthorizationRepairFlow(hass, data)


class O365AuthCallbackView(HomeAssistantView):
    """O365 Authorization Callback View."""

    requires_auth = False
    url = AUTH_CALLBACK_PATH_ALT
    name = AUTH_CALLBACK_NAME

    def __init__(self):
        """Initialize."""
        self.token_url = None

    @callback
    async def get(self, request):
        """Receive authorization token."""
        self.token_url = str(request.url)

        return web_response.Response(
            headers={"content-type": "text/html"},
            text="<script>window.close()</script>This window can be closed",
        )
