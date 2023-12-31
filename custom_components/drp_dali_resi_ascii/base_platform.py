"""Base implementation for all DALI platforms."""
from __future__ import annotations

import asyncio
from abc import abstractmethod
from collections.abc import Callable
from datetime import datetime, timedelta
import logging
import struct
from typing import Any, cast

from homeassistant.const import (
    CONF_ADDRESS,
    CONF_COMMAND_OFF,
    CONF_COMMAND_ON,
    CONF_COUNT,
    CONF_DELAY,
    CONF_DEVICE_CLASS,
    CONF_NAME,
    CONF_OFFSET,
    CONF_SCAN_INTERVAL,
    CONF_SLAVE,
    CONF_STRUCTURE,
    CONF_UNIQUE_ID,
    STATE_OFF,
    STATE_ON,
    EVENT_HOMEASSISTANT_START,
)
from homeassistant.core import HomeAssistant
from homeassistant.core import callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import Entity, ToggleEntity
from homeassistant.helpers.event import async_call_later, async_track_time_interval
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.helpers.event import (
    async_track_state_change_event
)
from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_COLOR_MODE,
    ATTR_COLOR_TEMP,
    ATTR_EFFECT,
    ATTR_EFFECT_LIST,
    ATTR_HS_COLOR,
    ATTR_MAX_MIREDS,
    ATTR_MIN_MIREDS,
    ATTR_RGB_COLOR,
    ATTR_RGBW_COLOR,
    ATTR_RGBWW_COLOR,
    ATTR_SUPPORTED_COLOR_MODES,
    ATTR_WHITE,
    ATTR_XY_COLOR,
    ENTITY_ID_FORMAT,
    ColorMode,
    LightEntity,
    LightEntityFeature,
    valid_supported_color_modes,
)

from .dali_resi_master import DALIHub
from .const import (
    ATTR_DALI_ADDRESS,
    ATTR_DALI_DEVICE,
    ATTR_DALI_CONTROL_GEAR,
    ATTR_DALI_LAMP_FAILURE,
    ATTR_DALI_LAMP_ARC_POWER_ON,
    ATTR_DALI_QUERY_LIMIT_ERROR,
    ATTR_DALI_FADE_RUNNING,
    ATTR_DALI_QUERY_RESET_STATE,
    ATTR_DALI_QUERY_MISSING_SHORT_ADDR,
    ATTR_DALI_QUERY_POWER_FAILURE,
    CONF_SWITCH_CONSTRAINT,
    CONF_COLOR_MODE,
    CONF_LAZY_ERROR,
    CONF_DEVICE_ADDRESS,
    SIGNAL_STOP_ENTITY,
    SIGNAL_START_ENTITY,
    DALI_RESI_DOMAIN as DOMAIN,
)
from .dali_const import (
    DONE,
    TIMEOUT,
    ERROR,
    NAME,
    TAG,
    DALICMD,
    ATTR_ACTUAL_LAMP_LEVEL,
    RECALL_MAX_LEVEL,
    QUERY_ACTUAL_LEVEL,
    QUERY_DEVICE_TYPE,
    QUERY_VERSION_NUMBER,
    OFF,
    ON,
)

PARALLEL_UPDATES = 1

_LOGGER = logging.getLogger(__name__)

