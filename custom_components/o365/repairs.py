"""Repair flows."""

from __future__ import annotations

import functools as ft
import logging

import voluptuous as vol
from aiohttp import web_response
from homeassistant import data_entry_flow
from homeassistant.components.http import HomeAssistantView
from homeassistant.components.repairs import RepairsFlow  # ConfirmRepairFlow,
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.network import get_url

from .classes.permissions import Permissions
from .const import (
    AUTH_CALLBACK_NAME,
    AUTH_CALLBACK_PATH_ALT,
    AUTH_CALLBACK_PATH_DEFAULT,
    CONF_ACCOUNT,
    CONF_ACCOUNT_CONF,
    CONF_ACCOUNT_NAME,
    CONF_ALT_AUTH_METHOD,
    CONF_AUTH_URL,
    CONF_CONFIG_TYPE,
    CONF_FAILED_PERMISSIONS,
    CONF_URL,
    TOKEN_FILE_CORRUPTED,
    TOKEN_FILE_MISSING,
)
from .helpers.setup import do_setup
from .schema import REQUEST_AUTHORIZATION_DEFAULT_SCHEMA

_LOGGER = logging.getLogger(__name__)


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
        self._permissions = Permissions(hass, self._conf, self._conf_type)
        self._scope = self._permissions.requested_permissions
        self._flow = None
        self._url = None
        self._callback_view = None

    async def async_step_init(
        self,
        user_input: dict[str, str] | None = None,  # pylint: disable=unused-argument
    ) -> data_entry_flow.FlowResult:
        """Handle the first step of a fix flow."""
        self._url, self._flow = await self.hass.async_add_executor_job(
            ft.partial(
                self._account.con.get_authorization_url,
                requested_scopes=self._scope,
                redirect_uri=self._callback_url,
            )
        )
        if self._alt_config:
            return await self.async_step_request_alt()

        return await self.async_step_request_default()

    async def async_step_request_default(
        self, user_input: dict[str, str] | None = None
    ) -> data_entry_flow.FlowResult:
        """Handle the confirm step of a fix flow."""
        errors = {}
        _LOGGER.debug("Token file: %s", self._account.con.token_backend)
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
        url = (
            self._callback_view.token_url if self._alt_config else user_input[CONF_URL]
        )
        if url[:5].lower() == "http:":
            url = f"https:{url[5:]}"
        if "code" not in url:
            errors[CONF_URL] = "invalid_url"
            return errors

        result = await self.hass.async_add_executor_job(
            ft.partial(
                self._account.con.request_token,
                url,
                flow=self._flow,
                redirect_uri=self._callback_url,
            )
        )

        if result is not True:
            _LOGGER.error("Token file error - check log for errors from O365")
            errors[CONF_URL] = "token_file_error"
            return errors

        (
            permissions,
            self._failed_permissions,
        ) = await self._permissions.async_check_authorizations()
        if permissions == TOKEN_FILE_MISSING:
            errors[CONF_URL] = "missing_token_file"
            return errors
        if permissions == TOKEN_FILE_CORRUPTED:
            errors[CONF_URL] = "corrupted_token_file"
            return errors

        if not permissions:
            errors[CONF_URL] = "minimum_permissions"

        await do_setup(
            self.hass,
            self._conf,
            self._account,
            True,
            self._account_name,
            self._conf_type,
            self._permissions,
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


def get_callback_url(hass, alt_config):
    """Get the callback URL."""
    if alt_config:
        return f"{get_url(hass, prefer_external=True)}{AUTH_CALLBACK_PATH_ALT}"

    return AUTH_CALLBACK_PATH_DEFAULT
