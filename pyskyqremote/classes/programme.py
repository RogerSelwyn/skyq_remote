"""Structure of a standard EPG programme."""

import json
from dataclasses import dataclass, field
from datetime import datetime


@dataclass(order=True)
class Programme:
    """SkyQ Programme Class."""

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
    pvrid: str = "n/a"
    eid: str = "n/a"

    def __hash__(self):
        """Calculate the hash of this object."""
        return hash(self.starttime)

    def as_json(self) -> str:
        """Return a JSON string representing this Programme."""
        return json.dumps(self, cls=_ProgrammeJSONEncoder)


def programmedecoder(obj):
    """Decode programme object from json."""
    programme = json.loads(obj, object_hook=_json_decoder_hook)
    if "__type__" in programme and programme["__type__"] == "__programme__":
        return Programme(**programme["attributes"])
    return programme


def _json_decoder_hook(obj):
    """Decode JSON into appropriate types used in this library."""
    if "starttime" in obj:
        obj["starttime"] = datetime.strptime(obj["starttime"], "%Y-%m-%dT%H:%M:%SZ")
    if "endtime" in obj:
        obj["endtime"] = datetime.strptime(obj["endtime"], "%Y-%m-%dT%H:%M:%SZ")
    return obj


class _ProgrammeJSONEncoder(json.JSONEncoder):
    def default(self, o):
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
