from discord.ext import commands
from discord import Game, Streaming, Activity, ActivityType, Status
from discordbot.bot import extensions, extensionfolder


class Owneronly(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.color = 0x000000


    @commands.command()
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


    @commands.command()
    @commands.is_owner()
    async def stopbot(self, ctx):
        await ctx.sendEmbed(title="Stop", color=self.color, fields=[("Status", "Gestoppt")])
        await self.bot.logout()


    @commands.command()
    @commands.is_owner()
    async def status(self, ctx, STATUS:str="", ACTIVITY:str="", arg1:str=""):
        arg2 = ctx.getargs()
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
            /status <STATUS> [AKTIVITÄT] [ARGUMENTE]

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


def setup(bot):
    bot.add_cog(Owneronly(bot))
