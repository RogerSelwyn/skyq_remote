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

Will return a dictionary object such as below:

```
{
   'channel':'Sky Comedy HD',
   'imageUrl':'https://d2n0069hmnqmmx.cloudfront.net/epgdata/1.0/newchanlogos/600/600/skychb1143.png',
   'title':None,
   'season':None,
   'episode':None,
   'sid':1143,
   'live':True
}
```

### Get EPG information

```
epg = self.client.getEpgData(sid, epgDate)
```

Will return a dictionary object with an array of events:

```
[
   {
      'progammeuuid':'57a11caf-1ebd-4c01-a40b-7fdfe5c5fad0',
      'starttime':datetime.datetime(2020,4,16,21,50),
      'endtime':datetime.datetime(2020,4,16,22,50),
      'title':'New: Tonight Show Starring. Jimmy Fallon',
      'season':7,
      'episode':119,
      'imageUrl':'https://images.metadata.sky.com/pd-image/57a11caf-1ebd-4c01-a40b-7fdfe5c5fad0/16-9'
   },
   {
      'progammeuuid':'d2d67048-673a-4ea8-8a32-3ad386e306d2',
      'starttime':datetime.datetime(2020,4,16,22,50),
      'endtime':datetime.datetime(2020,4,16,23,50),
      'title':'New: Late Late Show With...',
      'season':2020,
      'episode':89,
      'imageUrl':'https://images.metadata.sky.com/pd-image/d2d67048-673a-4ea8-8a32-3ad386e306d2/16-9'
   },
   {...}
]
```

### Get programme at a point in time on a day 

Note that at the end of a day, the programme may appear on the next day's schedule. 

```
programme = self.client.getProgrammeFromEpg(sid, epgDate, queryDate)
```

Will return a dictionary object such as below:

```
{
   'progammeuuid':'9fbdcefe-312c-4681-b996-00637e85313a',
   'starttime':datetime.datetime(2020,4,17,8,30),
   'endtime':datetime.datetime(2020,4,17,9,0),
   'title':'Parks And Recreation',
   'season':4,
   'episode':5,
   'imageUrl':'https://images.metadata.sky.com/pd-image/9fbdcefe-312c-4681-b996-00637e85313a/16-9'
}
```

### Get current live TV programme on a channel

```
currentTV = self.client.getCurrentLiveTVProgramme(sid)
```

Will return a dictionary object such as below:

```
{
   'title':'Parks And Recreation',
   'season':4,
   'episode':5,
   'imageUrl':'https://images.metadata.sky.com/pd-image/9fbdcefe-312c-4681-b996-00637e85313a/16-9'
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
