import os

# Discordbot Config

ALLOW_BOTS = False
ALLOW_WEBHOOKS = True

ALL_PREFIXES = ["/", "!", "$", ".", "-", ">", "?"]
MAIN_PREFIXES = ["/"]

EXTENSIONFOLDER = "discordbot.botcmds"
EXTENSIONS = ['basic','support','moderation','games','help','channels','music','owneronly','converters','embedgenerator','notifier']

# Help

HELP_HIDDEN_COGS = ["owneronly", "notifier"]

# Music

DEBUG = os.getenv("DEBUG", False)

FILESPATH = os.path.join(os.path.dirname(os.path.realpath(__file__)), "botfiles")
MEMESPATH = os.path.join(FILESPATH, "memes")

FFMPEG_OPTIONS = {
    'options': '-vn',
    'executable': os.path.join(FILESPATH, "ffmpeg.exe")
}

RADIOS = {
    "swisspop": "http://www.radioswisspop.ch/live/mp3.m3u",
    "nrjbern":  "https://energybern.ice.infomaniak.ch/energybern-high.mp3",
}
