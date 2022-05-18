"""Methods for retrieving recording information."""

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime

from pyskyqremote.classes.channel import build_channel_image_url

from ..const import (ALLRECORDINGS, PVR_IMAGE_URL, RESPONSE_OK,
                     REST_BOOK_PPVRECORDING, REST_BOOK_RECORDING,
                     REST_BOOK_SERIES_RECORDING, REST_DELETE, REST_POST,
                     REST_QUOTA_DETAILS, REST_RECORDING_DELETE,
                     REST_RECORDING_DETAILS, REST_RECORDING_ERASE,
                     REST_RECORDING_ERASE_ALL, REST_RECORDING_KEEP,
                     REST_RECORDING_LOCK,
                     REST_RECORDING_SET_LAST_PLAYED_POSITION,
                     REST_RECORDING_UNDELETE, REST_RECORDING_UNKEEP,
                     REST_RECORDING_UNLOCK, REST_RECORDINGS_LIST,
                     REST_SERIES_LINK, REST_SERIES_UNLINK)
from .programme import Programme

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
            _LOGGER.error(
                "E0010R - Timeout retrieving recordings: %s", self._remote_config.host
            )
            return Recordings(recordings)
        rec_data = resp["pvrItems"]
        for recording in rec_data:
            if recording["status"] == status or status == ALLRECORDINGS:
                built = self._build_recording(recording)
                recordings.add(built)

        return Recordings(recordings)

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
        resp = None
        if series:
            resp = self._remote_config.device_access.retrieve_information(
                REST_BOOK_SERIES_RECORDING.format(eid), REST_POST
            )
        else:
            resp = self._remote_config.device_access.retrieve_information(
                REST_BOOK_RECORDING.format(eid), REST_POST
            )

        if resp != RESPONSE_OK:
            return False

        return True

    def book_ppv_recording(self, eid, offerref):
        """Book PPV recording for specified item."""
        resp = self._remote_config.device_access.retrieve_information(
            REST_BOOK_PPVRECORDING.format(eid, offerref), REST_POST
        )
        if resp != RESPONSE_OK:
            return False

        return True

    def series_link(self, pvrid, linkon):
        """Series link the specified item."""
        resp = None
        if linkon:
            resp = self._remote_config.device_access.retrieve_information(
                REST_SERIES_LINK.format(pvrid), REST_POST
            )
        else:
            resp = self._remote_config.device_access.retrieve_information(
                REST_SERIES_UNLINK.format(pvrid), REST_POST
            )

        if resp != RESPONSE_OK:
            return False

        return True

    def recording_keep(self, pvrid, keepon):
        """Keep the specified item."""
        resp = None
        if keepon:
            resp = self._remote_config.device_access.retrieve_information(
                REST_RECORDING_KEEP.format(pvrid), REST_POST
            )
        else:
            resp = self._remote_config.device_access.retrieve_information(
                REST_RECORDING_UNKEEP.format(pvrid), REST_POST
            )

        if resp != RESPONSE_OK:
            return False

        return True

    def recording_lock(self, pvrid, lockon):
        """Lock the specified item."""
        resp = None
        if lockon:
            resp = self._remote_config.device_access.retrieve_information(
                REST_RECORDING_LOCK.format(pvrid), REST_POST
            )
        else:
            resp = self._remote_config.device_access.retrieve_information(
                REST_RECORDING_UNLOCK.format(pvrid), REST_POST
            )

        if resp != RESPONSE_OK:
            return False

        return True

    def recording_delete(self, pvrid, deleteon):
        """Delete the specified item."""
        resp = None
        if deleteon:
            resp = self._remote_config.device_access.retrieve_information(
                REST_RECORDING_DELETE.format(pvrid), REST_POST
            )
        else:
            resp = self._remote_config.device_access.retrieve_information(
                REST_RECORDING_UNDELETE.format(pvrid), REST_POST
            )

        if resp != RESPONSE_OK:
            return False

        return True

    def recording_erase(self, pvrid):
        """Permanently erase the specified item."""
        resp = self._remote_config.device_access.retrieve_information(
            REST_RECORDING_ERASE.format(pvrid), REST_POST
        )

        if resp != RESPONSE_OK:
            return False

        return True

    def recording_erase_all(self):
        """Permanently erase the specified item."""
        resp = self._remote_config.device_access.retrieve_information(
            REST_RECORDING_ERASE_ALL, REST_DELETE
        )

        if resp != RESPONSE_OK:
            return False

        return True

    def recording_set_last_played_position(self, pvrid, pos):
        """Set the last played position for specified item."""
        resp = self._remote_config.device_access.retrieve_information(
            REST_RECORDING_SET_LAST_PLAYED_POSITION.format(pos, pvrid), REST_POST
        )
        if resp != RESPONSE_OK:
            return False

        return True

    def _build_recording(self, recording):
        channel = recording["cn"]
        title = recording["t"]

        season = None
        episode = None
        if "seasonnumber" in recording and "episodenumber" in recording:
            season = recording["seasonnumber"]
            episode = recording["episodenumber"]

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

        starttimestamp = 0
        if "ast" in recording:
            starttimestamp = recording["ast"]
        elif "st" in recording:
            starttimestamp = recording["st"]
        starttime = datetime.utcfromtimestamp(starttimestamp)

        endtime = None
        if "finald" in recording:
            endtime = datetime.utcfromtimestamp(starttimestamp + recording["finald"])
        elif "schd" in recording:
            endtime = datetime.utcfromtimestamp(starttimestamp + recording["schd"])
        else:
            endtime = starttime

        pvrid = recording["pvrid"]

        eid = recording["oeid"] if "oeid" in recording else None
        status = recording["status"]

        return Programme(
            programmeuuid,
            starttime,
            endtime,
            title,
            season,
            episode,
            image_url,
            channel,
            status,
            pvrid,
            eid,
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


def recordings_decoder(obj):
    """Decode channel object from json."""
    recordings = json.loads(obj, object_hook=_json_decoder_hook)
    if "__type__" in recordings and recordings["__type__"] == "__recordings__":
        return Recordings(
            programmes=recordings["programmes"], **recordings["attributes"]
        )
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
    def default(self, o):
        if isinstance(o, Recordings):
            type_ = "__recordings__"
            programmes = o.programmes
            attributes = {k: v for k, v in vars(o).items() if k not in {"programmes"}}
            return {
                "__type__": type_,
                "attributes": attributes,
                "programmes": programmes,
            }

        if isinstance(o, set):
            return list(o)

        if isinstance(o, Programme):
            attributes = {}
            for k, val in vars(o).items():
                if isinstance(val, datetime):
                    val = val.strftime("%Y-%m-%dT%H:%M:%SZ")
                attributes[k] = val
            return {
                "__type__": "__programme__",
                "attributes": attributes,
            }

        json.JSONEncoder.default(self, o)  # pragma: no cover


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
