"""Structure of a standard channel."""

import json
from dataclasses import dataclass, field

AUDIO = "audio"
VIDEO = "video"


@dataclass(order=True)
class Channel:
    """SkyQ Channel Class."""

    channelno: str = field(
        init=True,
        repr=True,
        compare=True,
    )
    channelname: str = field(
        init=True,
        repr=True,
        compare=False,
    )
    channelsid: str = field(
        init=True,
        repr=True,
        compare=False,
    )
    channelimageurl: str = field(
        init=True,
        repr=True,
        compare=False,
    )
    channeltype: str = None
    channelnoint: int = None
    sf: str = None

    def __post_init__(self):
        """Post process the channel setup."""
        if self.sf == "au":
            self.channeltype = AUDIO
        else:
            self.channeltype = VIDEO
        self.channelnoint = int(self.channelno)

    def __hash__(self):
        """Calculate the hash of this object."""
        typesort = "100" if self.channeltype == VIDEO else "20"
        return hash(typesort + self.channelno)

    def as_json(self) -> str:
        """Return a JSON string representing this Channel."""
        return json.dumps(self, cls=_ChannelJSONEncoder)


def ChannelDecoder(obj):
    """Decode channel object from json."""
    channel = json.loads(obj)
    if "__type__" in channel and channel["__type__"] == "__channel__":
        return Channel(**channel["attributes"])
    return channel


class _ChannelJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Channel):
            attributes = {}
            for k, v in vars(obj).items():
                attributes.update({k: v})

            result = {
                "__type__": "__channel__",
                "attributes": attributes,
            }
            return result
