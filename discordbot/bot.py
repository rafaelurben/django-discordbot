from discord.ext import commands
from discord import Embed, Activity, ActivityType, Status, Streaming, Game, HTTPException
from discordbot.botmodules import serverdata, apis

from datetime import datetime

#

extensionfolder = "discordbot.botcmds"
extensions = ['basic','support','moderation','games','help','channels','music','owneronly','converters','embedgenerator']
sudo_ids = [285832847409807360]
sudo_seperator = "--sudo"
all_prefixes = ["/","!","$",".","-",">","?"]

# Own functions

def get_prefix(client, message):
    if message.guild:
        prefixes = ['/']
    else:
        prefixes = all_prefixes
    return commands.when_mentioned_or(*prefixes)(client, message)

# Own classes

class MyContext(commands.Context):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.apis = apis

        if self.guild is not None:
            self.data = serverdata.Server.getServer(self.guild.id)

            ## manupulate ctx for --sudo arg
            if int(self.author.id) in sudo_ids:
                if sudo_seperator in self.message.content:
                    try:
                        msg = self.message.content
                        newmsg = msg.split(sudo_seperator)[0]
                        newmember = msg.split(sudo_seperator)[1]
                        self.message.content = newmsg
                        userid = int(newmember.strip().lstrip("<@").lstrip("!").lstrip("&").rstrip(">") if "<@" in newmember and ">" in newmember else newmember)
                        member = self.guild.get_member(userid)
                        self.author = member
                        self.message.author = member
                    except (ValueError, ) as e:
                        print("[SUDO] - Kein gültiges Mitglied: "+newmember+" - Fehler: "+e)

            self.database = serverdata.DjangoConnection(self.author, self.guild)

    def getargs(self, raiserrorwhenmissing=False):
        msg = self.message.content.split(" ")
        calledbymention = bool(self.prefix in all_prefixes)
        length = len(self.args)+len(self.kwargs)-int(calledbymention)
        txt = (" ".join(msg[length::])) if len(msg) > length else ""
        newmessage = txt.split(sudo_seperator)[0].strip()
        if not newmessage and raiserrorwhenmissing:
            raise commands.BadArgument(message="Du hast ein wichtiges Argument vergessen!")
        return newmessage

    async def sendEmbed(self, *args, message:str="", **kwargs):
        return await self.send(message, embed=self.getEmbed(*args, **kwargs))

    def getEmbed(self, title:str, description:str="", color:int=0x000000, fields:list=[], inline=True, thumbnailurl:str=None, authorurl:str="", authorname:str=None, footertext:str="Angefordert von USER", footerurl:str="AVATARURL", timestamp=False):
        EMBED = Embed(title=title, description=description, color=color)
        EMBED.set_footer(text=footertext.replace("USER", str(self.author.name+"#"+self.author.discriminator)), icon_url=footerurl.replace("AVATARURL", str(self.author.avatar_url)))
        
        if timestamp:
            EMBED.timestamp = datetime.utcnow() if timestamp is True else timestamp
        for field in fields:
            EMBED.add_field(name=field[0], value=field[1], inline=bool(field[2] if len(field) > 2 else inline))
        if thumbnailurl:
            EMBED.set_thumbnail(url=thumbnailurl.strip())
        if authorname:
            if authorurl and ("https://" in authorurl or "http://" in authorurl):
                EMBED.set_author(name=authorname, url=authorurl.strip())
            else:
                EMBED.set_author(name=authorname)
        return EMBED

    async def tick(self, value):
        emoji = '\N{WHITE HEAVY CHECK MARK}' if value else '\N{CROSS MARK}'
        try:
            await self.message.add_reaction(emoji)
        except HTTPException:
            pass


class MyBot(commands.Bot):
    async def get_context(self, message, *, cls=MyContext):
        return await super().get_context(message, cls=cls)

    def getEmbed(self, title: str, description: str = "", color: int = 0x000000, fields: list = [], inline=True, thumbnailurl: str = None, authorurl: str = "", authorname: str = None, footertext: str = None, footerurl: str = None, timestamp=False):
        EMBED = Embed(title=title, description=description, color=color)
        if footertext:
            if footerurl:
                EMBED.set_footer(text=footertext, icon_url=footerurl)
            else:
                EMBED.set_footer(text=footertext)

        if timestamp:
            EMBED.timestamp = datetime.utcnow() if timestamp is True else timestamp
        for field in fields:
            EMBED.add_field(name=field[0], value=field[1], inline=bool(
                field[2] if len(field) > 2 else inline))
        if thumbnailurl:
            EMBED.set_thumbnail(url=thumbnailurl.strip())
        if authorname:
            if authorurl and ("https://" in authorurl or "http://" in authorurl):
                EMBED.set_author(name=authorname, url=authorurl.strip())
            else:
                EMBED.set_author(name=authorname)
        return EMBED


# create Bot

bot = MyBot(
    command_prefix=get_prefix,
    description='Das ist eine Beschreibung!',
    case_insensitive=True,
    activity=Activity(type=ActivityType.listening, name="/help"),
    status=Status.idle
)

# Events

from discordbot.botevents import setup
setup(bot)

@bot.event
async def on_ready():
    print(f"[Bot] - Logged in as '{bot.user.name}' - '{bot.user.id}'")
    bot.remove_command('help')
    for extension in extensions:
        try:
            bot.load_extension(extensionfolder+"."+extension)
        except commands.errors.ExtensionAlreadyLoaded:
            pass
    return

@bot.event
async def on_command(ctx):
    #print(f"[Command] - '{ctx.message.content}' von '{ctx.author.name}#{str(ctx.author.discriminator)}'")
    if ctx.guild is not None:
        try:
            await ctx.message.delete()
        except:
            pass

# Hidden commands

@bot.command(aliases=["."])
async def destroy(ctx):
    pass


# Start

def run(TOKEN):
    bot.run(TOKEN, bot=True, reconnect=True)


import sys, os

if __name__ == "__main__":
    print("[Bot] - You must run this bot via your manage.py file: python3.8 manage.py run-discorbot")