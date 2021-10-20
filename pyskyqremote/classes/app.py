"""Structure of an app information."""

import json
from dataclasses import dataclass, field


@dataclass
class App:
    """SkyQ App Class."""

    appId: str = field(
        init=True,
        repr=True,
        compare=False,
    )
    title: str = field(
        init=True,
        repr=True,
        compare=False,
    )

    def as_json(self) -> str:
        """Return a JSON string representing this app info."""
        return json.dumps(self, cls=_AppJSONEncoder)


def AppDecoder(obj):
    """Decode programme object from json."""
    app = json.loads(obj)
    if "__type__" in app and app["__type__"] == "__app__":
        return App(**app["attributes"])
    return app


class _AppJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, App):
            attributes = {k: v for k, v in vars(obj).items()}
            return {
                "__type__": "__app__",
                "attributes": attributes,
            }
