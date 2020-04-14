#!/usr/bin/env python
from pyskyqremote.skyq_remote import SkyQRemote
import requests
import sys


# Run ./bash_sky.py <sky_box_ip>
# example: ./bash_sky_test.py 192.168.0.9
# Note: you may need to modify top line change python3 to python, depending on OS/setup. this is works for me on my mac
country = "UK"
if len(sys.argv) == 3:
    country = sys.argv[2]

sky = SkyQRemote(sys.argv[1], country=country)

print("----------- Power status")
print(sky.powerStatus())
print("----------- Current Media")
currentMedia = sky.getCurrentMedia()
print(currentMedia)
if currentMedia["live"]:
    print("----------- Current Live TV")
    print(sky.getCurrentLiveTVProgramme(currentMedia["sid"], currentMedia["channelno"]))

print("----------- Active Application")
print(str(sky.getActiveApplication()))

# print("----------- Testing Description 0")
# print(sky._getSoapControlURL(0))
# print("----------- Testing Description 1")
# print(sky._getSoapControlURL(1))
# print("----------- Testing Description 2")
# print(sky._getSoapControlURL(2))

# print("----------- Transport Info")
# print(sky._callSkySOAPService('GetTransportInfo'))
