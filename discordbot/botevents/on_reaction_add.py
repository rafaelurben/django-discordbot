# pylint: disable=unused-variable

from discord.ext import commands
from discord import Embed, User, Member, utils, PermissionOverwrite, Role, PCMVolumeTransformer, FFmpegPCMAudio
import os

from discordbot.models import AmongUsGame, AMONGUS_PLAYER_COLORS, AMONGUS_EMOJI_COLORS

from discordbot.botmodules.serverdata import DjangoConnection

#####

DELETE = "❌"

#####

def setup(bot):
    @bot.event
    async def on_raw_reaction_add(payload):
        if not payload.user_id == bot.user.id:
            ### Games -> AmongUs

            emoji = payload.emoji.name

            if (emoji in AMONGUS_EMOJI_COLORS or emoji == DELETE) and await DjangoConnection._hasAmongUsGame(text_message_id=payload.message_id):
                game = await DjangoConnection._getAmongUsGame(text_message_id=payload.message_id)
                if emoji == DELETE:
                    await DjangoConnection._removeAmongUsUser(game=game, userid=payload.user_id, save=True)
                else:
                    c = AMONGUS_EMOJI_COLORS[payload.emoji.name]
                    await DjangoConnection._setAmongUsUser(game=game, userid=payload.user_id, color=c, save=True)

                channel = await bot.fetch_channel(payload.channel_id)
                message = await channel.fetch_message(payload.message_id)
                await message.remove_reaction(emoji, payload.member)
