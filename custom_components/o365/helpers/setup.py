"""Do configuration setup."""

import asyncio
import logging

from homeassistant.const import CONF_ENABLED
from homeassistant.helpers import discovery

from ..const import (
    CONF_ACCOUNT_NAME,
    CONF_CHAT_SENSORS,
    CONF_COORDINATOR_EMAIL,
    CONF_COORDINATOR_SENSORS,
    CONF_EMAIL_SENSORS,
    CONF_ENABLE_CALENDAR,
    CONF_ENABLE_UPDATE,
    CONF_KEYS_EMAIL,
    CONF_KEYS_SENSORS,
    CONF_QUERY_SENSORS,
    CONF_STATUS_SENSORS,
    CONF_TODO_SENSORS,
    DOMAIN,
)
from ..utils.utils import build_account_config
from .coordinator import O365EmailCordinator, O365SensorCordinator

_LOGGER = logging.getLogger(__name__)


async def do_setup(
    hass, config, account, is_authenticated, account_name, conf_type, perms
):
    """Run the setup after we have everything configured."""
    account_config = build_account_config(
        config, account, is_authenticated, conf_type, perms
    )

    if DOMAIN not in hass.data:
        hass.data[DOMAIN] = {}
    hass.data[DOMAIN][account_name] = account_config

    async with asyncio.TaskGroup() as group:
        sensors_result = group.create_task(_async_sensor_setup(hass, account_config))
        email_result = group.create_task(_async_email_setup(hass, account_config))

    sensor_keys = sensors_result.result()["keys"]
    sensor_coordinator = sensors_result.result()["coordinator"]
    email_keys = email_result.result()["keys"]
    email_coordinator = email_result.result()["coordinator"]
    hass.data[DOMAIN][account_name][CONF_KEYS_SENSORS] = sensor_keys
    hass.data[DOMAIN][account_name][CONF_COORDINATOR_SENSORS] = sensor_coordinator
    hass.data[DOMAIN][account_name][CONF_KEYS_EMAIL] = email_keys
    hass.data[DOMAIN][account_name][CONF_COORDINATOR_EMAIL] = email_coordinator

    _load_platforms(hass, account_name, config, account_config)


async def _async_sensor_setup(hass, account_config):
    _LOGGER.debug("Sensor setup - start")
    sensor_coordinator = O365SensorCordinator(hass, account_config)
    sensor_keys = await sensor_coordinator.async_setup_entries()
    if sensor_keys:
        await sensor_coordinator.async_config_entry_first_refresh()
    _LOGGER.debug("Sensor setup - finish")
    return {"coordinator": sensor_coordinator, "keys": sensor_keys}


async def _async_email_setup(hass, account_config):
    _LOGGER.debug("Email setup - start")
    email_coordinator = O365EmailCordinator(hass, account_config)
    email_keys = await email_coordinator.async_setup_entries()
    if email_keys:
        await email_coordinator.async_config_entry_first_refresh()
    _LOGGER.debug("Email setup - finish")
    return {"coordinator": email_coordinator, "keys": email_keys}


def _load_platforms(hass, account_name, config, account_config):
    if account_config[CONF_ENABLE_CALENDAR]:
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

    if len(account_config[CONF_TODO_SENSORS]) > 0 and account_config[
        CONF_TODO_SENSORS
    ].get(CONF_ENABLED, False):
        hass.async_create_task(
            discovery.async_load_platform(
                hass, "todo", DOMAIN, {CONF_ACCOUNT_NAME: account_name}, config
            )
        )
