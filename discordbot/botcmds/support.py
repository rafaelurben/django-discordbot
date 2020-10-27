from discord.ext import commands
from discord import Embed, Member, User
import time

class Support(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.color = 0xffdf00

    @commands.command(
        brief='Melde einen Spieler',
        description='Benutze diesen Command um Spieler zu melden',
        aliases=[],
        help="Wenn ein Benutzer Blödsinn treibt, dann benutze /report <Member> [Grund]",
        usage="<Member> [Grund]"
        )
    @commands.guild_only()
    async def report(self, ctx, member: Member):
        Grund = ctx.getargs()
        Grund = Grund if Grund.rstrip(" ") else "Leer"
        await ctx.database.createReport(dc_user=member, reason=Grund)
        await ctx.sendEmbed(title="Benutzer Gemeldet", color=self.color, fields=[("Betroffener",member.mention),("Grund",Grund)])
        return


    @commands.command(
        brief='Erhalte alle Reports',
        description='Benutze diesen Command um alle Reports zu sehen',
        aliases=["getreports","getreport"],
        help="Mit /getreports [Member] kannst du alle Reports ansehen.",
        usage="[Member]"
        )
    @commands.has_any_role("Moderator","Supporter","Admin")
    @commands.guild_only()
    async def reports(self, ctx, member:Member=None):
        if member == None:
            EMBED = Embed(title="Server Reports", color=self.color)
            EMBED.set_footer(text=f'Angefordert von {ctx.author.name}',icon_url=ctx.author.avatar_url)
            for user in await ctx.database.getReports():
                EMBED.add_field(**user)
            await ctx.send(embed=EMBED)
        else:
            EMBED = Embed(title="User Reports", color=self.color, description=("User: "+member.mention))
            EMBED.set_footer(text=f'Angefordert von {ctx.author.name}',icon_url=ctx.author.avatar_url)
            for report in await ctx.database.getReports(dc_user=member):
                EMBED.add_field(**report)
            await ctx.send(embed=EMBED)
        return




def setup(bot):
    bot.add_cog(Support(bot))
