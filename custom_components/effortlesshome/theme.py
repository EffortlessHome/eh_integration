import logging

from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)


class EHTheme:
    """Class to represent the EffortlessHome theme."""

    def __init__(self, hass: HomeAssistant) -> None:
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

    def apply_theme(self) -> None:
        """Apply the theme to Home Assistant."""
        _LOGGER.info(f"Applying {self.theme_name} theme")
        self.hass.services.call(
            "frontend", "set_theme", {"name": self.theme_name, "data": self.theme_data}
        )

    async def async_setup_theme(self) -> None:
        """Setup the EffortlessHome theme during integration setup."""
        _LOGGER.info(f"Setting up {self.theme_name} theme")
        # Register the theme service with Home Assistant
        self.hass.services.async_register(
            "effortlesshome", "apply_theme", self.apply_theme
        )
