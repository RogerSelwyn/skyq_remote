"""Python module for accessing SkyQ box and EPG, and sending commands."""
import logging
from datetime import datetime

from .classes.app import AppInformation
from .classes.channel import ChannelInformation
from .classes.channelepg import ChannelEPGInformation
from .classes.device import DeviceInformation, TransportInfo
from .classes.deviceaccess import DeviceAccess
from .classes.favourite import FavouriteInformation
from .classes.media import MediaInformation
from .classes.programme import Programme
from .classes.recordings import RecordingsInformation
from .const import (
    ALLRECORDINGS,
    COMMANDS,
    EPG_ERROR_NO_DATA,
    EPG_ERROR_PAST_END,
    SKY_STATE_OFF,
    SKY_STATE_ON,
    SKY_STATE_STANDBY,
    SKY_STATE_UNSUPPORTED,
    TERRITORIES,
    UNSUPPORTED_DEVICES,
    URL_PREFIX,
)

_LOGGER = logging.getLogger(__name__)


class SkyQRemote:
    """SkyQRemote is the instantiation of the SKYQ remote ccontrol."""

    commands = COMMANDS

    def __init__(self, host, epg_cache_len=20, port=49160, json_port=9006):
        """Stand up a new SkyQ box."""
        self._remote_setup = False
        self._device_type = None
        self._host = host
        self._override_country = None
        self._channel = None
        self._programme = None
        self._recorded_programme = None
        self._last_programme_epg = None
        self._last_pvr_id = None
        self._error = False
        self._channellist = None

        self._app_information = None
        self._channel_information = None
        self._device_information = None
        self._channel_epg_information = None
        self._favourite_information = None
        self._media_information = None
        self._recordings_information = None

        self._remote_config = _RemoteConfig(host, port, json_port, epg_cache_len)

        self._setup_remote()

    @property
    def device_setup(self):
        """Get the dev ice setp state."""
        return self._remote_setup

    @property
    def device_type(self):
        """Get the device type of the Sky Q box."""
        return self._device_type

    def power_status(self) -> str:
        """Get the power status of the Sky Q box."""
        if not self._remote_setup:
            self._setup_remote()

        system_info = self._device_information.get_system_information()

        if system_info is None:
            return SKY_STATE_OFF
        if "activeStandby" in system_info and system_info["activeStandby"] is True:
            return SKY_STATE_STANDBY

        return SKY_STATE_ON

    def get_current_state(self):
        """Get current state of the SkyQ box."""
        if not self._remote_setup:
            self._setup_remote()

        if self._device_type in UNSUPPORTED_DEVICES:
            return TransportInfo(SKY_STATE_UNSUPPORTED, None, None)

        return self._device_information.get_transport_information()

    def get_active_application(self):
        """Get the active application on Sky Q box."""
        if not self._app_information:
            self._app_information = AppInformation(self._remote_config)

        return self._app_information.get_active_application()

    def get_current_media(self):
        """Get the currently playing media on the SkyQ box."""
        if not self._media_information:
            self._media_information = MediaInformation(self._remote_config)

        return self._media_information.get_current_media()

    def get_epg_data(self, sid, epg_date, days=2):
        """Get EPG data for the specified channel/date."""
        if not self._channel_epg_information:
            self._channel_epg_information = ChannelEPGInformation(self._remote_config)

        return self._channel_epg_information.get_epg_data(sid, epg_date, days)

    def get_programme_from_epg(self, sid, epg_date, query_date):
        """Get programme from EPG for specfied time and channel."""
        sidint = 0
        try:
            sidint = int(sid)
        except ValueError:
            if not self._error:
                self._error = True
                _LOGGER.info(
                    "I0010 - Programme data not found for host: %s/%s sid: %s : %s",
                    self._host,
                    self._override_country,
                    sid,
                    epg_date,
                )
                return EPG_ERROR_NO_DATA

            self._error = False

        programme_epg = f'{sidint} {epg_date.strftime("%Y%m%d")}'
        if (
            self._last_programme_epg == programme_epg
            and query_date < self._programme.endtime
        ):
            return self._programme

        epg_data = self.get_epg_data(sidint, epg_date)

        if len(epg_data.programmes) == 0:
            if not self._error:
                self._error = True
                _LOGGER.info(
                    "I0020 - Programme data not found for host: %s/%s sid: %s : %s",
                    self._host,
                    self._override_country,
                    sid,
                    epg_date,
                )
            return EPG_ERROR_NO_DATA

        self._error = False

        try:
            programme = next(
                p
                for p in epg_data.programmes
                if p.starttime <= query_date and p.endtime >= query_date
            )

            self._programme = programme
            self._last_programme_epg = programme_epg
            return programme

        except StopIteration:
            return EPG_ERROR_PAST_END

    def get_current_live_tv_programme(self, sid):
        """Get current live programme on the specified channel."""
        try:
            query_date = datetime.utcnow()
            programme = self.get_programme_from_epg(sid, query_date, query_date)
            if not isinstance(programme, Programme):
                return None

            return programme
        except Exception as err:  # pylint: disable=broad-except
            _LOGGER.exception(
                "X0010 - Error occurred: %s : %s : %s", self._host, sid, err
            )
            return None

    def get_recordings(self, status=ALLRECORDINGS, limit=1000, offset=0):
        """Get the list of available Recordings."""
        if not self._recordings_information:
            self._recordings_information = RecordingsInformation(self._remote_config)

        return self._recordings_information.get_recordings(status, limit, offset)

    def get_recording(self, pvrid):
        """Get the recording details."""
        if not self._recordings_information:
            self._recordings_information = RecordingsInformation(self._remote_config)

        if self._last_pvr_id == pvrid:
            return self._recorded_programme
        self._last_pvr_id = pvrid

        self._recorded_programme = self._recordings_information.get_recording(pvrid)
        return self._recorded_programme

    def get_quota(self):
        """Retrieve the available storage quota."""
        if not self._recordings_information:
            self._recordings_information = RecordingsInformation(self._remote_config)

        return self._recordings_information.get_quota()

    def book_recording(self, eid, series=False):
        """Book recording for specified item."""
        if not self._recordings_information:
            self._recordings_information = RecordingsInformation(self._remote_config)

        return self._recordings_information.book_recording(eid, series)

    def book_ppv_recording(self, eid, offerref):
        """Book recording for specified item."""
        if not self._recordings_information:
            self._recordings_information = RecordingsInformation(self._remote_config)

        return self._recordings_information.book_ppv_recording(eid, offerref)

    def series_link(self, pvrid, linkon=True):
        """Book recording for specified item."""
        if not self._recordings_information:
            self._recordings_information = RecordingsInformation(self._remote_config)

        return self._recordings_information.series_link(pvrid, linkon)

    def recording_keep(self, pvrid, keepon=True):
        """Keep the recording."""
        if not self._recordings_information:
            self._recordings_information = RecordingsInformation(self._remote_config)

        return self._recordings_information.recording_keep(pvrid, keepon)

    def recording_lock(self, pvrid, lockon=True):
        """Lock the recording."""
        if not self._recordings_information:
            self._recordings_information = RecordingsInformation(self._remote_config)

        return self._recordings_information.recording_lock(pvrid, lockon)

    def recording_delete(self, pvrid, deleteon=True):
        """Delete the recording."""
        if not self._recordings_information:
            self._recordings_information = RecordingsInformation(self._remote_config)

        return self._recordings_information.recording_delete(pvrid, deleteon)

    def recording_erase(self, pvrid):
        """Delete the recording."""
        if not self._recordings_information:
            self._recordings_information = RecordingsInformation(self._remote_config)

        return self._recordings_information.recording_erase(pvrid)

    def recording_erase_all(self):
        """Delete the reording."""
        if not self._recordings_information:
            self._recordings_information = RecordingsInformation(self._remote_config)

        return self._recordings_information.recording_erase_all()

    def recording_set_last_played_position(self, pvrid, pos):
        """Set the last played position for specified item."""
        if not self._recordings_information:
            self._recordings_information = RecordingsInformation(self._remote_config)

        return self._recordings_information.recording_set_last_played_position(
            pvrid, pos
        )

    def get_device_information(self):
        """Get the device information from the SkyQ box."""
        if not self._device_information:
            self._device_information = DeviceInformation(self._remote_config)

        device_info = self._device_information.get_device_information(
            self._override_country
        )
        if not device_info:
            return None

        self._remote_config.set_device_info(device_info)
        return device_info

    def get_channel_list(self):
        """Get Channel list for Sky Q box."""
        if not self._channel_information:
            self._channel_information = ChannelInformation(self._remote_config)

        self._channellist = self._channel_information.get_channel_list()
        return self._channellist

    def get_channel_info(self, channel_no):
        """Retrieve channel information for specified channelNo."""
        if not self._channel_information:
            self._channel_information = ChannelInformation(self._remote_config)

        return self._channel_information.get_channel_info(channel_no)

    def get_favourite_list(self):
        """Retrieve the list of favourites."""
        if not self._favourite_information:
            self._favourite_information = FavouriteInformation(self._remote_config)

        if not self._channellist:
            self.get_channel_list()
        return self._favourite_information.get_favourite_list(self._channellist)

    def press(self, sequence):
        """Issue the specified sequence of commands to SkyQ box."""
        self._remote_config.device_access.press(sequence)

    def set_overrides(
        self, override_country=None, test_channel=None, json_port=None, port=None
    ):
        """Override various items."""
        if override_country:
            self._override_country = override_country
        if test_channel:
            self._remote_config.test_channel = test_channel
        if json_port:
            self._remote_config.json_port = json_port
        if port:
            self._remote_config.port = port

    def _setup_remote(self):
        device_info = self.get_device_information()
        if not device_info:
            return

        self._remote_setup = True
        self._device_type = self._remote_config.device_info.deviceType


class _RemoteConfig:
    device_access = None
    host = 0
    port = 0
    json_port = 0
    epg_cache_len = 0
    remote_country = ""
    test_channel = 0
    epg_cache_len = 0
    device_info = None

    def __init__(
        self,
        host,
        port,
        json_port,
        epg_cache_len,
        device_access=None,
        remote_country=None,
        test_channel=None,
        device_info=None,
    ):
        self.host = host
        self.port = port
        self.json_port = json_port
        self.device_access = device_access
        self.remote_country = remote_country
        self.territory = None
        self.test_channel = test_channel
        self.epg_cache_len = epg_cache_len
        self.device_access = DeviceAccess(host, json_port, port)
        self.device_info = device_info
        self.territory = None
        self.url_prefix = None

    def set_device_info(self, device_info):
        """Initilise the device info for the Sky Q box."""
        self.device_info = device_info
        self.territory = TERRITORIES[device_info.used_country_code]
        self.url_prefix = URL_PREFIX[device_info.used_country_code]
