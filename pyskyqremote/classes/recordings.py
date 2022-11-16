"""Methods for retrieving recording information."""

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from operator import attrgetter

from pyskyqremote.classes.channel import build_channel_image_url

from ..const import (
    ALLRECORDINGS,
    PVR_IMAGE_URL,
    RESPONSE_OK,
    REST_BOOK_PPVRECORDING,
    REST_BOOK_RECORDING,
    REST_BOOK_SERIES_RECORDING,
    REST_DELETE,
    REST_POST,
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

_LOGGER = logging.getLogger(__name__)


class RecordingsInformation:
    """Sky Q recordings information retrieval methods."""

    def __init__(self, remote_config):
        """Initialise the recordings information class."""
        self._remote_config = remote_config

    def get_recordings(self, status, limit, offset):
        """Get the list of available Recordings."""
        recordings = set()
        resp = self._remote_config.device_access.retrieve_information(
            REST_RECORDINGS_LIST.format(limit, offset)
        )
        if not resp or "pvrItems" not in resp:
            return None
        rec_data = resp["pvrItems"]
        for recording in rec_data:
            if recording["status"] == status or status == ALLRECORDINGS:
                built = self._build_recording(recording)
                recordings.add(built)

        recordingssorted = sorted(recordings, key=attrgetter("starttime"))
        return Recordings(recordingssorted)

    def get_recording(self, pvrid):
        """Get the recording details."""
        resp = self._remote_config.device_access.retrieve_information(
            REST_RECORDING_DETAILS.format(pvrid)
        )
        if not resp or "details" not in resp:
            _LOGGER.info("I0010R - Recording data not found for %s", pvrid)
            return None

        recording = resp["details"]

        return self._build_recording(recording)

    def get_quota(self):
        """Get the quota information."""
        resp = self._remote_config.device_access.retrieve_information(
            REST_QUOTA_DETAILS
        )
        if not resp:
            return None

        if "userQuotaMax" not in resp:
            _LOGGER.debug("D0010R - Recording data not found for %s", resp)
            return None
        return Quota(resp["userQuotaMax"], resp["userQuotaUsed"])

    def book_recording(self, eid, series):
        """Book recording for specified item."""
        return self._perform_api_function(
            series, eid, REST_BOOK_SERIES_RECORDING, REST_BOOK_RECORDING
        )

    def book_ppv_recording(self, eid, offerref):
        """Book PPV recording for specified item."""
        resp = self._remote_config.device_access.retrieve_information(
            REST_BOOK_PPVRECORDING.format(eid, offerref), REST_POST
        )
        return resp == RESPONSE_OK

    def series_link(self, pvrid, linkon):
        """Series link the specified item."""
        return self._perform_api_function(
            linkon, pvrid, REST_SERIES_LINK, REST_SERIES_UNLINK
        )

    def recording_keep(self, pvrid, keepon):
        """Keep the specified item."""
        return self._perform_api_function(
            keepon, pvrid, REST_RECORDING_KEEP, REST_RECORDING_UNKEEP
        )

    def recording_lock(self, pvrid, lockon):
        """Lock the specified item."""
        return self._perform_api_function(
            lockon, pvrid, REST_RECORDING_LOCK, REST_RECORDING_UNLOCK
        )

    def recording_delete(self, pvrid, deleteon):
        """Delete the specified item."""
        return self._perform_api_function(
            deleteon, pvrid, REST_RECORDING_DELETE, REST_RECORDING_UNDELETE
        )

    def _perform_api_function(self, function_on, item_id, on_function, off_function):
        resp = None
        if function_on:
            resp = self._remote_config.device_access.retrieve_information(
                on_function.format(item_id), REST_POST
            )

        else:
            resp = self._remote_config.device_access.retrieve_information(
                off_function.format(item_id), REST_POST
            )

        return resp == RESPONSE_OK

    def recording_erase(self, pvrid):
        """Permanently erase the specified item."""
        resp = self._remote_config.device_access.retrieve_information(
            REST_RECORDING_ERASE.format(pvrid), REST_POST
        )

        return resp == RESPONSE_OK

    def recording_erase_all(self):
        """Permanently erase the specified item."""
        resp = self._remote_config.device_access.retrieve_information(
            REST_RECORDING_ERASE_ALL, REST_DELETE
        )

        return resp == RESPONSE_OK

    def recording_set_last_played_position(self, pvrid, pos):
        """Set the last played position for specified item."""
        resp = self._remote_config.device_access.retrieve_information(
            REST_RECORDING_SET_LAST_PLAYED_POSITION.format(pos, pvrid), REST_POST
        )
        return resp == RESPONSE_OK

    def _build_recording(self, recording):
        channel = recording["cn"]
        title = recording["t"]

        season = None
        episode = None
        if "seasonnumber" in recording and "episodenumber" in recording:
            season = recording["seasonnumber"]
            episode = recording["episodenumber"]

        programmeuuid, image_url = self._build_image_url(channel, recording)

        status = recording["status"]
        starttime, endtime = self._build_recording_times(status, recording)

        pvrid = recording["pvrid"]

        eid = recording["oeid"] if "oeid" in recording else None

        deletetime = (
            datetime.utcfromtimestamp(recording["del"]) if "del" in recording else None
        )
        failurereason = recording["fr"] if "fr" in recording else None
        source = recording["src"] if "src" in recording else None
        summary = recording["sy"] if "sy" in recording else None

        return Recording(
            programmeuuid,
            starttime,
            endtime,
            title,
            summary,
            season,
            episode,
            image_url,
            channel,
            status,
            deletetime,
            failurereason,
            source,
            pvrid,
            eid,
        )

    def _build_image_url(self, channel, recording):
        programmeuuid = None
        image_url = None
        if "programmeuuid" in recording:
            programmeuuid = recording["programmeuuid"]
            image_url = PVR_IMAGE_URL.format(
                programmeuuid,
                self._remote_config.url_prefix,
                self._remote_config.territory,
            )
        elif "osid" in recording:
            sid = str(recording["osid"])
            image_url = build_channel_image_url(
                sid,
                channel,
                self._remote_config.url_prefix,
                self._remote_config.territory,
            )

        return programmeuuid, image_url

    def _build_recording_times(self, status, recording):
        starttimestamp = 0
        endtimestamp = 0
        if status == "SCHEDULED":
            if "st" in recording:
                starttimestamp = recording["st"]
            endtimestamp = (
                starttimestamp + recording["schd"]
                if "schd" in recording
                else starttimestamp
            )
        elif status == "RECORDING":
            starttimestamp = recording["ast"]
            if "fr" not in recording or recording["fr"] == "N/A":
                usedtimestamp = (
                    recording["ast"]
                    if recording["ast"] > recording["st"]
                    else recording["st"]
                )
                endtimestamp = usedtimestamp + recording["schd"]
            else:
                endtimestamp = recording["st"] + recording["schd"]
        else:
            starttimestamp = 0
            if "ast" in recording:
                starttimestamp = recording["ast"]
            elif "st" in recording:
                starttimestamp = recording["st"]
            if "finald" in recording:
                endtimestamp = starttimestamp + recording["finald"]
            elif "schd" in recording:
                endtimestamp = starttimestamp + recording["schd"]
            else:
                endtimestamp = starttimestamp

        return datetime.utcfromtimestamp(starttimestamp), datetime.utcfromtimestamp(
            endtimestamp
        )


@dataclass
class Recordings:
    """SkyQ Channel EPG Class."""

    recordings: set = field(
        init=True,
        repr=True,
        compare=False,
    )

    def as_json(self) -> str:
        """Return a JSON string representing this Channel."""
        return json.dumps(self, cls=_RecordingsJSONEncoder)


def recordings_decoder(obj):
    """Decode channel object from json."""
    recordings = json.loads(obj, object_hook=_json_decoder_hook)
    if "__type__" in recordings and recordings["__type__"] == "__recordings__":
        return Recordings(
            recordings=recordings["recordings"], **recordings["attributes"]
        )
    return recordings


def _json_decoder_hook(obj):
    """Decode JSON into appropriate types used in this library."""
    if "starttime" in obj:
        obj["starttime"] = datetime.strptime(obj["starttime"], "%Y-%m-%dT%H:%M:%SZ")
    if "endtime" in obj:
        obj["endtime"] = datetime.strptime(obj["endtime"], "%Y-%m-%dT%H:%M:%SZ")
    if "deletetime" in obj:
        obj["deletetime"] = datetime.strptime(obj["deletetime"], "%Y-%m-%dT%H:%M:%SZ")
    if "__type__" in obj and obj["__type__"] == "__recording__":
        obj = Recording(**obj["attributes"])
    return obj


class _RecordingsJSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Recordings):
            type_ = "__recordings__"
            recordings = o.recordings
            attributes = {k: v for k, v in vars(o).items() if k not in {"recordings"}}
            return {
                "__type__": type_,
                "attributes": attributes,
                "recordings": recordings,
            }

        if isinstance(o, set):
            return list(o)

        if isinstance(o, Recording):
            attributes = {}
            for k, val in vars(o).items():
                if isinstance(val, datetime):
                    val = val.strftime("%Y-%m-%dT%H:%M:%SZ")
                attributes[k] = val
            return {
                "__type__": "__recording__",
                "attributes": attributes,
            }

        json.JSONEncoder.default(self, o)  # pragma: no cover


