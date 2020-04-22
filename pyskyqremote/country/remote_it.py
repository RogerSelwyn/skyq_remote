"""Italy specific code."""
from datetime import datetime
import logging
import requests

from pyskyqremote.channel import Programme

RESPONSE_OK = 200

SCHEDULE_URL = "https://apid.sky.it/gtv/v1/events?from={1}&to={2}&pageSize=50&pageNum=0&env=DTH&channels={0}"
LIVE_IMAGE_URL = "https://ethaneurope.it.imageservice.sky.com/pd-image/{0}/16-9"
PVR_IMAGE_URL = "https://ethaneurope.it.imageservice.sky.com/pd-image/{0}/16-9"
CHANNEL_URL = "https://apid.sky.it/gtv/v1/channels?env=DTH"
CHANNEL_IMAGE_URL = (
    "https://ethaneurope.it.imageservice.sky.com/pd-logo/skychb_{0}{1}/600/600"
)

_LOGGER = logging.getLogger(__name__)


class SkyQCountry:
    """Italy specific SkyQ."""

    def __init__(self, host):
        """Initialise Italy remote."""
        self.channel_image_url = CHANNEL_IMAGE_URL
        self.pvr_image_url = PVR_IMAGE_URL
        self.epgData = None

        self._lastEpgUrl = None
        self._host = host
        self._channellist = None

        self._getChannels()

    def getEpgData(self, sid, channelno, epgDate):
        """Get EPG data for Italy."""
        queryDateFrom = epgDate.strftime("%Y-%m-%dT00:00:00Z")
        queryDateTo = epgDate.strftime("%Y-%m-%dT23:59:59Z")

        cid = None
        for channel in self._channellist:
            if str(channel["number"]) == str(channelno):
                cid = channel["id"]

        epgData = None
        epgUrl = SCHEDULE_URL.format(cid, queryDateFrom, queryDateTo)
        if self._lastEpgUrl is None or self._lastEpgUrl != epgUrl:
            resp = requests.get(epgUrl)
            if resp.status_code == RESPONSE_OK:
                epgData = resp.json()["events"]
                self._lastEpgUrl = epgUrl
        else:
            return self.epgData

        if epgData is None:
            return None
        if len(epgData) == 0:
            _LOGGER.warning(
                f"W0010IT - Programme data not found. Do you need to set 'live_tv' to False? {self._host}"
            )
            return None

        self.epgData = []
        epgDataLen = len(epgData) - 1
        for index, p in enumerate(epgData):
            starttime = datetime.strptime(p["starttime"], "%Y-%m-%dT%H:%M:%SZ")
            if index < epgDataLen:
                endtimeStr = epgData[index + 1]["starttime"]
            else:
                endtimeStr = p["endtime"]
            endtime = datetime.strptime(endtimeStr, "%Y-%m-%dT%H:%M:%SZ")
            title = p["eventTitle"]
            season = None
            if "seasonNumber" in p["content"]:
                if p["content"]["seasonNumber"] > 0:
                    season = p["content"]["seasonNumber"]
            episode = None
            if "episodeNumber" in p["content"]:
                if p["content"]["episodeNumber"] > 0:
                    episode = p["content"]["episodeNumber"]
            programmeuuid = None
            imageUrl = None
            if "uuid" in p["content"]:
                programmeuuid = str(p["content"]["uuid"])
                imageUrl = LIVE_IMAGE_URL.format(programmeuuid)

            programme = vars(
                Programme(
                    programmeuuid, starttime, endtime, title, season, episode, imageUrl
                )
            )

            self.epgData.append(programme)
        return self.epgData

    def _getChannels(self):
        resp = requests.get(CHANNEL_URL)
        if resp.status_code == RESPONSE_OK:
            self._channellist = resp.json()["channels"]
