import logging
from homeassistant.components.group import DOMAIN as GROUP_DOMAIN
from homeassistant.helpers import entity_registry

_LOGGER = logging.getLogger(__name__)

DOMAIN = "motion_sensor_groups"


class MotionSensorGrouper:
    """Class to group motion sensors by area."""

    def __init__(self, hass):
        """Initialize the motion sensor grouper."""
        self.hass = hass

    async def create_sensor_groups(self):
        """Create groups of motion sensors by area."""
        # Get all areas from Home Assistant

        areas = self.hass.helpers.area_registry.async_get()
        # area_list = areas.async_list_areas()

        # Get all entities from Home Assistant
        # entities = await self.hass.helpers.entity_registry.async_get_registry()

        # Get entity registry to find light entities
        entities = entity_registry.async_get(self.hass)

        # Loop over each area and find associated motion sensors
        for area_id, area in areas.areas.items():
            # Find all motion sensors in the area
            motion_sensors = [
                entity.entity_id
                for entity in entities.entities.values()
                if entity.device_class == "motion" and entity.area_id == area_id
            ]

            if motion_sensors:
                group_name = (
                    f"group.motion_sensors_{area.name.lower().replace(' ', '_')}"
                )
                await self._create_group(group_name, motion_sensors)

    async def _create_group(self, group_name, entity_ids):
        """Create a group of entities in Home Assistant."""
        service_data = {
            "object_id": group_name.split(".")[-1],
            "name": group_name.split(".")[-1].replace("_", " ").title(),
            "entities": entity_ids,
        }

        # Call Home Assistant service to create the group
        await self.hass.services.async_call("group", "set", service_data, blocking=True)
        _LOGGER.info(f"Group {group_name} created with entities: {entity_ids}")
