# pylint: disable=unused-variable

from discord.ext import commands

from discordbot.config import DEBUG, EXTENSIONFOLDER, EXTENSIONS
from discordbot.botmodules.serverdata import DjangoConnection

def setup(bot):
    @bot.event
    async def on_ready():
        print(f"[Bot] - Logged in as '{bot.user.name}' - '{bot.user.id}'")
        for extension in EXTENSIONS:
            try:
                bot.load_extension(EXTENSIONFOLDER+"."+extension)
            except commands.errors.ExtensionAlreadyLoaded:
                pass
        print(f"[Bot] - Loaded extensions!")

    @bot.event
    async def on_connect():
        print(f"[Bot] - Connected!")

    @bot.event
    async def on_disconnect():
        print(f"[Bot] - Disconnected!")

    @bot.event
    async def on_guild_join(guild):
        print(f"[Bot] - Joined new guild: {guild.name} ({guild.id})")
        await DjangoConnection.fetch_server(guild)