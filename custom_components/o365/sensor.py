"""Sensor processing."""

import logging

from homeassistant.const import CONF_ENABLED, CONF_NAME, CONF_UNIQUE_ID
from homeassistant.helpers import entity_platform

from .classes.mailsensor import O365AutoReplySensor
from .classes.taskssensor import O365TasksSensor, O365TasksSensorSensorServices
from .classes.teamssensor import O365TeamsChatSensor, O365TeamsStatusSensor
from .const import (
    CONF_ACCOUNT,
    CONF_ACCOUNT_NAME,
    CONF_AUTO_REPLY_SENSORS,
    CONF_CHAT_SENSORS,
    CONF_COORDINATOR,
    CONF_ENABLE_UPDATE,
    CONF_ENTITIES,
    CONF_ENTITY_KEY,
    CONF_ENTITY_TYPE,
    CONF_KEYS,
    CONF_PERMISSIONS,
    CONF_TASK_LIST,
    CONF_TODO,
    CONF_TODO_SENSORS,
    DOMAIN,
    PERM_MINIMUM_CHAT_WRITE,
    PERM_MINIMUM_MAILBOX_SETTINGS,
    PERM_MINIMUM_TASKS_WRITE,
    SENSOR_AUTO_REPLY,
    SENSOR_MAIL,
    SENSOR_TEAMS_CHAT,
    SENSOR_TEAMS_STATUS,
    SENSOR_TODO,
)
from .schema import (
    AUTO_REPLY_SERVICE_DISABLE_SCHEMA,
    AUTO_REPLY_SERVICE_ENABLE_SCHEMA,
    CHAT_SERVICE_SEND_MESSAGE_SCHEMA,
    TASK_SERVICE_COMPLETE_SCHEMA,
    TASK_SERVICE_DELETE_SCHEMA,
    TASK_SERVICE_NEW_SCHEMA,
    TASK_SERVICE_UPDATE_SCHEMA,
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

    entities = conf[CONF_ENTITIES]
    sensorentities = [
        entity
        for entity in entities
        if entity.entity_type
        in [
            SENSOR_MAIL,
            # SENSOR_TEAMS_STATUS,
            # SENSOR_TEAMS_CHAT,
            # SENSOR_TODO,
            # SENSOR_AUTO_REPLY,
        ]
    ]
    coordinator = conf[CONF_COORDINATOR]
    for key in conf[CONF_KEYS]:
        if key[CONF_ENTITY_TYPE] == SENSOR_TODO:
            sensorentities.append(
                O365TasksSensor(
                    coordinator,
                    key[CONF_TODO],
                    key[CONF_NAME],
                    key[CONF_TASK_LIST],
                    conf,
                    key[CONF_ENTITY_KEY],
                    key[CONF_UNIQUE_ID],
                )
            )
        elif key[CONF_ENTITY_TYPE] == SENSOR_TEAMS_CHAT:
            sensorentities.append(
                O365TeamsChatSensor(
                    coordinator,
                    key[CONF_NAME],
                    key[CONF_ENTITY_KEY],
                    conf,
                    key[CONF_UNIQUE_ID],
                    key[CONF_ENABLE_UPDATE],
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
    await _async_setup_register_services(hass, conf)

    return True


async def _async_setup_register_services(hass, config):
    perms = config[CONF_PERMISSIONS]
    await _async_setup_task_services(hass, config, perms)
    await _async_setup_chat_services(config, perms)
    await _async_setup_mailbox_services(config, perms)


async def _async_setup_task_services(hass, config, perms):
    todo_sensors = config.get(CONF_TODO_SENSORS)
    if (
        not todo_sensors
        or not todo_sensors.get(CONF_ENABLED)
        or not todo_sensors.get(CONF_ENABLE_UPDATE)
    ):
        return

    sensor_services = O365TasksSensorSensorServices(hass)
    hass.services.async_register(
        DOMAIN, "scan_for_task_lists", sensor_services.async_scan_for_task_lists
    )

    platform = entity_platform.async_get_current_platform()
    if perms.validate_minimum_permission(PERM_MINIMUM_TASKS_WRITE):
        platform.async_register_entity_service(
            "new_task",
            TASK_SERVICE_NEW_SCHEMA,
            "new_task",
        )
        platform.async_register_entity_service(
            "update_task",
            TASK_SERVICE_UPDATE_SCHEMA,
            "update_task",
        )
        platform.async_register_entity_service(
            "delete_task",
            TASK_SERVICE_DELETE_SCHEMA,
            "delete_task",
        )
        platform.async_register_entity_service(
            "complete_task",
            TASK_SERVICE_COMPLETE_SCHEMA,
            "complete_task",
        )


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
