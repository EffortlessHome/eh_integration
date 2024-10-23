"""Initialization of effortlesshome alarm_control_panel platform."""

import asyncio
import datetime
import functools
import json
import logging
import operator
from abc import abstractmethod

import aiohttp
import homeassistant.util.dt as dt_util
from homeassistant.components.alarm_control_panel import (
    ATTR_CODE_ARM_REQUIRED,
    AlarmControlPanelEntity,
    AlarmControlPanelEntityFeature,
)
from homeassistant.components.alarm_control_panel import (
    DOMAIN as PLATFORM,
)
from homeassistant.const import (
    ATTR_CODE_FORMAT,
    ATTR_NAME,
    STATE_ALARM_ARMED_AWAY,
    STATE_ALARM_ARMED_CUSTOM_BYPASS,
    STATE_ALARM_ARMED_HOME,
    STATE_ALARM_ARMED_NIGHT,
    STATE_ALARM_ARMED_VACATION,
    STATE_ALARM_ARMING,
    STATE_ALARM_DISARMED,
    STATE_ALARM_PENDING,
    STATE_ALARM_TRIGGERED,
)
from homeassistant.core import (
    HomeAssistant,
    callback,
)
from homeassistant.helpers import entity_platform
from homeassistant.helpers.dispatcher import (
    async_dispatcher_connect,
    async_dispatcher_send,
    dispatcher_send,
)
from homeassistant.helpers.event import (
    async_call_later,
    async_track_point_in_time,
)
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.util import slugify

from . import const
from .const import DOMAIN, EH_SECURITY_API

_LOGGER = logging.getLogger(__name__)


class HASSComponent:
    # Class-level property to hold the hass instance
    hass_instance = None

    @classmethod
    def set_hass(cls, hass: HomeAssistant) -> None:
        cls.hass_instance = hass

    @classmethod
    def get_hass(cls):
        return cls.hass_instance


class PendingAlarm:
    def __init__(
        self, open_sensors: dict, sensor_device_class: str, sensor_device_name: str
    ) -> None:
        # Initialize the class with provided parameters
        self.open_sensors = open_sensors
        self.sensor_device_class = sensor_device_class
        self.sensor_device_name = sensor_device_name

    # method to display the alarm details
    def display_alarm_info(self) -> None:
        for _sensor, _status in self.open_sensors.items():
            pass


class PendingAlarmComponent:
    # Class-level property to hold the pending alarm instance
    _pendingalarm = None

    @classmethod
    def set_pendingalarm(cls, alarm: PendingAlarm) -> None:
        cls._pendingalarm = alarm

    @classmethod
    def get_pendingalarm(cls):
        return cls._pendingalarm


async def creatependingalarm(open_sensors: dict | None = None) -> None:
    _LOGGER.debug("in create pending alarm")
    hass = HASSComponent.get_hass()

    if open_sensors is not None:
        _LOGGER.debug("open_sensors" + str(open_sensors))

    sensor_device_class = None
    sensor_device_name = None

    if open_sensors is not None:
        for entity_id in open_sensors:
            devicestate = hass.states.get(entity_id)
            if devicestate and devicestate.attributes.get("friendly_name"):
                sensor_device_name = devicestate.attributes["friendly_name"]
            if devicestate and devicestate.attributes.get("device_class"):
                sensor_device_class = devicestate.attributes["device_class"]

    if sensor_device_class is not None:
        _LOGGER.debug("sensor_device_class" + sensor_device_class)

    if sensor_device_name is not None:
        _LOGGER.debug("sensor_device_nameopen_sensors" + sensor_device_name)

    alarm = PendingAlarm(open_sensors, sensor_device_class, sensor_device_name)
    _LOGGER.debug(alarm.display_alarm_info())

    PendingAlarmComponent.set_pendingalarm(alarm)

    hass.data[DOMAIN]["alarm_id"] = "pending"
    hass.data[DOMAIN]["alarmcreatemessage"] = "pending"
    hass.data[DOMAIN]["alarmownerid"] = "pending"
    hass.data[DOMAIN]["alarmstatus"] = "PENDING"
    hass.data[DOMAIN]["alarmlasteventtype"] = "alarm.status.pending"


async def createalarm(calldata) -> None:
    """Call the API to create alarm."""
    _LOGGER.debug("in create alarm")
    hass = HASSComponent.get_hass()

    pendingAlarm = PendingAlarmComponent.get_pendingalarm()

    if pendingAlarm is None:
        _LOGGER.debug("No Pending Alarm Found")
        return
    _LOGGER.debug(pendingAlarm.display_alarm_info())

    sensor_device_class = pendingAlarm.sensor_device_class
    sensor_device_name = pendingAlarm.sensor_device_name

    response = None

    match sensor_device_class:
        case "door":
            response = await createsecurityalarm(
                sensor_device_class, sensor_device_name
            )
        case "window":
            response = await createsecurityalarm(
                sensor_device_class, sensor_device_name
            )
        case "motion":
            response = await createsecurityalarm(
                sensor_device_class, sensor_device_name
            )
        case "moisture":
            response = await createmonitoringalarm(
                sensor_device_class, sensor_device_name
            )
        case "heat":
            response = await createmonitoringalarm(
                sensor_device_class, sensor_device_name
            )
        case "smoke":
            response = await createmonitoringalarm(
                sensor_device_class, sensor_device_name
            )
        case "carbon_monoxide":
            response = await createmonitoringalarm(
                sensor_device_class, sensor_device_name
            )
        case "safety":
            response = await createmedicalalarm(sensor_device_class, sensor_device_name)

    if response is not None:
        json_dict = json.loads(response)
        alarmcreatemessage = json_dict["Message"]
        alarmid = json_dict["AlarmID"]
        alarmownerid = json_dict["OwnerID"]
        alarmstatus = json_dict["Status"]

        hass.data[DOMAIN]["alarm_id"] = alarmid
        hass.data[DOMAIN]["alarmcreatemessage"] = alarmcreatemessage
        hass.data[DOMAIN]["alarmownerid"] = alarmownerid
        hass.data[DOMAIN]["alarmstatus"] = alarmstatus
        hass.data[DOMAIN]["alarmlasteventtype"] = "alarm.status.created"

        PendingAlarmComponent.set_pendingalarm(None)

    return


