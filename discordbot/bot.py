from datetime import datetime

from discord import (Activity, ActivityType, Embed, Game, HTTPException,
                     Status, Streaming)
from discord.ext import commands
from rich.traceback import install as install_traceback

from discordbot.botmodules import apis, serverdata

install_traceback()
from rich.pretty import install as install_pretty

install_pretty()

#

extensionfolder = "discordbot.botcmds"
extensions = ['basic','support','moderation','games','help','channels','music','owneronly','converters','embedgenerator']
all_prefixes = ["/","!","$",".","-",">","?"]

# Own functions



# Own classes

class MyContext(commands.Context):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.apis = apis

        if self.guild is not None:
            self.data = serverdata.Server.getServer(self.guild.id)

            self.database = serverdata.DjangoConnection(self.author, self.guild)

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

    async def tick(self, value=True):
        emoji = '\N{WHITE HEAVY CHECK MARK}' if value else '\N{CROSS MARK}'
        try:
            await self.message.add_reaction(emoji)
        except HTTPException:
            pass

    async def send_help(self):
        await self.invoke(self.bot.get_command("help"), self.invoked_with)


class MyBot(commands.Bot):
    def __init__(self, **kwargs):
        super().__init__(self.get_command_prefix, **kwargs)

    def get_command_prefix(self, client, message):
        if message.guild:
            prefixes = ['/']
        else:
            prefixes = all_prefixes
        return commands.when_mentioned_or(*prefixes)(client, message)
        
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
    description='Das ist eine Beschreibung!',
    case_insensitive=True,
    activity=Activity(type=ActivityType.listening, name="/help"),
    status=Status.idle,
    help_command=None,
)

# Events

from discordbot.botevents import setup

setup(bot)

@bot.event
async def on_ready():
    print(f"[Bot] - Logged in as '{bot.user.name}' - '{bot.user.id}'")
    for extension in extensions:
        try:
            bot.load_extension(extensionfolder+"."+extension)
        except commands.errors.ExtensionAlreadyLoaded:
            pass
    return

# Hidden commands

@bot.command(aliases=["."], hidden=True)
async def destroy(ctx):
    pass


# Start

def run(TOKEN):
    bot.run(TOKEN, bot=True, reconnect=True)

if __name__ == "__main__":
    print("[Bot] - You must run this bot via your manage.py file: python3.8 manage.py run-discorbot")
