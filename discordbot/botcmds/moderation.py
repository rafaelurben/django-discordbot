import discord
from discord import DiscordException, Member, app_commands
from discord.ext import commands

from discordbot.errors import ErrorMessage, SuccessMessage

VOTEKILL_EMOJI = "☠"
VOTEKICK_EMOJI = "👋"


class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.color = 0x5156FF

    # Listeners

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if not payload.user_id == self.bot.user.id:
            emoji = payload.emoji.name
            channel = await self.bot.fetch_channel(payload.channel_id)
            message = await channel.fetch_message(payload.message_id)

            if message.author.id == self.bot.user.id:
                # Votekill

                if (
                    emoji == VOTEKILL_EMOJI
                    and message.embeds
                    and message.embeds[0].title.startswith("[Votekill]")
                ):
                    _, memberid, _, channelid, _ = message.embeds[
                        0
                    ].title.split("'")

                    voicechannel = await self.bot.fetch_channel(channelid)
                    member = await channel.guild.fetch_member(memberid)

                    if voicechannel and member:
                        if not (
                            member.voice
                            and member.voice.channel
                            and member.voice.channel == voicechannel
                        ):
                            await message.delete()
                        else:
                            allowedvoterids = [
                                member.id
                                for member in voicechannel.members
                                if not member.id == self.bot.user.id
                            ]
                            voters = []

                            for reaction in message.reactions:
                                if reaction.emoji == VOTEKILL_EMOJI:
                                    async for user in reaction.users():
                                        if user.id in allowedvoterids:
                                            voters.append(user)
                                    break

                            a = len(allowedvoterids)
                            minvotercount = a if a <= 2 else a / 2
                            votercount = len(voters)

                            print(
                                f"{votercount} of {a} voted to kick {member.name}#{member.discriminator}! (Required {minvotercount})"
                            )

                            if votercount >= minvotercount:
                                emb = self.bot.getEmbed(
                                    title="Benutzer getötet",
                                    color=0x0078D7,
                                    description=member.mention
                                    + " flog aus dem Kanal\nZählende Stimmen: "
                                    + ", ".join(
                                        [voter.mention for voter in voters]
                                    ),
                                )
                                await member.edit(voice_channel=None)
                                await message.edit(embed=emb)
                    else:
                        await message.delete()

                # Votekick

                if (
                    emoji == VOTEKICK_EMOJI
                    and message.embeds
                    and message.embeds[0].title.startswith("[Votekick]")
                ):
                    _, memberid, _ = message.embeds[0].title.split("'")

                    member = await channel.guild.fetch_member(memberid)
                    if member:
                        m = (
                            message.guild.member_count - 1
                        )  # TODO: Subtract Bots

                        minvotes = m / 2 if m <= 200 else 100

                        for reaction in message.reactions:
                            if reaction.emoji == VOTEKICK_EMOJI:
                                votes = (
                                    reaction.count - 1
                                    if reaction.me
                                    else reaction.count
                                )

                        print(
                            f"{votes} of {m} voted to kick {member.name}#{member.discriminator}! (Required {minvotes})"
                        )

                        if votes >= minvotes:
                            emb = self.bot.getEmbed(
                                title="Benutzer gekickt",
                                color=0x0078D7,
                                description=f"{member.mention} wurde vom Server gekickt!\nStimmen: {votes}",
                            )
                            await member.kick(
                                reason=f"{votes} voted to kick this person."
                            )
                            await message.edit(embed=emb)
                    else:
                        await message.delete()

    # Public commands

    @commands.command(
        brief="Stimme dafür, jemanden aus deinem Sprachkanal zu werfen.",
        description="Jemand stört? Stimme dafür, dass ein Benutzer aus dem Sprachkanal fliegt. (dieser kann danach jedoch jederzeit wieder beitreten)",
        aliases=[],
        help="Benutze /votekill <Benutzer> um eine Abstimmung zu starten.",
        usage="<Benutzer>",
    )
    @commands.guild_only()
    async def votekill(self, ctx, member: Member):
        if ctx.author.voice and ctx.author.voice.channel is not None:
            if (
                member.voice
                and member.voice.channel == ctx.author.voice.channel
            ):
                msg = await ctx.sendEmbed(
                    title=f"[Votekill] '{member.id}' in '{ctx.author.voice.channel.id}'",
                    color=0x0078D7,
                    description=f"Stimme mit {VOTEKILL_EMOJI} ab um dafür zu stimmen, dass {member.mention} aus dem Sprachkanal fliegt! (er kann danach jederzeit wieder beitreten)",
                )
                await msg.add_reaction(VOTEKILL_EMOJI)
            else:
                raise ErrorMessage(
                    "Du musst dich im gleichen Sprachkanal wie der betroffene Benutzer befinden."
                )
        else:
            raise ErrorMessage("Du musst dich in einem Sprachkanal befinden!")

    @commands.command(
        brief="Stimme dafür, jemanden aus dem Server zu werfen.",
        description="Jemand stört? Stimme dafür, dass ein Benutzer aus dem Server fliegt. (dieser kann danach jedoch jederzeit wieder mit einem Einladungslink beitreten)",
        aliases=[],
        help="Benutze /votekick <Benutzer> um eine Abstimmung zu starten.",
        usage="<Benutzer>",
    )
    @commands.guild_only()
    @commands.bot_has_permissions(kick_members=True)
    async def votekick(self, ctx, member: Member):
        msg = await ctx.sendEmbed(
            title=f"[Votekick] '{member.id}'",
            color=0x0078D7,
            description=f"Stimme mit {VOTEKICK_EMOJI} ab um dafür zu stimmen, dass {member.mention} aus dem Server fliegt! (dieser kann danach jedoch jederzeit wieder mit einem Einladungslink beitreten)",
        )
        await msg.add_reaction(VOTEKICK_EMOJI)

    # Moderator commands

    @app_commands.command(
        name="clear-channel",
        description="Löscht Nachrichten in diesem Kanal",
    )
    @app_commands.describe(
        only_bot="Nur die Nachrichten dieses Bots löschen.",
        oldest_first="Älteste zuerst",
        limit="Maximale Anzahl Nachrichten",
    )
    @app_commands.default_permissions(manage_messages=True)
    @app_commands.checks.cooldown(1, 30, key=lambda i: i.channel.id)
    @app_commands.checks.bot_has_permissions(read_message_history=True)
    @app_commands.guild_only()
    async def clear_channel(
        self,
        interaction: discord.Interaction,
        only_bot: bool = False,
        oldest_first: bool = False,
        limit: app_commands.Range[int, 0] = None,
    ):
        await interaction.response.defer(ephemeral=True)

        if only_bot:
            deleted_messages = await interaction.channel.purge(
                limit=limit,
                check=lambda m: m.author.id == self.bot.user.id,
                oldest_first=oldest_first,
                bulk=interaction.app_permissions.manage_messages,
                reason=f"User {interaction.user.mention} used /clear-channel",
            )
            raise SuccessMessage(
                f"{len(deleted_messages)} Nachricht(en) von mir gelöscht!"
            )

        if not interaction.app_permissions.manage_messages:
            raise ErrorMessage(
                "Ich darf in diesem Kanal nur meine Nachrichten löschen."
            )

        deleted_messages = await interaction.channel.purge(
            limit=limit,
            oldest_first=oldest_first,
            bulk=True,
            reason=f"User {interaction.user.mention} used /clear-channel",
        )
        raise SuccessMessage(
            f"{len(deleted_messages)} Nachricht(en) von gelöscht!"
        )

    @commands.command(
        brief="Entbannt einen Spieler",
        description="Entbannt einen zuvor gebannten Spieler",
        aliases=["pardon"],
        help="Benutze /unban <Userid> [Grund] um einen Spieler zu entbannen",
        usage="<Userid> [Grund]",
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
            raise ErrorMessage("Benutzer wurde nicht gefunden!")
        try:
            await ctx.guild.unban(
                user,
                reason="Von Moderator "
                + ctx.author.name
                + "#"
                + ctx.author.discriminator
                + " angefordert: "
                + Grund,
            )
            raise SuccessMessage(
                "Benutzer Entbannt",
                fields=[("Betroffener", user.mention), ("Grund", Grund)],
            )
        except DiscordException:
            raise ErrorMessage("Benutzer wurde nicht gefunden!")

    @commands.command(
        brief="Bewegt einen Spieler zu dir",
        description="Bewegt einen Spieler in deinen aktuellen Kanal",
        aliases=["mvhere"],
        help="Benutze /movehere <Member> um ein Mitglied hier hin zu bewegen.",
        usage="<Member>",
    )
    @commands.guild_only()
    async def movehere(self, ctx, member: Member):
        if member.voice:
            if ctx.author.voice:
                if member.voice.channel.permissions_for(
                    ctx.author
                ).move_members:
                    if member.voice.channel.permissions_for(
                        ctx.guild.get_member(self.bot.user.id)
                    ).move_members:
                        await member.edit(
                            voice_channel=ctx.author.voice.channel,
                            reason="Von Moderator "
                            + ctx.author.name
                            + "#"
                            + ctx.author.discriminator
                            + " angefordert.",
                        )
                        raise SuccessMessage(
                            "Hierhin bewegt",
                            fields=[
                                ("Betroffener", member.mention),
                                ("Kanal", ctx.author.voice.channel.name),
                            ],
                        )
                    raise commands.BotMissingPermissions([])
                raise commands.MissingPermissions([])
            raise ErrorMessage("Du befindest sich nicht in einem Sprachkanal.")
        raise ErrorMessage(
            "Der Benutzer befindet sich nicht in einem Sprachkanal."
        )


async def setup(bot):
    await bot.add_cog(Moderation(bot))
