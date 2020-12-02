from discord.ext import commands
from discord import utils
import typing

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

def setup(bot):
    bot.add_cog(PRESET(bot))
