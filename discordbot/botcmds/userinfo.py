from datetime import datetime

from discord.ext import commands
import discord

from discordbot.errors import ErrorMessage

class UserInfo(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.color = 0xffffff

    @commands.command(
        brief="Erhalte Benutzerinfos",
        description="Erhalte den Standardavatar, Avatar und das Alter eines Discordaccounts",
        aliases=["avatar", "defaultavatar", "accountage"],
        help="Benutze /userinfo <User> und du erhältst Informationen über diesen Discord Account",
        usage="<User>"
    )
    async def userinfo(self, ctx, user: discord.User):
        d = datetime.now()-user.created_at
        await ctx.sendEmbed(
            title="Benutzerinformationen",
            description=f"Infos über den Benutzer {user.mention}",
            fields=[
                ("ID", str(user.id)),
                ("Account erstellt am", f"<t:{int(datetime.timestamp(user.created_at))}>"),
                ("Account erstellt vor", f"{d.days} Tag(en)"),
                ("Standardavatar", f"[{user.default_avatar}]({user.default_avatar_url})"),
                ],
            inline=False,
            thumbnailurl=str(user.avatar_url))

    @commands.command(
        brief='Stalke musikhörende Leute',
        description='Erhalte Links zu dem Song, welcher jemand gerade hört',
        aliases=[],
        help="Benutze /usersong <Member> um den Song zu erhalten",
        usage="<Member>"
    )
    @commands.guild_only()
    async def usersong(self, ctx, member: discord.Member):
        found = False
        for activity in member.activities:
            if str(activity.type) == "ActivityType.listening":
                try:
                    await ctx.sendEmbed(title="Spotify Song", fields=[
                        ("Titel", activity.title),
                        ("Künstler", activity.artist),
                        ("Link", ("[Spotify](https://open.spotify.com/track/"+activity.track_id+")")),
                        ("Benutzer", member.mention)])
                except AttributeError:
                    raise ErrorMessage(
                        message="Scheinbar hört dieser Benutzer keinen richtigen Song.")
                found = True
        if not found:
            raise ErrorMessage(message="Dieser Benutzer hört keinen Song!")

def setup(bot):
    bot.add_cog(UserInfo(bot))
