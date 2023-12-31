
NAME = "NAME"
OPCODE = "OPCODE"
DESCRIPTION = "DESCRIPTION"
TAG = "tag"
DEFAULT = "default"
DONE = "done"
TIMEOUT = "timeout"
ERROR = "error"
ERR9 = "9"
ERR99 = "99"

ATTR_ACTUAL_LAMP_LEVEL = "actualLampLevel"

DALI_RESP_OK = "#OK"
DALI_RESP_PERR = "#ERR"
DALI_RESP_ERR = "ERR"
DALI_RESP_LQTC = "#LQTC"
DALI_RESP_LQRGBWAF = "#LQRGBWAF"

OFF = "OFF"
ON = "ON"
RECALL_MAX_LEVEL = "RECALL MAX LEVEL"
RECALL_MIN_LEVEL = "RECALL MIN LEVEL"
STORE_ACTUAL_LEVEL_IN_DTR = "STORE ACTUAL LEVEL IN DTR"
STORE_THE_DTR_AS_MAX_LEVEL = "STORE THE DTR AS MAX LEVEL"
STORE_THE_DTR_AS_MIN_LEVEL = "STORE THE DTR AS MIN LEVEL"
STORE_DTR_AS_SYSTEM_FAILURE_LEVEL = "STORE DTR AS SYSTEM FAILURE LEVEL"
STORE_DTR_AS_POWER_ON_LEVEL = "STORE DTR AS POWER ON LEVEL"
STORE_DTR_AS_FADETIME = "STORE DTR AS FADETIME"
STORE_DTR_AS_FADERATE = "STORE DTR AS FADERATE"
STORE_THE_DTR_AS_SCENE_0 = "STORE THE DTR AS SCENE 0"

STORE_THE_DTR_AS_SCENE_15 = "STORE THE DTR AS SCENE 15"
QUERY_STATUS = "QUERY STATUS"
QUERY_CONTROL_GEAR_PRESENT = "QUERY CONTROL GEAR PRESENT"
QUERY_VERSION_NUMBER = "QUERY VERSION NUMBER"
QUERY_DEVICE_TYPE = "QUERY DEVICE TYPE"
QUERY_PHYSICAL_MINIMUM = "QUERY PHYSICAL MINIMUM"
QUERY_CONTENT_DTR1 = "QUERY CONTENT DTR1"
QUERY_CONTENT_DTR2 = "QUERY CONTENT DTR2"
QUERY_ACTUAL_LEVEL = "QUERY ACTUAL LEVEL"
QUERY_MAX_LEVEL = "QUERY MAX LEVEL"
QUERY_MIN_LEVEL = "QUERY MIN LEVEL"
QUERY_POWER_ON_LEVEL = "QUERY POWER ON LEVEL"
QUERY_SYSTEM_FAILURE_LEVEL = "QUERY SYSTEM FAILURE LEVEL"
QUERY_FADE_TIME_FADE_RATE = "QUERY FADE TIME FADE RATE"
QUERY_SCENE_LEVEL = "QUERY SCENE LEVEL"
QUERY_GROUPS_0_7 = "QUERY GROUPS 0-7"
QUERY_GROUPS_8_15 = "QUERY GROUPS 8-15"

STORE_THE_DTR_AS_SCENE = "STORE THE DTR AS SCENE"
DT8_SET_TEMPORARY_X_COORDINATE = "DT8:SET TEMPORARY X-COORDINATE"
DT8_SET_TEMPORARY_Y_COORDINATE = "DT8:SET TEMPORARY Y-COORDINATE"
DT8_SET_COLOUR_TEMPERATURE_TC = "DT8:SET COLOUR TEMPERATURE Tc"
DT8_SET_PRIMARY_N_DIMLEVEL = "DT8:SET PRIMARY N DIMLEVEL"
DT8_SET_RGB_DIMLEVEL = "DT8:SET RGB DIMLEVEL"
DT8_SET_WAF_DIMLEVEL = "DT8:SET WAF DIMLEVEL"
SET_DTR = "DTR="
ENABLE_DEVICE_TYPE = "ENABLE DEVICE TYPE"
SET_DTR1 = "DTR1="
SET_DTR2 = "DTR2="

