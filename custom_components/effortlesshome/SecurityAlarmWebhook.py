from __future__ import annotations

from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
import logging

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)
import json
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import Entity
from homeassistant.components.webhook import async_register, async_unregister

class SecurityAlarmWebhook:
    """Class to handle Security Alarm Webhook functionality."""

    def __init__(self, hass: HomeAssistant):
        """Initialize the EffortlessHome theme."""
        self.hass = hass
    
    async def async_setup_webhook(self):
        _LOGGER.debug("Setting up Security Alarm Webhook")

        self.hass.components.webhook.async_register(
            DOMAIN, "Security Alarm Webhook", "alarmwebhook", self.handle_webhook
        )

        return True


    async def handle_webhook(self, hass: HomeAssistant, webhook_id, request):
        """Handle incoming webhook requests."""
        _LOGGER.debug("In security alarm handle webhook")

        if request.method not in ["POST", "PUT"]:
            return  # Ignore methods other than POST or PUT

        # Extract the JSON payload from the request
        try:
            responsejson = await request.json()

            _LOGGER.debug("webhookjson:"+ str(responsejson))

            alarmstate = hass.states.get("effortlesshome.alarm_id")
  
            if alarmstate is not None:
                alarmstatus = hass.states.get("effortlesshome.alarmstatus").state

                if alarmstatus == "ACTIVE":
                    latestalarmid = hass.states.get("effortlesshome.alarm_id").state

                    for event in responsejson:
                        alarm_id = event["meta"]["alarm_id"]

                        if alarm_id == latestalarmid:
                            event_type = event["event_type"]
                            hass.states.async_set("effortlesshome.alarmlasteventtype", event_type)

                            if event_type == "alarm.closed":
                                hass.states.async_set("effortlesshome.alarmstatus", "Closed")
                            elif event_type == "alarm.status.canceled":
                                hass.states.async_set("effortlesshome.alarmstatus", "Canceled")

        except ValueError:
            _LOGGER.debug("webhookjson error:"+ str(ValueError))
            return  # Handle invalid JSON
          
    async def async_remove(self):
        """Unregister the webhook when the integration is removed."""
        async_unregister(self.hass, self.webhook_id)


