from datetime import datetime

import discord
from discord.ext import commands

from discordbot.botmodules import serverdata, audio
from discordbot.errors import ErrorMessage
from discordbot import utils

CONVERTERS = {
    discord.Member: commands.MemberConverter,
    discord.User: commands.UserConverter,
    discord.TextChannel: commands.TextChannelConverter,
    discord.VoiceChannel: commands.VoiceChannelConverter,
    discord.Role: commands.RoleConverter,
    discord.Invite: commands.InviteConverter,
    discord.Game: commands.GameConverter,
    discord.Emoji: commands.EmojiConverter,
    discord.PartialEmoji: commands.PartialEmojiConverter,
    discord.Colour: commands.ColourConverter
}

class Context(commands.Context):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.database = serverdata.DjangoConnection(self.author, self.guild)
        self.audio = audio.AudioManager(self)

        if self.guild is not None:
            self.data = serverdata.Server.getServer(self.guild.id)

    async def sendEmbed(self, title: str, *args, receiver=None, message: str = "", description: str = "", fields: list = list(), **kwargs):
        return await utils.sendEmbed(receiver or self.channel, title, *args, message=message, description=description, fields=fields, **kwargs)

    def getEmbed(self, title:str, description:str="", color:int=0x000000, fields:list=list(), inline=True, thumbnailurl:str=None, authorurl:str="", authorname:str=None, footertext:str="Angefordert von USER", footerurl:str="AVATARURL", timestamp=False):
        return utils.getEmbed(author=self.author, title=title, description=description, color=color or getattr(self.cog, "color", 0x000000), fields=fields, inline=inline, thumbnailurl=thumbnailurl, authorurl=authorurl, authorname=authorname, footertext=footertext, footerurl=footerurl, timestamp=timestamp)

    async def tick(self, value=True):
        emoji = '\N{WHITE HEAVY CHECK MARK}' if value else '\N{CROSS MARK}'
        try:
            await self.message.add_reaction(emoji)
        except discord.HTTPException:
            pass
