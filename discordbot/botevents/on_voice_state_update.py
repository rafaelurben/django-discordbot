# pylint: disable=unused-variable

from discord.ext import commands
from discord import Embed, User, Member, utils, PermissionOverwrite, Role, PCMVolumeTransformer, FFmpegPCMAudio
import os

def setup(bot):
    @bot.event
    async def on_voice_state_update(member, before, after):
        ##### Channels
        from discordbot.botcmds.channels import getUserChannelCategory

        category = await getUserChannelCategory(member.guild)
        # Delete channel if empty
        if before.channel and before.channel.category and before.channel.category.name.upper() == "BENUTZERKANÄLE" and "#" in before.channel.name and before.channel.members == []:
            await before.channel.delete(reason="Kanal war leer")
            channelowner = utils.get(before.channel.guild.members, name=before.channel.name.split("#")[0], discriminator=before.channel.name.split("#")[1])
            EMBED = Embed(title="Sprachkanal gelöscht!")
            EMBED.set_footer(text=f'Kanal von {member.name}',icon_url=member.avatar_url)
            EMBED.add_field(name="Server",value=member.guild.name)
            await channelowner.send(embed=EMBED)
        # Create new channel
        if after.channel and after.channel.name == "Sprachkanal erstellen":
            channel = utils.get(member.guild.voice_channels, name=(member.name+"#"+member.discriminator))
            if channel:
                await member.edit(voice_channel=channel,reason="Benutzer wollte einen Kanal erstellen, besitzte aber bereits Einen")
            else:
                overwrites = { member.guild.default_role: PermissionOverwrite(connect=False,speak=True,read_messages=True), member: PermissionOverwrite(connect=True,speak=True,read_messages=True,move_members=True,mute_members=True) }
                newchannel = await category.create_voice_channel(name=(member.name+"#"+member.discriminator),overwrites=overwrites,reason="Benutzer hat den Sprachkanal erstellt")
                await member.edit(voice_channel=newchannel,reason="Benutzer hat den Sprachkanal erstellt")
                EMBED = Embed(title="Sprachkanal erstellt!")
                EMBED.set_footer(text=f'Kanal von {member.name}',icon_url=member.avatar_url)
                EMBED.add_field(name="Server",value=member.guild.name)
                await member.send(embed=EMBED)





        ##### Music
        if os.getenv("DEBUG", False):
            filespath = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), "botfiles")
            memespath = os.path.join(filespath, "memes")

            ffmpeg_options = {
                'options': '-vn',
                'executable': os.path.join(filespath,"ffmpeg.exe")
            }

            # *Grillenzirpen* nach Streamende
            if before.channel and before.self_stream and not after.self_stream:
                voice_client = before.channel.guild.voice_client
                if voice_client is None:
                    voice_client = await before.channel.connect()
                elif voice_client.is_playing():
                    voice_client.stop()
                    await voice_client.move_to(before.channel)

                player = PCMVolumeTransformer(FFmpegPCMAudio(source=os.path.join(memespath, "grillenzirpen.wav"), **ffmpeg_options))
                voice_client.play(player, after=lambda e: print('[Msuic] - Error: %s' % e) if e else None)
