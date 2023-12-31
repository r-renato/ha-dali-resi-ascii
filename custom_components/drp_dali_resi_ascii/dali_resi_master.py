"""Support for DALI."""
from __future__ import annotations

import asyncio
from collections import namedtuple
from collections.abc import Callable
from typing import Any

import telnetlib  # pylint: disable=deprecated-module
import telnetlib3
import logging

import voluptuous as vol

from homeassistant.core import Event, HomeAssistant, ServiceCall, callback

import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.discovery import async_load_platform
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.event import async_call_later
from homeassistant.helpers.reload import async_setup_reload_service
from homeassistant.helpers.typing import ConfigType

from homeassistant.components.light import (
    ColorMode
)

from homeassistant.const import (
    ATTR_STATE,
    CONF_DELAY,
    CONF_HOST,
    CONF_METHOD,
    CONF_NAME,
    CONF_PORT,
    CONF_TIMEOUT,
    CONF_TYPE,
    EVENT_HOMEASSISTANT_STOP,
)

from .const import (
    ATTR_HUB,
    CONF_MSG_WAIT,
    DALI_RESI_DOMAIN as DOMAIN,
    SERVICE_STOP,
    SERVICE_RESTART,
    SIGNAL_STOP_ENTITY,
    SIGNAL_START_ENTITY,
    PLATFORMS,
)

from .dali_const import (
    TAG,
    RESICMD,
    DALICMD,
    DALI_DEVICE_TYPES,
    DONE,
    ERROR,
    ERR9,
    ERR99,
    TIMEOUT,
    DALI_RESP_OK,
    DALI_RESP_ERR,
    DALI_RESP_LQTC,
    DALI_RESP_LQRGBWAF,
    OFF,
    OK,
    NAME,
    OPCODE,
    RECALL_MAX_LEVEL,
    LAMP,
    LAMP_OFF,
    LAMP_ARC_POWER,
    LAMP_LEVEL,
    LAMP_COMMAND,
    LAMP_COMMAND_REPEAT,
    LAMP_COMMAND_ANSWER,
    LAMP_RGBWAF,
    LAMP_QUERY_RGBWAF,
    LAMP_TC_KELVIN,
    LAMP_QUERY_TC,
    QUERY_STATUS,
    QUERY_ACTUAL_LEVEL,
    QUERY_DEVICE_TYPE,
    QUERY_CONTROL_GEAR_PRESENT,
    QUERY_POWER_ON_LEVEL,
    QUERY_SYSTEM_FAILURE_LEVEL,
    QUERY_FADE_TIME_FADE_RATE,
    QUERY_PHYSICAL_MINIMUM,
    QUERY_MIN_LEVEL,
    QUERY_MAX_LEVEL,
    DT8_SET_COLOUR_TEMPERATURE_TC,
    DT8_SET_PRIMARY_N_DIMLEVEL,
    RESIRESP,
)

_LOGGER = logging.getLogger(__name__)

async def async_dali_setup(
    hass: HomeAssistant,
    config: ConfigType,
) -> bool:
    """Set up DALI component."""

    await async_setup_reload_service(hass, DOMAIN, [DOMAIN])

    if DOMAIN in hass.data and config[DOMAIN] == []:
        hubs = hass.data[DOMAIN]
        for name in hubs:
            if not await hubs[name].async_setup():
                return False
        hub_collect = hass.data[DOMAIN]
    else:
        hass.data[DOMAIN] = hub_collect = {}

    for conf_hub in config[DOMAIN]:
        my_hub = DALIHub(hass, conf_hub)
        hub_collect[conf_hub[CONF_NAME]] = my_hub

        # dali needs to be activated before components are loaded
        # to avoid a racing problem
        if not await my_hub.async_setup():
            return False

        # load platforms
        for component, conf_key in PLATFORMS:
            if conf_key in conf_hub:
                hass.async_create_task(
                    async_load_platform(hass, component, DOMAIN, conf_hub, config)
                )

    async def async_stop_dali(event: Event) -> None:
        """Stop dali service."""

        async_dispatcher_send(hass, SIGNAL_STOP_ENTITY)
        for client in hub_collect.values():
            await client.async_close()

    hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, async_stop_dali)

    # async def async_write_register(service: ServiceCall) -> None:
    #     """Write dali registers."""
    #     slave = 0
    #     if ATTR_UNIT in service.data:
    #         slave = int(float(service.data[ATTR_UNIT]))

    #     if ATTR_SLAVE in service.data:
    #         slave = int(float(service.data[ATTR_SLAVE]))
    #     address = int(float(service.data[ATTR_ADDRESS]))
    #     value = service.data[ATTR_VALUE]
    #     hub = hub_collect[
    #         service.data[ATTR_HUB] if ATTR_HUB in service.data else DEFAULT_HUB
    #     ]

    #     _LOGGER.debug( '### async_write_register slave:%d, address:%d, value:%s', 
    #          slave, address, str(value) )
    #     if isinstance(value, list):
    #         await hub.async_pb_call(
    #             slave,
    #             address,
    #             [int(float(i)) for i in value],
    #             CALL_TYPE_WRITE_REGISTERS,
    #         )
    #     else:
    #         await hub.async_pb_call(
    #             slave, address, int(float(value)), CALL_TYPE_WRITE_REGISTER
    #         )

    # async def async_write_coil(service: ServiceCall) -> None:
    #     """Write dali coil."""
    #     slave = 0
    #     if ATTR_UNIT in service.data:
    #         slave = int(float(service.data[ATTR_UNIT]))
    #     if ATTR_SLAVE in service.data:
    #         slave = int(float(service.data[ATTR_SLAVE]))
    #     address = service.data[ATTR_ADDRESS]
    #     state = service.data[ATTR_STATE]
    #     hub = hub_collect[
    #         service.data[ATTR_HUB] if ATTR_HUB in service.data else DEFAULT_HUB
    #     ]
    #     if isinstance(state, list):
    #         await hub.async_pb_call(slave, address, state, CALL_TYPE_WRITE_COILS)
    #     else:
    #         await hub.async_pb_call(slave, address, state, CALL_TYPE_WRITE_COIL)

    # for x_write in (
    #     (SERVICE_WRITE_REGISTER, async_write_register, ATTR_VALUE, cv.positive_int),
    #     (SERVICE_WRITE_COIL, async_write_coil, ATTR_STATE, cv.boolean),
    # ):
    #     hass.services.async_register(
    #         DOMAIN,
    #         x_write[0],
    #         x_write[1],
    #         schema=vol.Schema(
    #             {
    #                 vol.Optional(ATTR_HUB, default=DEFAULT_HUB): cv.string,
    #                 vol.Exclusive(ATTR_SLAVE, "unit"): cv.positive_int,
    #                 vol.Exclusive(ATTR_UNIT, "unit"): cv.positive_int,
    #                 vol.Required(ATTR_ADDRESS): cv.positive_int,
    #                 vol.Required(x_write[2]): vol.Any(
    #                     cv.positive_int, vol.All(cv.ensure_list, [x_write[3]])
    #                 ),
    #             }
    #         ),
    #     )

    async def async_stop_hub(service: ServiceCall) -> None:
        """Stop dali hub."""
        async_dispatcher_send(hass, SIGNAL_STOP_ENTITY)
        hub = hub_collect[service.data[ATTR_HUB]]
        await hub.async_close()

    async def async_restart_hub(service: ServiceCall) -> None:
        """Restart dali hub."""
        async_dispatcher_send(hass, SIGNAL_START_ENTITY)
        hub = hub_collect[service.data[ATTR_HUB]]
        await hub.async_restart()

    for x_service in (
        (SERVICE_STOP, async_stop_hub),
        (SERVICE_RESTART, async_restart_hub),
    ):
        hass.services.async_register(
            DOMAIN,
            x_service[0],
            x_service[1],
            schema=vol.Schema({vol.Required(ATTR_HUB): cv.string}),
        )
    return True

