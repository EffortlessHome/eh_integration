from homeassistant.components.group import DOMAIN as GROUP_DOMAIN
from homeassistant.helpers.entity import Entity
from homeassistant.components.input_boolean import InputBoolean
from homeassistant.components.input_text import InputText
from homeassistant.components.text import TextEntity

import logging
from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.helpers.template import Template

_LOGGER = logging.getLogger(__name__)

from .const import CONF_USERNAME
from .const import CONF_SYSTEMID
from .const import DOMAIN

class DeviceClassGroupSync:
    """Custom integration class to sync devices by device_class into a group."""

    def __init__(self, hass, group_name, device_class):
        """Initialize the class with the Home Assistant instance."""
        self.hass = hass
        self.group_name = group_name
        self.device_class = device_class

    async def find_and_sync_devices(self):
        """Find all devices by device_class and sync them into a group."""
        # Get all states from Home Assistant
        all_entities = self.hass.states.async_all()

        # Filter entities by device_class
        matching_entities = [
            entity.entity_id
            for entity in all_entities
            if entity.attributes.get('device_class') == self.device_class
        ]      

        if matching_entities:
            _LOGGER.debug("Device Class Entities " + str(matching_entities))

            # Use the group.set service to create or update the group
           # await self.hass.services.async_call(
           #     'group', 'set',
           #     {
           #         'object_id': self.group_name,  # Group name (without the "group." prefix)
           #         'name': f"Devices with {self.device_class}",
           #         'entities': matching_entities,
           #         'visible': True
           #     }
           # )
            print(f"Synced {len(matching_entities)} entities to group {self.group_name}")
        else:
            print(f"No entities found with device_class '{self.device_class}'")

# Example usage inside your custom integration
async def async_setup_devicegroup(hass, config):
    """Set up the integration."""
    # Initialize the group sync for 'temperature' device_class
    device_sync = DeviceClassGroupSync(hass, "heat_sensors_group", "heat")
    await device_sync.find_and_sync_devices()

    # Initialize the group sync for 'motion' device_class
    motion_sync = DeviceClassGroupSync(hass, "motion_sensors_group", "motion")
    await motion_sync.find_and_sync_devices()

    # Initialize the group sync for 'smoke' device_class
    smokealarm_sync = DeviceClassGroupSync(hass, "smokealarm_sensors_group", "smoke")
    await smokealarm_sync.find_and_sync_devices()

    # Initialize the group sync for 'carbon_monoxide' device_class
    carbon_monoxide_sync = DeviceClassGroupSync(hass, "carbon_monoxide_sensors_group", "carbon_monoxide")
    await carbon_monoxide_sync.find_and_sync_devices()

    # Initialize the group sync for 'door' device_class
    door_sync = DeviceClassGroupSync(hass, "door_sensors_group", "door")
    await door_sync.find_and_sync_devices()

    # Initialize the group sync for 'window' device_class
    window_sync = DeviceClassGroupSync(hass, "window_sensors_group", "window")
    await window_sync.find_and_sync_devices()

    # Initialize the group sync for 'safety' device_class
    safety_sync = DeviceClassGroupSync(hass, "safety_sensors_group", "safety")
    await safety_sync.find_and_sync_devices()

    return True