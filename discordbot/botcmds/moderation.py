import typing

import discord
import discord.ui
from discord import Member, app_commands
from discord.ext import commands

from discordbot import utils
from discordbot.errors import ErrorMessage, SuccessMessage


class VoteKickUi(discord.ui.View):
    def __init__(
        self,
        target: discord.Member,
        creator: discord.Member,
        online_users: int,
    ):
        self._target = target
        self._creator = creator
        self._member_ids_voted_kick = [creator.id]
        self._member_ids_voted_stay = []
        self._votes_required = max(2, min(online_users // 2, 10))
        super().__init__(timeout=3600)

    def _get_vote_info(self) -> tuple[int, int]:
        kick_votes = len(self._member_ids_voted_kick)
        stay_votes = len(self._member_ids_voted_stay)
        total_votes = kick_votes + stay_votes
        vote_percentage = (
            (kick_votes * 100 // total_votes) if total_votes else 0
        )
        return total_votes, vote_percentage

    def get_embed(self, status="Abstimmung aktiv"):
        total_votes, vote_percentage = self._get_vote_info()
        return utils.getEmbed(
            title=f"Vote-Kick",
            color=0x0078D7,
            description=f"Möchtest du, dass {self._target.mention} vom Server gekickt wird?",
            inline=False,
            fields=[
                ("Stimmen für 'kick'", str(len(self._member_ids_voted_kick))),
                (
                    "Stimmen für 'bleiben'",
                    str(len(self._member_ids_voted_stay)),
                ),
                (
                    "Benötigte Stimmquote",
                    f"75%+ bei {self._votes_required} Stimmen",
                ),
                (
                    "Aktuelle Stimmquote",
                    f"{vote_percentage}% bei {total_votes} Stimmen",
                ),
                ("Status", status),
            ],
        )

    async def handle_changed(self, interaction: discord.Interaction):
        total_votes, vote_percentage = self._get_vote_info()
        if total_votes >= self._votes_required:
            if vote_percentage >= 75:
                await interaction.response.edit_message(
                    view=None,
                    embed=self.get_embed(
                        status=f"{self._target.mention} wurde gekickt!"
                    ),
                )
                await self._target.kick(
                    reason=f"Vote-Kick with {total_votes} votes of which {vote_percentage}% voted for kick."
                )
            else:
                await interaction.response.edit_message(
                    view=None,
                    embed=self.get_embed(
                        status=f"{self._target.mention} darf bleiben!"
                    ),
                )
        else:
            await interaction.response.edit_message(
                view=self, embed=self.get_embed()
            )

    @discord.ui.button(label="Weg mit dir! 👋", style=discord.ButtonStyle.red)
    async def add_kick_vote(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        if interaction.user.id in self._member_ids_voted_kick:
            return await interaction.response.send_message(
                "❌ Du hast bereits für 'kick' abgestimmt!", ephemeral=True
            )

        if interaction.user.id in self._member_ids_voted_stay:
            self._member_ids_voted_stay.remove(interaction.user.id)
        self._member_ids_voted_kick.append(interaction.user.id)

        await self.handle_changed(interaction)
        await interaction.followup.send(
            "✅ Erfolgreich für 'kick' abgestimmt!", ephemeral=True
        )

    @discord.ui.button(
        label="Du darfst bleiben! 🛑", style=discord.ButtonStyle.green
    )
    async def add_stay_vote(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        if interaction.user.id in self._member_ids_voted_stay:
            return await interaction.response.send_message(
                "❌ Du hast bereits für 'bleiben' abgestimmt!", ephemeral=True
            )
        if interaction.user.id == self._target.id:
            return await interaction.response.send_message(
                "❌ Du darfst nicht für dich selbst stimmen!", ephemeral=True
            )

        if interaction.user.id in self._member_ids_voted_kick:
            self._member_ids_voted_kick.remove(interaction.user.id)
        self._member_ids_voted_stay.append(interaction.user.id)

        await self.handle_changed(interaction)
        await interaction.followup.send(
            "✅ Erfolgreich für 'bleiben' abgestimmt!", ephemeral=True
        )

    @discord.ui.button(
        label="Stimme entfernen", style=discord.ButtonStyle.gray
    )
    async def remove_vote(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        if interaction.user.id in self._member_ids_voted_kick:
            self._member_ids_voted_kick.remove(interaction.user.id)
        elif interaction.user.id in self._member_ids_voted_stay:
            self._member_ids_voted_stay.remove(interaction.user.id)
        else:
            return await interaction.response.send_message(
                "❌ Du hattest gar keine Stimme abgegeben!", ephemeral=True
            )

        await self.handle_changed(interaction)
        await interaction.followup.send("✅ Stimme entfernt!", ephemeral=True)


class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.color = 0x5156FF

    # Public commands

    @app_commands.command(
        name="vote-kick",
        description="Stimme dafür, jemanden aus dem Server zu werfen.",
    )
    @app_commands.guild_only()
    @app_commands.guild_install()
    @app_commands.checks.bot_has_permissions(kick_members=True)
    async def vote_kick(
        self, interaction: discord.Interaction, member: Member
    ):
        guild = await self.bot.fetch_guild(
            interaction.guild_id, with_counts=True
        )
        online_users = guild.approximate_presence_count - 1
        if online_users <= 2:
            raise ErrorMessage(
                "Es sind zu wenige Benutzer online, um abzustimmen."
            )

        view = VoteKickUi(member, interaction.user, online_users)
        await interaction.response.send_message(
            view=view, embed=view.get_embed(), ephemeral=False
        )

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
    @app_commands.guild_install()
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

    @app_commands.command(
        name="unban",
        description="Entbanne einen zuvor gebannten Spieler",
    )
    @app_commands.describe(user_id="Benutzer-ID", reason="Begründung")
    @app_commands.default_permissions(ban_members=True)
    @app_commands.checks.bot_has_permissions(ban_members=True)
    @app_commands.guild_only()
    @app_commands.guild_install()
    async def unban(
        self,
        interaction: discord.Interaction,
        user_id: str,
        reason: str = "",
    ):
        try:
            user_id = int(user_id)
        except TypeError:
            raise ErrorMessage("Ungültige Benutzer-ID!")

        try:
            user = discord.Object(user_id, type=discord.User)

            await interaction.guild.unban(
                user,
                reason=f"Von @{interaction.user.name} angefordert mit Begründung: {reason}",
            )
            raise SuccessMessage(
                "Benutzer entbannt!",
                inline=False,
                fields=[("Betroffener", f"<@{user_id}>"), ("Grund", reason)],
            )
        except discord.NotFound:
            raise ErrorMessage(
                "Zu entbannender Benutzer konnte nicht gefunden werden!"
            )

    @unban.autocomplete("user_id")
    async def unban__user_autocomplete(
        self,
        interaction: discord.Interaction,
        current: str,
    ) -> typing.List[app_commands.Choice[str]]:
        results = []
        async for ban_entry in interaction.guild.bans():
            if (
                current in ban_entry.user.name
                or current in ban_entry.user.global_name
                or current in ban_entry.reason
            ):
                name = f"@{ban_entry.user.name} wegen '{ban_entry.reason}'"
                if len(name) > 100:
                    name = name[:96] + "...'"
                results.append(
                    app_commands.Choice(
                        name=name,
                        value=str(ban_entry.user.id),
                    )
                )

            if len(results) == 25:
                break
        return results[:25]

    @app_commands.command(
        name="move-here",
        description="Bewegt einen Spieler in deinen aktuellen Sprachkanal",
    )
    @app_commands.default_permissions(move_members=True)
    @app_commands.checks.bot_has_permissions(move_members=True)
    @app_commands.guild_only()
    @app_commands.guild_install()
    async def move_here(
        self, interaction: discord.Interaction, member: discord.Member
    ):
        target = (
            interaction.user.voice.channel if interaction.user.voice else None
        )
        if target is None:
            raise ErrorMessage("Du befindest sich nicht in einem Sprachkanal.")

        source = member.voice.channel if member.voice else None
        if source is None:
            raise ErrorMessage(
                "Der Benutzer befindet sich nicht in einem Sprachkanal."
            )

        if not source.permissions_for(interaction.user).move_members:
            raise app_commands.MissingPermissions(["move_members"])

        await member.edit(
            voice_channel=target,
            reason=f"Von @{interaction.user.name} angefordert.",
        )
        raise SuccessMessage(
            f"{member.mention} wurde bewegt!",
            inline=True,
            fields=[
                ("Von", source.mention),
                ("Zu", target.mention),
            ],
        )


async def setup(bot):
    await bot.add_cog(Moderation(bot))
