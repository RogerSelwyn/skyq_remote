"""Structure of a media information."""

import json
from dataclasses import dataclass, field
from datetime import datetime

from ..const import CURRENT_URI, PVR, UPNP_GET_MEDIA_INFO, XSI
from .channel import ChannelInformation, build_channel_image_url


class MediaInformation:
    """Sky Q media information retrieval methods."""

    def __init__(self, remote_config):
        """Initialise the media information class."""
        self._remote_config = remote_config
        self._device_access = remote_config.device_access
        self._remote_country = remote_config.remote_country
        self._test_channel = remote_config.test_channel
        self._channel_information = None

    def get_current_media(self):
        """Get the currently playing media on the SkyQ box."""
        channel = None
        channelno = None
        image_url = None
        sid = None
        pvrid = None
        live = False

        response = self._device_access.call_sky_soap_service(UPNP_GET_MEDIA_INFO)
        if response is None:
            return None

        current_uri = response[CURRENT_URI]
        if current_uri is None:
            return None

        if XSI in current_uri:
            sid = self._test_channel or int(current_uri[6:], 16)
            live = True
            if channel_node := self._get_channel_node(sid):
                channel = channel_node["channel"]
                channelno = channel_node["channelno"]
                image_url = build_channel_image_url(
                    sid,
                    channel,
                    self._remote_config.url_prefix,
                    self._remote_config.territory,
                )
        elif PVR in current_uri:
            # Recorded content
            pvrid = f"P{current_uri[11:]}"
            live = False

        return Media(channel, channelno, image_url, sid, pvrid, live)

    def _get_channel_node(self, sid):
        if not self._channel_information:
            self._channel_information = ChannelInformation(self._remote_config)

        return self._channel_information.get_channel_node(sid)


@dataclass
class Media:
    """SkyQ Programme Class."""

    channel: str = field(
        init=True,
        repr=True,
        compare=False,
    )
    channelno: str = field(
        init=True,
        repr=True,
        compare=False,
    )
    image_url: str = field(
        init=True,
        repr=True,
        compare=False,
    )
    sid: str = field(
        init=True,
        repr=True,
        compare=False,
    )
    pvrid: str = field(
        init=True,
        repr=True,
        compare=False,
    )
    live: bool = field(
        init=True,
        repr=True,
        compare=False,
    )

    def as_json(self) -> str:
        """Return a JSON string representing this media info."""
        return json.dumps(self, cls=_MediaJSONEncoder)


def media_decoder(obj):
    """Decode programme object from json."""
    media = json.loads(obj)
    if "__type__" in media and media["__type__"] == "__media__":
        return Media(**media["attributes"])
    return media


class _MediaJSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Media):
            attributes = {}
            for k, val in vars(o).items():
                if isinstance(val, datetime):
                    val = val.strftime("%Y-%m-%dT%H:%M:%SZ")
                attributes[k] = val
            return {
                "__type__": "__media__",
                "attributes": attributes,
            }
