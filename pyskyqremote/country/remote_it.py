"""Italy specific code."""
import logging
from datetime import datetime, timedelta

import requests

from ..classes.programme import Programme
from ..const import RESPONSE_OK, SKY_STATUS_LIVE
from .const_it import (CHANNEL_IMAGE_URL, CHANNEL_URL, LIVE_IMAGE_URL,
                       PVR_IMAGE_URL, SCHEDULE_URL)

_LOGGER = logging.getLogger(__name__)


class SkyQCountry:
    """Italy specific SkyQ."""

    def __init__(self):
        """Initialise Italy remote."""
        self.pvr_image_url = PVR_IMAGE_URL
        self._channellist = None

        self._get_channels()

    def get_epg_data(self, sid, channelno, channel_name, epg_date):
        """Get EPG data for Italy."""
        epg_prev = epg_date - timedelta(days=1)
        query_date_from = epg_prev.strftime("%Y-%m-%dT22:00:00Z")
        query_date_to = epg_date.strftime("%Y-%m-%dT23:59:59Z")
        epg_data = self._get_data(
            sid, channelno, channel_name, query_date_from, query_date_to
        )

        midnight = datetime.combine(epg_date.date(), datetime.min.time())

        return [p for p in epg_data if p.endtime >= midnight]

    def build_channel_image_url(self, sid, channelname):
        """Build the channel image URL."""
        chid = "".join(e for e in channelname.casefold() if e.isalnum())
        return CHANNEL_IMAGE_URL.format(sid, chid)

    def _get_data(
        self, sid, channelno, channel_name, query_date_from, query_date_to
    ):  # pylint: disable=unused-argument
        programmes = set()

        try:
            epg_data = self._get_epg_data(channelno, query_date_from, query_date_to)
        except requests.exceptions.ConnectionError:
            return programmes

        if epg_data is None:
            return programmes

        if len(epg_data) == 0:
            return programmes

        epg_data_len = len(epg_data) - 1
        for index, programme in enumerate(epg_data):
            starttime = datetime.strptime(programme["starttime"], "%Y-%m-%dT%H:%M:%SZ")
            if index < epg_data_len:
                endtime_str = epg_data[index + 1]["starttime"]
            else:
                endtime_str = programme["endtime"]
            endtime = datetime.strptime(endtime_str, "%Y-%m-%dT%H:%M:%SZ")
            title = programme["eventTitle"]
            season = None
            if (
                "seasonNumber" in programme["content"]
                and programme["content"]["seasonNumber"] > 0
            ):
                season = programme["content"]["seasonNumber"]
            episode = None
            if (
                "episodeNumber" in programme["content"]
                and programme["content"]["episodeNumber"] > 0
            ):
                episode = programme["content"]["episodeNumber"]
            programmeuuid = None
            image_url = None
            if "uuid" in programme["content"]:
                programmeuuid = str(programme["content"]["uuid"])
                image_url = LIVE_IMAGE_URL.format(programmeuuid)

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
            )
            programmes.add(programme)

        return programmes

    def _get_channels(self):
        resp = requests.get(CHANNEL_URL)
        if resp.status_code == RESPONSE_OK:
            self._channellist = resp.json()["channels"]

    def _get_epg_data(self, channelno, query_date_from, query_date_to):

        cid = None
        for channel in self._channellist:
            if str(channel["number"]) == str(channelno):
                cid = channel["id"]

        epg_url = SCHEDULE_URL.format(cid, query_date_from, query_date_to)

        resp = requests.get(epg_url)

        return resp.json()["events"] if resp.status_code == RESPONSE_OK else None
