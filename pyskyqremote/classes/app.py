"""Sky Q app methods and data class."""

import json
from dataclasses import dataclass, field

from ..const import APP_EPG, APP_STATUS_VISIBLE, REST_PATH_APPS, WS_CURRENT_APPS


class AppInformation:
    """Sky Q app information retrieval methods."""

    def __init__(self, remote_config):
        """Initialise the app information class."""
        self._device_access = remote_config.device_access
        self._current_app = APP_EPG
        self._apps = {}

    def get_active_application(self):
        """Get the active application on Sky Q box."""
        try:
            if apps := self._device_access.call_sky_web_socket(WS_CURRENT_APPS):
                self._current_app = next(
                    a for a in apps["apps"] if a["status"] == APP_STATUS_VISIBLE
                )["appId"]

            return App(self._current_app, self._get_app_title(self._current_app))
        except Exception:  # pylint: disable=broad-except
            return App(self._current_app, self._get_app_title(self._current_app))

    def _get_app_title(self, appid):
        if len(self._apps) == 0:
            apps = self._device_access.retrieve_information(REST_PATH_APPS)
            if not apps:
                return None
            for app in apps["apps"]:
                self._apps[app["appId"]] = app["title"]

        return self._apps[appid] if appid in self._apps else None


@dataclass
class App:
    """SkyQ App Class."""

    appId: str = field(  # pylint: disable=invalid-name
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


def app_decoder(obj):
    """Decode programme object from json."""
    app = json.loads(obj)
    if "__type__" in app and app["__type__"] == "__app__":
        return App(**app["attributes"])
    return app


class _AppJSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, App):
            attributes = dict(vars(o))
            return {
                "__type__": "__app__",
                "attributes": attributes,
            }
