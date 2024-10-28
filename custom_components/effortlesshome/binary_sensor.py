"""Platform for sensor integration."""  # noqa: EXE002

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from homeassistant.components.binary_sensor import BinarySensorEntity

from .const import DOMAIN

from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

from homeassistant.helpers import entity_registry

from .presence import (
    PresenceBinarySensor,
)

from .auto_area import AutoArea


_LOGGER = logging.getLogger(__name__)


def setup_platform(
    hass: HomeAssistant,  # noqa: ARG001
    config: ConfigType,  # noqa: ARG001
    add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Set up the sensor platform."""
    # We only want this platform to be set up via discovery.
    if discovery_info is None:
        return

    add_entities([BinaryMedAlertSensor()])
    add_entities([SleepingSensor()])
    add_entities([SomeoneHomeSensor()])
    add_entities([RenterOccupiedSensor()])
    add_entities([SmokeGroup()])
    add_entities([MoistureGroup()])
    add_entities([CarbonMonoxideGroup()])
    add_entities([DoorGroup()])
    add_entities([WindowGroup()])
    add_entities([SecurityMotionGroup()])
    add_entities([MedicationTrackingSensor("medicationtracking1")])
    add_entities([MedicationTrackingSensor("medicationtracking2")])
    add_entities([MedicationTrackingSensor("medicationtracking3")])
    add_entities([MotionNotifcationSensor()])
    add_entities([SmartApplianceSensor("smartappliance1")])
    add_entities([SmartApplianceSensor("smartappliance2")])
    add_entities([SmartApplianceSensor("smartappliance3")])

    #areas = hass.helpers.area_registry.async_get()

    # Loop over each area and find associated motion sensors
    # for area_id, area in areas.areas.items():
    #    auto_area = AutoArea(hass=hass, areaid=area_id)
    #    add_entities([PresenceBinarySensor(hass, auto_area)])


class SecurityMotionGroup(BinarySensorEntity):
    """Representation of a sensor."""

    @property
    def device_class(self) -> str:
        """Return the device_class of the sensor."""
        return "motion"

    def __init__(self) -> None:
        """Initialize the sensor."""
        self._state = "off"

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return "Security Motion Group Sensor"

    @property
    def unique_id(self) -> str:
        """Return the unique ID of the sensor."""
        return self.name

    @property
    def icon(self) -> str:
        """Return the icon of the sensor."""
        return "mdi:motion-sensor"

    @property
    def state(self):  # noqa: ANN201
        """Return the state of the sensor."""
        return self._state

    def update(self) -> None:
        """
        Fetch new state data for the sensor.

        This is the only method that should fetch new data for Home Assistant.
        """
        entity_id = "group.security_motion_sensors_group"
        sensor_state = self.hass.states.get(entity_id)

        if sensor_state != None:
            self._state = sensor_state.state  # type: ignore  # noqa: PGH003
        else:
            sensor_state = "unknown"


class WindowGroup(BinarySensorEntity):
    """Representation of a sensor."""

    @property
    def device_class(self) -> str:
        """Return the device_class of the sensor."""
        return "window"

    def __init__(self) -> None:
        """Initialize the sensor."""
        self._state = "off"

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return "Window Group Sensor"

    @property
    def unique_id(self) -> str:
        """Return the unique ID of the sensor."""
        return self.name

    @property
    def icon(self) -> str:
        """Return the icon of the sensor."""
        return "mdi:window-closed"

    @property
    def state(self):  # noqa: ANN201
        """Return the state of the sensor."""
        return self._state

    def update(self) -> None:
        """
        Fetch new state data for the sensor.

        This is the only method that should fetch new data for Home Assistant.
        """
        entity_id = "group.window_sensors_group"
        sensor_state = self.hass.states.get(entity_id)

        if sensor_state != None:
            self._state = sensor_state.state  # type: ignore  # noqa: PGH003
        else:
            sensor_state = "unknown"


class DoorGroup(BinarySensorEntity):
    """Representation of a sensor."""

    @property
    def device_class(self) -> str:
        """Return the device_class of the sensor."""
        return "door"

    def __init__(self) -> None:
        """Initialize the sensor."""
        self._state = "off"

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return "Door Group Sensor"

    @property
    def unique_id(self) -> str:
        """Return the unique ID of the sensor."""
        return self.name

    @property
    def icon(self) -> str:
        """Return the icon of the sensor."""
        return "mdi:door"

    @property
    def state(self):  # noqa: ANN201
        """Return the state of the sensor."""
        return self._state

    def update(self) -> None:
        """
        Fetch new state data for the sensor.

        This is the only method that should fetch new data for Home Assistant.
        """
        entity_id = "group.door_sensors_group"
        sensor_state = self.hass.states.get(entity_id)

        if sensor_state != None:
            self._state = sensor_state.state  # type: ignore  # noqa: PGH003
        else:
            sensor_state = "unknown"


class CarbonMonoxideGroup(BinarySensorEntity):
    """Representation of a sensor."""

    @property
    def device_class(self) -> str:
        """Return the device_class of the sensor."""
        return "carbon_monoxide"

    def __init__(self) -> None:
        """Initialize the sensor."""
        self._state = "off"

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return "Carbon Monoxide Group Sensor"

    @property
    def unique_id(self) -> str:
        """Return the unique ID of the sensor."""
        return self.name

    @property
    def icon(self) -> str:
        """Return the icon of the sensor."""
        return "mdi:molecule-co"

    @property
    def state(self):  # noqa: ANN201
        """Return the state of the sensor."""
        return self._state

    def update(self) -> None:
        """
        Fetch new state data for the sensor.

        This is the only method that should fetch new data for Home Assistant.
        """
        entity_id = "group.carbon_monoxide_sensors_group"
        sensor_state = self.hass.states.get(entity_id)

        if sensor_state != None:
            self._state = sensor_state.state  # type: ignore  # noqa: PGH003
        else:
            sensor_state = "unknown"


class MoistureGroup(BinarySensorEntity):
    """Representation of a sensor."""

    @property
    def device_class(self) -> str:
        """Return the device_class of the sensor."""
        return "moisture"

    def __init__(self) -> None:
        """Initialize the sensor."""
        self._state = "off"

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return "Moisture Group Sensor"

    @property
    def unique_id(self) -> str:
        """Return the unique ID of the sensor."""
        return self.name

    @property
    def icon(self) -> str:
        """Return the icon of the sensor."""
        return "mdi:water"

    @property
    def state(self):  # noqa: ANN201
        """Return the state of the sensor."""
        return self._state

    def update(self) -> None:
        """
        Fetch new state data for the sensor.

        This is the only method that should fetch new data for Home Assistant.
        """
        entity_id = "group.moisture_sensors_group"
        sensor_state = self.hass.states.get(entity_id)

        if sensor_state != None:
            self._state = sensor_state.state  # type: ignore  # noqa: PGH003
        else:
            sensor_state = "unknown"


class SmokeGroup(BinarySensorEntity):
    """Representation of a sensor."""

    @property
    def device_class(self) -> str:
        """Return the device_class of the sensor."""
        return "smoke"

    def __init__(self) -> None:
        """Initialize the sensor."""
        self._state = "off"

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return "Smoke Group Sensor"

    @property
    def unique_id(self) -> str:
        """Return the unique ID of the sensor."""
        return self.name

    @property
    def icon(self) -> str:
        """Return the icon of the sensor."""
        return "mdi:smoke-detector"

    @property
    def state(self):  # noqa: ANN201
        """Return the state of the sensor."""
        return self._state

    def update(self) -> None:
        """
        Fetch new state data for the sensor.

        This is the only method that should fetch new data for Home Assistant.
        """
        entity_id = "group.smokealarm_sensors_group"
        sensor_state = self.hass.states.get(entity_id)

        if sensor_state != None:
            self._state = sensor_state.state  # type: ignore  # noqa: PGH003
        else:
            sensor_state = "unknown"


class BinaryMedAlertSensor(BinarySensorEntity):
    """Representation of a sensor."""

    @property
    def device_class(self) -> str:
        """Return the device_class of the sensor."""
        return "safety"

    def __init__(self) -> None:
        """Initialize the sensor."""
        self._state = "off"

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return "Medical Alert Sensor"

    @property
    def unique_id(self) -> str:
        """Return the unique ID of the sensor."""
        return self.name

    @property
    def icon(self) -> str:
        """Return the icon of the sensor."""
        return "mdi:ambulance"

    @property
    def state(self):  # noqa: ANN201
        """Return the state of the sensor."""
        return self._state

    def update(self) -> None:
        """
        Fetch new state data for the sensor.

        This is the only method that should fetch new data for Home Assistant.
        """
        try:
            self._state = self.hass.data[DOMAIN]["MedicalAlertTriggered"]
        except:
            self._state = "Unknown"


class SleepingSensor(BinarySensorEntity):
    """Representation of a sensor."""

    def __init__(self) -> None:
        """Initialize the sensor."""
        self._state = "off"

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return "Sleeping Sensor"

    @property
    def unique_id(self) -> str:
        """Return the unique ID of the sensor."""
        return self.name

    @property
    def state(self):  # noqa: ANN201
        """Return the state of the sensor."""
        return self._state

    @property
    def icon(self) -> str:
        """Return the icon of the sensor."""
        return "mdi:chat-sleep"

    def update(self) -> None:
        """
        Fetch new state data for the sensor.

        This is the only method that should fetch new data for Home Assistant.
        """
        entity_id = "switch.switch_sleep_mode"

        # Get the state of the entity
        state = self.hass.states.get(entity_id)

        if state is not None:
            # Get the state value (e.g., "on" or "off")
            switch_state = state.state
            _LOGGER.info(f"The state of {entity_id} is: {switch_state}")
            self._state = switch_state
        else:
            self._state = "off"


class SomeoneHomeSensor(BinarySensorEntity):
    """Representation of a sensor."""

    def __init__(self) -> None:
        """Initialize the sensor."""
        self._state = "off"

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return "Someone Home Sensor"

    @property
    def unique_id(self) -> str:
        """Return the unique ID of the sensor."""
        return self.name

    @property
    def icon(self) -> str:
        """Return the icon of the sensor."""
        return "mdi:account-check"

    @property
    def state(self):  # noqa: ANN201
        """Return the state of the sensor."""
        return self._state

    def update(self) -> None:
        """
        Fetch new state data for the sensor.

        This is the only method that should fetch new data for Home Assistant.
        """
        home = 0
        for entity_id in self.hass.states.entity_ids("device_tracker"):
            state = self.hass.states.get(entity_id)
            if state.state == "home":  # type: ignore  # noqa: PGH003
                home = home + 1

        entity_id = "group.security_motion_sensors_group"
        motion_sensor_state = self.hass.states.get(entity_id)

        motion_sensor_state_val = "Unknown"

        if motion_sensor_state != None:
            motion_sensor_state_val = motion_sensor_state.state  # type: ignore  # noqa: PGH003

        entity_id = "switch.switch_renter_occupied"

        # Get the state of the entity
        state = self.hass.states.get(entity_id)

        renter_occupied_state = "off"

        if state is not None:
            # Get the state value (e.g., "on" or "off")
            renter_occupied_state = state.state

        if (
            home > 0
            or motion_sensor_state_val.lower() == "on"  # type: ignore  # noqa: PGH003
            or renter_occupied_state.lower() == "on"
        ):
            self._state = "on"
        else:
            self._state = "off"


class RenterOccupiedSensor(BinarySensorEntity):
    """Representation of a sensor."""

    def __init__(self) -> None:
        """Initialize the sensor."""
        self._state = "off"

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return "Renter Occupied Sensor"

    @property
    def unique_id(self) -> str:
        """Return the unique ID of the sensor."""
        return self.name

    @property
    def state(self):  # noqa: ANN201
        """Return the state of the sensor."""
        return self._state

    @property
    def icon(self) -> str:
        """Return the icon of the sensor."""
        return "mdi:bag-suitcase"

    def update(self) -> None:
        """
        Fetch new state data for the sensor.

        This is the only method that should fetch new data for Home Assistant.
        """
        entity_id = "switch.switch_renter_occupied"

        # Get the state of the entity
        state = self.hass.states.get(entity_id)

        if state is not None:
            # Get the state value (e.g., "on" or "off")
            switch_state = state.state
            _LOGGER.info(f"The state of {entity_id} is: {switch_state}")
            self._state = switch_state
        else:
            self._state = "off"


class MedicationTrackingSensor(BinarySensorEntity):
    """Representation of a sensor."""

    def __init__(self, entityname) -> None:
        """Initialize the sensor."""
        self._state = "off"
        self._name = entityname

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return self._name

    @property
    def unique_id(self) -> str:
        """Return the unique ID of the sensor."""
        return self.name

    @property
    def state(self):  # noqa: ANN201
        """Return the state of the sensor."""
        return self._state

    @property
    def icon(self) -> str:
        """Return the icon of the sensor."""
        return "mdi:pill"

    def update(self) -> None:
        """
        Fetch new state data for the sensor.

        This is the only method that should fetch new data for Home Assistant.
        """
        entity_id = f"switch.{self._name}"

        # Get the state of the entity
        state = self.hass.states.get(entity_id)

        if state is not None:
            # Get the state value (e.g., "on" or "off")
            switch_state = state.state
            _LOGGER.info(f"The state of {entity_id} is: {switch_state}")
            self._state = switch_state
        else:
            _LOGGER.info(f"The state of {entity_id} cannnot be determined")
            self._state = "off"


class MotionNotifcationSensor(BinarySensorEntity):
    """Representation of a sensor."""

    def __init__(self) -> None:
        """Initialize the sensor."""
        self._state = "on"

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return "Motion Notification Sensor"

    @property
    def unique_id(self) -> str:
        """Return the unique ID of the sensor."""
        return self.name

    @property
    def state(self):  # noqa: ANN201
        """Return the state of the sensor."""
        return self._state

    @property
    def icon(self) -> str:
        """Return the icon of the sensor."""
        return "mdi:email-check"

    def update(self) -> None:
        """
        Fetch new state data for the sensor.

        This is the only method that should fetch new data for Home Assistant.
        """
        entity_id = "switch.switch_motion_notifications"

        # Get the state of the entity
        state = self.hass.states.get(entity_id)

        if state is not None:
            # Get the state value (e.g., "on" or "off")
            switch_state = state.state
            _LOGGER.info(f"The state of {entity_id} is: {switch_state}")
            self._state = switch_state
        else:
            self._state = "off"

class SmartApplianceSensor(BinarySensorEntity):
    """Representation of a sensor."""

    def __init__(self, entityname) -> None:
        """Initialize the sensor."""
        self._state = "off"
        self._name = entityname

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return self._name
    
    @property
    def device_class(self) -> str:
        """Return the device_class of the sensor."""
        return "running"

    @property
    def unique_id(self) -> str:
        """Return the unique ID of the sensor."""
        return self.name

    @property
    def state(self):  # noqa: ANN201
        """Return the state of the sensor."""
        return self._state

    @property
    def icon(self) -> str:
        """Return the icon of the sensor."""
        return "mdi:washing-machine"

    def update(self) -> None:
        """
        Fetch new state data for the sensor.

        This is the only method that should fetch new data for Home Assistant.
        """
        entity_id = f"switch.{self._name}"

        # Get the state of the entity
        state = self.hass.states.get(entity_id)

        if state is not None:
            # Get the state value (e.g., "on" or "off")
            switch_state = state.state
            _LOGGER.info(f"The state of {entity_id} is: {switch_state}")
            self._state = switch_state
        else:
            _LOGGER.info(f"The state of {entity_id} cannnot be determined")
            self._state = "off"

