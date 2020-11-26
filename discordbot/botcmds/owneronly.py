from discord.ext import commands
from discord import Game, Streaming, Activity, ActivityType, Status, Member, User, TextChannel, VoiceChannel, Role, Invite, Game, Emoji, PartialEmoji, Colour

from discordbot.config import EXTENSIONS, EXTENSIONFOLDER

import typing

class Owneronly(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.color = 0x000000


    @commands.command(
        brief="Lade die Bot-Extensionen neu",
    )
    @commands.is_owner()
    async def reload(self, ctx, extension:str=None):
        msg = await ctx.sendEmbed(title="Reload", fields=[("Status", "Reloading")])
        EMBED = ctx.getEmbed(title="Reload", fields=[])
        if extension in EXTENSIONS:
            print("[Bot] - Reloading '"+extension+"' extension...")
            try:
                self.bot.unload_extension(EXTENSIONFOLDER+"."+extension)
            except commands.errors.ExtensionNotLoaded:
                pass
            try:
                self.bot.load_extension(EXTENSIONFOLDER+"."+extension)
            except commands.errors.ExtensionAlreadyLoaded:
                pass
            EMBED.add_field(name="Status",value="Reloaded category "+extension.upper()+"!")
        else:
            print("[Bot] - Reloading all extensions...")
            for extension in EXTENSIONS:
                try:
                    self.bot.unload_extension(EXTENSIONFOLDER+"."+extension)
                except commands.errors.ExtensionNotLoaded:
                    pass
                try:
                    self.bot.load_extension(EXTENSIONFOLDER+"."+extension)
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
        await ctx.sendEmbed(title="Stop", fields=[("Status", "Gestoppt")])
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
            await ctx.sendEmbed(title="Status ändern", inline=False,
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
    async def sudo(self, ctx, member: typing.Union[Member, User], command: str, *args):
        await ctx.invoke_as(member, command, *args)

    @commands.command(
        brief="Erhalte diesen Chat",
        usage="[Messages = 100]",
        aliases=["archiv", "log"],
        hidden=True,
    )
    @commands.is_owner()
    @commands.guild_only()
    async def archive(self, ctx, messages: int = 100):
        msgs = []
        text = ""
        async for msg in ctx.channel.history(limit=messages, oldest_first=True):
            msgs.append(msg)
            time = msg.created_at.strftime("%Y/%m/%d - %H:%M:%S")
            text += f"[[{time}]]({msg.jump_url}) {msg.author.name}#{msg.author.discriminator}: {msg.content}\n"
        await ctx.sendEmbed(
            title="Kanalarchiv",
            description=f"Kanal: {ctx.channel.mention}\nNachrichten: {len(msgs)}\n\n"+text,
            receiver=ctx.author,
        )

def setup(bot):
    bot.add_cog(Owneronly(bot))
