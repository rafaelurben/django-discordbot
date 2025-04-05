import os
import typing

import discord
from discord import (
    FFmpegPCMAudio,
    PCMVolumeTransformer,
    app_commands,
)
from discord.ext import commands
from fuzzywuzzy import process

from discordbot.config import (
    FFMPEG_OPTIONS,
    MEMESPATH,
    RADIOS,
)
from discordbot.errors import ErrorMessage, SuccessMessage


async def ensure_voice_connection(
    interaction: discord.Interaction,
) -> discord.VoiceClient:
    if (
        interaction.user.voice
        and interaction.user.voice.channel.guild == interaction.guild
    ):
        if interaction.guild.voice_client is None:
            return await interaction.user.voice.channel.connect(self_deaf=True)

        voice_client = typing.cast(
            discord.VoiceClient, interaction.guild.voice_client
        )
        if voice_client.is_playing():
            voice_client.stop()
        await voice_client.move_to(interaction.user.voice.channel)

        return voice_client
    else:
        raise ErrorMessage(
            "Du bist mit keinem Sprachkanal in diesem Server verbunden!"
        )


class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.color = 0xEE00FF

    # Utils

    async def ensure_voice(self, ctx):
        if ctx.author.voice and ctx.author.voice.channel.guild == ctx.guild:
            if ctx.voice_client is None:
                await ctx.author.voice.channel.connect(self_deaf=True)
            # elif ctx.voice_client.is_playing():
            # ctx.voice_client.stop()
            await ctx.voice_client.move_to(ctx.author.voice.channel)
        else:
            raise ErrorMessage(
                "Du bist mit keinem Sprachkanal in diesem Server verbunden!"
            )

    if os.path.exists(MEMESPATH) and os.path.isdir(MEMESPATH):

        memes_group = app_commands.Group(
            name="memes",
            description="Spiele Memes ab",
            guild_only=True,
            allowed_installs=app_commands.AppInstallationType(guild=True),
        )

        @memes_group.command(
            name="list",
            description="Liste alle Memes auf",
        )
        async def memes(self, interaction: discord.Interaction):
            filenames = list(os.listdir(MEMESPATH))
            raise SuccessMessage(
                "\n".join(
                    map(
                        lambda filename: "- " + filename.split(".")[0].title(),
                        filenames,
                    )
                ),
                title="Memes",
                color=self.color,
            )

        @memes_group.command(
            name="play",
            description="Spiele ein Meme ab",
        )
        @app_commands.describe(search="Suchbegriff")
        @app_commands.checks.bot_has_permissions(connect=True, speak=True)
        async def meme(
            self,
            interaction: discord.Interaction,
            search: str,
        ):
            voice_client = await ensure_voice_connection(interaction)

            filenames = list(os.listdir(MEMESPATH))

            result = process.extractOne(search, filenames)
            filename = result[0]

            print("[Music] - Suchergebnis:", search, result)

            if result[1] >= 75:
                player = PCMVolumeTransformer(
                    FFmpegPCMAudio(
                        source=os.path.join(MEMESPATH, filename),
                        **FFMPEG_OPTIONS,
                    )
                )

                if voice_client.is_playing():
                    voice_client.stop()

                voice_client.play(
                    player,
                    after=lambda e: (
                        print("[Music] - Fehler: %s" % e) if e else None
                    ),
                )
                raise SuccessMessage(
                    "Meme: " + str(filename).split(".")[0],
                    title="It's meme time!",
                    color=self.color,
                )
            else:
                raise ErrorMessage(
                    "Es wurden keine mit '{}' übereinstimmende Audiodatei gefunden.".format(
                        search
                    )
                )

        @meme.autocomplete("search")
        async def cmd_meme__search_autocomplete(
            self,
            interaction: discord.Interaction,
            current: str,
        ) -> typing.List[app_commands.Choice[str]]:
            filenames = list(os.listdir(MEMESPATH))

            matches = process.extractBests(current, filenames, limit=25)
            return list(
                map(
                    lambda match: app_commands.Choice(
                        value=match[0],
                        name=match[0].split(".")[0].title(),
                    ),
                    matches,
                )
            )

    @commands.command(
        brief="Spiele Musik",
        description="Spiele Musik von Youtube und anderen Plattformen!",
        aliases=["yt", "youtube"],
        usage="<Url/YT Suche>",
    )
    @commands.guild_only()
    async def play(self, ctx, search: str, *args):
        url = " ".join((search,) + args)
        async with ctx.typing():
            player = await ctx.data.musicqueue.createYoutubePlayer(
                url, loop=self.bot.loop
            )
            if ctx.voice_client.is_playing():
                ctx.data.musicqueue.addPlayer(player)
                await player.send(ctx, status="Song zur Playlist hinzugefügt!")
            else:
                player.play(ctx)
                await player.send(ctx)

    @commands.command(
        name="stream",
        brief="Streame einen Stream",
        description="Streame einen Stream von YouTube oder anderen Plattformen",
        aliases=[],
        usage="<Url/YT Suche>",
    )
    @commands.guild_only()
    async def stream(self, ctx, search: str, *args):
        url = " ".join((search,) + args)
        url = RADIOS.get(url, url)

        async with ctx.typing():
            player = await ctx.data.musicqueue.createYoutubePlayer(
                url, loop=self.bot.loop, stream=True
            )

            if ctx.voice_client.is_playing():
                ctx.voice_client.stop()

            player.play(ctx)
            await player.send(ctx, "Stream wird direkt wiedergegeben!")

    @commands.command(
        brief="Aktueller Titel abrufen",
        description="Sieh, was gerade läuft",
        aliases=["np"],
    )
    @commands.guild_only()
    async def nowplaying(self, ctx):
        await ctx.data.musicqueue.sendNowPlaying(ctx)

    @commands.command(
        brief="Warteschlange abrufen",
        description="Sieh, was als nächstes läuft",
    )
    @commands.guild_only()
    async def queue(self, ctx):
        await ctx.data.musicqueue.sendQueue(ctx)

    @commands.command(
        brief="Pausiere Musik",
        description="Pausiere die aktuelle Musik",
    )
    @commands.guild_only()
    async def pause(self, ctx):
        if ctx.voice_client and ctx.voice_client.is_playing():
            ctx.voice_client.pause()
            await ctx.sendEmbed(title="Musik pausiert")

    @commands.command(
        brief="Führe Musik fort",
        description="Hebe die Pausierung der aktuellen Musik auf.",
    )
    @commands.guild_only()
    async def resume(self, ctx):
        if ctx.voice_client and ctx.voice_client.is_paused():
            ctx.voice_client.resume()
            await ctx.sendEmbed(title="Pausierung aufgehoben")

    @commands.command(
        brief="Überspringe Musik",
        description="Überspringe aktuelle Musik",
        usage="<Url/Suche>",
    )
    @commands.guild_only()
    async def skip(self, ctx):
        async with ctx.typing():
            if ctx.voice_client.is_playing():
                ctx.voice_client.stop()
            ctx.data.musicqueue.playNext(ctx)
            await ctx.data.musicqueue.sendNowPlaying(ctx)

    @commands.command(
        brief="Ändere die Lautstärke",
        description="Ändere die Lautstärke des Bots",
        aliases=["vol"],
        usage="<1-200>",
    )
    @commands.guild_only()
    async def volume(self, ctx, newvolume: float = None):
        if not ctx.voice_client.source:
            raise ErrorMessage("Der Bot scheint aktuell nichts abzuspielen.")

        oldvolume = ctx.voice_client.source.volume * 100

        if newvolume is None:
            await ctx.sendEmbed(
                title="Lautstärke",
                fields=[("Aktuell", str(oldvolume) + "%")],
            )
        else:
            ctx.voice_client.source.volume = newvolume / 100

            raise SuccessMessage(
                "Lautstärke geändert",
                fields=[
                    ("Zuvor", str(oldvolume) + "%"),
                    ("Jetzt", str(newvolume) + "%"),
                ],
            )

    @commands.command(
        brief="Stoppe Musik",
        description="Stoppe Musik!",
        aliases=["die", "leave", "disconnect"],
        help="Benutze /stop um den Bot aus dem Sprachkanal zu entfernen.",
    )
    @commands.guild_only()
    async def stop(self, ctx):
        if ctx.voice_client:
            await ctx.voice_client.disconnect()
            raise SuccessMessage("Bye bye!")
        raise ErrorMessage("Der Bot war in gar keinem Sprachkanal!")

    @play.before_invoke
    @stream.before_invoke
    @nowplaying.before_invoke
    @skip.before_invoke
    @volume.before_invoke
    async def autojoin(self, ctx):
        await self.ensure_voice(ctx)

    @commands.command(
        brief="Erhalte Infos über einen Song",
        description="Erhalte Infos über einen Song oder eine Playlist",
        aliases=[],
        hidden=True,
    )
    async def songinfo(self, ctx, query: str):
        async with ctx.typing():
            embdata = await ctx.audio.getInfoEmbedData(query)
            await ctx.sendEmbed(**embdata)


async def setup(bot):
    await bot.add_cog(Music(bot))
