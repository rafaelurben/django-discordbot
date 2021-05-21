from discord.ext import commands
from discord import Embed, Member, User, Permissions, DiscordException
from discordbot.errors import ErrorMessage, SuccessMessage

VOTEKILL_EMOJI = "☠"
VOTEKICK_EMOJI = "👋"


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
                # Votekill

                if emoji == VOTEKILL_EMOJI and message.embeds and message.embeds[0].title.startswith("[Votekill]"):
                    _, memberid, _, channelid, _ = message.embeds[0].title.split(
                        "'")

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

                            print(
                                f"{votercount} of {a} voted to kick {member.name}#{member.discriminator}! (Required {minvotercount})")

                            if votercount >= minvotercount:
                                emb = self.bot.getEmbed(
                                    title="Benutzer getötet",
                                    color=0x0078D7,
                                    description=member.mention+" flog aus dem Kanal\nZählende Stimmen: " +
                                    ", ".join(
                                        [voter.mention for voter in voters])
                                )
                                await member.edit(voice_channel=None)
                                await message.edit(embed=emb)
                    else:
                        await message.delete()

                # Votekick

                if emoji == VOTEKICK_EMOJI and message.embeds and message.embeds[0].title.startswith("[Votekick]"):
                    _, memberid, _ = message.embeds[0].title.split("'")

                    member = await channel.guild.fetch_member(memberid)
                    if member:
                        m = message.guild.member_count-1  # TODO: Subtract Bots

                        minvotes = m/2 if m <= 200 else 100

                        for reaction in message.reactions:
                            if reaction.emoji == VOTEKICK_EMOJI:
                                votes = (reaction.count -
                                         1 if reaction.me else reaction.count)

                        print(
                            f"{votes} of {m} voted to kick {member.name}#{member.discriminator}! (Required {minvotes})")

                        if votes >= minvotes:
                            emb = self.bot.getEmbed(
                                title="Benutzer gekickt",
                                color=0x0078D7,
                                description=f"{member.mention} wurde vom Server gekickt!\nStimmen: {votes}"
                            )
                            await member.kick(reason=f"{votes} voted to kick this person.")
                            await message.edit(embed=emb)
                    else:
                        await message.delete()

    # Public commands

    @commands.command(
        brief="Stimme dafür, jemanden aus deinem Sprachkanal zu werfen.",
        description="Jemand stört? Stimme dafür, dass ein Benutzer aus dem Sprachkanal fliegt. (dieser kann danach jedoch jederzeit wieder beitreten)",
        aliases=[],
        help="Benutze /votekill <Benutzer> um eine Abstimmung zu starten.",
        usage="<Benutzer>"
    )
    @commands.guild_only()
    async def votekill(self, ctx, member: Member):
        if ctx.author.voice and ctx.author.voice.channel is not None:
            if member.voice and member.voice.channel == ctx.author.voice.channel:
                msg = await ctx.sendEmbed(
                    title=f"[Votekill] '{member.id}' in '{ctx.author.voice.channel.id}'",
                    color=0x0078D7,
                    description=f"Stimme mit {VOTEKILL_EMOJI} ab um dafür zu stimmen, dass {member.mention} aus dem Sprachkanal fliegt! (er kann danach jederzeit wieder beitreten)"
                )
                await msg.add_reaction(VOTEKILL_EMOJI)
            else:
                raise ErrorMessage(
                    "Du musst dich im gleichen Sprachkanal wie der betroffene Benutzer befinden.")
        else:
            raise ErrorMessage("Du musst dich in einem Sprachkanal befinden!")

    @commands.command(
        brief="Stimme dafür, jemanden aus dem Server zu werfen.",
        description="Jemand stört? Stimme dafür, dass ein Benutzer aus dem Server fliegt. (dieser kann danach jedoch jederzeit wieder mit einem Einladungslink beitreten)",
        aliases=[],
        help="Benutze /votekick <Benutzer> um eine Abstimmung zu starten.",
        usage="<Benutzer>"
    )
    @commands.guild_only()
    @commands.bot_has_permissions(kick_members=True)
    async def votekick(self, ctx, member: Member):
        msg = await ctx.sendEmbed(
            title=f"[Votekick] '{member.id}'",
            color=0x0078D7,
            description=f"Stimme mit {VOTEKICK_EMOJI} ab um dafür zu stimmen, dass {member.mention} aus dem Server fliegt! (dieser kann danach jedoch jederzeit wieder mit einem Einladungslink beitreten)"
        )
        await msg.add_reaction(VOTEKICK_EMOJI)

    # Moderator commands

    @commands.command(
        brief="Leert den Chat",
        description="Leert den Chat",
        aliases=["cc"],
        help="Gib einfach /clearchat ein und der Chat wird bald leer sein",
        usage="[Limit]"
    )
    @commands.cooldown(1, 2.0, commands.BucketType.channel)
    @commands.has_permissions(manage_messages=True)
    @commands.bot_has_permissions(manage_messages=True)
    @commands.guild_only()
    async def clearchat(self, ctx, limit: int = 0):
        await ctx.sendEmbed(title="Chat leeren...", description="Der Chat wird geleert!")
        try:
            if limit > 0:
                await ctx.message.channel.purge(limit=limit+1)
            else:
                await ctx.message.channel.purge()
        except DiscordException as e:
            print("[Clearchat] - Error:", e)

    @commands.command(
        brief="Löscht alle Nachrichten von mir",
        description="Löscht alle von diesem Bot gesendeten Nachrichten",
        aliases=[],
        help="Nicht mit /clearchat zu verwechseln!",
        usage="",
        hidden=True,
    )
    @commands.has_permissions(manage_messages=True)
    @commands.guild_only()
    async def cleanchat(self, ctx):
        await ctx.sendEmbed(title="Chat aufräumen...", description="Der Chat wird aufgeräumt!")

        def is_me(message):
            return message.author.id == ctx.bot.user.id

        await ctx.channel.purge(limit=100, check=is_me)

    @commands.command(
        brief="Kickt einen Spieler",
        description="Kickt einen Spieler vom Server",
        aliases=[],
        help="Benutze /kick <Member> [Grund] um einen Spieler zu kicken",
        usage="<Member> [Grund]"
    )
    @commands.has_permissions(kick_members=True)
    @commands.bot_has_permissions(kick_members=True)
    @commands.guild_only()
    async def kick(self, ctx, member: Member, *args):
        if not ctx.author.roles[-1] > member.roles[-1]:
            raise ErrorMessage(
                message="Deine Rolle ist nicht höher als die des Benutzers, den du kicken wolltest!")
        Grund = " ".join(args)
        if Grund.rstrip() == "":
            Grund = "Leer"
        await member.kick(reason="Von Moderator "+ctx.author.name+"#"+ctx.author.discriminator+" angefordert: "+Grund)
        raise SuccessMessage("Benutzer Gekickt", fields=[
            ("Betroffener", member.mention), ("Grund", Grund)])

    @commands.command(
        brief="Bannt einen Spieler",
        description="Bannt einen Spieler vom Server",
        aliases=[],
        help="Benutze /ban <Member> [Grund] um einen Spieler zu bannen",
        usage="<Member> [Grund]"
    )
    @commands.has_permissions(ban_members=True)
    @commands.bot_has_permissions(ban_members=True)
    @commands.guild_only()
    async def ban(self, ctx, member: Member, *args):
        if not ctx.author.roles[-1] > member.roles[-1]:
            raise ErrorMessage(
                message="Deine Rolle ist nicht höher als die des Benutzers, den du bannen wolltest!")
        Grund = " ".join(args)
        if Grund.rstrip() == "":
            Grund = "Leer"
        await member.ban(reason="Von Moderator "+ctx.author.name+"#"+ctx.author.discriminator+" angefordert: "+Grund)
        raise SuccessMessage("Benutzer Gebannt", fields=[
            ("Betroffener", member.mention), ("Grund", Grund)])

    @commands.command(
        brief="Entbannt einen Spieler",
        description="Entbannt einen zuvor gebannten Spieler",
        aliases=["pardon"],
        help="Benutze /unban <Userid> [Grund] um einen Spieler zu entbannen",
        usage="<Userid> [Grund]"
    )
    @commands.has_permissions(ban_members=True)
    @commands.bot_has_permissions(ban_members=True)
    @commands.guild_only()
    async def unban(self, ctx, userid: int, *args):
        Grund = " ".join(args)
        if Grund.rstrip() == "":
            Grund = "Leer"
        user = self.bot.get_user(userid)
        if user is None:
            raise ErrorMessage(message="Benutzer wurde nicht gefunden!")
        try:
            await ctx.guild.unban(user, reason="Von Moderator "+ctx.author.name+"#"+ctx.author.discriminator+" angefordert: "+Grund)
            raise SuccessMessage("Benutzer Entbannt", fields=[
                                 ("Betroffener", user.mention), ("Grund", Grund)])
        except DiscordException:
            raise ErrorMessage(message="Benutzer wurde nicht gefunden!")

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
                        await member.edit(voice_channel=None, reason="Von Moderator "+ctx.author.name+"#"+ctx.author.discriminator+" angefordert: "+Grund)
                        raise SuccessMessage("Benutzer Getötet", fields=[
                                             ("Betroffener", member.mention), ("Grund", Grund)])
                    raise ErrorMessage(
                        message="Deine Rolle ist nicht höher als oder gleich wie die des Benutzers, den du töten wolltest!")
                raise commands.BotMissingPermissions([])
            raise commands.MissingPermissions([])
        raise ErrorMessage(
            message="Der Benutzer befindet sich nicht in einem Sprachkanal.")

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
                        await member.edit(voice_channel=ctx.author.voice.channel, reason="Von Moderator "+ctx.author.name+"#"+ctx.author.discriminator+" angefordert.")
                        raise SuccessMessage("Hierhin bewegt", fields=[
                                             ("Betroffener", member.mention), ("Kanal", ctx.author.voice.channel.name)])
                    raise commands.BotMissingPermissions([])
                raise commands.MissingPermissions([])
            raise ErrorMessage(
                message="Du befindest sich nicht in einem Sprachkanal.")
        raise ErrorMessage(
            message="Der Benutzer befindet sich nicht in einem Sprachkanal.")


def setup(bot):
    bot.add_cog(Moderation(bot))
