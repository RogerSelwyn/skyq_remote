"""Structure of a standard EPG prorgramme."""

import json
from dataclasses import dataclass, field

from .channel import Channel


@dataclass
class ChannelList:
    """SkyQ Channel List Class."""

    channels: set = field(
        init=True, repr=True, compare=False,
    )

    def as_json(self) -> str:
        """Return a JSON string representing this Channel."""
        return json.dumps(self, cls=_ChannelListJSONEncoder)


def ChannelListDecoder(obj):
    """Decode channel object from json."""
    channellist = json.loads(obj, object_hook=_json_decoder_hook)
    if "__type__" in channellist and channellist["__type__"] == "__channellist__":
        return ChannelList(
            channels=channellist["channels"], **channellist["attributes"]
        )
    return channellist


def _json_decoder_hook(obj):
    """Decode JSON into appropriate types used in this library."""
    if "__type__" in obj and obj["__type__"] == "__channel__":
        obj = Channel(**obj["attributes"])
    return obj


class _ChannelListJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, ChannelList):
            type_ = "__channellist__"
            channels = obj.channels
            attributes = {}
            for k, v in vars(obj).items():
                if k not in {"channels"}:
                    attributes.update({k: v})
            return {
                "__type__": type_,
                "attributes": attributes,
                "channels": channels,
            }

        if isinstance(obj, set):
            return list(obj)

        if isinstance(obj, Channel):
            attributes = {}
            for k, v in vars(obj).items():
                attributes.update({k: v})

            result = {
                "__type__": "__channel__",
                "attributes": attributes,
            }
            return result

        json.JSONEncoder.default(self, obj)  # pragma: no cover
