from json import JSONEncoder
from datetime import datetime


class Programme:
    def __init__(
        self, programmeuuid, starttime, endtime, title, season, episode, imageUrl
    ):
        self.progammeuuid = programmeuuid
        self.starttime = starttime
        self.endtime = endtime
        self.title = title
        self.season = season
        self.episode = episode
        self.imageUrl = imageUrl
