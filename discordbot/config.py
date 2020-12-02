import os
from django.conf import settings

# Discordbot Configuration
## Helper function

def _s(name:str, default=None, prefix:str="DISCORDBOT_"):
    return getattr(settings, prefix+name, os.getenv(prefix+name, default))

## Config

DEBUG = _s("DEBUG", False)

DOMAIN = _s("DOMAIN", None)

## Discordbot Config

ALLOW_BOTS = _s("ALLOW_BOTS", False)
ALLOW_WEBHOOKS = _s("ALLOW_WEBHOOKS", True)

ALL_PREFIXES = _s("ALL_PREFIXES", ["/", "!", "$", ".", "-", ">", "?"])
MAIN_PREFIXES = _s("MAIN_PREFIXES", ["/"])

EXTENSIONFOLDER = "discordbot.botcmds"
EXTENSIONS = _s("EXTENSIONS", ['basic','support','moderation','games','help','channels','music','owneronly','converters','embedgenerator','notifier', 'polls', 'domains'])

## Basic

INVITE_OWNER = "https://rebrand.ly/RUdiscord"
INVITE_BOT = "https://rebrand.ly/RUdiscordbot"

SPAM_ALLOWED = False

## Help

HELP_HIDDEN_COGS = ["owneronly", "notifier"]

## Music

MUSIC_MODULE = _s("MUSIC_MODULE", False)

FILESPATH = _s("FILESPATH", os.path.join(os.path.dirname(os.path.realpath(__file__)), "botfiles"))
MEMESPATH = _s("MEMESPATH", os.path.join(FILESPATH, "memes"))
FFMPEGPATH = _s("FFMPEGPATH", os.path.join(FILESPATH, "ffmpeg.exe"))

FFMPEG_OPTIONS = {
    'options': '-vn',
    'executable': FFMPEGPATH,
}

FFMPEG_OPTIONS_STREAM = {
    'options': '-vn',
    'before_options': " -reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
    'executable': FFMPEGPATH,
}

RADIOS = {
    "swisspop": "http://www.radioswisspop.ch/live/mp3.m3u",
    "nrjbern":  "https://energybern.ice.infomaniak.ch/energybern-high.mp3",
}
