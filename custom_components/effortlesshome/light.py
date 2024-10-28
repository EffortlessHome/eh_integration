from __future__ import annotations  # noqa: D100, EXE002

import logging
from typing import TYPE_CHECKING

from homeassistant.components.light import LightEntity
from homeassistant.helpers import area_registry, device_registry, entity_registry
from homeassistant.helpers.entity_component import async_update_entity

from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
from functools import cached_property
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.components.group.light import LightGroup
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.components.light import DOMAIN as LIGHT_DOMAIN

from .auto_area import AutoArea
from .const import (
    CONFIG_EXCLUDED_LIGHT_ENTITIES,
    DOMAIN,
    EXCLUDED_DOMAINS,
    LIGHT_GROUP_ENTITY_PREFIX,
    LIGHT_GROUP_PREFIX,
)

from .ha_helpers import get_all_entities

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

    areas = area_registry.async_get(hass)

    # Initialize a list for all light entity IDs across areas
    all_light_entity_ids = []

    # Loop over each area to find associated light entities
    for area_id, area in areas.areas.items():
        auto_area = AutoArea(hass=hass, areaid=area_id)

        light_entity_ids = [
            entity.entity_id
            for entity in get_all_entities(
                auto_area.entity_registry,
                auto_area.device_registry,
                auto_area.area_id,
                [LIGHT_DOMAIN],
            )
        ]

        if not light_entity_ids:
            _LOGGER.info(
                "%s: No lights found in area. Not creating light group.",
                auto_area.area_name,
            )
        else:
            add_entities([AutoLightGroup(hass, auto_area, entity_ids=light_entity_ids)])
            all_light_entity_ids.extend(light_entity_ids)  # Extend instead of append

    # Add an AllLightGroup with all light entities across areas
    add_entities([AllLightGroup(hass, entity_ids=all_light_entity_ids)])


class AutoLightGroup(LightGroup):
    """Cover group with area covers."""

    def __init__(self, hass, auto_area: AutoArea, entity_ids: list[str]) -> None:
        """Initialize cover group."""
        self.hass = hass
        self.auto_area = auto_area
        self._name_prefix = LIGHT_GROUP_PREFIX
        self._prefix = LIGHT_GROUP_ENTITY_PREFIX
        self.entity_ids: list[str] = entity_ids

        LightGroup.__init__(
            self,
            unique_id=self._attr_unique_id,
            name=None,
            entity_ids=self.entity_ids,
            mode=None,
        )
        _LOGGER.info(
            "%s (%s): Initialized light group. Entities: %s",
            self.auto_area.area_name,
            self.device_class,
            self.entity_ids,
        )

    @cached_property
    def name(self):
        """Name of this entity."""
        return f"{self._name_prefix}{self.auto_area.area_name}"

    @cached_property
    def device_info(self) -> DeviceInfo:
        """Information about this device."""
        return self.auto_area.device_info

    @cached_property
    def unique_id(self) -> str | None:
        """Return a unique ID."""
        return f"{self.auto_area.area_id}_light_group"


class AllLightGroup(LightGroup):
    """Cover group with area covers."""

    def __init__(self, hass, entity_ids: list[str]) -> None:
        """Initialize cover group."""
        self.hass = hass
        self.entity_ids: list[str] = entity_ids

        LightGroup.__init__(
            self,
            unique_id=self._attr_unique_id,
            name=None,
            entity_ids=self.entity_ids,
            mode=None,
        )

    @cached_property
    def name(self):
        """Name of this entity."""
        return "all_light_group"

    # @cached_property
    # def device_info(self) -> DeviceInfo:
    #    """Information about this device."""
    #    return self.auto_area.device_info

    @cached_property
    def unique_id(self) -> str | None:
        """Return a unique ID."""
        return "all_light_group"
