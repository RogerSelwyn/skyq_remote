#!/usr/bin/env python
"""Test script."""
import sys
from datetime import datetime

from pyskyqremote.skyq_remote import SkyQRemote
from pyskyqremote.const import APP_EPG, SKY_STATE_STANDBY, SKY_STATE_OFF
from pyskyqremote.classes.media import MediaDecoder

# from pyskyqremote.device import DeviceDecoder
# from pyskyqremote.channel import ChannelDecoder
# from pyskyqremote.programme import ProgrammeDecoder, RecordedProgrammeDecoder


# Run ./bash_sky.py <sky_box_ip>
# example: ./bash_sky_test.py 192.168.0.9
# Note: you may need to modify top line change python3 to python, depending on OS/setup. this is works for me on my mac
country = None
test_channel = None
queryDate = datetime.utcnow()
if len(sys.argv) > 2:
    if sys.argv[2] != "None":
        country = sys.argv[2]
if len(sys.argv) > 3:
    test_channel = sys.argv[3]
if len(sys.argv) > 4:
    queryDate = datetime.utcfromtimestamp(int(sys.argv[4]))

sky = SkyQRemote(sys.argv[1])
sky.setOverrides(overrideCountry=country, test_channel=test_channel)

print("----------- Power status")
print(sky.powerStatus())

if sky.powerStatus != SKY_STATE_OFF:
    print("----------- DeviceInfo")
    print(sky.getDeviceInformation().as_json())
    # print("----------- DeviceInfo Decoded")
    # print(DeviceDecoder(sky.getDeviceInformation().as_json()))

print("----------- Current status")
currentState = sky.getCurrentState()
print(sky.getCurrentState())
if currentState == SKY_STATE_STANDBY:
    exit()

print("----------- Active Application")
app = sky.getActiveApplication()
print(str(app))
if app != APP_EPG:
    exit()

print("----------- Current Media")
currentMedia = sky.getCurrentMedia().as_json()
print(currentMedia)

media = MediaDecoder(currentMedia)
if not media.live:
    print("----------- Recording")
    print(sky.getRecording(media.pvrId).as_json())

if test_channel:
    sid = test_channel
else:
    sid = media.sid

print(f"----------- Programme from Epg - {queryDate} - {sid}")
print(sky.getProgrammeFromEpg(sid, queryDate, queryDate).as_json())

print(f"----------- Current Live TV - {sid}")
print(sky.getCurrentLiveTVProgramme(sid).as_json())

print("----------- Channel list")
print(sky.getChannelList().as_json())

# print("----------- Today's EPG")
# print(sky.getEpgData(sid, queryDate).as_json())
