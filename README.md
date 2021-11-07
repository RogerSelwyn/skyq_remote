[![CodeFactor](https://www.codefactor.io/repository/github/rogerselwyn/skyq_remote/badge)](https://www.codefactor.io/repository/github/rogerselwyn/skyq_remote)

[![maintained](https://img.shields.io/maintenance/yes/2021.svg)](#)
[![maintainer](https://img.shields.io/badge/maintainer-%20%40RogerSelwyn-blue.svg)](https://github.com/RogerSelwyn)
[![Community Forum](https://img.shields.io/badge/community-forum-brightgreen.svg)](https://community.home-assistant.io/t/custom-component-skyq-media-player/140306)

# pyskyqremote
Python module for accessing SkyQ box and EPG, and sending commands

## Introduction

This library enables access to SkyQ devices, primarily focused on the UK, but should also work for Italy and Germany.

## Installing

To install:

```
pip install pyskyqremote
```

## Usage

### Base
```
from pyskyqremote.skyq_remote import SkyQRemote

self.client = SkyQRemote('192.168.1.99')
```
Optional parameters:
* epgCacheLen - Default = 20
* port - Default = 49160
* jsonPort - Default = 9006


### Get device information

```
device = self.client.getDeviceInformation()
```

Will return an object such as below for device informatiom:

```
{
   'ASVersion':'Q112.000.21.00-AS_asdev',
   'IPAddress':'192.168.1.22',
   'countryCode':'GBR',
   'epgCountryCode':'GBR',
   'hardwareModel':'ES240',
   'hardwareName':'Falcon',
   'manufacturer':'Sky',
   'modelNumber':'Q112.000.21.00L (53wk8j8)',
   'serialNumber':'0627086857 2',
   'versionNumber':'32B12D'
}
```

### Get device information (JSON)

```
device = self.client.getDeviceInformation().as_json()
```

Will return a JSON structure such as below for device information:

```
{
   "__type__":"__device__",
   "attributes":{
      "ASVersion":"Q112.000.21.00-AS_asdev",
      "IPAddress":"192.168.x.xx",
      "countryCode":"GBR",
      "epgCountryCode":"GBR",
      "hardwareModel":"ES240",
      "hardwareName":"Falcon",
      "manufacturer":"Sky",
      "modelNumber":"Q112.000.21.00L (53wk8j8)",
      "serialNumber":"##########",
      "versionNumber":"32B12D"
   }
}

```

### Decode device information (JSON)

```
from pyskyqremote.media import DeviceDecoder
device = DeviceDecoder(deviceJSON)
```

Will decode the JSON structure to a python object.


### Get power status

```
status = self.client.powerStatus()
```

Will return "POWERED OFF", "STANDBY or "ON"

### Get current state

```
status = self.client.getCurrentState()
```

Will return "OFF", "STANDBY", "PLAYING", "PAUSED PLAYBACK"

### Get the active application

```
app = self.client.getActiveApplication()
```

Will return an object such as below for the running application name:

```
{
   'appId':'com.bskyb.beehive',
   'title':'Beehive Bedlam'
}
```

### Get the active application (JSON)

```
app = self.client.getActiveApplication().as_json()
```

Will return a JSON structure such as below for the running application name:

```
{
   "__type__":"__app__",
   "attributes":{
      "appId":"com.bskyb.beehive",
      "title":"Beehive Bedlam"
   }
}
```

### Get current media

```
app = self.client.getCurrentMedia()
```

Will return an object such as below for live programme:

```
{
   'channel':'Sky Comedy HD',
   'channelno':'153',
   'imageUrl':'https://d2n0069hmnqmmx.cloudfront.net/epgdata/1.0/newchanlogos/600/600/skychb1143.png',
   'sid':1143,
   'pvrId':None,
   'live':True
}
```
or for recording

```
{
   'channel':None,
   'channelno':'None',
   'imageUrl':None,
   'sid':None,
   'pvrId':'P12345ABC'
   'live':False
}
```
### Get current media (JSON)

```
media = self.client.getCurrentMedia().as_json()
```

Will return a JSON structure such as below for live programme:

```
{
   "__type__":"__media__",
   "attributes":{
      "channel":"BBC One South",
      "channelno":"101",
      "imageUrl":"https://d2n0069hmnqmmx.cloudfront.net/epgdata/1.0/newchanlogos/600/600/skychb2153.png",
      "sid":2153,
      "pvrId":null,
      "live":true
   }
}

```
or for recording

```
{
   "__type__":"__media__",
   "attributes":{
      "channel":null,
      "channelno":null,
      "imageUrl":null,
      "sid":null,
      "pvrId":"P12345ABC",
      "live":false
   }
}
```

### Decode current media (JSON)

```
from pyskyqremote.media import MediaDecoder
media = MediaDecoder(mediaJSON)
```

Will decode the JSON structure to a python object.


### Get EPG information

```
epg = self.client.getEpgData(sid, epgDate, days)
```

Will return an object with an array of events including the specified number of days. Defaults to 2 days.

```
{
   'sid':2153,
   'channelno':'101',
   'channelname':'BBC One South',
   'channelImageUrl':'https://d2n0069hmnqmmx.cloudfront.net/epgdata/1.0/newchanlogos/600/600/skychb2153.png',
   'programmes':[
      {
         'progammeuuid':'57a11caf-1ebd-4c01-a40b-7fdfe5c5fad0',
         'starttime':datetime.datetime(2020,4,16,21,50),
         'endtime':datetime.datetime(2020,4,16,22,50),
         'title':'New: Tonight Show Starring. Jimmy Fallon',
         'season':7,
         'episode':119,
         'imageUrl':'https://images.metadata.sky.com/pd-image/57a11caf-1ebd-4c01-a40b-7fdfe5c5fad0/16-9',
         'channelname':'BBC One South',
         'status':'LIVE'
      },
      {
         'progammeuuid':'d2d67048-673a-4ea8-8a32-3ad386e306d2',
         'starttime':datetime.datetime(2020,4,16,22,50),
         'endtime':datetime.datetime(2020,4,16,23,50),
         'title':'New: Late Late Show With...',
         'season':2020,
         'episode':89,
         'imageUrl':'https://images.metadata.sky.com/pd-image/d2d67048-673a-4ea8-8a32-3ad386e306d2/16-9',
         'channelname':'BBC One South',
         'status':'LIVE'
      },
      {...}
   ]
}
```
### Get EPG information (JSON)

```
epg = self.client.getEpgData(sid, epgDate, days).as_json()
```

Will return a JSON structure with an array of events including the specified number of days. Defaults to 2 days.

```
{
   "__type__":"__channel__",
   "attributes":{
      "sid":2153,
      "channelno":"101",
      "channelname":"BBC One South",
      "channelImageUrl":"https://d2n0069hmnqmmx.cloudfront.net/epgdata/1.0/newchanlogos/600/600/skychb2153.png"
   },
   "programmes":[
      {
         "__type__":"__programme__",
         "attributes":{
            "programmeuuid":"62ad0457-1a6a-4b45-9ef7-6e144639d734",
            "starttime":"2020-04-27T21:45:00Z",
            "endtime":"2020-04-27T22:10:00Z",
            "title":"Man Like Mobeen",
            "season":3,
            "episode":5,
            "imageUrl":"https://images.metadata.sky.com/pd-image/62ad0457-1a6a-4b45-9ef7-6e144639d734/16-9",
            "channelname":"BBC One South",
            "status":"LIVE"
        }
      },
      {
         "__type__":"__programme__",
         "attributes":{
            "programmeuuid":"a975bdeb-c19b-4de2-9557-c6d2757bdae7",
            "starttime":"2020-04-27T22:10:00Z",
            "endtime":"2020-04-27T22:50:00Z",
            "title":"Have I Got A Bit More News For You",
            "season":59,
            "episode":4,
            "imageUrl":"https://images.metadata.sky.com/pd-image/a975bdeb-c19b-4de2-9557-c6d2757bdae7/16-9",
            "channelname":"BBC One South"
            "status":"LIVE"
         }
      },
      {...},
   ]
}
```

### Decode EPG information (JSON)

```
from pyskyqremote.channel import ChannelDecoder
channel = ChannelDecoder(channelJSON)
```

Will decode the JSON structure to a python object.

### Get programme at a point in time on a day

Note that at the end of a day, the programme may appear on the next day's schedule.

```
programme = self.client.getProgrammeFromEpg(sid, epgDate, queryDate)
```

Will return an object such as below:

```
{
   'progammeuuid':'9fbdcefe-312c-4681-b996-00637e85313a',
   'starttime':datetime.datetime(2020,4,17,8,30),
   'endtime':datetime.datetime(2020,4,17,9,0),
   'title':'Parks And Recreation',
   'season':4,
   'episode':5,
   'imageUrl':'https://images.metadata.sky.com/pd-image/9fbdcefe-312c-4681-b996-00637e85313a/16-9',
   'channelname':'Channel 5 HD',
   'status':'LIVE'
}
```
### Get programme at a point in time on a day (JSON)

Note that at the end of a day, the programme may appear on the next day's schedule.

```
programme = self.client.getProgrammeFromEpg(sid, epgDate, queryDate).as_json()
```

Will return a JSON structure such as below:

```
{
   "__type__":"__programme__",
   "attributes":{
      "programmeuuid":"e11d9e93-0eec-4855-88f5-6ade9946d5dd",
      "starttime":"2020-04-28T21:00:00Z",
      "endtime":"2020-04-28T21:30:00Z",
      "title":"BBC News at Ten",
      "season":null,
      "episode":null,
      "imageUrl":"https://images.metadata.sky.com/pd-image/e11d9e93-0eec-4855-88f5-6ade9946d5dd/16-9",
      "channelname":"BBC ONE HD",
      "status":"LIVE"
   }
}
```
### Decode programme information (JSON)

```
from pyskyqremote.programme import ProgrammeDecoder
programme = ProgrammeDecoder(programmeJSON)
```

### Get current live TV programme on a channel

```
currentTV = self.client.getCurrentLiveTVProgramme(sid)
```

Will return an object such as below:

```
{
   'progammeuuid':'9fbdcefe-312c-4681-b996-00637e85313a',
   'starttime':datetime.datetime(2020,4,17,8,30),
   'endtime':datetime.datetime(2020,4,17,9,0),
   'title':'Parks And Recreation',
   'season':4,
   'episode':5,
   'imageUrl':'https://images.metadata.sky.com/pd-image/9fbdcefe-312c-4681-b996-00637e85313a/16-9',
   'channelname':'Channel 5 HD',
   'status':'LIVE'
}
```
### Get current live TV programme on a channel (JSON)

```
currentTV = self.client.getCurrentLiveTVProgramme(sid).as_json()
```

Will return a JSON structure such as below:

```
{
   "__type__":"__programme__",
   "attributes":{
      "programmeuuid":"e11d9e93-0eec-4855-88f5-6ade9946d5dd",
      "starttime":"2020-04-28T21:00:00Z",
      "endtime":"2020-04-28T21:30:00Z",
      "title":"BBC News at Ten",
      "season":null,
      "episode":null,
      "imageUrl":"https://images.metadata.sky.com/pd-image/e11d9e93-0eec-4855-88f5-6ade9946d5dd/16-9",
      "channelname":"BBC ONE HD",
      "status":"LIVE"
  }
}
```

### Get recordings

```
recordings = self.client.getRecordings(status)
```

Will return an object such as below for recordings with the provided status (default returns all):

```
{
   'programmes':[
      {
        'programmeuuid':'54bfc205-c56e-4583-b03f-59c31f97f8c7',
        'starttime':'2020-08-02T19:58:00Z',
        'endtime':'2020-08-02T21:01:59Z',
        'title':'New: Batwoman',
        'season':1,
        'episode':19,
        'imageUrl':'https://images.metadata.sky.com/pd-image/54bfc205-c56e-4583-b03f-59c31f97f8c7/16-9',
        'channelname':'E4 HD',
        'status':'RECORDED'
      },
      {
        'programmeuuid':'af9ecd2c-5026-4050-9c15-37598fe26713',
        'starttime':null,
        'endtime':'null,
        'title':'Home and Away',
        'season':35,
        'episode':4,
        'imageUrl':'https://images.metadata.sky.com/pd-image/af9ecd2c-5026-4050-9c15-37598fe26713/16-9',
        'channelname':'Channel 5 HD',
        'status':'SCHEDULED'
      },
      {…}
      }
   ]
}
```

### Get recordings (JSON)

```
recordings = self.client.getRecordings(status).as_json()
```

Will return an object such as below for recordings with the provided status (default returns all):

```
{
   "__type__":"__recordings__",
   "attributes":{

   },
   "programmes":[
      {
         "__type__":"__programme__",
         "attributes":{
            "programmeuuid":"54bfc205-c56e-4583-b03f-59c31f97f8c7",
            "starttime":"2020-08-02T19:58:00Z",
            "endtime":"2020-08-02T21:01:59Z",
            "title":"New: Batwoman",
            "season":1,
            "episode":19,
            "imageUrl":"https://images.metadata.sky.com/pd-image/54bfc205-c56e-4583-b03f-59c31f97f8c7/16-9",
            "channelname":"E4 HD",
            "status":"RECORDED"
        }
      },
      {
         "__type__":"__programme__",
         "attributes":{
            "programmeuuid":"af9ecd2c-5026-4050-9c15-37598fe26713",
            "starttime":"null",
            "endtime":"null",
            "title":"Home and Away",
            "season":35,
            "episode":4,
            "imageUrl":"https://images.metadata.sky.com/pd-image/af9ecd2c-5026-4050-9c15-37598fe26713/16-9",
            "channelname":"Channel 5 HD",
            "status":"SCHEDULED"
     },
      {...}
      }
   ]
}
```

### Get recording

```
recording = self.client.getRecording(pvrId)
```

Will return an object such as below:

```
{
   'progammeuuid':'9fbdcefe-312c-4681-b996-00637e85313a',
   'starttime':datetime.datetime(2020,4,17,8,30),
   'endtime':datetime.datetime(2020,4,17,9,0),
   'channelname':'ITV HD',
   'title':'Van Der Valk',
   'season':4,
   'episode':5,
   'imageUrl':'https://images.metadata.sky.com/pd-image/ddcd727f-487f-4558-8365-7bed4fe41c87/16-9',
   'status':'RECORDED'
}
```
### Get recording (JSON)

```
recording = self.client.getRecording(pvrId).as_json()
```

Will return an object such as below:

```
{
   "__type__":"__recording__",
   "attributes":{
      "programmeuuid":"e11d9e93-0eec-4855-88f5-6ade9946d5dd",
      "starttime":"2020-04-28T21:00:00Z",
      "endtime":"2020-04-28T21:30:00Z",
      "channelname":"ITV HD",
      "title":"BBC News at Ten",
      "season":null,
      "episode":null,
      "imageUrl":"https://images.metadata.sky.com/pd-image/e11d9e93-0eec-4855-88f5-6ade9946d5dd/16-9",
      "status":"RECORDED"
   }
}
```
### Decode recording information (JSON)

```
from pyskyqremote.programme import RecordedProgrammeDecoder
recording = RecordedProgrammeDecoder(recordingJSON)
```

### Get Channel List

```
channelList = self.client.getChannelList()
```

Will return an object with an array of channels.

```
{
   'channels':[
      {
         'channelno':'101',
         'channelname':'BBC ONE',
         'channelsid'='2153',
         'channelimageurl'='https://d2n0069hmnqmmx.cloudfront.net/epgdata/1.0/newchanlogos/600/600/skychb2153.png',
         'channeltype':'video',
         'channelnoint':101,
         'sf':'sd'
      },
      {
         'channelno':'0102',
         'channelname':'BBC R2',
         'channelsid'='2153',
         'channelimageurl'='https://d2n0069hmnqmmx.cloudfront.net/epgdata/1.0/newchanlogos/600/600/skychb2153.png',
         'channeltype':'audio',
         'channelnoint':102,
         'sf':'au'
      },
      {...}
   ]
}
```
### Get Channel List (JSON)

```
channelList = self.client.getChannelList().as_json()
```

Will return a JSON structure with an array of channels.

```
{
   "__type__":"__channellist__",
   "attributes":{
   },
   "channels":[
      {
         "__type__":"__channel__",
         "attributes":{
            "channelno":"101",
            "channelname":"BBC ONE",
            "channelsid":"2153",
            "channelimageurl":"https://d2n0069hmnqmmx.cloudfront.net/epgdata/1.0/newchanlogos/600/600/skychb2153.png",
            "channeltype":"video",
            "channelnoint":101,
            "sf":"sd"
         }
      },
      {
         "__type__":"__channel__",
         "attributes":{
            "channelno":"0102",
            "channelname":"BBC R2",
            "channelsid":"2153",
            "channelimageurl":"https://d2n0069hmnqmmx.cloudfront.net/epgdata/1.0/newchanlogos/600/600/skychb2153.png",
            "channeltype":"audio",
            "channelnoint":102,
            "sf":"au"
         }
      },
      {...},
   ]
}
```

### Get Channel Information (for a specific channel number)

```
channelInfo = self.client.getChannelInfo(channelNo)
```

Will return an object such as below:

```
{
   'channelno'='101',
   'channelname'='BBC One South',
   'channelsid'='2153',
   'channelimageurl'='https://d2n0069hmnqmmx.cloudfront.net/epgdata/1.0/newchanlogos/600/600/skychb2153.png',
   'channeltype'='video',
   'channelnoint'=101,
   'sf'='sd'
}
```
### Get Channel Information (for a specific channel number) (JSON)

```
channelInfo = self.client.getChannelInfo(channelNo).as_json()
```

Will return an object such as below:

```
{
   "__type__":"__channel__",
   "attributes":{
      "channelno":"101",
      "channelname":"BBC One South",
      "channelsid":"2153",
      "channelimageurl":"https://d2n0069hmnqmmx.cloudfront.net/epgdata/1.0/newchanlogos/600/600/skychb2153.png",
      "channeltype":"video",
      "channelnoint":101,
      "sf":"sd"
   }
}
```

### Get Favourite List

```
favouriteList = self.client.getFavouriteList()
```

Will return an object with an array of favourites.

```
{
   'favourites':[
      {
         'lcn': 1,
         'channelno':'101',
         'channelname':'BBC ONE',
         'sid'='2153'
      },
      {
         'lcn': 2,
         'channelno':'0102',
         'channelname':'BBC R2',
         'sid'='2153'
      },
      {...}
   ]
}
```
### Get Favorite List (JSON)

```
favouriteList = self.client.getFavouriteList().as_json()
```

Will return a JSON structure with an array of channels.

```
{
   "__type__":"__favouritelist__",
   "attributes":{
   },
   "favourites":[
      {
         "__type__":"__favourite__",
         "attributes":{
            "lcn": 1,
            "channelno":"101",
            "channelname":"BBC ONE",
            "sid":"2153"
         }
      },
      {
         "__type__":"__favourite__",
         "attributes":{
            "lcn": 2,
            "channelno":"0102",
            "channelname":"BBC R2",
            "sid":"2153"
         }
      },
      {...},
   ]
}
```

### Decode EPG information (JSON)

```
from pyskyqremote.channel import ChannelDecoder
channel = ChannelDecoder(channelJSON)
```

Will decode the JSON structure to a python object.

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