@dataclass(order=True)
class Recording:
    """SkyQ Recording Class."""

    programmeuuid: str = field(
        init=True,
        repr=True,
        compare=False,
    )
    starttime: datetime = field(
        init=True,
        repr=True,
        compare=True,
    )
    endtime: datetime = field(
        init=True,
        repr=True,
        compare=False,
    )
    title: str = field(
        init=True,
        repr=True,
        compare=True,
    )
    summary: str = field(
        init=True,
        repr=True,
        compare=False,
    )
    season: str = field(
        init=True,
        repr=True,
        compare=False,
    )
    episode: str = field(
        init=True,
        repr=True,
        compare=False,
    )
    image_url: str = field(
        init=True,
        repr=True,
        compare=False,
    )
    channelname: str = field(
        init=True,
        repr=True,
        compare=False,
    )
    status: str = field(
        init=True,
        repr=True,
        compare=False,
    )
    deletetime: datetime = field(
        init=True,
        repr=True,
        compare=False,
    )
    failurereason: str = field(init=True, repr=True, compare=False)
    source: str = field(init=True, repr=True, compare=False)
    pvrid: str = "n/a"
    eid: str = "n/a"

    def __hash__(self):
        """Calculate the hash of this object."""
        return hash(self.starttime)

    def as_json(self) -> str:
        """Return a JSON string representing this Recording."""
        return json.dumps(self, cls=_RecordingJSONEncoder)


