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

INVITE_OWNER = _s("INVITE_OWNER", "https://go.rafaelurben.ch/discord")
INVITE_BOT = _s("INVITE_BOT", "https://go.rafaelurben.ch/discordbot")

SPAM_ALLOWED = _s("SPAM_ALLOWED", False)

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

## Moderation

REGELN = {
    "1) Verhalten":
        [
            "Sei nett zu anderen Leuten und behandle sie so, wie auch du behandelt werden möchtest!",
            "Habe Respekt vor deinen Mitmenschen!",
            "Benutze anständige Sprache!",
        ],
    "2) Text":
        [
            "Bleib beim Thema! Für off-topic gibt es andere Plätze.",
            "Spamming ist verboten!",
            "Werbung ohne Erlaubnis eines Administrators ist verboten!",
        ],
    "3) Ton":
        [
            "Stimmverzerrer, Sprach- und Videoaufnahmen sind nur mit Einverständnis aller Teilnehmer gestattet.",
            "Mache wenn möglich keine unnötigen Hintergrundgeräusche!",
            "Channel Hopping bitte unterlassen!",
        ],
    "4) NSFW":
        [
            "Anstössige Inhalte ausserhalb NSFW-Kanälen werden sofort gelöscht und der Autor mit einem Bann/Mute bestraft!",
        ],
    "5) Sicherheit":
        [
            "Blockiere Anfragen nach persönlichen Daten und melde sie jemandem aus dem Serverteam!",
            "Melde schlimme oder wiederkehrende Fälle bitte auch Discord!",
            "Sende nie jemandem dein Passwort!",
        ],
    "6) Moderation":
        [
            "Anweisungen vom Serverteam sind zu befolgen!",
            "Das Serverteam kann dich bei falschem oder verdächtigem Verhalten ohne Vorwarnung bestrafen.",
            "Regelmissachtungen können mit dem `/report add` Befehl gemeldet werden.",
        ],
    "7) Weiteres":
        [
            "Discords Bedingungen gelten hier auch!",
            "Deine Handlungen haben Folgen - handle mit Verstand ;)",
        ],
}
