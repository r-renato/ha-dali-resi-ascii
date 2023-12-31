"""Support for DALI."""
from __future__ import annotations

import logging
from typing import cast

import voluptuous as vol

from homeassistant.core import HomeAssistant
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.typing import ConfigType

from homeassistant.components.light import (
    ColorMode,
    LightEntity,
)
from homeassistant.const import (
    CONF_ADDRESS,
    CONF_BINARY_SENSORS,
    CONF_COMMAND_OFF,
    CONF_COMMAND_ON,
    CONF_COUNT,
    CONF_COVERS,
    CONF_DELAY,
    CONF_DEVICE_CLASS,
    CONF_FRIENDLY_NAME,
    CONF_HOST,
    CONF_LIGHTS,
    CONF_METHOD,
    CONF_NAME,
    CONF_OFFSET,
    CONF_PORT,
    CONF_SCAN_INTERVAL,
    CONF_SENSORS,
    CONF_SLAVE,
    CONF_STRUCTURE,
    CONF_SWITCHES,
    CONF_TEMPERATURE_UNIT,
    CONF_TIMEOUT,
    CONF_TYPE,
    CONF_UNIQUE_ID,
    CONF_UNIT_OF_MEASUREMENT,
    CONF_ICON,
    CONF_MODE,
)

from .const import (
    DEFAULT_HUB,
    DALI_RESI_DOMAIN as DOMAIN,
    CONF_SWITCH_CONSTRAINT,
    CONF_DEVICE_ADDRESS,
    CONF_COLOR_MODE,
    CONF_LAZY_ERROR,
    DEFAULT_SCAN_INTERVAL,
    CONF_MSG_WAIT,
    TCP,
    UNKNOWN,
    ONOFF,
    BRIGHTNESS,
    COLOR_TEMP,
    HS,
    XY,
    RGB,
    RGBW,
    RGBWW,
    WHITE,
)

from .dali_resi_master import DALIHub, async_dali_setup

_LOGGER = logging.getLogger(__name__)

BASE_SCHEMA = vol.Schema({vol.Optional(CONF_NAME, default=DEFAULT_HUB): cv.string})

BASE_COMPONENT_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_NAME): cv.string,
        # vol.Required(CONF_ADDRESS): cv.positive_int,

        vol.Optional(CONF_SWITCH_CONSTRAINT): cv.string,

        vol.Exclusive(CONF_DEVICE_ADDRESS, "slave_addr"): cv.positive_int,
        vol.Exclusive(CONF_SLAVE, "slave_addr"): cv.positive_int,
        vol.Optional(
            CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL
        ): cv.positive_int,
        vol.Optional(CONF_LAZY_ERROR, default=0): cv.positive_int,
        vol.Optional(CONF_UNIQUE_ID): cv.string,
    }
)

LIGHT_SCHEMA = BASE_COMPONENT_SCHEMA.extend({
    vol.Required(CONF_COLOR_MODE, default=ONOFF): vol.Any(
        UNKNOWN,
        ONOFF,
        BRIGHTNESS,
        COLOR_TEMP,
        HS,
        XY,
        RGB,
        RGBW,
        RGBWW,
        WHITE,
    ),
})

DALI_SCHEMA = vol.Schema(
    {
        vol.Optional(CONF_NAME, default=DEFAULT_HUB): cv.string,
        vol.Optional(CONF_TIMEOUT, default=3): cv.socket_timeout,
        # vol.Optional(CONF_CLOSE_COMM_ON_ERROR): cv.boolean,
        vol.Optional(CONF_DELAY, default=0): cv.positive_int,
        # vol.Optional(CONF_RETRIES, default=3): cv.positive_int,
        # vol.Optional(CONF_RETRY_ON_EMPTY): cv.boolean,
        vol.Optional(CONF_MSG_WAIT): cv.positive_int,

        vol.Optional(CONF_LIGHTS): vol.All(cv.ensure_list, [LIGHT_SCHEMA]),
        # vol.Optional(CONF_SWITCHES): vol.All(cv.ensure_list, [SWITCH_SCHEMA]),
    }
)

ETHERNET_SCHEMA = DALI_SCHEMA.extend(
    {
        vol.Required(CONF_HOST): cv.string,
        vol.Required(CONF_PORT): cv.port,
        vol.Required(CONF_TYPE): vol.Any(TCP),
    }
)

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.All(
            cv.ensure_list,
            # scan_interval_validator,
            # duplicate_entity_validator,
            # duplicate_modbus_validator,
            [
                vol.Any(ETHERNET_SCHEMA),
            ],
        ),
    },
    extra=vol.ALLOW_EXTRA,
)

def get_hub(hass: HomeAssistant, name: str) -> DALIHub:
    """Return dali hub with name."""
    return cast(DALIHub, hass.data[DOMAIN][name])


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up dali component."""
    if DOMAIN not in config:
        return True
    return await async_dali_setup(
        hass,
        config,
    )


async def async_reset_platform(hass: HomeAssistant, integration_name: str) -> None:
    """Release dali resources."""
    _LOGGER.info("DALI reloading")
    hubs = hass.data[DOMAIN]
    for name in hubs:
        await hubs[name].async_close()