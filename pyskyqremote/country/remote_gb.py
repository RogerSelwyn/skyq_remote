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
        self._host = host

    def getEpgData(self, sid, channelno, epgDate):
        """Get EPG data for UK."""
        epgDateStr = epgDate.strftime("%Y%m%d")

        epgUrl = SCHEDULE_URL.format(sid, epgDateStr)
        epgData = None
        programmes = set()

        resp = requests.get(epgUrl)
        if resp.status_code == RESPONSE_OK:
            epgData = resp.json()["schedule"]

        if epgData is None:
            return programmes

        if len(epgData) == 0:
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

        return programmes