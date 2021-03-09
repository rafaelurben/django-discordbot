from discord.ext import commands
from discord import Embed, Member, User, Permissions
from discordbot.errors import ErrorMessage

VOTEKILL_EMOJI = "☠"

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.color = 0x5156ff

    # Listeners

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if not payload.user_id == self.bot.user.id:
            emoji = payload.emoji.name
            channel = await self.bot.fetch_channel(payload.channel_id)
            message = await channel.fetch_message(payload.message_id)

            if message.author.id == self.bot.user.id:
                ### Votekill

                if emoji == VOTEKILL_EMOJI and message.embeds and message.embeds[0].title.startswith("[Votekill]"):
                    _,memberid,_,channelid,_ = message.embeds[0].title.split("'")

                    voicechannel = await self.bot.fetch_channel(channelid)
                    member = await channel.guild.fetch_member(memberid)

                    if voicechannel and member:
                        if not (member.voice and member.voice.channel and member.voice.channel == voicechannel):
                            await message.delete()
                        else:
                            allowedvoterids = [
                                member.id for member in voicechannel.members if not member.id == self.bot.user.id]
                            voters = []

                            for reaction in message.reactions:
                                if reaction.emoji == VOTEKILL_EMOJI:
                                    async for user in reaction.users():
                                        if user.id in allowedvoterids:
                                            voters.append(user)
                                    break

                            a = len(allowedvoterids)
                            minvotercount = a if a <= 2 else a/2
                            votercount = len(voters)

                            print(f"{votercount} of {a} voted to kick {member.name}#{member.discriminator}! (Required {minvotercount})")

                            if votercount >= minvotercount:
                                emb = self.bot.getEmbed(
                                    title="[Votekill completed]",
                                    color=0x0078D7,
                                    description="Voted to kill "+member.mention+"\n\nAll voters: "+", ".join([voter.mention for voter in voters])
                                )
                                await member.edit(voice_channel=None)
                                await channel.send(embed=emb)
                                await message.delete()
                    else:
                        await message.delete()
                    


    # Public commands

    @commands.command(
        brief="Votekill someone in your current voice channel"
    )
    @commands.guild_only()
    async def votekill(self, ctx, member:Member):
        if ctx.author.voice and ctx.author.voice.channel is not None:
            if member.voice and member.voice.channel == ctx.author.voice.channel:
                msg = await ctx.sendEmbed(
                    title=f"[Votekill] '{member.id}' in '{ctx.author.voice.channel.id}'",
                    color=0x0078D7,
                    description=f"Stimme mit {VOTEKILL_EMOJI} ab um dafür zu stimmen, dass {member.mention} aus dem Sprachkanal fliegt!"
                )
                await msg.add_reaction(VOTEKILL_EMOJI)
            else:
                raise ErrorMessage("Du musst dich im gleichen Sprachkanal wie der betroffene Benutzer befinden.")
        else:
            raise ErrorMessage("Du musst dich in einem Sprachkanal befinden!")



    # Moderator commands


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
        await ctx.sendEmbed(title="Chat wird geleert...", description="Der Chat wird geleert!")
        try:
            await ctx.message.channel.purge()
        except Exception as e:
            print("[Clearchat] - Error:", e)
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
    async def kick(self, ctx, member: Member, *args):
        if ctx.author.roles[-1] > member.roles[-1]:
            Grund = " ".join(args)
            if Grund.rstrip() == "":
                Grund = "Leer"
            await member.kick(reason="Von Moderator "+ctx.author.name+"#"+ctx.author.discriminator+" angefordert: "+Grund)
            await ctx.sendEmbed(title="Benutzer Gekickt", fields=[("Betroffener",member.mention),("Grund",Grund)])
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
    async def ban(self, ctx, member: Member, *args):
        if ctx.author.roles[-1] > member.roles[-1]:
            Grund = " ".join(args)
            if Grund.rstrip() == "":
                Grund = "Leer"
            await member.ban(reason="Von Moderator "+ctx.author.name+"#"+ctx.author.discriminator+" angefordert: "+Grund)
            await ctx.sendEmbed(title="Benutzer Gebannt", fields=[("Betroffener",member.mention),("Grund",Grund)])
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
    async def unban(self, ctx, userid: int, *args):
        Grund = " ".join(args)
        if Grund.rstrip() == "":
            Grund = "Leer"
        user = self.bot.get_user(userid)
        if user is None:
            raise commands.BadArgument(message="Benutzer wurde nicht gefunden!")
        try:
            await ctx.guild.unban(user,reason="Von Moderator "+ctx.author.name+"#"+ctx.author.discriminator+" angefordert: "+Grund)
            await ctx.sendEmbed(title="Benutzer Entbannt", fields=[("Betroffener",user.mention),("Grund",Grund)])
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
    async def kill(self, ctx, member: Member, *args):
        Grund = " ".join(args)
        if Grund.rstrip() == "":
            Grund = "Leer"
        VoiceState = member.voice
        if VoiceState:
            if VoiceState.channel.permissions_for(ctx.author).move_members:
                if VoiceState.channel.permissions_for(ctx.guild.get_member(self.bot.user.id)).move_members:
                    if ctx.author.roles[-1] >= member.roles[-1]:
                        await member.edit(voice_channel=None,reason="Von Moderator "+ctx.author.name+"#"+ctx.author.discriminator+" angefordert: "+Grund)
                        await ctx.sendEmbed(title="Benutzer Getötet", fields=[("Betroffener",member.mention),("Grund",Grund)])
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
                        await ctx.sendEmbed(title="Hierhin bewegt", fields=[("Betroffener",member.mention),("Kanal",ctx.author.voice.channel.name)])
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
