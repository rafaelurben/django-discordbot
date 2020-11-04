from discord.ext import commands
from discord import Game, Streaming, Activity, ActivityType, Status, Member, User, TextChannel, VoiceChannel, Role, Invite, Game, Emoji, PartialEmoji, Colour

from discordbot.bot import extensions, extensionfolder

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

class Owneronly(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.color = 0x000000


    @commands.command(
        brief="Lade die Bot-Extensionen neu",
    )
    @commands.is_owner()
    async def reload(self, ctx, extension:str=None):
        msg = await ctx.sendEmbed(title="Reload", color=self.color, fields=[("Status", "Reloading")])
        EMBED = ctx.getEmbed(title="Reload", color=self.color, fields=[])
        if extension in extensions:
            print("[Bot] - Reloading"+extension+"...")
            try:
                self.bot.unload_extension(extensionfolder+"."+extension)
            except:
                pass
            try:
                self.bot.load_extension(extensionfolder+"."+extension)
            except commands.errors.ExtensionAlreadyLoaded:
                pass
            EMBED.add_field(name="Status",value="Reloaded category "+extension.upper()+"!")
        else:
            print("[Bot] - Reloading all extensions...")
            for extension in extensions:
                try:
                    self.bot.unload_extension(extensionfolder+"."+extension)
                except:
                    pass
                try:
                    self.bot.load_extension(extensionfolder+"."+extension)
                except commands.errors.ExtensionAlreadyLoaded:
                    pass
            EMBED.add_field(name="Status",value="Reloaded all categories!")
        await msg.edit(embed=EMBED)
        print("[Bot] - Reload completed!")


    @commands.command(
        brief="Stoppe den Bot",
    )
    @commands.is_owner()
    async def stopbot(self, ctx):
        await ctx.sendEmbed(title="Stop", color=self.color, fields=[("Status", "Gestoppt")])
        await self.bot.logout()


    @commands.command(
        brief="Ändere den Status des Bots",
        usage="<Status> [Aktivität [Argumente(e)]]",
    )
    @commands.is_owner()
    async def status(self, ctx, STATUS:str="", ACTIVITY:str="", arg1:str="", *args):
        arg2 = " ".join(args)
        status = None
        activity = None
        if STATUS.lower() in ["on","online","green"]:
            status = Status.online
        elif STATUS.lower() in ["off","offline","invisible","grey"]:
            status = Status.invisible
        elif STATUS.lower() in ["dnd","donotdisturb","do_not_disturb","bittenichtstören","red"]:
            status = Status.dnd
        elif STATUS.lower() in ["idle","abwesend","orange","yellow"]:
            status = Status.idle

        if ACTIVITY.lower() in ["playing","spielt","game","play"]:
            activity=Game(name=arg1+" "+arg2)
        elif ACTIVITY.lower() in ["streaming","streamt","stream","live","twitch"]:
            activity=Streaming(url="https://twitch.tv/"+arg1, name=arg2)
        elif ACTIVITY.lower() in ["listening","listen","hört","hören","song"]:
            activity=Activity(type=ActivityType.listening, name=arg1+" "+arg2)
        elif ACTIVITY.lower() in ["watching","watch","schaut","video"]:
            activity=Activity(type=ActivityType.watching, name=arg1+" "+arg2)

        if status is not None or activity is not None:
            await ctx.bot.change_presence(status=status, activity=activity)
        else:
            await ctx.sendEmbed(title="Status ändern", color=0xff0000, inline=False,
            description="""
            **Syntax:**
            /status <STATUS> [AKTIVITÄT [ARGUMENT(E)]]

            **Mögliche Status:**
            on/online (Online)
            idle (Abwesend)
            dnd (Bitte nicht stören)
            off/offline (Unsichtbar)

            **Mögliche Aktivitäten:**
            spielt <SPIEL>
            streamt <TWITCH-NAME> <SPIEL>
            hört <SONG>
            schaut <VIDEO>
            """
            )

    @commands.command(
        brief="Führe einen Command als jemanden anderes aus",
        usage="<Member> <Command> [Argumente]",
        aliases=["runas"],
        help="Falls Unterbefehle verwendet werden, benutze bitte befehl_unterbefehl als Command",
    )
    @commands.is_owner()
    @commands.guild_only()
    async def sudo(self, ctx, member: Member, command: str, *args):
        _command = command.replace("_", " ")
        cmd = self.bot.get_command(_command)
        ctx.message.content = ctx.prefix+_command+ctx.message.content.split(command)[1]
        ctx.message.author = member
        ctx.author = member
        ctx.database = type(ctx.database)(ctx.author, ctx.guild)
        annotations = cmd.callback.__annotations__
        annotations.pop("return", None)
        arguments = list(args)
        for i, cls in enumerate(annotations.values()):
            if len(arguments) > i:
                if cls in CONVERTERS:
                    arguments[i] = await CONVERTERS[cls]().convert(ctx, arguments[i])
                else:
                    arguments[i] = cls(arguments[i])
        await ctx.invoke(cmd, *arguments)

def setup(bot):
    bot.add_cog(Owneronly(bot))
