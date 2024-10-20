"""The effortlesshome Integration."""  # noqa: EXE002

from __future__ import annotations

import asyncio
import base64
import json
import logging
import re
from typing import TYPE_CHECKING
import homeassistant.core
import aiohttp
import bcrypt
import subprocess

from homeassistant.components.alarm_control_panel import (
    DOMAIN as PLATFORM,  # type: ignore  # noqa: PGH003
)
from homeassistant.const import (
    ATTR_CODE,
    ATTR_NAME,
)
from homeassistant.core import (
    HomeAssistant,
    ServiceCall,
    asyncio,  # noqa: F811, PGH003 # type: ignore
    callback,
)
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.dispatcher import (
    async_dispatcher_connect,
    async_dispatcher_send,
)
from homeassistant.helpers.service import (
    async_register_admin_service,
)
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from . import const
from .ai import AIHASSComponent, optimize_home
from .alarm_control_panel import createalarm
from .automations import AutomationHandler
from .card import async_register_card
from .const import (
    CONF_SYSTEMID,
    CONF_USERNAME,
    DOMAIN,
    EH_INITIALIZE_API,
    EH_SECURITY_API,
)
from .deviceclassgroupsync import async_setup_devicegroup
from .event import EventHandler
from .MotionSensorGrouper import MotionSensorGrouper
from .mqtt import MqttHandler
from .panel import (
    async_register_panel,
    async_unregister_panel,
)
from .SecurityAlarmWebhook import SecurityAlarmWebhook
from .SecurityAlarmWebhook import async_remove
from .sensors import (
    ATTR_ENTITIES,
    ATTR_GROUP,
    ATTR_NEW_ENTITY_ID,
    SensorHandler,
)
from .store import async_get_registry
from .websockets import async_register_websockets

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry

_LOGGER = logging.getLogger(__name__)


class HASSComponent:
    """Hasscomponent."""

    # Class-level property to hold the hass instance
    hass_instance = None

    @classmethod
    def set_hass(cls, hass: HomeAssistant) -> None:
        """Set Hass."""
        cls.hass_instance = hass

    @classmethod
    def get_hass(cls):  # noqa: ANN206
        """Get Hass."""
        return cls.hass_instance


async def async_setup(hass, config) -> bool:  # noqa: ANN001
    """Track states and offer events for sensors."""
    HASSComponent.set_hass(hass)

    _LOGGER.info("Setting up effortlesshome binary sensors integration")
    await hass.helpers.discovery.async_load_platform(
        "binary_sensor", const.DOMAIN, {}, config
    )

    _LOGGER.info("Setting up effortlesshome light integration")

    await hass.helpers.discovery.async_load_platform("light", const.DOMAIN, {}, config)

    # Load the group platform
    await hass.helpers.discovery.async_load_platform("group", const.DOMAIN, {}, config)

    AIHASSComponent.set_hass(hass)

    @callback
    async def createoptimizehomeservice(call: ServiceCall) -> None:
        await optimize_home(call)

    hass.services.async_register(DOMAIN, "createoptimizehomeservice", optimize_home)

    @callback
    async def createcleanmotionfilesservice(call: ServiceCall) -> None:
        await cleanmotionfiles(call)

    hass.services.async_register(
        DOMAIN, "createcleanmotionfilesservice", cleanmotionfiles
    )

    async def after_home_assistant_started(event):
        """Call this function after Home Assistant has started."""
        # Call your function here
        await loaddevicegroups(None)

    # Listen for the 'homeassistant_started' event
    hass.bus.async_listen_once(
        homeassistant.core.EVENT_HOMEASSISTANT_STARTED, after_home_assistant_started
    )

    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool | None:
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
        return None

    if entry.unique_id is None:
        hass.config_entries.async_update_entry(entry, unique_id=coordinator.id, data={})

    hass.async_create_task(
        hass.config_entries.async_forward_entry_setup(entry, PLATFORM)
    )

    # Register the panel (frontend)
    await async_register_panel(hass)
    await async_register_card(hass)

    await getPlanStatus(None)

    webhook = SecurityAlarmWebhook(hass)
    await SecurityAlarmWebhook.async_setup_webhook(webhook)

    # Websocket support
    await async_register_websockets(hass)

    # Register custom services
    register_services(hass)
    register_security_services(hass)

    hass.data[DOMAIN]["MedicalAlertTriggered"] = "Off"
    hass.data[DOMAIN]["GoodnightRanForDay"] = "Off"
    hass.data[DOMAIN]["IsRenterOccupied"] = "Off"

    # Initialize the Motion Sensor Grouper
    grouper = MotionSensorGrouper(hass)

    # Create groups for motion sensors
    await grouper.create_sensor_groups()
    await grouper.create_security_sensor_group()

    return True


