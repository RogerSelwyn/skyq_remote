"""List of favourites available on the Sky Q box."""

import json
from dataclasses import dataclass, field

from .favourite import Favourite


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
