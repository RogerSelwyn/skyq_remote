"""Methods for retrieving recording information."""

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime

import requests

from ..const import (
    ALLRECORDINGS,
    RESPONSE_OK,
    REST_BOOK_PPVRECORDING,
    REST_BOOK_RECORDING,
    REST_BOOK_SERIES_RECORDING,
    REST_QUOTA_DETAILS,
    REST_RECORDING_DELETE,
    REST_RECORDING_DETAILS,
    REST_RECORDING_ERASE,
    REST_RECORDING_ERASE_ALL,
    REST_RECORDING_KEEP,
    REST_RECORDING_LOCK,
    REST_RECORDING_SET_LAST_PLAYED_POSITION,
    REST_RECORDING_UNDELETE,
    REST_RECORDING_UNKEEP,
    REST_RECORDING_UNLOCK,
    REST_RECORDINGS_LIST,
    REST_SERIES_LINK,
    REST_SERIES_UNLINK,
)
from .programme import Programme

_LOGGER = logging.getLogger(__name__)


class RecordingsInformation:
    """Sky Q recordings information retrieval methods."""

    def __init__(self, remoteConfig):
        """Initialise the recordings information class."""
        self._remoteConfig = remoteConfig

    def getRecordings(self, status, limit, offset):
        """Get the list of available Recordings."""
        try:
            recordings = set()
            resp = self._remoteConfig.deviceAccess.http_json(REST_RECORDINGS_LIST.format(limit, offset))
            recData = resp["pvrItems"]
            for recording in recData:
                if recording["status"] == status or status == ALLRECORDINGS:
                    built = self._buildRecording(recording)
                    recordings.add(built)

            return Recordings(recordings)
        except requests.exceptions.ReadTimeout:
            _LOGGER.error(f"E0040 - Timeout retrieving recordings: {self._host}")
            return Recordings(recordings)

    def getRecording(self, pvrId):
        """Get the recording details."""
        resp = self._remoteConfig.deviceAccess.http_json(REST_RECORDING_DETAILS.format(pvrId))
        if "details" not in resp:
            _LOGGER.info(f"I0030 - Recording data not found for {pvrId}")
            return None

        recording = resp["details"]

        return self._buildRecording(recording)

    def getQuota(self):
        """Get the quota information."""
        resp = self._remoteConfig.deviceAccess.http_json(REST_QUOTA_DETAILS)
        return Quota(resp["userQuotaMax"], resp["userQuotaUsed"])

    def bookRecording(self, eid, series):
        """Book recording for specified item."""
        resp = None
        if not series:
            resp = self._remoteConfig.deviceAccess.http_json_post(REST_BOOK_RECORDING.format(eid))
        else:
            resp = self._remoteConfig.deviceAccess.http_json_post(REST_BOOK_SERIES_RECORDING.format(eid))

        if resp != RESPONSE_OK:
            return False

        return True

    def bookPPVRecording(self, eid, offerref):
        """Book PPV recording for specified item."""
        resp = self._remoteConfig.deviceAccess.http_json_post(REST_BOOK_PPVRECORDING.format(eid, offerref))
        if resp != RESPONSE_OK:
            return False

        return True

    def seriesLink(self, pvrid, On):
        """Series link the specified item."""
        resp = None
        if On:
            resp = self._remoteConfig.deviceAccess.http_json_post(REST_SERIES_LINK.format(pvrid))
        else:
            resp = self._remoteConfig.deviceAccess.http_json_post(REST_SERIES_UNLINK.format(pvrid))

        if resp != RESPONSE_OK:
            return False

        return True

    def recordingKeep(self, pvrid, On):
        """Keep the specified item."""
        resp = None
        if On:
            resp = self._remoteConfig.deviceAccess.http_json_post(REST_RECORDING_KEEP.format(pvrid))
        else:
            resp = self._remoteConfig.deviceAccess.http_json_post(REST_RECORDING_UNKEEP.format(pvrid))

        if resp != RESPONSE_OK:
            return False

        return True

    def recordingLock(self, pvrid, On):
        """Lock the specified item."""
        resp = None
        if On:
            resp = self._remoteConfig.deviceAccess.http_json_post(REST_RECORDING_LOCK.format(pvrid))
        else:
            resp = self._remoteConfig.deviceAccess.http_json_post(REST_RECORDING_UNLOCK.format(pvrid))

        if resp != RESPONSE_OK:
            return False

        return True

    def recordingDelete(self, pvrid, On):
        """Delete the specified item."""
        resp = None
        if On:
            resp = self._remoteConfig.deviceAccess.http_json_post(REST_RECORDING_DELETE.format(pvrid))
        else:
            resp = self._remoteConfig.deviceAccess.http_json_post(REST_RECORDING_UNDELETE.format(pvrid))

        if resp != RESPONSE_OK:
            return False

        return True

    def recordingErase(self, pvrid):
        """Permanently erase the specified item."""
        resp = self._remoteConfig.deviceAccess.http_json_post(REST_RECORDING_ERASE.format(pvrid))

        if resp != RESPONSE_OK:
            return False

        return True

    def recordingEraseAll(self):
        """Permanently erase the specified item."""
        resp = self._remoteConfig.deviceAccess.http_json_post(REST_RECORDING_ERASE_ALL)

        if resp != RESPONSE_OK:
            return False

        return True

    def recordingSetLastPlayedPosition(self, pvrid, pos):
        """Set the last played position for specified item."""
        resp = self._remoteConfig.deviceAccess.http_json_post(
            REST_RECORDING_SET_LAST_PLAYED_POSITION.format(pos, pvrid)
        )
        print(resp)
        if resp != RESPONSE_OK:
            return False

        return True

    def _buildRecording(self, recording):
        season = None
        episode = None
        starttime = None
        endtime = None
        programmeuuid = None
        channel = None
        imageUrl = None
        title = None
        status = None
        pvrid = None
        eid = None

        channel = recording["cn"]
        title = recording["t"]
        if "seasonnumber" in recording and "episodenumber" in recording:
            season = recording["seasonnumber"]
            episode = recording["episodenumber"]
        if "programmeuuid" in recording:
            programmeuuid = recording["programmeuuid"]
            imageUrl = self._remoteConfig.remoteCountry.pvr_image_url.format(str(programmeuuid))
        elif "osid" in recording:
            sid = str(recording["osid"])
            imageUrl = self._remoteCountry.buildChannelImageUrl(sid, channel)

        starttimestamp = 0
        if "ast" in recording:
            starttimestamp = recording["ast"]
        elif "st" in recording:
            starttimestamp = recording["st"]
        starttime = datetime.utcfromtimestamp(starttimestamp)

        if "finald" in recording:
            endtime = datetime.utcfromtimestamp(starttimestamp + recording["finald"])
        elif "schd" in recording:
            endtime = datetime.utcfromtimestamp(starttimestamp + recording["schd"])
        else:
            endtime = starttime

        status = recording["status"]
        pvrid = recording["pvrid"]
        eid = recording["oeid"]

        return Programme(
            programmeuuid, starttime, endtime, title, season, episode, imageUrl, channel, status, pvrid, eid
        )


