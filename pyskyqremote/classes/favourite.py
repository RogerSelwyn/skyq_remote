"""Structure of a standard favourite."""

import json
from dataclasses import dataclass, field


@dataclass(order=True)
class Favourite:
    """SkyQ favourite Class."""

    lcn: int = field(
        init=True,
        repr=True,
        compare=True,
    )
    channelno: str = field(
        init=True,
        repr=True,
        compare=False,
    )
    channelname: str = field(
        init=True,
        repr=True,
        compare=False,
    )
    sid: str = field(
        init=True,
        repr=True,
        compare=False,
    )

    def __hash__(self):
        """Calculate the hash of this object."""
        return hash(self.lcn)

    def as_json(self) -> str:
        """Return a JSON string representing this favourite."""
        return json.dumps(self, cls=_favouriteJSONEncoder)


def favouriteDecoder(obj):
    """Decode favourite object from json."""
    favourite = json.loads(obj)
    if "__type__" in favourite and favourite["__type__"] == "__favourite__":
        return favourite(**favourite["attributes"])
    return favourite


class _favouriteJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Favourite):
            attributes = {k: v for k, v in vars(obj).items()}
            return {
                "__type__": "__favourite__",
                "attributes": attributes,
            }
