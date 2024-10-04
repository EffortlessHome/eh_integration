from homeassistant.components.group import Group
from homeassistant.helpers.entity import async_generate_entity_id
from homeassistant.const import ENTITY_MATCH_ALL

import logging
from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.helpers.template import Template

_LOGGER = logging.getLogger(__name__)

from .const import CONF_USERNAME
from .const import CONF_SYSTEMID
from .const import DOMAIN

async def create_light_group(hass, group_name):
    """Create a light group programmatically by automatically finding all light entities."""
    
    # Find all light entities in Home Assistant
    all_entities = hass.states.async_all()
    light_entities = [entity.entity_id for entity in all_entities if entity.entity_id.startswith("light.")]

    if not light_entities:
        # If no light entities are found, log a warning and return
        hass.logger.warning("No light entities found to add to the group.")
        return None

    # Generate a unique entity ID for the new light group
    entity_id = async_generate_entity_id("light.{}", group_name, hass=hass)

    # Create the group using the Group component
    group = Group(
        hass,  # Home Assistant core object
        name=group_name,
        entity_ids=light_entities,  # List of light entities
        mode=ENTITY_MATCH_ALL,  # Match all entities in the group
        created_by_service=True,
        order=any,
        icon="mdi:lightbulb",  # Optional: set an icon for the group
    )

    # Register the group in Home Assistant
    await group.async_update_ha_state()
    hass.states.async_set(entity_id, "on")  # Set the group state to 'on' by default

    return entity_id

# Example usage inside a custom integration
async def async_setup_lightgroup_entry(hass, config_entry):
    # Call the function to create a light group with all discovered lights
    await create_light_group(hass, "all_lights_group")

    return True