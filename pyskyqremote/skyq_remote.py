"""Python module for accessing SkyQ box and EPG, and sending commands."""
import time
import math
import socket
import requests
import json
import xmltodict
import logging
import importlib
import pycountry
from datetime import datetime, timedelta
from http import HTTPStatus

from ws4py.client.threadedclient import WebSocketClient

from .const import (
    SKY_PLAY_URN,
    SKYCONTROL,
    SOAP_ACTION,
    SOAP_CONTROL_BASE_URL,
    SOAP_DESCRIPTION_BASE_URL,
    SOAP_PAYLOAD,
    SOAP_RESPONSE,
    SOAP_USER_AGENT,
    UPNP_GET_MEDIA_INFO,
    UPNP_GET_TRANSPORT_INFO,
    WS_BASE_URL,
    WS_CURRENT_APPS,
    REST_BASE_URL,
    REST_CHANNEL_LIST,
    REST_RECORDING_DETAILS,
    REST_PATH_INFO,
    REST_PATH_DEVICEINFO,
    DEFAULT_ENCODING,
    CURRENT_URI,
    CURRENT_TRANSPORT_STATE,
    APP_STATUS_VISIBLE,
    PVR,
    XSI,
    PAST_END_OF_EPG,
    CONNECTTIMEOUT,
    TIMEOUT,
    COMMANDS,
    SKY_STATE_PLAYING,
    SKY_STATE_PAUSED,
    SKY_STATE_STANDBY,
    SKY_STATE_ON,
    SKY_STATE_OFF,
    APP_EPG,
)
from .const import TEST_CHANNEL_LIST
from .channel import Channel
from .programme import RecordedProgramme
from .media import Media

_LOGGER = logging.getLogger(__name__)


