"""Platform for sensor integration."""  # noqa: EXE002

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from homeassistant.components.binary_sensor import BinarySensorEntity

from .const import DOMAIN

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback
    from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

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


class SecurityMotionGroup(BinarySensorEntity):
    """Representation of a sensor."""

    @property
    def device_class(self) -> str:
        """Return the device_class of the sensor."""
        return "motion"

    def __init__(self) -> None:
        """Initialize the sensor."""
        self._state = "Clear"

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
            sensor_state = "Unknown"


class WindowGroup(BinarySensorEntity):
    """Representation of a sensor."""

    @property
    def device_class(self) -> str:
        """Return the device_class of the sensor."""
        return "window"

    def __init__(self) -> None:
        """Initialize the sensor."""
        self._state = "Closed"

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
            sensor_state = "Unknown"


class DoorGroup(BinarySensorEntity):
    """Representation of a sensor."""

    @property
    def device_class(self) -> str:
        """Return the device_class of the sensor."""
        return "door"

    def __init__(self) -> None:
        """Initialize the sensor."""
        self._state = "Closed"

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
            sensor_state = "Unknown"


class CarbonMonoxideGroup(BinarySensorEntity):
    """Representation of a sensor."""

    @property
    def device_class(self) -> str:
        """Return the device_class of the sensor."""
        return "carbon_monoxide"

    def __init__(self) -> None:
        """Initialize the sensor."""
        self._state = "Clear"

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
            sensor_state = "Unknown"


class MoistureGroup(BinarySensorEntity):
    """Representation of a sensor."""

    @property
    def device_class(self) -> str:
        """Return the device_class of the sensor."""
        return "moisture"

    def __init__(self) -> None:
        """Initialize the sensor."""
        self._state = "Dry"

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
            sensor_state = "Unknown"


class SmokeGroup(BinarySensorEntity):
    """Representation of a sensor."""

    @property
    def device_class(self) -> str:
        """Return the device_class of the sensor."""
        return "smoke"

    def __init__(self) -> None:
        """Initialize the sensor."""
        self._state = "Clear"

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
            sensor_state = "Unknown"


class BinaryMedAlertSensor(BinarySensorEntity):
    """Representation of a sensor."""

    @property
    def device_class(self) -> str:
        """Return the device_class of the sensor."""
        return "safety"

    def __init__(self) -> None:
        """Initialize the sensor."""
        self._state = "Safe"

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
        self._state = "Off"

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
        try:
            self._state = self.hass.data[DOMAIN]["GoodnightRanForDay"]
        except:
            self._state = "Unknown"


class SomeoneHomeSensor(BinarySensorEntity):
    """Representation of a sensor."""

    def __init__(self) -> None:
        """Initialize the sensor."""
        self._state = "Off"

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

        if motion_sensor_state != None:
            self._state = motion_sensor_state.state  # type: ignore  # noqa: PGH003
        else:
            self._state = "Unknown"

        if (
            home > 0
            or motion_sensor_state.state == "On"  # type: ignore  # noqa: PGH003
            or self.hass.data[DOMAIN]["IsRenterOccupied"] == "On"
        ):
            self._state = "On"
        else:
            self._state = "Off"


class RenterOccupiedSensor(BinarySensorEntity):
    """Representation of a sensor."""

    def __init__(self) -> None:
        """Initialize the sensor."""
        self._state = "Off"

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
        try:
            self._state = self.hass.data[DOMAIN]["IsRenterOccupied"]
        except:
            self._state = "Unknown"
