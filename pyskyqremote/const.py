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
REST_FAVOURITES = "services/favourites"
REST_RECORDING_DETAILS = "pvr/details/{0}"
REST_RECORDINGS_LIST = "pvr/?limit={0}&offset={1}"
REST_QUOTA_DETAILS = "pvr/storage"
REST_BOOK_RECORDING = "pvr/action/bookrecording?eid={0}"
REST_BOOK_PPVRECORDING = "pvr/action/bookppvrecording?eid={0}&offerref={1}"
REST_BOOK_SERIES_RECORDING = "pvr/action/bookseriesrecording?eid={0}"
REST_SERIES_LINK = "pvr/action/serieslink?pvrid={0}"
REST_SERIES_UNLINK = "pvr/action/seriesunlink?pvrid={0}"
REST_RECORDING_KEEP = "pvr/action/keep?pvrid={0}"
REST_RECORDING_UNKEEP = "pvr/action/unkeep?pvrid={0}"
REST_RECORDING_LOCK = "pvr/action/lock?pvrid={0}"
REST_RECORDING_UNLOCK = "pvr/action/unlock?pvrid={0}"
REST_RECORDING_DELETE = "pvr/action/delete?pvrid={0}"
REST_RECORDING_UNDELETE = "pvr/action/undelete?pvrid={0}"
REST_RECORDING_ERASE = "pvr/action/erase?pvrid={0}"
REST_RECORDING_ERASE_ALL = "pvr"
REST_RECORDING_SET_LAST_PLAYED_POSITION = "pvr/action/setlastplayedposition?pos={0}&pvrid={1}"
REST_PATH_SYSTEMINFO = "system/information"
REST_PATH_DEVICEINFO = "system/deviceinformation"
REST_PATH_APPS = "apps"

# Sky specific constants
CURRENT_URI = "CurrentURI"
CURRENT_TRANSPORT_STATE = "CurrentTransportState"
APP_STATUS_VISIBLE = "VISIBLE"

PVR = "pvr"
XSI = "xsi"

SKY_STATE_NOMEDIA = "NO_MEDIA_PRESENT"
SKY_STATE_OFF = "POWERED OFF"
SKY_STATE_ON = "ON"
SKY_STATE_PLAYING = "PLAYING"
SKY_STATE_PAUSED = "PAUSED_PLAYBACK"
SKY_STATE_STANDBY = "STANDBY"
SKY_STATE_STOPPED = "STOPPED"
SKY_STATE_TRANSITIONING = "TRANSITIONING"
SKY_STATUS_LIVE = "LIVE"

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

KNOWN_COUNTRIES = {
    "DEU": "DEU",
    "GBR": "GBR",
    "IRL": "GBR",
    "ITA": "ITA",
}

# Random set of other constants
EPG_ERROR_PAST_END = "past end of epg"
EPG_ERROR_NO_DATA = "no epg data found"

RESPONSE_OK = 200
CONNECT_TIMEOUT = 1000
HTTP_TIMEOUT = 6
SOAP_TIMEOUT = 2

AUDIO = "audio"
VIDEO = "video"

ALLRECORDINGS = "all"