class DALIRESIClient3:
    """Thread safe wrapper class for telnetlib."""
    """Thread safe wrapper class for telnetlib."""

    def __init__(
            self,
            hass: HomeAssistant, 
            config: dict[str, Any]
    ) -> None:
        self.hass = hass
        self.name = config[CONF_NAME]
        self._pb_params = {
            "host": config[CONF_HOST],
            "port": config[CONF_PORT],
            # "timeout": config[CONF_TIMEOUT],
        }
        self._msg_wait = config.get(CONF_MSG_WAIT, None)
        self._config_delay = config[CONF_DELAY]

        # generic configuration
        self._lock = asyncio.Lock()
        self._async_cancel_listener: Callable[[], None] | None = None
        self._in_error = False
        self._client_reader = None
        self._client_writer = None

        # self._client = telnetlib.Telnet()
        self._msg_read_timeout = 5

    async def async_setup(self) -> bool:
        """Set up telnetlib client."""
        # try:
        #     # _LOGGER.debug( "_pb_params: %s", str(self._pb_params ))
        #     self._client = telnetlib.Telnet(**self._pb_params)
        # except Exception as exception_error:
        #     self._log_error(str(exception_error), error_state=False)
        #     return False

        # for entry in PB_CALL:
        #     func = getattr(self._client, entry.func_name)
        #     self._pb_request[entry.call_type] = RunEntry(entry.attr, func)

        self.hass.async_create_background_task(
            self.async_pb_connect(), "dali-connect"
        )

        # Start counting down to allow dali requests.
        if self._config_delay:
            self._async_cancel_listener = async_call_later(
                self.hass, self._config_delay, self.async_end_delay
            )
        return True
    
    async def async_restart(self) -> None:
        """Reconnect client."""
        if self._client:
            await self.async_close()

        await self.async_setup()

    @callback
    def async_end_delay(self, args: Any) -> None:
        """End startup delay."""
        self._async_cancel_listener = None
        self._config_delay = 0

    def _log_error(self, text: str, error_state: bool = True) -> None:
        log_text = f"dali: {self.name}: {text}"
        if self._in_error:
            _LOGGER.debug(log_text)
        else:
            _LOGGER.error(log_text)
            self._in_error = error_state

    async def async_close(self) -> None:
        """Disconnect client."""
        if self._async_cancel_listener:
            self._async_cancel_listener()
            self._async_cancel_listener = None

        async with self._lock:
            if self._client_writer:
                try:
                    self._client_writer.close()
                except Exception as exception_error:
                    self._log_error(str(exception_error))
                del self._client_writer
                self._client_writer = None
                message = f"dali {self.name} writer communication closed"
                _LOGGER.warning(message)
            if self._client_reader:
                try:
                    self._client_reader.close()
                except Exception as exception_error:
                    self._log_error(str(exception_error))
                del self._client_reader
                self._client_reader = None
                message = f"dali {self.name} reader communication closed"
                _LOGGER.warning(message)

    async def async_pb_connect(self) -> bool:
        """Connect client."""
        async with self._lock:
            try:
                self._client_reader, self._client_writer = await telnetlib3.open_connection(**self._pb_params)
                # self._client.open(**self._pb_params)  # type: ignore[union-attr]
            except Exception as exception_error:
                self._log_error(str(exception_error), error_state=False)
                return False

            message = f"dali {self.name} communication open"
            _LOGGER.info(message)
            return True

    # async def async_pb_connect(self) -> None:
    #     """Connect to device, async."""
    #     async with self._lock:
    #         if not await self.hass.async_add_executor_job(self.pb_connect):
    #             err = f"{self.name} connect failed, retry in dali-resi"
    #             self._log_error(err, error_state=False)

    # def pb_call(
    #     self, command: str
    # ) -> str | None:
    #     """Call sync. telnetlib."""
    #     line = None
    #     try:
    #         # cmd = command.encode('ascii') + b"\r\n"
    #         # # cmd = "\r" + command + "\r"
    #         # _LOGGER.debug( '### pb_call command: |%s|', cmd )
    #         self._client.write( b"\r" + b"\r" + b"\r" +b"\r" + b"\n")
    #         # self._client.write( b"\r" )
    #         # asyncio.sleep(0.1)
    #         # self._client.write( b"\r" )
    #         # asyncio.sleep(0.1)
    #         # self._client.write( b"\r" )
    #         # asyncio.sleep(0.1)
    #         self._client.write( b"\r" + b"\r" + b"\r" +b"\r" + b"\n" + command.encode('ascii') + b"\r" + b"\n" )
    #         line = self._client.read_until(b"\r", self._msg_read_timeout).decode('ascii').rstrip()

    #         _LOGGER.debug( '### pb_call command: %s %s | result: %s', command, command.encode('ascii'), line )
    #     except Exception as exception_error:
    #         self._log_error(str(exception_error))
    #         return None
        
    #     return line
    
    async def async_pb_call(
        self, 
        request: any, 
    ) -> str | None:
        """Convert async to sync dali call."""

        # _LOGGER.debug( '### async_pb_call request: %s', str(request) )

        command = request["command"]

        async with self._lock:
            if not self._client_reader:
                return None   

            if self._msg_wait:
                # small delay until next request/response
                await asyncio.sleep(self._msg_wait) 

            try:
                result = (await asyncio.wait_for(self._client_reader.read(), timeout=0.5))
            except asyncio.exceptions.TimeoutError as e:
                result = ''

            # await asyncio.sleep(0.2)
            self._client_writer.write("\r\r\r\r")
            await asyncio.sleep(0.1)
            self._client_writer.write(command)
            await asyncio.sleep(0.2)
            self._client_writer.write("\r")
            try:
                result = (await asyncio.wait_for(self._client_reader.readuntil(separator=b'\r'), timeout=5)).decode().rstrip()
            except asyncio.exceptions.TimeoutError as e:
                result = ''

            # result = await self.hass.async_add_executor_job(
            #     self.pb_call, command
            # )

            if result is None:
                _LOGGER.warning( 'DALI Master integration %s restart', self.name )
                await self.async_restart()

                
            # _LOGGER.debug( '### async_pb_call command {%s} response {%s}', command, result)
            return result

