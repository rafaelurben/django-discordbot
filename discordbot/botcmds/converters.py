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
        aliases=["mors","morsecode"],
        help="Benutze /morse <Text> und erhalte den Text in Morsecode oder umgekehrt",
        usage="<Morsecode | Nachricht>"
        )
    async def morse(self, ctx, text: str, *args):
        message = " ".join((text,)+args)
        if message.replace("-", "").replace("_", "").replace(".", "").replace("|", "").replace(" ", "") == "":
            text = converters.morse_decrypt(message.replace("_","-").replace(" | ", "  "))
            morse = message
        else:
            text = message
            morse = converters.morse_encrypt(message)
        await ctx.sendEmbed(title="Morsecode", fields=[("Morsecode", morse.replace("  "," | ")),("Text", text)])


async def setup(bot):
    await bot.add_cog(Converters(bot))
