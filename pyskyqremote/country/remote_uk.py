from datetime import datetime, timedelta
import logging
import requests

from pyskyqremote.channel import Programme

RESPONSE_OK = 200

SCHEDULE_URL = "http://awk.epgsky.com/hawk/linear/schedule/{1}/{0}"
LIVE_IMAGE_URL = "https://images.metadata.sky.com/pd-image/{0}/16-9"
PVR_IMAGE_URL = "https://images.metadata.sky.com/pd-image/{0}/16-9"
CHANNEL_IMAGE_URL = "https://d2n0069hmnqmmx.cloudfront.net/epgdata/1.0/newchanlogos/600/600/skychb{0}.png"  # also at https://epgstatic.sky.com/...

_LOGGER = logging.getLogger(__name__)


class SkyQCountry:
    def __init__(self, host):
        self.channel_image_url = CHANNEL_IMAGE_URL
        self.pvr_image_url = PVR_IMAGE_URL
        self.epgData = None

        self._lastEpgUrl = None
        self._host = host

    def getEpgData(self, sid, channelno, epgDate):
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
            return None
        if len(epgData[0]["events"]) == 0:
            _LOGGER.warning(
                f"W0010UK - Programme data not found. Do you need to set 'live_tv' to False?"
            )
            return None

        self.epgData = []
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

            programme = vars(
                Programme(
                    programmeuuid, starttime, endtime, title, season, episode, imageUrl
                )
            )

            self.epgData.append(programme)
        return self.epgData
