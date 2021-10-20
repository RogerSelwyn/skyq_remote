"""Structure of a standard EPG prorgramme."""

import json
from dataclasses import dataclass, field
from datetime import datetime

from .programme import Programme


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
