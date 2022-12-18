"""Generic O465 Sensor Entity."""
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from ..const import ATTR_STATE


class O365Sensor(CoordinatorEntity):
    """O365 generic Sensor class."""

    _attr_should_poll = False

    def __init__(self, coordinator, name, entity_id, entity_type, unique_id):
        """Initialise the O365 Sensor."""
        super().__init__(coordinator)
        self._name = name
        self._entity_id = entity_id
        self.entity_type = entity_type
        self._unique_id = unique_id

    @property
    def name(self):
        """Name property."""
        return self._name

    @property
    def entity_key(self):
        """Entity Keyr property."""
        return self._entity_id

    @property
    def state(self):
        """Sensor state."""
        return self.coordinator.data[self.entity_key][ATTR_STATE]

    @property
    def unique_id(self):
        """Entity unique id."""
        return self._unique_id
