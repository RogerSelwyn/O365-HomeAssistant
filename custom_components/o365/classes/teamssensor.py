"""O365 teams sensors."""

import logging

from homeassistant.components.sensor import SensorEntity
from homeassistant.const import ATTR_NAME

from ..const import (
    ATTR_ACTIVITY,
    ATTR_AVAILABILITY,
    ATTR_CHAT_ID,
    ATTR_CONTENT,
    ATTR_DATA,
    ATTR_FROM_DISPLAY_NAME,
    ATTR_IMPORTANCE,
    ATTR_STATE,
    ATTR_STATUS,
    ATTR_SUBJECT,
    ATTR_SUMMARY,
    CONF_ACCOUNT,
    CONF_CLIENT_ID,
    DOMAIN,
    EVENT_HA_EVENT,
    EVENT_SEND_CHAT_MESSAGE,
    EVENT_UPDATE_USER_STATUS,
    PERM_CHAT_READWRITE,
    PERM_MINIMUM_CHAT_WRITE,
    PERM_MINIMUM_PRESENCE_WRITE,
    PERM_PRESENCE_READWRITE,
    SENSOR_TEAMS_CHAT,
    SENSOR_TEAMS_STATUS,
)
from .entity import O365Entity

_LOGGER = logging.getLogger(__name__)


class O365TeamsSensor(O365Entity):
    """O365 Teams sensor processing."""

    def __init__(self, cordinator, name, entity_id, config, entity_type, unique_id):
        """Initialise the Teams Sensor."""
        super().__init__(cordinator, config, name, entity_id, entity_type, unique_id)
        self.teams = self._config[CONF_ACCOUNT].teams()
        self._application_id = self._config[CONF_CLIENT_ID]

    @property
    def icon(self):
        """Entity icon."""
        return "mdi:microsoft-teams"

    @property
    def native_value(self):
        """Sensor state."""
        return self.coordinator.data[self.entity_key][ATTR_STATE]


class O365TeamsStatusSensor(O365TeamsSensor, SensorEntity):
    """O365 Teams sensor processing."""

    def __init__(self, coordinator, name, entity_id, config, unique_id):
        """Initialise the Teams Sensor."""
        super().__init__(
            coordinator,
            name,
            entity_id,
            config,
            SENSOR_TEAMS_STATUS,
            unique_id,
        )

    def update_user_status(self, availability, activity, expiration_duration=None):
        """Update the users teams status."""
        if not self._validate_status_permissions():
            return False

        status = self.teams.set_my_presence(
            self._application_id, availability, activity, expiration_duration
        )
        self._raise_event(
            EVENT_UPDATE_USER_STATUS,
            {ATTR_AVAILABILITY: status.availability, ATTR_ACTIVITY: status.activity},
        )
        return False

    def _raise_event(self, event_type, status):
        self.hass.bus.fire(
            f"{DOMAIN}_{event_type}",
            {ATTR_NAME: self._name, ATTR_STATUS: status, EVENT_HA_EVENT: True},
        )
        _LOGGER.debug("%s - %s - %s", self._name, event_type, status)

    def _validate_status_permissions(self):
        return self._validate_permissions(
            PERM_MINIMUM_PRESENCE_WRITE,
            f"Not authorised to update status - requires permission: {PERM_PRESENCE_READWRITE}",
        )


class O365TeamsChatSensor(O365TeamsSensor, SensorEntity):
    """O365 Teams Chat sensor processing."""

    def __init__(self, coordinator, name, entity_id, config, unique_id):
        """Initialise the Teams Chat Sensor."""
        super().__init__(
            coordinator, name, entity_id, config, SENSOR_TEAMS_CHAT, unique_id
        )

    @property
    def extra_state_attributes(self):
        """Return entity specific state attributes."""
        attributes = {
            ATTR_FROM_DISPLAY_NAME: self.coordinator.data[self.entity_key][
                ATTR_FROM_DISPLAY_NAME
            ],
            ATTR_CONTENT: self.coordinator.data[self.entity_key][ATTR_CONTENT],
            ATTR_CHAT_ID: self.coordinator.data[self.entity_key][ATTR_CHAT_ID],
            ATTR_IMPORTANCE: self.coordinator.data[self.entity_key][ATTR_IMPORTANCE],
        }
        if self.coordinator.data[self.entity_key][ATTR_SUBJECT]:
            attributes[ATTR_SUBJECT] = self.coordinator.data[self.entity_key][
                ATTR_SUBJECT
            ]
        if self.coordinator.data[self.entity_key][ATTR_SUMMARY]:
            attributes[ATTR_SUMMARY] = self.coordinator.data[self.entity_key][
                ATTR_SUMMARY
            ]
        if self.coordinator.data[self.entity_key][ATTR_DATA]:
            attributes[ATTR_DATA] = self.coordinator.data[self.entity_key][ATTR_DATA]
        return attributes

    def send_chat_message(self, chat_id, message):
        """Send a message to the specified chat."""
        if not self._validate_chat_permissions():
            return False

        chats = self.teams.get_my_chats()
        for chat in chats:
            if chat.object_id == chat_id:
                message = chat.send_message(content=message)
                self._raise_event(EVENT_SEND_CHAT_MESSAGE, chat_id)
                return True
        _LOGGER.warning("Chat %s not found for send message", chat_id)
        return False

    def _raise_event(self, event_type, chat_id):
        self.hass.bus.fire(
            f"{DOMAIN}_{event_type}",
            {ATTR_CHAT_ID: chat_id, EVENT_HA_EVENT: True},
        )
        _LOGGER.debug("%s - %s", event_type, chat_id)

    def _validate_chat_permissions(self):
        return self._validate_permissions(
            PERM_MINIMUM_CHAT_WRITE,
            f"Not authorised to send message - requires permission: {PERM_CHAT_READWRITE}",
        )
