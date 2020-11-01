from discord.ext import commands
from discord import Embed, User, TextChannel, utils
from datetime import datetime as d
import typing

REGELN = {
    "1) Sei anständig":
        [
            "Sei nett zu anderen Leuten und behandle sie so, wie auch du behandelt werden möchtest!"
        ],
    "2) Text":
        [
            "Spamming ist verboten!","Werbung ist verboten!"
        ],
    "3) NSFW":
        [
            "Anstössige Inhalte werden sofort gelöscht und der Autor mit einem Bann bestraft!","Hier sind auch Kinder und Jugendliche auf diesem Server!"
        ],
    "4) Sicherheit":
        [
            "Anweisungen von Moderatoren, Supportern und Admins müssen befolgt werden!","Falls jemand ohne Grund nach persönlichen Daten fragt, ignoriert bitte die Nachricht und meldet sie einem anderen Admin.","Sendet nie jemandem euer Passwort!"
        ],
    "5) Ton":
        [
            "Benutzt keinen Stimmverzerrer!", "Macht keine unnötigen Hintergrundgeräusche!"
        ],
    "6) Empfehlungen":
        [
            "Habt Spass!"
        ],
    "7) Sprachkanäle":
        [
            "Channel Hopping unterlassen"
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
        start = d.timestamp(d.now())
        msg = await ctx.sendEmbed(title="Aktueller Ping", color=self.color, fields=[("Ping", "Berechnen...")])
        embed = ctx.getEmbed(title="Aktueller Ping", color=self.color, fields=[("Ping", str(int(( d.timestamp( d.now() ) - start ) * 1000))+"ms")])
        await msg.edit(embed=embed)
        return

    @commands.command(
        brief="Schreibt dir nach",
        description="Gibt den angegebenen Text zurück",
        aliases=["copy"],
        help="Benutze /say <Text> und der Bot schickt dir den Text zurück",
        usage="<Text>"
        )
    async def say(self,ctx,Text:str):
        txt = Text+" "+ctx.getargs()
        await ctx.send(txt)

    @commands.command(
        brief="Siehe den Avatar eines Benutzers",
        description="Erhalte den Standardavatar und Avatar eines Benutzers",
        aliases=["defaultavatar"],
        help="Benutze /avatar <User> und du siehst, welchen Avatar die Person hat",
        usage="<User>"
        )
    async def avatar(self,ctx,user:User):
        await ctx.sendEmbed(title="Avatar", fields=[("Benutzer",user.mention),("Standardavatar",user.default_avatar)], thumbnailurl=str(user.avatar_url))


    # @commands.command(
    #     brief="Spamt jemanden voll",
    #     description="Schickt jemandem ein paar Nachrichten",
    #     aliases=["troll"],
    #     help="Benutze /spam <User> und der Bot spamt den User voll",
    #     usage="<Kanal/Benutzer> [Anzahl<=10] [Text]"
    #     )
    # async def spam(self,ctx,what: typing.Union[TextChannel,User],anzahl:int=5,*args):
    #     anzahl = int(anzahl if anzahl <= 10 else 10)
    #     text = str(" ".join(str(i) for i in args))
    #     empty = not (len(text) > 0 and not text == (" "*len(text)))
    #     for i in range(anzahl):
    #         if not empty:
    #             await what.send(text+" von "+ctx.author.name+"#"+ctx.author.discriminator)
    #         else:
    #             await what.send("Spam"+" von "+ctx.author.name+"#"+ctx.author.discriminator)
    #     return


    @commands.command(
        brief="Zeigt die Regeln",
        description="Schickt die Regeln in den Chat",
        aliases=["rules"],
        help="Benutze /regeln um dich oder jemand anderes daran zu erinnern!",
        usage="<Kanal/Benutzer> [Anzahl<100] [Text]"
        )
    async def regeln(self,ctx):
        EMBED = Embed(title="Regeln", color=self.color, description="Das Nichtbeachten der Regeln kann mit einem Ban, Kick oder Mute bestraft werden!")
        owner = self.bot.get_user(self.bot.owner_id)
        if owner:
            EMBED.set_footer(text=f'Besitzer dieses Bots ist {owner.name}#{owner.discriminator}',icon_url=owner.avatar_url)
        for kategorie in REGELN:
            EMBED.add_field(name=kategorie,value="```nimrod\n- "+ ("\n- ".join(regel for regel in REGELN[kategorie])) +"```",inline=False)
        msg = await ctx.send(embed=EMBED)


    @commands.command(
        brief="Erhalte eine Einladung",
        description="Schickt dir eine Einladung zum Server und Bot",
        aliases=["invitelink"],
        help="Benutze /invite und erhalte eine Einladung zu diesem Server, dem Bot-Server und einen Link, um den Bot zum eigenen Server hinzuzufügen",
        usage=""
        )
    @commands.bot_has_permissions(manage_guild = True)
    async def invite(self,ctx):
        try:
            invite = await ctx.guild.vanity_invite()
        except:
            invite = utils.get(list(await ctx.guild.invites()), max_age=0, max_uses=0, temporary=False)
            if not invite:
                invite = await ctx.channel.create_invite()
        await ctx.sendEmbed(title="Einladungen", color=self.color, fields=[("Dieser Server", invite.url),("Bot Server","https://rebrand.ly/RUdiscord"),("Bot","https://rebrand.ly/RUdiscordbot")])

def setup(bot):
    bot.add_cog(Basic(bot))
