"""Generic O465 Sensor Entity."""

from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from ..const import ATTR_DATA, CONF_PERMISSIONS, DOMAIN


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

    def _validate_permissions(self, required_permission, required_permission_error):
        if not self._config[CONF_PERMISSIONS].validate_authorization(
            required_permission
        ):
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="not_authorised",
                translation_placeholders={
                    "required_permission": required_permission_error,
                },
            )

        return True
