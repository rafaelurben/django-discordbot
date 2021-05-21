# pylint: disable=unused-variable

from discord import DiscordException
from discord.ext import commands

from discordbot.config import DEBUG

def setup(bot):
    @bot.event
    async def on_command(ctx):
        if DEBUG:
            print(f"[Command] - '{ctx.message.content}' von '{ctx.author.name}#{str(ctx.author.discriminator)}'")
        if ctx.guild is not None:
            try:
                await ctx.message.delete()
            except DiscordException:
                ...