async def async_unload_entry(hass, entry) -> bool:  # noqa: ANN001
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

    await SecurityAlarmWebhook.async_remove(hass)

    return True


async def async_remove_entry(hass, entry) -> None:  # noqa: ANN001, ARG001
    """Remove effortlesshome config entry."""
    async_unregister_panel(hass)
    coordinator = hass.data[const.DOMAIN]["coordinator"]
    await coordinator.async_delete_config()
    del hass.data[const.DOMAIN]


class effortlesshomeCoordinator(DataUpdateCoordinator):  # noqa: N801
    """Define an object to hold effortlesshome device."""

    def __init__(self, hass, session, entry, store) -> None:  # noqa: ANN001, ARG002
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
    def setup_alarm_entities(self) -> None:
        """Setup alarm entities."""  # noqa: D401
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

    async def async_update_config(self, data) -> None:  # noqa: ANN001
        """Update config."""
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

    async def async_update_area_config(  # noqa: D102, PLR0912
        self, area_id: str | None = None, data: dict | None = None
    ) -> None:
        if data is None:
            data = {}
        if const.ATTR_REMOVE in data:
            # delete an area
            res = self.store.async_get_area(area_id)
            if not res:
                return
            sensors = self.store.async_get_sensors()
            sensors = dict(filter(lambda el: el[1]["area"] == area_id, sensors.items()))
            if sensors:
                for el in sensors:
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
            await self.async_remove_entity(area_id)  # type: ignore  # noqa: PGH003

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
                await self.async_remove_entity(area_id)  # type: ignore  # noqa: PGH003
                async_dispatcher_send(
                    self.hass, "effortlesshome_register_entity", entry
                )
        else:
            # create an area
            entry = self.store.async_create_area(data)
            async_dispatcher_send(self.hass, "effortlesshome_register_entity", entry)

            config = self.store.async_get_config()

            if len(self.store.async_get_areas()) == 2 and config["master"]["enabled"]:  # noqa: PLR2004
                async_dispatcher_send(
                    self.hass, "effortlesshome_register_master", config["master"]
                )

    def async_update_sensor_config(self, entity_id: str, data: dict) -> None:
        """Update sensor config."""
        group = None
        if ATTR_GROUP in data:
            group = data[ATTR_GROUP]
            del data[ATTR_GROUP]

        if ATTR_NEW_ENTITY_ID in data:
            # delete old sensor entry when changing the entity_id
            new_entity_id = data[ATTR_NEW_ENTITY_ID]
            del data[ATTR_NEW_ENTITY_ID]
            self.store.async_delete_sensor(entity_id)
            self.assign_sensor_to_group(new_entity_id, group)  # type: ignore  # noqa: PGH003
            self.assign_sensor_to_group(entity_id, None)  # type: ignore  # noqa: PGH003
            entity_id = new_entity_id

        if const.ATTR_REMOVE in data:
            self.store.async_delete_sensor(entity_id)
            self.assign_sensor_to_group(entity_id, None)  # type: ignore  # noqa: PGH003
        elif self.store.async_get_sensor(entity_id):
            self.store.async_update_sensor(entity_id, data)
            self.assign_sensor_to_group(entity_id, group)  # type: ignore  # noqa: PGH003
        else:
            self.store.async_create_sensor(entity_id, data)
            self.assign_sensor_to_group(entity_id, group)  # type: ignore  # noqa: PGH003

        async_dispatcher_send(self.hass, "effortlesshome_sensors_updated")

    def async_update_user_config(  # noqa: D102
        self, user_id: str | None = None, data: dict | None = None
    ) -> bool | None:
        if data is None:
            data = {}
        if const.ATTR_REMOVE in data:
            self.store.async_delete_user(user_id)
            return None

        if data.get(ATTR_CODE):
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
            return None
        if ATTR_CODE in data:
            if const.ATTR_OLD_CODE not in data or not self.async_authenticate_user(
                data[const.ATTR_OLD_CODE], user_id
            ):
                return False
            del data[const.ATTR_OLD_CODE]
            self.store.async_update_user(user_id, data)
            return None
        self.store.async_update_user(user_id, data)
        return None

    def async_authenticate_user(self, code: str, user_id: str | None = None):  # noqa: ANN201
        """Authenticate user."""
        if not user_id:
            users = self.store.async_get_users()
        else:
            users = {user_id: self.store.async_get_user(user_id)}

        for user_id, user in users.items():  # noqa: B007, PLR1704
            if not user[const.ATTR_ENABLED]:
                continue
            if not user[ATTR_CODE] and not code:
                return user
            if user[ATTR_CODE]:
                hash = base64.b64decode(user[ATTR_CODE])  # noqa: A001
                if bcrypt.checkpw(code.encode("utf-8"), hash):
                    return user

        return None

    def async_update_automation_config(  # noqa: D102
        self, automation_id: str | None = None, data: dict | None = None
    ) -> None:
        if data is None:
            data = {}
        if const.ATTR_REMOVE in data:
            self.store.async_delete_automation(automation_id)
        elif not automation_id:
            self.store.async_create_automation(data)
        else:
            self.store.async_update_automation(automation_id, data)

        async_dispatcher_send(self.hass, "effortlesshome_automations_updated")

    def register_events(self) -> None:
        """Register events."""

        # handle push notifications with action buttons
        @callback
        async def async_handle_push_event(event) -> None:  # noqa: ANN001
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
                alarm_entity = next(
                    iter(self.hass.data[const.DOMAIN]["areas"].values())
                )
            else:
                _LOGGER.info(
                    "Cannot process the push action, since there are multiple areas."
                )
                return

            arm_mode = (
                alarm_entity._revert_state  # noqa: SLF001
                if alarm_entity._revert_state in const.ARM_MODES  # noqa: SLF001
                else alarm_entity._arm_mode  # noqa: SLF001
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
                _LOGGER.info(f"Received request for arming with mode {arm_mode}")  # noqa: G004
                alarm_entity.async_handle_arm_request(arm_mode, skip_code=True)

        self._subscriptions.append(
            self.hass.bus.async_listen(const.PUSH_EVENT, async_handle_push_event)
        )

    async def async_remove_entity(self, area_id: str) -> None:
        """Remove entity."""
        entity_registry = er.async_get(self.hass)
        if area_id == "master":
            entity = self.hass.data[const.DOMAIN]["master"]
            entity_registry.async_remove(entity.entity_id)
            self.hass.data[const.DOMAIN]["master"] = None
        else:
            entity = self.hass.data[const.DOMAIN]["areas"][area_id]
            entity_registry.async_remove(entity.entity_id)
            self.hass.data[const.DOMAIN]["areas"].pop(area_id, None)

    def async_get_sensor_groups(self):  # noqa: ANN201
        """Fetch a list of sensor groups (websocket API hook)."""
        groups = self.store.async_get_sensor_groups()
        return list(groups.values())

    def async_get_group_for_sensor(self, entity_id: str):  # noqa: ANN201
        """Get group for sensor."""
        groups = self.async_get_sensor_groups()
        result = next((el for el in groups if entity_id in el[ATTR_ENTITIES]), None)
        return result["group_id"] if result else None

    def assign_sensor_to_group(self, entity_id: str, group_id: str) -> None:
        """Assign sensor to group."""
        updated = False
        old_group = self.async_get_group_for_sensor(entity_id)
        if old_group and group_id != old_group:
            # remove sensor from group
            el = self.store.async_get_sensor_group(old_group)
            if len(el[ATTR_ENTITIES]) > 2:  # noqa: PLR2004
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
                    f"Failed to assign entity {entity_id} to group {group_id}"  # noqa: G004
                )
            elif entity_id not in group[ATTR_ENTITIES]:
                self.store.async_update_sensor_group(
                    group_id, {ATTR_ENTITIES: group[ATTR_ENTITIES] + [entity_id]}
                )
                updated = True
        if updated:
            async_dispatcher_send(self.hass, "effortlesshome_sensors_updated")

    def async_update_sensor_group_config(  # noqa: D102
        self, group_id: str | None = None, data: dict | None = None
    ) -> None:
        if data is None:
            data = {}
        if const.ATTR_REMOVE in data:
            self.store.async_delete_sensor_group(group_id)
        elif not group_id:
            self.store.async_create_sensor_group(data)
        else:
            self.store.async_update_sensor_group(group_id, data)

        async_dispatcher_send(self.hass, "effortlesshome_sensors_updated")

    async def async_unload(self) -> None:
        """Remove all effortlesshome objects."""
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

    async def async_delete_config(self) -> None:
        """Wipe effortlesshome storage."""
        await self.store.async_delete()


