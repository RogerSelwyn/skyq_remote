"""Methods for retrieving device information."""

import json
import logging
from dataclasses import dataclass, field

from ..const import KNOWN_COUNTRIES, REST_PATH_DEVICEINFO, REST_PATH_SYSTEMINFO, UPNP_GET_TRANSPORT_INFO

_LOGGER = logging.getLogger(__name__)


class DeviceInformation:
    """Sky Q device information retrieval methods."""

    def __init__(self, remoteConfig):
        """Initialise the device information class."""
        self._remoteConfig = remoteConfig
        self._deviceAccess = remoteConfig.deviceAccess
        self._port = remoteConfig.port

    def getTransportInformation(self):
        """Get the transport information from the SkyQ box."""
        return self._deviceAccess.callSkySOAPService(self._remoteConfig.soapControlURL, UPNP_GET_TRANSPORT_INFO)

    def getSystemInformation(self):
        """Get the system information from the SkyQ box."""
        return self._deviceAccess.retrieveInformation(REST_PATH_SYSTEMINFO)

    def getDeviceInformation(self, overrideCountry):
        """Get the device information from the SkyQ box."""
        deviceInfo = self._deviceAccess.retrieveInformation(REST_PATH_DEVICEINFO)
        if not deviceInfo:
            return None

        systemInfo = self.getSystemInformation()
        ASVersion = deviceInfo["ASVersion"]
        IPAddress = deviceInfo["IPAddress"]
        countryCode = deviceInfo["countryCode"]
        gateway = deviceInfo["gateway"]
        hardwareModel = systemInfo["hardwareModel"]
        deviceType = systemInfo["deviceType"]
        hardwareName = deviceInfo["hardwareName"]
        manufacturer = systemInfo["manufacturer"]
        modelNumber = deviceInfo["modelNumber"]
        serialNumber = deviceInfo["serialNumber"]
        versionNumber = deviceInfo["versionNumber"]
        bouquet = deviceInfo["bouquet"]
        subbouquet = deviceInfo["subbouquet"]

        epgCountryCode = overrideCountry or countryCode.upper()
        if not epgCountryCode:
            _LOGGER.error(f"E0010 - No country identified: {self._host}")
            return None

        if epgCountryCode in KNOWN_COUNTRIES:
            epgCountryCode = KNOWN_COUNTRIES[epgCountryCode]

        return Device(
            ASVersion,
            IPAddress,
            countryCode,
            epgCountryCode,
            hardwareModel,
            hardwareName,
            deviceType,
            gateway,
            manufacturer,
            modelNumber,
            serialNumber,
            versionNumber,
            bouquet,
            subbouquet,
        )

    def getSoapControlURL(self):
        """Get the soapcontrourl for the SkyQ box."""
        url_index = 0
        soapControlURL = None
        while soapControlURL is None and url_index < 50:
            soapControlURL = self._deviceAccess.getSoapControlURL(url_index)["url"]
            url_index += 1

        return soapControlURL


@dataclass
class Device:
    """SkyQ Device Class."""

    ASVersion: str = field(
        init=True,
        repr=True,
        compare=False,
    )
    IPAddress: str = field(
        init=True,
        repr=True,
        compare=False,
    )
    countryCode: str = field(
        init=True,
        repr=True,
        compare=False,
    )
    epgCountryCode: str = field(
        init=True,
        repr=True,
        compare=False,
    )
    hardwareModel: str = field(
        init=True,
        repr=True,
        compare=False,
    )
    hardwareName: str = field(
        init=True,
        repr=True,
        compare=False,
    )
    deviceType: str = field(
        init=True,
        repr=True,
        compare=False,
    )
    gateway: str = field(
        init=True,
        repr=True,
        compare=False,
    )
    manufacturer: str = field(
        init=True,
        repr=True,
        compare=False,
    )
    modelNumber: str = field(
        init=True,
        repr=True,
        compare=False,
    )
    serialNumber: str = field(
        init=True,
        repr=True,
        compare=False,
    )
    versionNumber: str = field(
        init=True,
        repr=True,
        compare=False,
    )
    bouquet: str = field(
        init=True,
        repr=True,
        compare=False,
    )
    subbouquet: str = field(
        init=True,
        repr=True,
        compare=False,
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
