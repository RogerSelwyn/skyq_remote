"""UK specific code."""
import logging
from datetime import datetime

import requests

from ..classes.programme import Programme
from ..const import RESPONSE_OK, SKY_STATUS_LIVE
from .const_gb import (CHANNEL_IMAGE_URL, LIVE_IMAGE_URL, PVR_IMAGE_URL,
                       SCHEDULE_URL, TERRITORY)

_LOGGER = logging.getLogger(__name__)


class SkyQCountry:
    """UK specific SkyQ."""

    def __init__(self):
        """Initialise UK remote."""
        self.pvr_image_url = PVR_IMAGE_URL

    def get_epg_data(self, sid, channelno, channel_name, epg_date):
        """Get EPG data for UK."""
        return self._get_data(sid, channelno, channel_name, epg_date)

    def build_channel_image_url(self, sid, channelname):
        """Build the channel image URL."""
        chid = "".join(e for e in channelname.casefold() if e.isalnum())
        return CHANNEL_IMAGE_URL.format(sid, chid)

    def _get_data(
        self, sid, channelno, channel_name, epg_date
    ):  # pylint: disable=unused-argument
        programmes = set()
        epg_data = self._get_epg_data(sid, epg_date)
        if epg_data is None:
            return programmes

        if len(epg_data) == 0:
            return programmes

        for programme in epg_data[0]["events"]:
            starttime = datetime.utcfromtimestamp(programme["st"])
            endtime = datetime.utcfromtimestamp(programme["st"] + programme["d"])
            title = programme["t"]
            season = None
            if "seasonnumber" in programme and programme["seasonnumber"] > 0:
                season = programme["seasonnumber"]
            episode = None
            if "episodenumber" in programme and programme["episodenumber"] > 0:
                episode = programme["episodenumber"]
            programmeuuid = None
            image_url = None
            if "programmeuuid" in programme:
                programmeuuid = str(programme["programmeuuid"])
                image_url = LIVE_IMAGE_URL.format(programmeuuid)

            eid = programme["eid"]
            programme = Programme(
                programmeuuid,
                starttime,
                endtime,
                title,
                season,
                episode,
                image_url,
                channel_name,
                SKY_STATUS_LIVE,
                "n/a",
                eid,
            )
            programmes.add(programme)

        return programmes

    def _get_epg_data(self, sid, epg_date):
        epg_date_str = epg_date.strftime("%Y%m%d")

        epg_url = SCHEDULE_URL.format(sid, epg_date_str)
        headers = {
            "x-skyott-territory": TERRITORY,
            "x-skyott-provider": "SKY",
            "x-skyott-proposition": "SKYQ",
        }
        resp = requests.get(epg_url, headers=headers)
        return resp.json()["schedule"] if resp.status_code == RESPONSE_OK else None
