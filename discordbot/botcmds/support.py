from discord.ext import commands
from discord import app_commands
import discord

from discordbot.models import Report
from discordbot.errors import ErrorMessage, SuccessMessage

class Support(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.color = 0xffdf00

    # Reports

    async def send_report(self, ctx, report):
        try:
            channel = discord.utils.get(ctx.guild.channels, name="reports")
            await ctx.sendEmbed(
                title=f"Neuer Report ({report.pk})",
                fields=[
                    ("Gemeldeter Benutzer", report.user.mention),
                    ("Gemeldet von", report.reported_by.mention),
                    ("Grund", report.reason),
                    ("Zeitpunkt", report.timestamp.strftime('%Y/%m/%d %H:%M:%S')),
                ],
                inline=False,
                receiver=channel,
                footerurl="",
                footertext="",
                )
        except discord.DiscordException as e:
            print("[Support] - No #reports channel found!", e)

    @commands.group(
        brief="Melde Spieler und sehe dir Meldungen an",
        description="Dieses Modul unterstützt dich dabei, Personen, welche sich falsch verhalten, auf diesem Server zu erkennen",
        usage="<Unterbefehl> <Argumente>",
        aliases=["rp", "rep", "report"],
    )
    @commands.guild_only()
    async def reports(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send_help()

    @reports.command(
        name="create",
        brief='Melde einen Spieler',
        description='Benutze diesen Command um Spieler zu melden',
        aliases=["add", "+"],
        usage="<Member> [Grund]"
        )
    async def reports_create(self, ctx, member: discord.Member, *args):
        Grund = " ".join(args)
        Grund = Grund if Grund.rstrip(" ") else "Leer"
        report = await ctx.database.createReport(dc_user=member, reason=Grund)
        await self.send_report(ctx, report)
        raise SuccessMessage("Benutzer Gemeldet", fields=[
                             ("Betroffener", member.mention), ("Grund", Grund)])

    @reports.command(
        name="delete",
        brief='Lösche einen Report',
        description='Dieser Command ist für alle mit einer der folgenden Rollen verfügbar: Moderator, Supporter, Administrator und Admin',
        aliases=["del", "-"],
        usage="<ID>"
    )
    @commands.has_any_role("Moderator", "Supporter", "Admin", "Administrator")
    async def reports_delete(self, ctx, *repids:int):
        successids = []
        for repid in repids:
            if await ctx.database.deleteReport(repid=repid):
                successids.append(f'#{repid}')
        if not successids:
            raise ErrorMessage(f"Report mit der ID {repid} wurde nicht gefunden!")
        if len(successids) > 1:
            raise SuccessMessage(f"Reports mit folgenden IDs gelöscht: {successids}")
        raise SuccessMessage(f"Report #{repid} gelöscht!")

    @reports.command(
        name="view",
        brief='Siehe Reports an',
        description='Benutze diesen Command um alle Reports zu sehen',
        aliases=["get", "show", "list"],
        help="Mit /reports view kannst du dir alle Reports ansehen, mit /reports view [Member] kannst du dir Reports eines bestimmten Mitglieds ansehen.",
        usage="[Member]"
        )
    @commands.has_any_role("Moderator", "Supporter", "Admin", "Administrator")
    async def reports_view(self, ctx, member: discord.Member=None):
        if member is None:
            await ctx.sendEmbed(
                title="Serverreports",
                description=(
                    f"Reports auf {ctx.guild.name}\n\n"+
                    await ctx.database.getReports()
                )
            )
        else:
            await ctx.sendEmbed(
                title="Mitgliederreports",
                description=("Mitglied: "+member.mention),
                fields=await ctx.database.getReports(dc_user=member),
            )

async def setup(bot):
    await bot.add_cog(Support(bot))
