"""List of channels available on the Sky Q box."""

import json
from dataclasses import dataclass, field

from .channel import Channel


@dataclass
class ChannelList:
    """SkyQ Channel List Class."""

    channels: set = field(
        init=True,
        repr=True,
        compare=False,
    )

    def as_json(self) -> str:
        """Return a JSON string representing the Channel list."""
        return json.dumps(self, cls=_ChannelListJSONEncoder)


def ChannelListDecoder(obj):
    """Decode the channel list object from json."""
    channellist = json.loads(obj, object_hook=_json_decoder_hook)
    if "__type__" in channellist and channellist["__type__"] == "__channellist__":
        return ChannelList(channels=channellist["channels"], **channellist["attributes"])
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
            attributes = {k: v for k, v in vars(obj).items() if k not in {"channels"}}
            return {
                "__type__": type_,
                "attributes": attributes,
                "channels": channels,
            }

        if isinstance(obj, set):
            return list(obj)

        if isinstance(obj, Channel):
            attributes = {k: v for k, v in vars(obj).items()}
            return {
                "__type__": "__channel__",
                "attributes": attributes,
            }

        json.JSONEncoder.default(self, obj)  # pragma: no cover