class DALIRESIClient:
    """Thread safe wrapper class for telnetlib."""

    def __init__(
            self,
            hass: HomeAssistant, 
            config: dict[str, Any]
    ) -> None:
        self.hass = hass
        self.name = config[CONF_NAME]
        self._pb_params = {
            "host": config[CONF_HOST],
            "port": config[CONF_PORT],
            "timeout": config[CONF_TIMEOUT],
        }
        self._msg_wait = config.get(CONF_MSG_WAIT, 1.5)
        self._config_delay = config[CONF_DELAY]

        # generic configuration
        self._lock = asyncio.Lock()
        self._async_cancel_listener: Callable[[], None] | None = None
        self._in_error = False
        self._client = telnetlib.Telnet()
        self._msg_read_timeout = 5

    async def async_setup(self) -> bool:
        """Set up telnetlib client."""
        try:
            # _LOGGER.debug( "_pb_params: %s", str(self._pb_params ))
            self._client = telnetlib.Telnet(**self._pb_params)
        except Exception as exception_error:
            self._log_error(str(exception_error), error_state=False)
            return False

        # for entry in PB_CALL:
        #     func = getattr(self._client, entry.func_name)
        #     self._pb_request[entry.call_type] = RunEntry(entry.attr, func)

        self.hass.async_create_background_task(
            self.async_pb_connect(), "dali-connect"
        )

        # Start counting down to allow dali requests.
        if self._config_delay:
            self._async_cancel_listener = async_call_later(
                self.hass, self._config_delay, self.async_end_delay
            )
        return True
    
    async def async_restart(self) -> None:
        """Reconnect client."""
        if self._client:
            await self.async_close()

        await self.async_setup()

    @callback
    def async_end_delay(self, args: Any) -> None:
        """End startup delay."""
        self._async_cancel_listener = None
        self._config_delay = 0

    def _log_error(self, text: str, error_state: bool = True) -> None:
        log_text = f"dali: {self.name}: {text}"
        if self._in_error:
            _LOGGER.debug(log_text)
        else:
            _LOGGER.error(log_text)
            self._in_error = error_state

    async def async_close(self) -> None:
        """Disconnect client."""
        if self._async_cancel_listener:
            self._async_cancel_listener()
            self._async_cancel_listener = None

        async with self._lock:
            if self._client:
                try:
                    self._client.close()
                except Exception as exception_error:
                    self._log_error(str(exception_error))
                del self._client
                self._client = None
                message = f"dali {self.name} communication closed"
                _LOGGER.warning(message)

    def pb_connect(self) -> bool:
        """Connect client."""
        try:
            self._client.open(**self._pb_params)  # type: ignore[union-attr]
        except Exception as exception_error:
            self._log_error(str(exception_error), error_state=False)
            return False

        message = f"dali {self.name} communication open"
        _LOGGER.info(message)
        return True

    async def async_pb_connect(self) -> None:
        """Connect to device, async."""
        async with self._lock:
            if not await self.hass.async_add_executor_job(self.pb_connect):
                err = f"{self.name} connect failed, retry in dali-resi"
                self._log_error(err, error_state=False)

    def pb_call(
        self, command: str
    ) -> str | None:
        """Call sync. telnetlib."""
        line = None
        try:
            # cmd = command.encode('ascii') + b"\r\n"
            # # cmd = "\r" + command + "\r"
            # _LOGGER.debug( '### pb_call command: |%s|', cmd )
            self._client.write( b"\r" + b"\r" + b"\r" +b"\r" + b"\n")
            # self._client.write( b"\r" )
            # asyncio.sleep(0.1)
            # self._client.write( b"\r" )
            # asyncio.sleep(0.1)
            # self._client.write( b"\r" )
            # asyncio.sleep(0.1)
            self._client.write( b"\r" + b"\r" + b"\r" +b"\r" + b"\n" + command.encode('ascii') + b"\r" + b"\n" )
            line = self._client.read_until(b"\r", self._msg_read_timeout).decode('ascii').rstrip()

            _LOGGER.debug( '### pb_call command: %s %s | result: %s', command, command.encode('ascii'), line )
        except Exception as exception_error:
            self._log_error(str(exception_error))
            return None
        
        return line
    
    async def async_pb_call(
        self, 
        request: any, 
    ) -> str | None:
        """Convert async to sync dali call."""

        # _LOGGER.debug( '### async_pb_call request: %s', str(request) )

        command = request["command"]

        async with self._lock:
            if not self._client:
                return None   

            if self._msg_wait:
                # small delay until next request/response
                await asyncio.sleep(self._msg_wait) 

            result = await self.hass.async_add_executor_job(
                self.pb_call, command
            )

            if result is None:
                _LOGGER.warning( 'DALI Master integration %s restart', self.name )
                await self.async_restart()

                
            # _LOGGER.debug( '### async_pb_call command {%s} response {%s}', command, result)
            return result

