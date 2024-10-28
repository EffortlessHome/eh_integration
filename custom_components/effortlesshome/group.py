from __future__ import annotations  # noqa: D100, EXE002

import logging
from typing import TYPE_CHECKING

from homeassistant.components.group import entity
from homeassistant.components.group import GroupEntity
from homeassistant.helpers import area_registry, device_registry, entity_registry
from homeassistant.helpers.entity_component import async_update_entity

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback
    from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

_LOGGER = logging.getLogger(__name__)


def setup_platform(
    hass: HomeAssistant,
    config: ConfigType,  # noqa: ARG001
    add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Set up the platform."""
    # We only want this platform to be set up via discovery.
    if discovery_info is None:
        return


class group(GroupEntity):  # noqa: N801
    """Representation of a group of lights by area."""

    def __init__(self, hass, area_name) -> None:  # noqa: ANN001
        """Initialize an area light group."""
        self.hass = hass
        self.area_name = area_name

    async def async_added_to_hass(self) -> None:
        """Run when the entity is added to hass."""
        # Load the lights for the specified area
        # await self._load_lights_from_area()
