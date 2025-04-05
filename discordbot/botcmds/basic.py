from datetime import datetime

import discord
from discord import DiscordException, app_commands, utils
from discord.ext import commands

from discordbot.config import INVITE_BOT, INVITE_OWNER, RULES
from discordbot.errors import SuccessMessage
from discordbot.utils import getEmbed


class Basic(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.color = 0xFFFFFF

    @app_commands.command(
        name="ping",
        description="Gibt den aktuellen Ping des Bots zurück",
    )
    async def ping(self, interaction: discord.Interaction):
        await interaction.response.defer()

        emb = getEmbed(
            title="Aktueller Ping",
            inline=False,
            fields=[
                ("Websocket-Latency", f"{int(self.bot.latency * 1000)}ms"),
            ],
        )

        start = datetime.timestamp(discord.utils.utcnow())
        msg = await interaction.followup.send(embed=emb)
        end = datetime.timestamp(discord.utils.utcnow())

        emb.add_field(
            name="Ping",
            value=f"{str(int((end - start) * 1000))}ms",
            inline=False,
        )

        await msg.edit(embed=emb)

    @app_commands.command(
        name="rules",
        description="Schickt die Regeln in den Chat",
    )
    @app_commands.guild_only()
    @app_commands.guild_install()
    async def rules(self, interaction: discord.Interaction):
        description = (
            "Das Nichtbeachten der Regeln kann und wird bestraft werden!\n"
        )

        for category in RULES:
            description += f"\n### {category}\n\n"

            for rule in RULES[category]:
                description += f"- {rule}\n"

        await interaction.response.send_message(
            embed=getEmbed(title="Regeln", description=description)
        )

    @app_commands.command(
        name="about", description="Erhalte Infos über diesen Bot"
    )
    async def about(self, interaction: discord.Interaction):
        await interaction.response.defer()

        embed = getEmbed(
            title="Über mich",
            description="Ich bin ein Discord-Bot basierend auf [django-discordbot](https://github.com/rafaelurben/django-discordbot) von [Rafael Urben](https://github.com/rafaelurben).",
        )

        def mention(user):
            return f"{user.mention} (@{user.name})"

        app_info = await self.bot.application_info()
        if app_info.team:
            if app_info.team.owner:
                embed.add_field(
                    name="Team-Besitzer",
                    value=mention(app_info.team.owner),
                    inline=False,
                )
            team_member_mentions = ", ".join(
                [mention(member) for member in app_info.team.members]
            )
            embed.add_field(
                name="Team-Mitglieder",
                value=team_member_mentions,
                inline=False,
            )
        elif app_info.owner:
            embed.add_field(
                name="Bot-Besitzer",
                value=mention(app_info.owner),
                inline=False,
            )

        await interaction.followup.send(embed=embed)

    @app_commands.command(
        name="invite",
        description="Erhalte Einladungen zu diesem Server, zum Server des Besitzers und für diesen Bot.",
    )
    @app_commands.guild_only()
    @app_commands.guild_install()
    async def invite(self, interaction: discord.Interaction):
        await interaction.response.defer()

        server_invite: discord.Invite | None = None
        if interaction.guild:
            try:
                server_invite = await interaction.guild.vanity_invite()
            except DiscordException:
                try:
                    server_invite = utils.get(
                        list(await interaction.guild.invites()),
                        max_age=0,
                        max_uses=0,
                    )
                    if not server_invite:
                        server_invite = await (
                            interaction.guild.system_channel
                            or interaction.channel
                        ).create_invite()
                except DiscordException:
                    ...

        app_info = await self.bot.application_info()
        bot_invite_url = app_info.custom_install_url or INVITE_BOT

        raise SuccessMessage(
            f"Ich bin bereits auf {app_info.approximate_guild_count} Guild(s)!",
            title="Einladungen",
            inline=False,
            fields=[
                (
                    "Dieser Server",
                    (
                        f"[Beitreten]({server_invite.url})"
                        if server_invite
                        else "Unbekannt"
                    ),
                ),
                ("Bot Owner Server", f"[Beitreten]({INVITE_OWNER})"),
                (
                    "Dieser Bot",
                    (
                        f"[Einladen]({bot_invite_url})"
                        if app_info.bot_public
                        else "Bot ist privat :)"
                    ),
                ),
            ],
        )


async def setup(bot):
    await bot.add_cog(Basic(bot))
