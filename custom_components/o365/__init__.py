"""Main initialisation code."""

import json
import logging

import voluptuous as vol
import yaml
from homeassistant.const import CONF_ENABLED
from homeassistant.helpers.issue_registry import IssueSeverity, async_create_issue
from O365 import Account, FileSystemTokenBackend
from oauthlib.oauth2.rfc6749.errors import InvalidClientError

from .classes.permissions import Permissions
from .const import (
    CONF_ACCOUNT,
    CONF_ACCOUNT_CONF,
    CONF_ACCOUNT_NAME,
    CONF_ACCOUNTS,
    CONF_AUTO_REPLY_SENSORS,
    CONF_CHAT_SENSORS,
    CONF_CLIENT_ID,
    CONF_CLIENT_SECRET,
    CONF_CONFIG_TYPE,
    CONF_FAILED_PERMISSIONS,
    CONF_GROUPS,
    CONF_SHARED_MAILBOX,
    CONF_STATUS_SENSORS,
    CONF_TODO_SENSORS,
    CONST_CONFIG_TYPE_LIST,
    CONST_PRIMARY,
    CONST_UTC_TIMEZONE,
    DOMAIN,
    TOKEN_FILE_CORRUPTED,
    TOKEN_FILE_MISSING,
    TOKEN_FILE_OUTDATED,
)
from .helpers.migration import MigrationServices
from .helpers.setup import do_setup
from .schema import MULTI_ACCOUNT_SCHEMA

CONFIG_SCHEMA = vol.Schema({DOMAIN: MULTI_ACCOUNT_SCHEMA}, extra=vol.ALLOW_EXTRA)
_LOGGER = logging.getLogger(__name__)


async def async_setup(hass, config):
    """Set up the O365 platform."""
    _LOGGER.debug("Startup")
    conf = config.get(DOMAIN, {})

    accounts = MULTI_ACCOUNT_SCHEMA(conf)[CONF_ACCOUNTS]
    conf_type = CONST_CONFIG_TYPE_LIST

    for account in accounts:
        await _async_setup_account(hass, account, conf_type)

    await _async_setup_migration_service(hass, conf)
    _LOGGER.debug("Finish")
    return True


async def _async_setup_account(hass, account_conf, conf_type):
    credentials = (
        account_conf.get(CONF_CLIENT_ID),
        account_conf.get(CONF_CLIENT_SECRET),
    )
    account_name = account_conf.get(CONF_ACCOUNT_NAME, CONST_PRIMARY)
    main_resource = account_conf.get(CONF_SHARED_MAILBOX)
    _LOGGER.debug("Validate shared")
    if not _validate_shared_schema(account_name, main_resource, account_conf):
        return

    _LOGGER.debug("Permissions setup")
    perms = Permissions(hass, account_conf, conf_type)
    permissions, failed_permissions = await perms.async_check_authorizations()

    account, is_authenticated = await hass.async_add_executor_job(
        _try_authentication, perms, credentials, main_resource
    )

    if is_authenticated and permissions is True:
        _LOGGER.debug("do setup")
        check_token = await _async_check_token(hass, account, account_name)
        if check_token:
            await do_setup(
                hass,
                account_conf,
                account,
                is_authenticated,
                account_name,
                conf_type,
                perms,
            )
    else:
        await _async_authorization_repair(
            hass,
            account_conf,
            account,
            account_name,
            conf_type,
            failed_permissions,
            permissions,
        )


def _try_authentication(perms, credentials, main_resource):
    _LOGGER.debug("Setup token")
    token_backend = FileSystemTokenBackend(
        token_path=perms.token_path,
        token_filename=perms.token_filename,
    )
    _LOGGER.debug("Setup account")
    account = Account(
        credentials,
        token_backend=token_backend,
        timezone=CONST_UTC_TIMEZONE,
        main_resource=main_resource,
    )

    try:
        return account, account.is_authenticated

    except json.decoder.JSONDecodeError:
        return account, False


async def _async_check_token(hass, account, account_name):
    try:
        await hass.async_add_executor_job(account.get_current_user_data)
        return True
    except InvalidClientError as err:
        if "client secret" in err.description and "expired" in err.description:
            _LOGGER.warning(
                "Client Secret expired for account: %s. Create new Client Secret in Azure App.",
                account_name,
            )
        else:
            _LOGGER.warning(
                "Token error for account: %s. Error - %s", account_name, err.description
            )
        return False
    except RuntimeError as err:
        if "Refresh token operation failed: invalid_grant" in err.args:
            _LOGGER.warning(
                "Token has expired for account: '%s'. "
                + "Please delete token, reboot and re-authenticate.",
                account_name,
            )
            return False
        elif "Refresh token operation failed: invalid_client" in err.args:
            _LOGGER.warning(
                "Invalid Client ID for account: '%s'. "
                + "Please delete token, reboot and re-authenticate.",
                account_name,
            )
            return False
        raise err


def _validate_shared_schema(account_name, main_account, config):
    if not main_account:
        return True

    error = False
    if config.get(CONF_STATUS_SENSORS, None):
        _LOGGER.error("Status sensor not allowed for shared account: %s", account_name)
        error = True
    if config.get(CONF_CHAT_SENSORS, None):
        _LOGGER.error("Chat sensor not allowed for shared account: %s", account_name)
        error = True
    if (
        config.get(CONF_TODO_SENSORS, None)
        and config.get(CONF_TODO_SENSORS)[CONF_ENABLED]
    ):
        _LOGGER.error("Todo sensors not allowed for shared account: %s", account_name)
        error = True
    if config.get(CONF_GROUPS, None):
        _LOGGER.error("Groups not allowed for shared account: %s", account_name)
        error = True
    if config.get(CONF_AUTO_REPLY_SENSORS, None):
        _LOGGER.error(
            "AutoReply sensor not allowed for shared account: %s", account_name
        )
        error = True

    return not error


async def _async_authorization_repair(
    hass,
    account_conf,
    account,
    account_name,
    conf_type,
    failed_permissions,
    token_missing,
):
    base_message = f"requesting authorization for account: {account_name}"

    if token_missing == TOKEN_FILE_MISSING:
        message = "No token file found;"
    elif token_missing == TOKEN_FILE_CORRUPTED:
        message = "Token file corrupted;"
    elif token_missing == TOKEN_FILE_OUTDATED:
        message = "Token file is outdated, it has been deleted;"
    else:
        message = "Token doesn't have all required permissions;"

    _LOGGER.warning("%s %s", message, base_message)
    data = {
        CONF_ACCOUNT_CONF: account_conf,
        CONF_ACCOUNT: account,
        CONF_ACCOUNT_NAME: account_name,
        CONF_CONFIG_TYPE: conf_type,
        CONF_FAILED_PERMISSIONS: failed_permissions,
    }
    # Register a repair issue
    async_create_issue(
        hass,
        DOMAIN,
        "authorization",
        data=data,
        is_fixable=True,
        # learn_more_url=url,
        severity=IssueSeverity.ERROR,
        translation_key="authorization",
        translation_placeholders={
            CONF_ACCOUNT_NAME: account_name,
        },
    )


async def _async_setup_migration_service(hass, config):
    migration_services = MigrationServices(hass, config)
    hass.services.async_register(
        DOMAIN, "migrate_config", migration_services.async_migrate_config
    )


class _IncreaseIndent(yaml.Dumper):
    def increase_indent(self, flow=False, indentless=False):
        return super(_IncreaseIndent, self).increase_indent(flow, False)