class DALIRESIMaster(DALIRESIClient3):
        
    async def async_decode_default_response( 
        self,
        prefix : str, 
        suffix : str,
        tag : str,
    ):
        result : any = { }
        data = ['', DALI_RESP_OK]

        if suffix is not None:
            data = suffix.split( ',' )
            isError = (len(data) == 3 and data[ 0 ] == '9' and data[ 1 ] == '99' and data[ 2 ] == '0x63')
        else:
            isError = False

        _LOGGER.debug( "#### async_decode_default_response %s %s %s | %s", str(prefix),  str(suffix), str(tag), str(data))
        if DALI_RESP_OK == prefix and not isError:
            code = int( data[ 0 ] ) if (data[ 0 ]).isnumeric() else data[ 0 ]
            resp = int( data[ 1 ] ) if (data[ 1 ]).isnumeric() else data[ 1 ]
            
            result[ tag ] = resp
            result[DONE] = True
        else:
            result[ERROR] = True

        return result
    
    async def async_decode_query_status_resp(
        self,
        prefix: str, 
        suffix: str,
        tag: str
    ):
        _LOGGER.debug( "#### async_decode_query_status_resp %s %s %s", str(prefix),  str(suffix), str(tag))
        result = { } 
        data = suffix.split( ',' ) 
        code = int( data[ 0 ] )
        resp = int( data[ 1 ] )

        if DALI_RESP_OK == prefix and code == 1:
            result[tag] = {
                # /* Note STATUS INFORMATION: 8-bit data indicating the status of a slave.
                #    The meanings of the bits are as follows:
                #       Bit 0: Status of control gear 0=OK
                #       Bit 1: Lamp failure 0=OK
                #       Bit 2: Lamp arc power on 0=OFF 1=ON
                #       Bit 3: Limit Error 0=Actual level is between MIN and MAX or OFF
                #       Bit 4: Fade running 0=Fading is finished 1=Fading is active
                #       Bit 5: RESET STATE 0=OK
                #       Bit 6: Missing short address 0=No 1=Yes
                #       Bit 7: POWER FAILURE 0=No
                # */
                "statusControlGear" : (resp >> 0 & 1) == 0,         # Bit 0: Status of control gear 0=OK
                "lampFailure" : (resp >> 1 & 1) == 1,               # Bit 1: Lamp failure 0=OK
                "lampArcPowerOn" : (resp >> 2 & 1) == 1,            # Bit 2: Lamp arc power on 0=OFF 1=ON
                "queryLimitError" : (resp >> 3 & 1) == 1,           # Bit 3: Limit Error 0=Actual level is between MIN and MAX or OFF
                "fadeRunning" : (resp >> 4 & 1) == 1,               # Bit 4: Fade running 0=Fading is finished 1=Fading is active
                "queryResetState" : (resp >> 5 & 1) == 1,           # Bit 5: RESET STATE 0=OK
                "queryMissingShortAddress" : (resp >> 6 & 1) == 1,  # Bit 6: Missing short address 0=No 1=Yes
                "queryPowerFailure" : (resp >> 7 & 1) == 1,         # Bit 7: POWER FAILURE 0=No
            }
            result[DONE] = True
        else:
            result[ERROR] = True
    
        return result
    
    async def async_decode_rgbwaf_query_response(
        self,
        prefix: str, 
        suffix: str,
        tag: str
    ):
        # #LQRGBWAF:6,50,0,196,0,0,0
        #           0 1  2   3   4   5   6
        # #LQRGBWAF:7,0,255,252,253,112,255
        # #LQRGBWAF:ERR
        result : any = { }

        if DALI_RESP_LQRGBWAF == prefix and DALI_RESP_ERR != suffix:
            respTokenized = suffix.split( ',' )
            if len(respTokenized) > 0:
                result["lamp"] = int(respTokenized[0])
            if len(respTokenized) > 1:
                result["arc_level"] = int(respTokenized[1])
            if len(respTokenized) > 2:
                result["red"] = int(respTokenized[2])
            if len(respTokenized) > 3:
                result["green"] = int(respTokenized[3])
            if len(respTokenized) > 4:
                result["blue"] = int(respTokenized[4])
            if len(respTokenized) > 5:
                result["white"] = int(respTokenized[5])
            if len(respTokenized) > 6:
                result["amber"] = int(respTokenized[6])
            
            if (result["arc_level"] >= 0 and result["arc_level"]<= 254):
                result[DONE] = True
            else:
                result[ERROR] = True
        else:
            result[ERROR] = True

        return result
    
    async def async_decode_tc_query_response(
        self,
        prefix: str, 
        suffix: str,
        tag: str
    ):
        # #LQTC:30,43269,0x010D,3717.472
        result : any = { }

        if DALI_RESP_LQTC == prefix and DALI_RESP_ERR != suffix:
            respTokenized = suffix.split( ',' )
            
            result["lamp"] = int(respTokenized[0])          
            # result["mirek"] = int(respTokenized[2], 16)
            result["kelvin"] = float(respTokenized[3])
            
            if (int(respTokenized[1]) >= 0 and int(respTokenized[1])<= 254):
                result["brightness"] = int(respTokenized[1])

            if (result["kelvin"] >= 16 and result["kelvin"] <=1000000):
                result[DONE] = True
            else:
                result[ERROR] = True
        else:
            result[ERROR] = True

        return { tag : result }
    
    async def async_build_request(
        self, 
        command: str, 
        action: str,
        address: int,
        params: str
    ) -> str | None:
        """Build a DALI Request"""
        return {
            "dali_command" : command,
            "action" : action,
            "address" : address,
            "params" : params,
            "command" : command[NAME] + str(address) + (params if params is not None else '')
        }

    async def async_decode_dali_master_response(self, response: str, request):
        """Initialize the DALI hub."""
        LAMP_CMDS = [
            RESICMD[LAMP][NAME]
             ] 
        PREAMBLE = 0
        BODY = 1

        try:   
            COMMAND = (request["dali_command"])[NAME]
            ACTION  = (request["action"])[NAME] if request["action"] is not None else None

            result = {} 
            result["request"] = request
            result["response"] = response

            if response is None or len(response) == 0:
                result[ERROR] = True
                return result
            
            respTokenized = response.split( ':' )

            # if DALI_RESP_OK == respTokenized[PREAMBLE] and len(respTokenized) > 1 and len(respTokenized[BODY]) > 5:
            #     respSuffixTokenized = respTokenized[1].split( ',' )
            #     if ERR9 == respSuffixTokenized[0] and ERR99 == respSuffixTokenized[1]:
            #         result[TIMEOUT] = True
            #         return result

            _LOGGER.debug('### async_decode_dali_master_response LAMP_COMMAND_ANSWER: %s %s %s',
                          str(COMMAND), str(LAMP_COMMAND_ANSWER), 
                              str((COMMAND == LAMP_COMMAND_ANSWER))
                )
            if COMMAND == LAMP_COMMAND_ANSWER:   

                if ACTION == DALICMD[QUERY_STATUS][NAME]:
                    result.update(
                        await self.async_decode_query_status_resp(
                            respTokenized[ 0 ], respTokenized[ 1 ], DALICMD[QUERY_STATUS][TAG])
                    )
                if ACTION == DALICMD[QUERY_DEVICE_TYPE][NAME]:
                    result.update(
                        await self.async_decode_default_response(
                            respTokenized[ 0 ], respTokenized[ 1 ], DALICMD[QUERY_DEVICE_TYPE][TAG])
                    )
                    if DONE in result and result[DONE]:
                        result[DALICMD[QUERY_DEVICE_TYPE][TAG]+NAME] = DALI_DEVICE_TYPES[ result[DALICMD[QUERY_DEVICE_TYPE][TAG]] ] 

                if ACTION == DALICMD[QUERY_CONTROL_GEAR_PRESENT][NAME]:
                    result.update(
                        await self.async_decode_default_response(
                            respTokenized[ 0 ], respTokenized[ 1 ], DALICMD[QUERY_CONTROL_GEAR_PRESENT][TAG])
                        )
                    if DONE in result and result[DONE]:
                        result["isControlGearPresent"] = (result[DALICMD[QUERY_CONTROL_GEAR_PRESENT][TAG]] == 255)

                if ACTION == DALICMD[QUERY_ACTUAL_LEVEL][NAME]:
                    result.update(
                        await self.async_decode_default_response(
                            respTokenized[ 0 ], respTokenized[ 1 ], DALICMD[QUERY_ACTUAL_LEVEL][TAG])
                    )

                if ACTION == DALICMD[QUERY_MIN_LEVEL][NAME]:
                    result.update(
                        await self.async_decode_default_response(
                            respTokenized[ 0 ], respTokenized[ 1 ], DALICMD[QUERY_MIN_LEVEL][TAG])
                    )

                if ACTION == DALICMD[QUERY_MAX_LEVEL][NAME]:
                    result.update(
                        await self.async_decode_default_response(
                            respTokenized[ 0 ], respTokenized[ 1 ], DALICMD[QUERY_MAX_LEVEL][TAG])
                    )

            elif COMMAND == LAMP_COMMAND: 
                prefix = response if len(response) == 3 else respTokenized[ 0 ]
                suffix = None if len(response) == 3 else respTokenized[ 1 ]
                result.update(
                    await self.async_decode_default_response(
                        prefix, suffix, (request["action"])[TAG]
                    )
                )   
            elif COMMAND == LAMP_COMMAND_REPEAT: 
                prefix = response if len(response) == 3 else respTokenized[ 0 ]
                suffix = None if len(response) == 3 else respTokenized[ 1 ]
                result.update(
                    await self.async_decode_default_response(
                        prefix, suffix, (request["action"])[TAG]
                    )
                )                 
            elif COMMAND == RESICMD[LAMP_QUERY_TC][NAME]:
                result.update(
                    await self.async_decode_tc_query_response(
                        respTokenized[ 0 ], respTokenized[ 1 ], RESICMD[LAMP_QUERY_TC][TAG]
                    )
                )

            elif COMMAND == RESICMD[LAMP_QUERY_RGBWAF][NAME]:
                result.update(
                    await self.async_decode_rgbwaf_query_response(
                        respTokenized[ 0 ], respTokenized[ 1 ], RESICMD[LAMP_QUERY_RGBWAF][TAG]
                    )
                )

            elif COMMAND == RESICMD[LAMP_LEVEL][NAME]:
                prefix = response if len(response) == 3 else respTokenized[ 0 ]
                suffix = None if len(response) == 3 else respTokenized[ 1 ]
                result.update(
                    await self.async_decode_default_response(
                        prefix, suffix, RESICMD[LAMP_LEVEL][TAG]
                    )
                )

            elif COMMAND == RESICMD[LAMP_ARC_POWER][NAME]:
                prefix = response if len(response) == 3 else respTokenized[ 0 ]
                suffix = None if len(response) == 3 else respTokenized[ 1 ]
                result.update(
                    await self.async_decode_default_response(
                        prefix, suffix, DALICMD[QUERY_ACTUAL_LEVEL][TAG]
                    )
                )

            elif COMMAND == RESICMD[LAMP_OFF][NAME]:
                prefix = response if len(response) == 3 else respTokenized[ 0 ]
                suffix = None if len(response) == 3 else respTokenized[ 1 ]
                result.update(
                    await self.async_decode_default_response(
                        prefix, suffix, RESICMD[LAMP_OFF][TAG]
                    )
                )

            elif COMMAND == RESICMD[LAMP_RGBWAF][NAME]:
                prefix = response if len(response) == 3 else respTokenized[ 0 ]
                suffix = None if len(response) == 3 else respTokenized[ 1 ]
                result.update(
                    await self.async_decode_default_response(
                        prefix, suffix, RESICMD[LAMP_RGBWAF][TAG]
                    )
                )

            elif COMMAND == RESICMD[LAMP_TC_KELVIN][NAME]:
                prefix = response if len(response) == 3 else respTokenized[ 0 ]
                suffix = None if len(response) == 3 else respTokenized[ 1 ]
                result.update(
                    await self.async_decode_default_response(
                        prefix, suffix, RESICMD[LAMP_TC_KELVIN][TAG]
                    )
                )


        except Exception as e:
            result[ERROR] = True
            result["exception"] = e
            _LOGGER.error(e, exc_info=True)
            _LOGGER.error( '### async_decode_dali_master_response request: %s || response: %s - %s', 
                      str(request), str(response), str(e) )
            
        return result

