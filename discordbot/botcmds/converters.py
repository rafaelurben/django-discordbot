from discord.ext import commands
from discord import utils
from datetime import datetime as d
import typing
from discordbot.botmodules import converters

class Converters(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.color = 0xffffff

    @commands.command(
        brief="Wandle Morsecode um",
        description="Wandle Morsecode um",
        aliases=["mors","morsecode"],
        help="Benutze /morse <Text> und erhalte den Text in Morsecode oder umgekehrt",
        usage="<Morsecode | Nachricht>"
        )
    async def morse(self, ctx):
        message = ctx.getargs()
        if message.replace("-","").replace("_","").replace(".","").replace(" ","") == "":
            text = converters.morse_decrypt(message.replace("_","-"))
            morse = message
        else:
            text = message
            morse = converters.morse_encrypt(message)
        await ctx.sendEmbed(title="Morsecode", color=self.color, fields=[("Morsecode", morse.replace("  "," | ")),("Text", text)])


def setup(bot):
    bot.add_cog(Converters(bot))