@dataclass
class Recordings:
    """SkyQ Channel EPG Class."""

    programmes: set = field(
        init=True,
        repr=True,
        compare=False,
    )

    def as_json(self) -> str:
        """Return a JSON string representing this Channel."""
        return json.dumps(self, cls=_RecordingsJSONEncoder)


def RecordingsDecoder(obj):
    """Decode channel object from json."""
    recordings = json.loads(obj, object_hook=_json_decoder_hook)
    if "__type__" in recordings and recordings["__type__"] == "__recordings__":
        return Recordings(programmes=recordings["programmes"], **recordings["attributes"])
    return recordings


def _json_decoder_hook(obj):
    """Decode JSON into appropriate types used in this library."""
    if "starttime" in obj:
        obj["starttime"] = datetime.strptime(obj["starttime"], "%Y-%m-%dT%H:%M:%SZ")
    if "endtime" in obj:
        obj["endtime"] = datetime.strptime(obj["endtime"], "%Y-%m-%dT%H:%M:%SZ")
    if "__type__" in obj and obj["__type__"] == "__programme__":
        obj = Programme(**obj["attributes"])
    return obj


class _RecordingsJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Recordings):
            type_ = "__recordings__"
            programmes = obj.programmes
            attributes = {k: v for k, v in vars(obj).items() if k not in {"programmes"}}
            return {
                "__type__": type_,
                "attributes": attributes,
                "programmes": programmes,
            }

        if isinstance(obj, set):
            return list(obj)

        if isinstance(obj, Programme):
            attributes = {}
            for k, v in vars(obj).items():
                if isinstance(v, datetime):
                    v = v.strftime("%Y-%m-%dT%H:%M:%SZ")
                attributes[k] = v
            return {
                "__type__": "__programme__",
                "attributes": attributes,
            }

        json.JSONEncoder.default(self, obj)  # pragma: no cover


@dataclass
class Quota:
    """SkyQ Quota Class."""

    quotaMax: int = field(
        init=True,
        repr=True,
        compare=False,
    )
    quotaUsed: str = field(
        init=True,
        repr=True,
        compare=False,
    )

    def as_json(self) -> str:
        """Return a JSON string representing this quota info."""
        return json.dumps(self, cls=_QuotaJSONEncoder)


def QuotaDecoder(obj):
    """Decode quota object from json."""
    quota = json.loads(obj)
    if "__type__" in quota and quota["__type__"] == "__quota__":
        return Quota(**quota["attributes"])
    return quota


class _QuotaJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Quota):
            attributes = {k: v for k, v in vars(obj).items()}
            return {
                "__type__": "__quota__",
                "attributes": attributes,
            }
