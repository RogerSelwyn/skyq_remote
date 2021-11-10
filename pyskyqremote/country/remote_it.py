"""Italy specific code."""
import logging
from datetime import datetime, timedelta

import requests

from ..classes.programme import Programme
from ..const import RESPONSE_OK, SKY_STATUS_LIVE
from .const_it import CHANNEL_IMAGE_URL, CHANNEL_URL, LIVE_IMAGE_URL, PVR_IMAGE_URL, SCHEDULE_URL

_LOGGER = logging.getLogger(__name__)


class SkyQCountry:
    """Italy specific SkyQ."""

    def __init__(self):
        """Initialise Italy remote."""
        self.pvr_image_url = PVR_IMAGE_URL
        self._channellist = None

        self._getChannels()

    def getEpgData(self, sid, channelno, channelName, epgDate):
        """Get EPG data for Italy."""
        epgPrev = epgDate - timedelta(days=1)
        queryDateFrom = epgPrev.strftime("%Y-%m-%dT22:00:00Z")
        queryDateTo = epgDate.strftime("%Y-%m-%dT23:59:59Z")
        epgData = self._getData(sid, channelno, channelName, queryDateFrom, queryDateTo)

        midnight = datetime.combine(epgDate.date(), datetime.min.time())

        return [p for p in epgData if p.endtime >= midnight]

    def buildChannelImageUrl(self, sid, channelname):
        """Build the channel image URL."""
        chid = "".join(e for e in channelname.casefold() if e.isalnum())
        return CHANNEL_IMAGE_URL.format(sid, chid)

    def _getData(self, sid, channelno, channelName, queryDateFrom, queryDateTo):
        cid = None
        for channel in self._channellist:
            if str(channel["number"]) == str(channelno):
                cid = channel["id"]

        epgUrl = SCHEDULE_URL.format(cid, queryDateFrom, queryDateTo)
        programmes = set()

        try:
            resp = requests.get(epgUrl)
        except requests.exceptions.ConnectionError:
            return programmes

        epgData = resp.json()["events"] if resp.status_code == RESPONSE_OK else None
        if epgData is None:
            return programmes

        if len(epgData) == 0:
            return programmes

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
            if "seasonNumber" in p["content"] and p["content"]["seasonNumber"] > 0:
                season = p["content"]["seasonNumber"]
            episode = None
            if "episodeNumber" in p["content"] and p["content"]["episodeNumber"] > 0:
                episode = p["content"]["episodeNumber"]
            programmeuuid = None
            imageUrl = None
            if "uuid" in p["content"]:
                programmeuuid = str(p["content"]["uuid"])
                imageUrl = LIVE_IMAGE_URL.format(programmeuuid)

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
            )
            programmes.add(programme)

        return programmes

    def _getChannels(self):
        resp = requests.get(CHANNEL_URL)
        if resp.status_code == RESPONSE_OK:
            self._channellist = resp.json()["channels"]
