"""The effortlesshome Integration."""

from __future__ import annotations
import logging
import bcrypt
import base64
import re

from homeassistant.core import (
    callback,
)
from homeassistant.components.alarm_control_panel import DOMAIN as PLATFORM
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    ATTR_CODE,
    ATTR_NAME,
)
from homeassistant.core import HomeAssistant, asyncio
from homeassistant.helpers import device_registry as dr, entity_registry as er
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.helpers.dispatcher import (
    async_dispatcher_connect,
    async_dispatcher_send,
)
from homeassistant.helpers.service import (
    async_register_admin_service,
)
from . import const
from .const import DOMAIN
from .store import async_get_registry
from .panel import (
    async_register_panel,
    async_unregister_panel,
)
from .card import async_register_card
from .websockets import async_register_websockets
from .entity import async_setup_entities
from .theme import effortlesshomeTheme
from .deviceclassgroupsync import async_setup_devicegroup

from .sensors import (
    SensorHandler,
    ATTR_GROUP,
    ATTR_ENTITIES,
    ATTR_NEW_ENTITY_ID,
)
from .automations import AutomationHandler
from .mqtt import MqttHandler
from .event import EventHandler

import asyncio
import logging
from datetime import timedelta

import socket

import aiohttp
import async_timeout
import json

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import Config
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.helpers.update_coordinator import UpdateFailed
from homeassistant.helpers.discovery import async_load_platform

from .const import CONF_USERNAME
from .const import CONF_SYSTEMID
from .const import DOMAIN
from .const import EH_INITIALIZE_API
from .const import EH_SECURITY_API

from homeassistant.core import HomeAssistant, ServiceCall, callback
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.typing import ConfigType
from .sensor import ehsensor
from .binary_sensor import binarymedalertsensor

import os
import yaml

_LOGGER = logging.getLogger(__name__)


class HASSComponent:
    # Class-level property to hold the hass instance
    hass_instance = None

    @classmethod
    def set_hass(cls, hass: HomeAssistant):
        cls.hass_instance = hass

    @classmethod
    def get_hass(cls):
        return cls.hass_instance


