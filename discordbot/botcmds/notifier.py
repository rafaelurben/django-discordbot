"This module can be used to subscribe to website updates"

from discord.ext import commands, tasks
from discord import errors

from discordbot.botmodules.serverdata import DjangoConnection
from discordbot.models import NotifierSource, NotifierTarget

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

    async def notifier_update(self, frequency:str, initial:bool=False):
        for source in await DjangoConnection._list(NotifierSource, frequency=frequency):
            updated, data, targets = await source.fetch_update(initialfetch=initial)
            if updated:
                await DjangoConnection._save(source)

                if not initial:
                    for target in targets:
                        try:
                            if target.where_type == "channel":
                                where = self.bot.get_channel(int(target.where_id)) or await self.bot.fetch_channel(int(target.where_id))
                            elif target.where_type == "member":
                                where = self.bot.get_user(int(target.where_id)) or await self.bot.fetch_user(int(target.where_id))
                            emb = self.bot.getEmbed(
                                title="Neue Änderung!",
                                description=str(data),
                                authorname=source.name,
                                authorurl=source.url,
                                color=self.color,
                            )
                            await where.send(embed=emb)
                        except errors.NotFound:
                            print(f"[Notifier] Failed to send: {target.where_id} ({target.where_type}) not found!")

    #

    @tasks.loop(minutes=1)
    async def notifier_backgroundtasks_minute(self):
        await self.notifier_update("minute", initial=False)

    @notifier_backgroundtasks_minute.before_loop
    async def notifier_backgroundtasks_minute_before(self):
        await self.notifier_update("minute", initial=True)

    @tasks.loop(hours=1)
    async def notifier_backgroundtasks_hour(self):
        await self.notifier_update("hour", initial=False)

    @notifier_backgroundtasks_hour.before_loop
    async def notifier_backgroundtasks_hour_before(self):
        await self.notifier_update("hour", initial=True)

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



def setup(bot):
    bot.add_cog(Notifier(bot))
