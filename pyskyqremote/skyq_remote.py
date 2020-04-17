import time
import math
import socket
import requests
import json
import xmltodict
import logging
import traceback
from datetime import datetime, timedelta
from http import HTTPStatus

from ws4py.client.threadedclient import WebSocketClient

_LOGGER = logging.getLogger(__name__)

# SOAP/UPnP Constants
SKY_PLAY_URN = "urn:nds-com:serviceId:SkyPlay"
SKYControl = "SkyControl"
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
REST_PATH_APPS = "apps/status"
REST_CHANNEL_LIST = "services"
REST_RECORDING_DETAILS = "pvr/details/{0}"

# Generic Constants
DEFAULT_ENCODING = "utf-8"

# Sky specific constants
CURRENT_URI = "CurrentURI"
CURRENT_TRANSPORT_STATE = "CurrentTransportState"

PVR = "pvr"
XSI = "xsi"
PAST_END_OF_EPG = "past end of epg"


class SkyQRemote:
    commands = {
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
    connectTimeout = 1000
    TIMEOUT = 2

    REST_BASE_URL = "http://{0}:{1}/as/{2}"
    REST_PATH_INFO = "system/information"

    SKY_STATE_NO_MEDIA_PRESENT = "NO_MEDIA_PRESENT"
    SKY_STATE_PLAYING = "PLAYING"
    SKY_STATE_PAUSED = "PAUSED_PLAYBACK"
    SKY_STATE_OFF = "OFF"

    # Application Constants
    APP_EPG = "com.bskyb.epgui"
    APP_STATUS_VISIBLE = "VISIBLE"

    def __init__(self, host, country, port=49160, jsonport=9006):
        self._host = host
        self._country = country.casefold()
        self._port = port
        self._jsonport = jsonport
        url_index = 0
        self._soapControlURL = None
        while self._soapControlURL is None and url_index < 50:
            self._soapControlURL = self._getSoapControlURL(url_index)["url"]
            url_index += 1

        if self._country == "uk":
            from pyskyqremote.country.remote_uk import SkyQCountry
        elif self._country == "it":
            from pyskyqremote.country.remote_it import SkyQCountry
        elif self._country == "test":
            from pyskyqremote.country.remote_it import SkyQCountry
        else:
            _LOGGER.exception(
                f"X0999 - Invalid country: {self._host} : {self._country}"
            )

        self._remoteCountry = SkyQCountry(self._host)
        self._channels = self._http_json(REST_CHANNEL_LIST)

    def powerStatus(self) -> str:
        if self._soapControlURL is None:
            return "Powered Off"
        try:
            output = self._http_json(self.REST_PATH_INFO)
            if "activeStandby" in output and output["activeStandby"] is False:
                return "On"
            return "Off"
        except (
            requests.exceptions.ConnectTimeout,
            requests.exceptions.ReadTimeout,
        ):
            return "Off"
        except (requests.exceptions.ConnectionError):
            _LOGGER.info(
                f"I0010 - Device has control URL but connection request failed: {self._host}"
            )
            return "Off"
        except Exception as err:
            _LOGGER.exception(f"X0060 - Error occurred: {self._host} : {err}")
            return "Off"

    def getCurrentState(self):
        if self.powerStatus() == "Off":
            return self.SKY_STATE_OFF
        response = self._callSkySOAPService(UPNP_GET_TRANSPORT_INFO)
        if response is not None:
            state = response[CURRENT_TRANSPORT_STATE]
            if state == self.SKY_STATE_PLAYING:
                return self.SKY_STATE_PLAYING
            if state == self.SKY_STATE_PAUSED:
                return self.SKY_STATE_PAUSED
        return self.SKY_STATE_OFF

    def getActiveApplication(self):
        try:
            result = self.APP_EPG
            apps = self._callSkyWebSocket(WS_CURRENT_APPS)
            if apps is None:
                return result
            app = next(
                a for a in apps["apps"] if a["status"] == self.APP_STATUS_VISIBLE
            )["appId"]

            # app = "com.roku"
            result = app

            return result
        except Exception:
            return result

    def getCurrentMedia(self):
        result = {
            "channel": None,
            "imageUrl": None,
            "title": None,
            "season": None,
            "episode": None,
            "sid": None,
            "live": False,
        }
        response = self._callSkySOAPService(UPNP_GET_MEDIA_INFO)
        if response is not None:
            currentURI = response[CURRENT_URI]
            if currentURI is not None:
                if XSI in currentURI:
                    # Live content
                    sid = int(currentURI[6:], 16)

                    if self._country == "test":
                        sid = 74

                    channel = self._getChannelNode(sid)["channel"]
                    result.update({"sid": sid, "live": True})
                    result.update({"channel": channel})
                    chid = "".join(e for e in channel.casefold() if e.isalnum())
                    result.update({"imageUrl": self._buildCloudFrontUrl(sid, chid)})
                elif PVR in currentURI:
                    # Recorded content
                    pvrId = "P" + currentURI[11:]
                    recording = self._http_json(REST_RECORDING_DETAILS.format(pvrId))
                    result.update({"channel": recording["details"]["cn"]})
                    result.update({"title": recording["details"]["t"]})
                    if (
                        "seasonnumber" in recording["details"]
                        and "episodenumber" in recording["details"]
                    ):
                        result.update({"season": recording["details"]["seasonnumber"]})
                        result.update(
                            {"episode": recording["details"]["episodenumber"]}
                        )
                    if "programmeuuid" in recording["details"]:
                        programmeuuid = recording["details"]["programmeuuid"]
                        imageUrl = self._remoteCountry.pvr_image_url.format(
                            str(programmeuuid)
                        )
                        if "osid" in recording["details"]:
                            osid = recording["details"]["osid"]
                            imageUrl += "?sid=" + str(osid)
                        result.update({"imageUrl": imageUrl})
        return result

    def getEpgData(self, sid, epgDate):
        channelno = self._getChannelNode(sid)["channelno"]
        return self._remoteCountry.getEpgData(sid, channelno, epgDate)

    def getProgrammeFromEpg(self, sid, epgDate, queryDate):
        epgData = self.getEpgData(sid, epgDate)
        if epgData is None:
            return None

        try:
            programme = next(
                p
                for p in epgData
                if p["starttime"] <= queryDate and p["endtime"] >= queryDate
            )
            return programme

        except StopIteration:
            return PAST_END_OF_EPG

    def getCurrentLiveTVProgramme(self, sid):
        try:
            result = {"title": None, "season": None, "episode": None, "imageUrl": None}
            queryDate = datetime.utcnow()
            programme = self.getProgrammeFromEpg(sid, queryDate, queryDate)
            if programme == PAST_END_OF_EPG:
                programme = self.getProgrammeFromEpg(
                    sid, queryDate + timedelta(days=1), queryDate
                )
            result.update({"title": programme["title"]})
            result.update({"episode": programme["episode"]})
            result.update({"season": programme["season"]})
            result.update({"imageUrl": programme["imageUrl"]})
            return result
        except Exception as err:
            _LOGGER.exception(f"X0030 - Error occurred: {self._host} : {sid} : {err}")
            return result

    def press(self, sequence):
        if isinstance(sequence, list):
            for item in sequence:
                if item not in self.commands:
                    _LOGGER.error(
                        "E0010 - Invalid command: {self._host} : {0}".format(item)
                    )
                    break
                self._sendCommand(self.commands[item.casefold()])
                time.sleep(0.5)
        else:
            if sequence not in self.commands:
                _LOGGER.error(
                    "E0020 - Invalid command: {self._host} : {0}".format(sequence)
                )
            else:
                self._sendCommand(self.commands[sequence])

    def _http_json(self, path, headers=None) -> str:
        response = requests.get(
            self.REST_BASE_URL.format(self._host, self._jsonport, path),
            timeout=self.TIMEOUT,
            headers=headers,
        )
        return json.loads(response.content)

    def _getSoapControlURL(self, descriptionIndex):
        try:
            descriptionUrl = SOAP_DESCRIPTION_BASE_URL.format(
                self._host, descriptionIndex
            )
            headers = {"User-Agent": SOAP_USER_AGENT}
            resp = requests.get(descriptionUrl, headers=headers, timeout=self.TIMEOUT)
            if resp.status_code == HTTPStatus.OK:
                description = xmltodict.parse(resp.text)
                deviceType = description["root"]["device"]["deviceType"]
                if not (SKYControl in deviceType):
                    return {"url": None, "status": "Not Found"}
                services = description["root"]["device"]["serviceList"]["service"]
                if not isinstance(services, list):
                    services = [services]
                playService = None
                for s in services:
                    if s["serviceId"] == SKY_PLAY_URN:
                        playService = s
                if playService is None:
                    return {"url": None, "status": "Not Found"}
                return {
                    "url": SOAP_CONTROL_BASE_URL.format(
                        self._host, playService["controlURL"]
                    ),
                    "status": "OK",
                }
            return {"url": None, "status": "Not Found"}
        except (requests.exceptions.Timeout) as err:
            _LOGGER.warning(
                f"W0020 - Control URL not accessible: {self._host} : {descriptionUrl}"
            )
            return {"url": None, "status": "Error"}
        except (requests.exceptions.ConnectionError) as err:
            _LOGGER.exception(f"X0070 - Connection error: {self._host} : {err}")
            return {"url": None, "status": "Error"}
        except Exception as err:
            _LOGGER.exception(f"X0010 - Other error occurred: {self._host} : {err}")
            return {"url": None, "status": "Error"}

    def _callSkySOAPService(self, method):
        try:
            payload = SOAP_PAYLOAD.format(method)
            headers = {
                "Content-Type": 'text/xml; charset="utf-8"',
                "SOAPACTION": SOAP_ACTION.format(method),
            }
            resp = requests.post(
                self._soapControlURL,
                headers=headers,
                data=payload,
                verify=True,
                timeout=self.TIMEOUT,
            )
            if resp.status_code == HTTPStatus.OK:
                xml = resp.text
                return xmltodict.parse(xml)["s:Envelope"]["s:Body"][
                    SOAP_RESPONSE.format(method)
                ]
            return None
        except requests.exceptions.RequestException:
            return None

    def _callSkyWebSocket(self, method):
        try:
            client = SkyWebSocket(WS_BASE_URL.format(self._host, method))
            client.connect()
            timeout = datetime.now() + timedelta(0, 5)
            while client.data is None and datetime.now() < timeout:
                pass
            client.close()
            if client.data is not None:
                return json.loads(
                    client.data.decode(DEFAULT_ENCODING), encoding=DEFAULT_ENCODING
                )
            return None
        except (AttributeError) as err:
            _LOGGER.debug(f"D0010 - Attribute Error occurred: {self._host} : {err}")
            return None
        except (TimeoutError) as err:
            _LOGGER.warning(f"W0030 - Websocket call failed: {self._host} : {method}")
            return {"url": None, "status": "Error"}
        except Exception as err:
            _LOGGER.exception(f"X0020 - Error occurred: {self._host} : {err}")
            return None

    def _sendCommand(self, code):
        commandBytes = bytearray(
            [4, 1, 0, 0, 0, 0, int(math.floor(224 + (code / 16))), code % 16]
        )

        try:
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        except socket.error as err:
            _LOGGER.exception(
                f"X0040 - Failed to create socket when sending command: {self._host} : {err}"
            )
            return

        try:
            client.connect((self._host, self._port))
        except Exception as err:
            _LOGGER.exception(
                f"X0050 - Failed to connect to client when sending command: {self._host} : {err}"
            )
            return

        l = 12
        timeout = time.time() + self.connectTimeout

        while 1:
            data = client.recv(1024)
            data = data

            if len(data) < 24:
                client.sendall(data[0:l])
                l = 1
            else:
                client.sendall(commandBytes)
                commandBytes[1] = 0
                client.sendall(commandBytes)
                client.close()
                break

            if time.time() > timeout:
                _LOGGER.error(
                    "E0030 - Timeout error sending command: {self._host} : {0}".format(
                        str(code)
                    )
                )
                break

    def _buildCloudFrontUrl(self, sid, chid):
        channel_image_url = self._remoteCountry.channel_image_url
        return channel_image_url.format(sid, chid)

    def _getChannelNode(self, sid):
        if self._country == "test":
            return {"channel": "Sky Arte HD", "channelno": "120"}

        channelNode = next(
            s for s in self._channels["services"] if s["sid"] == str(sid)
        )
        channel = channelNode["t"]
        channelno = channelNode["c"]
        return {"channel": channel, "channelno": channelno}


class SkyWebSocket(WebSocketClient):
    def __init__(self, url):
        super(SkyWebSocket, self).__init__(url)
        self.data = None

    def received_message(self, message):
        self.data = message.data
