from discord.ext import commands
from discord import User, TextChannel, utils, DiscordException
from datetime import datetime
import typing

from discordbot.config import INVITE_OWNER, INVITE_BOT, REGELN
#from discordbot.errors import ErrorMessage


class Basic(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.color = 0xffffff

    @commands.command(
        brief="Zeigt den Ping des Bots an",
        description='Gibt den aktuellen Ping zurück',
        aliases=['p'],
        help="Gib einfach /ping ein und warte ab.",
        usage=""
    )
    async def ping(self, ctx):
        start = datetime.timestamp(datetime.now())
        msg = await ctx.sendEmbed(title="Aktueller Ping", fields=[("Ping", "Berechnen...")])
        embed = ctx.getEmbed(title="Aktueller Ping", fields=[("Ping", str(
            int((datetime.timestamp(datetime.now()) - start) * 1000))+"ms")])
        await msg.edit(embed=embed)

    @commands.command(
        brief="Schreibt dir nach",
        description="Gibt den angegebenen Text zurück",
        aliases=["copy"],
        help="Benutze /say <Text> und der Bot schickt dir den Text zurück",
        usage="<Text>"
    )
    @commands.has_permissions(manage_messages=True)
    async def say(self, ctx, text: str, *args):
        txt = " ".join((text,)+args)
        await ctx.send(txt)

    @commands.command(
        brief="Spamt einen Benutzer oder Textkanal voll",
        description="Schickt jemandem 'ein paar' Nachrichten",
        aliases=["troll"],
        help="Benutze /spam <Kanal/Benutzer> und der Bot spamt den User voll",
        usage="<Kanal/Benutzer> [Text]"
    )
    async def spam(self, ctx):
        await ctx.invoke(ctx.bot.get_command("regeln"))
        await ctx.sendEmbed(
            title="Spam verboten",
            description="Schon vergessen, dass Spam laut Regeln verboten ist? "
                        "Hast du wirklich gedacht, ich breche meine eigenen Regeln? "
                        "Scheinbar magst du Trolls, [das](https://www.youtube.com/watch?v=dQw4w9WgXcQ) "
                        "sollte dir also gefallen."
        )
        if ctx.guild is not None:
            report = await ctx.database.createReport(dc_user=ctx.author, reason="Tried to use /spam", reportedby_dc_user=ctx.guild.me)
            cog = ctx.bot.get_cog("Support")
            await cog.send_report(ctx, report)

    @commands.command(
        brief="Zeigt die Regeln",
        description="Schickt die Regeln in den Chat",
        aliases=["rules"],
        help="Benutze /regeln um dich oder jemand anderes daran zu erinnern!",
        usage="<Kanal/Benutzer> [Anzahl<100] [Text]"
    )
    async def regeln(self, ctx):
        EMBED = self.bot.getEmbed(
            title="Regeln", description="Das Nichtbeachten der Regeln kann mit einem Ban, Kick oder Mute bestraft werden!")
        owner = self.bot.get_user(self.bot.owner_id)
        if owner:
            EMBED.set_footer(
                text=f'Besitzer dieses Bots ist {owner.name}#{owner.discriminator}', icon_url=owner.avatar_url)
        for kategorie in REGELN:
            EMBED.add_field(name=kategorie, value="```nimrod\n- " + (
                "\n- ".join(regel for regel in REGELN[kategorie])) + "```", inline=False)
        await ctx.send(embed=EMBED)

    @commands.command(
        brief="Erhalte eine Einladung",
        description="Schickt dir eine Einladung zum Server und Bot",
        aliases=["invitelink"],
        help="Benutze /invite und erhalte eine Einladung zu diesem Server, dem Bot-Server und einen Link, um den Bot zum eigenen Server hinzuzufügen",
        usage=""
    )
    async def invite(self, ctx):
        invite = None
        if ctx.guild:
            try:
                invite = await ctx.guild.vanity_invite()
            except DiscordException:
                try:
                    invite = utils.get(list(await ctx.guild.invites()), max_age=0, max_uses=0)
                    if not invite:
                        invite = await (ctx.guild.system_channel or ctx.channel).create_invite()
                except DiscordException:
                    invite = None

        gc = len(ctx.bot.guilds)
        desc = f"Ich bin bereits auf {gc} Guild(s)! Du möchtest, dass diese Zahl steigt? Kein Problem! Du möchtest Leute auf diesen Server einladen? Auch kein Problem!"

        inviteurl = invite.url if invite and invite.url else None
        await ctx.sendEmbed(title="Einladungen", description=desc, fields=[("Dieser Server", f"[Beitreten]({inviteurl})" if inviteurl else "Unbekannt"), ("Bot Owner Server", f"[Beitreten]({INVITE_OWNER})"), ("Bot", f"[Beitreten]({INVITE_BOT})")])


def setup(bot):
    bot.add_cog(Basic(bot))
