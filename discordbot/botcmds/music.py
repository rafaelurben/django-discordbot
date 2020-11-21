from discord.ext import commands
from discord import Embed, User, Member, FFmpegPCMAudio, PCMVolumeTransformer, VoiceChannel
from fuzzywuzzy import process
import os

from discordbot.config import RADIOS, FFMPEG_OPTIONS, FILESPATH, MEMESPATH, MUSIC_MODULE
from discordbot.errors import ErrorMessage

#####

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.color = 0xee00ff

    # Events

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if MUSIC_MODULE:
            # *Grillenzirpen* nach Streamende
            if before.channel and before.self_stream and not after.self_stream:
                filepath = os.path.join(MEMESPATH, "grillenzirpen.wav")
                if os.path.isfile(filepath):
                    voice_client = before.channel.guild.voice_client
                    if voice_client is None:
                        voice_client = await before.channel.connect()
                    elif voice_client.is_playing():
                        voice_client.stop()
                        await voice_client.move_to(before.channel)

                    player = PCMVolumeTransformer(FFmpegPCMAudio(
                        source=filepath, **FFMPEG_OPTIONS))
                    voice_client.play(player, after=lambda e: print(
                        '[Music] - Error: %s' % e) if e else None)

    @commands.Cog.listener()
    async def on_message(self, message):
        if MUSIC_MODULE:
            # *Help I need somebody Help*
            if "i need somebody" in message.content.lower() and message.guild and message.author.voice:
                filepath = os.path.join(MEMESPATH, "help-i-need-somebody.wav")
                if os.path.isfile(filepath):
                    voice_client = message.guild.voice_client
                    if voice_client is None:
                        voice_client = await message.author.voice.channel.connect()
                    elif voice_client.is_playing():
                        voice_client.stop()
                        await voice_client.move_to(message.author.voice.channel)

                    player = PCMVolumeTransformer(FFmpegPCMAudio(
                        source=filepath, **FFMPEG_OPTIONS))
                    voice_client.play(player, after=lambda e: print(
                        '[Music] - Error: %s' % e) if e else None)

    # Utils

    async def ensure_voice(self, ctx):
        if ctx.author.voice and ctx.author.voice.channel.guild == ctx.guild:
            if ctx.voice_client is None:
                await ctx.author.voice.channel.connect()
            #elif ctx.voice_client.is_playing():
                #ctx.voice_client.stop()
            await ctx.voice_client.move_to(ctx.author.voice.channel)
        else:
            raise ErrorMessage("Du bist mit keinem Sprachkanal in diesem Server verbunden!")

    if MUSIC_MODULE:
        @commands.command(
            brief='Liste alle Memes auf',
            description='Liste alle Memes auf',
        )
        async def memes(self, ctx):
            filenames = list(os.listdir(MEMESPATH))
            await ctx.sendEmbed(title="Memes", description="\n".join(["- "+filename.split(".")[0] for filename in filenames]))


        @commands.command(
            brief='Spiele Memes',
            description='Spiele Memes von einer Audiodatei!',
            usage="<Suche>"
        )
        @commands.guild_only()
        async def meme(self, ctx, search:str="windows-xp-error", *args):
            search = " ".join((search,)+args)
            filenames = list(os.listdir(MEMESPATH))

            result = process.extractOne(search, filenames)
            filename = result[0]

            print("[Music] - Suchergebnis:", search, result)

            if result[1] >= 75:
                player = PCMVolumeTransformer(FFmpegPCMAudio(source=os.path.join(MEMESPATH, filename), **FFMPEG_OPTIONS))

                if ctx.voice_client.is_playing():
                    ctx.voice_client.stop()

                ctx.voice_client.play(player, after=lambda e: print('[Music] - Fehler: %s' % e) if e else None)
                await ctx.sendEmbed(title="Memetime!", fields=[("Meme",str(filename).split(".")[0])])
            else:
                raise commands.BadArgument(message="Es wurden keine mit '{}' übereinstimmende Audiodatei gefunden.".format(search))

        @commands.command(
            brief='Spiele Musik',
            description='Spiele Musik von Youtube und anderen Plattformen!',
            aliases=["yt","youtube"],
            usage="<Url/YT Suche>"
        )
        @commands.guild_only()
        async def play(self, ctx, search: str, *args):
            url = " ".join((search,)+args)
            async with ctx.typing():
                player = await ctx.data.musicqueue.createYoutubePlayer(url, loop=self.bot.loop)
                if ctx.voice_client.is_playing():
                    ctx.data.musicqueue.addPlayer(player)
                    await player.send(ctx, status="Song zur Playlist hinzugefügt!")
                else:
                    player.play(ctx)
                    await player.send(ctx)


        @commands.command(
            name='stream',
            brief='Streame einen Stream',
            description='Streame einen Stream von YouTube oder anderen Plattformen',
            aliases=[],
            usage="<Url/YT Suche>"
        )
        @commands.guild_only()
        async def stream(self, ctx, search: str, *args):
            url = " ".join((search,)+args)
            if url in RADIOS:
                url = RADIOS[url]

            async with ctx.typing():
                player = await ctx.data.musicqueue.createYoutubePlayer(url, loop=self.bot.loop, stream=True)

                if ctx.voice_client.is_playing():
                    ctx.voice_client.stop()

                player.play(ctx)
                await player.send(ctx, "Stream wird direkt wiedergegeben!")

        @commands.command(
            brief='Aktueller Titel abrufen',
            description='Sieh, was gerade läuft',
            aliases=["np"],
        )
        @commands.guild_only()
        async def nowplaying(self, ctx):
            await ctx.data.musicqueue.sendNowPlaying(ctx)

        @commands.command(
            brief="Warteschlange abrufen",
            description='Sieh, was als nächstes läuft',
        )
        @commands.guild_only()
        async def queue(self, ctx):
            await ctx.data.musicqueue.sendQueue(ctx)

        @commands.command(
            brief='Pausiere Musik',
            description='Pausiere die aktuelle Musik',
        )
        @commands.guild_only()
        async def pause(self, ctx):
            if ctx.voice_client and ctx.voice_client.is_playing():
                ctx.voice_client.pause()
                await ctx.sendEmbed(title="Musik pausiert")

        @commands.command(
            brief='Führe Musik fort',
            description='Hebe die Pausierung der aktuellen Musik auf.',
        )
        @commands.guild_only()
        async def resume(self, ctx):
            if ctx.voice_client and ctx.voice_client.is_paused():
                ctx.voice_client.resume()
                await ctx.sendEmbed(title="Pausierung aufgehoben")

        @commands.command(
            brief='Überspringe Musik',
            description='Überspringe aktuelle Musik',
            usage="<Url/Suche>"
        )
        @commands.guild_only()
        async def skip(self, ctx):
            async with ctx.typing():
                if ctx.voice_client.is_playing():
                    ctx.voice_client.stop()
                ctx.data.musicqueue.playNext(ctx)
                await ctx.data.musicqueue.sendNowPlaying(ctx)

        @commands.command(
            brief='Ändere die Lautstärke',
            description='Ändere die Lautstärke des Bots',
            aliases=["vol"],
            usage="<1-200>"
        )
        @commands.guild_only()
        async def volume(self, ctx, newvolume: float = None):
            if not ctx.voice_client.source:
                raise ErrorMessage("Der Bot scheint aktuell nichts abzuspielen.")

            oldvolume = ctx.voice_client.source.volume * 100

            if newvolume is None:
                await ctx.sendEmbed(title="Lautstärke", fields=[("Aktuell", str(oldvolume)+"%")])
            else:
                ctx.voice_client.source.volume = newvolume / 100

                await ctx.sendEmbed(title="Lautstärke geändert", fields=[("Zuvor", str(oldvolume)+"%"),("Jetzt",str(newvolume)+"%")])

        @commands.command(
            brief='Stoppe Musik',
            description='Stoppe Musik!',
            aliases=["die","leave","disconnect"],
            help="Benutze /stop um den Bot aus dem Sprachkanal zu entfernen.",
        )
        @commands.guild_only()
        async def stop(self, ctx):
            if ctx.voice_client:
                await ctx.voice_client.disconnect()
                await ctx.sendEmbed(title="Bye bye!")
            else:
                raise ErrorMessage("Der Bot war in gar keinem Sprachkanal!")

        @meme.before_invoke
        @play.before_invoke
        @stream.before_invoke
        @nowplaying.before_invoke
        @skip.before_invoke
        @volume.before_invoke
        async def autojoin(self, ctx):
            await self.ensure_voice(ctx)

    # Generelle Commands

    @commands.command(
        brief='Erhalte Infos über einen Song',
        description='Erhalte Infos über einen Song oder eine Playlist',
        aliases=[],
        hidden=True,
    )
    async def songinfo(self, ctx, query:str):
        async with ctx.typing():
            embdata = await ctx.audio.getInfoEmbedData(query)
            await ctx.sendEmbed(**embdata)

    @commands.command(
        name='usersong',
        brief='Stalke musikhörende Leute',
        description='Erhalte Links zu dem Song, welcher jemand gerade hört',
        aliases=[],
        help="Benutze /usersong <Member> um den Song zu erhalten",
        usage="<Member>"
    )
    @commands.guild_only()
    async def usersong(self, ctx, Member:Member):
        found = False
        for activity in Member.activities:
            if str(activity.type) == "ActivityType.listening":
                try:
                    await ctx.sendEmbed(title="User Song", fields=[("Titel", activity.title),("Künstler", activity.artist),("Link", ("[Spotify](https://open.spotify.com/track/"+activity.track_id+")"))])
                except AttributeError:
                    raise commands.BadArgument(message="Scheinbar hört dieser Benutzer keinen richtigen Song.")
                found = True
        if not found:
            raise commands.BadArgument(message="Dieser Benutzer hört keinen Song!")




def setup(bot):
    bot.add_cog(Music(bot))
