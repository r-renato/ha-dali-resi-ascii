"""Constants used in dali integration."""
from enum import Enum
from enum import StrEnum

from homeassistant.const import (
    CONF_LIGHTS,
    CONF_SWITCHES,
    Platform,
)

DALI_RESI_DOMAIN = "drp_dali_resi_ascii"

CONF_SWITCH_CONSTRAINT = "switch_constraint"
CONF_DEVICE_ADDRESS = "device_address"
CONF_COLOR_MODE = "color_mode"
CONF_LAZY_ERROR = "lazy_error_count"
CONF_MSG_WAIT = "message_wait_milliseconds"

DEFAULT_HUB = "dalihub"
DEFAULT_SCAN_INTERVAL = 30  # seconds

# service call attributes
ATTR_HUB = "hub"

ATTR_DALI_ADDRESS = "dali_address"
ATTR_DALI_DEVICE = "dali_device"
ATTR_DALI_CONTROL_GEAR = "control_gear"
ATTR_DALI_LAMP_FAILURE = "lamp_failure"
ATTR_DALI_LAMP_ARC_POWER_ON = "lamp_arc_power_on"
ATTR_DALI_QUERY_LIMIT_ERROR = "query_limit_error"
ATTR_DALI_FADE_RUNNING = "fade_running"
ATTR_DALI_QUERY_RESET_STATE = "query_reset_state"
ATTR_DALI_QUERY_MISSING_SHORT_ADDR = "query_missing_short_addr"
ATTR_DALI_QUERY_POWER_FAILURE = "query_power_failure"

TCP = "tcp"

UNKNOWN = "unknown"
# """Ambiguous color mode"""
ONOFF = "onoff"
# """Must be the only supported mode"""
BRIGHTNESS = "brightness"
# """Must be the only supported mode"""
COLOR_TEMP = "color_temp"
HS = "hs"
XY = "xy"
RGB = "rgb"
RGBW = "rgbw"
RGBWW = "rgbww"
WHITE = "white"

# service calls
SERVICE_STOP = "stop"
SERVICE_RESTART = "restart"

# dispatcher signals
SIGNAL_STOP_ENTITY = "dali.stop"
SIGNAL_START_ENTITY = "dali.start"

PLATFORMS = (
    (Platform.LIGHT, CONF_LIGHTS),
    (Platform.SWITCH, CONF_SWITCHES),
)


class DALIActionModel(str, Enum):
    """..."""

    LAMP = "lamp"
    GROUP = "group"
    ALL = "all"

class DALICommandNames(str, Enum):

    LAMP_LEVEL = "LAMP LEVEL"

DALI_COMMANDS = {
    Platform.LIGHT : {
        DALIActionModel.LAMP : {

        }
    }
}
