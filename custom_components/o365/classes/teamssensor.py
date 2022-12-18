"""O365 teams sensors."""

from homeassistant.components.sensor import SensorEntity

from ..const import (
    ATTR_CHAT_ID,
    ATTR_CONTENT,
    ATTR_FROM_DISPLAY_NAME,
    ATTR_IMPORTANCE,
    ATTR_SUBJECT,
    ATTR_SUMMARY,
    SENSOR_TEAMS_CHAT,
    SENSOR_TEAMS_STATUS,
)
from .sensorentity import O365Sensor


class O365TeamsSensor(O365Sensor):
    """O365 Teams sensor processing."""

    def __init__(self, cordinator, account, name, entity_id, entity_type, unique_id):
        """Initialise the Teams Sensor."""
        super().__init__(cordinator, name, entity_id, entity_type, unique_id)
        self.teams = account.teams()

    @property
    def icon(self):
        """Entity icon."""
        return "mdi:microsoft-teams"


class O365TeamsStatusSensor(O365TeamsSensor, SensorEntity):
    """O365 Teams sensor processing."""

    def __init__(self, coordinator, account, name, entity_id, unique_id):
        """Initialise the Teams Sensor."""
        super().__init__(
            coordinator, account, name, entity_id, SENSOR_TEAMS_STATUS, unique_id
        )


class O365TeamsChatSensor(O365TeamsSensor, SensorEntity):
    """O365 Teams Chat sensor processing."""

    def __init__(self, coordinator, account, name, entity_id, unique_id):
        """Initialise the Teams Chat Sensor."""
        super().__init__(
            coordinator, account, name, entity_id, SENSOR_TEAMS_CHAT, unique_id
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
        return attributes