class BasePlatform(Entity):
    """Base for readonly platforms."""

    def __init__(self, hub: DALIHub, entry: dict[str, Any]) -> None:
        """Initialize the DALI."""
        self._hub = hub
        self._config = entry
        self._slave = entry.get(CONF_SLAVE, None) or entry.get(CONF_DEVICE_ADDRESS, 0)
        # self._address = int(entry[CONF_ADDRESS])
        self._address = -1
        self._value: str | None = None
        self._scan_interval = int(entry[CONF_SCAN_INTERVAL])
        self._call_active = False
        self._cancel_timer: Callable[[], None] | None = None
        self._cancel_call: Callable[[], None] | None = None
        self._state_constraint = 'on'
        self._attr_unique_id = entry.get(CONF_UNIQUE_ID)
        self._attr_name = entry[CONF_NAME]
        self._attr_should_poll = False
        self._attr_device_class = entry.get(CONF_DEVICE_CLASS)
        self._attr_available = True
        self._attr_unit_of_measurement = None
        self._lazy_error_count = entry[CONF_LAZY_ERROR]
        self._lazy_errors = self._lazy_error_count

        self._switch_constraint = entry.get(CONF_SWITCH_CONSTRAINT, None)
        self._state_constraint = None

        self._extra_state_attr = {}
        self._attr_dali_device = None
        self._attr_dali_device_code = None
        self._attr_dali_status_control_gear = None
        self._attr_dali_lamp_failure = None
        self._attr_dali_lamp_arc_power_on = None
        self._attr_dali_query_limit_error = None
        self._attr_dali_fade_running = None
        self._attr_dali_query_reset_state = None
        self._attr_dali_query_missing_short_address = None
        self._attr_dali_query_power_failure = None

        def get_optional_numeric_config(config_name: str) -> int | float | None:
            if (val := entry.get(config_name)) is None:
                return None
            assert isinstance(
                val, (float, int)
            ), f"Expected float or int but {config_name} was {type(val)}"
            return val

        # self._min_value = get_optional_numeric_config(CONF_MIN_VALUE)
        # self._max_value = get_optional_numeric_config(CONF_MAX_VALUE)
        # self._nan_value = entry.get(CONF_NAN_VALUE, None)
        # self._zero_suppress = get_optional_numeric_config(CONF_ZERO_SUPPRESS)

        # _LOGGER.debug( '## scan_interval:%d', self._scan_interval )

    @abstractmethod
    async def async_update(self, now: datetime | None = None) -> None:
        """Virtual function to be overwritten."""

    @callback
    def async_run(self) -> None:
        """Remote start entity."""
        self.async_hold(update=False)
        self._cancel_call = async_call_later(
            self.hass, timedelta(milliseconds=100), self.async_update
        )
        if self._scan_interval > 0:
            self._cancel_timer = async_track_time_interval(
                self.hass, self.async_update, timedelta(seconds=self._scan_interval)
            )
        self._attr_available = True
        self.async_write_ha_state()

    @callback
    def async_hold(self, update: bool = True) -> None:
        """Remote stop entity."""
        if self._cancel_call:
            self._cancel_call()
            self._cancel_call = None
        if self._cancel_timer:
            self._cancel_timer()
            self._cancel_timer = None
        if update:
            self._attr_available = False
            self.async_write_ha_state()

    async def async_base_added_to_hass(self) -> None:
        """Handle entity which will be added."""
        self.async_run()
        self.async_on_remove(
            async_dispatcher_connect(self.hass, SIGNAL_STOP_ENTITY, self.async_hold)
        )
        self.async_on_remove(
            async_dispatcher_connect(self.hass, SIGNAL_START_ENTITY, self.async_run)
        )
        if self._switch_constraint:
            self.async_on_remove(
                async_track_state_change_event(self.hass, self._switch_constraint, self._async_component_changed)
            )
        self.hass.bus.async_listen_once(EVENT_HOMEASSISTANT_START, self._async_update_switch_constraint_status)

    async def _async_update_switch_constraint_status(self, event) -> None:
        """Handle entity which will be added."""
        if self._switch_constraint:
            self._old_state_constraint = self._state_constraint
            self._state_constraint = self.hass.states.get(self._switch_constraint).state

        # if not self._switch_constraint or self._state_constraint == 'on':
        #     response = await self._hub.async_dali_retrieve_device_type(self._slave)
        #     if DONE in response and response[DONE]:
        #         self._attr_dali_device_code = response[DALICMD[QUERY_DEVICE_TYPE][TAG]]
        #         self._attr_dali_device = response[DALICMD[QUERY_DEVICE_TYPE][TAG]+NAME]

        if self._state_constraint == 'on':
            self._attr_available = True

        self.async_write_ha_state()
        async_call_later(self.hass, 7, self.async_update)

        _LOGGER.debug( "#### _async_update_switch_constraint_status %s %s %s %s",
                str(self._switch_constraint), str(self._state_constraint), 
                str(self._attr_available), str(self._attr_dali_device_code)
        )

    async def _async_component_changed(self, event):
        """Handle sensor changes."""
        self._old_state_constraint = self._state_constraint
        new_state = event.data.get("new_state")
        self._state_constraint = new_state.state

        if self._state_constraint == 'on':
            self._attr_available = True
            self.async_write_ha_state()
            async_call_later(self.hass, 7, self.async_update)
        else:
            self._attr_available = False
            self.async_write_ha_state()

        _LOGGER.debug( '### async_component_changed: slave:%d, %s %s', 
                      self._slave, str(self._old_state_constraint), str(self._state_constraint) )