@callback
def register_services(hass: HomeAssistant) -> None:
    """Register services used by effortlesshome component."""
    coordinator = hass.data[const.DOMAIN]["coordinator"]

    async def async_srv_toggle_user(call) -> None:  # noqa: ANN001
        """Enable a user by service call."""
        name = call.data.get(ATTR_NAME)
        enable = call.service == const.SERVICE_ENABLE_USER
        users = coordinator.store.async_get_users()
        user = next(
            (item for item in list(users.values()) if item[ATTR_NAME] == name), None
        )
        if user is None:
            _LOGGER.warning(
                "Failed to {} user, no match for name '{}'".format(  # noqa: G001
                    "enable" if enable else "disable", name
                )
            )
            return

        coordinator.store.async_update_user(
            user[const.ATTR_USER_ID], {const.ATTR_ENABLED: enable}
        )
        _LOGGER.debug(
            "User user '{}' was {}".format(name, "enabled" if enable else "disabled")  # noqa: G001
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
def register_security_services(hass) -> None:  # noqa: ANN001
    """Register security services."""

    @callback
    async def createeventservice(call: ServiceCall) -> None:
        await createevent(call)

    @callback
    async def cancelalarmservice(call: ServiceCall) -> None:
        await cancelalarm(call)

    @callback
    async def getalarmstatusservice(call: ServiceCall) -> None:
        await getalarmstatus(call)

    @callback
    async def getplanstatusservice(call: ServiceCall) -> None:
        await getPlanStatus(call)

    @callback
    async def changemedicalalertstateservice(call: ServiceCall) -> None:
        await changemedicalalertstate(call)

    @callback
    async def changegoodnightranfordaystateservice(call: ServiceCall) -> None:
        await changegoodnightranfordaystate(call)

    @callback
    async def changerenteroccupiedstateservice(call: ServiceCall) -> None:
        await changerenteroccupiedstate(call)

    @callback
    async def confirmpendingalarmservice(call: ServiceCall) -> None:
        await createalarm(call)

    @callback
    async def loaddevicegroupservice(call: ServiceCall) -> None:
        await loaddevicegroups(call)

    # Register our service with Home Assistant.
    hass.services.async_register(DOMAIN, "createeventservice", createevent)
    hass.services.async_register(DOMAIN, "cancelalarmservice", cancelalarm)
    hass.services.async_register(DOMAIN, "getalarmstatusservice", getalarmstatus)
    hass.services.async_register(DOMAIN, "getplanstatusservice", getPlanStatus)
    hass.services.async_register(DOMAIN, "loaddevicegroupservice", loaddevicegroups)
    hass.services.async_register(
        DOMAIN, "changemedicalalertstateservice", changemedicalalertstate
    )
    hass.services.async_register(
        DOMAIN, "changegoodnightranfordaystateservice", changegoodnightranfordaystate
    )
    hass.services.async_register(
        DOMAIN, "changerenteroccupiedstateservice", changerenteroccupiedstate
    )
    hass.services.async_register(DOMAIN, "confirmpendingalarmservice", createalarm)


async def initialize_eh(hass: HomeAssistant, username, systemid, coordinator) -> bool:  # noqa: ANN001
    """Initialize EH."""
    url = EH_INITIALIZE_API + username + "/" + systemid
    headers = {
        "Accept": "application/json, text/html",
    }

    async with aiohttp.ClientSession() as session:  # noqa: SIM117
        async with session.post(url, headers=headers, json={}) as response:
            _LOGGER.debug("API response status: %s", response.status)
            _LOGGER.debug("API response headers: %s", response.headers)
            content = await response.text()
            _LOGGER.debug("API response content: %s", content)

            if response.status == 200 and content != None:  # noqa: PLR2004
                parsed_data = json.loads(content)

                hass.states.async_set(
                    "effortlesshome.fullname", parsed_data["fullname"]
                )
                hass.states.async_set(
                    "effortlesshome.phonenumber", parsed_data["phonenumber"]
                )

                hass.data.setdefault(const.DOMAIN, {})
                hass.data[const.DOMAIN] = {
                    "coordinator": coordinator,
                    "areas": {},
                    "master": None,
                    "username": username,
                    "systemid": systemid,
                    "eh_security_token": parsed_data["ha_security_token"],
                }

                return True
            return False


async def changemedicalalertstate(calldata) -> None:  # noqa: ANN001
    """Change medical alert state."""
    hass = HASSComponent.get_hass()
    hass.data[DOMAIN]["MedicalAlertTriggered"] = calldata.data["newstate"]  # type: ignore  # noqa: PGH003


async def loaddevicegroups(calldata) -> None:  # noqa: ANN001, ARG001
    """Load device groups."""
    hass = HASSComponent.get_hass()
    await async_setup_devicegroup(hass)


async def changegoodnightranfordaystate(calldata) -> None:  # noqa: ANN001
    """Change goodnight ran for day state."""
    hass = HASSComponent.get_hass()
    hass.data[DOMAIN]["GoodnightRanForDay"] = calldata.data["newstate"]  # type: ignore  # noqa: PGH003


async def changerenteroccupiedstate(calldata) -> None:  # noqa: ANN001
    """Change renter occupied state."""
    _LOGGER.debug("change renter occupied state calldata =" + str(calldata.data))  # noqa: G003

    hass = HASSComponent.get_hass()
    hass.data[DOMAIN]["IsRenterOccupied"] = calldata.data["newstate"]  # type: ignore  # noqa: PGH003


async def createevent(calldata) -> None:  # noqa: ANN001
    """Create event."""
    _LOGGER.debug("create event calldata =" + str(calldata.data))  # noqa: G003

    hass = HASSComponent.get_hass()

    devicestate = hass.states.get(calldata.data["entity_id"])  # type: ignore  # noqa: PGH003
    sensor_device_class = None
    sensor_device_name = None

    if devicestate and devicestate.attributes.get("friendly_name"):
        sensor_device_name = devicestate.attributes["friendly_name"]

    if devicestate and devicestate.attributes.get("device_class"):
        sensor_device_class = devicestate.attributes["device_class"]

    if sensor_device_class is not None and sensor_device_name is not None:
        await createevent_internal(sensor_device_name, sensor_device_class)


async def createevent_internal(sensor_device_name, sensor_device_class):  # noqa: ANN001, ANN201
    """Create event internal."""
    hass = HASSComponent.get_hass()

    alarmstate = hass.states.get("effortlesshome.alarm_id")  # type: ignore  # noqa: PGH003

    jsonpayload = (
        '{ "sensor_device_class":"'
        + sensor_device_class
        + '", "sensor_device_name":"'
        + sensor_device_name
        + '" }'
    )

    if alarmstate is not None:
        alarmstatus = hass.states.get("effortlesshome.alarmstatus").state  # type: ignore  # noqa: PGH003

        if alarmstatus == "ACTIVE":
            alarmid = hass.states.get("effortlesshome.alarm_id").state  # type: ignore  # noqa: PGH003
            _LOGGER.debug("alarm id =" + alarmid)  # noqa: G003

            """Call the API to create event."""
            systemid = hass.data[const.DOMAIN]["systemid"]  # type: ignore  # noqa: PGH003
            eh_security_token = hass.data[const.DOMAIN]["eh_security_token"]  # type: ignore  # noqa: PGH003

            url = EH_SECURITY_API + "createevent/" + alarmid
            headers = {
                "accept": "application/json, text/html",
                "X-Custom-PSK": eh_security_token,
                "eh_system_id": systemid,
                "Content-Type": "application/json; charset=utf-8",
            }

            _LOGGER.info("Calling create event API with payload: %s", jsonpayload)

            async with (
                aiohttp.ClientSession() as session,
                session.post(
                    url, headers=headers, json=json.loads(jsonpayload)
                ) as response,
            ):
                _LOGGER.debug("API response status: %s", response.status)
                _LOGGER.debug("API response headers: %s", response.headers)
                content = await response.text()
                _LOGGER.debug("API response content: %s", content)

                return content
        return None
    return None


async def cancelalarm(calldata):  # noqa: ANN001, ANN201, ARG001
    """Cancel alarm."""
    hass = HASSComponent.get_hass()

    """Call the API to create a medical alarm."""
    alarmstate = hass.states.get("effortlesshome.alarm_id")  # type: ignore  # noqa: PGH003

    if alarmstate is not None:
        alarmstatus = hass.states.get("effortlesshome.alarmstatus").state  # type: ignore  # noqa: PGH003

        if alarmstatus == "ACTIVE":
            alarmid = hass.states.get("effortlesshome.alarm_id").state  # type: ignore  # noqa: PGH003

            systemid = hass.data[const.DOMAIN]["systemid"]  # type: ignore  # noqa: PGH003
            eh_security_token = hass.data[const.DOMAIN]["eh_security_token"]  # type: ignore  # noqa: PGH003

            url = EH_SECURITY_API + "cancelalarm/" + alarmid
            headers = {
                "accept": "application/json, text/html",
                "X-Custom-PSK": eh_security_token,
                "eh_system_id": systemid,
                "Content-Type": "application/json; charset=utf-8",
            }

            _LOGGER.info("Calling cancel alarm API")

            async with aiohttp.ClientSession() as session:  # noqa: SIM117
                async with session.post(url, headers=headers) as response:
                    _LOGGER.debug("API response status: %s", response.status)
                    _LOGGER.debug("API response headers: %s", response.headers)
                    content = await response.text()
                    _LOGGER.debug("API response content: %s", content)

                    return content
        return None
    return None


async def getalarmstatus(calldata):  # noqa: ANN001, ANN201, ARG001
    """Get alarm status."""
    hass = HASSComponent.get_hass()

    """Call the API to create a medical alarm."""

    alarmstate = hass.states.get("effortlesshome.alarm_id")  # type: ignore  # noqa: PGH003

    if alarmstate is not None:
        alarmid = alarmstate.state

        systemid = hass.data[const.DOMAIN]["systemid"]  # type: ignore  # noqa: PGH003
        eh_security_token = hass.data[const.DOMAIN]["eh_security_token"]  # type: ignore  # noqa: PGH003

        url = EH_SECURITY_API + "getalarmstatus/" + alarmid
        headers = {
            "accept": "application/json, text/html",
            "X-Custom-PSK": eh_security_token,
            "eh_system_id": systemid,
            "Content-Type": "application/json; charset=utf-8",
        }

        _LOGGER.info("Calling get alarm status API")

        async with aiohttp.ClientSession() as session:  # noqa: SIM117
            async with session.post(url, headers=headers) as response:
                _LOGGER.debug("API response status: %s", response.status)
                _LOGGER.debug("API response headers: %s", response.headers)
                content = await response.text()
                _LOGGER.debug("API response content: %s", content)

                if content is not None:
                    json_dict = json.loads(content)
                    alarmstatus = json_dict["status"]
                    hass.states.async_set("effortlesshome.alarmstatus", alarmstatus)  # type: ignore  # noqa: PGH003

                return content
    return None


async def cleanmotionfiles(calldata):
    """Execute the shell command to delete old snapshots."""

    age = "30"

    try:
        age = calldata.data["age"]
    except:
        _LOGGER.error("Invalid Args To Clean Motion Service. Using Default 30 days")

    command = "find /media/snapshots/* -mtime +" + age + " -exec rm {} \\;"

    # Use subprocess to execute the shell command
    process = subprocess.run(
        command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )

    if process.returncode == 0:
        _LOGGER.info("Successfully deleted old snapshots.")
    else:
        _LOGGER.error(f"Error deleting snapshots: {process.stderr.decode()}")


async def getPlanStatus(calldata):  # noqa: ANN001, ANN201, ARG001, N802
    """Get plan status."""
    hass = HASSComponent.get_hass()

    systemid = hass.data[const.DOMAIN]["systemid"]  # type: ignore  # noqa: PGH003
    eh_security_token = hass.data[const.DOMAIN]["eh_security_token"]  # type: ignore  # noqa: PGH003

    url = EH_SECURITY_API + "getsystemplansbysystemid/" + systemid
    headers = {
        "accept": "application/json, text/html",
        "X-Custom-PSK": eh_security_token,
        "eh_system_id": systemid,
        "Content-Type": "application/json; charset=utf-8",
    }

    _LOGGER.info("Calling get plan status API")

    async with aiohttp.ClientSession() as session:  # noqa: SIM117
        async with session.post(url, headers=headers) as response:
            _LOGGER.debug("API response status: %s", response.status)
            _LOGGER.debug("API response headers: %s", response.headers)
            content = await response.text()
            _LOGGER.debug("API response content: %s", content)

            if content is not None:
                data = json.loads(content)

            if "results" in data:
                # Iterate through the 'results' array and process the PlanID
                for result in data["results"]:
                    plan_id = result.get("PlanID")
                    name = result.get("name")
                    active = result.get("active")
                    if plan_id is not None:
                        _LOGGER.debug(
                            f"EH PlanID: {plan_id}, Plan Name: {name}, Active: {active}"
                        )  # noqa: G004

                        if plan_id == 1:
                            hass.states.async_set(
                                "effortlesshome.activebaseplan", active == 1
                            )  # type: ignore  # noqa: FBT003, PGH003
                        elif plan_id == 2:  # noqa: PLR2004
                            hass.states.async_set(  # type: ignore  # noqa: PGH003
                                "effortlesshome.activesecurityplan",
                                active == 1,  # noqa: FBT003, PGH003 # type: ignore
                            )
                        elif plan_id == 3:  # noqa: PLR2004
                            hass.states.async_set(  # type: ignore  # noqa: PGH003
                                "effortlesshome.activemonitoringplan",
                                active == 1,  # noqa: FBT003, PGH003 # type: ignore
                            )
                        elif plan_id == 4:  # noqa: PLR2004
                            hass.states.async_set(  # type: ignore  # noqa: PGH003
                                "effortlesshome.activemedicalalertplan",
                                active == 1,  # noqa: FBT003, PGH003 # type: ignore
                            )

            else:
                _LOGGER.debug("No Active Plans Found For This System")

            return content