LAMP = "#LAMP "
LAMP_OFF = "#LAMP OFF:"
LAMP_ARC_POWER = "#LAMP ARC POWER:"
LAMP_LEVEL = "#LAMP LEVEL:"
LAMP_COMMAND = "#LAMP COMMAND:"
LAMP_COMMAND_REPEAT = "#LAMP COMMAND REPEAT:"
LAMP_COMMAND_ANSWER = "#LAMP COMMAND ANSWER:"
LAMP_RGBWAF = "#LAMP RGBWAF:"
LAMP_QUERY_RGBWAF = "#LAMP QUERY RGBWAF:"
LAMP_TC_KELVIN = "LAMP TC KELVIN"
LAMP_XY = "#LAMP XY:"
LAMP_XY_DIGITS = "#LAMP XY DIGITS:"
LAMP_QUERY_XY = "#LAMP QUERY XY:"
LAMP_QUERY_TC = "#LAMP QUERY TC:"
DALI_CMD16 = "#DALI CMD16:"
LAMP_PRIMARY_N = "#LAMP PRIMARY N:"
DALI_BUS_ERROR = "#DALI BUS ERROR"

OK = "OK"

DALI_DEVICE_TYPES =  {
     0 : 'Fluorescent lamp control gear',
     1 : 'Self-contained emergency lamp control gear',
     2 : 'Discharge (HID) lamp control gear',
     3 : 'Low-voltage halogen lamp control gear',
     4 : 'Incandescent lamp dimmer',
     5 : 'DC voltage lamp dimmer (0/1-10V)',
     6 : 'LED lamp control gear',
     7 : 'witching (relay) control gear',
     8 : 'Color lamp control gear',
    15 : 'Load referencing',
    16 : 'Thermal gear protection',
    17 : 'Dimming curve selection',
    18 : 'Under consideration',
    19 : 'Centrally supplied emergency operation',
    20 : 'Demand response',
    21 : 'Thermal lamp protection',
    22 : 'Under consideration',
    23 : 'Non-replaceable light source',
    255 : 'Unknown device'
} 

