[![CodeFactor](https://www.codefactor.io/repository/github/rogerselwyn/skyq_remote/badge)](https://www.codefactor.io/repository/github/rogerselwyn/skyq_remote)

![GitHub release](https://img.shields.io/github/v/release/RogerSelwyn/skyq_remote) [![maintained](https://img.shields.io/maintenance/yes/2022.svg)](#)
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
* epg_cache_len - Default = 20
* port - Default = 49160
* json_port - Default = 9006


### Get device information

```
device = self.client.get_device_information()
```

Will return an object such as below for device informatiom:

```
{
   'ASVersion':'Q112.000.21.00-AS_asdev',
   'IPAddress':'192.168.1.22',
   'countryCode':'GBR',
   'usedCountryCode':'GBR',
   'hardwareModel':'ES240',
   'hardwareName':'Falcon',
   'deviceType': 'GATEWAYSTB',
   'gateway': true,
   'gatewayIPAddress': '192.168.1.20',
   'manufacturer':'Sky',
   'modelNumber':'Q112.000.21.00L (53wk8j8)',
   'serialNumber':'0627086857 2',
   'versionNumber':'32B12D',
   'bouquet': 4101,
   'subbouquet': 9,
   'wakeReason': 'ECO',
   'systemUptime': 28346,
   'hdrCapable': true,
   'uhdCapable': true,
   'presentLocalTimeOffset': 3600,
   'utc': 1660486276,
   'futureLocalTimeOffset': 0,
   'futureTransitionUtc': 1667091599
}
```

### Get device information (JSON)

```
device = self.client.get_device_information().as_json()
```

Will return a JSON structure such as below for device information:

```
{
   "__type__":"__device__",
   "attributes":{
      "ASVersion":"Q112.000.21.00-AS_asdev",
      "IPAddress":"192.168.x.xx",
      "countryCode":"GBR",
      "usedCountryCode":"GBR",
      "hardwareModel":"ES240",
      "hardwareName":"Falcon",
      "deviceType": "GATEWAYSTB",
      "gateway": true,
      "gatewayIPAddress": "192.168.1.20",
      "manufacturer":"Sky",
      "modelNumber":"Q112.000.21.00L (53wk8j8)",
      "serialNumber":"##########",
      "versionNumber":"32B12D",
      "bouquet": 4101,
      "subbouquet": 9,
      "wakeReason": "ECO",
      "systemUptime": 28346,
      "hdrCapable": true,
      "uhdCapable": true,
      "presentLocalTimeOffset": 3600,
      "utc": 1660486276,
      "futureLocalTimeOffset": 0,
      "futureTransitionUtc": 1667091599
   }
}

```

### Decode device information (JSON)

```
from pyskyqremote.media import device_decoder
device = device_decoder(device_json)
```

Will decode the JSON structure to a python object.


### Get power status

```
status = self.client.power_status()
```

Will return "POWERED OFF", "STANDBY or "ON"

### Get current state

```
status = self.client.get_current_state()
```

Will return an object such as below with current transport status information (`state` is the same as the previously returned single attribute):
```
{
    'CurrentTransportState':'PLAYING',
    'CurrentTransportStatus':'OK',
    'CurrentSpeed':'1',
    'state':'PLAYING'
}
```

### Get current state (JSON)

```
status = self.client.get_current_state().as_json()
```

Will return an object such as below with current transport status information (`state` is the same as the previously returned single attribute):
```
{
   "__type__":"__transportinfo__",
   "attributes":{
      "CurrentTransportState":"PLAYING",
      "CurrentTransportStatus":"OK",
      "CurrentSpeed":"1",
      "state":"PLAYING"
}
```

### Get the active application

```
app = self.client.get_active_application()
```

Will return an object such as below for the running application name:

```
{
   'appid':'com.bskyb.beehive',
   'title':'Beehive Bedlam'
}
```

### Get the active application (JSON)

```
app = self.client.get_active_application().as_json()
```

Will return a JSON structure such as below for the running application name:

```
{
   "__type__":"__app__",
   "attributes":{
      "appid":"com.bskyb.beehive",
      "title":"Beehive Bedlam"
   }
}
```

### Get current media

```
app = self.client.get_current_media()
```

Will return an object such as below for live programme:

```
{
   'channel':'Sky Comedy HD',
   'channelno':'153',
   'image_url':'https://d2n0069hmnqmmx.cloudfront.net/epgdata/1.0/newchanlogos/600/600/skychb1143.png',
   'sid':1143,
   'pvrid':None,
   'live':True
}
```
or for recording

```
{
   'channel':None,
   'channelno':'None',
   'image_url':None,
   'sid':None,
   'pvrid':'P12345ABC'
   'live':False
}
```
### Get current media (JSON)

```
media = self.client.get_current_media().as_json()
```

Will return a JSON structure such as below for live programme:

```
{
   "__type__":"__media__",
   "attributes":{
      "channel":"BBC One South",
      "channelno":"101",
      "image_url":"https://d2n0069hmnqmmx.cloudfront.net/epgdata/1.0/newchanlogos/600/600/skychb2153.png",
      "sid":2153,
      "pvrid":null,
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
      "image_url":null,
      "sid":null,
      "pvrid":"P12345ABC",
      "live":false
   }
}
```

### Decode current media (JSON)

```
from pyskyqremote.media import media_decoder
media = media_decoder(media_json)
```

Will decode the JSON structure to a python object.


### Get EPG information

```
epg = self.client.get_epg_data(sid, epgDate, days)
```

Will return an object with an array of events including the specified number of days. Defaults to 2 days.

```
{
   'sid':2153,
   'channelno':'101',
   'channelname':'BBC One South',
   'channelimage_url':'https://d2n0069hmnqmmx.cloudfront.net/epgdata/1.0/newchanlogos/600/600/skychb2153.png',
   'programmes':[
      {
         'progammeuuid':'57a11caf-1ebd-4c01-a40b-7fdfe5c5fad0',
         'starttime':datetime.datetime(2020,4,16,21,50),
         'endtime':datetime.datetime(2020,4,16,22,50),
         'title':'New: Tonight Show Starring. Jimmy Fallon',
         'season':7,
         'episode':119,
         'image_url':'https://images.metadata.sky.com/pd-image/57a11caf-1ebd-4c01-a40b-7fdfe5c5fad0/16-9',
         'channelname':'BBC One South',
         'status':'LIVE',
         'eid':'E4b8-19b'
      },
      {
         'progammeuuid':'d2d67048-673a-4ea8-8a32-3ad386e306d2',
         'starttime':datetime.datetime(2020,4,16,22,50),
         'endtime':datetime.datetime(2020,4,16,23,50),
         'title':'New: Late Late Show With...',
         'season':2020,
         'episode':89,
         'image_url':'https://images.metadata.sky.com/pd-image/d2d67048-673a-4ea8-8a32-3ad386e306d2/16-9',
         'channelname':'BBC One South',
         'status':'LIVE',
         'eid':'E4b8-19b'
      },
      {...}
   ]
}
```
### Get EPG information (JSON)

```
epg = self.client.get_epg_data(sid, epgDate, days).as_json()
```

Will return a JSON structure with an array of events including the specified number of days. Defaults to 2 days.

```
{
   "__type__":"__channel__",
   "attributes":{
      "sid":2153,
      "channelno":"101",
      "channelname":"BBC One South",
      "channelimage_url":"https://d2n0069hmnqmmx.cloudfront.net/epgdata/1.0/newchanlogos/600/600/skychb2153.png"
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
            "image_url":"https://images.metadata.sky.com/pd-image/62ad0457-1a6a-4b45-9ef7-6e144639d734/16-9",
            "channelname":"BBC One South",
            "status":"LIVE",
            "eid":"E4b8-19b"
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
            "image_url":"https://images.metadata.sky.com/pd-image/a975bdeb-c19b-4de2-9557-c6d2757bdae7/16-9",
            "channelname":"BBC One South"
            "status":"LIVE",
            "eid":"E4b8-19b"
         }
      },
      {...},
   ]
}
```

### Decode EPG information (JSON)

```
from pyskyqremote.channel import channel_decoder
channel = channel_decoder(channel_json)
```

Will decode the JSON structure to a python object.

### Get programme at a point in time on a day

Note that at the end of a day, the programme may appear on the next day's schedule.

```
programme = self.client.get_programme_from_epg(sid, epgDate, queryDate)
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
   'image_url':'https://images.metadata.sky.com/pd-image/9fbdcefe-312c-4681-b996-00637e85313a/16-9',
   'channelname':'Channel 5 HD',
   'status':'LIVE',
   'eid':'E4b8-19b'
}
```
### Get programme at a point in time on a day (JSON)

Note that at the end of a day, the programme may appear on the next day's schedule.

```
programme = self.client.get_programme_from_epg(sid, epgDate, queryDate).as_json()
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
      "image_url":"https://images.metadata.sky.com/pd-image/e11d9e93-0eec-4855-88f5-6ade9946d5dd/16-9",
      "channelname":"BBC ONE HD",
      "status":"LIVE",
      "eid':"E4b8-19b"
   }
}
```
### Decode programme information (JSON)

```
from pyskyqremote.programme import programme_decoder
programme = programme_decoder(programmeJSON)
```

### Get current live TV programme on a channel

```
currentTV = self.client.get_current_live_tv_programme(sid)
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
   'image_url':'https://images.metadata.sky.com/pd-image/9fbdcefe-312c-4681-b996-00637e85313a/16-9',
   'channelname':'Channel 5 HD',
   'status':'LIVE',
   'eid':'E4b8-19b'
}
```
### Get current live TV programme on a channel (JSON)

```
currentTV = self.client.get_current_live_tv_programme(sid).as_json()
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
      "image_url":"https://images.metadata.sky.com/pd-image/e11d9e93-0eec-4855-88f5-6ade9946d5dd/16-9",
      "channelname":"BBC ONE HD",
      "status":"LIVE",
      "eid":"E4b8-19b"
  }
}
```

### Get recordings

```
recordings = self.client.get_recordings(<status="all">, <limit=1000>, <offset=0>)
```

Will return an object such as below for the number of recordings specified by limit with the specified offset and with the provided status:

```
{
   'programmes':[
      {
        'programmeuuid':'54bfc205-c56e-4583-b03f-59c31f97f8c7',
        'starttime':'2020-08-02T19:58:00Z',
        'endtime':'2020-08-02T21:01:59Z',
        'title':'New: Batwoman',
        'summary': 'Lorum ipsum...',
        'season':1,
        'episode':19,
        'image_url':'https://images.metadata.sky.com/pd-image/54bfc205-c56e-4583-b03f-59c31f97f8c7/16-9',
        'channelname':'E4 HD',
        'status':'RECORDED',
        'deletetime': '2020-09-02T20:00:59Z',
        'failurereason': None,
        'source': 'LIVE',
        'pvrid':'P29014192',
        'eid':'E869-67b1',
      },
      {
        'programmeuuid':'af9ecd2c-5026-4050-9c15-37598fe26713',
        'starttime':null,
        'endtime':'null,
        'title':'Home and Away',
        'summary': 'Lorum ipsum...',
        'season':35,
        'episode':4,
        'image_url':'https://images.metadata.sky.com/pd-image/af9ecd2c-5026-4050-9c15-37598fe26713/16-9',
        'channelname':'Channel 5 HD',
        'status':'SCHEDULED',
        'deletetime': None,
        'failurereason': None,
        'source': 'LIVE',
        'pvrid':'P29014192',
        'eid':'E869-67b1'
      },
      {
        'programmeuuid':'575736fd-0719-4249-88cc-babd6e232bfa',
        'starttime':'2020-08-02T19:58:00Z',
        'endtime':'2020-08-02T21:01:59Z',
        'title':'Lorraine',
        'summary': 'Lorum ipsum...',
        'season':35,
        'episode':4,
        'image_url':'https://images.metadata.sky.com/pd-image/575736fd-0719-4249-88cc-babd6e232bfa/16-9',
        'channelname':'ITV HD',
        'status':'PART REC',
        'deletetime': None,
        'failurereason': 'Start Missed',
        'source': 'VOD',
        'pvrid':'P29014192',
        'eid':'E869-67b1'
      },
      {…}
      }
   ]
}
```

### Get recordings (JSON)

```
recordings = self.client.get_recordings(<status="all">, <limit=1000>, <offset=0>).as_json()
```

Will return an object such as below for the number of recordings specified by limit with the specified offset and with the provided status:

```
{
   "__type__":"__recordings__",
   "attributes":{

   },
   "recordings":[
      {
         "__type__":"__recording__",
         "attributes":{
            "programmeuuid":"54bfc205-c56e-4583-b03f-59c31f97f8c7",
            "starttime":"2020-08-02T19:58:00Z",
            "endtime":"2020-08-02T21:01:59Z",
            "title":"New: Batwoman",
            "summary":"Lorum ipsum...",
            "season":1,
            "episode":19,
            "image_url":"https://images.metadata.sky.com/pd-image/54bfc205-c56e-4583-b03f-59c31f97f8c7/16-9",
            "channelname":"E4 HD",
            "status":"RECORDED",
            "deletetime":"2020-09-02T20:00:59Z",
            "failurereason":"null",
            "source":"LIVE",
            "pvrid":"P29014192",
            "eid":"E869-67b1"
        }
      },
      {
         "__type__":"__recording__",
         "attributes":{
            "programmeuuid":"af9ecd2c-5026-4050-9c15-37598fe26713",
            "starttime":"null",
            "endtime":"null",
            "title":"Home and Away",
            "summary":"Lorum ipsum...",
            "season":35,
            "episode":4,
            "image_url":"https://images.metadata.sky.com/pd-image/af9ecd2c-5026-4050-9c15-37598fe26713/16-9",
            "channelname":"Channel 5 HD",
            "status":"SCHEDULED",
            "deletetime":"null",
            "failurereason":"null",
            "source":"LIVE",
            "pvrid":"P29014192",
            "eid":"E869-67b1"
     },
     {
        "__type__":"__recording__",
        "attributes":{
           "programmeuuid":"af9ecd2c-5026-4050-9c15-37598fe26713",
           "starttime":"2020-08-02T19:58:00Z",
           "endtime":"2020-08-02T21:01:59Z",
           "title":"Home and Away",
           "summary":"Lorum ipsum...",
           "season":35,
           "episode":4,
           "image_url":"https://images.metadata.sky.com/pd-image/af9ecd2c-5026-4050-9c15-37598fe26713/16-9",
           "channelname":"Channel 5 HD",
           "status":"PART REC",
           "deletetime":"null",
           "failurereason":"Start Missed",
           "source":"VOD",
           "pvrid":"P29014192",
           "eid":"E869-67b1"
    },
      {...}
      }
   ]
}
```

### Get recording

```
recording = self.client.getRecording(pvrid)
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
   'image_url':'https://images.metadata.sky.com/pd-image/ddcd727f-487f-4558-8365-7bed4fe41c87/16-9',
   'status':'RECORDED',
   'deletetime': None,
   'failurereason': None,
   'pvrid':'P29014192',
   'eid':'E869-67b1'
}
```
### Get recording (JSON)

```
recording = self.client.getRecording(pvrid).as_json()
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
      "image_url":"https://images.metadata.sky.com/pd-image/e11d9e93-0eec-4855-88f5-6ade9946d5dd/16-9",
      "status":"RECORDED",
      "deletetime": null,
      "failurereason": null,
      "pvrid":"P29014192",
      "eid":"E869-67b1"
   }
}
```
### Decode recording information (JSON)

```
from pyskyqremote.programme import recorded_programme_decoder
recording = recorded_programme_decoder(recording_json)
```

### Get quota

```
quota = self.client.get_quota()
```

Will return an object such as below:

```
{
   'quotamax':1604285,
   'quotaused':171083
}
```
### Get quota (JSON)

```
recording = self.client.get_quota().as_json()
```

Will return an object such as below:

```
{
   "__type__":"__quota__",
   "attributes":{
     "quotaMax":1604285,
     "quotaUsed":171083
   }
}
```

### Book Recording

```
response = self.client.book_recording(eid, <series=False>)
```


Will return True for success or False for failure. Set series to True for series link or False for no series link.

### Book PPV Recording

```
response = self.client.book_ppv_recording(eid, offerref)
```


Will return True for success or False for failure.

### Series Link Recording

```
response = self.client.series_link(pvrid, <linkon=True>)
```

Will return True for success or False for failure. Set on to True for linking, False for unlinking.

### Keep Recording

```
response = self.client.recording_keep(pvrid, <keepon=True>)
```

Will return True for success or False for failure. Set on to True to keep, False to unkeep.

### Lock Recording

```
response = self.client.recording_lock(pvrid, <lockon=True>)
```

Will return True for success or False for failure. Set on to True to lock, False to unlock.

### Delete Recording (or scheduled recording)

```
response = self.client.recording_delete(pvrid, <deleteon=True>)
```

Will return True for success or False for failure. Set on to True to delete, False to undelete. Cannot undelete scheduled recording.

### Erase Recording

```
response = self.client.recording_erase(pvrid)
```

Will return True for success or False for failure.

### Erase all Recordings including scheduled recordings

```
response = self.client.recording_erase_all()
```

Will return True for success or False for failure.

### Set Last Played Position

```
response = self.client.recording_set_last_played_position(pvrid, pos)
```

Will return True for success or False for failure. Only works on the main Sky Q box.

### Get Channel List

```
channelList = self.client.get_channel_list()
```

Will return an object with an array of channels.

```
{
   'channels':[
      {
         'channelno':'101',
         'channelname':'BBC ONE',
         'channelsid'='2153',
         'channelimage_url'='https://d2n0069hmnqmmx.cloudfront.net/epgdata/1.0/newchanlogos/600/600/skychb2153.png',
         'channeltype':'video',
         'channelnoint':101,
         'sf':'sd'
      },
      {
         'channelno':'0102',
         'channelname':'BBC R2',
         'channelsid'='2153',
         'channelimage_url'='https://d2n0069hmnqmmx.cloudfront.net/epgdata/1.0/newchanlogos/600/600/skychb2153.png',
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
channelList = self.client.get_channel_list().as_json()
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
            "channelimage_url":"https://d2n0069hmnqmmx.cloudfront.net/epgdata/1.0/newchanlogos/600/600/skychb2153.png",
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
            "channelimage_url":"https://d2n0069hmnqmmx.cloudfront.net/epgdata/1.0/newchanlogos/600/600/skychb2153.png",
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
channelInfo = self.client.get_channel_info(channel_no)
```

Will return an object such as below:

```
{
   'channelno'='101',
   'channelname'='BBC One South',
   'channelsid'='2153',
   'channelimage_url'='https://d2n0069hmnqmmx.cloudfront.net/epgdata/1.0/newchanlogos/600/600/skychb2153.png',
   'channeltype'='video',
   'channelnoint'=101,
   'sf'='sd'
}
```
### Get Channel Information (for a specific channel number) (JSON)

```
channelInfo = self.client.get_channel_info(channel_no).as_json()
```

Will return an object such as below:

```
{
   "__type__":"__channel__",
   "attributes":{
      "channelno":"101",
      "channelname":"BBC One South",
      "channelsid":"2153",
      "channelimage_url":"https://d2n0069hmnqmmx.cloudfront.net/epgdata/1.0/newchanlogos/600/600/skychb2153.png",
      "channeltype":"video",
      "channelnoint":101,
      "sf":"sd"
   }
}
```

### Get Favourite List

```
favouriteList = self.client.get_favourite_list()
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
favouriteList = self.client.get_favourite_list().as_json()
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
