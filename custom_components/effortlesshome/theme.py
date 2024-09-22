from homeassistant.helpers.entity import Entity
from homeassistant.components.input_boolean import InputBoolean
from homeassistant.components.input_text import InputText
import logging
from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.helpers.template import Template
from homeassistant.core import HomeAssistant, asyncio

from .const import CONF_USERNAME
from .const import CONF_SYSTEMID
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

class effortlesshomeTheme:
    """Class to represent the EffortlessHome theme."""

    def __init__(self, hass: HomeAssistant):
        """Initialize the EffortlessHome theme."""
        self.hass = hass
        self.theme_name = "EffortlessHome"
        self.theme_data = {
            "accent-color": "orange",
            "modes": {
                "light": {
                    "secondary-text-color": "slategray",
                    "primary-color": "black",
                    "text-primary-color": "white",
                    "lovelace-background": 'left no-repeat url("/local/ehvirtualbackground.png")',
                },
                "dark": {
                    "secondary-text-color": "white",
                    "primary-color": "slategray",
                    "text-primary-color": "white",
                    "lovelace-background": 'left no-repeat url("/local/ehvirtualbackground.png")',
                },
            },
        }

    def apply_theme(self):
        """Apply the theme to Home Assistant."""
        _LOGGER.info(f"Applying {self.theme_name} theme")
        self.hass.services.call(
            "frontend", "set_theme", {"name": self.theme_name, "data": self.theme_data}
        )

    async def async_setup(self):
        """Setup the EffortlessHome theme during integration setup."""
        _LOGGER.info(f"Setting up {self.theme_name} theme")
        # Register the theme service with Home Assistant
        self.hass.services.async_register(
            "effortlesshome", "apply_theme", self.apply_theme
        )