DALICMD = {
    # // Source: https://onlinedocs.microchip.com/pr/GUID-0CDBB4BA-5972-4F58-98B2-3F0408F3E10B-en-US-1/index.html?GUID-DA5EBBA5-6A56-4135-AF78-FB1F780EF475
    OFF : { 
        NAME : OFF,
        OPCODE : '0x00',
        TAG : 'off',
        DESCRIPTION : 'Switches off lamp(s)'
    },
    RECALL_MAX_LEVEL : { 
        NAME : RECALL_MAX_LEVEL,
        OPCODE : '0x05',
        TAG: 'recall_max_level',
        DESCRIPTION : 'Changes the current light output to the maximum level'
    },
    RECALL_MIN_LEVEL : { 
        NAME : RECALL_MIN_LEVEL,
        OPCODE : '0x06',
        DESCRIPTION : 'Changes the current light output to the minimum level'
    },
    STORE_ACTUAL_LEVEL_IN_DTR : {
        NAME : STORE_ACTUAL_LEVEL_IN_DTR,
        OPCODE : '0x21',
        DESCRIPTION : 'Determines the control gear\'s status based on a combination of gear properties'
    },
    STORE_THE_DTR_AS_MAX_LEVEL : {
        NAME : 'STORE THE DTR AS MAX LEVEL',
        OPCODE : '0x2A',
        DESCRIPTION : 'Stores the actual register value DTR as maximum level for lamp'
    },
    STORE_THE_DTR_AS_MIN_LEVEL : {
        NAME : 'STORE THE DTR AS MIN LEVEL',
        OPCODE : '0x2B',
        DESCRIPTION : 'Stores the actual register value DTR as minimum level for lamp'
    },
    STORE_DTR_AS_SYSTEM_FAILURE_LEVEL : {
        NAME : 'STORE DTR AS SYSTEM FAILURE LEVEL',
        OPCODE : '0x2C',
        DESCRIPTION : 'Stores the actual register value DTR as system failure level for lamp'
    },
    STORE_DTR_AS_POWER_ON_LEVEL : {
        NAME : 'STORE DTR AS POWER ON LEVEL',
        OPCODE : '0x2D',
        DESCRIPTION : 'Stores the actual register value DTR as power on level for lamp'
    },
    STORE_DTR_AS_FADETIME : {
        NAME : 'STORE DTR AS FADETIME',
        OPCODE : '0x2E',
        DESCRIPTION : 'Stores the actual register value DTR as fade time for lamp'
    },
    STORE_DTR_AS_FADERATE : {
        NAME : 'STORE DTR AS FADERATE',
        OPCODE : '0x2F',
        DESCRIPTION : 'Stores the actual register value DTR as fade rate for lamp'
    },
    STORE_THE_DTR_AS_SCENE_0: {
        NAME : 'STORE THE DTR AS SCENE 0',
        OPCODE : '0x40',
        DESCRIPTION : 'Stores the actual register value DTR as new brightness level forscene x (0 to 15)'
    },
    # //TO-DO
    STORE_THE_DTR_AS_SCENE_15: {
        NAME : 'STORE THE DTR AS SCENE 15',
        OPCODE : '0x40F',
        DESCRIPTION : 'Stores the actual register value DTR as new brightness level forscene x (0 to 15)'
    },

    QUERY_STATUS : { 
        NAME : 'QUERY STATUS',
        OPCODE : '0x90',
        TAG : 'query_status',
        DESCRIPTION : 'Determines the control gear\'s status based on a combination of gear properties'
    },
    QUERY_CONTROL_GEAR_PRESENT : { 
        NAME : 'QUERY CONTROL GEAR PRESENT',
        OPCODE : '0x91',
        TAG: 'query_control_gear_present',
        DESCRIPTION : 'Determines if a control gear is present'
    },
    QUERY_VERSION_NUMBER : { 
        NAME : 'QUERY VERSION NUMBER',
        OPCODE : '0x97',
        DESCRIPTION : 'Returns the device\'s version number located in memory bank 0, location 0x16'
    },
    QUERY_DEVICE_TYPE : { 
        NAME : 'QUERY DEVICE TYPE',
        OPCODE : '0x99',
        TAG: 'query_device_type',
        DESCRIPTION : 'Determines the device type supported by the control gear'
    },
    QUERY_PHYSICAL_MINIMUM: {
        NAME : 'QUERY PHYSICAL MINIMUM',
        OPCODE : '0x9A',
        DESCRIPTION : 'Returns the minimum light output that the control gear can operate at'
    },
    QUERY_CONTENT_DTR1: {
        NAME : 'QUERY CONTENT DTR1',
        OPCODE : '0x9C',
        DESCRIPTION : 'Returns the value of DTR1'
    },
    QUERY_CONTENT_DTR2: {
        NAME : 'QUERY CONTENT DTR2',
        OPCODE : '0x9D',
        DESCRIPTION : 'Returns the value of DTR2'
    },
    QUERY_ACTUAL_LEVEL : { 
        NAME : 'QUERY ACTUAL LEVEL',
        OPCODE : '0xA0',
        TAG: 'query_actual_level',
        DESCRIPTION : 'Returns the control gear\'s actual power output level'
    },
    QUERY_MAX_LEVEL : { 
        NAME : 'QUERY MAX LEVEL',
        OPCODE : '0xA1',
        TAG: 'query_max_level',
        DESCRIPTION : 'Returns the control gear\'s maximum output setting'
    },
    QUERY_MIN_LEVEL : { 
        NAME : 'QUERY MIN LEVEL',
        OPCODE : '0xA2',
        TAG: 'query_min_level',
        DESCRIPTION : 'Returns the control gear\'s minimum output setting'
    },
    QUERY_POWER_ON_LEVEL : { 
        NAME : 'QUERY POWER ON LEVEL',
        OPCODE : '0xA3',
        DESCRIPTION : 'Returns the control gear\'s minimum output setting'
    },  
    QUERY_SYSTEM_FAILURE_LEVEL : { 
        NAME : 'QUERY SYSTEM FAILURE LEVEL',
        OPCODE : '0xA4',
        DESCRIPTION : 'Returns the value of the intensity level due to a system failure'
    },  
    QUERY_FADE_TIME_FADE_RATE : { 
        NAME : 'QUERY FADE TIME FADE RATE',
        OPCODE : '0xA5',
        DESCRIPTION : 'Returns a byte in which the upper nibble is equal to the fade time value and the lower nibble is the fade rate value'
    },   
    QUERY_SCENE_LEVEL : { 
        NAME : 'QUERY SCENE LEVEL',
        OPCODE : '0xB0',
        DESCRIPTION : 'Returns the level value of scene \'x\''
    },   
    QUERY_GROUPS_0_7 : { 
        NAME : 'QUERY GROUPS 0-7',
        OPCODE : '0xC0',
        DESCRIPTION : 'Returns a byte in which each bit represents a member of a group. A \'1\' represents a member of the group'
    },     
    QUERY_GROUPS_8_15 : { 
        NAME : 'QUERY GROUPS 8-15',
        OPCODE : '0xC1',
        DESCRIPTION : 'Returns a byte in which each bit represents a member of a group. A \'1\' represents a member of the group'
    },
# //
# // 16 BIT command
# //
    STORE_THE_DTR_AS_SCENE: {
        NAME : 'STORE THE DTR AS SCENE',
        OPCODE : '0x0140',
        DESCRIPTION : 'Stores the actual register value DTR as new brightness level forscene x (0 to 15)'
    },
    DT8_SET_TEMPORARY_X_COORDINATE : { 
        NAME : 'DT8:SET TEMPORARY X-COORDINATE',
        OPCODE : '0x01E0',
        DESCRIPTION : ''
    },
    DT8_SET_TEMPORARY_Y_COORDINATE : { 
        NAME : 'DT8:SET TEMPORARY Y-COORDINATE',
        OPCODE : '0x01E1',
        DESCRIPTION : ''
    },  
    DT8_SET_COLOUR_TEMPERATURE_TC : { 
        NAME : 'DT8:SET COLOUR TEMPERATURE Tc',
        OPCODE : '0x01E7',
        DESCRIPTION : ''
    },  
    DT8_SET_PRIMARY_N_DIMLEVEL : { 
        NAME : 'DT8:SET PRIMARY N DIMLEVEL',
        OPCODE : '0x01EA',
        DESCRIPTION : ''
    },  
    DT8_SET_RGB_DIMLEVEL : { 
        NAME : 'DT8:SET RGB DIMLEVEL',
        OPCODE : '0x01EB',
        DESCRIPTION : ''
    },  
    DT8_SET_WAF_DIMLEVEL : { 
        NAME : 'DT8:SET WAF DIMLEVEL',
        OPCODE : '0x01EC',
        DESCRIPTION : ''
    },      
    SET_DTR : { 
        NAME : 'DTR=',
        OPCODE : '0xA3',
        DESCRIPTION : 'This command loads the hex value HH into the DTR register'
    },    
    ENABLE_DEVICE_TYPE : { 
        NAME : 'ENABLE DEVICE TYPE',
        OPCODE : '0xC1',
        DESCRIPTION : 'If you want to use special device type depended commands youhave to precede this commands with this enable command. HHis the selected device type e.g. 8)'
    },    
    SET_DTR1 : { 
        NAME : 'DTR1=',
        OPCODE : '0xC3',
        DESCRIPTION : 'This command loads the hex value HH into the DTR1 register'
    },  
    SET_DTR2: { 
        NAME : 'DTR2=',
        OPCODE : '0xC5',
        DESCRIPTION : 'This command loads the hex value HH into the DTR2 register'
    },    
}

