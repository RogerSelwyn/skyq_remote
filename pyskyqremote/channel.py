"""Structure of a standard channel."""

from dataclasses import dataclass, field
import json


@dataclass(order=True)
class Channel:
    """SkyQ Channel Class."""

    channelno: str = field(
        init=True, repr=True, compare=True,
    )
    channelname: str = field(
        init=True, repr=True, compare=False,
    )

    def __hash__(self):
        """Calculate the hash of this object."""
        return hash(self.channelno)

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
