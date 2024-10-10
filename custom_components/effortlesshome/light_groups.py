from __future__ import annotations

import logging
from homeassistant.components.light import DOMAIN as LIGHT_DOMAIN
from homeassistant.components.group import DOMAIN as GROUP_DOMAIN
from homeassistant.helpers import entity_registry

_LOGGER = logging.getLogger(__name__)


async def create_light_groups_by_area(hass):
    """Create light groups based on areas with assigned lights."""

    _LOGGER.debug("In create light groups")

    # Get all areas
    areas = hass.helpers.area_registry.async_get()
    area_list = areas.async_list_areas()

    # Get entity registry to find light entities
    entity_reg = entity_registry.async_get(hass)

    _LOGGER.debug(area_list)

    # Iterate over each area and group lights
    for area in area_list:
        # Find all lights in the current area
        light_entities = [
            entry.entity_id
            for entry in entity_reg.entities.values()
            if entry.domain == LIGHT_DOMAIN and entry.area_id == area.id
        ]

        if light_entities:
            # Create group name based on area name
            group_name = f"light_group_{area.name.replace(' ', '_').lower()}"
            group_entity_id = f"{GROUP_DOMAIN}.{group_name}"

            # Dynamically create the light group
            await hass.services.async_call(
                GROUP_DOMAIN,
                "set",
                {
                    "object_id": group_name,
                    "name": f"{area.name} Light Group",
                    "entities": light_entities,
                },
                blocking=True,
            )

            # Log created group
            # hass.components.persistent_notification.create(
            #    f"Created light group for {area.name}: {group_entity_id}",
            #    title="Area Light Groups",
            # )