RESICMD = {
    LAMP : {
        NAME : '#LAMP '
    },
    LAMP_OFF : {
        NAME : '#LAMP OFF:',
        TAG : 'lamp_off'
    },
    LAMP_ARC_POWER : {
        NAME : "#LAMP ARC POWER:",
        TAG: "lamp_arc_power"
    },
    LAMP_LEVEL : {
        NAME : '#LAMP LEVEL:',
        TAG: 'lamp_level'
    },
    LAMP_COMMAND : {
        NAME : '#LAMP COMMAND:',
        TAG: 'lamp_command'
    },
    LAMP_COMMAND_REPEAT : {
        NAME : '#LAMP COMMAND REPEAT:',
        TAG: 'lamp_command_repeat'
    },
    LAMP_COMMAND_ANSWER : {
        NAME : '#LAMP COMMAND ANSWER:',
        TAG: 'lamp_command_answer'
    },
    LAMP_RGBWAF : {
        NAME : '#LAMP RGBWAF:',
        TAG : 'rgbwaf'
    },
    LAMP_QUERY_RGBWAF : {
        NAME : '#LAMP QUERY RGBWAF:',
        TAG: 'query_rgbwaf'
    },
    LAMP_TC_KELVIN : {
        NAME : '#LAMP TC KELVIN:',
        TAG : 'tc_kelvin'
    },
    LAMP_XY : {
        NAME : '#LAMP XY:'
    },
    LAMP_XY_DIGITS : {
        NAME : '#LAMP XY DIGITS:'
    },
    LAMP_QUERY_XY : {
        NAME : '#LAMP QUERY XY:'
    },
    LAMP_QUERY_TC : {
        NAME : "#LAMP QUERY TC:",
        TAG: "query_tc"
    },
    DALI_CMD16 : {
        NAME : '#DALI CMD16:'
    },
    LAMP_PRIMARY_N : {
        NAME : '#LAMP PRIMARY N:'
    },
    DALI_BUS_ERROR : {
        NAME : '#DALI BUS ERROR'
    }
}

RESIRESP = {
    OK : {
        NAME : '#OK'
    }
}

