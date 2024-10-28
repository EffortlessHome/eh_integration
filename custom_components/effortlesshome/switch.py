"""Switch platform for integration_blueprint."""

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
from .renter_occupied import RenterOccupiedSwitch
from .motion_notification import MotionNotificationsSwitch
from .medication_tracking import MedicationTrackingSwitch
from .smart_appliance_conversion import SmartApplianceConversionSwitch

from .auto_area import AutoArea


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

    auto_area = AutoArea(hass=hass, areaid="unknown")

    add_entities(
        [
            # PresenceLockSwitch(auto_area),
            SleepModeSwitch(auto_area),
            RenterOccupiedSwitch(auto_area),
            MotionNotificationsSwitch(auto_area),
            MedicationTrackingSwitch(auto_area, "medicationtracking1"),
            MedicationTrackingSwitch(auto_area, "medicationtracking1"),
            MedicationTrackingSwitch(auto_area, "medicationtracking1"),
            SmartApplianceConversionSwitch(auto_area, "SmartAppliance1"),
            SmartApplianceConversionSwitch(auto_area, "SmartAppliance2"),
            SmartApplianceConversionSwitch(auto_area, "SmartAppliance3"),
        ]
    )
