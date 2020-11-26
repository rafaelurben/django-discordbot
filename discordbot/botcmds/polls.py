from discord.ext import commands
from discord import Embed, User, TextChannel, utils
from datetime import datetime as d
import typing

NUMBER_EMOJIS = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
BOOL_EMOJIS = ["✅", "❌"]

class Polls(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.color = 0xff8c00

    @commands.command(
        brief="Erstelle eine Umfrage",
        aliases=["umfrage"],
        usage="<Frage> [1-10 Antworten]",
        help="Eine Antwort pro Zeile. Wenn keine Antworten angegeben werden, wird standardmässig Ja und Nein verwendet."
    )
    async def poll(self, ctx, *, msg):
        answers = msg.split("\n")
        question = answers.pop(0)
        if len(answers) == 0:
            msg = await ctx.sendEmbed(
                title=question,
                description=f"{BOOL_EMOJIS[0]} - Ja\n{BOOL_EMOJIS[1]} - Nein",
            )
            for e in BOOL_EMOJIS:
                await msg.add_reaction(e)
        else:
            description = "\n".join([f"{NUMBER_EMOJIS[i]} - {a}" for i, a in enumerate(answers[:10])])
            msg = await ctx.sendEmbed(
                title=question,
                description=description,
            )
            for e in NUMBER_EMOJIS[:len(answers)]:
                await msg.add_reaction(e)

def setup(bot):
    bot.add_cog(Polls(bot))
