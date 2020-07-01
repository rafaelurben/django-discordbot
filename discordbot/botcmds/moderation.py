from discord.ext import commands
from discord import Embed, Member, User, Permissions


class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.color = 0x5156ff


    @commands.command(
        brief="Leert den Chat",
        description="Leert den Chat",
        aliases=["cc"],
        help="Gib einfach /clearchat ein und der Chat wird bald leer sein",
        usage=""
        )
    @commands.cooldown(1,2.0,commands.BucketType.channel)
    @commands.has_permissions(manage_messages = True)
    @commands.bot_has_permissions(manage_messages = True)
    @commands.guild_only()
    async def clearchat(self,ctx):
        try:
            await ctx.message.channel.purge()
        except Exception as e:
            pass



    @commands.command(
        brief="Kickt einen Spieler",
        description="Kickt einen Spieler vom Server",
        aliases=[],
        help="Benutze /kick <Member> [Grund] um einen Spieler zu kicken",
        usage="<Member> [Grund]"
        )
    @commands.has_permissions(kick_members = True)
    @commands.bot_has_permissions(kick_members = True)
    @commands.guild_only()
    async def kick(self, ctx, member: Member):
        if ctx.author.roles[-1] > member.roles[-1]:
            Grund = ctx.getargs()
            if Grund.rstrip() == "":
                Grund = "Leer"
            await member.kick(reason="Von Moderator "+ctx.author.name+"#"+ctx.author.discriminator+" angefordert: "+Grund)
            await ctx.sendEmbed(title="Benutzer Gekickt", color=self.color, fields=[("Betroffener",member.mention),("Grund",Grund)])
        else:
            raise commands.BadArgument(message="Deine Rolle ist nicht höher als die des Benutzers, den du kicken wolltest!")


    @commands.command(
        brief="Bannt einen Spieler",
        description="Bannt einen Spieler vom Server",
        aliases=[],
        help="Benutze /ban <Member> [Grund] um einen Spieler zu bannen",
        usage="<Member> [Grund]"
        )
    @commands.has_permissions(ban_members = True)
    @commands.bot_has_permissions(ban_members = True)
    @commands.guild_only()
    async def ban(self, ctx, member: Member):
        if ctx.author.roles[-1] > member.roles[-1]:
            Grund = ctx.getargs()
            if Grund.rstrip() == "":
                Grund = "Leer"
            await member.ban(reason="Von Moderator "+ctx.author.name+"#"+ctx.author.discriminator+" angefordert: "+Grund)
            await ctx.sendEmbed(title="Benutzer Gebannt", color=self.color, fields=[("Betroffener",member.mention),("Grund",Grund)])
        else:
            raise commands.BadArgument(message="Deine Rolle ist nicht höher als die des Benutzers, den du bannen wolltest!")



    @commands.command(
        brief="Entbannt einen Spieler",
        description="Entbannt einen zuvor gebannten Spieler",
        aliases=["pardon"],
        help="Benutze /unban <Userid> [Grund] um einen Spieler zu entbannen",
        usage="<Userid> [Grund]"
        )
    @commands.has_permissions(ban_members = True)
    @commands.bot_has_permissions(ban_members = True)
    @commands.guild_only()
    async def unban(self, ctx, userid: int):
        Grund = ctx.getargs()
        if Grund.rstrip() == "":
            Grund = "Leer"
        User = self.bot.get_user(userid)
        if User is None:
            raise commands.BadArgument(message="Benutzer wurde nicht gefunden!")
        try:
            await ctx.guild.unban(User,reason="Von Moderator "+ctx.author.name+"#"+ctx.author.discriminator+" angefordert: "+Grund)
            await ctx.sendEmbed(title="Benutzer Entbannt", color=self.color, fields=[("Betroffener",member.mention),("Grund",Grund)])
        except:
            raise commands.BadArgument(message="Benutzer wurde nicht gefunden!")


    @commands.command(
        brief="Tötet einen Spieler",
        description="Kickt einen Spieler aus dem aktuellen Sprachkanal",
        aliases=["kickvoice"],
        help="Benutze /kill <Member> [Grund] um einen Spieler zu töten",
        usage="<Member> [Grund]"
        )
    @commands.guild_only()
    async def kill(self, ctx, member: Member):
        Grund = ctx.getargs()
        if Grund.rstrip() == "":
            Grund = "Leer"
        VoiceState = member.voice
        if VoiceState:
            if VoiceState.channel.permissions_for(ctx.author).move_members:
                if VoiceState.channel.permissions_for(ctx.guild.get_member(self.bot.user.id)).move_members:
                    if ctx.author.roles[-1] >= member.roles[-1]:
                        await member.edit(voice_channel=None,reason="Von Moderator "+ctx.author.name+"#"+ctx.author.discriminator+" angefordert: "+Grund)
                        await ctx.sendEmbed(title="Benutzer Getötet", color=self.color, fields=[("Betroffener",member.mention),("Grund",Grund)])
                    else:
                        raise commands.BadArgument(message="Deine Rolle ist nicht höher als oder gleich wie die des Benutzers, den du töten wolltest!")
                else:
                    raise commands.BotMissingPermissions([])
            else:
                raise commands.MissingPermissions([])
        else:
            raise commands.BadArgument(message="Der Benutzer befindet sich nicht in einem Sprachkanal.")

    @commands.command(
        brief="Bewegt einen Spieler zu dir",
        description="Bewegt einen Spieler in deinen aktuellen Kanal",
        aliases=["mvhere"],
        help="Benutze /movehere <Member> um ein Mitglied hier hin zu bewegen.",
        usage="<Member>"
        )
    @commands.guild_only()
    async def movehere(self, ctx, member: Member):
        if member.voice:
            if ctx.author.voice:
                if member.voice.channel.permissions_for(ctx.author).move_members:
                    if member.voice.channel.permissions_for(ctx.guild.get_member(self.bot.user.id)).move_members:
                        await member.edit(voice_channel=ctx.author.voice.channel,reason="Von Moderator "+ctx.author.name+"#"+ctx.author.discriminator+" angefordert.")
                        await ctx.sendEmbed(title="Hierhin bewegt", color=self.color, fields=[("Betroffener",member.mention),("Kanal",ctx.author.voice.channel.name)])
                    else:
                        raise commands.BotMissingPermissions([])
                else:
                    raise commands.MissingPermissions([])
            else:
                raise commands.BadArgument(message="Du befindest sich nicht in einem Sprachkanal.")
        else:
            raise commands.BadArgument(message="Der Benutzer befindet sich nicht in einem Sprachkanal.")


def setup(bot):
    bot.add_cog(Moderation(bot))
