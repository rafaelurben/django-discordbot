from datetime import datetime

import discord
from discord.ext import commands

from discordbot.botmodules import serverdata, audio
from discordbot.utils import chunks
from discordbot.errors import ErrorMessage

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
        if len(description) > 2048:
            desc = list(chunks(description, 2042))
            for i in range(len(desc)):
                if i == 0:
                    await (receiver or self).send(message, embed=self.getEmbed(f"{title} ({i+1}/{len(desc)})", *args, description=desc[i]+" [...]", fields=fields, **kwargs))
                elif i == len(desc)-1:
                    return await (receiver or self).send(embed=self.getEmbed(f"{title} ({i+1}/{len(desc)})", *args, description=desc[i], **kwargs))
                else:
                    await (receiver or self).send(embed=self.getEmbed(f"{title} ({i+1}/{len(desc)})", *args, description=desc[i]+" [...]", **kwargs))
        elif len(fields) > 25:
            flds = list(chunks(fields, 25))
            for i in range(len(flds)):
                if i == 0:
                    await (receiver or self).send(message, embed=self.getEmbed(f"{title} ({i+1}/{len(flds)})", *args, description=description, fields=flds[i], **kwargs))
                elif i == len(flds)-1:
                    return await (receiver or self).send(embed=self.getEmbed(f"{title} ({i+1}/{len(flds)})", *args, fields=flds[i], **kwargs))
                else:
                    await (receiver or self).send(embed=self.getEmbed(f"{title} ({i+1}/{len(flds)})", *args, fields=flds[i], **kwargs))
        else:
            return await (receiver or self).send(message, embed=self.getEmbed(title=title, *args, description=description, fields=fields, **kwargs))

    def getEmbed(self, title:str, description:str="", color:int=0x000000, fields:list=[], inline=True, thumbnailurl:str=None, authorurl:str="", authorname:str=None, footertext:str="Angefordert von USER", footerurl:str="AVATARURL", timestamp=False):
        EMBED = discord.Embed(title=title[:256], description=description[:2048], color=color or getattr(self.cog, "color", 0x000000))
        EMBED.set_footer(text=footertext.replace("USER", str(self.author.name+"#"+self.author.discriminator))[:2048], icon_url=footerurl.replace("AVATARURL", str(self.author.avatar)))
        
        if timestamp:
            EMBED.timestamp = datetime.utcnow() if timestamp is True else timestamp
        for field in fields[:25]:
            EMBED.add_field(name=field[0][:256], value=(field[1][:1018]+" [...]" if len(field[1]) > 1024 else field[1]), inline=bool(field[2] if len(field) > 2 else inline))
        if thumbnailurl:
            EMBED.set_thumbnail(url=thumbnailurl.strip())
        if authorname:
            if authorurl and ("https://" in authorurl or "http://" in authorurl):
                EMBED.set_author(name=authorname[:256], url=authorurl.strip())
            else:
                EMBED.set_author(name=authorname[:256])
        return EMBED

    async def tick(self, value=True):
        emoji = '\N{WHITE HEAVY CHECK MARK}' if value else '\N{CROSS MARK}'
        try:
            await self.message.add_reaction(emoji)
        except discord.HTTPException:
            pass

    async def send_help(self):
        await self.invoke(self.bot.get_command("help"), self.invoked_with)

    async def invoke_as(self, member, command, *args):
        _command = command.replace("_", " ")
        cmd = self.bot.get_command(_command)
        if cmd is None:
            raise ErrorMessage(f"Der Befehl `{ _command }` wurde nicht gefunden! \nPS: Benutze im Command bitte kein Prefix! Für Subcommands, benutze command_subcommand.")
        self.message.content = self.prefix+_command+self.message.content.split(command)[1]
        self.message.author = member
        self.author = member
        self.database = type(self.database)(self.author, self.guild)
        annotations = cmd.callback.__annotations__
        annotations.pop("return", None)
        arguments = list(args)
        for i, cls in enumerate(annotations.values()):
            if len(arguments) > i:
                if cls in CONVERTERS:
                    arguments[i] = await CONVERTERS[cls]().convert(self, arguments[i])
                else:
                    arguments[i] = cls(arguments[i])
        await self.invoke(cmd, *arguments)
