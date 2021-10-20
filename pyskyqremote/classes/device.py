"""Structure of a device information."""

import json
from dataclasses import dataclass, field


@dataclass
class Device:
    """SkyQ Device Class."""

    ASVersion: str = field(
        init=True, repr=True, compare=False,
    )
    IPAddress: str = field(
        init=True, repr=True, compare=False,
    )
    countryCode: str = field(
        init=True, repr=True, compare=False,
    )
    epgCountryCode: str = field(
        init=True, repr=True, compare=False,
    )
    hardwareModel: str = field(
        init=True, repr=True, compare=False,
    )
    hardwareName: str = field(
        init=True, repr=True, compare=False,
    )
    manufacturer: str = field(
        init=True, repr=True, compare=False,
    )
    modelNumber: str = field(
        init=True, repr=True, compare=False,
    )
    serialNumber: str = field(
        init=True, repr=True, compare=False,
    )
    versionNumber: str = field(
        init=True, repr=True, compare=False,
    )

    def as_json(self) -> str:
        """Return a JSON string representing this device info."""
        return json.dumps(self, cls=_DeviceJSONEncoder)


def DeviceDecoder(obj):
    """Decode programme object from json."""
    device = json.loads(obj)
    if "__type__" in device and device["__type__"] == "__device__":
        return Device(**device["attributes"])
    return device


class _DeviceJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Device):
            attributes = {k: v for k, v in vars(obj).items()}
            return {
                "__type__": "__device__",
                "attributes": attributes,
            }
