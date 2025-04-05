from datetime import datetime

import discord
from discord import app_commands
from discord.ext import commands

from discordbot import utils


class UserInfo(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.color = 0xFFFFFF

    group = app_commands.Group(
        name="userinfo", description="Sammle Informationen über Benutzer"
    )

    @group.command(
        name="profile",
        description="Erhalte den Standardavatar, Avatar und das Alter eines Discordaccounts",
    )
    @app_commands.describe(user="Benutzer (oder Benutzer-ID)")
    async def profile(
        self,
        interaction: discord.Interaction,
        user: discord.User | discord.Member,
    ):
        diff_created = discord.utils.utcnow() - user.created_at
        emb = utils.getEmbed(
            title="Benutzerinformationen",
            description=f"Infos über {user.mention}",
            fields=[
                (
                    "Benutzername",
                    (
                        f"@{user.name}#{user.discriminator}"
                        if user.discriminator
                        and user.discriminator != "0"
                        and user.discriminator != "0000"
                        else f"@{user.name}"
                    ),
                ),
                ("Globaler Nickname", user.global_name or "_n/a_"),
                ("ID", str(user.id)),
                (
                    "Account erstellt",
                    f"<t:{int(datetime.timestamp(user.created_at))}> (vor {diff_created.days} Tag(en))",
                ),
                (
                    "Benutzer-Typ",
                    (
                        "Bot"
                        if user.bot
                        else (
                            "System"
                            if user.system or user.public_flags.system
                            else (
                                "Team"
                                if user.public_flags.team_user
                                else "Mensch"
                            )
                        )
                    ),
                ),
                (
                    "Standardavatar",
                    f"[{user.default_avatar.key}]({user.default_avatar})",
                ),
            ],
            inline=False,
            thumbnailurl=str(user.avatar) if user.avatar else None,
        )

        if not isinstance(user, discord.Member):
            return await interaction.response.send_message(embed=emb)

        diff_joined = discord.utils.utcnow() - user.created_at
        emb2 = utils.getEmbed(
            title="Guild-spezifische Infos",
            fields=[
                ("Guild Nickname", user.display_name),
                (
                    "Guild beigetreten",
                    f"<t:{int(datetime.timestamp(user.joined_at))}> (vor {diff_joined.days} Tag(en))",
                ),
                (
                    "Mehrfach beigetreten?",
                    "Ja" if user.flags.did_rejoin else "Nein",
                ),
            ],
            inline=False,
            thumbnailurl=(
                str(user.display_avatar)
                if user.display_avatar and user.display_avatar != user.avatar
                else None
            ),
        )
        return await interaction.response.send_message(embeds=[emb, emb2])

    @group.command(
        name="song",
        description="Erhalte Links zu dem Song, welcher jemand gerade hört",
    )
    @app_commands.guild_only()
    @app_commands.describe(member="Benutzer")
    async def song(
        self, interaction: discord.Interaction, member: discord.Member
    ):
        for activity in member.activities:
            if str(activity.type) == "ActivityType.listening":
                try:
                    emb = utils.getEmbed(
                        title="Spotify Song",
                        fields=[
                            ("Titel", activity.title),
                            ("Künstler", activity.artist),
                            (
                                "Link",
                                (
                                    "[Spotify](https://open.spotify.com/track/"
                                    + activity.track_id
                                    + ")"
                                ),
                            ),
                            ("Benutzer", member.mention),
                        ],
                    )
                    await interaction.response.send_message(embed=emb)
                except AttributeError:
                    await interaction.response.send_message(
                        f"Scheinbar hört {member.mention} keinen richtigen Song.",
                        ephemeral=True,
                    )
                return
        await interaction.response.send_message(
            f"{member.mention} hört keinen Song!", ephemeral=True
        )


async def setup(bot):
    await bot.add_cog(UserInfo(bot))
