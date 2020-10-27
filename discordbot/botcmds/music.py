from discord.ext import commands
from discord import Embed, User, Member, opus, FFmpegPCMAudio, PCMVolumeTransformer, VoiceChannel
from fuzzywuzzy import process
import os

###

def chunks(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i:i + n]

###

filespath = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), "botfiles")
memespath = os.path.join(filespath, "memes")

# opus.load_opus('opus')

ffmpeg_options = {
    'options': '-vn',
    'executable': os.path.join(filespath,"ffmpeg.exe")
}

radios = {
    "swisspop": "http://www.radioswisspop.ch/live/mp3.m3u",
    "nrjbern":  "https://energybern.ice.infomaniak.ch/energybern-high.mp3",
}



#####

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.color = 0xee00ff

        # Siehe Botevent -> on_voice_state_update

    # sich in Entwicklung befindende Befehle
    if os.getenv("DEBUG", False):
        @commands.command(
            name='memes',
            brief='Liste alle Memes auf',
            description='Liste alle Memes auf',
            aliases=[],
            help="Benutze /memes um eine Liste aller Memes zu erhalten.",
            usage=""
        )
        async def memes(self, ctx):
            filenames = list(os.listdir(memespath))
            chunklist = list(chunks(filenames, 25))
            for chunkindex in range(len(chunklist)):
                chunk = chunklist[chunkindex]
                await ctx.sendEmbed(
                    title="Memes (Seite "+str(chunkindex+1)+"/"+str(len(chunklist))+")",
                    color=self.color,
                    fields=[("Meme", filename.split(".")[0]) for filename in chunk]
                )


        @commands.command(
            name='meme',
            brief='Spiele Memes',
            description='Spiele Memes von einer Audiodatei!',
            aliases=[],
            help="Benutze /meme <Name> um einen Meme abzuspielen.",
            usage="<Suche>"
        )
        @commands.guild_only()
        async def meme(self, ctx, search:str="windows-xp-error"):
            search = search+" "+ctx.getargs()
            filenames = list(os.listdir(memespath))

            result = process.extractOne(search, filenames)
            filename = result[0]

            print("[Music] - Suchergebnis:", search, result)

            if result[1] >= 75:
                player = PCMVolumeTransformer(FFmpegPCMAudio(source=os.path.join(memespath, filename), **ffmpeg_options))

                if ctx.voice_client.is_playing():
                    ctx.voice_client.stop()

                ctx.voice_client.play(player, after=lambda e: print('[Music] - Fehler: %s' % e) if e else None)
                await ctx.sendEmbed(title="Memetime!", color=self.color, fields=[("Meme",str(filename).split(".")[0])])
            else:
                raise commands.BadArgument(message="Es wurden keine mit '{}' übereinstimmende Audiodatei gefunden.".format(search))

        # from example

        @commands.command(
            name='play',
            brief='Spiele Musik',
            description='Spiele Musik von Youtube und anderen Plattformen!',
            aliases=["yt","youtube"],
            help="Benutze /play <Url/Suche> um einen Song abzuspielen.",
            usage="<Url/Suche>"
        )
        @commands.guild_only()
        async def play(self, ctx):
            url = ctx.getargs(True)
            async with ctx.typing():
                player = list(await ctx.data.musicqueue.createYoutubePlayer(url, loop=self.bot.loop))[0]
                if ctx.voice_client.is_playing():
                    ctx.data.musicqueue.addPlayer(player)
                    await player.send(ctx, status="Song zur Playlist hinzugefügt!")
                else:
                    player.play(ctx)
                    await player.send(ctx)


        @commands.command(
            name='stream',
            brief='Streame einen Stream',
            description='Streame einen Stream von Twitch oder YouTube',
            aliases=[],
            help="Benutze /stream <Url/Suche> den einen Stream zu streamen.",
            usage="<Url/Suche>"
        )
        @commands.guild_only()
        async def stream(self, ctx):
            url = ctx.getargs(True)
            if url in radios:
                url = radios[url]

            async with ctx.typing():
                player = list(await ctx.data.musicqueue.createYoutubePlayer(url, loop=self.bot.loop, stream=True))[0]

                if ctx.voice_client.is_playing():
                    ctx.voice_client.stop()

                player.play(ctx)
                await player.send(ctx, "Stream wird direkt wiedergegeben!")

        @commands.command(
            name='nowplaying',
            brief='Was läuft gerade?',
            description='Sieh, was gerade läuft',
            aliases=["np"],
            help="Benutze /np um zu sehen, was aktuell läuft.",
            usage=""
        )
        @commands.guild_only()
        async def nowplaying(self, ctx):
            await ctx.data.musicqueue.sendNowPlaying(ctx)

        @commands.command(
            name='pause',
            brief='Pausiere Musik',
            description='Pausiere die aktuelle Musik',
            aliases=[],
            help="Benutze /pause um die aktuelle Musik zu pausieren.",
            usage=""
        )
        @commands.guild_only()
        async def pause(self, ctx):
            if ctx.voice_client and ctx.voice_client.is_playing():
                ctx.voice_client.pause()
                await ctx.sendEmbed(title="Musik pausiert", color=self.color)

        @commands.command(
            name='resume',
            brief='Führe Musik fort',
            description='Hebe die Pausierung der aktuellen Musik auf.',
            aliases=[],
            help="Benutze /resume um die aktuelle Musik weiter zu spielen.",
            usage=""
        )
        @commands.guild_only()
        async def resume(self, ctx):
            if ctx.voice_client and ctx.voice_client.is_paused():
                ctx.voice_client.resume()
                await ctx.sendEmbed(title="Pausierung aufgehoben", color=self.color)

        @commands.command(
            name='skip',
            brief='Überspringe Musik',
            description='Überspringe aktuelle Musik',
            aliases=[],
            help="Benutze /skip um den aktuellen Song zu überspringen.",
            usage="<Url/Suche>"
        )
        @commands.guild_only()
        async def skip(self, ctx):
            async with ctx.typing():
                if ctx.voice_client is not None and ctx.voice_client.is_playing():
                    ctx.voice_client.stop()
                if ctx.voice_client is not None:
                    ctx.data.musicqueue.playNext(ctx)
                    await ctx.data.musicqueue.sendNowPlaying(ctx)
                else:
                    raise commands.CommandError(message="Es wurde gar kein Song abgespielt.")

        @commands.command(
            name='volume',
            brief='Ändere die Lautstärke',
            description='Ändere die Lautstärke des Bots',
            aliases=["vol"],
            help="Benutze /volume <1-200> um die Lautstärke des Bots zu ändern.",
            usage="<1-200>"
        )
        @commands.guild_only()
        async def volume(self, ctx, newvolume: float):
            if ctx.voice_client is None:
                raise commands.CommandError("Der Bot ist nicht mit einem Sprachkanal verbunden.")
            elif not ctx.voice_client.source:
                raise commands.CommandError("Der Bot scheint aktuell nichts abzuspielen.")

            oldvolume = ctx.voice_client.source.volume * 100
            ctx.voice_client.source.volume = newvolume / 100

            await ctx.sendEmbed(title="Lautstärke geändert", color=self.color, fields=[("Zuvor", str(oldvolume)+"%"),("Jetzt",str(newvolume)+"%")])

        @commands.command(
            name='stop',
            brief='Stoppe Musik',
            description='Stoppe Musik!',
            aliases=["die","leave","disconnect"],
            help="Benutze /stop um den Bot aus dem Sprachkanal zu entfernen.",
            usage=""
        )
        @commands.guild_only()
        async def stop(self, ctx):
            if ctx.voice_client:
                await ctx.voice_client.disconnect()
            else:
                raise commands.CommandError(message="Der Bot war in gar keinem Sprachkanal!")

        @meme.before_invoke
        @play.before_invoke
        @stream.before_invoke
        @nowplaying.before_invoke
        @skip.before_invoke
        @volume.before_invoke
        async def autojoin(self, ctx):
            if ctx.author.voice and ctx.author.voice.channel.guild == ctx.guild:
                if ctx.voice_client is None:
                    await ctx.author.voice.channel.connect()
                #elif ctx.voice_client.is_playing():
                    #ctx.voice_client.stop()
                await ctx.voice_client.move_to(ctx.author.voice.channel)
            else:
                raise commands.CommandError("Du bist mit keinem Sprachkanal in diesem Server verbunden!")



    # Generelle Commands

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
                    await ctx.sendEmbed(title="User Song", color=self.color, fields=[("Titel", activity.title),("Künstler", activity.artist),("Link", ("[Spotify](https://open.spotify.com/track/"+activity.track_id+")"))])
                except AttributeError:
                    raise commands.BadArgument(message="Scheinbar hört dieser Benutzer keinen richtigen Song.")
                found = True
        if not found:
            raise commands.BadArgument(message="Dieser Benutzer hört keinen Song!")




def setup(bot):
    bot.add_cog(Music(bot))
