"""Python module for accessing SkyQ box and EPG, and sending commands."""
import importlib
import logging
import time
from collections import OrderedDict
from datetime import datetime, timedelta
from operator import attrgetter

import pycountry
import requests

from .classes.app import App
from .classes.channel import Channel
from .classes.channelepg import ChannelEPG
from .classes.channellist import ChannelList
from .classes.device import Device
from .classes.favourite import Favourite
from .classes.favouritelist import FavouriteList
from .classes.media import Media
from .classes.programme import Programme
from .classes.recordings import Recordings
from .const import (
    APP_EPG,
    APP_STATUS_VISIBLE,
    COMMANDS,
    CURRENT_TRANSPORT_STATE,
    CURRENT_URI,
    EPG_ERROR_NO_DATA,
    EPG_ERROR_PAST_END,
    KNOWN_COUNTRIES,
    PVR,
    REST_CHANNEL_LIST,
    REST_FAVOURITES,
    REST_PATH_APPS,
    REST_PATH_DEVICEINFO,
    REST_PATH_SYSTEMINFO,
    REST_RECORDING_DETAILS,
    REST_RECORDINGS_LIST,
    SKY_STATE_NOMEDIA,
    SKY_STATE_OFF,
    SKY_STATE_ON,
    SKY_STATE_PAUSED,
    SKY_STATE_PLAYING,
    SKY_STATE_STANDBY,
    SKY_STATE_STOPPED,
    SKY_STATE_TRANSITIONING,
    UPNP_GET_MEDIA_INFO,
    UPNP_GET_TRANSPORT_INFO,
    WS_CURRENT_APPS,
    XSI,
)
from .const_test import TEST_CHANNEL_LIST
from .utils import deviceAccess

_LOGGER = logging.getLogger(__name__)


