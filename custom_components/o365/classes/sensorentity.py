"""Generic O465 Sensor Entity."""
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from ..const import ATTR_STATE


class O365Sensor(CoordinatorEntity):
    """O365 generic Sensor class."""

    _attr_should_poll = False

    def __init__(self, coordinator, name, entity_id, entity_type):
        """Initialise the O365 Sensor."""
        super().__init__(coordinator)
        self._name = name
        self._entity_id = entity_id
        self.entity_type = entity_type

    @property
    def name(self):
        """Name property."""
        return self._name

    @property
    def entity_id(self):
        """Entity_Id property."""
        return self._entity_id

    @property
    def state(self):
        """Sensor state."""
        return self.coordinator.data[self.entity_id][ATTR_STATE]
