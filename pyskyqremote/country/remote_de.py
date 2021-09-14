"""DE specific code."""
import json
import logging
from datetime import datetime, timedelta, timezone

import pytz
import requests

from ..classes.programme import Programme
from ..const import RESPONSE_OK, SKY_STATUS_LIVE
from .const_de import (
    CHANNEL_IMAGE_URL,
    CHANNEL_URL,
    LIVE_IMAGE_URL,
    PVR_IMAGE_URL,
    SCHEDULE_URL,
    TIMEZONE,
)

_LOGGER = logging.getLogger(__name__)


class SkyQCountry:
    """DE specific SkyQ."""

    def __init__(self):
        """Initialise DE remote."""
        self.pvr_image_url = PVR_IMAGE_URL
        self._channellist = None

        self._getChannels()

    def getEpgData(self, sid, channelno, channelName, epgDate):
        """Get EPG data for DE."""
        return self._getData(sid, channelno, channelName, epgDate)

    def buildChannelImageUrl(self, sid, channelname):
        """Build the channel image URL."""
        for channel in self._channellist:
            if str(channel["sid"]) == str(sid):
                return CHANNEL_IMAGE_URL.format(channel["clu"])

    def _getData(self, sid, channelno, channelName, epgDate):
        cid = None
        for channel in self._channellist:
            if str(channel["sid"]) == str(sid):
                cid = channel["ci"]

        milliDate = int(epgDate.replace(tzinfo=timezone.utc).timestamp() * 1000)
        berlinDT = epgDate.replace(tzinfo=pytz.utc).astimezone(pytz.timezone(TIMEZONE))
        berlinDate = berlinDT.strftime("%Y-%m-%dT")

        epgUrl = SCHEDULE_URL
        programmes = set()

        headers = {
            "Content-Type": 'application/json; charset="utf-8"',
        }
        payload = json.dumps(
            {
                "d": milliDate,
                "lt": 6,
                "t": 0,
                "s": 0,
                "pn": 1,
                "sto": 10,
                "epp": 50,
                "cil": [cid],
            }
        )

        resp = requests.post(
            epgUrl,
            headers=headers,
            data=payload,
            verify=True,
            timeout=10,
        )
        epgData = resp.json()["el"] if resp.status_code == RESPONSE_OK else None
        if epgData is None:
            return programmes

        if len(epgData) == 0:
            return programmes

        for p in epgData:
            starttimede = datetime.strptime(berlinDate + p["bst"], "%Y-%m-%dT%H:%M")
            starttime = (
                starttimede.replace(tzinfo=berlinDT.tzinfo)
                .astimezone(pytz.utc)
                .replace(tzinfo=None)
            )
            endtime = starttime + timedelta(minutes=p["len"])
            title = p["et"]
            season = None
            # if "seasonnumber" in p:
            #     if p["seasonnumber"] > 0:
            #         season = p["seasonnumber"]
            episode = None
            # if "episodenumber" in p:
            #     if p["episodenumber"] > 0:
            #         episode = p["episodenumber"]
            programmeuuid = None
            imageUrl = None
            # if "programmeuuid" in p:
            programmeuuid = str(p["ei"])
            if "pu" in p:
                imageUrl = LIVE_IMAGE_URL.format(p["pu"])
            elif "clu" in p:
                imageUrl = LIVE_IMAGE_URL.format(p["clu"])

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
            self._channellist = resp.json()