# await asyncio.sleep(self._msg_wait)

class BaseSwitch(BasePlatform, ToggleEntity, RestoreEntity):
    """Base class representing a DALI switch."""

    def __init__(
            self,
            hass: HomeAssistant,
            hub: DALIHub, 
            config: dict[str, Any]
        ) -> None:
        """Initialize the switch."""
        super().__init__(hub, config)
        
        self.hass = hass
        self._update_lock = asyncio.Lock()
        self._update_lock_flag = False

    async def async_added_to_hass(self) -> None:
        """Handle entity which will be added."""
        await self.async_base_added_to_hass()

        # if state := await self.async_get_last_state():
        #     if state.state == STATE_ON:
        #         self._attr_is_on = True
        #     elif state.state == STATE_OFF:
        #         self._attr_is_on = False
 
        self._attr_is_on = None

    async def _async_update_switch_constraint_status(self, event) -> None:
        """Handle entity which will be added."""
        await super()._async_update_switch_constraint_status(event)

    async def _async_lamp_status(self):
        result = { 'lamp': self._slave }

        # {'request': {'command': '#LAMP ', 'action': 'QUERY STATUS', 'params': ':18'}, 
        #  'response': '#OK:1,4,0x4', 'default': 4, 'done': True, 'statusControlGear': True, 'lampFailure': False, 
        #  'lampArcPowerOn': True, 'queryLimitError': False, 'fadeRunning': False, 'queryResetState': False, 
        #  'queryMissingShortAddress': False, 'queryPowerFailure': False }

        if self._attr_dali_device_code is None:
            response = await self._hub.async_dali_retrieve_device_type(self._slave)
            if DONE in response and response[DONE]:
                result['query_device_type'] = response[DALICMD[QUERY_DEVICE_TYPE][TAG]]
                result['query_device_typename'] = response[DALICMD[QUERY_DEVICE_TYPE][TAG]+NAME]


        status_response = await self._hub.async_dali_retrieve_device_status(self._slave)
        if DONE in status_response and status_response[DONE]:
            result.update(
                status_response['query_status']  
            )

        if self._attr_color_mode == ColorMode.ONOFF or self._attr_color_mode == ColorMode.BRIGHTNESS:
            actual_level_response = await self._hub.async_dali_retrieve_actual_level( self._attr_color_mode, self._slave )
            if (DONE in actual_level_response and actual_level_response[DONE]):
                result["brightness"] = actual_level_response["query_actual_level"]
    
        if self._attr_color_mode == ColorMode.COLOR_TEMP:
            actual_level_response = await self._hub.async_dali_retrieve_actual_level( self._attr_color_mode, self._slave )
            cw_ww_lamp_response = await self._hub.async_dali_20_dt8_retrieve_cw_ww_lamp(self._slave)
            if (DONE in cw_ww_lamp_response and cw_ww_lamp_response[DONE]):
                result["brightness"] = cw_ww_lamp_response['query_tc']["brightness"]
                # result["mirek"] = cw_ww_lamp_response['query_tc']["mirek"]
                result["kelvin"] = cw_ww_lamp_response['query_tc']["kelvin"]
            if (DONE in actual_level_response and actual_level_response[DONE]):
                result["brightness"] = actual_level_response['query_actual_level']

        if self._attr_color_mode == ColorMode.RGB:
            actual_level_response = await self._hub.async_dali_retrieve_actual_level( self._attr_color_mode, self._slave )
            rgb_response = await self._hub.async_dali_20_dt8_retrieve_rgb_lamp(self._slave)
            if (DONE in rgb_response and rgb_response[DONE]):
                result["rgb_color"] = [
                            int(rgb_response['red']), int(rgb_response['green']), int(rgb_response['blue'])
                        ]
                result["brightness"] = int(rgb_response['arc_level'])
            if (DONE in actual_level_response and actual_level_response[DONE]):
                result["brightness"] = actual_level_response['query_actual_level']
        
        if self._attr_color_mode == ColorMode.RGBWW:
            actual_level_response = await self._hub.async_dali_retrieve_actual_level( self._attr_color_mode, self._slave )
            rgbwaf_response = await self._hub.async_dali_20_dt8_retrieve_rgbww_lamp(self._slave)
            if (DONE in rgbwaf_response and rgbwaf_response[DONE]):
                result["rgbww_color"] = [
                            int(rgbwaf_response['red']), int(rgbwaf_response['green']), int(rgbwaf_response['blue']), 
                            int(rgbwaf_response['white']), int(rgbwaf_response['amber'])
                        ]
                result["brightness"] = int(rgbwaf_response['arc_level'])
            if (DONE in actual_level_response and actual_level_response[DONE]):
                result["brightness"] = actual_level_response['query_actual_level']

        _LOGGER.debug( "#### _async_lamp_status %s", str(result))
        return result

    async def async_update(self, now: datetime | None = None) -> None:
        """Update the entity state.""" 

        if self._update_lock_flag:
            return
        
        async with self._update_lock:
            self._update_lock_flag = True

            if self._switch_constraint and self._state_constraint != 'on':
                self._attr_available = False
                self._attr_native_value = None
                self._attr_is_on = None
                if self._coordinator:
                    self._coordinator.async_set_updated_data(None)
                self.async_write_ha_state()
                self._update_lock_flag = False
                return   
            
            lamp_status = await self._async_lamp_status()

            if lamp_status is None or not bool(lamp_status):
                self._attr_available = False
                self._attr_native_value = None
                self._attr_is_on = None
                if self._coordinator:
                    self._coordinator.async_set_updated_data(None)
                self.async_write_ha_state()
                self._update_lock_flag = False
                return 

            if ("statusControlGear" in lamp_status):
                self._attr_dali_status_control_gear = lamp_status['statusControlGear']
                self._attr_dali_lamp_failure = lamp_status['lampFailure']
                self._attr_dali_lamp_arc_power_on = lamp_status['lampArcPowerOn']
                self._attr_dali_query_limit_error = lamp_status['queryLimitError']
                self._attr_dali_fade_running = lamp_status['fadeRunning']
                self._attr_dali_query_reset_state = lamp_status['queryResetState']
                self._attr_dali_query_missing_short_address = lamp_status['queryMissingShortAddress']
                self._attr_dali_query_power_failure = lamp_status['queryPowerFailure']

            if ("brightness" in lamp_status): 
                self._attr_brightness = lamp_status["brightness"]

            if ("query_device_type" in lamp_status): 
                self._attr_dali_device_code = lamp_status["query_device_type"]
                self._attr_dali_device = lamp_status["query_device_typename"]

            # if self._attr_color_mode == ColorMode.ONOFF or self._attr_color_mode == ColorMode.BRIGHTNESS:
            #     self._attr_brightness = lamp_status["brightness"]

            if self._attr_color_mode == ColorMode.COLOR_TEMP and ("kelvin" in lamp_status):
                # self._attr_brightness = lamp_status["brightness"]
                self._attr_color_temp_kelvin = lamp_status["kelvin"]

            if self._attr_color_mode == ColorMode.RGBWW and ("rgbww_color" in lamp_status):
                # self._attr_brightness = lamp_status["brightness"]
                self._attr_rgbww_color = lamp_status["rgbww_color"]

            if self._attr_color_mode == ColorMode.RGB and ("rgb_color" in lamp_status):
                # self._attr_brightness = lamp_status["brightness"]
                self._attr_rgb_color = lamp_status["rgb_color"]

            if self._attr_brightness is not None and self._attr_brightness > 0:
                self._attr_is_on = True
                self._attr_native_value = True
            else:
                self._attr_is_on = False
                self._attr_native_value = False

            self._attr_available = True
            
            self.async_write_ha_state()
            self._update_lock_flag = False
            _LOGGER.debug( "#### async_update [%s], %s | %s %s", 
                          str(self._slave), str(self._attr_brightness), str(self._attr_is_on), str(self._attr_native_value))

    # async def async_turn(self, state: str) -> None:
    #     """Set switch on\off."""

    #     if state == ON:
    #         response = await self._hub.async_dali_recall_max_level(self._slave, self._attr_color_mode)
    #         if DONE in response and response[DONE]:
    #             self._attr_is_on = True
    #             self._attr_native_value = True
    #             # response = await self._hub.async_dali_1_lamp_answer(self._slave, QUERY_DEVICE_TYPE)
    #             # if DONE in response and response[DONE]:
    #             #     self._attr_dali_device_code = response['default']
    #             #     self._attr_dali_device = await self._hub.async_dali_decode_device_type(self._attr_dali_device_code)
    #             self.async_write_ha_state()
    #             await async_call_later(self.hass, 7, self.async_update)
    #     elif state == OFF:
    #         response = await self._hub.async_dali_recall_off(self._slave, OFF)
    #         if DONE in response and response[DONE]:
    #             self._attr_is_on = False
    #             self.async_write_ha_state()

    #     _LOGGER.debug( "#### async_turn %s, %s", str(state), str(response))
    #     return response

