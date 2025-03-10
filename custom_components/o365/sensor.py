"""Sensor processing."""

import logging

from homeassistant.const import CONF_EMAIL, CONF_NAME, CONF_UNIQUE_ID
from homeassistant.helpers import entity_platform

from .classes.mailsensor import O365AutoReplySensor, O365MailSensor
from .classes.teamssensor import O365TeamsChatSensor, O365TeamsStatusSensor
from .const import (
    CONF_ACCOUNT_NAME,
    CONF_AUTO_REPLY_SENSORS,
    CONF_CHAT_SENSORS,
    CONF_COORDINATOR_EMAIL,
    CONF_COORDINATOR_SENSORS,
    CONF_ENABLE_UPDATE,
    CONF_ENTITY_KEY,
    CONF_ENTITY_TYPE,
    CONF_IS_AUTHENTICATED,
    CONF_KEYS_EMAIL,
    CONF_KEYS_SENSORS,
    CONF_PERMISSIONS,
    CONF_SENSOR_CONF,
    CONF_STATUS_SENSORS,
    DOMAIN,
    PERM_CHAT_READWRITE,
    PERM_MAILBOX_SETTINGS,
    PERM_PRESENCE_READWRITE,
    SENSOR_AUTO_REPLY,
    SENSOR_TEAMS_CHAT,
    SENSOR_TEAMS_STATUS,
)
from .schema import (
    AUTO_REPLY_SERVICE_DISABLE_SCHEMA,
    AUTO_REPLY_SERVICE_ENABLE_SCHEMA,
    CHAT_SERVICE_SEND_MESSAGE_SCHEMA,
    STATUS_SERVICE_UPDATE_USER_PERERRED_STATUS_SCHEMA,
    STATUS_SERVICE_UPDATE_USER_STATUS_SCHEMA,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):  # pylint: disable=unused-argument
    """O365 platform definition."""
    if discovery_info is None:
        return None

    account_name = discovery_info[CONF_ACCOUNT_NAME]
    conf = hass.data[DOMAIN][account_name]

    is_authenticated = conf[CONF_IS_AUTHENTICATED]
    if not is_authenticated:
        return False

    sensor_entities = await _async_sensor_entities(conf, hass)
    email_entities = _email_entities(conf)
    entities = sensor_entities + email_entities

    async_add_entities(entities, False)
    await _async_setup_register_services(conf)

    return True


async def _async_sensor_entities(conf, hass):
    sensor_coordinator = conf[CONF_COORDINATOR_SENSORS]
    sensorentities = []
    for key in conf[CONF_KEYS_SENSORS]:
        if key[CONF_ENTITY_TYPE] == SENSOR_TEAMS_CHAT:
            sensorentities.append(
                O365TeamsChatSensor(
                    sensor_coordinator,
                    key[CONF_NAME],
                    key[CONF_ENTITY_KEY],
                    conf,
                    key[CONF_UNIQUE_ID],
                )
            )
            _LOGGER.warning(
                "The O365 Teams Chat sensors are now deprecated - please migrate to MS365 Teams "
                + "- for more details on how to do this see "
                + "https://rogerselwyn.github.io/O365-HomeAssistant/migration.html"
            )
        elif key[CONF_ENTITY_TYPE] == SENSOR_TEAMS_STATUS:
            sensorentities.append(
                O365TeamsStatusSensor(
                    sensor_coordinator,
                    key[CONF_NAME],
                    key[CONF_ENTITY_KEY],
                    conf,
                    key[CONF_UNIQUE_ID],
                    key[CONF_EMAIL],
                )
            )
            _LOGGER.warning(
                "The O365 Teams Status sensors are now deprecated - please migrate to MS365 Teams "
                + "- for more details on how to do this see "
                + "https://rogerselwyn.github.io/O365-HomeAssistant/migration.html"
            )
        elif key[CONF_ENTITY_TYPE] == SENSOR_AUTO_REPLY:
            entity = O365AutoReplySensor(
                sensor_coordinator,
                key[CONF_NAME],
                key[CONF_ENTITY_KEY],
                conf,
                key[CONF_UNIQUE_ID],
            )
            await entity.async_init(hass)
            sensorentities.append(entity)
            _LOGGER.warning(
                "The O365 Auto Reply sensors are now deprecated - please migrate to MS365 Mail "
                + "- for more details on how to do this see "
                + "https://rogerselwyn.github.io/O365-HomeAssistant/migration.html"
            )
    return sensorentities


def _email_entities(conf):
    email_coordinator = conf[CONF_COORDINATOR_EMAIL]
    _LOGGER.warning(
        "The O365 Email sensors are now deprecated - please migrate to MS365 Mail "
        + "- for more details on how to do this see "
        + "https://rogerselwyn.github.io/O365-HomeAssistant/migration.html"
    )
    return [
        O365MailSensor(
            email_coordinator,
            conf,
            key[CONF_SENSOR_CONF],
            key[CONF_NAME],
            key[CONF_ENTITY_KEY],
            key[CONF_UNIQUE_ID],
        )
        for key in conf[CONF_KEYS_EMAIL]
    ]


async def _async_setup_register_services(config):
    perms = config[CONF_PERMISSIONS]
    await _async_setup_status_services(config, perms)
    await _async_setup_chat_services(config, perms)
    await _async_setup_mailbox_services(config, perms)


async def _async_setup_status_services(config, perms):
    status_sensors = config.get(CONF_STATUS_SENSORS)
    if not status_sensors:
        return

    if not any(
        status_sensor.get(CONF_ENABLE_UPDATE) for status_sensor in status_sensors
    ):
        return

    platform = entity_platform.async_get_current_platform()
    if perms.validate_authorization(PERM_PRESENCE_READWRITE):
        platform.async_register_entity_service(
            "update_user_status",
            STATUS_SERVICE_UPDATE_USER_STATUS_SCHEMA,
            "async_update_user_status",
        )
        platform.async_register_entity_service(
            "update_user_preferred_status",
            STATUS_SERVICE_UPDATE_USER_PERERRED_STATUS_SCHEMA,
            "async_update_user_preferred_status",
        )


async def _async_setup_chat_services(config, perms):
    chat_sensors = config.get(CONF_CHAT_SENSORS)
    if not chat_sensors:
        return
    chat_sensor = chat_sensors[0]
    if not chat_sensor or not chat_sensor.get(CONF_ENABLE_UPDATE):
        return

    platform = entity_platform.async_get_current_platform()
    if perms.validate_authorization(PERM_CHAT_READWRITE):
        platform.async_register_entity_service(
            "send_chat_message",
            CHAT_SERVICE_SEND_MESSAGE_SCHEMA,
            "async_send_chat_message",
        )


async def _async_setup_mailbox_services(config, perms):
    if not config.get(CONF_ENABLE_UPDATE):
        return

    if not config.get(CONF_AUTO_REPLY_SENSORS):
        return

    platform = entity_platform.async_get_current_platform()
    if perms.validate_authorization(PERM_MAILBOX_SETTINGS):
        platform.async_register_entity_service(
            "auto_reply_enable",
            AUTO_REPLY_SERVICE_ENABLE_SCHEMA,
            "async_auto_reply_enable",
        )
        platform.async_register_entity_service(
            "auto_reply_disable",
            AUTO_REPLY_SERVICE_DISABLE_SCHEMA,
            "async_auto_reply_disable",
        )
