"""Information for channellist and channel."""

import json
from dataclasses import dataclass, field
from operator import attrgetter

from ..const import AUDIO, REST_CHANNEL_LIST, VIDEO
from ..const_test import TEST_CHANNEL_LIST


class ChannelInformation:
    """Channel information retrieval methods."""

    def __init__(self, remoteConfig):
        """Initialise the channel information class."""
        self._deviceAccess = remoteConfig.deviceAccess
        self._remoteCountry = remoteConfig.remoteCountry
        self._test_channel = remoteConfig.test_channel
        self._channels = []

    def getChannelList(self):
        """Get Channel list for Sky Q box."""
        self._channels = self._getChannels()
        if not self._channels:
            return None

        channelitems = set()

        for c in self._channels:
            channel = Channel(c["c"], c["t"], c["sid"], None, sf=c["sf"])
            channelitems.add(channel)

        channelnosorted = sorted(channelitems, key=attrgetter("channelnoint"))

        return ChannelList(sorted(channelnosorted, key=attrgetter("channeltype"), reverse=True))

    def getChannelInfo(self, channelNo):
        """Retrieve channel information for specified channelNo."""
        if not channelNo.isnumeric():
            return None

        if not self._channels:
            self._channels = self._getChannels()

        try:
            channel = next(c for c in self._channels if c["c"] == channelNo)
        except StopIteration:
            return None

        channelno = channel["c"]
        channelname = channel["t"]
        channelsid = channel["sid"]
        channelImageUrl = self._remoteCountry.buildChannelImageUrl(channelsid, channelname)
        sf = channel["sf"]
        return Channel(channelno, channelname, channelsid, channelImageUrl, sf=sf)

    def getChannelNode(
        self,
        sid,
    ):
        """Retrieve the channel node for the given sid."""
        channelNode = self._getNodeFromChannels(sid)

        if not channelNode:
            # Load the channel list for the first time.
            # It's also possible the channels may have changed since last HA restart, so reload them
            self._channels = self._getChannels()
            channelNode = self._getNodeFromChannels(sid)
        if not channelNode:
            return None

        channel = channelNode["t"]
        channelno = channelNode["c"]
        return {"channel": channel, "channelno": channelno}

    def _getChannels(self):
        """Get the list of channels from the Sky Q box."""
        # This is here because otherwise I can never validate code for a foreign device
        if self._test_channel:
            return TEST_CHANNEL_LIST

        channels = self._deviceAccess.http_json(REST_CHANNEL_LIST)
        if channels and "services" in channels:
            return channels["services"]

        return []

    def _getNodeFromChannels(self, sid):
        return next((s for s in self._channels if s["sid"] == str(sid)), None)


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
        self.channeltype = AUDIO if self.sf == "au" else VIDEO
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
            attributes = {k: v for k, v in vars(obj).items()}
            return {
                "__type__": "__channel__",
                "attributes": attributes,
            }
