"""Favourites methods for the Sky Q box."""
import json
from dataclasses import dataclass, field
from operator import attrgetter

from ..const import REST_FAVOURITES


class FavouriteInformation:
    """Sky Q favourites information retrieval methods."""

    def __init__(self, remote_config):
        """Initialise the favourites information class."""
        self._device_access = remote_config.device_access
        self._channellist = None
        self._favouritelist = None

    def get_favourite_list(self, channellist):
        """Retrieve the list of favourites."""
        self._channellist = channellist
        favourites = self._device_access.retrieve_information(REST_FAVOURITES)
        if not favourites or "favourites" not in favourites:
            return []

        favitems = set()

        for favourite in favourites["favourites"]:
            favsid = favourite["sid"]
            channel = self._get_fav_channel(favsid)
            channelno = channel.channelno if channel else None
            channelname = channel.channelname if channel else None
            favourite = Favourite(favourite["lcn"], channelno, channelname, favsid)
            favitems.add(favourite)

        favouritesorted = sorted(favitems, key=attrgetter("lcn"))
        self._favouritelist = FavouriteList(favouritesorted)

        return self._favouritelist

    def _get_fav_channel(self, sid):
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


def favourite_list_decoder(obj):
    """Decode favourite object from json."""
    favouritelist = json.loads(obj, object_hook=_json_decoder_hook)
    if "__type__" in favouritelist and favouritelist["__type__"] == "__favouritelist__":
        return FavouriteList(
            favourites=favouritelist["favourites"], **favouritelist["attributes"]
        )
    return favouritelist


def _json_decoder_hook(obj):
    """Decode JSON into appropriate types used in this library."""
    if "__type__" in obj and obj["__type__"] == "__favourite__":
        obj = Favourite(**obj["attributes"])
    return obj


class _FavouriteListJSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, FavouriteList):
            type_ = "__favouritelist__"
            favourites = o.favourites
            attributes = {k: v for k, v in vars(o).items() if k not in {"favourites"}}
            return {
                "__type__": type_,
                "attributes": attributes,
                "favourites": favourites,
            }

        if isinstance(o, set):
            return list(o)

        if isinstance(o, Favourite):
            attributes = dict(vars(o))
            return {
                "__type__": "__favourite__",
                "attributes": attributes,
            }

        json.JSONEncoder.default(self, o)  # pragma: no cover


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


def favourite_decoder(obj):
    """Decode favourite object from json."""
    favourite = json.loads(obj)
    if "__type__" in favourite and favourite["__type__"] == "__favourite__":
        return favourite(**favourite["attributes"])
    return favourite


class _favouriteJSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Favourite):
            attributes = dict(vars(o))
            return {
                "__type__": "__favourite__",
                "attributes": attributes,
            }
