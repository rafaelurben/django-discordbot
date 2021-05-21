from discord.ext import commands
from discord import Embed, Member, User, Webhook, utils, DiscordException

from discordbot.models import BotPermission, Report
from discordbot.errors import ErrorMessage, SuccessMessage

import time
import typing

class Support(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.color = 0xffdf00

    # Reports

    async def send_report(self, ctx, report):
        try:
            channel = utils.get(ctx.guild.channels, name="reports")
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
        except DiscordException as e:
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
    async def reports_create(self, ctx, member: Member, *args):
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
    async def reports_view(self, ctx, member:Member=None):
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

    # Remote
    
    @commands.group(
        brief="Lasse jemanden Commands für dich ausführen",
        description="Überlasse jemandem das Recht, Commands in deinem Namen auszuführen.",
        usage="<Unterbefehl> <Argumente>",
    )
    async def remote(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send_help()

    @remote.command(
        name="allow",
        brief="Füge einen erlaubten Spieler hinzu",
        aliases=["+", "add"],
        usage="<Member>",
        help="Dieser Befehl kann ziemlich viel Mist machen, vorallem wenn du Rechte hast! Also pass auf!",
    )
    async def remote_allow(self, ctx, member: typing.Union[Member, User]):
        if not await ctx.database._has(BotPermission, id_1=str(ctx.author.id), id_2=str(member.id), typ="remote_permission"):
            await ctx.database._create(BotPermission, id_1=str(ctx.author.id), id_2=str(member.id), typ="remote_permission")
            raise SuccessMessage(member.mention+" darf nun Befehle für dich ausführen!")
        raise ErrorMessage("Dieser Benutzer darf bereits Befehle für dich ausführen!")

    @remote.command(
        name="allowraw",
        brief="Füge eine erlaubte ID hinzu",
        aliases=["allowwebhook", "++", "addraw"],
        usage="<ID>",
        help="Dies wird gebraucht, um Webhooks die Erlaubnis zu geben, Commands für dich auszuführen. Dieser Befehl kann ziemlich viel Mist machen, vorallem wenn du Rechte hast! Also pass auf!",
        hidden=True,
    )
    async def remote_allowraw(self, ctx, id: int):
        if not await ctx.database._has(BotPermission, id_1=str(ctx.author.id), id_2=str(id), typ="remote_permission"):
            await ctx.database._create(BotPermission, id_1=str(ctx.author.id), id_2=str(id), typ="remote_permission")
            raise SuccessMessage(str(id)+" darf nun Befehle für dich ausführen!")
        raise ErrorMessage("Diese ID darf bereits Befehle für dich ausführen!")

    @remote.command(
        name="disallow",
        brief="Entferne einen erlaubten Spieler",
        aliases=["-", "remove"],
        usage="<Member>",
    )
    async def remote_disallow(self, ctx, member: typing.Union[Member, User]):
        if await ctx.database._has(BotPermission, id_1=str(ctx.author.id), id_2=str(member.id), typ="remote_permission"):
            await ctx.database._listdelete(BotPermission, id_1=str(ctx.author.id), id_2=str(member.id), typ="remote_permission")
            raise SuccessMessage(member.mention+" darf nun nicht mehr Befehle für dich ausführen!")
        raise ErrorMessage("Dieser Benutzer steht nicht auf deiner Liste!")

    @remote.command(
        name="disallowraw",
        brief="Entferne eine erlaubte ID",
        aliases=["--", "removeraw"],
        usage="<Member>",
        help="Dies wird gebraucht, um Webhooks die Erlaubnis zu geben, Commands für dich auszuführen.",
        hidden=True,
    )
    async def remote_disallowraw(self, ctx, id: int):
        if await ctx.database._has(BotPermission, id_1=str(ctx.author.id), id_2=str(id), typ="remote_permission"):
            await ctx.database._listdelete(BotPermission, id_1=str(ctx.author.id), id_2=str(id), typ="remote_permission")
            raise SuccessMessage(str(id)+" darf nun nicht mehr Befehle für dich ausführen!")
        raise ErrorMessage("Diese ID steht nicht auf deiner Liste!")

    @remote.command(
        name="list",
        brief="Liste die erlaubten Spieler auf",
        aliases=[],
        usage=""
    )
    async def remote_list(self, ctx):
        perms = await ctx.database._list(BotPermission, id_1=str(ctx.author.id), typ="remote_permission")
        await ctx.sendEmbed(
            title="Benutzerliste",
            description="Folgende Benutzer/IDs dürfen Befehle für dich ausführen:\n\n"+"\n".join([f"<@{i.id_2}> ({i.id_2})" for i in perms])
        )

    @remote.command(
        name="run",
        brief="Führe einen Befehl als jemand anderes aus",
        aliases=[],
        usage="<Member> <Command> [Argumente]",
        help="Falls Unterbefehle verwendet werden, benutze bitte befehl_unterbefehl als Command",
    )
    async def remote_run(self, ctx, member: typing.Union[Member, User], command: str, *args):
        if await ctx.database._has(BotPermission, id_1=str(member.id), id_2=str(ctx.author.id), typ="remote_permission") or await ctx.database._has(BotPermission, id_1=str(member.id), id_2=str(ctx.message.webhook_id), typ="remote_permission"):
            await ctx.invoke_as(member, command, *args)
        else:
            raise ErrorMessage("Du darfst keine Befehle für diesen Benutzer ausführen!")

def setup(bot):
    bot.add_cog(Support(bot))
