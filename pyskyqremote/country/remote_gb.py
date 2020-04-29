"""UK specific code."""
from datetime import datetime
import logging
import requests

from ..const import RESPONSE_OK
from ..programme import Programme

from .const_gb import CHANNEL_IMAGE_URL, PVR_IMAGE_URL, SCHEDULE_URL, LIVE_IMAGE_URL

_LOGGER = logging.getLogger(__name__)


class SkyQCountry:
    """UK specific SkyQ."""

    def __init__(self, host):
        """Initialise UK remote."""
        self.channel_image_url = CHANNEL_IMAGE_URL
        self.pvr_image_url = PVR_IMAGE_URL
        self.epgData = set()

        self._lastEpgUrl = None
        self._host = host

    def getEpgData(self, sid, channelno, epgDate):
        """Get EPG data for UK."""
        programmes = set()
        epgDateStr = epgDate.strftime("%Y%m%d")
        epgUrl = SCHEDULE_URL.format(sid, epgDateStr)
        epgData = None
        if self._lastEpgUrl is None or self._lastEpgUrl != epgUrl:
            resp = requests.get(epgUrl)
            if resp.status_code == RESPONSE_OK:
                epgData = resp.json()["schedule"]
                self._lastEpgUrl = epgUrl
        else:
            return self.epgData

        if epgData is None:
            return programmes

        if len(epgData[0]["events"]) == 0:
            _LOGGER.warning(
                f"W0010UK - Programme data not found. Do you need to set 'live_tv' to False? {self._host}"
            )
            return programmes

        for p in epgData[0]["events"]:
            starttime = datetime.utcfromtimestamp(p["st"])
            endtime = datetime.utcfromtimestamp(p["st"] + p["d"])
            title = p["t"]
            season = None
            if "seasonnumber" in p:
                if p["seasonnumber"] > 0:
                    season = p["seasonnumber"]
            episode = None
            if "episodenumber" in p:
                if p["episodenumber"] > 0:
                    episode = p["episodenumber"]
            programmeuuid = None
            imageUrl = None
            if "programmeuuid" in p:
                programmeuuid = str(p["programmeuuid"])
                imageUrl = LIVE_IMAGE_URL.format(programmeuuid)

            programme = Programme(
                programmeuuid, starttime, endtime, title, season, episode, imageUrl
            )
            programmes.add(programme)
        self.epgData = programmes
        return self.epgData
