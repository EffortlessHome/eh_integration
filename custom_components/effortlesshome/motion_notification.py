"""Sleep mode switch."""

from __future__ import annotations
from functools import cached_property

from homeassistant.components.switch import (
    SwitchEntity,
    SwitchDeviceClass,
)
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.typing import UndefinedType

from .auto_area import AutoArea
from .const import SLEEP_MODE_SWITCH_PREFIX
import logging

_LOGGER: logging.Logger = logging.getLogger(__package__)


class MotionNotificationsSwitch(SwitchEntity):
    """Set up a motion notifications switch."""

    _attr_should_poll = False

    def __init__(self, auto_area: AutoArea) -> None:
        """Initialize motion notifications switch."""
        self.auto_area = auto_area
        self._is_on: bool = True
        _LOGGER.info(
            "%s: Initialized motion notifications switch (%s)",
            self.auto_area.area_name,
            self.name,
        )

    @cached_property
    def name(self) -> str | UndefinedType | None:
        """Return the name of the entity."""
        return "switch.motion_notifications"

    @cached_property
    def device_info(self) -> DeviceInfo:
        """Information about this device."""
        return self.auto_area.device_info

    @cached_property
    def device_class(self) -> SwitchDeviceClass | None:
        """Return device class."""
        return SwitchDeviceClass.SWITCH

    @property
    def is_on(self) -> bool | None:
        """Return the state of the switch."""
        return self._is_on

    def turn_on(self, **kwargs) -> None:
        """Turn on switch."""
        _LOGGER.info("%s: Motion notifications turned on", self.auto_area.area_name)
        self._is_on = True
        self.schedule_update_ha_state()

    def turn_off(self, **kwargs):
        """Turn off switch."""
        _LOGGER.info("%s: Motion notifications turned off", self.auto_area.area_name)
        self._is_on = False
        self.schedule_update_ha_state()