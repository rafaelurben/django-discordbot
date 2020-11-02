# pylint: disable=unused-variable

from discord.ext import commands
from discord import Embed, User, Member, utils, PermissionOverwrite, Role, PCMVolumeTransformer, FFmpegPCMAudio
import os

from discordbot.models import AmongUsGame, AMONGUS_PLAYER_COLORS, AMONGUS_EMOJI_COLORS, VierGewinntGame, VIERGEWINNT_NUMBER_EMOJIS, VIERGEWINNT_PLAYER_EMOJIS

from discordbot.botmodules.serverdata import DjangoConnection

#####

DELETE = "❌"

#####

def setup(bot):
    @bot.event
    async def on_raw_reaction_add(payload):
        if not payload.user_id == bot.user.id:
            emoji = payload.emoji.name
            channel = await bot.fetch_channel(payload.channel_id)
            message = await channel.fetch_message(payload.message_id)

            ### Games -> AmongUs

            if (emoji in AMONGUS_EMOJI_COLORS or emoji == DELETE) and await DjangoConnection._hasAmongUsGame(text_message_id=payload.message_id):
                game = await DjangoConnection._getAmongUsGame(text_message_id=payload.message_id)

                if emoji == DELETE:
                    await DjangoConnection._removeAmongUsUser(game=game, userid=payload.user_id, save=True)
                else:
                    c = AMONGUS_EMOJI_COLORS[payload.emoji.name]
                    await DjangoConnection._setAmongUsUser(game=game, userid=payload.user_id, color=c, save=True)

                await message.remove_reaction(emoji, payload.member)

            ### Games -> VierGewinnt

            if (emoji in VIERGEWINNT_NUMBER_EMOJIS) and await DjangoConnection._hasVierGewinntGame(message_id=payload.message_id):
                game = await DjangoConnection._getVierGewinntGame(message_id=payload.message_id)
                
                if not game.finished:
                    n = VIERGEWINNT_NUMBER_EMOJIS.index(emoji)

                    if game.process(n, payload.user_id):
                        await DjangoConnection._save(game)

                        embed = bot.getEmbed(
                            title=f"Vier Gewinnt (#{game.pk})",
                            color=0x0078D7,
                            description=game.get_description()
                        )

                        await message.edit(embed=embed)

                    
                    if game.process_bot():
                        await DjangoConnection._save(game)

                        embed = bot.getEmbed(
                            title=f"Vier Gewinnt (#{game.pk})",
                            color=0x0078D7,
                            description=game.get_description()
                        )

                        await message.edit(embed=embed)

                    if game.finished:
                        for emoji in VIERGEWINNT_NUMBER_EMOJIS[:game.width]:
                            await message.remove_reaction(emoji, bot.user)

                await message.remove_reaction(emoji, payload.member)