async def createsecurityalarm(sensor_device_class: str, sensor_device_name: str):
    """Call the API to create a security alarm."""
    _LOGGER.debug("in create security alarm")

    hass = HASSComponent.get_hass()

    systemid = hass.data[const.DOMAIN]["systemid"]
    eh_security_token = hass.data[const.DOMAIN]["eh_security_token"]

    url = EH_SECURITY_API + "createsecurityalarm/0"
    headers = {
        "accept": "application/json, text/html",
        "X-Custom-PSK": eh_security_token,
        "eh_system_id": systemid,
        "Content-Type": "application/json; charset=utf-8",
    }
    payload = (
        '{"sensor_device_class":"'
        + sensor_device_class
        + '", "sensor_device_name":"'
        + sensor_device_name
        + '"}'
    )

    _LOGGER.debug("Calling create alarm API with payload: %s", payload)

    async with (
        aiohttp.ClientSession() as session,
        session.post(url, headers=headers, json=json.loads(payload)) as response,
    ):
        _LOGGER.debug("API response status: %s", response.status)
        _LOGGER.debug("API response headers: %s", response.headers)
        content = await response.text()
        _LOGGER.debug("API response content: %s", content)

        return content


async def createmonitoringalarm(sensor_device_class: str, sensor_device_name: str):
    hass = HASSComponent.get_hass()

    """Call the API to create a monitoring alarm."""
    _LOGGER.debug("in create monitoring alarm")
    systemid = hass.data[const.DOMAIN]["systemid"]
    eh_security_token = hass.data[const.DOMAIN]["eh_security_token"]

    url = EH_SECURITY_API + "createmonitoringalarm/0"
    headers = {
        "accept": "application/json, text/html",
        "X-Custom-PSK": eh_security_token,
        "eh_system_id": systemid,
        "Content-Type": "application/json; charset=utf-8",
    }
    payload = (
        '{"sensor_device_class":"'
        + sensor_device_class
        + '", "sensor_device_name":"'
        + sensor_device_name
        + '"}'
    )

    _LOGGER.info("Calling create monitoring alarm API with payload: %s", payload)

    async with (
        aiohttp.ClientSession() as session,
        session.post(url, headers=headers, json=json.loads(payload)) as response,
    ):
        _LOGGER.debug("API response status: %s", response.status)
        _LOGGER.debug("API response headers: %s", response.headers)
        content = await response.text()
        _LOGGER.debug("API response content: %s", content)

        return content


async def createmedicalalarm(sensor_device_class: str, sensor_device_name: str):
    hass = HASSComponent.get_hass()

    """Call the API to create a medical alarm."""
    _LOGGER.debug("in create medical alert alarm")
    systemid = hass.data[const.DOMAIN]["systemid"]
    eh_security_token = hass.data[const.DOMAIN]["eh_security_token"]

    url = EH_SECURITY_API + "createmedicalalarm/0"
    headers = {
        "accept": "application/json, text/html",
        "X-Custom-PSK": eh_security_token,
        "eh_system_id": systemid,
        "Content-Type": "application/json; charset=utf-8",
    }
    payload = (
        '{"sensor_device_class":"'
        + sensor_device_class
        + '", "sensor_device_name":"'
        + sensor_device_name
        + '"}'
    )

    _LOGGER.info("Calling create medical alert alarm API with payload: %s", payload)

    async with (
        aiohttp.ClientSession() as session,
        session.post(url, headers=headers, json=json.loads(payload)) as response,
    ):
        _LOGGER.debug("API response status: %s", response.status)
        _LOGGER.debug("API response headers: %s", response.headers)
        content = await response.text()
        _LOGGER.debug("API response content: %s", content)

        return content


async def cancelalarm():
    hass = HASSComponent.get_hass()

    """Call the API to create a medical alarm."""
    _LOGGER.debug("in cancel alarm")

    hass.data[DOMAIN]["MedicalAlertTriggered"] = "Off"

    alarmstate = hass.data[DOMAIN]["alarm_id"]

    if alarmstate is not None and alarmstate != "":
        alarmstatus = hass.data[DOMAIN]["alarmstatus"]

        if alarmstatus == "PENDING":
            PendingAlarmComponent.set_pendingalarm(None)

            hass.data[DOMAIN]["alarm_id"] = ""
            hass.data[DOMAIN]["alarmcreatemessage"] = ""
            hass.data[DOMAIN]["alarmownerid"] = ""
            hass.data[DOMAIN]["alarmstatus"] = ""
            hass.data[DOMAIN]["alarmlasteventtype"] = ""

            return None

        if alarmstatus == "ACTIVE":
            alarmid = hass.data[DOMAIN]["alarm_id"]
            _LOGGER.debug("alarm id =" + alarmid)

            systemid = hass.data[const.DOMAIN]["systemid"]
            eh_security_token = hass.data[const.DOMAIN]["eh_security_token"]

            url = EH_SECURITY_API + "cancelalarm/" + alarmid
            headers = {
                "accept": "application/json, text/html",
                "X-Custom-PSK": eh_security_token,
                "eh_system_id": systemid,
                "Content-Type": "application/json; charset=utf-8",
            }

            _LOGGER.info("Calling cancel alarm API")

            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers) as response:
                    _LOGGER.debug("API response status: %s", response.status)
                    _LOGGER.debug("API response headers: %s", response.headers)
                    content = await response.text()
                    _LOGGER.debug("API response content: %s", content)

                    # {"status":"CANCELED","created_at":"2024-09-21T15:13:24.895Z"}
                    if content is not None:
                        json_dict = json.loads(content)
                        alarmstatus = json_dict["status"]

                        hass.data[DOMAIN]["alarm_id"] = ""
                        hass.data[DOMAIN]["alarmcreatemessage"] = ""
                        hass.data[DOMAIN]["alarmownerid"] = ""
                        hass.data[DOMAIN]["alarmstatus"] = ""
                        hass.data[DOMAIN]["alarmlasteventtype"] = alarmstatus

                    return content
        return None
    return None


async def getalarmstatus():
    hass = HASSComponent.get_hass()

    """Call the API to create a medical alarm."""
    _LOGGER.debug("in get alarm status")

    alarmstate = hass.data[DOMAIN]["alarm_id"]

    if alarmstate is not None and alarmstate != "":
        alarmid = hass.data[DOMAIN]["alarm_id"]

        if alarmid == "pending":
            return None

        systemid = hass.data[const.DOMAIN]["systemid"]
        eh_security_token = hass.data[const.DOMAIN]["eh_security_token"]

        url = EH_SECURITY_API + "getalarmstatus/" + alarmid
        headers = {
            "accept": "application/json, text/html",
            "X-Custom-PSK": eh_security_token,
            "eh_system_id": systemid,
            "Content-Type": "application/json; charset=utf-8",
        }

        _LOGGER.info("Calling get alarm status API")

        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers) as response:
                _LOGGER.debug("API response status: %s", response.status)
                _LOGGER.debug("API response headers: %s", response.headers)
                content = await response.text()
                _LOGGER.debug("API response content: %s", content)

                if content is not None:
                    json_dict = json.loads(content)
                    alarmstatus = json_dict["status"]
                    hass.states.async_set("effortlesshome.alarmstatus", alarmstatus)

                return content
    return None


