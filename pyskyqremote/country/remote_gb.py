"""UK specific code."""
import logging
from datetime import datetime

import requests

from ..classes.programme import Programme
from ..const import RESPONSE_OK, SKY_STATUS_LIVE
from .const_gb import CHANNEL_IMAGE_URL, LIVE_IMAGE_URL, PVR_IMAGE_URL, SCHEDULE_URL

_LOGGER = logging.getLogger(__name__)


class SkyQCountry:
    """UK specific SkyQ."""

    def __init__(self):
        """Initialise UK remote."""
        self.pvr_image_url = PVR_IMAGE_URL

    def getEpgData(self, sid, channelno, channelName, epgDate):
        """Get EPG data for UK."""
        return self._getData(sid, channelno, channelName, epgDate)

    def buildChannelImageUrl(self, sid, channelname):
        """Build the channel image URL."""
        return CHANNEL_IMAGE_URL.format(sid)

    def _getData(self, sid, channelno, channelName, epgDate):
        epgDateStr = epgDate.strftime("%Y%m%d")

        epgUrl = SCHEDULE_URL.format(sid, epgDateStr)
        programmes = set()

        resp = requests.get(epgUrl)
        epgData = resp.json()["schedule"] if resp.status_code == RESPONSE_OK else None
        if epgData is None:
            return programmes

        if len(epgData) == 0:
            return programmes

        for p in epgData[0]["events"]:
            starttime = datetime.utcfromtimestamp(p["st"])
            endtime = datetime.utcfromtimestamp(p["st"] + p["d"])
            title = p["t"]
            season = None
            if "seasonnumber" in p and p["seasonnumber"] > 0:
                season = p["seasonnumber"]
            episode = None
            if "episodenumber" in p and p["episodenumber"] > 0:
                episode = p["episodenumber"]
            programmeuuid = None
            imageUrl = None
            if "programmeuuid" in p:
                programmeuuid = str(p["programmeuuid"])
                imageUrl = LIVE_IMAGE_URL.format(programmeuuid)

            eid = p["eid"]
            programme = Programme(
                programmeuuid,
                starttime,
                endtime,
                title,
                season,
                episode,
                imageUrl,
                channelName,
                SKY_STATUS_LIVE,
                "n/a",
                eid,
            )
            programmes.add(programme)

        return programmes