class SkyQRemote:
    """SkyQRemote is the instantiation of the SKYQ remote ccontrol."""

    commands = COMMANDS

    def __init__(
        self, host, overrideCountry=None, test_channel=None, port=49160, jsonport=9006,
    ):
        """Stand up a new SkyQ box."""
        self._host = host
        self._test_channel = test_channel
        self._port = port
        self._jsonport = jsonport
        self._overrideCountry = overrideCountry
        self.deviceSetup = False
        self.channel = None
        self._soapControlURL = None
        self._lastEpg = None

        self.powerStatus()
        if not self.deviceSetup:
            _LOGGER.error(
                f"E0060 - Device not switched on during restart: {self._host}"
            )

    def powerStatus(self) -> str:
        """Get the power status of the Sky Q box."""
        if not self.deviceSetup:
            self._setupDevice()

        if self._soapControlURL is None:
            return SKY_STATE_OFF
        try:
            output = self._http_json(REST_PATH_INFO)
            if "activeStandby" in output and output["activeStandby"] is False:
                return SKY_STATE_ON
            return SKY_STATE_STANDBY
        except (
            requests.exceptions.ConnectTimeout,
            requests.exceptions.ReadTimeout,
        ):
            return SKY_STATE_STANDBY
        except (requests.exceptions.ConnectionError):
            _LOGGER.info(
                f"I0010 - Device has control URL but connection request failed: {self._host}"
            )
            return SKY_STATE_OFF
        except Exception as err:
            _LOGGER.exception(f"X0060 - Error occurred: {self._host} : {err}")
            return SKY_STATE_STANDBY

    def getCurrentState(self):
        """Get current state of the SkyQ box."""
        if self.powerStatus() == SKY_STATE_OFF:
            return SKY_STATE_OFF
        if self.powerStatus() == SKY_STATE_STANDBY:
            return SKY_STATE_STANDBY
        response = self._callSkySOAPService(UPNP_GET_TRANSPORT_INFO)
        if response is not None:
            state = response[CURRENT_TRANSPORT_STATE]
            if state == SKY_STATE_PLAYING:
                return SKY_STATE_PLAYING
            if state == SKY_STATE_PAUSED:
                return SKY_STATE_PAUSED
        return SKY_STATE_STANDBY

    def getActiveApplication(self):
        """Get the active application on Sky Q box."""
        try:
            result = APP_EPG
            apps = self._callSkyWebSocket(WS_CURRENT_APPS)
            if apps is None:
                return result
            app = next(a for a in apps["apps"] if a["status"] == APP_STATUS_VISIBLE)[
                "appId"
            ]

            result = app

            return result
        except Exception:
            return result

    def getCurrentMediaJSON(self):
        """Get the currently playing media on the SkyQ box as json."""
        media = self.getCurrentMedia()
        if media:
            return media.as_json()
        else:
            return None

    def getCurrentMedia(self):
        """Get the currently playing media on the SkyQ box."""
        channel = None
        imageUrl = None
        sid = None
        pvrId = None
        live = False

        response = self._callSkySOAPService(UPNP_GET_MEDIA_INFO)
        if response is not None:
            currentURI = response[CURRENT_URI]
            if currentURI is not None:
                if XSI in currentURI:
                    # Live content
                    sid = int(currentURI[6:], 16)

                    if self._test_channel:
                        sid = self._test_channel

                    live = True
                    channel = self._getChannelNode(sid)["channel"]
                    imageUrl = self._buildChannelUrl(sid, channel)
                elif PVR in currentURI:
                    # Recorded content
                    pvrId = "P" + currentURI[11:]
                    live = False
        media = Media(channel, imageUrl, sid, pvrId, live)

        return media

    def getEpgDataJSON(self, sid, epgDate):
        """Get EPG data for the specified channel as json."""
        channel = self.getEpgData(sid, epgDate)
        if channel:
            return channel.as_json()
        else:
            return None

    def getEpgData(self, sid, epgDate, days=2):
        """Get EPG data for the specified channel/date."""
        channelNode = self._getChannelNode(sid)
        channelno = channelNode["channelno"]
        channelname = channelNode["channel"]
        channelImageUrl = self._buildChannelUrl(sid, channelname)

        epg = str(sid) + epgDate.strftime("%Y%m%d")
        if self._lastEpg == epg:
            return self.channel

        programmes = set()
        for n in range(days):
            programmesData = self._remoteCountry.getEpgData(
                sid, channelno, epgDate + timedelta(days=n)
            )
            if len(programmesData) > 0:
                programmes = programmes.union(programmesData)
            else:
                break

        self._lastEpg = epg

        if len(programmes) == 0:
            _LOGGER.info(f"I0020 - Programme data not found for {sid} : {epgDate}")

        self.channel = Channel(
            sid, channelno, channelname, channelImageUrl, sorted(programmes)
        )

        return self.channel

    def getProgrammeFromEpgJSON(self, sid, epgDate, queryDate):
        """Get programme from EPG for specfied time and channel as json."""
        programme = self.getProgrammeFromEpg(sid, epgDate, queryDate)
        if programme:
            return programme.as_json()
        else:
            return None

    def getProgrammeFromEpg(self, sid, epgDate, queryDate):
        """Get programme from EPG for specfied time and channel."""
        epgData = self.getEpgData(sid, epgDate)
        if len(epgData.programmes) == 0:
            return None

        try:
            programme = next(
                p
                for p in epgData.programmes
                if p.starttime <= queryDate and p.endtime >= queryDate
            )
            return programme

        except StopIteration:
            return PAST_END_OF_EPG

    def getCurrentLiveTVProgrammeJSON(self, sid):
        """Get current live programme on the specified channel as json."""
        programme = self.getCurrentLiveTVProgramme(sid)
        if programme:
            return programme.as_json()
        else:
            return None

    def getCurrentLiveTVProgramme(self, sid):
        """Get current live programme on the specified channel."""
        try:
            queryDate = datetime.utcnow()
            programme = self.getProgrammeFromEpg(sid, queryDate, queryDate)
            if programme is None:
                return None

            return programme
        except Exception as err:
            _LOGGER.exception(f"X0030 - Error occurred: {self._host} : {sid} : {err}")
            return None

    def getRecordingJSON(self, pvrId):
        """Get the recording details as json."""
        recording = self.getRecording(pvrId)
        if recording:
            return recording.as_json()
        else:
            return None

    def getRecording(self, pvrId):
        """Get the recording details."""
        season = None
        episode = None
        starttime = None
        endtime = None
        programmeuuid = None
        channel = None
        imageUrl = None
        title = None

        resp = self._http_json(REST_RECORDING_DETAILS.format(pvrId))
        if "details" not in resp:
            _LOGGER.info(f"I0030 - Recording data not found for {pvrId}")
            return None

        recording = resp["details"]

        channel = recording["cn"]
        title = recording["t"]
        if "seasonnumber" in recording and "episodenumber" in recording:
            season = recording["seasonnumber"]
            episode = recording["episodenumber"]
        if "programmeuuid" in recording:
            programmeuuid = recording["programmeuuid"]
            imageUrl = self._remoteCountry.pvr_image_url.format(str(programmeuuid))
        elif "osid" in recording:
            sid = str(recording["osid"])
            imageUrl = self._buildChannelUrl(sid)

        starttime = datetime.utcfromtimestamp(recording["ast"])
        if "finald" in recording:
            endtime = datetime.utcfromtimestamp(recording["ast"] + recording["finald"])
        elif "schd" in recording:
            endtime = datetime.utcfromtimestamp(recording["ast"] + recording["schd"])
        else:
            endtime = starttime

        programme = RecordedProgramme(
            programmeuuid, starttime, endtime, title, season, episode, imageUrl, channel
        )

        return programme

    def press(self, sequence):
        """Issue the specified sequence of commands to SkyQ box."""
        if isinstance(sequence, list):
            for item in sequence:
                if item.casefold() not in self.commands:
                    _LOGGER.error(f"E0010 - Invalid command: {self._host} : {item}")
                    break
                self._sendCommand(self.commands[item.casefold()])
                time.sleep(0.5)
        else:
            if sequence not in self.commands:
                _LOGGER.error(f"E0020 - Invalid command: {self._host} : {sequence}")
            else:
                self._sendCommand(self.commands[sequence.casefold()])

    def _http_json(self, path, headers=None) -> str:
        response = requests.get(
            REST_BASE_URL.format(self._host, self._jsonport, path),
            timeout=TIMEOUT,
            headers=headers,
        )
        return json.loads(response.content)

    def _getSoapControlURL(self, descriptionIndex):
        try:
            descriptionUrl = SOAP_DESCRIPTION_BASE_URL.format(
                self._host, descriptionIndex
            )
            headers = {"User-Agent": SOAP_USER_AGENT}
            resp = requests.get(descriptionUrl, headers=headers, timeout=TIMEOUT)
            if resp.status_code == HTTPStatus.OK:
                description = xmltodict.parse(resp.text)
                deviceType = description["root"]["device"]["deviceType"]
                if not (SKYCONTROL in deviceType):
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
        except (requests.exceptions.Timeout):
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
                timeout=TIMEOUT,
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
            client = _SkyWebSocket(WS_BASE_URL.format(self._host, method))
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
        except (TimeoutError):
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

        strlen = 12
        timeout = time.time() + CONNECTTIMEOUT

        while 1:
            data = client.recv(1024)
            data = data

            if len(data) < 24:
                client.sendall(data[0:strlen])
                strlen = 1
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

    def _buildChannelUrl(self, sid, channel):
        chid = "".join(e for e in channel.casefold() if e.isalnum())
        channel_image_url = self._remoteCountry.channel_image_url
        return channel_image_url.format(sid, chid)

    def _getChannelNode(self, sid):
        channelNode = next(
            s for s in self._channels["services"] if s["sid"] == str(sid)
        )
        channel = channelNode["t"]
        channelno = channelNode["c"]
        return {"channel": channel, "channelno": channelno}

    def _getDeviceInformation(self):
        try:
            resp = self._http_json(REST_PATH_DEVICEINFO)
            return resp
        except requests.exceptions.ConnectTimeout:
            return None
        except Exception as err:
            _LOGGER.exception(f"X0080 - Error occurred: {self._host} : {err}")
            return None

    def _setupDevice(self):
        """Set the remote up."""
        deviceInfo = self._getDeviceInformation()
        if not deviceInfo:
            return None

        alpha3 = None
        if self._overrideCountry:
            alpha3 = self._overrideCountry
        elif "countryCode" in deviceInfo:
            alpha3 = deviceInfo["countryCode"].upper()

        if not alpha3:
            _LOGGER.error(f"E0050 - No country identified: {self._host}")
            return None

        country = pycountry.countries.get(alpha_3=alpha3).alpha_2.casefold()

        url_index = 0
        self._soapControlURL = None
        while self._soapControlURL is None and url_index < 50:
            self._soapControlURL = self._getSoapControlURL(url_index)["url"]
            url_index += 1

        try:
            SkyQCountry = importlib.import_module(
                "pyskyqremote.country.remote_" + country
            ).SkyQCountry

            self._remoteCountry = SkyQCountry(self._host)
            if not self._test_channel:
                self._channels = self._http_json(REST_CHANNEL_LIST)
            else:
                self._channels = TEST_CHANNEL_LIST

            self.deviceSetup = True
            return "ok"

        except Exception as err:
            _LOGGER.error(f"E0040 - Invalid country: {self._host} : {alpha3} : {err}")
            return None


class _SkyWebSocket(WebSocketClient):
    def __init__(self, url):
        super(_SkyWebSocket, self).__init__(url)
        self.data = None

    def received_message(self, message):
        self.data = message.data