#######################


async def async_setup(hass, config) -> bool:
    """Track states and offer events for sensors."""
    HASSComponent.set_hass(hass)
    return True


async def async_setup_platform(
    hass, config, async_add_entities, discovery_info=None
) -> bool:
    """Set up the platform from config."""
    HASSComponent.set_hass(hass)
    return True


async def async_setup_entry(hass, config_entry, async_add_devices) -> None:
    """Set up the effortlesshome entities."""
    HASSComponent.set_hass(hass)

    @callback
    def async_add_alarm_entity(config: dict) -> None:
        """Add each entity as Alarm Control Panel."""
        entity_id = "{}.{}".format(PLATFORM, slugify(config["name"]))

        alarm_entity = effortlesshomeAreaEntity(
            hass=hass,
            entity_id=entity_id,
            name=config["name"],
            area_id=config["area_id"],
        )
        hass.data[const.DOMAIN]["areas"][config["area_id"]] = alarm_entity
        async_add_devices([alarm_entity])

    async_dispatcher_connect(
        hass, "effortlesshome_register_entity", async_add_alarm_entity
    )

    @callback
    def async_add_alarm_master(config: dict) -> None:
        """Add each entity as Alarm Control Panel."""
        entity_id = "{}.{}".format(PLATFORM, slugify(config["name"]))

        alarm_entity = effortlesshomeMasterEntity(
            hass=hass,
            entity_id=entity_id,
            name=config["name"],
        )
        hass.data[const.DOMAIN]["master"] = alarm_entity
        async_add_devices([alarm_entity])

    async_dispatcher_connect(
        hass, "effortlesshome_register_master", async_add_alarm_master
    )
    async_dispatcher_send(hass, "effortlesshome_platform_loaded")

    # Register services
    platform = entity_platform.current_platform.get()
    platform.async_register_entity_service(
        const.SERVICE_ARM,
        const.SERVICE_ARM_SCHEMA,
        "async_service_arm_handler",
    )
    platform.async_register_entity_service(
        const.SERVICE_DISARM,
        const.SERVICE_DISARM_SCHEMA,
        "async_service_disarm_handler",
    )


