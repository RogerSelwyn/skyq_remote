"""Structure of a standard EPG programme."""

import json
from collections import OrderedDict
from dataclasses import dataclass, field
from datetime import datetime, timedelta

from .channel import ChannelInformation
from .programme import Programme


class ChannelEPGInformation:
    """Sky Q Channel EPG information retrieval methods."""

    def __init__(self, remote_config):
        """Initialise the channel epg information class."""
        self._remote_config = remote_config
        self._device_access = remote_config.device_access
        self._remote_country = remote_config.remote_country
        self._test_channel = remote_config.test_channel
        self._epg_cache_len = remote_config.epg_cache_len
        self._epg_cache = OrderedDict()
        self._channel = None
        self._channel_information = None

    def get_epg_data(self, sid, epg_date, days=2):
        """Get EPG data for the specified channel/date."""
        epg = f'{sid} {"{:0>2d}".format(days)} {epg_date.strftime("%Y%m%d")}'

        if sid in self._epg_cache and self._epg_cache[sid]["epg"] == epg:
            return self._epg_cache[sid]["channel"]

        channel_no = None
        channel_name = None
        channel_image_url = None
        programmes = set()

        if channel_node := self._get_channel_node(sid):
            channel_no = channel_node["channelno"]
            channel_name = channel_node["channel"]
            channel_image_url = self._remote_country.build_channel_image_url(
                sid, channel_name
            )

            for day in range(days):
                programmes_data = self._remote_country.get_epg_data(
                    sid, channel_no, channel_name, epg_date + timedelta(days=day)
                )
                if len(programmes_data) > 0:
                    programmes = programmes.union(programmes_data)
                else:
                    break

        self._channel = ChannelEPG(
            sid, channel_no, channel_name, channel_image_url, sorted(programmes)
        )
        self._epg_cache[sid] = {
            "epg": epg,
            "channel": self._channel,
            "updatetime": datetime.utcnow(),
        }
        self._epg_cache = OrderedDict(
            sorted(
                self._epg_cache.items(), key=lambda x: x[1]["updatetime"], reverse=True
            )
        )
        while len(self._epg_cache) > self._epg_cache_len:
            self._epg_cache.popitem(last=True)

        return self._channel

    def _get_channel_node(self, sid):
        if not self._channel_information:
            self._channel_information = ChannelInformation(self._remote_config)

        return self._channel_information.get_channel_node(sid)


@dataclass
class ChannelEPG:
    """SkyQ Channel EPG Class."""

    sid: str = field(
        init=True,
        repr=True,
        compare=False,
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
    channelimageurl: str = field(
        init=True,
        repr=True,
        compare=False,
    )
    programmes: set = field(
        init=True,
        repr=True,
        compare=False,
    )

    def as_json(self) -> str:
        """Return a JSON string representing this Channel."""
        return json.dumps(self, cls=_ChannelEPGJSONEncoder)


def channel_epg_decoder(obj):
    """Decode channel object from json."""
    channelepg = json.loads(obj, object_hook=_json_decoder_hook)
    if "__type__" in channelepg and channelepg["__type__"] == "__channelepg__":
        return ChannelEPG(
            programmes=channelepg["programmes"], **channelepg["attributes"]
        )
    return channelepg


def _json_decoder_hook(obj):
    """Decode JSON into appropriate types used in this library."""
    if "starttime" in obj:
        obj["starttime"] = datetime.strptime(obj["starttime"], "%Y-%m-%dT%H:%M:%SZ")
    if "endtime" in obj:
        obj["endtime"] = datetime.strptime(obj["endtime"], "%Y-%m-%dT%H:%M:%SZ")
    if "__type__" in obj and obj["__type__"] == "__programme__":
        obj = Programme(**obj["attributes"])
    return obj


class _ChannelEPGJSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, ChannelEPG):
            type_ = "__channelepg__"
            programmes = o.programmes
            attributes = {k: v for k, v in vars(o).items() if k not in {"programmes"}}
            return {
                "__type__": type_,
                "attributes": attributes,
                "programmes": programmes,
            }

        if isinstance(o, set):
            return list(o)

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

        json.JSONEncoder.default(self, o)  # pragma: no cover
