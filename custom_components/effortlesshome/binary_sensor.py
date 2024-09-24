"""Platform for sensor integration."""
from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
import logging

from .const import DOMAIN

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


class binarymedalertsensor(BinarySensorEntity):
    """Representation of a sensor."""

    device_class = "safety"

    def __init__(self) -> None:
        """Initialize the sensor."""
        self._state = None

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return "Medical Alert Sensor"
    
    @property 
    def icon(self):
        return "mdi:ambulance"

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    def update(self) -> None:
        """Fetch new state data for the sensor.

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
    def icon(self):
        return "mdi:chat-sleep"

    def update(self) -> None:
        """Fetch new state data for the sensor.

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
    def icon(self):
        return "mdi:account-check"

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    def update(self) -> None:
        """Fetch new state data for the sensor.

        This is the only method that should fetch new data for Home Assistant.
        """
        home = 0
        for entity_id in self.hass.states.entity_ids('device_tracker'):
            state = self.hass.states.get(entity_id)
            if state.state == 'home':
                home = home + 1

         # Access the state of the 'binary_sensor.motionsensors' entity
        entity_id = 'binary_sensor.motionsensors'
        motion_sensor_state = self.hass.states.get(entity_id)

        if home > 0 or motion_sensor_state.state == "on" or self.hass.data[DOMAIN]["IsRenterOccupied"] == "On":
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
    def icon(self):
        return "mdi:bag-suitcase"

    def update(self) -> None:
        """Fetch new state data for the sensor.

        This is the only method that should fetch new data for Home Assistant.
        """
        self._state = self.hass.data[DOMAIN]["IsRenterOccupied"]