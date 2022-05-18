"""Methods for retrieving device information."""

import json
import logging
from dataclasses import dataclass, field

from ..const import (CURRENT_SPEED, CURRENT_TRANSPORT_STATE,
                     CURRENT_TRANSPORT_STATUS, DEFAULT_TRANSPORT_SPEED,
                     DEFAULT_TRANSPORT_STATE, KNOWN_COUNTRIES,
                     REST_PATH_DEVICEINFO, REST_PATH_SYSTEMINFO,
                     SKY_STATE_NOMEDIA, SKY_STATE_OFF, SKY_STATE_PAUSED,
                     SKY_STATE_PLAYING, SKY_STATE_STANDBY, SKY_STATE_STOPPED,
                     SKY_STATE_TRANSITIONING, SKY_STATE_UNSUPPORTED,
                     UPNP_GET_TRANSPORT_INFO)

_LOGGER = logging.getLogger(__name__)


class DeviceInformation:
    """Sky Q device information retrieval methods."""

    def __init__(self, remote_config):
        """Initialise the device information class."""
        self._remote_config = remote_config
        self._device_access = remote_config.device_access
        self._port = remote_config.port

    def get_transport_information(self):
        """Get the transport information from the SkyQ box."""
        response = self._device_access.call_sky_soap_service(UPNP_GET_TRANSPORT_INFO)
        if response is not None:
            return TransportInfo(
                response[CURRENT_TRANSPORT_STATE],
                response[CURRENT_TRANSPORT_STATUS],
                response[CURRENT_SPEED],
            )

        return TransportInfo(
            SKY_STATE_OFF, DEFAULT_TRANSPORT_STATE, DEFAULT_TRANSPORT_SPEED
        )

    def get_system_information(self):
        """Get the system information from the SkyQ box."""
        return self._device_access.retrieve_information(REST_PATH_SYSTEMINFO)

    def get_device_information(self, override_country):
        """Get the device information from the SkyQ box."""
        device_info = self._device_access.retrieve_information(REST_PATH_DEVICEINFO)
        if not device_info:
            return None

        system_info = self.get_system_information()
        as_version = device_info["ASVersion"]
        ip_address = device_info["IPAddress"]
        country_code = device_info["countryCode"]
        gateway = device_info["gateway"]
        hardware_model = system_info["hardwareModel"]
        device_type = system_info["deviceType"]
        hardware_name = device_info["hardwareName"]
        manufacturer = system_info["manufacturer"]
        model_number = device_info["modelNumber"]
        serial_number = device_info["serialNumber"]
        version_number = device_info["versionNumber"]
        bouquet = device_info["bouquet"]
        subbouquet = device_info["subbouquet"]
        wake_reason = system_info["wakeReason"]
        system_uptime = system_info["systemUptime"]
        hdr_capable = system_info["hdrCapable"]
        uhd_capable = system_info["uhdCapable"]

        used_country_code = override_country or country_code.upper()
        if not used_country_code:
            _LOGGER.error("E0010 - No country identified: %s", self._remote_config.host)
            return None

        if used_country_code in KNOWN_COUNTRIES:
            used_country_code = KNOWN_COUNTRIES[used_country_code]
        else:
            _LOGGER.error(
                "W0010 - Country code %s unknown, defaulting to GBR: %s",
                used_country_code,
                self._remote_config.host,
            )
            used_country_code = "GBR"

        return Device(
            as_version,
            ip_address,
            country_code,
            used_country_code,
            hardware_model,
            hardware_name,
            device_type,
            gateway,
            manufacturer,
            model_number,
            serial_number,
            version_number,
            bouquet,
            subbouquet,
            wake_reason,
            system_uptime,
            hdr_capable,
            uhd_capable,
        )


@dataclass
class Device:
    """SkyQ Device Class."""

    ASVersion: str = field(  # pylint: disable=invalid-name
        init=True,
        repr=True,
        compare=False,
    )
    IPAddress: str = field(  # pylint: disable=invalid-name
        init=True,
        repr=True,
        compare=False,
    )
    countryCode: str = field(  # pylint: disable=invalid-name
        init=True,
        repr=True,
        compare=False,
    )
    used_country_code: str = field(
        init=True,
        repr=True,
        compare=False,
    )
    hardwareModel: str = field(  # pylint: disable=invalid-name
        init=True,
        repr=True,
        compare=False,
    )
    hardwareName: str = field(  # pylint: disable=invalid-name
        init=True,
        repr=True,
        compare=False,
    )
    deviceType: str = field(  # pylint: disable=invalid-name
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
    modelNumber: str = field(  # pylint: disable=invalid-name
        init=True,
        repr=True,
        compare=False,
    )
    serialNumber: str = field(  # pylint: disable=invalid-name
        init=True,
        repr=True,
        compare=False,
    )
    versionNumber: str = field(  # pylint: disable=invalid-name
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
    wakeReason: str = field(  # pylint: disable=invalid-name
        init=True,
        repr=True,
        compare=False,
    )
    systemUptime: str = field(  # pylint: disable=invalid-name
        init=True,
        repr=True,
        compare=False,
    )
    hdrCapable: str = field(  # pylint: disable=invalid-name
        init=True,
        repr=True,
        compare=False,
    )
    uhdCapable: str = field(  # pylint: disable=invalid-name
        init=True,
        repr=True,
        compare=False,
    )

    def as_json(self) -> str:
        """Return a JSON string representing this device info."""
        return json.dumps(self, cls=_DeviceJSONEncoder)


def device_decoder(obj):
    """Decode programme object from json."""
    device = json.loads(obj)
    if "__type__" in device and device["__type__"] == "__device__":
        return Device(**device["attributes"])
    return device


class _DeviceJSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Device):
            attributes = dict(vars(o))
            return {
                "__type__": "__device__",
                "attributes": attributes,
            }


@dataclass
class TransportInfo:
    """SkyQ TransportInfo Class."""

    CurrentTransportState: str = field(  # pylint: disable=invalid-name
        init=True,
        repr=True,
        compare=False,
    )
    CurrentTransportStatus: str = field(  # pylint: disable=invalid-name
        init=True,
        repr=True,
        compare=False,
    )
    CurrentSpeed: float = field(  # pylint: disable=invalid-name
        init=True,
        repr=True,
        compare=False,
    )
    state: str = None

    def __post_init__(self):
        """Post process the transport setup."""
        self.state = self.CurrentTransportState
        if self.CurrentTransportState in [SKY_STATE_NOMEDIA, SKY_STATE_STOPPED]:
            self.state = SKY_STATE_STANDBY
        if self.CurrentTransportState in [SKY_STATE_PLAYING, SKY_STATE_TRANSITIONING]:
            self.state = SKY_STATE_PLAYING
        if self.CurrentTransportState == SKY_STATE_PAUSED:
            self.state = SKY_STATE_PAUSED
        if self.CurrentTransportState == SKY_STATE_UNSUPPORTED:
            self.CurrentTransportState = None

    def as_json(self) -> str:
        """Return a JSON string representing this app info."""
        return json.dumps(self, cls=_TransportInfoJSONEncoder)


def transportinfo_decoder(obj):
    """Decode programme object from json."""
    transportinfo = json.loads(obj)
    if "__type__" in transportinfo and transportinfo["__type__"] == "__transportinfo__":
        return TransportInfo(**transportinfo["attributes"])
    return transportinfo


class _TransportInfoJSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, TransportInfo):
            attributes = dict(vars(o))
            return {
                "__type__": "__transportinfo__",
                "attributes": attributes,
            }
