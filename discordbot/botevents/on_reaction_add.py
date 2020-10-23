# pylint: disable=unused-variable

from discord.ext import commands
from discord import Embed, User, Member, utils, PermissionOverwrite, Role, PCMVolumeTransformer, FFmpegPCMAudio
import os

from discordbot.models import AmongUsGame, AMONGUS_PLAYER_COLORS, AMONGUS_EMOJI_COLORS


def setup(bot):
    # @bot.event
    # async def on_reaction_add(reaction, user):
    #     if not reaction.me:
    #         pass

    @bot.event
    async def on_raw_reaction_add(payload):
        if not payload.user_id == bot.user.id:
            ### Games -> AmongUs

            if payload.emoji.name in AMONGUS_EMOJI_COLORS and AmongUsGame.objects.filter(text_message_id=payload.message_id).exists():
                game = AmongUsGame.objects.get(text_message_id=payload.message_id)
                c = AMONGUS_EMOJI_COLORS[payload.emoji.name]
                game.set_user(userid=payload.user_id, color=c, save=True)

    @bot.event
    async def on_raw_reaction_remove(payload):
        if not payload.user_id == bot.user.id:
            ### Games -> AmongUs

            if payload.emoji.name in AMONGUS_EMOJI_COLORS and AmongUsGame.objects.filter(text_message_id=payload.message_id).exists():
                game = AmongUsGame.objects.get(text_message_id=payload.message_id)
                game.remove_user(userid=payload.user_id, save=True)
