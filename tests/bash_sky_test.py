#!/usr/bin/env python
"""Test script."""

import json
import sys
from datetime import datetime

from pyskyqremote.classes.channelepg import ChannelEPGDecoder
from pyskyqremote.classes.media import MediaDecoder
from pyskyqremote.const import APP_EPG, SKY_STATE_OFF, SKY_STATE_STANDBY
from pyskyqremote.skyq_remote import SkyQRemote

# from pyskyqremote.device import DeviceDecoder
# from pyskyqremote.channel import ChannelDecoder
# from pyskyqremote.programme import ProgrammeDecoder, RecordedProgrammeDecoder


# Run ./bash_sky.py <sky_box_ip>
# example: ./bash_sky_test.py 192.168.0.9
# Note: you may need to modify top line change python3 to python, depending on OS/setup. this is works for me on my mac
country = None
queryDate = datetime.utcnow()
if len(sys.argv) > 2 and sys.argv[2] != "None":
    country = sys.argv[2]
test_channel = sys.argv[3] if len(sys.argv) > 3 else None
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
appJSON = sky.getActiveApplication().as_json()
print(appJSON)
app = json.loads(appJSON)["attributes"]["appId"]
if app != APP_EPG:
    exit()

print("----------- Current Media")
currentMedia = sky.getCurrentMedia().as_json()
print(currentMedia)

media = MediaDecoder(currentMedia)
if not media.live:
    print("----------- Recording")
    print(sky.getRecording(media.pvrId).as_json())

sid = test_channel or media.sid
if sid:
    print(f"----------- Programme from Epg - {queryDate} - {sid}")
    print(sky.getProgrammeFromEpg(sid, queryDate, queryDate).as_json())

    print(f"----------- Current Live TV - {sid}")
    print(sky.getCurrentLiveTVProgramme(sid).as_json())

print("----------- Get Channel Info - 101")
print(sky.getChannelInfo("101").as_json())

print("----------- Channel list")
print(sky.getChannelList().as_json())

print("----------- Favourites")
print(sky.getFavouriteList().as_json())

print("----------- Today's EPG")
epgJSON = sky.getEpgData(sid, queryDate).as_json()
print(epgJSON)

print("----------- Get scheduled recordings")
print(sky.getRecordings("SCHEDULED").as_json())

print("----------- Get quota info")
print(sky.getQuota().as_json())

print("----------- Book recording")
epgProgrammes = ChannelEPGDecoder(epgJSON).programmes
eid = epgProgrammes[len(epgProgrammes) - 1].eid
print(eid)
print(sky.bookRecording(eid))
recordings = sky.getRecordings("SCHEDULED")
pvrid = None
for recording in recordings.programmes:
    if recording.eid == eid:
        pvrid = recording.pvrid
        break
print(pvrid)

print("----------- Book series recording")
print(sky.bookRecording(eid, series=True))


print("----------- Unlink series")
print(sky.seriesLink(pvrid, False))
print("----------- Link series")
print(sky.seriesLink(pvrid, True))
sky.seriesLink(pvrid, False)

print("----------- Recording keep")
print(sky.recordingKeep(pvrid, True))
print("----------- Recording unkeep")
print(sky.recordingKeep(pvrid, False))

print("----------- Recording lock")
print(sky.recordingLock(pvrid, True))
print("----------- Recording unlock")
print(sky.recordingLock(pvrid, False))

print("----------- Recording delete")
print(sky.recordingDelete(pvrid, True))
print("----------- Recording undelete")
print(sky.recordingDelete(pvrid, False))

print("----------- Recording true")
print(sky.recordingErase(pvrid))

# print("----------- Set last played position")
# print(sky.recordingSetLastPlayedPosition("P2901079b", 20))