class DALIHub(DALIRESIMaster):

    def __init__(
            self, hass: HomeAssistant, 
            client_config: dict[str, Any]
            ) -> None:
        """Initialize the DALI hub."""
        super().__init__(hass, client_config)

# ####### # ####### # ####### # ####### # ####### # ####### # ####### # #######
# PRIVATE Query methods
# ####### # ####### # ####### # ####### # ####### # ####### # ####### # #######
        
    async def _async_dali_1_lamp_answer(self, lamp: int, command: str) -> None:
        dali_request = await self.async_build_request(
            RESICMD[LAMP_COMMAND_ANSWER],
            DALICMD[command],
            lamp, '=' + DALICMD[command][OPCODE]
        )
        dali_response = await self.async_pb_call(dali_request)
        decoded_response = await self.async_decode_dali_master_response(dali_response, dali_request)

        # _LOGGER.debug( '### _async_dali_1_lamp_answer %s', str(decoded_response) )
        return decoded_response
    
    async def _async_dali_20_dt8_rgbwaf_lamp_query(self, lamp: int, channels: int) -> None:
        dali_request = await self.async_build_request(
            RESICMD[LAMP_QUERY_RGBWAF],
            None,
            lamp, ',' + str(channels)
        )
        dali_response = await self.async_pb_call(dali_request)
        decoded_response = await self.async_decode_dali_master_response(dali_response, dali_request)

        # _LOGGER.debug( '### _async_dali_20_dt8_rgbwaf_lamp_query %s', str(decoded_response) )

        return decoded_response
    
    async def _async_dali_20_dt8_cw_ww_lamp_query(self, lamp: int) -> None:
        dali_request = await self.async_build_request(
            RESICMD[LAMP_QUERY_TC],
            None,
            lamp, ''
        )
        dali_response = await self.async_pb_call(dali_request)
        decoded_response = await self.async_decode_dali_master_response(dali_response, dali_request)

        # _LOGGER.debug( '### _async_dali_20_dt8_cw_ww_lamp_query %s', str(decoded_response) )
        return decoded_response
    
    
