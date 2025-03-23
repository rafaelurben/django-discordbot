import typing

import discord
from discord import Member, Interaction
from discord import app_commands
from discord import ui
from discord.ext import commands

from discordbot import utils
from discordbot.botmodules.serverdata import DjangoConnection
from discordbot.errors import SuccessMessage, ErrorMessage
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
    reason = ui.TextInput(label='Begründung', style=discord.TextStyle.paragraph, required=True, min_length=20,
                          max_length=250)

    def __init__(self, member: Member, reason: str = ""):
        self.title = f"@{member.name} melden"
        super().__init__()
        self._member = member
        self.reason.default = reason

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        dj = DjangoConnection.from_interaction(interaction)
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

    @app_commands.command(
        name="report",
        description="Melde ein Mitglied",
        extras={'help': "Verwende diesen Befehl, um Servermitglieder zu melden, welche sich falsch verhalten."}
    )
    @app_commands.describe(member="Zu meldendes Mitglied", reason="Begründung")
    @app_commands.guild_only
    async def report_create(self, interaction: discord.Interaction, member: Member, reason: str = None):
        await interaction.response.send_modal(ReportModal(member, reason))

    @app_commands.guild_only
    async def report_create_contextmenu(self, interaction: discord.Interaction, member: Member):
        await interaction.response.send_modal(ReportModal(member))

    report_mgmt_group = app_commands.Group(name="reports", description="Verwalte Reports von Mitgliedern",
                                           guild_only=True,
                                           default_permissions=discord.Permissions(kick_members=True),
                                           extras={'help': "Verwende Befehle diese Gruppe, um Reports zu verwalten."})

    @report_mgmt_group.command(
        name="view",
        description="Sieh Reports eines Mitglieds oder aller Mitglieder an"
    )
    @app_commands.describe(member="Mitglied (leer lassen für alle Mitglieder)")
    async def reports_view(self, interaction: discord.Interaction, member: Member = None):
        await interaction.response.defer(ephemeral=True)
        dj = DjangoConnection.from_interaction(interaction)
        if member is None:
            await utils.sendEmbed(
                interaction.followup,
                title="Serverreports",
                description=(
                        f"Reports auf {interaction.guild.name}\n\n" +
                        await dj.getReports()
                )
            )
        else:
            await utils.sendEmbed(
                interaction.followup,
                title="Mitgliederreports",
                description=("Mitglied: " + member.mention),
                fields=await dj.getReports(dc_user=member),
            )

    @report_mgmt_group.command(
        name="delete",
        description="Lösche einen Report"
    )
    @app_commands.describe(report_id="ID des Reports")
    async def reports_delete(self, interaction: discord.Interaction, report_id: int):
        dj = DjangoConnection.from_interaction(interaction)
        if await dj.deleteReport(repid=report_id):
            raise SuccessMessage(f"Report mit folgender ID gelöscht: {report_id}")
        else:
            raise ErrorMessage(f"Report mit der ID {report_id} wurde nicht gefunden!")

    @reports_delete.autocomplete('report_id')
    async def reports_delete__report_id_autocomplete(self,
                                                     interaction: discord.Interaction,
                                                     current: str,
                                                     ) -> typing.List[app_commands.Choice[str]]:
        result = []
        async for report in Report.objects.filter(server_id=interaction.guild.id,
                                                  pk__contains=f"{current}").select_related('user', 'reported_by')[:25]:
            name = f"{report.id} (@{report.user.name} von @{report.reported_by.name} wegen {report.reason})"
            if len(name) > 100:
                name = name[:96] + "...)"

            result.append(app_commands.Choice(name=name, value=report.id))
        return result

    @report_mgmt_group.command(
        name="clear",
        description="Lösche alle Reports zu einem Mitglied"
    )
    @app_commands.describe(member="Mitglied")
    async def reports_clear(self, interaction: discord.Interaction, member: Member):
        await interaction.response.defer(ephemeral=True)
        dj = DjangoConnection.from_interaction(interaction)
        await dj.clearReports(member.id)
        raise SuccessMessage(f"Reports für {member.mention} gelöscht!")


async def setup(bot):
    await bot.add_cog(ReportsCog(bot))
