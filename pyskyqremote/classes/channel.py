"""Information for channellist and channel."""

import json
from dataclasses import dataclass, field
from operator import attrgetter

from ..const import AUDIO, CHANNEL_IMAGE_URL, REST_CHANNEL_LIST, VIDEO
from ..const_test import TEST_CHANNEL_LIST


class ChannelInformation:
    """Channel information retrieval methods."""

    def __init__(self, remote_config):
        """Initialise the channel information class."""
        self._remote_config = remote_config
        self._device_access = remote_config.device_access
        self._test_channel = remote_config.test_channel
        self._channels = []
        self._bouquet = remote_config.device_info.bouquet
        self._subbouquet = remote_config.device_info.subbouquet

    def get_channel_list(self):
        """Get Channel list for Sky Q box."""
        self._channels = self._get_channels()
        if not self._channels:
            return None

        channelitems = set()

        for channel in self._channels:
            channel = Channel(
                channel["c"], channel["t"], channel["sid"], None, sf=channel["sf"]
            )
            channelitems.add(channel)

        channelnosorted = sorted(channelitems, key=attrgetter("channelnoint"))

        return ChannelList(
            sorted(channelnosorted, key=attrgetter("channeltype"), reverse=True)
        )

    def get_channel_info(self, channel_no):
        """Retrieve channel information for specified channelNo."""
        if not channel_no.isnumeric():
            return None

        if not self._channels:
            self._channels = self._get_channels()

        try:
            channel = next(c for c in self._channels if c["c"] == channel_no)
        except StopIteration:
            return None

        channelno = channel["c"]
        channelname = channel["t"]
        channelsid = channel["sid"]
        channel_image_url = build_channel_image_url(
            channelsid,
            channelname,
            self._remote_config.url_prefix,
            self._remote_config.territory,
        )
        sformat = channel["sf"]
        return Channel(
            channelno, channelname, channelsid, channel_image_url, sf=sformat
        )

    def get_channel_node(
        self,
        sid,
    ):
        """Retrieve the channel node for the given sid."""
        channel_node = self._get_node_from_channels(sid)

        if not channel_node:
            # Load the channel list for the first time.
            # It's also possible the channels may have changed since last HA restart, so reload them
            self._channels = self._get_channels()
            channel_node = self._get_node_from_channels(sid)
        if not channel_node:
            return None

        channel = channel_node["t"]
        channelno = channel_node["c"]
        return {"channel": channel, "channelno": channelno}

    def _get_channels(self):
        """Get the list of channels from the Sky Q box."""
        # This is here because otherwise I can never validate code for a foreign device
        if self._test_channel:
            return TEST_CHANNEL_LIST

        channels = self._device_access.retrieve_information(
            REST_CHANNEL_LIST.format(self._bouquet, self._subbouquet)
        )
        if channels and "services" in channels:
            return channels["services"]

        return []

    def _get_node_from_channels(self, sid):
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


def channel_list_decoder(obj):
    """Decode the channel list object from json."""
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
    def default(self, o):
        if isinstance(o, ChannelList):
            type_ = "__channellist__"
            channels = o.channels
            attributes = {k: v for k, v in vars(o).items() if k not in {"channels"}}
            return {
                "__type__": type_,
                "attributes": attributes,
                "channels": channels,
            }

        if isinstance(o, set):
            return list(o)

        if isinstance(o, Channel):
            attributes = dict(vars(o))
            return {
                "__type__": "__channel__",
                "attributes": attributes,
            }

        json.JSONEncoder.default(self, o)  # pragma: no cover


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
    sf: str = None  # pylint: disable=invalid-name

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


def channel_decoder(obj):
    """Decode channel object from json."""
    channel = json.loads(obj)
    if "__type__" in channel and channel["__type__"] == "__channel__":
        return Channel(**channel["attributes"])
    return channel


class _ChannelJSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Channel):
            attributes = dict(vars(o))
            return {
                "__type__": "__channel__",
                "attributes": attributes,
            }


def build_channel_image_url(sid, channelname, url_prefix, territory):
    """Build the channel image URL."""
    chid = "".join(e for e in channelname.casefold() if e.isalnum())
    return CHANNEL_IMAGE_URL.format(sid, chid, url_prefix, territory)
