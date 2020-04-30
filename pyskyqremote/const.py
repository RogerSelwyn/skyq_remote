"""Constants for pyskyqremote."""
# SOAP/UPnP Constants
SKY_PLAY_URN = "urn:nds-com:serviceId:SkyPlay"
SKYCONTROL = "SkyControl"
SOAP_ACTION = '"urn:schemas-nds-com:service:SkyPlay:2#{0}"'
SOAP_CONTROL_BASE_URL = "http://{0}:49153{1}"
SOAP_DESCRIPTION_BASE_URL = "http://{0}:49153/description{1}.xml"
SOAP_PAYLOAD = """<s:Envelope xmlns:s='http://schemas.xmlsoap.org/soap/envelope/' s:encodingStyle='http://schemas.xmlsoap.org/soap/encoding/'>
    <s:Body>
        <u:{0} xmlns:u="urn:schemas-nds-com:service:SkyPlay:2">
            <InstanceID>0</InstanceID>
        </u:{0}>
    </s:Body>
</s:Envelope>"""
SOAP_RESPONSE = "u:{0}Response"
SOAP_USER_AGENT = "SKYPLUS_skyplus"
UPNP_GET_MEDIA_INFO = "GetMediaInfo"
UPNP_GET_TRANSPORT_INFO = "GetTransportInfo"

# WebSocket Constants
WS_BASE_URL = "ws://{0}:9006/as/{1}"
WS_CURRENT_APPS = "apps/status"

# REST Constants
REST_BASE_URL = "http://{0}:{1}/as/{2}"
REST_CHANNEL_LIST = "services"
REST_RECORDING_DETAILS = "pvr/details/{0}"
REST_PATH_INFO = "system/information"
REST_PATH_DEVICEINFO = "system/deviceinformation"

# Generic Constants
DEFAULT_ENCODING = "utf-8"

# Sky specific constants
CURRENT_URI = "CurrentURI"
CURRENT_TRANSPORT_STATE = "CurrentTransportState"
APP_STATUS_VISIBLE = "VISIBLE"

PVR = "pvr"
XSI = "xsi"
PAST_END_OF_EPG = "past end of epg"

CONNECTTIMEOUT = 1000
TIMEOUT = 2

SKY_STATE_PLAYING = "PLAYING"
SKY_STATE_PAUSED = "PAUSED_PLAYBACK"
SKY_STATE_STANDBY = "STANDBY"
SKY_STATE_ON = "ON"
SKY_STATE_OFF = "POWERED OFF"

# Application Constants
APP_EPG = "com.bskyb.epgui"


COMMANDS = {
    "power": 0,
    "select": 1,
    "backup": 2,
    "dismiss": 2,
    "channelup": 6,
    "channeldown": 7,
    "interactive": 8,
    "sidebar": 8,
    "help": 9,
    "services": 10,
    "search": 10,
    "tvguide": 11,
    "home": 11,
    "i": 14,
    "text": 15,
    "up": 16,
    "down": 17,
    "left": 18,
    "right": 19,
    "red": 32,
    "green": 33,
    "yellow": 34,
    "blue": 35,
    "0": 48,
    "1": 49,
    "2": 50,
    "3": 51,
    "4": 52,
    "5": 53,
    "6": 54,
    "7": 55,
    "8": 56,
    "9": 57,
    "play": 64,
    "pause": 65,
    "stop": 66,
    "record": 67,
    "fastforward": 69,
    "rewind": 71,
    "boxoffice": 240,
    "sky": 241,
}

RESPONSE_OK = 200

TEST_CHANNEL_LIST = {
    "documentId": "2416",
    "services": [
        {
            "c": "317",
            "dvbtriplet": "64511.8800.11684",
            "schedule": True,
            "servicetype": "DSAT",
            "servicetypes": ["DSAT"],
            "sf": "hd",
            "sg": 12,
            "sid": "684",
            "sk": 684,
            "t": "Premium Comedy HD",
            "xsg": 3,
        },
        {
            "c": "105",
            "dvbtriplet": "64511.6400.11075",
            "schedule": True,
            "servicetype": "DSAT",
            "servicetypes": ["DSAT"],
            "sf": "hd",
            "sg": 13,
            "sid": "5435",
            "sk": 75,
            "t": "Canale 5 HD",
            "xsg": 4,
        },
        {
            "c": "120",
            "dvbtriplet": "64511.6400.11074",
            "schedule": True,
            "servicetype": "DSAT",
            "servicetypes": ["DSAT"],
            "sf": "hd",
            "sg": 21,
            "sid": "74",
            "sk": 74,
            "t": "Sky Arte HD",
            "xsg": 1,
        },
        {
            "c": "101",
            "dvbtriplet": "2.2048.10353",
            "schedule": True,
            "servicetype": "DSAT",
            "servicetypes": ["DSAT"],
            "sf": "sd",
            "sg": 12,
            "sid": "2153",
            "sk": 2153,
            "t": "BBC One South",
            "xsg": 3,
        },
    ],
}
