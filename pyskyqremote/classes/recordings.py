"""Structure of a standard EPG prorgramme."""

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime

import requests

from ..const import REST_RECORDING_DETAILS, REST_RECORDINGS_LIST
from .programme import Programme

_LOGGER = logging.getLogger(__name__)


class RecordingsInformation:
    """Sky Q recordings information retrieval methods."""

    def __init__(self, deviceAccess, remoteCountry):
        """Initialise the recordings information class."""
        self._deviceAccess = deviceAccess
        self._remoteCountry = remoteCountry

    def getRecordings(self, status=None):
        """Get the list of available Recordings."""
        try:
            recordings = set()
            resp = self._deviceAccess.http_json(REST_RECORDINGS_LIST)
            recData = resp["pvrItems"]
            for recording in recData:
                if recording["status"] == status or not status:
                    built = self._buildRecording(recording)
                    recordings.add(built)

            return Recordings(recordings)
        except requests.exceptions.ReadTimeout:
            _LOGGER.error(f"E0040 - Timeout retrieving recordings: {self._host}")
            return Recordings(recordings)

    def getRecording(self, pvrId):
        """Get the recording details."""
        resp = self._deviceAccess.http_json(REST_RECORDING_DETAILS.format(pvrId))
        if "details" not in resp:
            _LOGGER.info(f"I0030 - Recording data not found for {pvrId}")
            return None

        recording = resp["details"]

        return self._buildRecording(recording)

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

        channel = recording["cn"]
        title = recording["t"]
        if "seasonnumber" in recording and "episodenumber" in recording:
            season = recording["seasonnumber"]
            episode = recording["episodenumber"]
        if "programmeuuid" in recording:
            programmeuuid = recording["programmeuuid"]
            imageUrl = self._remoteCountry.pvr_image_url.format(str(programmeuuid))
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

        return Programme(
            programmeuuid,
            starttime,
            endtime,
            title,
            season,
            episode,
            imageUrl,
            channel,
            status,
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
