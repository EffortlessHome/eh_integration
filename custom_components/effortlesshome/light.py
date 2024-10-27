from __future__ import annotations  # noqa: D100, EXE002

import logging
from typing import TYPE_CHECKING

from homeassistant.components.light import LightEntity
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

    arearegistry = area_registry.async_get(hass)

    for area in arearegistry.areas.values():
        add_entities([light(hass, area.name)])


class light(LightEntity):  # noqa: N801
    """Representation of a group of lights by area."""

    def __init__(self, hass, area_name) -> None:  # noqa: ANN001
        """Initialize an area light group."""
        self.hass = hass
        self.area_name = area_name
        self._lights = []  # This will hold the entity_ids of the lights in the area
        self._is_on = False
        self._brightness = None

    async def async_added_to_hass(self) -> None:
        """Run when the entity is added to hass."""
        # Load the lights for the specified area
        await self._load_lights_from_area()

    async def _load_lights_from_area(self) -> None:
        """Load all light entities assigned to the specified area."""
        # Get the area registry, device registry, and entity registry
        arearegistry = area_registry.async_get(self.hass)

        deviceregistry = device_registry.async_get(self.hass)

        entityregistry = entity_registry.async_get(self.hass)

        # Find the area by its name
        area = next(
            (a for a in arearegistry.areas.values() if a.name == self.area_name), None
        )

        if area is None:
            _LOGGER.error(f"Area '{self.area_name}' not found.")  # noqa: G004
            return

        area_id = area.id

        # Find all devices in the area
        devices_in_area = [
            device
            for device in deviceregistry.devices.values()
            if device.area_id == area_id
        ]

        # Find all light entities related to the devices in the area
        for device in devices_in_area:
            # Get all entities for the device
            device_entities = [
                entity
                for entity in entityregistry.entities.values()
                if entity.device_id == device.id and entity.domain == "light"
            ]
            for entity in device_entities:
                self._lights.append(entity.entity_id)

        _LOGGER.info(f"Lights found for area '{self.area_name}': {self._lights}")  # noqa: G004

    @property
    def name(self) -> str:
        """Return the name of the light group."""
        return f"{self.area_name} Area Light Group"

    @property
    def is_on(self):  # noqa: ANN201
        """Return true if any light in the group is on."""
        return self._is_on

    @property
    def unique_id(self) -> str:
        """Return the unique ID of the sensor."""
        return self.name

    @property
    def brightness(self):  # noqa: ANN201
        """Return the brightness of the group."""
        return self._brightness

    async def async_turn_on(self, **kwargs):
        """Turn on all lights in the group, with optional brightness control."""
        if not self._lights:
            _LOGGER.error("No lights found in the group.")
            return

        brightness = kwargs.get("brightness", None)

        # Turn on all lights with the specified brightness (if provided)
        for light_entity_id in self._lights:
            service_data = {"entity_id": light_entity_id}
            if brightness:
                service_data["brightness"] = brightness
            await self.hass.services.async_call("light", "turn_on", service_data)

        self._is_on = True
        if brightness:
            self._brightness = brightness

    async def async_turn_off(self, **kwargs) -> None:  # noqa: ANN003
        """Turn off all lights in the group."""
        if not self._lights:
            _LOGGER.debug("No lights found in the group.")
            return

        for light_entity_id in self._lights:
            await self.hass.services.async_call(
                "light", "turn_off", {"entity_id": light_entity_id, **kwargs}
            )
        self._is_on = False

    async def async_update(self):
        """Fetch the state of all lights in the group and determine if any are on, and get brightness."""
        if not self._lights:
            return

        total_brightness = 0
        brightness_count = 0

        # Update the state of the group based on individual light states
        for light_entity_id in self._lights:
            await async_update_entity(self.hass, light_entity_id)
            state = self.hass.states.get(light_entity_id)

            if state and state.state == "on":
                self._is_on = True
                light_brightness = state.attributes.get("brightness")
                if light_brightness:
                    total_brightness += light_brightness
                    brightness_count += 1
            else:
                self._is_on = False

        # Calculate average brightness for the group if there are lights with brightness
        if brightness_count > 0:
            self._brightness = total_brightness // brightness_count
        else:
            self._brightness = None
