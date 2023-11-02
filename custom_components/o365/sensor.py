"""Sensor processing."""

import logging

from homeassistant.const import CONF_NAME, CONF_UNIQUE_ID
from homeassistant.helpers import entity_platform

from .classes.mailsensor import O365AutoReplySensor, O365MailSensor

# from .classes.taskssensor import O365TasksSensor
from .classes.teamssensor import O365TeamsChatSensor, O365TeamsStatusSensor
from .const import CONF_ACCOUNT  # CONF_TASK_LIST,; CONF_TODO,
from .const import (
    CONF_ACCOUNT_NAME,
    CONF_AUTO_REPLY_SENSORS,  # TODO_TODO,
    CONF_CHAT_SENSORS,
    CONF_COORDINATOR,
    CONF_ENABLE_UPDATE,
    CONF_ENTITY_KEY,
    CONF_ENTITY_TYPE,
    CONF_KEYS,
    CONF_PERMISSIONS,
    CONF_SENSOR_CONF,
    DOMAIN,
    PERM_MINIMUM_CHAT_WRITE,
    PERM_MINIMUM_MAILBOX_SETTINGS,
    SENSOR_AUTO_REPLY,
    SENSOR_EMAIL,
    SENSOR_TEAMS_CHAT,
    SENSOR_TEAMS_STATUS,
)
from .schema import (
    AUTO_REPLY_SERVICE_DISABLE_SCHEMA,
    AUTO_REPLY_SERVICE_ENABLE_SCHEMA,
    CHAT_SERVICE_SEND_MESSAGE_SCHEMA,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_platform(
    hass, config, async_add_entities, discovery_info=None
):  # pylint: disable=unused-argument
    """O365 platform definition."""
    if discovery_info is None:
        return None

    account_name = discovery_info[CONF_ACCOUNT_NAME]
    conf = hass.data[DOMAIN][account_name]
    account = conf[CONF_ACCOUNT]

    is_authenticated = account.is_authenticated
    if not is_authenticated:
        return False

    coordinator = conf[CONF_COORDINATOR]
    sensorentities = []
    for key in conf[CONF_KEYS]:
        if key[CONF_ENTITY_TYPE] in SENSOR_EMAIL:
            sensorentities.append(
                O365MailSensor(
                    coordinator,
                    conf,
                    key[CONF_SENSOR_CONF],
                    key[CONF_NAME],
                    key[CONF_ENTITY_KEY],
                    key[CONF_UNIQUE_ID],
                )
            )
        # elif key[CONF_ENTITY_TYPE] == TODO_TODO:
        #     sensorentities.append(
        #         O365TasksSensor(
        #             coordinator,
        #             key[CONF_TODO],
        #             key[CONF_NAME],
        #             key[CONF_TASK_LIST],
        #             conf,
        #             key[CONF_ENTITY_KEY],
        #             key[CONF_UNIQUE_ID],
        #         )
        #     )
        elif key[CONF_ENTITY_TYPE] == SENSOR_TEAMS_CHAT:
            sensorentities.append(
                O365TeamsChatSensor(
                    coordinator,
                    key[CONF_NAME],
                    key[CONF_ENTITY_KEY],
                    conf,
                    key[CONF_UNIQUE_ID],
                )
            )
        elif key[CONF_ENTITY_TYPE] == SENSOR_TEAMS_STATUS:
            sensorentities.append(
                O365TeamsStatusSensor(
                    coordinator,
                    key[CONF_NAME],
                    key[CONF_ENTITY_KEY],
                    conf,
                    key[CONF_UNIQUE_ID],
                )
            )
        elif key[CONF_ENTITY_TYPE] == SENSOR_AUTO_REPLY:
            sensorentities.append(
                O365AutoReplySensor(
                    coordinator,
                    key[CONF_NAME],
                    key[CONF_ENTITY_KEY],
                    conf,
                    key[CONF_UNIQUE_ID],
                )
            )

    async_add_entities(sensorentities, False)
    await _async_setup_register_services(conf)

    return True


async def _async_setup_register_services(config):
    perms = config[CONF_PERMISSIONS]
    await _async_setup_chat_services(config, perms)
    await _async_setup_mailbox_services(config, perms)


async def _async_setup_chat_services(config, perms):
    chat_sensors = config.get(CONF_CHAT_SENSORS)
    if not chat_sensors:
        return
    chat_sensor = chat_sensors[0]
    if not chat_sensor or not chat_sensor.get(CONF_ENABLE_UPDATE):
        return

    platform = entity_platform.async_get_current_platform()
    if perms.validate_minimum_permission(PERM_MINIMUM_CHAT_WRITE):
        platform.async_register_entity_service(
            "send_chat_message",
            CHAT_SERVICE_SEND_MESSAGE_SCHEMA,
            "send_chat_message",
        )


async def _async_setup_mailbox_services(config, perms):
    if not config.get(CONF_ENABLE_UPDATE):
        return

    if not config.get(CONF_AUTO_REPLY_SENSORS):
        return

    platform = entity_platform.async_get_current_platform()
    if perms.validate_minimum_permission(PERM_MINIMUM_MAILBOX_SETTINGS):
        platform.async_register_entity_service(
            "auto_reply_enable",
            AUTO_REPLY_SERVICE_ENABLE_SCHEMA,
            "auto_reply_enable",
        )
        platform.async_register_entity_service(
            "auto_reply_disable",
            AUTO_REPLY_SERVICE_DISABLE_SCHEMA,
            "auto_reply_disable",
        )
