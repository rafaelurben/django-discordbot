import typing
from datetime import datetime

from discord import Activity, ActivityType, Embed, Game, HTTPException, Status, Member, User, TextChannel, VoiceChannel, Role, Invite, Game, Emoji, PartialEmoji, Colour
from discord.ext import commands

from discordbot.botmodules import apis, serverdata
from discordbot.config import EXTENSIONFOLDER, EXTENSIONS, ALL_PREFIXES, MAIN_PREFIXES


from rich.traceback import install as install_traceback
install_traceback()
from rich.pretty import install as install_pretty
install_pretty()

#

CONVERTERS = {
    Member: commands.MemberConverter,
    User: commands.UserConverter,
    TextChannel: commands.TextChannelConverter,
    VoiceChannel: commands.VoiceChannelConverter,
    Role: commands.RoleConverter,
    Invite: commands.InviteConverter,
    Game: commands.GameConverter,
    Emoji: commands.EmojiConverter,
    PartialEmoji: commands.PartialEmojiConverter,
    Colour: commands.ColourConverter
}

# Own classes

class MyContext(commands.Context):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.apis = apis
        self.database = serverdata.DjangoConnection(self.author, self.guild)

        if self.guild is not None:
            self.data = serverdata.Server.getServer(self.guild.id)

    async def sendEmbed(self, *args, message:str="", **kwargs):
        return await self.send(message, embed=self.getEmbed(*args, **kwargs))

    def getEmbed(self, title:str, description:str="", color:int=0x000000, fields:list=[], inline=True, thumbnailurl:str=None, authorurl:str="", authorname:str=None, footertext:str="Angefordert von USER", footerurl:str="AVATARURL", timestamp=False):
        EMBED = Embed(title=title, description=description, color=color)
        EMBED.set_footer(text=footertext.replace("USER", str(self.author.name+"#"+self.author.discriminator)), icon_url=footerurl.replace("AVATARURL", str(self.author.avatar_url)))
        
        if timestamp:
            EMBED.timestamp = datetime.utcnow() if timestamp is True else timestamp
        for field in fields:
            EMBED.add_field(name=field[0], value=(field[1][:1018]+" [...]" if len(field[1]) > 1024 else field[1]), inline=bool(field[2] if len(field) > 2 else inline))
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

    async def invoke_as(self, member, command, *args):
        _command = command.replace("_", " ")
        cmd = self.bot.get_command(_command)
        if cmd is None:
            raise commands.BadArgument(f"Der Befehl `{ _command }` wurde nicht gefunden! \nPS: Benutze im Command bitte kein Prefix!")
        self.message.content = self.prefix+_command+self.message.content.split(command)[1]
        self.message.author = member
        self.author = member
        self.database = type(self.database)(self.author, self.guild)
        annotations = cmd.callback.__annotations__
        annotations.pop("return", None)
        arguments = list(args)
        for i, cls in enumerate(annotations.values()):
            if len(arguments) > i:
                if cls in CONVERTERS:
                    arguments[i] = await CONVERTERS[cls]().convert(self, arguments[i])
                else:
                    arguments[i] = cls(arguments[i])
        await self.invoke(cmd, *arguments)


class MyBot(commands.Bot):
    def __init__(self, **kwargs):
        super().__init__(self.get_command_prefix, **kwargs)

    def get_command_prefix(self, client, message):
        if message.guild:
            prefixes = MAIN_PREFIXES
        else:
            prefixes = ALL_PREFIXES
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
            EMBED.add_field(name=field[0], value=(field[1][:1018]+" [...]" if len(field[1]) > 1024 else field[1]), inline=bool(
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
    for extension in EXTENSIONS:
        try:
            bot.load_extension(EXTENSIONFOLDER+"."+extension)
        except commands.errors.ExtensionAlreadyLoaded:
            pass
    return
    
# Start

def run(TOKEN):
    bot.run(TOKEN, bot=True, reconnect=True)

if __name__ == "__main__":
    print("[Bot] - You must run this bot via your manage.py file: python3.8 manage.py run-discorbot")