# ####### # ####### # ####### # ####### # ####### # ####### # ####### # #######
# PRIVATE Command methods
# ####### # ####### # ####### # ####### # ####### # ####### # ####### # #######

    async def _async_dali_1_lamp_command(self, lamp: int, command: str) -> None:
        dali_request = await self.async_build_request(
            RESICMD[LAMP_COMMAND_REPEAT],
            DALICMD[command],
            lamp, '=' + DALICMD[command][OPCODE]
        )
        dali_response = await self.async_pb_call(dali_request)
        decoded_response = await self.async_decode_dali_master_response(dali_response, dali_request)

        # _LOGGER.debug( '### _async_dali_1_lamp_command %s', str(decoded_response) )
        
        return decoded_response

    async def _async_dali_1_lamp_off_command(self, lamp: int) -> None:
        dali_request = await self.async_build_request(
            RESICMD[LAMP_OFF],
            None,
            lamp, ''
        )
        dali_response = await self.async_pb_call(dali_request)
        decoded_response = await self.async_decode_dali_master_response(dali_response, dali_request)

        # _LOGGER.debug( '### _async_dali_1_lamp_command %s', str(decoded_response) )
        
        return decoded_response
    
    async def _async_dali_1_lamp_level(self, lamp: int, level: int) -> None:
        dali_request = await self.async_build_request(
            RESICMD[LAMP_LEVEL],
            None,
            lamp, '=' + str(level if level < 255 else 254)
        )
        dali_response = await self.async_pb_call(dali_request)
        decoded_response = await self.async_decode_dali_master_response(dali_response, dali_request)

        # _LOGGER.debug( '### _async_dali_1_lamp_command %s', str(decoded_response) )
        
        return decoded_response
    
    async def _async_dali_1_lamp_arc_power_command(self, lamp: int, level: int) -> None:
        dali_request = await self.async_build_request(
            RESICMD[LAMP_ARC_POWER],
            None,
            lamp, '=' + str(level if level < 255 else 254)
        )
        dali_response = await self.async_pb_call(dali_request)
        decoded_response = await self.async_decode_dali_master_response(dali_response, dali_request)

        # _LOGGER.debug( '### _async_dali_1_lamp_command %s', str(decoded_response) )
        return decoded_response

    async def _async_dali_20_dt8_cw_ww_lamp_command(self, lamp: int, level: int, kelvin: int) -> None:
        dali_request = await self.async_build_request(
            RESICMD[LAMP_TC_KELVIN],
            None,
            lamp, ',' + str(level) + ',' + str(kelvin)
        )
        dali_response = await self.async_pb_call(dali_request)
        decoded_response = await self.async_decode_dali_master_response(dali_response, dali_request)

        # _LOGGER.debug( '### _async_dali_20_dt8_cw_ww_lamp_query %s', str(decoded_response) )
        return decoded_response
    
    async def _async_dali_20_dt8_rgbwaf_channels_lamp_command(
            self, 
            lamp: int,
            level: int,
            red: int, 
            green: int, 
            blue: int, 
            white: int, 
            amber: int
    ):
        # #LAMP PRIMARY N:1,127,6554,13107,19661,26214,32767,39321<CR>
        # #LAMP PRIMARY N:15,65535,255,130,0,33,33,65535
        dali_request = await self.async_build_request(
            RESICMD[LAMP_RGBWAF], 
            None,
            lamp,
            ',' + str(level if level is not None else 255)
            + ',' + str((red if red < 255 else 254) if red is not None else 255) 
            + ',' + str((green if green < 255 else 254) if green is not None else 255)
            + ',' + str((blue if blue < 255 else 254) if blue is not None else 255)
            + ',' + str((white if white < 255 else 254) if white is not None else 255)
            + ',' + str((amber if amber < 255 else 254) if amber is not None else 155) 
            # + ',65535'
        )

        dali_response = await self.async_pb_call(dali_request)
        response = await self.async_decode_dali_master_response(dali_response, dali_request)

        return response

