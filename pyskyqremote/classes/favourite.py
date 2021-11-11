"""Favourites methods for the Sky Q box."""
import json
from dataclasses import dataclass, field
from operator import attrgetter

from ..const import REST_FAVOURITES


class FavouriteInformation:
    """Sky Q favourites information retrieval methods."""

    def __init__(self, remoteConfig):
        """Initialise the favourites information class."""
        self._deviceAccess = remoteConfig.deviceAccess

    def getFavouriteList(self, channellist):
        """Retrieve the list of favourites."""
        self._channellist = channellist
        favourites = self._deviceAccess.http_json(REST_FAVOURITES)
        if not favourites or "favourites" not in favourites:
            return []

        favitems = set()

        for f in favourites["favourites"]:
            favsid = f["sid"]
            channel = self._getFavChannel(favsid)
            channelno = channel.channelno if channel else None
            channelname = channel.channelname if channel else None
            favourite = Favourite(f["lcn"], channelno, channelname, favsid)
            favitems.add(favourite)

        favouritesorted = sorted(favitems, key=attrgetter("lcn"))
        self._favouritelist = FavouriteList(favouritesorted)

        return self._favouritelist

    def _getFavChannel(self, sid):
        try:
            return next(c for c in self._channellist.channels if c.channelsid == sid)
        except StopIteration:
            return None


@dataclass
class FavouriteList:
    """SkyQ Favourite List Class."""

    favourites: set = field(
        init=True,
        repr=True,
        compare=False,
    )

    def as_json(self) -> str:
        """Return a JSON string representing this Favourite."""
        return json.dumps(self, cls=_FavouriteListJSONEncoder)


def FavouriteListDecoder(obj):
    """Decode favourite object from json."""
    favouritelist = json.loads(obj, object_hook=_json_decoder_hook)
    if "__type__" in favouritelist and favouritelist["__type__"] == "__favouritelist__":
        return FavouriteList(favourites=favouritelist["favourites"], **favouritelist["attributes"])
    return favouritelist


def _json_decoder_hook(obj):
    """Decode JSON into appropriate types used in this library."""
    if "__type__" in obj and obj["__type__"] == "__favourite__":
        obj = Favourite(**obj["attributes"])
    return obj


class _FavouriteListJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, FavouriteList):
            type_ = "__favouritelist__"
            favourites = obj.favourites
            attributes = {k: v for k, v in vars(obj).items() if k not in {"favourites"}}
            return {
                "__type__": type_,
                "attributes": attributes,
                "favourites": favourites,
            }

        if isinstance(obj, set):
            return list(obj)

        if isinstance(obj, Favourite):
            attributes = {k: v for k, v in vars(obj).items()}
            return {
                "__type__": "__favourite__",
                "attributes": attributes,
            }

        json.JSONEncoder.default(self, obj)  # pragma: no cover


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
