"""DE specific code."""
import json
import logging
from datetime import datetime, timedelta, timezone

import pytz
import requests

from ..classes.programme import Programme
from ..const import RESPONSE_OK, SKY_STATUS_LIVE
from .const_de import (CHANNEL_IMAGE_URL, CHANNEL_URL, LIVE_IMAGE_URL,
                       PVR_IMAGE_URL, SCHEDULE_URL, TIMEZONE)

_LOGGER = logging.getLogger(__name__)


class SkyQCountry:
    """DE specific SkyQ."""

    def __init__(self):
        """Initialise DE remote."""
        self.pvr_image_url = PVR_IMAGE_URL
        self._channellist = None

        self._get_channels()

    def get_epg_data(self, sid, channelno, channel_name, epg_date):
        """Get EPG data for DE."""
        return self._get_data(sid, channelno, channel_name, epg_date)

    def build_channel_image_url(
        self, sid, channelname
    ):  # pylint: disable=unused-argument
        """Build the channel image URL."""
        for channel in self._channellist:
            if str(channel["sid"]) == str(sid):
                return CHANNEL_IMAGE_URL.format(channel["clu"])

    def _get_data(
        self, sid, channelno, channel_name, epg_date
    ):  # pylint: disable=unused-argument

        berlin_dt = epg_date.replace(tzinfo=pytz.utc).astimezone(
            pytz.timezone(TIMEZONE)
        )
        berlin_date = berlin_dt.strftime("%Y-%m-%dT")

        programmes = set()
        epg_data = self._get_epg_data(sid, epg_date)
        if epg_data is None:
            return programmes

        if len(epg_data) == 0:
            return programmes

        for programme in epg_data:
            starttimede = datetime.strptime(
                berlin_date + programme["bst"], "%Y-%m-%dT%H:%M"
            )
            starttime = (
                starttimede.replace(tzinfo=berlin_dt.tzinfo)
                .astimezone(pytz.utc)
                .replace(tzinfo=None)
            )
            endtime = starttime + timedelta(minutes=programme["len"])
            title = programme["et"]
            programmeuuid = str(programme["ei"])
            image_url = None
            if "pu" in programme:
                image_url = LIVE_IMAGE_URL.format(programme["pu"])
            elif "clu" in programme:
                image_url = LIVE_IMAGE_URL.format(programme["clu"])

            programme = Programme(
                programmeuuid,
                starttime,
                endtime,
                title,
                None,
                None,
                image_url,
                channel_name,
                SKY_STATUS_LIVE,
            )
            programmes.add(programme)

        return programmes

    def _get_channels(self):
        resp = requests.get(CHANNEL_URL)
        if resp.status_code == RESPONSE_OK:
            self._channellist = resp.json()

    def _get_epg_data(self, sid, epg_date):
        cid = None
        milli_date = int(epg_date.replace(tzinfo=timezone.utc).timestamp() * 1000)
        for channel in self._channellist:
            if str(channel["sid"]) == str(sid):
                cid = channel["ci"]

        epg_url = SCHEDULE_URL

        headers = {
            "Content-Type": 'application/json; charset="utf-8"',
        }
        payload = json.dumps(
            {
                "d": milli_date,
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
            epg_url,
            headers=headers,
            data=payload,
            verify=True,
            timeout=10,
        )
        return resp.json()["el"] if resp.status_code == RESPONSE_OK else None
