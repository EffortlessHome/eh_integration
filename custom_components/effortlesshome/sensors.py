import logging  # noqa: D100, EXE002

import homeassistant.util.dt as dt_util
from homeassistant.const import (
    ATTR_LAST_TRIP_TIME,
    ATTR_NAME,
    ATTR_STATE,
    EVENT_HOMEASSISTANT_STARTED,
    STATE_ALARM_ARMING,
    STATE_ALARM_PENDING,
    STATE_ALARM_TRIGGERED,
    STATE_CLOSED,
    STATE_LOCKED,  # type: ignore  # noqa: PGH003
    STATE_OFF,
    STATE_ON,
    STATE_OPEN,
    STATE_UNAVAILABLE,
    STATE_UNKNOWN,
    STATE_UNLOCKED,  # type: ignore  # noqa: PGH003
)
from homeassistant.core import (
    CoreState,
    HomeAssistant,
    callback,
)
from homeassistant.helpers.dispatcher import (
    async_dispatcher_connect,
)
from homeassistant.helpers.event import (
    async_track_point_in_time,
    async_track_state_change_event,
)

from . import const

ATTR_USE_EXIT_DELAY = "use_exit_delay"
ATTR_USE_ENTRY_DELAY = "use_entry_delay"
ATTR_ALWAYS_ON = "always_on"
ATTR_ARM_ON_CLOSE = "arm_on_close"
ATTR_ALLOW_OPEN = "allow_open"
ATTR_TRIGGER_UNAVAILABLE = "trigger_unavailable"
ATTR_AUTO_BYPASS = "auto_bypass"
ATTR_AUTO_BYPASS_MODES = "auto_bypass_modes"
ATTR_GROUP = "group"
ATTR_GROUP_ID = "group_id"
ATTR_TIMEOUT = "timeout"
ATTR_EVENT_COUNT = "event_count"
ATTR_ENTITIES = "entities"
ATTR_NEW_ENTITY_ID = "new_entity_id"

SENSOR_STATES_OPEN = [STATE_ON, STATE_OPEN, STATE_UNLOCKED]
SENSOR_STATES_CLOSED = [STATE_OFF, STATE_CLOSED, STATE_LOCKED]


SENSOR_TYPE_DOOR = "door"
SENSOR_TYPE_WINDOW = "window"
SENSOR_TYPE_MOTION = "motion"
SENSOR_TYPE_TAMPER = "tamper"
SENSOR_TYPE_ENVIRONMENTAL = "environmental"
SENSOR_TYPE_OTHER = "other"
SENSOR_TYPES = [
    SENSOR_TYPE_DOOR,
    SENSOR_TYPE_WINDOW,
    SENSOR_TYPE_MOTION,
    SENSOR_TYPE_TAMPER,
    SENSOR_TYPE_ENVIRONMENTAL,
    SENSOR_TYPE_OTHER,
]


_LOGGER = logging.getLogger(__name__)


def parse_sensor_state(state):  # noqa: ANN001, ANN201, D103
    if not state or not state.state or state.state == STATE_UNAVAILABLE:
        return STATE_UNAVAILABLE
    if state.state in SENSOR_STATES_OPEN:
        return STATE_OPEN
    if state.state in SENSOR_STATES_CLOSED:
        return STATE_CLOSED
    return STATE_UNKNOWN


def sensor_state_allowed(state, sensor_config, alarm_state) -> bool:  # noqa: ANN001, PLR0911
    """Return whether the sensor state is permitted or a state change should occur."""
    if state != STATE_OPEN and (
        state != STATE_UNAVAILABLE or not sensor_config[ATTR_TRIGGER_UNAVAILABLE]
    ):
        # sensor has the safe state
        return True

    if alarm_state == STATE_ALARM_TRIGGERED:
        # alarm is already triggered
        return True

    if sensor_config[ATTR_ALWAYS_ON]:
        # alarm should always be triggered by always-on sensor
        return False

    if alarm_state == STATE_ALARM_ARMING and not sensor_config[ATTR_USE_EXIT_DELAY]:
        # arming should be aborted if sensor without exit delay is active
        return False

    if alarm_state in const.ARM_MODES:
        # normal triggering case
        return False

    if alarm_state == STATE_ALARM_PENDING and not sensor_config[ATTR_USE_ENTRY_DELAY]:  # noqa: SIM103
        # triggering of immediate sensor while alarm is pending
        return False

    return True