class effortlesshomeBaseEntity(AlarmControlPanelEntity, RestoreEntity):
    def __init__(self, hass: HomeAssistant, name: str, entity_id: str) -> None:
        """Initialize the alarm_control_panel entity."""
        self.entity_id = entity_id
        self._name = name
        self._state = None
        self.hass = hass
        self._config = {}
        self._arm_mode = None
        self._changed_by = None
        self._open_sensors = {}
        self._bypassed_sensors = []
        self._delay = None
        self.expiration = None
        self.area_id = None
        self._revert_state = None
        self._ready_to_arm_modes = []

    @property
    def device_info(self) -> dict:
        """Return info for device registry."""
        return {
            "identifiers": {
                (const.DOMAIN, self.hass.data[const.DOMAIN]["coordinator"].id)
            },
            "name": const.NAME,
            "model": const.NAME,
            "sw_version": const.VERSION,
            "manufacturer": const.MANUFACTURER,
        }

    @property
    def unique_id(self) -> str:
        """Return a unique ID to use for this entity."""
        return f"{self.entity_id}"

    @property
    def name(self):
        """Return the friendly name to use for this entity."""
        return self._name

    @property
    def should_poll(self) -> bool:
        """Return the polling state."""
        return False

    @property
    def code_format(self):
        """Return whether code consists of digits or characters."""
        if (
            self._state == STATE_ALARM_DISARMED
            and self.code_arm_required
            or (
                self._state != STATE_ALARM_DISARMED
                and self._config
                and const.ATTR_CODE_DISARM_REQUIRED in self._config
                and self._config[const.ATTR_CODE_DISARM_REQUIRED]
            )
        ):
            return self._config[ATTR_CODE_FORMAT]

        return None

    @property
    def changed_by(self):
        """Last change triggered by."""
        return self._changed_by

    @property
    def state(self):
        """Return the state of the device."""
        return self._state

    @property
    def supported_features(self) -> int:
        """Return the list of supported features."""
        return 0

    @property
    def code_arm_required(self):
        """Whether the code is required for arm actions."""
        if not self._config or ATTR_CODE_ARM_REQUIRED not in self._config:
            return True  # assume code is needed (conservative approach)
        if self._state != STATE_ALARM_DISARMED:
            return self._config[const.ATTR_CODE_MODE_CHANGE_REQUIRED]
        return self._config[ATTR_CODE_ARM_REQUIRED]

    @property
    def arm_mode(self):
        """Return the arm mode."""
        return self._arm_mode if self._state != STATE_ALARM_DISARMED else None

    @property
    def open_sensors(self):
        """Get open sensors."""
        if not self._open_sensors:
            return None
        return self._open_sensors

    @open_sensors.setter
    def open_sensors(self, value) -> None:
        """Set open_sensors sensors."""
        if type(value) is dict:
            self._open_sensors = value
        else:
            self._open_sensors = {}

    @property
    def bypassed_sensors(self):
        """Get bypassed sensors."""
        if not self._bypassed_sensors:
            return None
        return self._bypassed_sensors

    @bypassed_sensors.setter
    def bypassed_sensors(self, value) -> None:
        """Set bypassed sensors."""
        if type(value) is list:
            self._bypassed_sensors = value
        elif not value:
            self._bypassed_sensors = None

    @property
    def delay(self):
        """Get delay."""
        return self._delay

    @delay.setter
    def delay(self, value) -> None:
        """Set delay."""
        if type(value) is int:
            self._delay = value
            self.expiration = (
                dt_util.utcnow() + datetime.timedelta(seconds=value)
            ).replace(microsecond=0)
        else:
            self._delay = None
            self.expiration = None

    @property
    def extra_state_attributes(self):
        """Return the data of the entity."""
        return {
            "arm_mode": self.arm_mode,
            "open_sensors": self.open_sensors,
            "bypassed_sensors": self.bypassed_sensors,
            "delay": self.delay,
        }

    def _validate_code(self, code, to_state):
        """Validate given code."""
        if (
            (
                to_state == STATE_ALARM_DISARMED
                and not self._config[const.ATTR_CODE_DISARM_REQUIRED]
            )
            or (
                to_state != STATE_ALARM_DISARMED
                and self._state == STATE_ALARM_DISARMED
                and not self._config[ATTR_CODE_ARM_REQUIRED]
            )
            or (
                STATE_ALARM_DISARMED not in (to_state, self._state)
                and not self._config[const.ATTR_CODE_MODE_CHANGE_REQUIRED]
            )
        ):
            self._changed_by = None
            return (True, None)
        if not code or len(code) < 1:
            return (False, const.EVENT_NO_CODE_PROVIDED)

        res = self.hass.data[const.DOMAIN]["coordinator"].async_authenticate_user(code)
        if not res:
            # wrong code was entered
            return (False, const.EVENT_INVALID_CODE_PROVIDED)
        if res[const.ATTR_AREA_LIMIT] and not all(
            area in res[const.ATTR_AREA_LIMIT]
            for area in (
                [self.area_id]
                if self.area_id
                else list(self.hass.data[const.DOMAIN]["areas"].keys())
            )
        ):
            # user is not allowed to operate this area
            _LOGGER.debug(
                f"User {res[ATTR_NAME]} has no permission to arm/disarm this area."
            )
            return (False, const.EVENT_INVALID_CODE_PROVIDED)
        if to_state == STATE_ALARM_DISARMED and not res["can_disarm"]:
            # user is not allowed to disarm the alarm
            _LOGGER.debug(
                f"User {res[ATTR_NAME]} has no permission to disarm the alarm."
            )
            return (False, const.EVENT_INVALID_CODE_PROVIDED)
        if to_state in const.ARM_MODES and not res["can_arm"]:
            # user is not allowed to arm the alarm
            _LOGGER.debug(f"User {res[ATTR_NAME]} has no permission to arm the alarm.")
            return (False, const.EVENT_INVALID_CODE_PROVIDED)
        self._changed_by = res[ATTR_NAME]
        return (True, res)

    @callback
    def async_service_disarm_handler(self, code, context_id=None) -> None:
        """Handle external disarm request from effortlesshome.disarm service."""
        _LOGGER.debug("Service effortlesshome.disarm was called")

        self.alarm_disarm(code=code, context_id=context_id)

    @callback
    def alarm_disarm(self, code, **kwargs) -> bool | None:
        """Send disarm command."""
        _LOGGER.debug("alarm_disarm")
        skip_code = kwargs.get("skip_code", False)
        context_id = kwargs.get("context_id", None)

        if self._state == STATE_ALARM_DISARMED or not self._config:
            if not self._config:
                _LOGGER.warning(
                    "Cannot process disarm command, alarm is not initialized yet."
                )
            else:
                _LOGGER.warning(
                    f"Cannot go to state {STATE_ALARM_DISARMED} from state {self._state}."
                )
            dispatcher_send(
                self.hass,
                "effortlesshome_event",
                const.EVENT_COMMAND_NOT_ALLOWED,
                self.area_id,
                {
                    "state": self._state,
                    "command": const.COMMAND_DISARM,
                    const.ATTR_CONTEXT_ID: context_id,
                },
            )
            return None
        (res, info) = self._validate_code(code, STATE_ALARM_DISARMED)
        if not res and not skip_code:
            dispatcher_send(
                self.hass,
                "effortlesshome_event",
                info,
                self.area_id,
                {
                    const.ATTR_CONTEXT_ID: context_id,
                    "command": const.COMMAND_DISARM,
                },
            )
            _LOGGER.warning("Wrong code provided.")
            return None
        self.open_sensors = None
        self.bypassed_sensors = None
        self.async_update_state(STATE_ALARM_DISARMED)
        if self.changed_by:
            _LOGGER.info(f"Alarm '{self.name}' is disarmed by {self.changed_by}.")
        else:
            _LOGGER.info(f"Alarm '{self.name}' is disarmed.")

        asyncio.run(cancelalarm())

        dispatcher_send(
            self.hass,
            "effortlesshome_event",
            const.EVENT_DISARM,
            self.area_id,
            {const.ATTR_CONTEXT_ID: context_id},
        )
        return True

    @callback
    def async_service_arm_handler(
        self, code, mode, skip_delay, force, context_id=None
    ) -> None:
        """Handle external arm request from effortlesshome.arm service."""
        _LOGGER.debug("Service effortlesshome.arm was called")

        if mode in const.ARM_MODE_TO_STATE:
            mode = const.ARM_MODE_TO_STATE[mode]

        self.async_handle_arm_request(
            mode,
            code=code,
            skip_delay=skip_delay,
            bypass_open_sensors=force,
            context_id=context_id,
        )

    @callback
    def async_handle_arm_request(self, arm_mode, **kwargs) -> bool | None:
        """Check if conditions are met for starting arm procedure."""
        code = kwargs.get(const.CONF_CODE, "")
        skip_code = kwargs.get("skip_code", False)
        skip_delay = kwargs.get(const.ATTR_SKIP_DELAY, False)
        bypass_open_sensors = kwargs.get("bypass_open_sensors", False)
        context_id = kwargs.get("context_id", None)

        if (
            not (const.MODES_TO_SUPPORTED_FEATURES[arm_mode] & self.supported_features)
            or (
                self._state != STATE_ALARM_DISARMED
                and self._state not in const.ARM_MODES
            )
            or not self._config
        ):
            if not self._config or not self._state:
                _LOGGER.warning(
                    "Cannot process arm command, alarm is not initialized yet."
                )
            elif not (
                const.MODES_TO_SUPPORTED_FEATURES[arm_mode] & self.supported_features
            ):
                _LOGGER.warning(f"Mode {arm_mode} is not supported, ignoring.")
            else:
                _LOGGER.warning(
                    f"Cannot go to state {arm_mode} from state {self._state}."
                )
            dispatcher_send(
                self.hass,
                "effortlesshome_event",
                const.EVENT_COMMAND_NOT_ALLOWED,
                self.area_id,
                {
                    "state": self._state,
                    "command": arm_mode.replace("armed", "arm"),
                    const.ATTR_CONTEXT_ID: context_id,
                },
            )
            return False
        if self._state in const.ARM_MODES and self._arm_mode == arm_mode:
            _LOGGER.debug(f"Alarm is already set to {arm_mode}, ignoring command.")
            return False

        if not skip_code:
            (res, info) = self._validate_code(code, arm_mode)
            if not res:
                dispatcher_send(
                    self.hass,
                    "effortlesshome_event",
                    info,
                    self.area_id,
                    {
                        "command": arm_mode.replace("armed", "arm"),
                        const.ATTR_CONTEXT_ID: context_id,
                    },
                )
                _LOGGER.warning("Wrong code provided.")
                if self.open_sensors:
                    self.open_sensors = None
                    self.schedule_update_ha_state()
                return False
            if info and info[const.ATTR_IS_OVERRIDE_CODE]:
                bypass_open_sensors = True
        else:
            self._changed_by = None

        if self._state in const.ARM_MODES:
            # we are switching between arm modes
            self._revert_state = self._state
        else:
            self._revert_state = STATE_ALARM_DISARMED
            self.open_sensors = None
            self.bypassed_sensors = None

        self.async_arm(
            arm_mode,
            skip_delay=skip_delay,
            bypass_open_sensors=bypass_open_sensors,
            context_id=context_id,
        )
        return None

    @abstractmethod
    @callback
    def async_update_state(self, state: str | None = None) -> None:
        """Update the state or refresh state attributes."""

    @abstractmethod
    @callback
    def async_trigger(self, skip_delay: bool = False, open_sensors: dict | None = None):
        """Trigger the alarm."""

    async def async_alarm_arm_away(
        self, code=None, skip_code=False, bypass_open_sensors=False, skip_delay=False
    ) -> None:
        """Send arm away command."""
        _LOGGER.debug("alarm_arm_away")
        self.async_handle_arm_request(
            STATE_ALARM_ARMED_AWAY,
            code=code,
            skip_code=skip_code,
            bypass_open_sensors=bypass_open_sensors,
            skip_delay=skip_delay,
        )

    async def async_alarm_arm_home(
        self, code=None, skip_code=False, bypass_open_sensors=False, skip_delay=False
    ) -> None:
        """Send arm home command."""
        _LOGGER.debug("alarm_arm_home")
        self.async_handle_arm_request(
            STATE_ALARM_ARMED_HOME,
            code=code,
            skip_code=skip_code,
            bypass_open_sensors=bypass_open_sensors,
            skip_delay=skip_delay,
        )

    async def async_alarm_arm_night(
        self, code=None, skip_code=False, bypass_open_sensors=False, skip_delay=False
    ) -> None:
        """Send arm night command."""
        _LOGGER.debug("alarm_arm_night")
        self.async_handle_arm_request(
            STATE_ALARM_ARMED_NIGHT,
            code=code,
            skip_code=skip_code,
            bypass_open_sensors=bypass_open_sensors,
            skip_delay=skip_delay,
        )

    async def async_alarm_arm_custom_bypass(
        self, code=None, skip_code=False, bypass_open_sensors=False, skip_delay=False
    ) -> None:
        """Send arm custom_bypass command."""
        _LOGGER.debug("alarm_arm_custom_bypass")
        self.async_handle_arm_request(
            STATE_ALARM_ARMED_CUSTOM_BYPASS,
            code=code,
            skip_code=skip_code,
            bypass_open_sensors=bypass_open_sensors,
            skip_delay=skip_delay,
        )

    async def async_alarm_arm_vacation(
        self, code=None, skip_code=False, bypass_open_sensors=False, skip_delay=False
    ) -> None:
        """Send arm vacation command."""
        _LOGGER.debug("alarm_arm_vacation")
        self.async_handle_arm_request(
            STATE_ALARM_ARMED_VACATION,
            code=code,
            skip_code=skip_code,
            bypass_open_sensors=bypass_open_sensors,
            skip_delay=skip_delay,
        )

    async def async_alarm_trigger(self, code=None) -> None:
        """Send alarm trigger command."""
        _LOGGER.debug("async_alarm_trigger")
        self.async_trigger(skip_delay=True)

    async def async_added_to_hass(self) -> None:
        """Connect to dispatcher listening for entity data notifications."""
        _LOGGER.debug(f"{self.entity_id} is added to hass")
        await super().async_added_to_hass()

        state = await self.async_get_last_state()

        # restore previous state
        if state:
            # restore attributes
            if "arm_mode" in state.attributes:
                self._arm_mode = state.attributes["arm_mode"]
            if "changed_by" in state.attributes:
                self._changed_by = state.attributes["changed_by"]
            if "open_sensors" in state.attributes:
                self.open_sensors = state.attributes["open_sensors"]
            if "bypassed_sensors" in state.attributes:
                self._bypassed_sensors = state.attributes["bypassed_sensors"]

    async def async_will_remove_from_hass(self) -> None:
        await super().async_will_remove_from_hass()
        _LOGGER.debug(f"{self.entity_id} is removed from hass")


