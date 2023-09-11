"""Main initialisation code."""
import copy
import functools as ft
import logging
import os
import shutil

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
    CONF_EMAIL_SENSORS,
    CONF_FAILED_PERMISSIONS,
    CONF_GROUPS,
    CONF_QUERY_SENSORS,
    CONF_SHARED_MAILBOX,
    CONF_STATUS_SENSORS,
    CONF_TODO_SENSORS,
    CONST_CONFIG_TYPE_DICT,
    CONST_CONFIG_TYPE_LIST,
    CONST_PRIMARY,
    CONST_UTC_TIMEZONE,
    DOMAIN,
    LEGACY_ACCOUNT_NAME,
    O365_STORAGE_TOKEN,
    TOKEN_FILE_MISSING,
    TOKEN_FILENAME,
    YAML_CALENDARS,
)
from .schema import LEGACY_SCHEMA, MULTI_ACCOUNT_SCHEMA
from .setup import do_setup
from .utils.filemgmt import build_config_file_path, build_token_filename

_LOGGER = logging.getLogger(__name__)


async def async_setup(hass, config):
    """Set up the O365 platform."""
    conf = config.get(DOMAIN, {})
    if CONF_ACCOUNTS not in conf:
        await _async_legacy_migration_repair(hass)
        accounts = [LEGACY_SCHEMA(conf)]
        conf_type = CONST_CONFIG_TYPE_DICT
        _write_out_config(hass, accounts)
    else:
        accounts = MULTI_ACCOUNT_SCHEMA(conf)[CONF_ACCOUNTS]
        conf_type = CONST_CONFIG_TYPE_LIST

    for account in accounts:
        await _async_setup_account(hass, account, conf_type)

    return True


async def _async_legacy_migration_repair(hass):
    url = "https://rogerselwyn.github.io/O365-HomeAssistant/legacy_migration.html"
    message = (
        "Secondary/Legacy configuration method is now deprecated and will be "
        + "removed in first release in 2024. Please migrate to the Primary configuration "
        + "method documented here - "
        + f"{url}"
    )
    _LOGGER.warning(message)
    # Register a repair issue
    async_create_issue(
        hass,
        DOMAIN,
        "deprecated_legacy_configuration",
        # breaks_in_ha_version="2023.4.0",  # Warning first added in 2022.11.0
        is_fixable=False,
        learn_more_url=url,
        severity=IssueSeverity.WARNING,
        translation_key="deprecated_legacy_configuration",
    )


def _write_out_config(hass, accounts):
    yaml_filepath = build_config_file_path(hass, "o365_converted_configuration.yaml")
    account_name = LEGACY_ACCOUNT_NAME
    account = copy.deepcopy(accounts[0])
    account[CONF_ACCOUNT_NAME] = account_name
    account.move_to_end(CONF_ACCOUNT_NAME, False)
    account[CONF_CLIENT_ID] = "xxxxx"
    account[CONF_CLIENT_SECRET] = "xxxxx"
    account = dict(account)
    _remove_ordered_dict(account, CONF_EMAIL_SENSORS)
    _remove_ordered_dict(account, CONF_QUERY_SENSORS)
    _remove_ordered_dict(account, CONF_STATUS_SENSORS)
    _remove_ordered_dict(account, CONF_CHAT_SENSORS)
    config = {"o365": {"accounts": [account]}}
    with open(yaml_filepath, "w", encoding="UTF8") as out:
        out.write("\n")
        yaml.dump(
            config,
            out,
            Dumper=_IncreaseIndent,
            default_flow_style=False,
            encoding="UTF8",
        )
        out.close()
    _copy_token_file(hass, account_name)


def _remove_ordered_dict(account, sensor):
    if sensor in account:
        sensors = account[sensor]
        new_sensors = [dict(item) for item in sensors]
        account[sensor] = new_sensors
    return account


async def _async_setup_account(hass, account_conf, conf_type):
    credentials = (
        account_conf.get(CONF_CLIENT_ID),
        account_conf.get(CONF_CLIENT_SECRET),
    )
    account_name = account_conf.get(CONF_ACCOUNT_NAME, CONST_PRIMARY)
    main_resource = account_conf.get(CONF_SHARED_MAILBOX)
    if not _validate_shared_schema(account_name, main_resource, account_conf):
        return

    token_path = build_config_file_path(hass, O365_STORAGE_TOKEN)
    token_file = build_token_filename(account_conf, conf_type)
    token_backend = await hass.async_add_executor_job(
        ft.partial(
            FileSystemTokenBackend, token_path=token_path, token_filename=token_file
        )
    )
    account = await hass.async_add_executor_job(
        ft.partial(
            Account,
            credentials,
            token_backend=token_backend,
            timezone=CONST_UTC_TIMEZONE,
            main_resource=main_resource,
        )
    )
    is_authenticated = account.is_authenticated
    perms = Permissions(hass, account_conf, conf_type)
    permissions, failed_permissions = perms.validate_permissions()
    check_token = None
    if is_authenticated and permissions and permissions != TOKEN_FILE_MISSING:
        check_token = await _async_check_token(hass, account, account_name)
        if check_token:
            do_setup(hass, account_conf, account, account_name, conf_type, perms)
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


async def _async_check_token(hass, account, account_name):
    try:
        await hass.async_add_executor_job(account.get_current_user)
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


def _copy_token_file(hass, account_name):
    old_file = TOKEN_FILENAME.format("")
    new_file = TOKEN_FILENAME.format(f"_{account_name}")
    old_filepath = build_config_file_path(hass, f"{O365_STORAGE_TOKEN}/{old_file}")
    new_filepath = build_config_file_path(hass, f"{O365_STORAGE_TOKEN}/{new_file}")
    if os.path.exists(old_filepath):
        shutil.copy(src=old_filepath, dst=new_filepath)

    old_file = YAML_CALENDARS.format(DOMAIN, "")
    new_file = YAML_CALENDARS.format(DOMAIN, f"_{account_name}")
    old_filepath = build_config_file_path(hass, old_file)
    new_filepath = build_config_file_path(hass, new_file)
    if os.path.exists(old_filepath):
        shutil.copy(src=old_filepath, dst=new_filepath)


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
    message = (
        "No token file found;"
        if token_missing == TOKEN_FILE_MISSING
        else "Token doesn't have all required permissions;"
    )
    _LOGGER.warning("%s %s", message, base_message)
    # url = "https://rogerselwyn.github.io/O365-HomeAssistant/legacy_migration.html"
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


class _IncreaseIndent(yaml.Dumper):
    def increase_indent(self, flow=False, indentless=False):
        return super(_IncreaseIndent, self).increase_indent(flow, False)