class BaseDALILight(BaseSwitch, LightEntity):
    """Class representing a DALI light."""

    def __init__(
        self,
        hass: HomeAssistant,
        hub: DALIHub,
        entry: dict[str, Any],
    ) -> None:
        """Initialize the modbus register sensor."""
        super().__init__(hass, hub, entry)

        self._attr_color_mode = entry[CONF_COLOR_MODE]
        supported_color_modes: set[ColorMode] = set()
        # supported_color_modes.add(ColorMode.ONOFF)
        # supported_color_modes.add(ColorMode.BRIGHTNESS)
        # supported_color_modes.add(ColorMode.COLOR_TEMP)
        # supported_color_modes.add(ColorMode.HS)
        # supported_color_modes.add(ColorMode.XY)
        # supported_color_modes.add(ColorMode.RGB)
        # supported_color_modes.add(ColorMode.RGBW)
        # supported_color_modes.add(ColorMode.RGBWW)

        # # Validate the color_modes configuration
        # self._attr_supported_color_modes = valid_supported_color_modes(
        #     supported_color_modes
        # )

        if ColorMode.ONOFF == self._attr_color_mode:
            supported_color_modes.add(ColorMode.ONOFF)
            self._attr_color_mode = ColorMode.ONOFF
        elif ColorMode.BRIGHTNESS == self._attr_color_mode:
            supported_color_modes.add(ColorMode.BRIGHTNESS)
        elif ColorMode.COLOR_TEMP == self._attr_color_mode:
            supported_color_modes.add(ColorMode.COLOR_TEMP)
            self._attr_min_color_temp_kelvin = 1000
            self._attr_max_color_temp_kelvin = 10000
        elif ColorMode.HS == self._attr_color_mode:
            supported_color_modes.add(ColorMode.HS)
        elif ColorMode.XY == self._attr_color_mode:
            supported_color_modes.add(ColorMode.XY)
        elif ColorMode.RGB == self._attr_color_mode:
            supported_color_modes.add(ColorMode.RGB)
        elif ColorMode.RGBW == self._attr_color_mode:
            supported_color_modes.add(ColorMode.RGBW)
        elif ColorMode.RGBWW == self._attr_color_mode:
            supported_color_modes.add(ColorMode.RGBWW)
        else:
            supported_color_modes.add(ColorMode.UNKNOWN)

        self._attr_supported_color_modes = supported_color_modes
        self._attr_supported_features = LightEntityFeature(0)

    async def async_set_temperature_color(self, temperature: int, kelvin: int) -> None:
        """Set switch on\off."""

        response = await self._hub.async_dali_20_dt8_cw_ww_lamp_command(self._slave, 255, kelvin)
        if DONE in response and response[DONE]:
            self._attr_color_temp_kelvin = kelvin
            self.async_write_ha_state()

    async def async_set_brightness(self, brightness: int) -> None:
        response = await self._hub.async_dali_1_arc_power(self._slave, brightness)
        if DONE in response and response[DONE]:
            self._attr_brightness = brightness
            self.async_write_ha_state()

        return response

    async def async_set_rgbww(
        self,
        level: int,
        red: int, 
        green: int, 
        blue: int, 
        white: int, 
        amber: int 
    ) -> None:
        """Set switch on\off."""

        response = await self._hub.async_dali_20_dt8_rgbwaf_channels_lamp_command(
            self._slave,
            level -1 if level == 255 else level, 
            red, green, blue, white, amber
        )
        if DONE in response and response[DONE]:
            self._attr_rgbww_color = (red,green,blue,white,amber)
            self.async_write_ha_state()

        return response
   
    # async def async_retrieve_dali_informations(self):
    #     if self._state_constraint == 'on':
    #         response = await self._hub.async_dali_1_lamp_answer(self._slave, QUERY_DEVICE_TYPE)
    #         if DONE in response and response[DONE]:
    #             self._attr_dali_device_code = response['default']
    #             self._attr_dali_device = await self._hub.async_dali_decode_device_type(self._attr_dali_device_code)
    #             _LOGGER.debug( '### async_retrieve_dali_informations: %s', str(response) )

    #         if self._attr_color_mode == ColorMode.RGBWW:
    #             response = await self._hub.async_dali_20_dt8_rgbwaf_channels_lamp_query(self._slave)
    #             _LOGGER.debug( '### async_retrieve_dali_informations: %s', str(response) )
    #             if DONE in response and response[DONE]:
    #                 self._attr_rgbww_color = [
    #                     int(response['red']), int(response['green']), int(response['blue']), 
    #                     int(response['white']), int(response['amber'])
    #                 ]
    #                 self.async_write_ha_state()
                    
    #         if self._attr_color_mode == ColorMode.RGB:
    #             response = await self._hub.async_dali_20_dt8_rgbwaf_channels_lamp_query(self._slave)
    #             _LOGGER.debug( '### async_retrieve_dali_informations: %s', str(response) )
    #             if DONE in response and response[DONE]:
    #                 self._attr_rgb_color = [
    #                     int(response['red']), int(response['green']), int(response['blue'])
    #                 ]
    #                 self.async_write_ha_state()

    @property
    def extra_state_attributes(self):
        """Return the state attributes of the device."""
        data: dict[str, Any] = { 
            ATTR_DALI_ADDRESS : self._slave 
        }

        if self._attr_dali_device:
            data[ ATTR_DALI_DEVICE ] = self._attr_dali_device

        if self._attr_dali_status_control_gear:
            data[ ATTR_DALI_CONTROL_GEAR ] = self._attr_dali_status_control_gear

        if self._attr_dali_lamp_failure:
            data[ ATTR_DALI_LAMP_FAILURE ] = self._attr_dali_lamp_failure

        if self._attr_dali_lamp_arc_power_on:
            data[ ATTR_DALI_LAMP_ARC_POWER_ON ] = self._attr_dali_lamp_arc_power_on

        if self._attr_dali_query_limit_error:
            data[ ATTR_DALI_QUERY_LIMIT_ERROR ] = self._attr_dali_query_limit_error

        if self._attr_dali_fade_running:
            data[ ATTR_DALI_FADE_RUNNING ] = self._attr_dali_fade_running

        if self._attr_dali_query_reset_state:
            data[ ATTR_DALI_QUERY_RESET_STATE ] = self._attr_dali_query_reset_state

        if self._attr_dali_query_missing_short_address:
            data[ ATTR_DALI_QUERY_MISSING_SHORT_ADDR ] = self._attr_dali_query_missing_short_address

        if self._attr_dali_query_power_failure:
            data[ ATTR_DALI_QUERY_POWER_FAILURE ] = self._attr_dali_query_power_failure

        return data 

