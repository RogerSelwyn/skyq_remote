"""Structure of a standard EPG prorgramme."""


class Programme:
    """SkyQ Programme Class."""

    def __init__(
        self, programmeuuid, starttime, endtime, title, season, episode, imageUrl
    ):
        """Programme structure for SkyQ."""
        self.progammeuuid = programmeuuid
        self.starttime = starttime
        self.endtime = endtime
        self.title = title
        self.season = season
        self.episode = episode
        self.imageUrl = imageUrl
