from discord.ext import commands
from discord import User, TextChannel, utils
from datetime import datetime
import typing

from discordbot.config import INVITE_OWNER, INVITE_BOT, SPAM_ALLOWED
#from discordbot.errors import ErrorMessage

REGELN = {
    "1) Verhalten":
        [
            "Sei nett zu anderen Leuten und behandle sie so, wie auch du behandelt werden möchtest!", 
            "Beleidige keine anderen Leute!",
            "Benutze anständige Sprache!",
            "Bleib beim Thema!",
        ],
    "2) Text":
        [
            "Spamming ist verboten!", 
            "Werbung ohne Erlaubnis eines Administrators ist verboten!",
        ],
    "3) Ton":
        [
            "Benutze keinen Stimmverzerrer!", 
            "Mache keine unnötigen Hintergrundgeräusche!", 
            "Channel Hopping bitte unterlassen!", 
            "Sprachaufnahmen sind nur mit Erlaubnis aller Teilnehmer gestattet!",
        ],
    "4) NSFW":
        [
            "Anstössige Inhalte ausserhalb NSFW-Kanälen werden sofort gelöscht und der Autor mit einem Bann/Mute bestraft!", 
        ],
    "5) Sicherheit":
        [
            "Anweisungen von Moderatoren, Supportern und Admins müssen befolgt werden!",
            "Falls jemand ohne Grund nach deinen persönlichen Daten fragt, ignoriere bitte die Nachricht und meldet sie einem Admin oder dem Serverbesitzer! Bitte melde den Benutzer ebenfalls bei Discord!",
            "Sende nie jemandem euer Passwort!",
        ],
    "6) Empfehlungen":
        [
            "Habe Spass!",
        ],
}


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
        embed = ctx.getEmbed(title="Aktueller Ping", fields=[("Ping", str(int(( datetime.timestamp( datetime.now() ) - start ) * 1000))+"ms")])
        await msg.edit(embed=embed)
        return

    @commands.command(
        brief="Schreibt dir nach",
        description="Gibt den angegebenen Text zurück",
        aliases=["copy"],
        help="Benutze /say <Text> und der Bot schickt dir den Text zurück",
        usage="<Text>"
        )
    async def say(self, ctx, text:str, *args):
        txt = " ".join((text,)+args)
        await ctx.send(txt)

    @commands.command(
        brief="Siehe den Avatar eines Benutzers",
        description="Erhalte den Standardavatar und Avatar eines Benutzers",
        aliases=["defaultavatar"],
        help="Benutze /avatar <User> und du siehst, welchen Avatar die Person hat",
        usage="<User>"
        )
    async def avatar(self, ctx, user:User):
        await ctx.sendEmbed(title="Avatar", fields=[("Benutzer",user.mention),("Standardavatar",user.default_avatar)], thumbnailurl=str(user.avatar_url))


    @commands.command(
        brief="Spamt jemanden voll",
        description="Schickt jemandem ein paar Nachrichten",
        aliases=["troll"],
        help="Benutze /spam <User> und der Bot spamt den User voll",
        usage="<Kanal/Benutzer> [Anzahl<=10] [Text]"
        )
    async def spam(self, ctx, what:typing.Union[TextChannel,User]=None, anzahl:int=5, *args):
        if SPAM_ALLOWED:
            anzahl = int(anzahl if anzahl <= 10 else 10)
            text = str(" ".join(str(i) for i in args))
            empty = not (len(text) > 0 and not text == (" "*len(text)))
            for _ in range(anzahl):
                if not empty:
                    await what.send(text+" von "+ctx.author.mention)
                else:
                    await what.send("Spam"+" von "+ctx.author.mention)
            return
        else:
            await ctx.invoke(ctx.bot.get_command("regeln"))
            await ctx.sendEmbed(
                title="Spam verboten",
                description="Schon vergessen, dass Spam laut Regeln verboten ist? Hast du wirklich gedacht, ich breche meine eigenen Regeln?"
            )
            if ctx.guild is not None:
                await ctx.database.createReport(dc_user=ctx.author, reason="Tried to use /spam", reportedby_dc_user=ctx.guild.me)


    @commands.command(
        brief="Zeigt die Regeln",
        description="Schickt die Regeln in den Chat",
        aliases=["rules"],
        help="Benutze /regeln um dich oder jemand anderes daran zu erinnern!",
        usage="<Kanal/Benutzer> [Anzahl<100] [Text]"
        )
    async def regeln(self,ctx):
        EMBED = self.bot.getEmbed(title="Regeln", description="Das Nichtbeachten der Regeln kann mit einem Ban, Kick oder Mute bestraft werden!")
        owner = self.bot.get_user(self.bot.owner_id)
        if owner:
            EMBED.set_footer(text=f'Besitzer dieses Bots ist {owner.name}#{owner.discriminator}',icon_url=owner.avatar_url)
        for kategorie in REGELN:
            EMBED.add_field(name=kategorie,value="```nimrod\n- "+ ("\n- ".join(regel for regel in REGELN[kategorie])) +"```",inline=False)
        await ctx.send(embed=EMBED)


    @commands.command(
        brief="Erhalte eine Einladung",
        description="Schickt dir eine Einladung zum Server und Bot",
        aliases=["invitelink"],
        help="Benutze /invite und erhalte eine Einladung zu diesem Server, dem Bot-Server und einen Link, um den Bot zum eigenen Server hinzuzufügen",
        usage=""
        )
    async def invite(self,ctx):
        invite = None
        if ctx.guild:
            try:
                invite = await ctx.guild.vanity_invite()
            except:
                try:
                    invite = utils.get(list(await ctx.guild.invites()), max_age=0, max_uses=0)
                    if not invite:
                        invite = await ctx.channel.create_invite()
                except:
                    invite = None

        if invite:
            await ctx.sendEmbed(title="Einladungen", fields=[("Dieser Server", invite.url or "Unbekannt"), ("Bot Owner Server", INVITE_OWNER), ("Bot", INVITE_BOT)])
        else:
            await ctx.sendEmbed(title="Einladungen", fields=[("Bot Owner Server",INVITE_OWNER), ("Bot",INVITE_BOT)])

def setup(bot):
    bot.add_cog(Basic(bot))
