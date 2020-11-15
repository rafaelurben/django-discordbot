# pylint: disable=unused-variable

from discord.ext import commands

from discordbot.config import ALLOW_BOTS, ALLOW_WEBHOOKS, DEBUG

def setup(bot):
    @bot.event
    async def on_message(message):
        if message.author != bot.user:
            is_bot = message.author.bot
            is_webhook = bool(message.webhook_id)

            if (not is_bot) or ((ALLOW_BOTS and not is_webhook) or (ALLOW_WEBHOOKS and is_webhook)):
                ctx = await bot.get_context(message)
                a = await bot.invoke(ctx)
