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


class effortlesshomeInputBoolean(InputBoolean):
    def __init__(self, hass, name, icon=None):
        self.hass = hass
        self._name = name
        self._state = False
        self._icon = icon

    @property
    def name(self):
        return self._name

    @property
    def state(self):
        return self._state

    @property
    def icon(self):
        return self._icon

    async def async_turn_on(self):
        self._state = True
        self.async_write_ha_state()

    async def async_turn_off(self):
        self._state = False
        self.async_write_ha_state()


class effortlesshomeInputText(TextEntity):
    def __init__(self, hass, name, max_length, mode="text", pattern=None, icon=None, unique_id=None):
        self.hass = hass
        self._name = name
        self._state = ""
        self._max_length = max_length
        self._mode = mode
        self._pattern = pattern
        self._icon = icon
        self._unique_id = unique_id

    @property
    def name(self):
        return self._name

    @property
    def state(self):
        return self._state

    @property
    def icon(self):
        return self._icon
    
    @property
    def unique_id(self):
        return self._unique_id

    async def async_set_value(self, value):
        if len(value) <= self._max_length:
            self._state = value
            self.async_write_ha_state()
        else:
            raise ValueError(f"Input exceeds max length of {self._max_length}")

class TemplateBinarySensor(BinarySensorEntity):
    """Representation of a binary sensor that evaluates a template."""

    def __init__(self, hass, name, value_template, device_class=None):
        """Initialize the binary sensor."""
        self.hass = hass
        self._name = name
        self._template = value_template
        self._device_class = device_class
        self._state = None

    @property
    def name(self):
        """Return the name of the binary sensor."""
        return self._name

    @property
    def is_on(self):
        """Return true if the binary sensor is on."""
        return self._state

    @property
    def device_class(self):
        """Return the class of this sensor."""
        return self._device_class

    async def async_update(self):
        """Update the state by evaluating the template."""
        try:
            self._state = self._template.async_render().lower() == 'true'
        except Exception as ex:
            _LOGGER.error(f"Error rendering template for {self._name}: {ex}")
            self._state = False

async def async_setup_entities(hass, config):
    # Set up input booleans
    booleans = {
        "issomeonehome": effortlesshomeInputBoolean(hass, DOMAIN +".IsSomeoneHome"),
        "ismotionsnoozed": effortlesshomeInputBoolean(hass, DOMAIN +".IsMotionSnoozed"),
        "goodnightranforday": effortlesshomeInputBoolean(hass, DOMAIN +".GoodnightRanForDay"),
        "isrenteroccupied": effortlesshomeInputBoolean(hass, DOMAIN +".IsRenterOccupied", icon="mdi:caravan"),
        "rentershavearrived": effortlesshomeInputBoolean(hass, DOMAIN +".RentersHaveArrived"),
        "internal_medicalalertswitch": effortlesshomeInputBoolean(hass, DOMAIN +".MedicalAlertSwitch"),
        "medicationtracking": effortlesshomeInputBoolean(hass, DOMAIN +".MedicationTracking", icon="mdi:pill-multiple"),
        "activebaseplan": effortlesshomeInputBoolean(hass, DOMAIN +".ActiveBasePlan"),
        "activesecurityplan": effortlesshomeInputBoolean(hass, DOMAIN +".ActiveSecurityPlan"),
        "activemonitoringplan": effortlesshomeInputBoolean(hass, DOMAIN +".ActiveMonitoringPlan"),
        "activemedicalalertplan": effortlesshomeInputBoolean(hass, DOMAIN +".ActiveMedicalAlertPlan"),
    }

    # Set up input texts
    texts = {
        "templockcode_pin": effortlesshomeInputText(hass, DOMAIN +".templockcode_pin", 4, icon="mdi:lock-smart", pattern="^\\d{4}$", unique_id="eh_templockcode_pin"),
        "ownerslockcode_pin": effortlesshomeInputText(hass, DOMAIN +".ownerslockcode_pin", 4, icon="mdi:lock-smart", pattern="^\\d{4}$", unique_id="eh_ownerslockcode_pin"),
        "currentrenterfullname": effortlesshomeInputText(hass, DOMAIN +".CurrentRenterFullName", 100, unique_id="eh_currentrenterfullname"),
        "currentrenterpincode": effortlesshomeInputText(hass, DOMAIN +".CurrentRenterPinCode", 4, unique_id="eh_currentrenterpincode"),
    }

    for entity in booleans.values():
        hass.states.async_set(entity.name, entity.state)

    for entity in texts.values():
        hass.states.async_set(entity.name, entity.state)

    return True




