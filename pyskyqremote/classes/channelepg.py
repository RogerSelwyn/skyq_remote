"""Structure of a standard EPG programme."""

import json
from collections import OrderedDict
from dataclasses import dataclass, field
from datetime import datetime, timedelta

from .channel import ChannelInformation
from .programme import Programme


class ChannelEPGInformation:
    """Sky Q Channel EPG information retrieval methods."""

    def __init__(self, remoteConfig):
        """Initialise the channel epg information class."""
        self._remoteConfig = remoteConfig
        self._deviceAccess = remoteConfig.deviceAccess
        self._remoteCountry = remoteConfig.remoteCountry
        self._test_channel = remoteConfig.test_channel
        self._epgCacheLen = remoteConfig.epgCacheLen
        self._epgCache = OrderedDict()
        self._channel = None
        self._channelInformation = None

    def getEpgData(self, sid, epgDate, days=2):
        """Get EPG data for the specified channel/date."""
        epg = f"{str(sid)} {'{:0>2d}'.format(days)} {epgDate.strftime('%Y%m%d')}"

        if sid in self._epgCache and self._epgCache[sid]["epg"] == epg:
            return self._epgCache[sid]["channel"]

        channelNo = None
        channelName = None
        channelImageUrl = None
        programmes = set()

        channelNode = self._getChannelNode(sid)
        if channelNode:
            channelNo = channelNode["channelno"]
            channelName = channelNode["channel"]
            channelImageUrl = self._remoteCountry.buildChannelImageUrl(sid, channelName)

            for n in range(days):
                programmesData = self._remoteCountry.getEpgData(
                    sid, channelNo, channelName, epgDate + timedelta(days=n)
                )
                if len(programmesData) > 0:
                    programmes = programmes.union(programmesData)
                else:
                    break

        self._channel = ChannelEPG(sid, channelNo, channelName, channelImageUrl, sorted(programmes))
        self._epgCache[sid] = {
            "epg": epg,
            "channel": self._channel,
            "updatetime": datetime.utcnow(),
        }
        self._epgCache = OrderedDict(sorted(self._epgCache.items(), key=lambda x: x[1]["updatetime"], reverse=True))
        while len(self._epgCache) > self._epgCacheLen:
            self._epgCache.popitem(last=True)

        return self._channel

    def _getChannelNode(self, sid):
        if not self._channelInformation:
            self._channelInformation = ChannelInformation(self._remoteConfig)

        return self._channelInformation.getChannelNode(sid)


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
    channelImageUrl: str = field(
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


def ChannelEPGDecoder(obj):
    """Decode channel object from json."""
    channelepg = json.loads(obj, object_hook=_json_decoder_hook)
    if "__type__" in channelepg and channelepg["__type__"] == "__channelepg__":
        return ChannelEPG(programmes=channelepg["programmes"], **channelepg["attributes"])
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
    def default(self, obj):
        if isinstance(obj, ChannelEPG):
            type_ = "__channelepg__"
            programmes = obj.programmes
            attributes = {k: v for k, v in vars(obj).items() if k not in {"programmes"}}
            return {
                "__type__": type_,
                "attributes": attributes,
                "programmes": programmes,
            }

        if isinstance(obj, set):
            return list(obj)

        if isinstance(obj, Programme):
            attributes = {}
            for k, v in vars(obj).items():
                if isinstance(v, datetime):
                    v = v.strftime("%Y-%m-%dT%H:%M:%SZ")
                attributes[k] = v
            return {
                "__type__": "__programme__",
                "attributes": attributes,
            }

        json.JSONEncoder.default(self, obj)  # pragma: no cover
