"""Platform for sensor integration."""

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
    hass: HomeAssistant,
    config: ConfigType,
    add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Set up the sensor platform."""
    # We only want this platform to be set up via discovery.
    if discovery_info is None:
        return

    add_entities([binarymedalertsensor()])
    add_entities([sleepingsensor()])
    add_entities([someonehomesensor()])
    add_entities([renteroccupiedsensor()])
    add_entities([motiongroup()])
    add_entities([smokegroup()])
    add_entities([moisturegroup()])
    add_entities([carbonmonoxidegroup()])
    add_entities([doorgroup()])
    add_entities([windowgroup()])
    add_entities([presencegroup()])
    add_entities([safetygroup()])
    add_entities([humiditygroup()])
    add_entities([runninggroup()])
    add_entities([temperaturegroup()])


class runninggroup(BinarySensorEntity):
    """Representation of a sensor."""

    device_class = "running"

    def __init__(self) -> None:
        """Initialize the sensor."""
        self._state = None

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return "Running Group Sensor"

    @property
    def icon(self) -> str:
        return "mdi:washing-machine"

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    def update(self) -> None:
        """
        Fetch new state data for the sensor.

        This is the only method that should fetch new data for Home Assistant.
        """
        entity_id = "group.running_sensors_group"
        sensor_state = self.hass.states.get(entity_id)

        self._state = sensor_state.state


class temperaturegroup(BinarySensorEntity):
    """Representation of a sensor."""

    device_class = "temperature"

    def __init__(self) -> None:
        """Initialize the sensor."""
        self._state = None

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return "Temperature Group Sensor"

    @property
    def icon(self) -> str:
        return "mdi:thermometer"

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    def update(self) -> None:
        """
        Fetch new state data for the sensor.

        This is the only method that should fetch new data for Home Assistant.
        """
        entity_id = "group.temperature_sensors_group"
        sensor_state = self.hass.states.get(entity_id)

        self._state = sensor_state.state


class humiditygroup(BinarySensorEntity):
    """Representation of a sensor."""

    device_class = "humidity"

    def __init__(self) -> None:
        """Initialize the sensor."""
        self._state = None

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return "Humidity Group Sensor"

    @property
    def icon(self) -> str:
        return "mdi:water-percent"

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    def update(self) -> None:
        """
        Fetch new state data for the sensor.

        This is the only method that should fetch new data for Home Assistant.
        """
        entity_id = "group.humidity_sensors_group"
        sensor_state = self.hass.states.get(entity_id)

        self._state = sensor_state.state


class presencegroup(BinarySensorEntity):
    """Representation of a sensor."""

    device_class = "presence"

    def __init__(self) -> None:
        """Initialize the sensor."""
        self._state = "Clear"

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return "Presence Group Sensor"

    @property
    def icon(self) -> str:
        return "mdi:motion-sensor"

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    def update(self) -> None:
        """
        Fetch new state data for the sensor.

        This is the only method that should fetch new data for Home Assistant.
        """
        entity_id = "group.presence_sensors_group"
        sensor_state = self.hass.states.get(entity_id)

        self._state = sensor_state.state


class safetygroup(BinarySensorEntity):
    """Representation of a sensor."""

    device_class = "safety"

    def __init__(self) -> None:
        """Initialize the sensor."""
        self._state = "Safe"

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return "Safety Group Sensor"

    @property
    def icon(self) -> str:
        return "mdi:ambulance"

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    def update(self) -> None:
        """
        Fetch new state data for the sensor.

        This is the only method that should fetch new data for Home Assistant.
        """
        entity_id = "group.safety_sensors_group"
        sensor_state = self.hass.states.get(entity_id)

        self._state = sensor_state.state


class windowgroup(BinarySensorEntity):
    """Representation of a sensor."""

    device_class = "window"

    def __init__(self) -> None:
        """Initialize the sensor."""
        self._state = "Closed"

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return "Window Group Sensor"

    @property
    def icon(self) -> str:
        return "mdi:window-closed"

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    def update(self) -> None:
        """
        Fetch new state data for the sensor.

        This is the only method that should fetch new data for Home Assistant.
        """
        entity_id = "group.window_sensors_group"
        sensor_state = self.hass.states.get(entity_id)

        self._state = sensor_state.state


class doorgroup(BinarySensorEntity):
    """Representation of a sensor."""

    device_class = "door"

    def __init__(self) -> None:
        """Initialize the sensor."""
        self._state = "Closed"

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return "Door Group Sensor"

    @property
    def icon(self) -> str:
        return "mdi:door"

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    def update(self) -> None:
        """
        Fetch new state data for the sensor.

        This is the only method that should fetch new data for Home Assistant.
        """
        entity_id = "group.door_sensors_group"
        sensor_state = self.hass.states.get(entity_id)

        self._state = sensor_state.state


class carbonmonoxidegroup(BinarySensorEntity):
    """Representation of a sensor."""

    device_class = "carbon_monoxide"

    def __init__(self) -> None:
        """Initialize the sensor."""
        self._state = "Clear"

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return "Carbon Monoxide Group Sensor"

    @property
    def icon(self) -> str:
        return "mdi:molecule-co"

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    def update(self) -> None:
        """
        Fetch new state data for the sensor.

        This is the only method that should fetch new data for Home Assistant.
        """
        entity_id = "group.carbon_monoxide_sensors_group"
        sensor_state = self.hass.states.get(entity_id)

        self._state = sensor_state.state


class moisturegroup(BinarySensorEntity):
    """Representation of a sensor."""

    device_class = "moisture"

    def __init__(self) -> None:
        """Initialize the sensor."""
        self._state = "Dry"

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return "Moisture Group Sensor"

    @property
    def icon(self) -> str:
        return "mdi:water"

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    def update(self) -> None:
        """
        Fetch new state data for the sensor.

        This is the only method that should fetch new data for Home Assistant.
        """
        entity_id = "group.moisture_sensors_group"
        sensor_state = self.hass.states.get(entity_id)

        self._state = sensor_state.state


class smokegroup(BinarySensorEntity):
    """Representation of a sensor."""

    device_class = "smoke"

    def __init__(self) -> None:
        """Initialize the sensor."""
        self._state = "Clear"

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return "Smoke Group Sensor"

    @property
    def icon(self) -> str:
        return "mdi:smoke-detector"

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    def update(self) -> None:
        """
        Fetch new state data for the sensor.

        This is the only method that should fetch new data for Home Assistant.
        """
        entity_id = "group.smokealarm_sensors_group"
        smoke_sensor_state = self.hass.states.get(entity_id)

        self._state = smoke_sensor_state.state


class motiongroup(BinarySensorEntity):
    """Representation of a sensor."""

    device_class = "motion"

    def __init__(self) -> None:
        """Initialize the sensor."""
        self._state = "Off"

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return "Motion Group Sensor"

    @property
    def icon(self) -> str:
        return "mdi:motion-sensor"

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    def update(self) -> None:
        """
        Fetch new state data for the sensor.

        This is the only method that should fetch new data for Home Assistant.
        """
        # Access the state of the 'binary_sensor.motionsensors' entity
        entity_id = "group.motion_sensors_group"
        motion_sensor_state = self.hass.states.get(entity_id)

        self._state = motion_sensor_state.state


class binarymedalertsensor(BinarySensorEntity):
    """Representation of a sensor."""

    device_class = "safety"

    def __init__(self) -> None:
        """Initialize the sensor."""
        self._state = "Safe"

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return "Medical Alert Sensor"

    @property
    def icon(self) -> str:
        return "mdi:ambulance"

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    def update(self) -> None:
        """
        Fetch new state data for the sensor.

        This is the only method that should fetch new data for Home Assistant.
        """
        self._state = self.hass.data[DOMAIN]["MedicalAlertTriggered"]


class sleepingsensor(BinarySensorEntity):
    """Representation of a sensor."""

    def __init__(self) -> None:
        """Initialize the sensor."""
        self._state = "Off"

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return "Sleeping Sensor"

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def icon(self) -> str:
        return "mdi:chat-sleep"

    def update(self) -> None:
        """
        Fetch new state data for the sensor.

        This is the only method that should fetch new data for Home Assistant.
        """
        self._state = self.hass.data[DOMAIN]["GoodnightRanForDay"]


class someonehomesensor(BinarySensorEntity):
    """Representation of a sensor."""

    def __init__(self) -> None:
        """Initialize the sensor."""
        self._state = "Off"

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return "Someone Home Sensor"

    @property
    def icon(self) -> str:
        return "mdi:account-check"

    @property
    def state(self):
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
            if state.state == "home":
                home = home + 1

        # Access the state of the 'binary_sensor.motionsensors' entity
        entity_id = "group.window_sensors_group"
        motion_sensor_state = self.hass.states.get(entity_id)

        if (
            home > 0
            or motion_sensor_state.state == "On"
            or self.hass.data[DOMAIN]["IsRenterOccupied"] == "On"
        ):
            self._state = "On"
        else:
            self._state = "Off"


class renteroccupiedsensor(BinarySensorEntity):
    """Representation of a sensor."""

    def __init__(self) -> None:
        """Initialize the sensor."""
        self._state = "Off"

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return "Renter Occupied Sensor"

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def icon(self) -> str:
        return "mdi:bag-suitcase"

    def update(self) -> None:
        """
        Fetch new state data for the sensor.

        This is the only method that should fetch new data for Home Assistant.
        """
        self._state = self.hass.data[DOMAIN]["IsRenterOccupied"]
