import json
import logging

from homeassistant.components import mqtt
from homeassistant.components.mqtt import (
    CONF_COMMAND_TOPIC,  # type: ignore
    CONF_STATE_TOPIC,  # type: ignore
)
from homeassistant.components.mqtt import (
    DOMAIN as ATTR_MQTT,  # type: ignore
)
from homeassistant.core import (
    HomeAssistant,
    callback,
)
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.json import JSONEncoder
from homeassistant.util import slugify

from . import const
from .helpers import (
    friendly_name_for_entity_id,
)

_LOGGER = logging.getLogger(__name__)
CONF_EVENT_TOPIC = "event_topic"


class MqttHandler:
    def __init__(self, hass: HomeAssistant) -> None:
        self.hass = hass
        self._config = None
        self._subscribed_topics = []
        self._subscriptions = []

        @callback
        def async_update_config(_args=None) -> None:
            """Mqtt config updated, reload the configuration."""
            old_config = self._config
            new_config = self.hass.data[const.DOMAIN][
                "coordinator"
            ].store.async_get_config()

            if old_config and old_config[ATTR_MQTT] == new_config[ATTR_MQTT]:
                # only update MQTT config if some parameters are changed
                return

            self._config = new_config

            if (
                not old_config
                or old_config[ATTR_MQTT][CONF_COMMAND_TOPIC]
                != new_config[ATTR_MQTT][CONF_COMMAND_TOPIC]
            ):
                # re-subscribing is only needed if the command topic has changed
                self.hass.add_job(self._async_subscribe_topics())

            _LOGGER.debug("MQTT config was (re)loaded")

        self._subscriptions.append(
            async_dispatcher_connect(
                hass, "effortlesshome_config_updated", async_update_config
            )
        )
        async_update_config()

        @callback
        def async_alarm_state_changed(
            area_id: str, old_state: str, new_state: str
        ) -> None:
            if not self._config[ATTR_MQTT][const.ATTR_ENABLED]:  # type: ignore
                return

            topic = self._config[ATTR_MQTT][CONF_STATE_TOPIC]  # type: ignore

            if not topic:  # do not publish if no topic is provided
                return

            if area_id and len(self.hass.data[const.DOMAIN]["areas"]) > 1:
                # handle the sending of a state update for a specific area
                area = self.hass.data[const.DOMAIN]["areas"][area_id]
                topic = topic.rsplit("/", 1)
                topic.insert(1, slugify(area.name))
                topic = "/".join(topic)

            payload_config = self._config[ATTR_MQTT][const.ATTR_STATE_PAYLOAD]  # type: ignore
            if payload_config.get(new_state):
                message = payload_config[new_state]
            else:
                message = new_state

            hass.async_create_task(
                mqtt.async_publish(self.hass, topic, message, retain=True)  # type: ignore
            )
            _LOGGER.debug(f"Published state '{message}' on topic '{topic}'")

        self._subscriptions.append(
            async_dispatcher_connect(
                self.hass, "effortlesshome_state_updated", async_alarm_state_changed
            )
        )

        @callback
        def async_handle_event(
            event: str, area_id: str, args: dict | None = None
        ) -> None:
            if args is None:
                args = {}
            if not self._config[ATTR_MQTT][const.ATTR_ENABLED]:  # type: ignore
                return

            topic = self._config[ATTR_MQTT][CONF_EVENT_TOPIC]  # type: ignore

            if not topic:  # do not publish if no topic is provided
                return

            if area_id and len(self.hass.data[const.DOMAIN]["areas"]) > 1:
                # handle the sending of a state update for a specific area
                area = self.hass.data[const.DOMAIN]["areas"][area_id]
                topic = topic.rsplit("/", 1)
                topic.insert(1, slugify(area.name))
                topic = "/".join(topic)

            if event == const.EVENT_ARM:
                payload = {
                    "event": "{}_{}".format(
                        event.upper(), args["arm_mode"].split("_", 1).pop(1).upper()
                    ),
                    "delay": args["delay"],
                }
            elif event == const.EVENT_TRIGGER:
                payload = {
                    "event": event.upper(),
                    "delay": args["delay"],
                    "sensors": [
                        {
                            "entity_id": entity,
                            "name": friendly_name_for_entity_id(entity, self.hass),
                        }
                        for (entity, state) in args["open_sensors"].items()
                    ],
                }
            elif event == const.EVENT_FAILED_TO_ARM:
                payload = {
                    "event": event.upper(),
                    "sensors": [
                        {
                            "entity_id": entity,
                            "name": friendly_name_for_entity_id(entity, self.hass),
                        }
                        for (entity, state) in args["open_sensors"].items()
                    ],
                }
            elif event == const.EVENT_COMMAND_NOT_ALLOWED:
                payload = {
                    "event": event.upper(),
                    "state": args["state"],
                    "command": args["command"].upper(),
                }
            elif event in [
                const.EVENT_INVALID_CODE_PROVIDED,
                const.EVENT_NO_CODE_PROVIDED,
            ]:
                payload = {"event": event.upper()}
            else:
                return

            payload = json.dumps(payload, cls=JSONEncoder)
            hass.async_create_task(mqtt.async_publish(self.hass, topic, payload))  # type: ignore

        self._subscriptions.append(
            async_dispatcher_connect(
                self.hass, "effortlesshome_event", async_handle_event
            )
        )

    def __del__(self) -> None:
        """Prepare for removal."""
        while len(self._subscribed_topics):
            self._subscribed_topics.pop()()
        while len(self._subscriptions):
            self._subscriptions.pop()()

    async def _async_subscribe_topics(self) -> None:
        """Install a listener for the command topic."""
        if len(self._subscribed_topics):
            while len(self._subscribed_topics):
                self._subscribed_topics.pop()()
            _LOGGER.debug("Removed subscribed topics")

        if not self._config[ATTR_MQTT][const.ATTR_ENABLED]:  # type: ignore
            return

        self._subscribed_topics.append(
            await mqtt.async_subscribe(  # type: ignore
                self.hass,
                self._config[ATTR_MQTT][CONF_COMMAND_TOPIC],  # type: ignore
                self.async_message_received,
            )
        )
        _LOGGER.debug(
            f"Subscribed to topic {self._config[ATTR_MQTT][CONF_COMMAND_TOPIC]}"  # noqa: G004 # type: ignore
        )

    @callback
    async def async_message_received(self, msg) -> None:
        command = None
        code = None
        area = None
        bypass_open_sensors = False
        skip_delay = False

        try:
            payload = json.loads(msg.payload)
            payload = {k.lower(): v for k, v in payload.items()}

            if "command" in payload:
                command = payload["command"]
            elif "cmd" in payload:
                command = payload["cmd"]
            elif "action" in payload:
                command = payload["action"]
            elif "state" in payload:
                command = payload["state"]

            if "code" in payload:
                code = payload["code"]
            elif "pin" in payload:
                code = payload["pin"]
            elif "password" in payload:
                code = payload["password"]
            elif "pincode" in payload:
                code = payload["pincode"]

            if payload.get("area"):
                area = payload["area"]

            if (payload.get("bypass_open_sensors")) or (payload.get("force")):
                bypass_open_sensors = payload["bypass_open_sensors"]

            if payload.get(const.ATTR_SKIP_DELAY):
                skip_delay = payload[const.ATTR_SKIP_DELAY]

        except ValueError:
            # no JSON structure found
            command = msg.payload
            code = None

        if type(command) is str:
            command = command.lower()
        else:
            _LOGGER.warning("Received unexpected command")
            return

        payload_config = self._config[ATTR_MQTT][const.ATTR_COMMAND_PAYLOAD]  # type: ignore
        skip_code = not self._config[ATTR_MQTT][const.ATTR_REQUIRE_CODE]  # type: ignore

        command_payloads = {}
        for item in const.COMMANDS:
            if payload_config.get(item):
                command_payloads[item] = payload_config[item].lower()
            else:
                command_payloads[item] = item.lower()

        if command not in list(command_payloads.values()):
            _LOGGER.warning("Received unexpected command: %s", command)
            return

        if area:
            res = list(
                filter(
                    lambda el: slugify(el.name) == area,
                    self.hass.data[const.DOMAIN]["areas"].values(),
                )
            )
            if not res:
                _LOGGER.warning(f"Area {area} does not exist")
                return
            entity = res[0]
        elif (
            self._config[const.ATTR_MASTER][const.ATTR_ENABLED]  # type: ignore
            and len(self.hass.data[const.DOMAIN]["areas"]) > 1
        ):
            entity = self.hass.data[const.DOMAIN]["master"]
        elif len(self.hass.data[const.DOMAIN]["areas"]) == 1:
            entity = next(iter(self.hass.data[const.DOMAIN]["areas"].values()))
        else:
            _LOGGER.warning("No area specified")
            return

        _LOGGER.debug(f"Received command {command}")

        if command == command_payloads[const.COMMAND_DISARM]:
            entity.alarm_disarm(code, skip_code=skip_code)
        elif command == command_payloads[const.COMMAND_ARM_AWAY]:
            await entity.async_alarm_arm_away(
                code, skip_code, bypass_open_sensors, skip_delay
            )
        elif command == command_payloads[const.COMMAND_ARM_NIGHT]:
            await entity.async_alarm_arm_night(
                code, skip_code, bypass_open_sensors, skip_delay
            )
        elif command == command_payloads[const.COMMAND_ARM_HOME]:
            await entity.async_alarm_arm_home(
                code, skip_code, bypass_open_sensors, skip_delay
            )
        elif command == command_payloads[const.COMMAND_ARM_CUSTOM_BYPASS]:
            await entity.async_alarm_arm_custom_bypass(
                code, skip_code, bypass_open_sensors, skip_delay
            )
        elif command == command_payloads[const.COMMAND_ARM_VACATION]:
            await entity.async_alarm_arm_vacation(
                code, skip_code, bypass_open_sensors, skip_delay
            )
