from __future__ import annotations

import logging

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)
from typing import TYPE_CHECKING

# from homeassistant.components.webhook import async_unregister

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant


class SecurityAlarmWebhook:
    """Class to handle Security Alarm Webhook functionality."""

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize the EffortlessHome theme."""
        self.hass = hass

    async def async_setup_webhook(self) -> bool:
        _LOGGER.debug("Setting up Security Alarm Webhook")

        self.hass.components.webhook.async_register(
            DOMAIN, "Security Alarm Webhook", "alarmwebhook", self.handle_ehwebhook
        )

        return True

    async def handle_ehwebhook(self, hass: HomeAssistant, webhook_id, request) -> None:
        """Handle incoming webhook requests."""
        _LOGGER.debug("In security alarm handle webhook")

        if request.method not in ["POST", "PUT"]:
            return  # Ignore methods other than POST or PUT

        # Extract the JSON payload from the request
        try:
            responsejson = await request.json()

            _LOGGER.debug("webhookjson:" + str(responsejson))

            alarmstate = hass.data[DOMAIN]["alarm_id"]

            if alarmstate is not None and alarmstate != "":
                alarmstatus = hass.data[DOMAIN]["alarmstatus"]

                if alarmstatus == "ACTIVE":
                    latestalarmid = hass.data[DOMAIN]["alarm_id"]

                    for event in responsejson:
                        alarm_id = event["meta"]["alarm_id"]

                        if alarm_id == latestalarmid:
                            event_type = event["event_type"]
                            hass.states.async_set(
                                "effortlesshome.alarmlasteventtype", event_type
                            )

                            if event_type == "alarm.closed":
                                hass.states.async_set(
                                    "effortlesshome.alarmstatus", "Closed"
                                )
                            elif event_type == "alarm.status.canceled":
                                hass.states.async_set(
                                    "effortlesshome.alarmstatus", "Canceled"
                                )

        except ValueError:
            _LOGGER.debug("webhookjson error:" + str(ValueError))
            return  # Handle invalid JSON


async def async_remove(self) -> None:
    """Unregister the webhook when the integration is removed."""
    async_unregister(self.hass, "alarmwebhook")  # type: ignore # noqa: F821
