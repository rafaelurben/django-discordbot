import time
import os
import youtube_dl
import asyncio

from discord import PCMVolumeTransformer, FFmpegPCMAudio
from discord.ext import commands

from asgiref.sync import sync_to_async

#####

filespath = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), "botfiles")

# Suppress noise about console usage from errors
youtube_dl.utils.bug_reports_message = lambda: ''

color = 0xee00ff

#####

class YouTubePlayer(PCMVolumeTransformer):
    _ytdl = youtube_dl.YoutubeDL({
        'format': 'bestaudio/best',
        'outtmpl': os.path.join(filespath,'youtube','%(extractor)s-%(id)s-%(title)s.%(ext)s'),
        'restrictfilenames': True,
        'noplaylist': True,
        'nocheckcertificate': True,
        'ignoreerrors': True,
        'logtostderr': False,
        'quiet': True,
        'no_warnings': True,
        'default_search': 'auto',
        'ffmpeg_location': filespath,
        'source_address': '0.0.0.0' # bind to ipv4 since ipv6 addresses cause issues sometimes
    })

    _ffmpeg_options = {
        'options': '-vn',
        'executable': os.path.join(filespath,"ffmpeg.exe")
    }

    def __init__(self, filename, *, queue, data, volume=0.5):
        source = FFmpegPCMAudio(filename, **self._ffmpeg_options)

        super().__init__(source, volume)

        data.pop("formats")

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

    async def send(self, ctx, status:str="Wird jetzt gespielt..."):
        fields = [("Ansehen/Anhören", "[Hier klicken]("+self.link+")")]
        if self.duration:
            fields.append(("Dauer", str(int(self.duration/60))+"min "+str(int(self.duration%60))+"s"))
        fields.append(("Status", status, False))
        await ctx.sendEmbed(
            title=self.title,
            description=((self.description if len(self.description) < 100 else self.description[0:100]+"...") if isinstance(self.description, str) else "Keine Beschreibung gefunden"),
            color=ctx.cog.color,
            fields=fields,
            thumbnailurl=self.thumbnail if self.thumbnail else None,
            authorname=self.uploader if self.uploader else None,
            authorurl=self.uploader_url if self.uploader_url else None,
        )

    def play(self, ctx):
        if ctx.voice_client and ctx.voice_client.is_playing():
            ctx.voice_client.stop()
        elif ctx.voice_client:
            ctx.voice_client.play(self, after=lambda e: self.queue.playNext(ctx))


    @classmethod
    async def from_url(self, url, *, queue, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: self._ytdl.extract_info(url, download=not stream))

        if 'entries' in data:
            data = data['entries'][0]

        filename = data['url'] if stream else self._ytdl.prepare_filename(data)
        return [self(queue=queue, filename=filename, data=data)]


class MusicQueue():
    def __init__(self, server):
        self.server = server

        self._players = []

    def addPlayer(self, player):
        self._players.append(player)

    def hasPlayer(self):
        return bool(self._players)

    def playNext(self, ctx):
        if self.hasPlayer() and ctx.voice_client and ctx.voice_client.is_connected():
            player = self._players.pop(0)
            player.play(ctx)
            return player
        else:
            return None

    async def sendNowPlaying(self, ctx):
        if ctx.voice_client and ctx.voice_client.source:
            if isinstance(ctx.voice_client.source, YouTubePlayer):
                await ctx.voice_client.source.send(ctx, status="Wird jetzt gespielt!")
        else:
            raise commands.CommandError("Aktuell wird nichts abgespielt.")

    async def createYoutubePlayer(self, search, loop=None, stream=False):
        players = await YouTubePlayer.from_url(search, queue=self, loop=loop, stream=stream)
        if not stream:
            for player in players:
                self.addPlayer(player)
        return players



class Server():
    _all = {}

    def __init__(self,id):
        self.id = id
        self.musicqueue = MusicQueue(server=self)
        #self.polls = {}

    @classmethod
    def getServer(self, serverid:int):
        if not serverid in self._all:
            self._all[serverid] = Server(serverid)
        return self._all[serverid]




### NEW

from discordbot.models import Server as DB_Server, User as DB_User, Report as DB_Report, Member as DB_Member, AmongUsGame, VierGewinntGame