class SensorHandler:  # noqa: D101
    def __init__(self, hass: HomeAssistant) -> None:  # noqa: D107
        self._config = None
        self.hass = hass
        self._state_listener = None
        self._subscriptions = []
        self._arm_timers = {}
        self._groups = {}
        self._group_events = {}
        self._startup_complete = False

        @callback
        def async_update_sensor_config() -> None:
            """Sensor config updated, reload the configuration."""
            self._config = self.hass.data[const.DOMAIN][
                "coordinator"
            ].store.async_get_sensors()
            self._groups = self.hass.data[const.DOMAIN][
                "coordinator"
            ].store.async_get_sensor_groups()
            self._group_events = {}
            self.async_watch_sensor_states()

        self._subscriptions.append(
            async_dispatcher_connect(
                hass, "effortlesshome_state_updated", self.async_watch_sensor_states
            )
        )
        self._subscriptions.append(
            async_dispatcher_connect(
                hass, "effortlesshome_sensors_updated", async_update_sensor_config
            )
        )
        async_update_sensor_config()

        def handle_startup(_event) -> None:  # noqa: ANN001
            self._startup_complete = True

        if hass.state == CoreState.running:
            self._startup_complete = True
        else:
            hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STARTED, handle_startup)

    def __del__(self) -> None:
        """Prepare for removal."""
        if self._state_listener:
            self._state_listener()
            self._state_listener = None
        while len(self._subscriptions):
            self._subscriptions.pop()()

    def async_watch_sensor_states(
        self,
        area_id: str | None = None,
        old_state: str | None = None,
        state: str | None = None,
    ) -> None:
        """Watch sensors based on the state of the alarm entities."""
        sensors_list = []
        for area in self.hass.data[const.DOMAIN]["areas"]:
            sensors_list.extend(self.active_sensors_for_alarm_state(area))

        if self._state_listener:
            self._state_listener()

        if len(sensors_list):
            self._state_listener = async_track_state_change_event(
                self.hass, sensors_list, self.async_sensor_state_changed
            )
        else:
            self._state_listener = None

        # clear previous sensor group events which are not active for current alarm state  # noqa: E501
        for group_id in self._group_events:
            self._group_events[group_id] = dict(
                filter(
                    lambda el: el[0] in sensors_list,
                    self._group_events[group_id].items(),
                )
            )

        # handle initial sensor states
        if area_id and old_state is None:
            sensors_list = self.active_sensors_for_alarm_state(area_id)
            for entity in sensors_list:
                state = self.hass.states.get(entity)  # type: ignore  # noqa: PGH003
                sensor_state = parse_sensor_state(state)
                if state and state.state and sensor_state != STATE_UNKNOWN:  # type: ignore  # noqa: PGH003
                    _LOGGER.debug(
                        f"Initial state for {entity} is {parse_sensor_state(state)}"  # noqa: G004
                    )

        if area_id:
            self.update_ready_to_arm_status(area_id)

    def active_sensors_for_alarm_state(self, area_id: str, to_state: str | None = None):  # noqa: ANN201
        """Compose a list of sensors that are active for the state."""
        alarm_entity = self.hass.data[const.DOMAIN]["areas"][area_id]

        if to_state:
            state = to_state
        else:
            state = (
                alarm_entity.arm_mode if alarm_entity.arm_mode else alarm_entity.state
            )

        entities = []
        for entity, config in self._config.items():  # type: ignore  # noqa: PGH003
            if (
                config["area"] != area_id
                or not config["enabled"]
                or (
                    alarm_entity.bypassed_sensors
                    and entity in alarm_entity.bypassed_sensors
                )
            ):
                continue
            if state in config[const.ATTR_MODES] or config[ATTR_ALWAYS_ON]:
                entities.append(entity)
            elif not to_state and config["type"] != SENSOR_TYPE_MOTION:
                # always watch all sensors other than motion sensors, to indicate readiness for arming  # noqa: E501
                entities.append(entity)

        return entities

    def validate_arming_event(  # noqa: ANN201
        self,
        area_id: str,
        target_state: str | None = None,
        **kwargs,  # noqa: ANN003
    ):
        """Check whether all sensors have the correct state prior to arming."""
        use_delay = kwargs.get("use_delay", False)
        bypass_open_sensors = kwargs.get("bypass_open_sensors", False)

        sensors_list = self.active_sensors_for_alarm_state(area_id, target_state)
        open_sensors = {}
        bypassed_sensors = []

        alarm_state = target_state
        if use_delay and alarm_state in const.ARM_MODES:
            alarm_state = STATE_ALARM_ARMING
        elif use_delay and alarm_state == STATE_ALARM_TRIGGERED:
            alarm_state = STATE_ALARM_PENDING

        for entity in sensors_list:
            sensor_config = self._config[entity]  # type: ignore  # noqa: PGH003
            state = self.hass.states.get(entity)
            sensor_state = parse_sensor_state(state)
            if not state or not state.state:
                # entity does not exist in HA
                res = False
            else:
                res = sensor_state_allowed(sensor_state, sensor_config, alarm_state)

            if not res and target_state in const.ARM_MODES:
                # sensor is active while arming
                if bypass_open_sensors or (
                    sensor_config[ATTR_AUTO_BYPASS]
                    and target_state in sensor_config[ATTR_AUTO_BYPASS_MODES]
                ):
                    # sensor may be bypassed
                    bypassed_sensors.append(entity)
                elif sensor_config[ATTR_ALLOW_OPEN] and sensor_state == STATE_OPEN:
                    # sensor is permitted to be open during/after arming
                    continue
                else:
                    open_sensors[entity] = sensor_state

        return (open_sensors, bypassed_sensors)

    @callback
    def async_sensor_state_changed(self, event) -> None:  # noqa: ANN001
        """Callback fired when a sensor state has changed."""  # noqa: D401
        entity = event.data["entity_id"]
        old_state = parse_sensor_state(event.data["old_state"])
        new_state = parse_sensor_state(event.data["new_state"])
        sensor_config = self._config[entity]  # type: ignore  # noqa: PGH003
        if old_state == STATE_UNKNOWN:
            # sensor is unknown at startup, state which comes after is considered as initial state  # noqa: E501
            _LOGGER.debug(f"Initial state for {entity} is {new_state}")  # noqa: G004
            self.update_ready_to_arm_status(sensor_config["area"])
            return
        if old_state == new_state:
            # not a state change - ignore
            return

        _LOGGER.debug(
            f"entity {entity} changed: old_state={old_state}, new_state={new_state}"  # noqa: G004
        )

        alarm_entity = self.hass.data[const.DOMAIN]["areas"][sensor_config["area"]]
        alarm_state = alarm_entity.state

        if (
            alarm_entity.arm_mode
            and alarm_entity.arm_mode not in sensor_config[const.ATTR_MODES]
            and not sensor_config[ATTR_ALWAYS_ON]
        ):
            # sensor is not active in this arm mode, ignore
            self.update_ready_to_arm_status(sensor_config["area"])
            return

        res = sensor_state_allowed(new_state, sensor_config, alarm_state)

        if sensor_config[ATTR_ARM_ON_CLOSE] and alarm_state == STATE_ALARM_ARMING:
            # we are arming and sensor is configured to arm on closing
            if new_state == STATE_CLOSED:
                self.start_arm_timer(entity)
            else:
                self.stop_arm_timer(entity)

        if res:
            # nothing to do here, sensor state is OK
            self.update_ready_to_arm_status(sensor_config["area"])
            return

        open_sensors = self.process_group_event(entity, new_state)
        if not open_sensors:
            # triggered sensor is part of a group and should be ignored
            self.update_ready_to_arm_status(sensor_config["area"])
            return

        if sensor_config[ATTR_ALWAYS_ON]:
            # immediate trigger due to always on sensor
            _LOGGER.info(f"Alarm is triggered due to an always-on sensor: {entity}")  # noqa: G004
            alarm_entity.async_trigger(skip_delay=True, open_sensors=open_sensors)

        elif alarm_state == STATE_ALARM_ARMING:
            # sensor triggered while arming, abort arming
            _LOGGER.debug(f"Arming was aborted due to a sensor being active: {entity}")  # noqa: G004
            alarm_entity.async_arm_failure(open_sensors)

        elif alarm_state in const.ARM_MODES:
            # standard alarm trigger
            _LOGGER.info(f"Alarm is triggered due to sensor: {entity}")  # noqa: G004
            alarm_entity.async_trigger(
                skip_delay=(not sensor_config[ATTR_USE_ENTRY_DELAY]),
                open_sensors=open_sensors,
            )

        elif alarm_state == STATE_ALARM_PENDING:
            # immediate trigger while in pending state
            _LOGGER.info(f"Alarm is triggered due to sensor: {entity}")  # noqa: G004
            alarm_entity.async_trigger(skip_delay=True, open_sensors=open_sensors)

        self.update_ready_to_arm_status(sensor_config["area"])

    def start_arm_timer(self, entity) -> None:  # noqa: ANN001
        """Start timer for automatical arming."""

        @callback
        def timer_finished(now) -> None:  # noqa: ANN001, ARG001
            _LOGGER.debug("timer finished")
            sensor_config = self._config[entity]  # type: ignore  # noqa: PGH003
            alarm_entity = self.hass.data[const.DOMAIN]["areas"][sensor_config["area"]]
            if alarm_entity.state == STATE_ALARM_ARMING:
                alarm_entity.async_arm(alarm_entity.arm_mode, skip_delay=True)

        now = dt_util.utcnow()

        if entity in self._arm_timers:
            self.stop_arm_timer(entity)

        self._arm_timers[entity] = async_track_point_in_time(
            self.hass, timer_finished, now + const.SENSOR_ARM_TIME
        )

    def stop_arm_timer(self, entity=None) -> None:  # noqa: ANN001
        """Cancel timer(s) for automatical arming."""
        if entity and entity in self._arm_timers:
            self._arm_timers[entity]()
        elif not entity:
            for entity in self._arm_timers:  # noqa: PLR1704
                self._arm_timers[entity]()

    def process_group_event(self, entity: str, state: str) -> dict:
        """Check if sensor entity is member of a group and compare with previous events to evaluate trigger."""  # noqa: E501
        group_id = None
        for group in self._groups.values():
            if entity in group[ATTR_ENTITIES]:
                group_id = group[ATTR_GROUP_ID]
                break

        open_sensors = {entity: state}
        if group_id is None:
            return open_sensors

        group = self._groups[group_id]
        group_events = self._group_events.get(group_id, {})
        now = dt_util.now()
        group_events[entity] = {ATTR_STATE: state, ATTR_LAST_TRIP_TIME: now}
        self._group_events[group_id] = group_events
        recent_events = {
            entity: (now - event[ATTR_LAST_TRIP_TIME]).total_seconds()
            for (entity, event) in group_events.items()
        }
        recent_events = dict(
            filter(lambda el: el[1] <= group[ATTR_TIMEOUT], recent_events.items())
        )
        if len(recent_events.keys()) < group[ATTR_EVENT_COUNT]:
            _LOGGER.debug(
                f"tripped sensor {entity} was ignored since it belongs to group {group[ATTR_NAME]}"  # noqa: E501, G004
            )
            return {}
        for entity in recent_events:  # noqa: PLR1704
            open_sensors[entity] = group_events[entity][ATTR_STATE]
        _LOGGER.debug(
            f"tripped sensor {entity} caused the triggering of group {group[ATTR_NAME]}"  # noqa: G004
        )
        return open_sensors

    def update_ready_to_arm_status(self, area_id) -> None:  # noqa: ANN001
        """Calculate whether the system is ready for arming (based on the sensor states)."""  # noqa: E501
        alarm_entity = self.hass.data[const.DOMAIN]["areas"][area_id]

        arm_modes = [
            mode
            for (mode, config) in alarm_entity._config[const.ATTR_MODES].items()  # noqa: SLF001
            if config[const.ATTR_ENABLED]
        ]

        if (
            alarm_entity.state in const.ARM_MODES
            or alarm_entity.state == STATE_ALARM_ARMING
            and alarm_entity.arm_mode
        ):
            arm_modes.remove(alarm_entity.arm_mode)

        def arm_mode_is_ready(mode) -> bool:  # noqa: ANN001
            (blocking_sensors, _bypassed_sensors) = self.validate_arming_event(
                area_id, mode
            )
            return not (len(blocking_sensors))

        arm_modes = list(filter(arm_mode_is_ready, arm_modes))
        prev_arm_modes = alarm_entity._ready_to_arm_modes  # noqa: SLF001

        if arm_modes != prev_arm_modes:
            alarm_entity.update_ready_to_arm_modes(arm_modes)
