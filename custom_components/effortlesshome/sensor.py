"""Platform for sensor integration."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
)

import logging

from .const import DOMAIN

from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers import entity_registry

from .humidity import HumiditySensor
from .illuminance import IlluminanceSensor
from .temperature import TemperatureSensor
from .auto_area import AutoArea

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

    add_entities([AlarmIDSensor()])
    add_entities([AlarmCreateMessageSensor()])
    add_entities([AlarmOwnerIDSensor()])
    add_entities([AlarmStatusSensor()])
    add_entities([AlarmLastEventSensor()])
    add_entities([AverageHumiditySensor()])
    add_entities([AverageTemperatureSensor()])

    #areas = hass.helpers.area_registry.async_get()

    # Loop over each area and find associated motion sensors
    #for area_id, area in areas.areas.items():
    #    auto_area = AutoArea(hass=hass, areaid=area_id)
    #    add_entities(
    #        [
                # IlluminanceSensor(hass, auto_area),
                # TemperatureSensor(hass, auto_area),
                # HumiditySensor(hass, auto_area),
    #        ]
    #    )


class AlarmIDSensor(SensorEntity):
    """Representation of a sensor."""

    def __init__(self) -> None:
        """Initialize the sensor."""
        self._state = ""

    @property
    def unique_id(self) -> str:
        """Return the unique ID of the sensor."""
        return self.name

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return "Alarm ID Sensor"

    @property
    def icon(self) -> str:
        """Return the icon of the sensor."""
        return "mdi:alarm-light"

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    def update(self) -> None:
        """
        Fetch new state data for the sensor.

        This is the only method that should fetch new data for Home Assistant.
        """

        try:
            self._state = self.hass.data[DOMAIN]["alarm_id"]
        except:
            self._state = ""


class AlarmCreateMessageSensor(SensorEntity):
    """Representation of a sensor."""

    def __init__(self) -> None:
        """Initialize the sensor."""
        self._state = ""

    @property
    def unique_id(self) -> str:
        """Return the unique ID of the sensor."""
        return self.name

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return "Alarm ID Sensor"

    @property
    def icon(self) -> str:
        """Return the icon of the sensor."""
        return "mdi:alarm-light"

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    def update(self) -> None:
        """
        Fetch new state data for the sensor.

        This is the only method that should fetch new data for Home Assistant.
        """

        try:
            self._state = self.hass.data[DOMAIN]["alarmcreatemessage"]
        except:
            self._state = ""


class AlarmOwnerIDSensor(SensorEntity):
    """Representation of a sensor."""

    def __init__(self) -> None:
        """Initialize the sensor."""
        self._state = ""

    @property
    def unique_id(self) -> str:
        """Return the unique ID of the sensor."""
        return self.name

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return "Alarm Owner ID Sensor"

    @property
    def icon(self) -> str:
        """Return the icon of the sensor."""
        return "mdi:alarm-light"

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    def update(self) -> None:
        """
        Fetch new state data for the sensor.

        This is the only method that should fetch new data for Home Assistant.
        """

        try:
            self._state = self.hass.data[DOMAIN]["alarmownerid"]
        except:
            self._state = ""


class AlarmStatusSensor(SensorEntity):
    """Representation of a sensor."""

    def __init__(self) -> None:
        """Initialize the sensor."""
        self._state = ""

    @property
    def unique_id(self) -> str:
        """Return the unique ID of the sensor."""
        return self.name

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return "Alarm Status Sensor"

    @property
    def icon(self) -> str:
        """Return the icon of the sensor."""
        return "mdi:alarm-light"

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    def update(self) -> None:
        """
        Fetch new state data for the sensor.

        This is the only method that should fetch new data for Home Assistant.
        """
        try:
            self._state = self.hass.data[DOMAIN]["alarmstatus"]
        except:
            self._state = ""


class AlarmLastEventSensor(SensorEntity):
    """Representation of a sensor."""

    def __init__(self) -> None:
        """Initialize the sensor."""
        self._state = ""

    @property
    def unique_id(self) -> str:
        """Return the unique ID of the sensor."""
        return self.name

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return "Alarm Last Event Sensor"

    @property
    def icon(self) -> str:
        """Return the icon of the sensor."""
        return "mdi:alarm-light"

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    def update(self) -> None:
        """
        Fetch new state data for the sensor.

        This is the only method that should fetch new data for Home Assistant.
        """

        try:
            self._state = self.hass.data[DOMAIN]["alarmlasteventtype"]
        except:
            self._state = ""


class AverageHumiditySensor(SensorEntity):
    """Representation of a sensor."""

    def __init__(self) -> None:
        """Initialize the sensor."""
        self._state = ""

    @property
    def unique_id(self) -> str:
        """Return the unique ID of the sensor."""
        return self.name

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return "Average Humidity Sensor"

    @property
    def icon(self) -> str:
        """Return the icon of the sensor."""
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

        group_entity_id = "group.humidity_sensors_group"

        # Ensure the group exists
        group_state = self.hass.states.get(group_entity_id)
        if not group_state:
            _LOGGER.debug(f"Group {group_entity_id} not found.")
            return

        # Get all entities in the group
        group_entities = group_state.attributes.get("entity_id", [])
        
        # Get all entities in the group
        group_entities = group_state.attributes.get("entity_id", [])

        numeric_values = []
        for entity_id in group_entities:
            entity_state = self.hass.states.get(entity_id)
            if entity_state:
                current_state = entity_state.state
                try:
                    # Attempt to convert the state to a float
                    numeric_value = float(current_state)
                    numeric_values.append(numeric_value)
                    _LOGGER.debug(f"Entity {entity_id} has a numeric state of {numeric_value}")
                except ValueError:
                    # Non-numeric state, skip
                    _LOGGER.debug(f"Entity {entity_id} state '{current_state}' is not numeric.")
            else:
                self.hass.logger.warning(f"Entity {entity_id} has no state available.")

        # Calculate the average if we have numeric values
        if numeric_values:
            average_value = sum(numeric_values) / len(numeric_values)
            self._state = average_value
            _LOGGER.debug(f"Average numeric state for group {group_entity_id}: {average_value}")
        else:
            _LOGGER.debug(f"No numeric values found for entities in group {group_entity_id}.")
            self._state = -1

class AverageTemperatureSensor(SensorEntity):
    """Representation of a sensor."""

    def __init__(self) -> None:
        """Initialize the sensor."""
        self._state = ""

    @property
    def unique_id(self) -> str:
        """Return the unique ID of the sensor."""
        return self.name

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return "Average Temperature Sensor"

    @property
    def icon(self) -> str:
        """Return the icon of the sensor."""
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

        group_entity_id = "group.temperature_sensors_group"

        # Ensure the group exists
        group_state = self.hass.states.get(group_entity_id)
        if not group_state:
            _LOGGER.debug(f"Group {group_entity_id} not found.")
            return

        # Get all entities in the group
        group_entities = group_state.attributes.get("entity_id", [])

        numeric_values = []
        for entity_id in group_entities:
            entity_state = self.hass.states.get(entity_id)
            if entity_state:
                current_state = entity_state.state
                try:
                    # Attempt to convert the state to a float
                    numeric_value = float(current_state)
                    numeric_values.append(numeric_value)
                    _LOGGER.debug(f"Entity {entity_id} has a numeric state of {numeric_value}")
                except ValueError:
                    # Non-numeric state, skip
                    _LOGGER.debug(f"Entity {entity_id} state '{current_state}' is not numeric.")
            else:
                self.hass.logger.warning(f"Entity {entity_id} has no state available.")

        # Calculate the average if we have numeric values
        if numeric_values:
            average_value = sum(numeric_values) / len(numeric_values)
            self._state = average_value
            _LOGGER.debug(f"Average numeric state for group {group_entity_id}: {average_value}")
        else:
            _LOGGER.debug(f"No numeric values found for entities in group {group_entity_id}.")
            self._state = -1