class DjangoConnection():
    def __init__(self, dc_user, dc_guild):
        self.dc_user = dc_user
        self.dc_guild = dc_guild
        self._db_user = None
        self._db_server = None

    @classmethod
    @sync_to_async
    def fetch_user(self, dc_user):
        if not DB_User.objects.filter(id=str(dc_user.id)).exists():
            user = DB_User.objects.create(id=str(dc_user.id), name=dc_user.name+"#"+dc_user.discriminator)
        else:
            user = DB_User.objects.get(id=str(dc_user.id))
            if not user.name == (dc_user.name+"#"+dc_user.discriminator):
                user.name = (dc_user.name+"#"+dc_user.discriminator)
                user.save()
        return user

    async def get_user(self):
        if self._db_user is None:
            self._db_user = await self.fetch_user(self.dc_user)
        return self._db_user

    @classmethod
    @sync_to_async
    def fetch_server(self, dc_guild):
        if not DB_Server.objects.filter(id=str(dc_guild.id)).exists():
            server = DB_Server.objects.create(id=str(dc_guild.id), name=dc_guild.name)
        else:
            server = DB_Server.objects.get(id=str(dc_guild.id))
            if not server.name == dc_guild.name:
                server.name = dc_guild.name
                server.save()
        return server

    async def get_server(self):
        if self._db_server is None:
            self._db_server = await self.fetch_server(self.dc_guild)
        return self._db_server

    @classmethod
    @sync_to_async
    def _join_server(self, user, server):
        user.joinServer(server)


    # Reports

    @classmethod
    @sync_to_async
    def _createReport(self, **kwargs):
        return DB_Report.objects.create(**kwargs)

    async def createReport(self, dc_user, reason:str=""):
        server = await self.get_server()
        user = await self.get_user()
        await self._join_server(user, server)
        reporteduser = await self.fetch_user(dc_user)
        await self._join_server(reporteduser, server)
        return await self._createReport(server=server, user=reporteduser, reported_by=user, reason=reason)

    @classmethod
    @sync_to_async
    def _getReports(self, server, **kwargs):
        return server.getReports(**kwargs)

    async def getReports(self, dc_user=None, **kwargs):
        server = await self.get_server()
        if dc_user is None:
            return await self._getReports(server, **kwargs)
        else:
            user = await self.fetch_user(dc_user)
            return await self._getReports(server, user=user, **kwargs)

    # AmongUs

    @classmethod
    @sync_to_async
    def _getAmongUsGame(self, **kwargs):
        return AmongUsGame.objects.get(**kwargs)

    async def getAmongUsGame(self, **kwargs):
        user = await self.get_user()
        server = await self.get_server()
        return await self._getAmongUsGame(creator=user, guild=server, **kwargs)

    @classmethod
    @sync_to_async
    def _hasAmongUsGame(self, **kwargs):
        return AmongUsGame.objects.filter(**kwargs).exists()

    async def hasAmongUsGame(self, **kwargs):
        user = await self.get_user()
        server = await self.get_server()
        return await self._hasAmongUsGame(creator=user, guild=server, **kwargs)

    @classmethod
    @sync_to_async
    def _createAmongUsGame(self, **kwargs):
        return AmongUsGame.objects.create(**kwargs)

    async def createAmongUsGame(self, **kwargs):
        user = await self.get_user()
        server = await self.get_server()
        return await self._createAmongUsGame(creator=user, guild=server, **kwargs)

    @classmethod
    @sync_to_async
    def _saveAmongUsGame(self, game: AmongUsGame):
        game.save()

    @classmethod
    @sync_to_async
    def _deleteAmongUsGame(self, game: AmongUsGame):
        game.delete()

    @classmethod
    @sync_to_async
    def _setAmongUsUser(self, game: AmongUsGame, userid: int, color: str, save: bool = False):
        game.set_user(userid=userid, color=color, save=save)

    @classmethod
    @sync_to_async
    def _removeAmongUsUser(self, game: AmongUsGame, userid: int, save: bool = False):
        game.remove_user(userid=userid, save=save)

    # VierGewinnt

    @classmethod
    @sync_to_async
    def _getVierGewinntGame(self, **kwargs):
        return VierGewinntGame.objects.get(**kwargs)

    @classmethod
    @sync_to_async
    def _hasVierGewinntGame(self, **kwargs):
        return VierGewinntGame.objects.filter(**kwargs).exists()

    @classmethod
    @sync_to_async
    def _createVierGewinntGame(self, **kwargs):
        return VierGewinntGame.create(**kwargs)

    @classmethod
    @sync_to_async
    def _saveVierGewinntGame(self, game: AmongUsGame):
        game.save()
