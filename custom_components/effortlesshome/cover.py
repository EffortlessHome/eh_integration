"""Cover group."""

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

from homeassistant.helpers.entity import Entity

from .const import CONFIG_IS_SLEEPING_AREA, DOMAIN
from .presence_lock import PresenceLockSwitch
from .sleep_mode import SleepModeSwitch

from .auto_area import AutoArea

from functools import cached_property
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.components.group.cover import CoverGroup
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.components.cover import (
    CoverDeviceClass,
    DEVICE_CLASSES as COVER_DEVICE_CLASSES,
)

from .auto_area import AutoArea
from .const import (
    COVER_GROUP_ENTITY_PREFIX,
    COVER_GROUP_PREFIX,
    DOMAIN,
)

import logging

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

    # Loop over each area and find associated motion sensors
    for area_id, area in areas.areas.items():
        auto_area = AutoArea(hass=hass, areaid=area_id)

        cover_entity_ids: list[str] = auto_area.get_area_entity_ids(
            COVER_DEVICE_CLASSES
        )

        if not cover_entity_ids:
            _LOGGER.info(
                "%s: No covers found in area. Not creating cover group.",
                auto_area.area_name,
            )
        else:
            add_entities([AutoCoverGroup(hass, auto_area, entity_ids=cover_entity_ids)])


class AutoCoverGroup(CoverGroup):
    """Cover group with area covers."""

    def __init__(self, hass, auto_area: AutoArea, entity_ids: list[str]) -> None:
        """Initialize cover group."""
        self.hass = hass
        self.auto_area = auto_area
        self._device_class = CoverDeviceClass.BLIND
        self._name_prefix = COVER_GROUP_PREFIX
        self._prefix = COVER_GROUP_ENTITY_PREFIX
        self.entity_ids: list[str] = entity_ids

        CoverGroup.__init__(
            self,
            entities=self.entity_ids,
            name=None,
            unique_id=self._attr_unique_id,
        )
        _LOGGER.info(
            "%s (%s): Initialized cover group. Entities: %s",
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
        return f"{self.auto_area.area_id}_cover_group"
