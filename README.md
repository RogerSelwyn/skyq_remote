[![CodeFactor](https://www.codefactor.io/repository/github/rogerselwyn/skyq_remote/badge)](https://www.codefactor.io/repository/github/rogerselwyn/skyq_remote)

[![maintained](https://img.shields.io/maintenance/yes/2020.svg)](#)
[![maintainer](https://img.shields.io/badge/maintainer-%20%40RogerSelwyn-blue.svg)](https://github.com/RogerSelwyn)
[![Community Forum](https://img.shields.io/badge/community-forum-brightgreen.svg)](https://community.home-assistant.io/t/custom-component-skyq-media-player/140306)

# pyskyqremote
Python module for accessing SkyQ box and EPG, and sending commands

## Introduction

This library enables access to SkyQ devices, primarily focused on the UK, but may be useable in other countries. However EPG information is not available unless provided from awk.epgsky.com.

## Installing

To install:

```
pip install pyskyqremote
```

## Usage

### Base
```
from pyskyqremote import SkyQRemote

self.client = SkyQRemote('192.168.1.99')
```

### Get power status

```
status = self.client.powerStatus()
```

Will return "Off", "On" or "Powered Off" 

### Get current state

```
status = self.client.getCurrentState()
```

Will return "OFF", "PLAYING", "PAUSED PLAYBACK"

### Get the active application

```
app = self.client.getActiveApplication()
```

Will return the running application name or 'com.bskyb.epgui'

### Get current media

```
app = self.client.getCurrentMedia()
```

Will return a JSON object such as below:

```
{
   'channel':'BBC One HD',
   'imageUrl':'https://d2n0069hmnqmmx.cloudfront.net/epgdata/1.0/newchanlogos/600/600/skychb2076.png',
   'title':None,
   'season':None,
   'episode':None,
   'sid':2076,
   'live':True
}
```

### Get EPG information

```
epg = self.client.getEpgData(sid, queryDate)
```

Will return a JSON object with an array of events:

```
{
   'sid':'2076',
   'events':[
      {
         'st':1586640300,
         'd':3000,
         'eid':'E81c-2be3',
         'cgid':5,
         'haschildren':False,
         't':'MOTD Top Ten Managers',
         'sy':'Gary ...',
         'eg':7,
         'esg':8,
         'tso':0,
         'r':'--',
         'at':'S',
         's':True,
         'ad':False,
         'hd':True,
         'new':False,
         'canl':True,
         'canb':True,
         'hasAlternativeAudio':False,
         'restartable':False,
         'slo':False,
         'w':True,
         'ippv':False,
         'oppv':False
      },
      {
         'st':1586643300,
         'd':3000,
         'eid':'E81c-2be5',
         'cgid':5,
         'programmeuuid':'dd524d18-995c-4957-9096-209e3ea4bb7c',
         'episodenumber':0,
         'seriesuuid':'d9432b96-d643-4d9d-859f-8f3f53e0b133',
         'haschildren':False,
         't':'Match of Their Day',
         'sy':'The pundits ...',
         'eg':7,
         'esg':8,
         'tso':0,
         'r':'--',
         'at':'S',
         's':True,
         'ad':False,
         'hd':True,
         'new':False,
         'canl':True,
         'canb':True,
         'hasAlternativeAudio':False,
         'restartable':False,
         'slo':False,
         'w':True,
         'ippv':False,
         'oppv':False
      },
      {...}
   ]
}
```

### Get programme at a point in time on a day

Note that the end of a day, the programme may appear on the next day's schedule. timeFromEpoch is teh number of seconds from the start of 1970.

```
programme = self.client.getProgrammeFromEpg(sid, querydate, timeFromEpoch)
```

Will return a JSON object such as below:

```
{
   'st':1586687400,
   'd':2400,
   'eid':'E81c-2baf',
   'cgid':5,
   'programmeuuid':'8dc6bcb7-b8be-4c4f-8844-ecc5bb84ebf4',
   'episodenumber':0,
   'seriesuuid':'5a6d57d0-901f-4508-bb6e-a217dc84dac1',
   'haschildren':False,
   't':'Sunday Worship',
   'sy':'The Very...',
   'eg':5,
   'esg':10,
   'tso':0,
   'r':'--',
   'at':'S',
   's':True,
   'ad':False,
   'hd':True,
   'new':False,
   'canl':True,
   'canb':True,
   'hasAlternativeAudio':False,
   'restartable':False,
   'slo':False,
   'w':True,
   'ippv':False,
   'oppv':False
}
```

### Get current live TV programme

```
currentTV = self.client.getCurrentLiveTVProgramme(sid)
```

Will return a JSON object such as below:

```
{
   'title':"Britain's Got Talent",
   'season':14,
   'episode':1,
   'imageUrl':'https://images.metadata.sky.com/pd-image/50d6b29f-35ac-49e3-b00d-9cf2718990c7/16-9/1788'
}
```

### Send key press

```
self.client.press(sequence)
```

Allows the sending of a sequence of key presses which are submitted at 1/2 second intervals

Valid values are:
```
power 
select 
backup 
dismiss 
channelup 
channeldown 
interactive 
sidebar 
help 
services 
search 
tvguide 
home 
i 
text 
up 
down 
left 
right 
red 
green 
yellow 
blue 
0 
1 
2 
3 
4
5 
6 
7 
8 
9,
play 
pause 
stop 
record 
fastforward 
rewind 
boxoffice 
sky 
```
