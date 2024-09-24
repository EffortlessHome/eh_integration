import json
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import Entity
from homeassistant.components.webhook import async_register, async_unregister

class SecurityAlarmWebhook:
    """Class to handle Security Alarm Webhook functionality."""

    def __init__(self, hass: HomeAssistant, webhook_id: str):
        self.hass = hass
        self.webhook_id = webhook_id

    async def async_setup(self):
        """Register the webhook when setting up the integration."""
        async_register(
            self.hass,
            self.webhook_id,
            "SecurityAlarm",
            "Security Alarm Webhook",
            self.handle_webhook
        )

    async def handle_webhook(self, hass: HomeAssistant, webhook_id: str, request):
        """Handle incoming webhook requests."""
        if request.method not in ["POST", "PUT"]:
            return  # Ignore methods other than POST or PUT

        # Extract the JSON payload from the request
        try:
            responsejson = await request.json()
        except ValueError:
            return  # Handle invalid JSON

        # Simulated test JSON (from the YAML definition)
        testjson = {
            "event_time": "2024-06-12T17:08:12.294Z",
            "meta": {"alarm_id": 56789}
        }

        # Get the alarm_id from the response JSON
        alarm_id = responsejson[0].get('meta', {}).get('alarm_id')

        # Get the latest_alarm_id from input_text entity in Home Assistant
        latest_alarm_id = hass.states.get('input_text.latest_alarm_id').state

        # Check if the alarm_id matches the latest_alarm_id
        if str(alarm_id) == latest_alarm_id:
            event_time = responsejson[0].get('event_time')
            event_type = responsejson[0].get('event_type')

            # Update Home Assistant input_text entities with the response data
            await hass.services.async_call(
                "input_text",
                "set_value",
                {
                    "entity_id": "input_text.lastalarmeventtime",
                    "value": event_time
                }
            )

            await hass.services.async_call(
                "input_text",
                "set_value",
                {
                    "entity_id": "input_text.lastalarmeventtype",
                    "value": event_type
                }
            )

            await hass.services.async_call(
                "input_text",
                "set_value",
                {
                    "entity_id": "input_text.latestalarmstatus",
                    "value": event_type
                }
            )

            # Send a notification about the alarm event
            await hass.services.async_call(
                "notify",
                "notify",
                {
                    "message": f"Received Security Alarm Status Update: {event_type} at {event_time}"
                }
            )

    async def async_remove(self):
        """Unregister the webhook when the integration is removed."""
        async_unregister(self.hass, self.webhook_id)


async def async_setup(hass: HomeAssistant, config):
    """Set up the Security Alarm Webhook integration."""
    webhook_id = 'alarmwebhook'
    alarm_webhook = SecurityAlarmWebhook(hass, webhook_id)
    await alarm_webhook.async_setup()

    return True