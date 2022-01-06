"""Constants for pyskyqremote- GB."""
TERRITORY = "GB"

SCHEDULE_URL = "http://atlantis.epgsky.com/as/schedule/{1}/{0}"
LIVE_IMAGE_URL = (
    "https://imageservice.sky.com/pd-image/{0}/16-9/456?territory=" + TERRITORY + "&provider=SKY&proposition=SKYQ"
)
PVR_IMAGE_URL = LIVE_IMAGE_URL
CHANNEL_IMAGE_URL = (
    "https://imageservice.sky.com/logo/skychb_{0}{1}/600/600?territory=" + TERRITORY + "&provider=SKY&proposition=SKYQ"
)
