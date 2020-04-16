from datetime import datetime, timedelta
import logging
import requests

PAST_END_OF_EPG = "past end of epg"
RESPONSE_OK = 200

SCHEDULE_URL = "https://apid.sky.it/gtv/v1/events?from={1}&to={2}&pageSize=50&pageNum=0&env=DTH&channels={0}"
LIVE_IMAGE_URL = "https://ethaneurope.it.imageservice.sky.com/pd-image/{0}/16-9"
PVR_IMAGE_URL = "https://ethaneurope.it.imageservice.sky.com/pd-image/{0}/16-9"
CHANNEL_URL = "https://apid.sky.it/gtv/v1/channels?env=DTH"
CHANNEL_IMAGE_URL = (
    "https://ethaneurope.it.imageservice.sky.com/pd-logo/skychb_{0}{1}/600/600"
)

_LOGGER = logging.getLogger(__name__)


class SkyQCountry:
    def __init__(self, host):
        self._lastEpgUrl = None
        self._host = host
        self.channel_image_url = CHANNEL_IMAGE_URL
        self.pvr_image_url = PVR_IMAGE_URL
        self._channellist = None

        self._getChannels()

    def getProgrammeFromEpgIt(self, cid, queryDate):
        queryDateFrom = queryDate.strftime("%Y-%m-%dT00:00:00Z")
        queryDateTo = queryDate.strftime("%Y-%m-%dT23:59:59Z")
        currentTime = datetime.utcnow()
        self.getEpgData(cid, "events", queryDateFrom, queryDateTo)
        if len(self.epgData) == 0:
            _LOGGER.warning(
                f"W0010IT - Programme data not found. Do you need to set 'live_tv' to False?"
            )
            return None

        try:
            programme = next(
                p
                for p in self.epgData
                if datetime.strptime(p["starttime"], "%Y-%m-%dT%H:%M:%SZ")
                <= currentTime
                and datetime.strptime(p["endtime"], "%Y-%m-%dT%H:%M:%SZ") >= currentTime
            )
            return programme

        except StopIteration:
            return PAST_END_OF_EPG

    def getCurrentLiveTVProgramme(self, sid, channelno):
        try:
            result = {"title": None, "season": None, "episode": None, "imageUrl": None}
            cid = None
            for channel in self._channellist:
                if str(channel["number"]) == str(channelno):
                    cid = channel["id"]
            queryDate = datetime.utcnow()
            programme = self.getProgrammeFromEpgIt(cid, queryDate)
            if programme == PAST_END_OF_EPG:
                programme = self.getProgrammeFromEpgIt(
                    sid, queryDate + timedelta(days=1)
                )

            result.update({"title": programme["eventTitle"]})
            if "episodeNumber" in programme["content"]:
                if programme["content"]["episodeNumber"] > 0:
                    result.update({"episode": programme["content"]["episodeNumber"]})
            if "seasonNumber" in programme["content"]:
                if programme["content"]["seasonNumber"] > 0:
                    result.update({"season": programme["content"]["seasonNumber"]})
            if "uuid" in programme["content"]:
                programmeuuid = str(programme["content"]["uuid"])
                result.update({"imageUrl": LIVE_IMAGE_URL.format(programmeuuid)})
            else:
                _LOGGER.info(
                    f"I0020 - No imagesMap: {self._host} : {sid} : {programme}"
                )
            return result
        except Exception as err:
            _LOGGER.exception(
                f"X0030UK - Error occurred: {self._host} : {sid} : {channelno} : {err}"
            )
            return result

    def _getChannels(self):
        resp = requests.get(CHANNEL_URL)
        if resp.status_code == RESPONSE_OK:
            self._channellist = resp.json()["channels"]

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
