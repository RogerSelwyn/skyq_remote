from datetime import datetime, timedelta
import logging
import requests

PAST_END_OF_EPG = "past end of epg"
RESPONSE_OK = 200

SCHEDULE_URL = "http://awk.epgsky.com/hawk/linear/schedule/{1}/{0}"
LIVE_IMAGE_URL = "https://images.metadata.sky.com/pd-image/{0}/16-9"
PVR_IMAGE_URL = "https://images.metadata.sky.com/pd-image/{0}/16-9"
CHANNEL_IMAGE_URL = "https://d2n0069hmnqmmx.cloudfront.net/epgdata/1.0/newchanlogos/600/600/skychb{0}.png"  # also at https://epgstatic.sky.com/...

_LOGGER = logging.getLogger(__name__)


class SkyQCountry:
    def __init__(self, host):
        self._lastEpgUrl = None
        self._host = host
        self.channel_image_url = CHANNEL_IMAGE_URL
        self.pvr_image_url = PVR_IMAGE_URL

    def getProgrammeFromEpg(self, sid, queryDate):
        epoch = datetime.utcfromtimestamp(0)
        timeFromEpoch = int((datetime.utcnow() - epoch).total_seconds())
        queryDateStr = queryDate.strftime("%Y%m%d")
        self.getEpgData(sid, "schedule", queryDateStr)
        if len(self.epgData[0]["events"]) == 0:
            _LOGGER.warning(
                f"W0010UK - Programme data not found. Do you need to set 'live_tv' to False?"
            )
            return None

        try:
            programme = next(
                p
                for p in self.epgData[0]["events"]
                if p["st"] <= timeFromEpoch and p["st"] + p["d"] >= timeFromEpoch
            )
            return programme

        except StopIteration:
            return PAST_END_OF_EPG

    def getCurrentLiveTVProgramme(self, sid, channelno):
        try:
            result = {"title": None, "season": None, "episode": None, "imageUrl": None}
            queryDate = datetime.utcnow()
            programme = self.getProgrammeFromEpg(sid, queryDate)
            if programme == PAST_END_OF_EPG:
                programme = self.getProgrammeFromEpg(sid, queryDate + timedelta(days=1))
            result.update({"title": programme["t"]})
            if "episodenumber" in programme:
                if programme["episodenumber"] > 0:
                    result.update({"episode": programme["episodenumber"]})
            if "seasonnumber" in programme:
                if programme["seasonnumber"] > 0:
                    result.update({"season": programme["seasonnumber"]})
            if "programmeuuid" in programme:
                programmeuuid = str(programme["programmeuuid"])
                result.update({"imageUrl": LIVE_IMAGE_URL.format(programmeuuid)})
            else:
                _LOGGER.info(
                    f"I0020 - No programmeuuid: {self._host} : {sid} : {programme}"
                )
            return result
        except Exception as err:
            _LOGGER.exception(
                f"X0030UK - Error occurred: {self._host} : {sid} : {channelno} : {err}"
            )
            return result

    def getEpgData(self, queryChannel, resultNode, queryFromDate, queryToDate=None):
        epgUrl = SCHEDULE_URL.format(queryChannel, queryFromDate, queryToDate)
        if self._lastEpgUrl is None or self._lastEpgUrl != epgUrl:
            resp = requests.get(epgUrl)
            if resp.status_code == RESPONSE_OK:
                self.epgData = resp.json()[resultNode]
                self._lastEpgUrl = epgUrl
            else:
                self.epgData = None
        return self.epgData