# ####### # ####### # ####### # ####### # ####### # ####### # ####### # #######
# PUBLIC Query methods
# ####### # ####### # ####### # ####### # ####### # ####### # ####### # #######

    async def async_dali_retrieve_min_level(self, lamp: int) -> None:
        command_response = await self._async_dali_1_lamp_answer(lamp, QUERY_MIN_LEVEL)
        if DONE in command_response and command_response[DONE]:
            _LOGGER.debug( '### async_dali_retrieve_min_level %s', str(command_response) )
        else:
            _LOGGER.error( '### async_dali_retrieve_min_level %s', str(command_response) )
        return command_response
    
    async def async_dali_retrieve_max_level(self, lamp: int) -> None:
        command_response = await self._async_dali_1_lamp_answer(lamp, QUERY_MAX_LEVEL)
        if DONE in command_response and command_response[DONE]:
            _LOGGER.debug( '### async_dali_retrieve_max_level %s', str(command_response) )
        else:
            _LOGGER.error( '### async_dali_retrieve_max_level %s', str(command_response) )
        return command_response
        
    async def async_dali_retrieve_actual_level(self, color_mode: str, lamp: int) -> None:
        command_response = {}
        if (color_mode == ColorMode.ONOFF or color_mode == ColorMode.BRIGHTNESS 
                or color_mode == ColorMode.COLOR_TEMP or color_mode == ColorMode.RGB
                or color_mode == ColorMode.RGBWW
        ):
            command_response = await self._async_dali_1_lamp_answer(lamp, QUERY_ACTUAL_LEVEL)
        if DONE in command_response and command_response[DONE]:  
            _LOGGER.debug( '### async_dali_retrieve_actual_level %s', str(command_response) )
        else:
            _LOGGER.error( '### async_dali_retrieve_actual_level %s', str(command_response) )
        return command_response

    async def async_dali_20_dt8_retrieve_rgbww_lamp(self, lamp: int) -> any:
        command_response = await self._async_dali_20_dt8_rgbwaf_lamp_query(lamp, 5)
        if DONE in command_response and command_response[DONE]:  
            _LOGGER.debug( '### async_dali_20_dt8_retrieve_rgbww_lamp %s', str(command_response) )
        else:
            _LOGGER.error( '### async_dali_20_dt8_retrieve_rgbww_lamp %s', str(command_response) )
        return command_response
    
    async def async_dali_20_dt8_retrieve_rgb_lamp(self, lamp: int) -> any:
        command_response = await self._async_dali_20_dt8_rgbwaf_lamp_query(lamp, 3)
        if DONE in command_response and command_response[DONE]:  
            _LOGGER.debug( '### async_dali_20_dt8_retrieve_rgb_lamp %s', str(command_response) )
        else:
            _LOGGER.error( '### async_dali_20_dt8_retrieve_rgb_lamp %s', str(command_response) )
        return command_response
        
    async def async_dali_20_dt8_retrieve_cw_ww_lamp(self, lamp: int):
        command_response = await self._async_dali_20_dt8_cw_ww_lamp_query(lamp)
        if DONE in command_response and command_response[DONE]:  
            _LOGGER.debug( '### async_dali_20_dt8_retrieve_cw_ww_lamp %s', str(command_response) )
        else:
            _LOGGER.error( '### async_dali_20_dt8_retrieve_cw_ww_lamp %s', str(command_response) )
        return command_response
    
    async def async_dali_retrieve_device_type(self, lamp: int) -> any:
        command_response = await self._async_dali_1_lamp_answer(lamp, QUERY_DEVICE_TYPE)
        if DONE in command_response and command_response[DONE]:        
            _LOGGER.debug( '### async_dali_retrieve_device_type %s', str(command_response) )
        else:
            _LOGGER.error( '### async_dali_retrieve_device_type %s', str(command_response) )
        return command_response

    async def async_dali_retrieve_device_status(self, lamp: int) -> any:
        command_response = await self._async_dali_1_lamp_answer(lamp, QUERY_STATUS)
        if DONE in command_response and command_response[DONE]:
            _LOGGER.debug( '### async_dali_retrieve_device_status %s', str(command_response) )
        else:
            _LOGGER.error( '### async_dali_retrieve_device_status %s', str(command_response) )
        return command_response

