"""Sky Q app methods and data class."""

import json
from dataclasses import dataclass, field

from ..const import APP_EPG, APP_STATUS_VISIBLE, REST_PATH_APPS, WS_CURRENT_APPS


class AppInformation:
    """Sky Q app information retrieval methods."""

    def __init__(self, remoteConfig):
        """Initialise the app information class."""
        self._deviceAccess = remoteConfig.deviceAccess
        self._currentApp = APP_EPG
        self._apps = {}

    def getActiveApplication(self):
        """Get the active application on Sky Q box."""
        try:
            apps = self._deviceAccess.callSkyWebSocket(WS_CURRENT_APPS)
            if apps:
                self._currentApp = next(a for a in apps["apps"] if a["status"] == APP_STATUS_VISIBLE)["appId"]

            return App(self._currentApp, self._get_app_title(self._currentApp))
        except Exception:
            return App(self._currentApp, self._get_app_title(self._currentApp))

    def _get_app_title(self, appId):
        if len(self._apps) == 0:
            apps = self._deviceAccess.retrieveInformation(REST_PATH_APPS)
            if not apps:
                return None
            for a in apps["apps"]:
                self._apps[a["appId"]] = a["title"]

        return self._apps[appId] if appId in self._apps else None


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
