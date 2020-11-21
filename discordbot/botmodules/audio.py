import youtube_dl
import os
import asyncio

from discord import PCMVolumeTransformer, FFmpegPCMAudio
from discord.ext import commands

from discordbot.config import FILESPATH, FFMPEG_OPTIONS, FFMPEG_OPTIONS_STREAM, DEBUG

# Suppress noise about console usage from errors
youtube_dl.utils.bug_reports_message = lambda: ''

_ytdl = youtube_dl.YoutubeDL({
    'format': 'bestaudio/best',
    'outtmpl': os.path.join(FILESPATH, 'youtube', '%(extractor)s-%(id)s-%(title)s.%(ext)s'),
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': True,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'ffmpeg_location': FILESPATH,
    # bind to ipv4 since ipv6 addresses cause issues sometimes
    'source_address': '0.0.0.0'
})

class AudioManager():
    def __init__(self, ctx):
        self.guild = ctx.guild
        self.loop = ctx.bot.loop
        self.database = ctx.database
        self.bot = ctx.bot
        
    async def playlist(self):
        return await self.database.get_playlist()

    async def refetchUrlIfYouTube(self, watchurl:str):
        if "youtube.com" in watchurl:
            data = await self.loop.run_in_executor(None, lambda: _ytdl.extract_info(watchurl, download=False))
            return [f for f in (data["entries"][0]["formats"] if "entries" in data else data["formats"]) if not f["acodec"] is None][0]
        else:
            return watchurl

    async def getSongs(self, query: str):
        data = await self.loop.run_in_executor(None, lambda: _ytdl.extract_info(query, download=False))

        if data:
            if 'entries' in data:
                return [await self.database.getOrCreateAudioSourceFromDict(d) for d in data['entries'] if not d is None]
            return [await self.database.getOrCreateAudioSourceFromDict(data)]
        return []

    async def getInfoEmbedData(self, query: str):
        data = await self.loop.run_in_executor(None, lambda: _ytdl.extract_info(query, download=False))

        if data:
            if DEBUG:
                with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "_debug.test.json"), "w+") as f:
                    import json
                    f.write(json.dumps(data, indent=2))

            if "entries" in data:
                if len(data["entries"]) > 1:
                    entries = list(entry for entry in data["entries"] if not entry is None)
                    return {
                        "title": "Playlist",
                        "description": f"{len(entries)} Stücke",
                        "authorname": data.get("title", "Unbekannt"),
                        "authorurl": data["webpage_url"] if "webpage_url" in data and "http" in data["webpage_url"] else ""
                    }
                else:
                    data = data["entries"][0]
            src = await self.database.getOrCreateAudioSourceFromDict(data)
            return {
                "title": src.title,
                "authorname": src.uploader_name,
                "authorurl": src.uploader_url,
                "description": src.description,
                "thumbnailurl": src.url_thumbnail,
                "inline": True,
                "fields": [
                    ("Dauer", src.duration_calc),
                    ("Ansehen/Anhören", f"[Hier klicken]({src.url_watch})")
                ]
            }

    async def processQuery(self, query:str):
        sources = await self.getSongs(query)
        print(sources)



class YouTubePlayer(PCMVolumeTransformer):
    def __init__(self, filename, *, queue, data, stream=False, volume=0.5):
        source = FFmpegPCMAudio(filename, **(FFMPEG_OPTIONS_STREAM if stream else FFMPEG_OPTIONS))

        super().__init__(source, volume)

        self.queue = queue

        self.data = data

        self.url = data.get('url', '')
        self.link = data.get('webpage_url', self.url)
        self.title = data.get('title', 'Unbekannter Titel')

        self.uploader = data.get('uploader', "")
        self.uploader_url = data.get('uploader_url', "")
        self.thumbnail = data.get('thumbnail', "")
        self.description = data.get('description', "")
        self.duration = int(data.get('duration', 0))

    async def send(self, ctx, status: str = "Wird jetzt gespielt..."):
        fields = [("Ansehen/Anhören", "[Hier klicken]("+self.link+")")]
        if self.duration:
            fields.append(("Dauer", str(int(self.duration/60)) +
                           "min "+str(int(self.duration % 60))+"s"))
        if status:
            fields.append(("Status", status, False))
        await ctx.sendEmbed(
            title=self.title,
            description=((self.description if len(self.description) < 100 else self.description[0:100]+"...") if isinstance(
                self.description, str) else "Keine Beschreibung gefunden"),
            color=ctx.cog.color,
            fields=fields,
            thumbnailurl=self.thumbnail if self.thumbnail else None,
            authorname=self.uploader if self.uploader else None,
            authorurl=self.uploader_url if self.uploader_url else None,
        )

    def getinfo(self):
        return f"[{self.title}]({self.link})"

    def play(self, ctx):
        if ctx.voice_client:
            if ctx.voice_client.is_playing():
                ctx.voice_client.stop()
            ctx.voice_client.play(
                self, after=lambda e: self.queue.playNext(ctx))

    @classmethod
    async def from_url(self, url, *, queue, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: _ytdl.extract_info(url, download=not stream))

        if 'entries' in data:
            data = data['entries'][0]

        filename = data['url'] if stream else _ytdl.prepare_filename(data)
        return self(queue=queue, filename=filename, data=data, stream=stream)