class effortlesshomeAreaEntity(effortlesshomeBaseEntity):
    """Defines a base alarm_control_panel entity."""

    def __init__(
        self, hass: HomeAssistant, name: str, entity_id: str, area_id: str
    ) -> None:
        """Initialize the alarm_control_panel entity."""
        super().__init__(hass, name, entity_id)

        self.area_id = area_id
        self._timer = None
        coordinator = self.hass.data[const.DOMAIN]["coordinator"]
        self._config = coordinator.store.async_get_config()
        self._config.update(coordinator.store.async_get_area(self.area_id))

    @property
    def supported_features(self) -> int:
        """Return the list of supported features."""
        if not self._config or const.ATTR_MODES not in self._config:
            return 0
        supported_features = AlarmControlPanelEntityFeature.TRIGGER
        for mode, mode_config in self._config[const.ATTR_MODES].items():
            if mode_config[const.ATTR_ENABLED]:
                supported_features = (
                    supported_features | const.MODES_TO_SUPPORTED_FEATURES[mode]
                )

        return supported_features

    async def async_added_to_hass(self) -> None:
        """Connect to dispatcher listening for entity data notifications."""
        await super().async_added_to_hass()

        # make sure that the config is reloaded on changes
        @callback
        def async_update_config(area_id: str | None = None) -> None:
            _LOGGER.debug("async_update_config")
            coordinator = self.hass.data[const.DOMAIN]["coordinator"]
            self._config = coordinator.store.async_get_config()
            self._config.update(coordinator.store.async_get_area(self.area_id))
            self.schedule_update_ha_state()

        self.async_on_remove(
            async_dispatcher_connect(
                self.hass, "effortlesshome_config_updated", async_update_config
            )
        )

        # restore previous state
        state = await self.async_get_last_state()
        if state:
            initial_state = state.state
            _LOGGER.debug(f"Initial state for {self.entity_id} is {initial_state}")
            if initial_state == STATE_ALARM_ARMING:
                self.async_arm(self.arm_mode)
            elif initial_state == STATE_ALARM_PENDING:
                self.async_trigger()
            elif initial_state == STATE_ALARM_TRIGGERED:
                self.async_trigger(skip_delay=True)
            else:
                self.async_update_state(initial_state)
        else:
            self.async_update_state(STATE_ALARM_DISARMED)

        self.async_write_ha_state()

    @callback
    def async_update_state(self, state: str | None = None) -> None:
        """Update the state or refresh state attributes."""
        if state == self._state:
            return

        old_state = self._state
        self._state = state

        _LOGGER.debug(
            f"entity {self.entity_id} was updated from {old_state} to {state}"
        )

        if state in [*const.ARM_MODES, STATE_ALARM_DISARMED]:
            # cancel a running timer that possibly running when transitioning from states arming, pending, triggered
            self.async_clear_timer()

        if self.state not in [STATE_ALARM_ARMING, STATE_ALARM_PENDING]:
            self.delay = None

        if state in const.ARM_MODES:
            self._arm_mode = state
            self._revert_state = None
        elif old_state == STATE_ALARM_DISARMED and state == STATE_ALARM_TRIGGERED:
            self._arm_mode = None

        dispatcher_send(
            self.hass, "effortlesshome_state_updated", self.area_id, old_state, state
        )

        self.schedule_update_ha_state()

    def async_arm_failure(self, open_sensors: dict, context_id=None) -> None:
        """Handle arm failure."""
        self._open_sensors = open_sensors
        command = self._arm_mode.replace("armed", "arm")

        if self._state != self._revert_state and self._revert_state:
            self.async_update_state(self._revert_state)
        else:
            # when disarmed, only update the attributes
            if self._revert_state in const.ARM_MODES:
                prev_arm_mode = self._arm_mode
                self._arm_mode = self._revert_state
                self._revert_state = prev_arm_mode

            self.schedule_update_ha_state()

        dispatcher_send(
            self.hass,
            "effortlesshome_event",
            const.EVENT_FAILED_TO_ARM,
            self.area_id,
            {
                "open_sensors": open_sensors,
                "command": command,
                const.ATTR_CONTEXT_ID: context_id,
            },
        )

    @callback
    def async_arm(self, arm_mode, **kwargs) -> bool:
        """Arm the alarm or switch between arm modes."""
        skip_delay = kwargs.get("skip_delay", False)
        bypass_open_sensors = kwargs.get("bypass_open_sensors", False)
        context_id = kwargs.get("context_id", None)

        self._arm_mode = arm_mode
        exit_delay = self._config[const.ATTR_MODES][arm_mode]["exit_time"]

        if skip_delay or not exit_delay:
            # immediate arm event

            (open_sensors, bypassed_sensors) = self.hass.data[const.DOMAIN][
                "sensor_handler"
            ].validate_arming_event(
                area_id=self.area_id,
                target_state=arm_mode,
                bypass_open_sensors=bypass_open_sensors,
            )

            if open_sensors:
                # there where errors -> abort the arm
                _LOGGER.info(
                    f"Cannot transition from state {self._state} to state {arm_mode}, there are open sensors"
                )
                self.async_arm_failure(open_sensors, context_id=context_id)
                return False
            # proceed the arm
            if bypassed_sensors:
                self.bypassed_sensors = bypassed_sensors
            self.open_sensors = None
            if self.changed_by:
                _LOGGER.info(
                    f"Alarm '{self.name}' is armed ({arm_mode}) by {self.changed_by}."
                )
            else:
                _LOGGER.info(f"Alarm '{self.name}' is armed ({arm_mode}).")
            if self._state and self._state != STATE_ALARM_ARMING:
                dispatcher_send(
                    self.hass,
                    "effortlesshome_event",
                    const.EVENT_ARM,
                    self.area_id,
                    {
                        "arm_mode": arm_mode,
                        "delay": 0,
                        const.ATTR_CONTEXT_ID: context_id,
                    },
                )
            self.async_update_state(arm_mode)
            return True

        # normal arm event (from disarmed via arming)
        (open_sensors, _bypassed_sensors) = self.hass.data[const.DOMAIN][
            "sensor_handler"
        ].validate_arming_event(
            area_id=self.area_id,
            target_state=arm_mode,
            use_delay=True,
            bypass_open_sensors=bypass_open_sensors,
        )

        if open_sensors:
            # there where errors -> abort the arm
            _LOGGER.info("Cannot arm right now, there are open sensors")
            self.async_arm_failure(open_sensors, context_id=context_id)
            return False
        # proceed the arm
        _LOGGER.info(f"Alarm is now arming. Waiting for {exit_delay} seconds.")

        @callback
        def async_leave_timer_finished(now) -> None:
            """Update state at a scheduled point in time."""
            _LOGGER.debug("async_leave_timer_finished")
            self.async_clear_timer()
            self.async_arm(
                self.arm_mode,
                bypass_open_sensors=bypass_open_sensors,
                skip_delay=True,
            )

        self.async_set_timer(exit_delay, async_leave_timer_finished)
        self.delay = exit_delay
        self.open_sensors = None

        dispatcher_send(
            self.hass,
            "effortlesshome_event",
            const.EVENT_ARM,
            self.area_id,
            {
                "arm_mode": arm_mode,
                "delay": exit_delay,
                const.ATTR_CONTEXT_ID: context_id,
            },
        )
        self.async_update_state(STATE_ALARM_ARMING)

        return True

    @callback
    def async_trigger(
        self, skip_delay: bool = False, open_sensors: dict | None = None
    ) -> None:
        """Trigger request. Will only be called the first time a sensor trips."""
        if self._state == STATE_ALARM_PENDING or skip_delay or not self._arm_mode:
            entry_delay = 0
        else:
            entry_delay = self._config[const.ATTR_MODES][self._arm_mode]["entry_time"]
        trigger_time = (
            self._config[const.ATTR_MODES][self._arm_mode]["trigger_time"]
            if self._arm_mode
            else 0
        )

        if self._state and (
            self._state != STATE_ALARM_PENDING
            or (
                self._state == STATE_ALARM_PENDING
                and skip_delay
                and open_sensors != self.open_sensors
            )
        ):
            # send event on first trigger or consecutive trigger in case it has no entry delay
            dispatcher_send(
                self.hass,
                "effortlesshome_event",
                const.EVENT_TRIGGER,
                self.area_id,
                {
                    "open_sensors": open_sensors
                    if open_sensors
                    else self._open_sensors,
                    "delay": entry_delay,
                },
            )

        if open_sensors:
            self.open_sensors = open_sensors

        if not entry_delay:
            # countdown finished or immediate trigger event

            if trigger_time:
                # there is a max. trigger time configured

                @callback
                def async_trigger_timer_finished(now) -> None:
                    """Update state at a scheduled point in time."""
                    _LOGGER.debug("async_trigger_timer_finished")
                    self._changed_by = None
                    self.async_clear_timer()
                    if (
                        self._config[const.ATTR_DISARM_AFTER_TRIGGER]
                        or not self.arm_mode
                    ):
                        self.bypassed_sensors = None
                        self.async_update_state(STATE_ALARM_DISARMED)
                    else:
                        self.open_sensors = None
                        self._revert_state = STATE_ALARM_DISARMED
                        self.async_arm(
                            self.arm_mode, bypass_open_sensors=False, skip_delay=True
                        )

                    dispatcher_send(
                        self.hass,
                        "effortlesshome_event",
                        const.EVENT_TRIGGER_TIME_EXPIRED,
                        self.area_id,
                    )

                self.async_set_timer(trigger_time, async_trigger_timer_finished)
            else:
                # clear previous timer when transitioning from pending state
                self.async_clear_timer()

            _LOGGER.info("Alarm is triggered!")
            self.async_update_state(STATE_ALARM_TRIGGERED)

            # call service to create alarm here, if device type is smoke, etc. raise monitor alarm, if it is medical alert raise med alert, else security
            asyncio.create_task(creatependingalarm(open_sensors))

        else:  # to pending state

            @callback
            def async_entry_timer_finished(now) -> None:
                """Update state at a scheduled point in time."""
                self.async_clear_timer()

                _LOGGER.debug("async_entry_timer_finished")
                self.async_trigger()

            self.async_set_timer(entry_delay, async_entry_timer_finished)
            self.delay = entry_delay
            _LOGGER.info(f"Alarm will be triggered after {entry_delay} seconds.")

            self.async_update_state(STATE_ALARM_PENDING)

    def async_clear_timer(self) -> None:
        """Clear a running timer."""
        if self._timer:
            self._timer()
            self._timer = None

    def async_set_timer(self, delay, cb_func) -> None:
        self.async_clear_timer()
        now = dt_util.utcnow()

        if not isinstance(delay, datetime.timedelta):
            delay = datetime.timedelta(seconds=delay)

        self._timer = async_track_point_in_time(self.hass, cb_func, now + delay)

    def update_ready_to_arm_modes(self, value) -> None:
        """Set arm modes which are ready for arming (no blocking sensors)."""
        if value == self._ready_to_arm_modes:
            return
        _LOGGER.debug(
            "ready_to_arm_modes for {} updated to {}".format(
                self.name, ", ".join(value).replace("armed_", "")
            )
        )
        self._ready_to_arm_modes = value
        dispatcher_send(
            self.hass,
            "effortlesshome_event",
            const.EVENT_READY_TO_ARM_MODES_CHANGED,
            self.area_id,
            {const.ATTR_MODES: value},
        )


