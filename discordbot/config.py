import os

from discord.ext import commands
from django.conf import settings

# Discordbot Configuration
# Helper function


def _s(name: str, default=None, prefix: str = "DISCORDBOT_"):
    return getattr(settings, prefix + name, os.getenv(prefix + name, default))


# Config


DEBUG = _s("DEBUG", False)

DEBUG_NO_RAISE_FOR = (
    commands.DisabledCommand,
    commands.CommandOnCooldown,
    commands.CommandNotFound,
    commands.UserInputError,
    commands.CheckFailure,
)

# Discordbot Config

ALLOW_BOTS = _s("ALLOW_BOTS", False)
ALLOW_WEBHOOKS = _s("ALLOW_WEBHOOKS", True)

ALL_PREFIXES = _s("ALL_PREFIXES", ["/", "!", "$", ".", "-", ">", "?"])
MAIN_PREFIXES = _s("MAIN_PREFIXES", ["/"])

EXTENSIONFOLDER = "discordbot.botcmds"
EXTENSIONS = _s(
    "EXTENSIONS",
    [
        "basic",
        "reports",
        "moderation",
        "games",
        "help",
        "channels",
        "userinfo",
        "music",
        "owneronly",
        "converters",
        "embedgenerator",
        "notifier",
        "networking",
    ],
)

# Basic

INVITE_OWNER = _s("INVITE_OWNER", "https://go.rafaelurben.ch/discord")
INVITE_BOT = _s("INVITE_BOT", "https://go.rafaelurben.ch/discordbot")

# Help

HELP_HIDDEN_COGS = [
    "owneronly",
    "notifier",
    "help",
    "networking",
    "userinfo",
    "converters",
]

# Music

MUSIC_MODULE = _s("MUSIC_MODULE", False)
if not MUSIC_MODULE and "music" in EXTENSIONS:
    EXTENSIONS.remove("music")

FILESPATH = _s(
    "FILESPATH",
    os.path.join(os.path.dirname(os.path.realpath(__file__)), "botfiles"),
)
MEMESPATH = _s("MEMESPATH", os.path.join(FILESPATH, "memes"))
FFMPEGPATH = _s("FFMPEGPATH", os.path.join(FILESPATH, "ffmpeg.exe"))

FFMPEG_OPTIONS = {
    "options": "-vn",
    "executable": FFMPEGPATH,
}

FFMPEG_OPTIONS_STREAM = {
    "options": "-vn",
    "before_options": " -reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
    "executable": FFMPEGPATH,
}

RADIOS = {
    "swisspop": "http://www.radioswisspop.ch/live/mp3.m3u",
    "nrjbern": "https://energybern.ice.infomaniak.ch/energybern-high.mp3",
    "rockit": "https://rockitradio.ice.infomaniak.ch/rockitradio-high.mp3",
    "vintage": "https://vintageradio.ice.infomaniak.ch/vintageradio-high.mp3",
}

# Moderation

RULES = {
    "1) Verhalten": [
        "Sei nett zu anderen Leuten und behandle sie so, wie auch du behandelt werden möchtest!",
        "Habe Respekt vor deinen Mitmenschen!",
        "Benutze anständige Sprache!",
    ],
    "2) Text": [
        "Bleib beim Thema! Für off-topic gibt es andere Plätze.",
        "Spamming ist verboten!",
        "Werbung ohne Erlaubnis eines Administrators ist verboten!",
    ],
    "3) Ton": [
        "Stimmverzerrer, Sprach- und Videoaufnahmen sind nur mit Einverständnis aller Teilnehmer gestattet.",
        "Mache wenn möglich keine unnötigen Hintergrundgeräusche!",
        "Channel Hopping bitte unterlassen!",
    ],
    "4) NSFW": [
        "Anstössige Inhalte ausserhalb NSFW-Kanälen werden sofort gelöscht und der Autor mit einem Bann/Mute "
        "bestraft!",
    ],
    "5) Sicherheit": [
        "Blockiere Anfragen nach persönlichen Daten und melde sie jemandem aus dem Serverteam!",
        "Melde schlimme oder wiederkehrende Fälle bitte auch Discord!",
        "Sende nie jemandem dein Passwort!",
    ],
    "6) Moderation": [
        "Anweisungen vom Serverteam sind zu befolgen!",
        "Das Serverteam kann dich bei falschem oder verdächtigem Verhalten ohne Vorwarnung bestrafen.",
        "Regelmissachtungen können mit dem `/report add` Befehl gemeldet werden.",
    ],
    "7) Weiteres": [
        "Discords Bedingungen gelten hier auch!",
        "Deine Handlungen haben Folgen - handle mit Verstand ;)",
    ],
}
