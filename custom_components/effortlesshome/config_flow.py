"""Config flow for the effortlesshome component."""

import logging
import secrets

import aiohttp
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback

from .const import (
    CONF_SYSTEMID,
    CONF_USERNAME,
    DOMAIN,
    EH_INITIALIZE_API,
    PLATFORMS,
)

_LOGGER: logging.Logger = logging.getLogger(__package__)


class effortlesshomeConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for effortlesshome."""

    VERSION = "1.0.0"
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_POLL

    def __init__(self) -> None:
        """Initialize."""
        self._errors = {}

    async def async_step_user(self, user_input=None):
        """Handle a flow initialized by the user."""
        # Only a single instance of the integration
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")

        id = secrets.token_hex(6)

        await self.async_set_unique_id(id)
        self._abort_if_unique_id_configured(updates=user_input)

        if user_input is not None:
            valid = await self.initialize_eh(
                user_input[CONF_USERNAME], user_input[CONF_SYSTEMID]
            )

            if valid:
                # TODO: add entries for the retrieved data
                self.async_create_entry(
                    title=user_input[CONF_USERNAME], data=user_input[CONF_USERNAME]
                )

                self.async_create_entry(
                    title=user_input[CONF_SYSTEMID], data=user_input[CONF_SYSTEMID]
                )

                return self.async_create_entry(
                    title=user_input[CONF_USERNAME], data=user_input
                )

            self._errors["base"] = "Invalid Email. Please check and try again."

            return await self._show_config_form(user_input)

        return await self._show_config_form(user_input)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return ehOptionsFlowHandler(config_entry)

    async def _show_config_form(self, user_input):  # pylint: disable=unused-argument
        """Show the configuration form to edit location data."""
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_USERNAME): str,
                    vol.Required(CONF_SYSTEMID): str,
                }
            ),
            errors=self._errors,
        )

    async def initialize_eh(self, username, systemid) -> bool:
        url = EH_INITIALIZE_API + username + "/" + systemid
        headers = {
            "Accept": "application/json, text/html",
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json={}) as response:
                _LOGGER.debug("API response status: %s", response.status)
                _LOGGER.debug("API response headers: %s", response.headers)
                content = await response.text()
                _LOGGER.debug("API response content: %s", content)

                if response.status == 200:
                    return content is not None
                return False


class ehOptionsFlowHandler(config_entries.OptionsFlow):
    """Config flow options handler for effortlesshome."""

    def __init__(self, config_entry) -> None:
        """Initialize HACS options flow."""
        self.config_entry = config_entry
        self.options = dict(config_entry.options)

    async def async_step_init(self, user_input=None):  # pylint: disable=unused-argument  # noqa: ANN001, ANN201, ARG002
        """Manage the options."""
        return await self.async_step_user()

    async def async_step_user(self, user_input=None):
        """Handle a flow initialized by the user."""
        if user_input is not None:
            self.options.update(user_input)
            return await self._update_options()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(x, default=self.options.get(x, True)): bool
                    for x in sorted(PLATFORMS)
                }
            ),
        )

    async def _update_options(self):
        """Update config entry options."""
        return self.async_create_entry(
            title=self.config_entry.data.get(CONF_USERNAME), data=self.options
        )
