"""Structure of a media information."""

from dataclasses import dataclass, field
import json
from datetime import datetime


@dataclass
class Media:
    """SkyQ Programme Class."""

    channel: str = field(
        init=True, repr=True, compare=False,
    )
    imageUrl: str = field(
        init=True, repr=True, compare=False,
    )
    sid: str = field(
        init=True, repr=True, compare=False,
    )
    pvrId: str = field(
        init=True, repr=True, compare=False,
    )
    live: bool = field(
        init=True, repr=True, compare=False,
    )

    def as_json(self) -> str:
        """Return a JSON string respenting this media info."""
        return json.dumps(self, cls=_MediaJSONEncoder)


def MediaDecoder(obj):
    """Decode programme object from json."""
    media = json.loads(obj)
    if "__type__" in media and media["__type__"] == "__media__":
        return Media(**media["attributes"])
    return media


class _MediaJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Media):
            attributes = {}
            for k, v in vars(obj).items():
                if type(v) is datetime:
                    v = v.strftime("%Y-%m-%dT%H:%M:%SZ")
                attributes.update({k: v})

            result = {
                "__type__": "__media__",
                "attributes": attributes,
            }
            return result