class effortlesshomeMasterEntity(effortlesshomeBaseEntity):
    """Defines a base alarm_control_panel entity."""

    def __init__(self, hass: HomeAssistant, name: str, entity_id: str) -> None:
        """Initialize the alarm_control_panel entity."""
        super().__init__(hass, name, entity_id)
        self.area_id = None
        self._target_state = None

    @property
    def supported_features(self) -> int:
        """Return the list of supported features."""
        supported_features = [
            item.supported_features or 0
            for item in self.hass.data[const.DOMAIN]["areas"].values()
        ]
        return functools.reduce(operator.and_, supported_features)

    async def async_added_to_hass(self) -> None:
        """Connect to dispatcher listening for entity data notifications."""
        await super().async_added_to_hass()

        # load the configuration and make sure that it is reloaded on changes
        @callback
        def async_update_config(area_id=None) -> None:
            if area_id and area_id in self.hass.data[const.DOMAIN]["areas"]:
                # wait for update of the area entity, to refresh the supported_features
                async_call_later(self.hass, 1, async_update_config)
                return

            coordinator = self.hass.data[const.DOMAIN]["coordinator"]
            self._config = coordinator.store.async_get_config()

            self.async_update_state()
            self.schedule_update_ha_state()

        self.async_on_remove(
            async_dispatcher_connect(
                self.hass, "effortlesshome_config_updated", async_update_config
            )
        )
        async_update_config()

        @callback
        def async_alarm_state_changed(
            area_id: str, old_state: str, new_state: str
        ) -> None:
            if not area_id:
                return
            self.async_update_state()

        async_dispatcher_connect(
            self.hass, "effortlesshome_state_updated", async_alarm_state_changed
        )

        @callback
        def async_handle_event(
            event: str, area_id: str, args: dict | None = None
        ) -> None:
            if args is None:
                args = {}
            if not area_id or event not in [
                const.EVENT_FAILED_TO_ARM,
                const.EVENT_TRIGGER,
                const.EVENT_TRIGGER_TIME_EXPIRED,
                const.EVENT_READY_TO_ARM_MODES_CHANGED,
            ]:
                return
            if event == const.EVENT_FAILED_TO_ARM and self._target_state is not None:
                open_sensors = args["open_sensors"]
                self.async_arm_failure(open_sensors)
            if event == const.EVENT_TRIGGER and (
                self._state not in [STATE_ALARM_TRIGGERED, STATE_ALARM_PENDING]
                or (
                    self._state == STATE_ALARM_PENDING
                    and self.delay
                    and self.delay > args.get("delay", 0)
                )
            ):
                # only pass initial trigger event or while trigger with shorter entry delay occurs during entry time
                dispatcher_send(
                    self.hass,
                    "effortlesshome_event",
                    const.EVENT_TRIGGER,
                    self.area_id,
                    args,
                )

            if event == const.EVENT_TRIGGER_TIME_EXPIRED and (
                self.hass.data[const.DOMAIN]["areas"][area_id].state
                == STATE_ALARM_DISARMED
            ):
                self.alarm_disarm(skip_code=True)
            if event == const.EVENT_READY_TO_ARM_MODES_CHANGED:
                self.update_ready_to_arm_modes()

        async_dispatcher_connect(self.hass, "effortlesshome_event", async_handle_event)

        state = await self.async_get_last_state()
        if state and state.state:
            self._state = state.state
        else:
            self._state = STATE_ALARM_DISARMED
        self.async_write_ha_state()

    @callback
    def async_update_state(self, state: str | None = None) -> None:
        """Update the state or refresh state attributes."""
        if state:
            # do not allow updating the state directly
            return

        states = [item.state for item in self.hass.data[const.DOMAIN]["areas"].values()]
        state = None
        if STATE_ALARM_TRIGGERED in states:
            state = STATE_ALARM_TRIGGERED
        elif STATE_ALARM_PENDING in states:
            state = STATE_ALARM_PENDING
        elif STATE_ALARM_ARMING in states and all(
            el in const.ARM_MODES or el == STATE_ALARM_ARMING for el in states
        ):
            state = STATE_ALARM_ARMING
        elif all(el == STATE_ALARM_ARMED_AWAY for el in states):
            state = STATE_ALARM_ARMED_AWAY
        elif all(el == STATE_ALARM_ARMED_HOME for el in states):
            state = STATE_ALARM_ARMED_HOME
        elif all(el == STATE_ALARM_ARMED_NIGHT for el in states):
            state = STATE_ALARM_ARMED_NIGHT
        elif all(el == STATE_ALARM_ARMED_CUSTOM_BYPASS for el in states):
            state = STATE_ALARM_ARMED_CUSTOM_BYPASS
        elif all(el == STATE_ALARM_ARMED_VACATION for el in states):
            state = STATE_ALARM_ARMED_VACATION
        elif all(el == STATE_ALARM_DISARMED for el in states):
            state = STATE_ALARM_DISARMED

        arm_modes = [
            item._arm_mode for item in self.hass.data[const.DOMAIN]["areas"].values()
        ]
        arm_mode = arm_modes[0] if len(set(arm_modes)) == 1 else None

        if state == self._target_state:
            # we are transitioning to an armed state and target state is reached
            self._target_state = None

        if state in [STATE_ALARM_ARMING, STATE_ALARM_PENDING]:
            # one or more areas went to arming/pending state, recalculate the delay time

            area_filter = dict(
                filter(
                    lambda el: el[1].state == state,
                    self.hass.data[const.DOMAIN]["areas"].items(),
                )
            )
            delays = [el.delay for el in area_filter.values()]

            # use maximum of all areas when arming, minimum of all areas when pending
            delay = (
                max(delays)
                if state == STATE_ALARM_ARMING
                else min(delays)
                if len(delays)
                else None
            )
        else:
            delay = None

        # take open sensors by combining areas having same state
        open_sensors = {}
        area_filter = dict(
            filter(
                lambda el: el[1].state == state,
                self.hass.data[const.DOMAIN]["areas"].items(),
            )
        )
        for item in area_filter.values():
            if item.open_sensors:
                open_sensors.update(item.open_sensors)

        if (
            arm_mode == self._arm_mode
            and (state == self._state or not state)
            and delay == self.delay
            and open_sensors == self.open_sensors
        ):
            # do not update if state and properties remain unchanged
            return

        self._arm_mode = arm_mode
        self.delay = delay
        self.open_sensors = open_sensors

        if state != self._state and state:
            # state changes
            old_state = self._state

            self._state = state
            _LOGGER.debug(
                f"entity {self.entity_id} was updated from {old_state} to {state}"
            )
            dispatcher_send(
                self.hass, "effortlesshome_state_updated", None, old_state, state
            )

        # take bypassed sensors by combining all areas
        bypassed_sensors = []
        for item in self.hass.data[const.DOMAIN]["areas"].values():
            if item.bypassed_sensors:
                bypassed_sensors.extend(item.bypassed_sensors)
        self.bypassed_sensors = bypassed_sensors

        self.update_ready_to_arm_modes()

        self.schedule_update_ha_state()

    @callback
    def alarm_disarm(self, code=None, **kwargs) -> None:
        """Send disarm command."""
        skip_code = kwargs.get("skip_code", False)
        context_id = kwargs.get("context_id", None)

        """Send disarm command."""
        res = super().alarm_disarm(code=code, skip_code=skip_code)
        if res:
            for item in self.hass.data[const.DOMAIN]["areas"].values():
                if item.state != STATE_ALARM_DISARMED:
                    item.alarm_disarm(code=code, skip_code=skip_code)

            dispatcher_send(
                self.hass,
                "effortlesshome_event",
                const.EVENT_DISARM,
                self.area_id,
                {const.ATTR_CONTEXT_ID: context_id},
            )

    def async_arm(self, arm_mode, **kwargs) -> None:
        """Arm the alarm or switch between arm modes."""
        skip_delay = kwargs.get("skip_delay", False)
        bypass_open_sensors = kwargs.get("bypass_open_sensors", False)
        context_id = kwargs.get("context_id", None)
        self._target_state = arm_mode

        open_sensors = {}
        for item in self.hass.data[const.DOMAIN]["areas"].values():
            if (
                item.state in const.ARM_MODES and item.arm_mode != arm_mode
            ) or item.state == STATE_ALARM_DISARMED:
                item._revert_state = (
                    item._state
                    if item._state in const.ARM_MODES
                    else STATE_ALARM_DISARMED
                )
                res = item.async_arm(
                    arm_mode,
                    skip_delay=skip_delay,
                    bypass_open_sensors=bypass_open_sensors,
                )
                if not res:
                    open_sensors.update(item.open_sensors)

        if open_sensors:
            self.async_arm_failure(open_sensors, context_id=context_id)
        else:
            delay = 0
            area_config = self.hass.data[const.DOMAIN][
                "coordinator"
            ].store.async_get_areas()
            for area_id, entity in self.hass.data[const.DOMAIN]["areas"].items():
                if entity.state == STATE_ALARM_ARMING:
                    t = area_config[area_id][const.ATTR_MODES][arm_mode]["exit_time"]
                    delay = max(delay, t)

            dispatcher_send(
                self.hass,
                "effortlesshome_event",
                const.EVENT_ARM,
                self.area_id,
                {
                    "arm_mode": arm_mode,
                    "delay": delay,
                    const.ATTR_CONTEXT_ID: context_id,
                },
            )

    def async_arm_failure(self, open_sensors: dict, context_id=None) -> None:
        """Handle arm failure."""
        self.open_sensors = open_sensors
        command = self._target_state.replace("armed", "arm")

        for item in self.hass.data[const.DOMAIN]["areas"].values():
            if item.state != self._revert_state and self._revert_state:
                item.async_update_state(self._revert_state)

        self._revert_state = self._target_state
        self._target_state = None
        dispatcher_send(
            self.hass,
            "effortlesshome_event",
            const.EVENT_FAILED_TO_ARM,
            None,
            {
                "open_sensors": open_sensors,
                "command": command,
                const.ATTR_CONTEXT_ID: context_id,
            },
        )
        self.schedule_update_ha_state()

    @callback
    def async_trigger(
        self, skip_delay: bool = False, _open_sensors: dict | None = None
    ) -> None:
        """Handle triggering via service call."""
        for item in self.hass.data[const.DOMAIN]["areas"].values():
            if item.state != self._revert_state:
                item.async_trigger(skip_delay=skip_delay)

    def update_ready_to_arm_modes(self) -> None:
        """Set arm modes which are ready for arming (no blocking sensors)."""
        modes_list = const.ARM_MODES
        for item in self.hass.data[const.DOMAIN]["areas"].values():
            modes_list = list(
                filter(lambda x: x in item._ready_to_arm_modes, modes_list)
            )
        if modes_list == self._ready_to_arm_modes:
            return
        self._ready_to_arm_modes = modes_list
        _LOGGER.debug(
            "ready_to_arm_modes for master updated to {}".format(
                ", ".join(modes_list).replace("armed_", "")
            )
        )
        dispatcher_send(
            self.hass,
            "effortlesshome_event",
            const.EVENT_READY_TO_ARM_MODES_CHANGED,
            self.area_id,
            {const.ATTR_MODES: modes_list},
        )
