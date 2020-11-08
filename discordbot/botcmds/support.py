from discord.ext import commands
from discord import Embed, Member, User, Webhook
import time
import typing

class Support(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.color = 0xffdf00

    @commands.command(
        brief='Melde einen Spieler',
        description='Benutze diesen Command um Spieler zu melden',
        aliases=[],
        help="Wenn ein Benutzer Blödsinn treibt, dann benutze /report <Member> [Grund]",
        usage="<Member> [Grund]"
        )
    @commands.guild_only()
    async def report(self, ctx, member: Member, *args):
        Grund = " ".join(args)
        Grund = Grund if Grund.rstrip(" ") else "Leer"
        await ctx.database.createReport(dc_user=member, reason=Grund)
        await ctx.sendEmbed(title="Benutzer Gemeldet", color=self.color, fields=[("Betroffener",member.mention),("Grund",Grund)])
        return


    @commands.command(
        brief='Erhalte alle Reports',
        description='Benutze diesen Command um alle Reports zu sehen',
        aliases=["getreports","getreport"],
        help="Mit /getreports [Member] kannst du alle Reports ansehen.",
        usage="[Member]"
        )
    @commands.has_any_role("Moderator","Supporter","Admin")
    @commands.guild_only()
    async def reports(self, ctx, member:Member=None):
        if member == None:
            EMBED = Embed(title="Server Reports", color=self.color)
            EMBED.set_footer(text=f'Angefordert von {ctx.author.name}',icon_url=ctx.author.avatar_url)
            for user in await ctx.database.getReports():
                EMBED.add_field(**user)
            await ctx.send(embed=EMBED)
        else:
            EMBED = Embed(title="User Reports", color=self.color, description=("User: "+member.mention))
            EMBED.set_footer(text=f'Angefordert von {ctx.author.name}',icon_url=ctx.author.avatar_url)
            for report in await ctx.database.getReports(dc_user=member):
                EMBED.add_field(**report)
            await ctx.send(embed=EMBED)
        return

    
    @commands.group(
        brief="Lasse jemanden Commands für dich ausführen",
        description="Überlasse jemanden, Commands als dich auszuführen.",
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
        if not await ctx.database._has_permissions(id_1=str(ctx.author.id), id_2=str(member.id), typ="remote_permission"):
            await ctx.database._create_permissions(id_1=str(ctx.author.id), id_2=str(member.id), typ="remote_permission")
            await ctx.sendEmbed(
                title="Benutzer erlaubt",
                color=self.color,
                description=member.mention+" darf nun Befehle für dich ausführen!"
            )
        else:
            raise commands.BadArgument("Dieser Benutzer darf bereits Befehle für dich ausführen!")

    @remote.command(
        name="allowraw",
        brief="Füge eine erlaubte ID hinzu",
        aliases=["allowwebhook", "++", "addraw"],
        usage="<ID>",
        help="Dies wird gebraucht, um Webhooks die Erlaubnis zu geben, Commands für dich auszuführen. Dieser Befehl kann ziemlich viel Mist machen, vorallem wenn du Rechte hast! Also pass auf!",
        hidden=True,
    )
    async def remote_allowraw(self, ctx, id: int):
        if not await ctx.database._has_permissions(id_1=str(ctx.author.id), id_2=str(id), typ="remote_permission"):
            await ctx.database._create_permissions(id_1=str(ctx.author.id), id_2=str(id), typ="remote_permission")
            await ctx.sendEmbed(
                title="ID erlaubt",
                color=self.color,
                description=str(id)+" darf nun Befehle für dich ausführen!"
            )
        else:
            raise commands.BadArgument("Diese ID darf bereits Befehle für dich ausführen!")

    @remote.command(
        name="disallow",
        brief="Entferne einen erlaubten Spieler",
        aliases=["-", "remove"],
        usage="<Member>",
    )
    async def remote_disallow(self, ctx, member: typing.Union[Member, User]):
        if await ctx.database._has_permissions(id_1=str(ctx.author.id), id_2=str(member.id), typ="remote_permission"):
            await ctx.database._delete_permissions(id_1=str(ctx.author.id), id_2=str(member.id), typ="remote_permission")
            await ctx.sendEmbed(
                title="Benutzer verboten", 
                color=self.color,
                description=member.mention+" darf nun nicht mehr Befehle für dich ausführen!"
            )
        else:
            raise commands.BadArgument("Dieser Benutzer steht nicht auf deiner Liste!")

    @remote.command(
        name="disallowraw",
        brief="Entferne eine erlaubte ID",
        aliases=["--", "removeraw"],
        usage="<Member>",
        help="Dies wird gebraucht, um Webhooks die Erlaubnis zu geben, Commands für dich auszuführen.",
        hidden=True,
    )
    async def remote_disallowraw(self, ctx, id: int):
        if await ctx.database._has_permissions(id_1=str(ctx.author.id), id_2=str(id), typ="remote_permission"):
            await ctx.database._delete_permissions(id_1=str(ctx.author.id), id_2=str(id), typ="remote_permission")
            await ctx.sendEmbed(
                title="ID verboten",
                color=self.color,
                description=str(id)+" darf nun nicht mehr Befehle für dich ausführen!"
            )
        else:
            raise commands.BadArgument(
                "Diese ID steht nicht auf deiner Liste!")

    @remote.command(
        name="list",
        brief="Liste die erlaubten Spieler auf",
        aliases=[],
        usage=""
    )
    async def remote_list(self, ctx):
        perms = await ctx.database._list_permissions(id_1=str(ctx.author.id), typ="remote_permission")
        await ctx.sendEmbed(
            title="Benutzerliste",
            color=self.color,
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
        if await ctx.database._has_permissions(id_1=str(member.id), id_2=str(ctx.author.id), typ="remote_permission") or await ctx.database._has_permissions(id_1=str(member.id), id_2=str(ctx.message.webhook_id), typ="remote_permission"):
            await ctx.invoke_as(member, command, *args)
        else:
            raise commands.BadArgument("Du darfs keine Befehle als diesen Benutzer ausführen!   ")

def setup(bot):
    bot.add_cog(Support(bot))
