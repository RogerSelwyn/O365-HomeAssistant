"""Generic O465 Sensor Entity."""
import voluptuous as vol
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from ..const import ATTR_DATA, CONF_PERMISSIONS


class O365Entity(CoordinatorEntity):
    """O365 generic Sensor class."""

    _attr_should_poll = False
    _unrecorded_attributes = frozenset((ATTR_DATA,))

    def __init__(self, coordinator, config, name, entity_id, entity_type, unique_id):
        """Initialise the O365 Sensor."""
        super().__init__(coordinator)
        self._config = config
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
        """Entity Key property."""
        return self._entity_id

    @property
    def unique_id(self):
        """Entity unique id."""
        return self._unique_id

    def _validate_permissions(self, minimum_perm_list, required_permission):
        if not self._config[CONF_PERMISSIONS].validate_minimum_permission(
            minimum_perm_list
        ):
            raise vol.Invalid(
                f"Not authorisied requires permission: {required_permission}"
            )

        return True
