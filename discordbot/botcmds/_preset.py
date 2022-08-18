from discord.ext import commands

import discord

from discordbot.errors import ErrorMessage


#from discordbot.config import 

class PRESET(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.color = 0xffffff

    @commands.command(
        brief="",
        description="",
        aliases=[],
        help="",
        usage=""
        )
    async def preset(self, ctx):
        pass

async def setup(bot):
    await bot.add_cog(PRESET(bot))
