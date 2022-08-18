from datetime import datetime

from discord.ext import commands
from discord import app_commands
import discord

from discordbot import utils

class UserInfo(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.color = 0xffffff

    group = app_commands.Group(name="userinfo", description="Sammle Informationen über Benutzer")

    @group.command(
        name='profile',
        description="Erhalte den Standardavatar, Avatar und das Alter eines Discordaccounts",
    )
    @app_commands.describe(user="Benutzer")
    async def profile(self, interaction: discord.Interaction, user: discord.User):
        diff = discord.utils.utcnow()-user.created_at
        emb = utils.getEmbed(
            title="Benutzerinformationen",
            description=f"Infos über den Benutzer {user.mention}",
            fields=[
                ("ID", str(user.id)),
                ("Account erstellt am", f"<t:{int(datetime.timestamp(user.created_at))}>"),
                ("Account erstellt vor", f"{diff.days} Tag(en)"),
                ("Standardavatar", f"[{user.default_avatar.key}]({user.default_avatar})"),
                ],
            inline=False,
            thumbnailurl=str(user.avatar))
        await interaction.response.send_message(embed=emb)

    @group.command(
        name='song',
        description='Erhalte Links zu dem Song, welcher jemand gerade hört',
    )
    @app_commands.guild_only()
    @app_commands.describe(member="Benutzer")
    async def song(self, interaction: discord.Interaction, member: discord.Member):
        for activity in member.activities:
            if str(activity.type) == "ActivityType.listening":
                try:
                    emb = utils.getEmbed(title="Spotify Song", fields=[
                        ("Titel", activity.title),
                        ("Künstler", activity.artist),
                        ("Link", ("[Spotify](https://open.spotify.com/track/"+activity.track_id+")")),
                        ("Benutzer", member.mention)])
                    await interaction.response.send_message(embed=emb)
                except AttributeError:
                    await interaction.response.send_message(f"Scheinbar hört {member.mention} keinen richtigen Song.", ephemeral=True)
                return
        await interaction.response.send_message(f"{member.mention} hört keinen Song!", ephemeral=True)

async def setup(bot):
    await bot.add_cog(UserInfo(bot))
