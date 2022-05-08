#!/usr/bin/env python
"""Test script."""


import json
import sys
from datetime import datetime

from pyskyqremote.classes.channelepg import channel_epg_decoder
from pyskyqremote.classes.media import media_decoder
from pyskyqremote.const import APP_EPG, SKY_STATE_OFF, SKY_STATE_STANDBY
from pyskyqremote.skyq_remote import SkyQRemote

# from pyskyqremote.device import DeviceDecoder
# from pyskyqremote.channel import ChannelDecoder
# from pyskyqremote.programme import ProgrammeDecoder, RecordedProgrammeDecoder


# Run ./bash_sky.py <sky_box_ip>
# example: ./bash_sky_test.py 192.168.0.9
# Note: you may need to modify top line change python3 to python,
# depending on OS/setup. this is works for me on my mac
country = None  # pylint: disable=invalid-name
queryDate = datetime.utcnow()
if len(sys.argv) > 2 and sys.argv[2] != "None":
    country = sys.argv[2]
test_channel = (  # pylint: disable=invalid-name
    sys.argv[3] if len(sys.argv) > 3 else None
)
if len(sys.argv) > 4:
    queryDate = datetime.utcfromtimestamp(int(sys.argv[4]))

sky = SkyQRemote(sys.argv[1])
sky.set_overrides(override_country=country, test_channel=test_channel)

print("----------- Power status")
print(sky.power_status())

if sky.power_status() != SKY_STATE_OFF:
    print("----------- DeviceInfo")
    print(sky.get_device_information().as_json())
    # print("----------- DeviceInfo Decoded")
    # print(DeviceDecoder(sky.getDeviceInformation().as_json()))

print("----------- Current status")
response = sky.get_current_state()  # pylint: disable=invalid-name
current_state = response.state
print(current_state)
if current_state == SKY_STATE_STANDBY:
    exit()

print("----------- TRANSPORT INFO")
transportInfo = sky.get_current_state()  # pylint: disable=invalid-name
print(transportInfo)


print("----------- Active Application")
appJSON = sky.get_active_application().as_json()
print(appJSON)
app = json.loads(appJSON)["attributes"]["appId"]
if app != APP_EPG:
    exit()

print("----------- Current Media")
currentMedia = sky.get_current_media().as_json()
print(currentMedia)

media = media_decoder(currentMedia)
if not media.live:
    print("----------- Recording")
    print(sky.get_recording(media.pvrid).as_json())

sid = test_channel or media.sid
if sid:
    print(f"----------- Programme from Epg - {queryDate} - {sid}")
    print(sky.get_programme_from_epg(sid, queryDate, queryDate).as_json())

    print(f"----------- Current Live TV - {sid}")
    print(sky.get_current_live_tv_programme(sid).as_json())

print("----------- Get Channel Info - 101")
print(sky.get_channel_info("101").as_json())

# print("----------- Channel list")
# print(sky.get_channel_list().as_json())

print("----------- Favourites")
print(sky.get_favourite_list().as_json())

# print("----------- Today's EPG")
# epgJSON = sky.get_epg_data(sid, queryDate).as_json()
# print(epgJSON)

# print("----------- Get scheduled recordings")
# print(sky.get_recordings("SCHEDULED").as_json())

print("----------- Get quota info")
print(sky.get_quota().as_json())

# print("----------- Book recording")
# epgProgrammes = channel_epg_decoder(epgJSON).programmes
# eid = epgProgrammes[len(epgProgrammes) - 1].eid
# print(eid)
# print(sky.book_recording(eid))
# recordings = sky.get_recordings("SCHEDULED")
# pvrid = next(
#     (
#         recording.pvrid
#         for recording in recordings.programmes
#         if recording.eid == eid
#     ),
#     None,
# )

# print(pvrid)

# print("----------- Book series recording")
# print(sky.book_recording(eid, series=True))


# print("----------- Unlink series")
# print(sky.series_link(pvrid, False))
# print("----------- Link series")
# print(sky.series_link(pvrid, True))
# sky.series_link(pvrid, False)

# print("----------- Recording keep")
# print(sky.recording_keep(pvrid, True))
# print("----------- Recording unkeep")
# print(sky.recording_keep(pvrid, False))

# print("----------- Recording lock")
# print(sky.recording_lock(pvrid, True))
# print("----------- Recording unlock")
# print(sky.recording_lock(pvrid, False))

# print("----------- Recording delete")
# print(sky.recording_delete(pvrid, True))
# print("----------- Recording undelete")
# print(sky.recording_delete(pvrid, False))

# print("----------- Recording erase")
# print(sky.recording_erase(pvrid))

# print("----------- Set last played position")
# print(sky.recording_set_last_played_position("P2900dbbf", 20))