class SkyQRemote:
    """SkyQRemote is the instantiation of the SKYQ remote ccontrol."""

    commands = COMMANDS

    def __init__(self, host, epgCacheLen=20, port=49160, jsonPort=9006):
        """Stand up a new SkyQ box."""
        self.deviceSetup = False
        self._host = host
        self._remoteCountry = None
        self._overrideCountry = None
        self._epgCountryCode = None
        self._serialNumber = None
        self._test_channel = None
        self._port = port
        self._jsonport = jsonPort
        self._soapControlURL = None
        self._channel = None
        self._lastEpg = None
        self._programme = None
        self._recordedProgramme = None
        self._lastProgrammeEpg = None
        self._epgCache = OrderedDict()
        self._lastPvrId = None
        self._currentApp = APP_EPG
        self._channels = []
        self._apps = {}
        self._error = False
        self._deviceAccess = deviceAccess(self._host)
        self._epgCacheLen = epgCacheLen
        self._channellist = None
        self._favouritelist = None

        deviceInfo = self.getDeviceInformation()
        if not deviceInfo:
            return None

        self._setupDevice()

    def powerStatus(self) -> str:
        """Get the power status of the Sky Q box."""
        if not self._remoteCountry:
            self._setupRemote()

        if self._soapControlURL is None:
            return SKY_STATE_OFF

        output = self._retrieveInformation(REST_PATH_SYSTEMINFO)
        if output is None:
            return SKY_STATE_OFF
        if "activeStandby" in output and output["activeStandby"] is True:
            return SKY_STATE_STANDBY

        return SKY_STATE_ON

    def getCurrentState(self):
        """Get current state of the SkyQ box."""
        if not self._remoteCountry:
            self._setupRemote()

        if self._soapControlURL is None:
            return SKY_STATE_OFF

        response = self._deviceAccess.callSkySOAPService(self._soapControlURL, UPNP_GET_TRANSPORT_INFO)
        if response is not None:
            state = response[CURRENT_TRANSPORT_STATE]
            if state in [SKY_STATE_NOMEDIA, SKY_STATE_STOPPED]:
                return SKY_STATE_STANDBY
            if state in [SKY_STATE_PLAYING, SKY_STATE_TRANSITIONING]:
                return SKY_STATE_PLAYING
            if state == SKY_STATE_PAUSED:
                return SKY_STATE_PAUSED
        return SKY_STATE_OFF

    def getActiveApplication(self):
        """Get the active application on Sky Q box."""
        try:
            apps = self._deviceAccess.callSkyWebSocket(WS_CURRENT_APPS)
            if apps is None:
                return self._currentApp

            self._currentApp = next(a for a in apps["apps"] if a["status"] == APP_STATUS_VISIBLE)["appId"]

            return App(self._currentApp, self._get_app_title(self._currentApp))
        except Exception:
            return App(self._currentApp, self._get_app_title(self._currentApp))

    def getCurrentMedia(self):
        """Get the currently playing media on the SkyQ box."""
        channel = None
        channelno = None
        imageUrl = None
        sid = None
        pvrId = None
        live = False

        response = self._deviceAccess.callSkySOAPService(self._soapControlURL, UPNP_GET_MEDIA_INFO)
        if response is None:
            return None

        currentURI = response[CURRENT_URI]
        if currentURI is None:
            return None

        if XSI in currentURI:
            sid = self._test_channel or int(currentURI[6:], 16)
            live = True
            channelNode = self._getChannelNode(sid)
            if channelNode:
                channel = channelNode["channel"]
                channelno = channelNode["channelno"]
                imageUrl = self._remoteCountry.buildChannelImageUrl(sid, channel)
        elif PVR in currentURI:
            # Recorded content
            pvrId = "P" + currentURI[11:]
            live = False

        return Media(channel, channelno, imageUrl, sid, pvrId, live)

    def getEpgData(self, sid, epgDate, days=2):
        """Get EPG data for the specified channel/date."""
        epg = f"{str(sid)} {'{:0>2d}'.format(days)} {epgDate.strftime('%Y%m%d')}"

        if sid in self._epgCache and self._epgCache[sid]["epg"] == epg:
            return self._epgCache[sid]["channel"]
        self._lastEpg = epg

        channelNo = None
        channelName = None
        channelImageUrl = None
        programmes = set()

        channelNode = self._getChannelNode(sid)
        if channelNode:
            channelNo = channelNode["channelno"]
            channelName = channelNode["channel"]
            channelImageUrl = self._remoteCountry.buildChannelImageUrl(sid, channelName)

            for n in range(days):
                programmesData = self._remoteCountry.getEpgData(
                    sid, channelNo, channelName, epgDate + timedelta(days=n)
                )
                if len(programmesData) > 0:
                    programmes = programmes.union(programmesData)
                else:
                    break

        self._channel = ChannelEPG(sid, channelNo, channelName, channelImageUrl, sorted(programmes))
        self._epgCache[sid] = {
            "epg": epg,
            "channel": self._channel,
            "updatetime": datetime.utcnow(),
        }
        self._epgCache = OrderedDict(sorted(self._epgCache.items(), key=lambda x: x[1]["updatetime"], reverse=True))
        while len(self._epgCache) > self._epgCacheLen:
            self._epgCache.popitem(last=True)

        return self._channel

    def getProgrammeFromEpg(self, sid, epgDate, queryDate):
        """Get programme from EPG for specfied time and channel."""
        sidint = 0
        try:
            sidint = int(sid)
        except ValueError:
            if not self._error:
                self._error = True
                _LOGGER.info(
                    f"I0010 - Programme data not found for host: {self._host}/{self._overrideCountry} sid: {sid} : {epgDate}"
                )
                return EPG_ERROR_NO_DATA

            self._error = False

        programmeEpg = f"{str(sidint)} {epgDate.strftime('%Y%m%d')}"
        if self._lastProgrammeEpg == programmeEpg and queryDate < self._programme.endtime:
            return self._programme

        epgData = self.getEpgData(sidint, epgDate)

        if len(epgData.programmes) == 0:
            if not self._error:
                self._error = True
                _LOGGER.info(
                    f"I0020 - Programme data not found for host: {self._host}/{self._overrideCountry} sid: {sid} : {epgDate}"
                )
            return EPG_ERROR_NO_DATA

        self._error = False

        try:
            programme = next(p for p in epgData.programmes if p.starttime <= queryDate and p.endtime >= queryDate)

            self._programme = programme
            self._lastProgrammeEpg = programmeEpg
            return programme

        except StopIteration:
            return EPG_ERROR_PAST_END

    def getCurrentLiveTVProgramme(self, sid):
        """Get current live programme on the specified channel."""
        try:
            queryDate = datetime.utcnow()
            programme = self.getProgrammeFromEpg(sid, queryDate, queryDate)
            if not isinstance(programme, Programme):
                return None

            return programme
        except Exception as err:
            _LOGGER.exception(f"X0010 - Error occurred: {self._host} : {sid} : {err}")
            return None

    def getRecordings(self, status=None):
        """Get the list of available Recordings."""
        try:
            recordings = set()
            resp = self._deviceAccess.http_json(self._jsonport, REST_RECORDINGS_LIST)
            recData = resp["pvrItems"]
            for recording in recData:
                if recording["status"] == status or not status:
                    built = self._buildRecording(recording)
                    recordings.add(built)

            return Recordings(recordings)
        except requests.exceptions.ReadTimeout:
            _LOGGER.error(f"E0040 - Timeout retrieving recordings: {self._host}")
            return Recordings(recordings)

    def getRecording(self, pvrId):
        """Get the recording details."""
        if self._lastPvrId == pvrId:
            return self._recordedProgramme
        self._lastPvrId = pvrId

        resp = self._deviceAccess.http_json(self._jsonport, REST_RECORDING_DETAILS.format(pvrId))
        if "details" not in resp:
            _LOGGER.info(f"I0030 - Recording data not found for {pvrId}")
            return None

        recording = resp["details"]

        self._recordedProgramme = self._buildRecording(recording)
        return self._recordedProgramme

    def getDeviceInformation(self):
        """Get the device information from the SkyQ box."""
        deviceInfo = self._retrieveInformation(REST_PATH_DEVICEINFO)
        if not deviceInfo:
            return None

        systemInfo = self._retrieveInformation(REST_PATH_SYSTEMINFO)
        ASVersion = deviceInfo["ASVersion"]
        IPAddress = deviceInfo["IPAddress"]
        countryCode = deviceInfo["countryCode"]
        hardwareModel = systemInfo["hardwareModel"]
        hardwareName = deviceInfo["hardwareName"]
        manufacturer = systemInfo["manufacturer"]
        modelNumber = deviceInfo["modelNumber"]
        serialNumber = deviceInfo["serialNumber"]
        versionNumber = deviceInfo["versionNumber"]

        epgCountryCode = self._overrideCountry or countryCode.upper()
        if not epgCountryCode:
            _LOGGER.error(f"E0010 - No country identified: {self._host}")
            return None

        if epgCountryCode in KNOWN_COUNTRIES:
            epgCountryCode = KNOWN_COUNTRIES[epgCountryCode]

        self._epgCountryCode = epgCountryCode

        return Device(
            ASVersion,
            IPAddress,
            countryCode,
            epgCountryCode,
            hardwareModel,
            hardwareName,
            manufacturer,
            modelNumber,
            serialNumber,
            versionNumber,
        )

    def getChannelList(self):
        """Get Channel list for Sky Q box."""
        channels = self._getChannels()
        if not channels:
            return None

        channelitems = set()

        for c in channels:
            channelno = c["c"]
            channelname = c["t"]
            channelsid = c["sid"]
            channelImageUrl = None  # Not available yet
            sf = c["sf"]
            channel = Channel(channelno, channelname, channelsid, channelImageUrl, sf=sf)
            channelitems.add(channel)

        channelnosorted = sorted(channelitems, key=attrgetter("channelnoint"))
        self._channellist = ChannelList(sorted(channelnosorted, key=attrgetter("channeltype"), reverse=True))

        return self._channellist

    def getChannelInfo(self, channelNo):
        """Retrieve channel information for specified channelNo."""
        if not channelNo.isnumeric():
            return None

        try:
            channel = next(c for c in self._channels if c["c"] == channelNo)
        except StopIteration:
            return None

        channelno = channel["c"]
        channelname = channel["t"]
        channelsid = channel["sid"]
        channelImageUrl = self._remoteCountry.buildChannelImageUrl(channelsid, channelname)
        sf = channel["sf"]
        return Channel(channelno, channelname, channelsid, channelImageUrl, sf=sf)

    def getFavouriteList(self):
        """Retrieve the list of favourites."""
        favourites = self._deviceAccess.http_json(self._jsonport, REST_FAVOURITES)
        if not favourites or "favourites" not in favourites:
            return []

        if not self._channellist:
            self.getChannelList()

        favitems = set()

        for f in favourites["favourites"]:
            favlcn = f["lcn"]
            favsid = f["sid"]
            channelno = None
            channelname = None
            channel = next(c for c in self._channellist.channels if c.channelsid == f["sid"])
            if channel:
                channelno = channel.channelno
                channelname = channel.channelname
            favourite = Favourite(favlcn, channelno, channelname, favsid)
            favitems.add(favourite)

        favouritesorted = sorted(favitems, key=attrgetter("lcn"))
        self._favouritelist = FavouriteList(favouritesorted)

        return self._favouritelist

    def press(self, sequence):
        """Issue the specified sequence of commands to SkyQ box."""
        if isinstance(sequence, list):
            for item in sequence:
                if item.casefold() not in self.commands:
                    _LOGGER.error(f"E0020 - Invalid command: {self._host} : {item}")
                    break
                self._deviceAccess.sendCommand(self._port, self.commands[item.casefold()])
                time.sleep(0.5)
        elif sequence not in self.commands:
            _LOGGER.error(f"E0030 - Invalid command: {self._host} : {sequence}")
        else:
            self._deviceAccess.sendCommand(self._port, self.commands[sequence.casefold()])

    def setOverrides(self, overrideCountry=None, test_channel=None, jsonPort=None, port=None):
        """Override various items."""
        if overrideCountry:
            self._overrideCountry = overrideCountry
        if test_channel:
            self._test_channel = test_channel
        if jsonPort:
            self._jsonport = jsonPort
        if port:
            self.port = port

    def _getChannelNode(self, sid):
        channelNode = self._getNodeFromChannels(sid)

        if not channelNode:
            # Load the channel list for the first time.
            # It's also possible the channels may have changed since last HA restart, so reload them
            self._channels = self._getChannels()
            channelNode = self._getNodeFromChannels(sid)
        if not channelNode:
            return None

        channel = channelNode["t"]
        channelno = channelNode["c"]
        return {"channel": channel, "channelno": channelno}

    def _getChannels(self):
        # This is here because otherwise I can never validate code for a foreign device
        if self._test_channel:
            return TEST_CHANNEL_LIST
        channels = self._deviceAccess.http_json(self._jsonport, REST_CHANNEL_LIST)
        if channels and "services" in channels:
            return channels["services"]

        return []

    def _getNodeFromChannels(self, sid):
        return next((s for s in self._channels if s["sid"] == str(sid)), None)

    def _setupRemote(self):
        deviceInfo = self.getDeviceInformation()
        if not deviceInfo:
            return

        if not self.deviceSetup:
            self._setupDevice()

        if not self._remoteCountry and self.deviceSetup:
            SkyQCountry = self.importCountry(self._epgCountryCode)
            self._remoteCountry = SkyQCountry()

        if len(self._channels) == 0 and self._remoteCountry:
            self._channels = self._getChannels()

    def _setupDevice(self):

        url_index = 0
        self._soapControlURL = None
        while self._soapControlURL is None and url_index < 50:
            self._soapControlURL = self._deviceAccess.getSoapControlURL(url_index)["url"]
            url_index += 1

        self.deviceSetup = True

    def _retrieveInformation(self, rest_path):
        try:
            return self._deviceAccess.http_json(self._jsonport, rest_path)
        except (
            requests.exceptions.ConnectTimeout,
            requests.exceptions.ConnectionError,
            requests.exceptions.ReadTimeout,
        ):  # as err:
            # _LOGGER.debug(f"D0010 - Connection error: {self._host} : {err}")
            return None
        except Exception as err:
            _LOGGER.exception(f"X0020 - Error occurred: {self._host} : {err}")
            return None

    def importCountry(self, countryCode):
        """Work out the country for the Country Code."""
        try:
            country = pycountry.countries.get(alpha_3=countryCode).alpha_2.casefold()
            SkyQCountry = importlib.import_module("pyskyqremote.country.remote_" + country).SkyQCountry

        except (AttributeError, ModuleNotFoundError) as err:
            _LOGGER.warning(f"W0010 - Invalid country, defaulting to GBR: {self._host} : {countryCode} : {err}")

            from pyskyqremote.country.remote_gb import SkyQCountry

        return SkyQCountry

    def _buildRecording(self, recording):
        season = None
        episode = None
        starttime = None
        endtime = None
        programmeuuid = None
        channel = None
        imageUrl = None
        title = None
        status = None

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
            imageUrl = self._remoteCountry.buildChannelImageUrl(sid, channel)

        starttimestamp = 0
        if "ast" in recording:
            starttimestamp = recording["ast"]
        elif "st" in recording:
            starttimestamp = recording["st"]
        starttime = datetime.utcfromtimestamp(starttimestamp)

        if "finald" in recording:
            endtime = datetime.utcfromtimestamp(starttimestamp + recording["finald"])
        elif "schd" in recording:
            endtime = datetime.utcfromtimestamp(starttimestamp + recording["schd"])
        else:
            endtime = starttime

        status = recording["status"]

        return Programme(
            programmeuuid,
            starttime,
            endtime,
            title,
            season,
            episode,
            imageUrl,
            channel,
            status,
        )

    def _get_app_title(self, appId):
        if len(self._apps) == 0:
            apps = self._retrieveInformation(REST_PATH_APPS)
            if not apps:
                return None
            for a in apps["apps"]:
                self._apps[a["appId"]] = a["title"]

        return self._apps[appId] if appId in self._apps else None
