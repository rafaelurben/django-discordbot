"This module can be used to subscribe to website updates"

from discord.ext import commands, tasks
from discord import errors

from discordbot.botmodules.serverdata import DjangoConnection
from discordbot.models import NotifierSource

class Notifier(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.color = 0xeb8f34

        print('[Notifier Background Tasks] - Started!')
        self.notifier_backgroundtasks_minute.start()
        self.notifier_backgroundtasks_hour.start()

    def cog_unload(self):
        print("[Notifier Background Tasks] - Stopped!")
        self.notifier_backgroundtasks_minute.cancel()
        self.notifier_backgroundtasks_hour.cancel()

    #

    async def notifier_update(self, frequency:str):
        print(f"[Notifier] - Fetching '{frequency}' sources...")
        for source in await DjangoConnection._list(NotifierSource, frequency=frequency):
            print(f"[Notifier] - Fetching '{frequency}' source: '{source.url}'...")

            updated, data, targets = await source.fetch_update()
            if updated:
                for target in targets:
                    try:
                        if target.where_type == "channel":
                            where = self.bot.get_channel(int(target.where_id)) or await self.bot.fetch_channel(int(target.where_id))
                        elif target.where_type == "member":
                            where = self.bot.get_user(int(target.where_id)) or await self.bot.fetch_user(int(target.where_id))
                        emb = self.bot.getEmbed(
                            title="Inhalt wurde geändert!",
                            description=str(data),
                            authorname=source.name,
                            authorurl=source.url,
                            color=self.color,
                        )
                        await where.send(embed=emb)
                    except errors.NotFound:
                        print(f"[Notifier] Failed to send: {target.where_id} ({target.where_type}) not found!")
        print(f"[Notifier] - Fetching '{frequency}' sources done!")

    #

    @tasks.loop(minutes=1)
    async def notifier_backgroundtasks_minute(self):
        await self.notifier_update("minute")

    @notifier_backgroundtasks_minute.before_loop
    async def notifier_backgroundtasks_minute_before(self):
        await self.notifier_update("minute")

    @tasks.loop(hours=1)
    async def notifier_backgroundtasks_hour(self):
        await self.notifier_update("hour")

    @notifier_backgroundtasks_hour.before_loop
    async def notifier_backgroundtasks_hour_before(self):
        await self.notifier_update("hour")

    #

    # @commands.group(
    #     brief="Erhalte Notifications zu Webseiten",
    #     description='Erhalte eine Nachricht, wenn sich auf einer Webseite etwas ändert.',
    #     aliases=['notify', 'noti'],
    #     usage=""
    # )
    # async def notifier(self, ctx):
    #     if ctx.invoked_subcommand is None:
    #         await ctx.send_help()



async def setup(bot):
    await bot.add_cog(Notifier(bot))
