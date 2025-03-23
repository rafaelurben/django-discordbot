# pylint: disable=no-member

import discord
from discord import Member, Interaction
from discord import app_commands
from discord import ui
from discord.ext import commands

from discordbot import utils
from discordbot.botmodules.serverdata import DjangoConnection
from discordbot.models import Report


async def send_report_to_reports_channel(interaction: Interaction, report: Report):
    try:
        channel = discord.utils.get(interaction.guild.channels, name="reports")
        if channel is not None:
            emb = utils.getEmbed(
                title=f"Neuer Report (#{report.pk})",
                fields=[
                    ("Gemeldeter Benutzer", report.user.mention),
                    ("Gemeldet von", report.reported_by.mention),
                    ("Grund", report.reason),
                    ("Zeitpunkt", report.timestamp.strftime('%Y/%m/%d %H:%M:%S')),
                ],
                inline=False,
                footerurl="",
                footertext="",
            )
            await channel.send(embed=emb)
            return

    except discord.DiscordException as e:
        print("[Support] - No #reports channel found!", e)

    await interaction.followup.send(
        ephemeral=True,
        embed=utils.getEmbed(title="Achtung", color=0xff8800,
                             description="In diesem Server existiert kein #reports-Kanal. Admins wurden daher nicht automatisch informiert! Der Report wurde trotzdem erstellt!")
    )


class ReportModal(ui.Modal):
    reason = ui.TextInput(label='Begründung', style=discord.TextStyle.paragraph, required=True)

    def __init__(self, member: Member, reason: str = ""):
        self.title = f"@{member.name} melden"
        super().__init__()
        self._member = member
        self.reason.default = reason

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        dj = DjangoConnection(interaction.user, interaction.guild)
        report = await dj.createReport(self._member, self.reason.value)
        await interaction.followup.send(
            ephemeral=True,
            embed=utils.getEmbed(title="Benutzer erfolgreich gemeldet!", inline=False, fields=[
                ("Betroffener", self._member.mention),
                ("Grund", self.reason.value)]))
        await send_report_to_reports_channel(interaction, report)


class ReportsCog(commands.Cog, name="Reports"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.color = 0xffdf00

        self.ctx_menu_report_create = app_commands.ContextMenu(
            name='Mitglied melden',
            callback=self.report_create_contextmenu,
        )
        self.bot.tree.add_command(self.ctx_menu_report_create)

    def cog_unload(self) -> None:
        self.bot.tree.remove_command(self.ctx_menu_report_create.name, type=self.ctx_menu_report_create.type)

    group = app_commands.Group(name="reports", description="Melde Spieler und sehe dir Meldungen an", guild_only=True)

    @group.command(
        name="create",
        description="Melde ein Mitglied"
    )
    @app_commands.describe(member="Zu meldendes Mitglied", reason="Begründung")
    async def report_create(self, interaction: discord.Interaction, member: Member, reason: str = None):
        await interaction.response.send_modal(ReportModal(member, reason))

    @app_commands.guild_only
    async def report_create_contextmenu(self, interaction: discord.Interaction, member: Member):
        await interaction.response.send_modal(ReportModal(member))


async def setup(bot):
    await bot.add_cog(ReportsCog(bot))
