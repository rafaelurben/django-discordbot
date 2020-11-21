# pylint: disable=no-member

from discord.ext import commands, tasks
from discord import Embed, User, TextChannel, utils
from datetime import datetime as d
import typing

from discordbot.botmodules.serverdata import DjangoConnection
from discordbot.models import NotifierSub

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

    async def notifier_update(self, frequency:str, send:bool=False):
        for sub in await DjangoConnection._list(NotifierSub, frequency=frequency):
            data = sub.process()
            if data:
                await DjangoConnection._save(sub)
            if send and isinstance(data, str):
                if sub.where_type == "channel":
                    where = self.bot.get_channel(int(sub.where_id)) or await self.bot.fetch_channel(int(sub.where_id))
                elif sub.where_type == "member":
                    where = self.bot.get_user(int(sub.where_id)) or await self.bot.fetch_user(int(sub.where_id))
                emb = self.bot.getEmbed(
                    title="Neue Änderung!",
                    description=str(data),
                    authorname=sub.name,
                    authorurl=sub.url,
                    color=self.color,
                )
                await where.send(embed=emb)

    #

    @tasks.loop(minutes=1)
    async def notifier_backgroundtasks_minute(self):
        await self.notifier_update("minute", send=True)

    @notifier_backgroundtasks_minute.before_loop
    async def notifier_backgroundtasks_minute_before(self):
        await self.notifier_update("minute", send=False)

    @tasks.loop(hours=1)
    async def notifier_backgroundtasks_hour(self):
        await self.notifier_update("hour", send=True)

    @notifier_backgroundtasks_hour.before_loop
    async def notifier_backgroundtasks_hour_before(self):
        await self.notifier_update("hour", send=False)

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
