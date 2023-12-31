"""Support for DALI lights."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_COLOR_MODE,
    ATTR_COLOR_TEMP,
    ATTR_COLOR_TEMP_KELVIN,
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
from homeassistant.const import CONF_LIGHTS, CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
from homeassistant.helpers.event import (
    async_track_state_change_event,
    async_call_later,
    async_track_time_interval
)
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from . import get_hub
from .base_platform import BaseDALILight
from .dali_resi_master import DALIHub
from .const import (
    CONF_SWITCH_CONSTRAINT,
    CONF_COLOR_MODE,
    DALI_RESI_DOMAIN as DOMAIN,
    ATTR_DALI_ADDRESS,
    ATTR_DALI_DEVICE,
)
from .dali_const import (
    DONE,
    OFF,
    ON,
)

PARALLEL_UPDATES = 1

_LOGGER = logging.getLogger(__name__)

async def async_setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    async_add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Read configuration and create DALI lights."""
    if discovery_info is None:
        return

    lights = []
    for entry in discovery_info[CONF_LIGHTS]:
        hub: DALIHub = get_hub(hass, discovery_info[CONF_NAME])
        lights.append(DALILight(hass, hub, entry))
    async_add_entities(lights)


class DALILight(BaseDALILight):
    """Class representing a DALI light."""

    def __init__(
        self,
        hass: HomeAssistant,
        hub: DALIHub,
        entry: dict[str, Any],
    ) -> None:
        """Initialize the modbus register sensor."""
        super().__init__(hass, hub, entry)

        self._coordinator: DataUpdateCoordinator[list[int] | None] | None = None

        _LOGGER.debug( "#### __init__ %s %s - %s %s", 
                      self._attr_color_mode, self.color_mode, 
                      str(self._attr_supported_color_modes), str(self._light_internal_supported_color_modes))

    # async def async_added_to_hass(self) -> None:
    #     """Handle entity which will be added."""
    #     await self.async_base_added_to_hass()

    #     await self.async_retrieve_dali_informations()

    #     # state = await self.async_get_last_sensor_data()
    #     # if state:
    #     #     self._attr_native_value = state.native_value

    #     if self._switch_constraint:
    #         self.async_on_remove(
    #                 async_track_state_change_event(
    #                     self.hass, self._switch_constraint, self._async_component_changed
    #                 )
    #         )
    #         _LOGGER.debug( '### async_added_to_hass: %s', str(self._switch_constraint) )

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Set light on."""
        response = {}

        _LOGGER.debug( "#### async_turn_on %s | %s", str(kwargs), str(response))
        if len(kwargs) == 0:
            max_level_response = await self._hub.async_dali_recall_max_level(self._attr_color_mode, self._slave)
            # _LOGGER.debug( "#### async_turn_on %s %s", str(kwargs), str(max_level_response))
            if DONE in max_level_response and max_level_response[DONE]:
                self._attr_is_on = True
                self._attr_native_value = True
                if "query_actual_level" in max_level_response:
                    self._attr_brightness = max_level_response["query_actual_level"]
                self.async_write_ha_state()
        #
        if ATTR_BRIGHTNESS in kwargs:
            brightness = self._attr_brightness
            brightness_response = await self._hub.async_dali_recall_level(
                self._attr_dali_device_code, self._attr_color_mode, self._slave, kwargs['brightness']
            )
            # _LOGGER.debug( "#### async_turn_on %s %s", str(kwargs), str(brightness_response))
            if DONE in brightness_response and brightness_response[DONE]:
                self._attr_brightness = kwargs['brightness']
            else:
                self._attr_brightness = brightness

            if self._attr_brightness > 0:
                self._attr_is_on = True
                self._attr_native_value = True
            else:
                self._attr_is_on = False
                self._attr_native_value = False
            self.async_write_ha_state()

        if ATTR_COLOR_TEMP in kwargs and ATTR_COLOR_TEMP_KELVIN in kwargs:
            # {'color_temp': 234, 'color_temp_kelvin': 4265}
            color_temp_kelvin = self._attr_color_temp_kelvin
            brightness = kwargs['brightness'] if ATTR_BRIGHTNESS in kwargs else None
            color_temp_response = await self._hub.async_dali_recall_color_temperature_level(
                self._attr_dali_device_code, self._attr_color_mode,
                self._slave, brightness, kwargs['color_temp_kelvin']
            )
            if DONE in color_temp_response and color_temp_response[DONE]:
                self._attr_color_temp_kelvin = kwargs['color_temp_kelvin']
            else:
                self._attr_color_temp_kelvin = color_temp_kelvin
            self.async_write_ha_state()

        if ATTR_RGB_COLOR in kwargs:
            # {'rgb_color': (255, 136, 13)}
            rgb_color = self._attr_rgb_color
            brightness = kwargs['brightness'] if ATTR_BRIGHTNESS in kwargs else None
            rgb = kwargs['rgb_color']
            rgb_response = await self._hub.async_dali_recall_rgb_level(
                self._attr_dali_device_code, self._attr_color_mode,
                self._slave, brightness, rgb[0], rgb[1], rgb[2]
            )
            if DONE in rgb_response and rgb_response[DONE]:
                self._attr_rgb_color = [rgb[0], rgb[1], rgb[2]]
            else:
                self._attr_rgb_color = rgb_color
            self.async_write_ha_state()

        if ATTR_RGBWW_COLOR in kwargs:
            # {'rgbww_color': (255, 130, 0, 33, 33)}
            rgbww_color = self._attr_rgbww_color
            brightness = kwargs['brightness'] if ATTR_BRIGHTNESS in kwargs else None
            rgbww = kwargs['rgbww_color']
            rgbww_response = await self._hub.async_dali_recall_rgbww_level(
                self._attr_dali_device_code, self._attr_color_mode,
                self._slave, brightness, rgbww[0], rgbww[1], rgbww[2], rgbww[3], rgbww[4]
            )
            if DONE in rgbww_response and rgbww_response[DONE]:
                self._attr_rgbww_color = [rgbww[0], rgbww[1], rgbww[2], rgbww[3], rgbww[4]]
            else:
                self._attr_rgbww_color = rgbww_color
            self.async_write_ha_state()        

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Set light on."""

        response = await self._hub.async_dali_recall_off(self._attr_dali_device_code, self._attr_color_mode, self._slave)
        if DONE in response and response[DONE]:
            self._attr_is_on = False
            self._attr_native_value = False
            self.async_write_ha_state()

        _LOGGER.debug( "#### async_turn_off %s %s", str(**kwargs), str(response))
    