def recordingdecoder(obj):
    """Decode recording object from json."""
    recording = json.loads(obj, object_hook=_json_decoder_hook)
    if "__type__" in recording and recording["__type__"] == "__recording__":
        return Recording(**recording["attributes"])
    return recording


class _RecordingJSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Recording):
            attributes = {}
            for k, val in vars(o).items():
                if isinstance(val, datetime):
                    val = val.strftime("%Y-%m-%dT%H:%M:%SZ")
                attributes[k] = val
            return {
                "__type__": "__recording__",
                "attributes": attributes,
            }


@dataclass
class Quota:
    """SkyQ Quota Class."""

    quota_max: int = field(
        init=True,
        repr=True,
        compare=False,
    )
    quota_used: str = field(
        init=True,
        repr=True,
        compare=False,
    )

    def as_json(self) -> str:
        """Return a JSON string representing this quota info."""
        return json.dumps(self, cls=_QuotaJSONEncoder)


def quota_decoder(obj):
    """Decode quota object from json."""
    quota = json.loads(obj)
    if "__type__" in quota and quota["__type__"] == "__quota__":
        return Quota(**quota["attributes"])
    return quota


class _QuotaJSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Quota):
            attributes = dict(vars(o))
            return {
                "__type__": "__quota__",
                "attributes": attributes,
            }
