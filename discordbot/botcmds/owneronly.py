from discord.ext import commands
import discord

from discordbot import config


class Owneronly(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.color = 0x000000

    @commands.command(
        brief="Lade die Bot-Extensionen neu",
    )
    @commands.is_owner()
    async def reload(self, ctx, extension: str = None):
        emb = ctx.getEmbed(title="Reload", fields=[("Status", "Reloading")])
        msg = await ctx.message.author.send(embed=emb)
        emb = ctx.getEmbed(title="Reload", fields=[])
        if extension in config.EXTENSIONS:
            print("[Bot] - Reloading '"+extension+"' extension...")
            try:
                await self.bot.unload_extension(config.EXTENSIONFOLDER+"."+extension)
            except commands.errors.ExtensionNotLoaded:
                pass
            try:
                await self.bot.load_extension(config.EXTENSIONFOLDER+"."+extension)
            except commands.errors.ExtensionAlreadyLoaded:
                pass
            emb.add_field(
                name="Status", value="Reloaded category "+extension.upper()+"!")
        else:
            print("[Bot] - Reloading all extensions...")
            for ext in config.EXTENSIONS:
                try:
                    await self.bot.unload_extension(config.EXTENSIONFOLDER+"."+ext)
                except commands.errors.ExtensionNotLoaded:
                    pass
                try:
                    await self.bot.load_extension(config.EXTENSIONFOLDER+"."+ext)
                except commands.errors.ExtensionAlreadyLoaded:
                    pass
            emb.add_field(name="Status", value="Reloaded all categories!")
        await msg.edit(embed=emb)
        print("[Bot] - Reload completed!")
        await self.bot.tree.sync()
        print("[Bot] - Tree synced!")

    @commands.command(
        brief="Stoppe den Bot",
    )
    @commands.is_owner()
    async def stopbot(self, ctx):
        await ctx.sendEmbed(title="Stop", fields=[("Status", "Gestoppt")])
        await self.bot.close()

    @commands.command(
        brief="Ändere den Status des Bots",
        usage="<Status> [Aktivität [Argumente(e)]]",
    )
    @commands.is_owner()
    async def status(self, ctx, new_state: str = "", new_activity: str = "", arg1: str = "", *args):
        arg2 = " ".join(args)
        status = None
        activity = None
        if new_state.lower() in ["on", "online", "green"]:
            status = discord.Status.online
        elif new_state.lower() in ["off", "offline", "invisible", "grey"]:
            status = discord.Status.invisible
        elif new_state.lower() in ["dnd", "donotdisturb", "do_not_disturb", "bittenichtstören", "red"]:
            status = discord.Status.dnd
        elif new_state.lower() in ["idle", "abwesend", "orange", "yellow"]:
            status = discord.Status.idle

        if new_activity.lower() in ["playing", "spielt", "game", "play"]:
            activity = discord.Game(name=arg1+" "+arg2)
        elif new_activity.lower() in ["streaming", "streamt", "stream", "live", "twitch"]:
            activity = discord.Streaming(url="https://twitch.tv/"+arg1, name=arg2)
        elif new_activity.lower() in ["listening", "listen", "hört", "hören", "song"]:
            activity = discord.Activity(
                type=discord.ActivityType.listening, name=arg1+" "+arg2)
        elif new_activity.lower() in ["watching", "watch", "schaut", "video"]:
            activity = discord.Activity(type=discord.ActivityType.watching, name=arg1+" "+arg2)

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
            description=f"Kanal: {ctx.channel.mention}\nNachrichten: {len(msgs)}\n\n" +
            text,
            receiver=ctx.author,
        )


async def setup(bot):
    await bot.add_cog(Owneronly(bot))
