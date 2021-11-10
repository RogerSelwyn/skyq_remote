"""Structure of a media information."""

import json
from dataclasses import dataclass, field
from datetime import datetime

from ..const import CURRENT_URI, PVR, UPNP_GET_MEDIA_INFO, XSI


class MediaInformation:
    """Sky Q media information retrieval methods."""

    def __init__(self, deviceAccess):
        """Initialise the media information class."""
        self._deviceAccess = deviceAccess

    def getCurrentMedia(self, test_channel, soapControlURL, getChannelNode, remoteCountry):
        """Get the currently playing media on the SkyQ box."""
        channel = None
        channelno = None
        imageUrl = None
        sid = None
        pvrId = None
        live = False

        response = self._deviceAccess.callSkySOAPService(soapControlURL, UPNP_GET_MEDIA_INFO)
        if response is None:
            return None

        currentURI = response[CURRENT_URI]
        if currentURI is None:
            return None

        if XSI in currentURI:
            sid = test_channel or int(currentURI[6:], 16)
            live = True
            channelNode = getChannelNode(sid)
            if channelNode:
                channel = channelNode["channel"]
                channelno = channelNode["channelno"]
                imageUrl = remoteCountry.buildChannelImageUrl(sid, channel)
        elif PVR in currentURI:
            # Recorded content
            pvrId = "P" + currentURI[11:]
            live = False

        return Media(channel, channelno, imageUrl, sid, pvrId, live)


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
    imageUrl: str = field(
        init=True,
        repr=True,
        compare=False,
    )
    sid: str = field(
        init=True,
        repr=True,
        compare=False,
    )
    pvrId: str = field(
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


def MediaDecoder(obj):
    """Decode programme object from json."""
    media = json.loads(obj)
    if "__type__" in media and media["__type__"] == "__media__":
        return Media(**media["attributes"])
    return media


class _MediaJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Media):
            attributes = {}
            for k, v in vars(obj).items():
                if isinstance(v, datetime):
                    v = v.strftime("%Y-%m-%dT%H:%M:%SZ")
                attributes[k] = v
            return {
                "__type__": "__media__",
                "attributes": attributes,
            }