# ####### # ####### # ####### # ####### # ####### # ####### # ####### # #######
# PUBLIC Command methods
# ####### # ####### # ####### # ####### # ####### # ####### # ####### # #######

    async def async_dali_recall_off(self, device_type: int, color_mode: str, lamp: int) -> None:
        command_response = await self._async_dali_1_lamp_command(lamp, OFF)
        command_response = await self._async_dali_1_lamp_off_command(lamp)
        # if ERROR in command_response and command_response[ERROR]:

        _LOGGER.debug( '### async_dali_recall_off %s || command_response: %s', 
                        str(command_response), str(command_response) )
        return command_response
            
    async def async_dali_recall_level(self, device_type: int, color_mode: str, lamp: int, level: int) -> None:
        if level > 0:
            command_response = await self._async_dali_1_lamp_arc_power_command(lamp, level)
            if (DONE in command_response and command_response[DONE]):
                query_response = await self.async_dali_retrieve_actual_level(color_mode, lamp)
                if (DONE in query_response and query_response[DONE]):
                    if( (level if level < 255 else 254) == query_response["query_actual_level"]):
                        command_response["query_actual_level"] = query_response["query_actual_level"]
                    else:
                        command_response = await self._async_dali_1_lamp_level(lamp, level)
        else:
            command_response = await self.async_dali_recall_off(color_mode, lamp)

        _LOGGER.debug( '### async_dali_recall_level %s || command_response: %s', 
                        str(command_response), str(command_response) )
        return command_response
        
    async def async_dali_recall_max_level(self, color_mode: str, lamp: int) -> None:
        query_response = await self.async_dali_retrieve_max_level(lamp)

        command_response = await self._async_dali_1_lamp_command(lamp, RECALL_MAX_LEVEL)
        if (DONE in command_response and command_response[DONE]):
            if (DONE in query_response and query_response[DONE]):
                command_response["query_actual_level"] = query_response["query_max_level"]
            else:
                query_response = await self.async_dali_retrieve_actual_level(color_mode, lamp)
                if (DONE in query_response and query_response[DONE]):
                    command_response["query_actual_level"] = query_response["query_actual_level"]
        
        _LOGGER.debug( '### async_dali_recall_max_level %s || command_response: %s', 
                        str(query_response), str(command_response) )

        return command_response

    async def async_dali_recall_color_temperature_level(
            self, device_type: int, color_mode: str,
            lamp: int, level: int, kelvin: int
    ) -> None:
        command_response = await self._async_dali_20_dt8_cw_ww_lamp_command(
            lamp, 255 if level is None else ( 254 if level == 255 else level), kelvin
         )

        _LOGGER.debug( '### async_dali_recall_color_temperature_level command_response: %s', 
                        str(command_response) )
        return command_response

    async def async_dali_recall_rgb_level(
            self, device_type: int, color_mode: str,
            lamp: int, level: int, red: int, green: int, blue: int
    ) -> None:
        command_response = await self._async_dali_20_dt8_rgbwaf_channels_lamp_command(
            lamp, 255 if level is None else ( 254 if level == 255 else level),
            red, green, blue, 0, 0
        )
        _LOGGER.debug( '### async_dali_recall_rgb_level command_response: %s', 
                        str(command_response) )
        return command_response

    async def async_dali_recall_rgbww_level(
            self, device_type: int, color_mode: str,
            lamp: int, level: int, red: int, green: int, blue: int, white: int, amber: int
    ) -> None:
        command_response = await self._async_dali_20_dt8_rgbwaf_channels_lamp_command(
            lamp, 255 if level is None else ( 254 if level == 255 else level),
            red, green, blue, white, amber
        )
        _LOGGER.debug( '### async_dali_recall_rgbww_level command_response: %s', 
                        str(command_response) )
        return command_response