async def async_setup(hass, config):
    """Track states and offer events for sensors."""
    HASSComponent.set_hass(hass)

    _LOGGER.info("Setting up effortlesshome binary sensors integration")

    await hass.helpers.discovery.async_load_platform('sensor', const.DOMAIN , {}, config)
    await hass.helpers.discovery.async_load_platform('binary_sensor', const.DOMAIN , {}, config) 

    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up effortlesshome integration from a config entry."""
    session = async_get_clientsession(hass)

    store = await async_get_registry(hass)
    coordinator = effortlesshomeCoordinator(hass, session, entry, store)

    device_registry = dr.async_get(hass)
    device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(const.DOMAIN, coordinator.id)},
        name=const.NAME,
        model=const.NAME,
        sw_version=const.VERSION,
        manufacturer=const.MANUFACTURER,
    )

    # retrieve the stored username from initial config flow
    username = entry.data.get(CONF_USERNAME)
    systemid = entry.data.get(CONF_SYSTEMID)

    result = await initialize_eh(hass, username, systemid, coordinator)

    if result is False:
        return
      
    if entry.unique_id is None:
        hass.config_entries.async_update_entry(entry, unique_id=coordinator.id, data={})

    hass.async_create_task(
        hass.config_entries.async_forward_entry_setup(entry, PLATFORM)
    )

    # Register the panel (frontend)
    await async_register_panel(hass)
    await async_register_card(hass)

    #eh custom
    await async_setup_entities(hass, entry)
    await async_setup_devicegroup(hass, entry)
    await getPlanStatus(None)

    theme = effortlesshomeTheme(hass)
    await theme.async_setup()

    # Websocket support
    await async_register_websockets(hass)

    # Register custom services
    register_services(hass)
    register_security_services(hass)

    return True


async def async_unload_entry(hass, entry):
    """Unload effortlesshome config entry."""
    unload_ok = all(
        await asyncio.gather(
            *[hass.config_entries.async_forward_entry_unload(entry, PLATFORM)]
        )
    )
    if not unload_ok:
        return False

    async_unregister_panel(hass)
    coordinator = hass.data[const.DOMAIN]["coordinator"]
    await coordinator.async_unload()
    return True


async def async_remove_entry(hass, entry):
    """Remove effortlesshome config entry."""
    async_unregister_panel(hass)
    coordinator = hass.data[const.DOMAIN]["coordinator"]
    await coordinator.async_delete_config()
    del hass.data[const.DOMAIN]

class effortlesshomeCoordinator(DataUpdateCoordinator):
    """Define an object to hold effortlesshome device."""

    def __init__(self, hass, session, entry, store):
        """Initialize."""
        self.id = entry.unique_id
        self.hass = hass
        self.entry = entry
        self.store = store
        self._subscriptions = []

        self._subscriptions.append(
            async_dispatcher_connect(
                hass, "effortlesshome_platform_loaded", self.setup_alarm_entities
            )
        )
        self.register_events()

        super().__init__(hass, _LOGGER, name=const.DOMAIN)

    @callback
    def setup_alarm_entities(self):
        self.hass.data[const.DOMAIN]["sensor_handler"] = SensorHandler(self.hass)
        self.hass.data[const.DOMAIN]["automation_handler"] = AutomationHandler(
            self.hass
        )
        self.hass.data[const.DOMAIN]["mqtt_handler"] = MqttHandler(self.hass)
        self.hass.data[const.DOMAIN]["event_handler"] = EventHandler(self.hass)

        areas = self.store.async_get_areas()
        config = self.store.async_get_config()

        for item in areas.values():
            async_dispatcher_send(self.hass, "effortlesshome_register_entity", item)

        if len(areas) > 1 and config["master"]["enabled"]:
            async_dispatcher_send(
                self.hass, "effortlesshome_register_master", config["master"]
            )

    async def async_update_config(self, data):
        if "master" in data:
            old_config = self.store.async_get_config()
            if old_config[const.ATTR_MASTER] != data["master"]:
                if self.hass.data[const.DOMAIN]["master"]:
                    await self.async_remove_entity("master")
                if data["master"]["enabled"]:
                    async_dispatcher_send(
                        self.hass, "effortlesshome_register_master", data["master"]
                    )
                else:
                    automations = self.hass.data[const.DOMAIN][
                        "automation_handler"
                    ].get_automations_by_area(None)
                    if len(automations):
                        for el in automations:
                            self.store.async_delete_automation(el)
                        async_dispatcher_send(
                            self.hass, "effortlesshome_automations_updated"
                        )

        self.store.async_update_config(data)
        async_dispatcher_send(self.hass, "effortlesshome_config_updated")

    async def async_update_area_config(self, area_id: str = None, data: dict = {}):
        if const.ATTR_REMOVE in data:
            # delete an area
            res = self.store.async_get_area(area_id)
            if not res:
                return
            sensors = self.store.async_get_sensors()
            sensors = dict(filter(lambda el: el[1]["area"] == area_id, sensors.items()))
            if sensors:
                for el in sensors.keys():
                    self.store.async_delete_sensor(el)
                async_dispatcher_send(self.hass, "effortlesshome_sensors_updated")

            automations = self.hass.data[const.DOMAIN][
                "automation_handler"
            ].get_automations_by_area(area_id)
            if len(automations):
                for el in automations:
                    self.store.async_delete_automation(el)
                async_dispatcher_send(self.hass, "effortlesshome_automations_updated")

            self.store.async_delete_area(area_id)
            await self.async_remove_entity(area_id)

            if (
                len(self.store.async_get_areas()) == 1
                and self.hass.data[const.DOMAIN]["master"]
            ):
                await self.async_remove_entity("master")

        elif self.store.async_get_area(area_id):
            # modify an area
            entry = self.store.async_update_area(area_id, data)
            if "name" not in data:
                async_dispatcher_send(
                    self.hass, "effortlesshome_config_updated", area_id
                )
            else:
                await self.async_remove_entity(area_id)
                async_dispatcher_send(
                    self.hass, "effortlesshome_register_entity", entry
                )
        else:
            # create an area
            entry = self.store.async_create_area(data)
            async_dispatcher_send(self.hass, "effortlesshome_register_entity", entry)

            config = self.store.async_get_config()

            if len(self.store.async_get_areas()) == 2 and config["master"]["enabled"]:
                async_dispatcher_send(
                    self.hass, "effortlesshome_register_master", config["master"]
                )

    def async_update_sensor_config(self, entity_id: str, data: dict):
        group = None
        if ATTR_GROUP in data:
            group = data[ATTR_GROUP]
            del data[ATTR_GROUP]

        if ATTR_NEW_ENTITY_ID in data:
            # delete old sensor entry when changing the entity_id
            new_entity_id = data[ATTR_NEW_ENTITY_ID]
            del data[ATTR_NEW_ENTITY_ID]
            self.store.async_delete_sensor(entity_id)
            self.assign_sensor_to_group(new_entity_id, group)
            self.assign_sensor_to_group(entity_id, None)
            entity_id = new_entity_id

        if const.ATTR_REMOVE in data:
            self.store.async_delete_sensor(entity_id)
            self.assign_sensor_to_group(entity_id, None)
        elif self.store.async_get_sensor(entity_id):
            self.store.async_update_sensor(entity_id, data)
            self.assign_sensor_to_group(entity_id, group)
        else:
            self.store.async_create_sensor(entity_id, data)
            self.assign_sensor_to_group(entity_id, group)

        async_dispatcher_send(self.hass, "effortlesshome_sensors_updated")

    def async_update_user_config(self, user_id: str = None, data: dict = {}):
        if const.ATTR_REMOVE in data:
            self.store.async_delete_user(user_id)
            return

        if ATTR_CODE in data and data[ATTR_CODE]:
            data[const.ATTR_CODE_FORMAT] = (
                "number" if data[ATTR_CODE].isdigit() else "text"
            )
            data[const.ATTR_CODE_LENGTH] = len(data[ATTR_CODE])
            hashed = bcrypt.hashpw(
                data[ATTR_CODE].encode("utf-8"), bcrypt.gensalt(rounds=12)
            )
            hashed = base64.b64encode(hashed)
            data[ATTR_CODE] = hashed.decode()

        if not user_id:
            self.store.async_create_user(data)
        else:
            if ATTR_CODE in data:
                if const.ATTR_OLD_CODE not in data:
                    return False
                elif not self.async_authenticate_user(
                    data[const.ATTR_OLD_CODE], user_id
                ):
                    return False
                else:
                    del data[const.ATTR_OLD_CODE]
                    self.store.async_update_user(user_id, data)
            else:
                self.store.async_update_user(user_id, data)

    def async_authenticate_user(self, code: str, user_id: str = None):
        if not user_id:
            users = self.store.async_get_users()
        else:
            users = {user_id: self.store.async_get_user(user_id)}

        for user_id, user in users.items():
            if not user[const.ATTR_ENABLED]:
                continue
            elif not user[ATTR_CODE] and not code:
                return user
            elif user[ATTR_CODE]:
                hash = base64.b64decode(user[ATTR_CODE])
                if bcrypt.checkpw(code.encode("utf-8"), hash):
                    return user

        return

    def async_update_automation_config(
        self, automation_id: str = None, data: dict = {}
    ):
        if const.ATTR_REMOVE in data:
            self.store.async_delete_automation(automation_id)
        elif not automation_id:
            self.store.async_create_automation(data)
        else:
            self.store.async_update_automation(automation_id, data)

        async_dispatcher_send(self.hass, "effortlesshome_automations_updated")

    def register_events(self):
        # handle push notifications with action buttons
        @callback
        async def async_handle_push_event(event):
            if not event.data:
                return
            action = (
                event.data.get("actionName")
                if "actionName" in event.data
                else event.data.get("action")
            )

            if action not in const.EVENT_ACTIONS:
                return

            if self.hass.data[const.DOMAIN]["master"]:
                alarm_entity = self.hass.data[const.DOMAIN]["master"]
            elif len(self.hass.data[const.DOMAIN]["areas"]) == 1:
                alarm_entity = list(self.hass.data[const.DOMAIN]["areas"].values())[0]
            else:
                _LOGGER.info(
                    "Cannot process the push action, since there are multiple areas."
                )
                return

            arm_mode = (
                alarm_entity._revert_state
                if alarm_entity._revert_state in const.ARM_MODES
                else alarm_entity._arm_mode
            )
            res = re.search(r"^effortlesshome_ARM_", action)
            if res:
                arm_mode = (
                    action.replace("effortlesshome_", "")
                    .lower()
                    .replace("arm", "armed")
                )
            if not arm_mode:
                _LOGGER.info(
                    "Cannot process the push action, since the arm mode is not known."
                )
                return

            if action == const.EVENT_ACTION_FORCE_ARM:
                _LOGGER.info("Received request for force arming")
                alarm_entity.async_handle_arm_request(
                    arm_mode, skip_code=True, bypass_open_sensors=True
                )
            elif action == const.EVENT_ACTION_RETRY_ARM:
                _LOGGER.info("Received request for retry arming")
                alarm_entity.async_handle_arm_request(arm_mode, skip_code=True)
            elif action == const.EVENT_ACTION_DISARM:
                _LOGGER.info("Received request for disarming")
                alarm_entity.alarm_disarm(None, skip_code=True)
            else:
                _LOGGER.info(
                    "Received request for arming with mode {}".format(arm_mode)
                )
                alarm_entity.async_handle_arm_request(arm_mode, skip_code=True)

        self._subscriptions.append(
            self.hass.bus.async_listen(const.PUSH_EVENT, async_handle_push_event)
        )

    async def async_remove_entity(self, area_id: str):
        entity_registry = er.async_get(self.hass)
        if area_id == "master":
            entity = self.hass.data[const.DOMAIN]["master"]
            entity_registry.async_remove(entity.entity_id)
            self.hass.data[const.DOMAIN]["master"] = None
        else:
            entity = self.hass.data[const.DOMAIN]["areas"][area_id]
            entity_registry.async_remove(entity.entity_id)
            self.hass.data[const.DOMAIN]["areas"].pop(area_id, None)

    def async_get_sensor_groups(self):
        """fetch a list of sensor groups (websocket API hook)"""
        groups = self.store.async_get_sensor_groups()
        return list(groups.values())

    def async_get_group_for_sensor(self, entity_id: str):
        groups = self.async_get_sensor_groups()
        result = next((el for el in groups if entity_id in el[ATTR_ENTITIES]), None)
        return result["group_id"] if result else None

    def assign_sensor_to_group(self, entity_id: str, group_id: str):
        updated = False
        old_group = self.async_get_group_for_sensor(entity_id)
        if old_group and group_id != old_group:
            # remove sensor from group
            el = self.store.async_get_sensor_group(old_group)
            if len(el[ATTR_ENTITIES]) > 2:
                self.store.async_update_sensor_group(
                    old_group,
                    {ATTR_ENTITIES: [x for x in el[ATTR_ENTITIES] if x != entity_id]},
                )
            else:
                self.store.async_delete_sensor_group(old_group)
            updated = True
        if group_id:
            # add sensor to group
            group = self.store.async_get_sensor_group(group_id)
            if not group:
                _LOGGER.error(
                    "Failed to assign entity {} to group {}".format(entity_id, group_id)
                )
            elif entity_id not in group[ATTR_ENTITIES]:
                self.store.async_update_sensor_group(
                    group_id, {ATTR_ENTITIES: group[ATTR_ENTITIES] + [entity_id]}
                )
                updated = True
        if updated:
            async_dispatcher_send(self.hass, "effortlesshome_sensors_updated")

    def async_update_sensor_group_config(self, group_id: str = None, data: dict = {}):
        if const.ATTR_REMOVE in data:
            self.store.async_delete_sensor_group(group_id)
        elif not group_id:
            self.store.async_create_sensor_group(data)
        else:
            self.store.async_update_sensor_group(group_id, data)

        async_dispatcher_send(self.hass, "effortlesshome_sensors_updated")

    async def async_unload(self):
        """remove all effortlesshome objects"""

        # remove alarm_control_panel entities
        areas = list(self.hass.data[const.DOMAIN]["areas"].keys())
        for area in areas:
            await self.async_remove_entity(area)
        if self.hass.data[const.DOMAIN]["master"]:
            await self.async_remove_entity("master")

        del self.hass.data[const.DOMAIN]["sensor_handler"]
        del self.hass.data[const.DOMAIN]["automation_handler"]
        del self.hass.data[const.DOMAIN]["mqtt_handler"]
        del self.hass.data[const.DOMAIN]["event_handler"]

        # remove subscriptions for coordinator
        while len(self._subscriptions):
            self._subscriptions.pop()()

    async def async_delete_config(self):
        """wipe effortlesshome storage"""
        await self.store.async_delete()


@callback
def register_services(hass):
    """Register services used by effortlesshome component."""

    coordinator = hass.data[const.DOMAIN]["coordinator"]

    async def async_srv_toggle_user(call):
        """Enable a user by service call"""
        name = call.data.get(ATTR_NAME)
        enable = True if call.service == const.SERVICE_ENABLE_USER else False
        users = coordinator.store.async_get_users()
        user = next(
            (item for item in list(users.values()) if item[ATTR_NAME] == name), None
        )
        if user is None:
            _LOGGER.warning(
                "Failed to {} user, no match for name '{}'".format(
                    "enable" if enable else "disable", name
                )
            )
            return

        coordinator.store.async_update_user(
            user[const.ATTR_USER_ID], {const.ATTR_ENABLED: enable}
        )
        _LOGGER.debug(
            "User user '{}' was {}".format(name, "enabled" if enable else "disabled")
        )

    async_register_admin_service(
        hass,
        const.DOMAIN,
        const.SERVICE_ENABLE_USER,
        async_srv_toggle_user,
        schema=const.SERVICE_TOGGLE_USER_SCHEMA,
    )
    async_register_admin_service(
        hass,
        const.DOMAIN,
        const.SERVICE_DISABLE_USER,
        async_srv_toggle_user,
        schema=const.SERVICE_TOGGLE_USER_SCHEMA,
    )



@callback
def register_security_services(hass):

    @callback
    async def createeventservice(call: ServiceCall):
        await createevent(call)

    @callback
    async def cancelalarmservice(call: ServiceCall):
        await cancelalarm(call)

    @callback
    async def getalarmstatusservice(call: ServiceCall):
        await getalarmstatus(call)

    @callback
    async def getplanstatusservice(call: ServiceCall):
        await getPlanStatus(call)    

    @callback
    async def changemedicalalertstateservice(call: ServiceCall):
        await changemedicalalertstate(call)        

    # Register our service with Home Assistant.
    hass.services.async_register(DOMAIN, "createeventservice", createevent)
    hass.services.async_register(DOMAIN, "cancelalarmservice", cancelalarm)
    hass.services.async_register(DOMAIN, "getalarmstatusservice", getalarmstatus)
    hass.services.async_register(DOMAIN, "getplanstatusservice", getPlanStatus)
    hass.services.async_register(DOMAIN, "changemedicalalertstateservice", changemedicalalertstate)


async def initialize_eh(hass: HomeAssistant, username, systemid, coordinator) -> bool:
    print("Calling Initialize EH API")

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
                parsed_data = json.loads(content)
            
                hass.states.async_set("effortlesshome.fullname", parsed_data["fullname"])
                hass.states.async_set(
                    "effortlesshome.phonenumber", parsed_data["phonenumber"]
                )

                hass.data.setdefault(const.DOMAIN, {})
                hass.data[const.DOMAIN] = {"coordinator": coordinator, "areas": {}, "master": None, "username": username, "systemid": systemid, "eh_security_token": parsed_data["ha_security_token"]}

                return True
            else:
                return False

async def changemedicalalertstate(calldata):
    _LOGGER.debug("change medical alert calldata ="+ str(calldata.data))
   
    hass = HASSComponent.get_hass()
    hass.data[DOMAIN]["MedicalAlertTriggered"] = calldata.data["newstate"]

 

async def createevent(calldata):
    _LOGGER.debug("create event calldata ="+ str(calldata.data))
   
    hass = HASSComponent.get_hass()
    
    devicestate = hass.states.get(calldata.data["entity_id"])
    sensor_device_class = None
    sensor_device_name = None

    if devicestate and devicestate.attributes.get("friendly_name"):
        sensor_device_name = devicestate.attributes["friendly_name"]

    if devicestate and devicestate.attributes.get("device_class"):
        sensor_device_class = devicestate.attributes["device_class"]

    _LOGGER.debug("sensor_device_class ="+ sensor_device_class)
    _LOGGER.debug("sensor_device_name ="+ sensor_device_name)

    if sensor_device_class is not None and sensor_device_name is not None:
        await createevent_internal(sensor_device_name, sensor_device_class)     


async def createevent_internal(sensor_device_name, sensor_device_class):
    hass = HASSComponent.get_hass()

    alarmstate = hass.states.get("effortlesshome.alarm_id")

    jsonpayload = '{ "sensor_device_class":"'+ sensor_device_class +'", "sensor_device_name":"'+ sensor_device_name +'" }'

    if alarmstate is not None:
        alarmstatus = hass.states.get("effortlesshome.alarmstatus").state

        if alarmstatus == "ACTIVE":
            alarmid = hass.states.get("effortlesshome.alarm_id").state
            _LOGGER.debug("alarm id ="+ alarmid)

            """Call the API to create event."""
            systemid = hass.data[const.DOMAIN]["systemid"]
            eh_security_token = hass.data[const.DOMAIN]["eh_security_token"]

            url = EH_SECURITY_API +"createevent/" + alarmid
            headers = {
                "accept": "application/json, text/html",
                "X-Custom-PSK": eh_security_token,
                "eh_system_id": systemid,
                "Content-Type": "application/json; charset=utf-8",
            }
            
            _LOGGER.info("Calling create event API with payload: %s", jsonpayload)

            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=json.loads(jsonpayload)) as response:
                    _LOGGER.debug("API response status: %s", response.status)
                    _LOGGER.debug("API response headers: %s", response.headers)
                    content = await response.text()
                    _LOGGER.debug("API response content: %s", content)

                    return content


async def cancelalarm(calldata):
    hass = HASSComponent.get_hass()

    """Call the API to create a medical alarm."""
    alarmstate = hass.states.get("effortlesshome.alarm_id")

    if alarmstate is not None:
        alarmstatus = hass.states.get("effortlesshome.alarmstatus").state

        if alarmstatus == "ACTIVE":
            alarmid = hass.states.get("effortlesshome.alarm_id").state
            _LOGGER.debug("alarm id ="+ alarmid)

            systemid = hass.data[const.DOMAIN]["systemid"]
            eh_security_token = hass.data[const.DOMAIN]["eh_security_token"]

            url = EH_SECURITY_API +"cancelalarm/" + alarmid
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

                    return content


async def getalarmstatus(calldata):
    hass = HASSComponent.get_hass()

    """Call the API to create a medical alarm."""

    alarmstate = hass.states.get("effortlesshome.alarm_id")

    if alarmstate is not None:
        alarmid = alarmstate.state

        systemid = hass.data[const.DOMAIN]["systemid"]
        eh_security_token = hass.data[const.DOMAIN]["eh_security_token"]

        url = EH_SECURITY_API +"getalarmstatus/" + alarmid
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
                    alarmstatus = json_dict['status']
                    hass.states.async_set("effortlesshome.alarmstatus", alarmstatus)

                return content
            
async def getPlanStatus(calldata):
    hass = HASSComponent.get_hass()

    systemid = hass.data[const.DOMAIN]["systemid"]
    eh_security_token = hass.data[const.DOMAIN]["eh_security_token"]

    url = EH_SECURITY_API +"getsystemplansbysystemid/" + systemid
    headers = {
        "accept": "application/json, text/html",
        "X-Custom-PSK": eh_security_token,
        "eh_system_id": systemid,
        "Content-Type": "application/json; charset=utf-8",
    }

    _LOGGER.info("Calling get plan status API")

    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers) as response:
            _LOGGER.debug("API response status: %s", response.status)
            _LOGGER.debug("API response headers: %s", response.headers)
            content = await response.text()
            _LOGGER.debug("API response content: %s", content)

            #content: {"success":true,"meta":{"served_by":"v3-prod","duration":0.2581,"changes":0,"last_row_id":0,"changed_db":false,"size_after":45056,"rows_read":24,"rows_written":0},"results":[{"PlanID":1,"name":"Base Plan"},{"PlanID":2,"name":"Security Plan"},{"PlanID":3,"name":"Monitoring Plan"},{"PlanID":4,"name":"Medical Alert Plan"}]}
            if content is not None:
                data = json.loads(content)

            if "results" in data:
                # Iterate through the 'results' array and process the PlanID
                for result in data["results"]:
                    plan_id = result.get("PlanID")
                    name = result.get("name")
                    if plan_id is not None:
                        _LOGGER.debug(f"EH PlanID: {plan_id}, Plan Name: {name}")

                        if plan_id == 1:
                            hass.states.async_set("effortlesshome.activebaseplan", True)
                        elif plan_id == 2:
                            hass.states.async_set("effortlesshome.activesecurityplan", True)
                        elif plan_id == 3:
                            hass.states.async_set("effortlesshome.activemonitoringplan", True)
                        elif plan_id == 4:
                            hass.states.async_set("effortlesshome.activemedicalalertplan", True)

            else:
                _LOGGER.debug("No Active Plans Found For This System")

            return content

    