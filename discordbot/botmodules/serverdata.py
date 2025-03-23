"""Module used to manage database connections in the Discord bot"""
from typing import Type

import discord
from asgiref.sync import sync_to_async
from django.db import connection, connections
from django.db.models import Model as DjangoModel, Count

from discordbot.botmodules.audio import YouTubePlayer
from discordbot.errors import ErrorMessage
from discordbot.models import AudioSource
from discordbot.models import Member as DB_Member
from discordbot.models import Report as DB_Report
from discordbot.models import Server as DB_Server
from discordbot.models import User as DB_User


#####

class MusicQueue:
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
        return None

    async def sendNowPlaying(self, ctx):
        if ctx.voice_client and ctx.voice_client.source:
            if isinstance(ctx.voice_client.source, YouTubePlayer):
                await ctx.voice_client.source.send(ctx, status="Wird aktuell gespielt.")
        else:
            raise ErrorMessage("Aktuell wird nichts abgespielt.")

    async def sendQueue(self, ctx):
        description = "\n".join(i.getinfo() for i in self._players)
        await ctx.sendEmbed(
            title="Warteschlange",
            color=ctx.command.cog.color,
            description=description,
        )

    async def createYoutubePlayer(self, search, loop=None, stream=False):
        return await YouTubePlayer.from_url(search, queue=self, loop=loop, stream=stream)


class Server:
    _all = {}

    def __init__(self, id):
        self.id = id
        self.musicqueue = MusicQueue(server=self)
        # self.polls = {}

    @classmethod
    def getServer(self, serverid: int):
        if not serverid in self._all:
            self._all[serverid] = Server(serverid)
        return self._all[serverid]


# NEW


class DjangoConnection:
    def __init__(self, dc_user: discord.User, dc_guild: discord.Guild):
        self.dc_user = dc_user
        self.dc_guild = dc_guild
        self._db_user = None
        self._db_member = None
        self._db_server = None
        self._db_playlist = None

    @classmethod
    def ensure_connection(self):
        if connection.connection and not connection.is_usable():
            del connections._connections.default

    @classmethod
    def from_interaction(cls, interaction: discord.Interaction):
        return cls(interaction.user, interaction.guild)

    # Basic Methods

    @classmethod
    @sync_to_async
    def _save(cls, obj: DjangoModel) -> None:
        "Saves the given object"
        cls.ensure_connection()
        obj.save()

    @classmethod
    @sync_to_async
    def _delete(cls, obj: DjangoModel) -> None:
        "Deletes the given object"
        cls.ensure_connection()
        obj.delete()

    @classmethod
    async def _create(cls, model: Type[DjangoModel], **kwargs) -> DjangoModel:
        "Creates a new object and returns it"
        cls.ensure_connection()
        return await model.objects.acreate(**kwargs)

    @classmethod
    async def _exists(cls, model: Type[DjangoModel], **filters) -> bool:
        "Checks if an object exists"
        cls.ensure_connection()
        return await model.objects.filter(**filters).aexists()

    @classmethod
    async def _has(cls, model: Type[DjangoModel], **filters) -> bool:
        "Synonym for ._exists"
        return await cls._exists(model, **filters)

    @classmethod
    @sync_to_async
    def _get(cls, model: Type[DjangoModel], **filters) -> DjangoModel:
        "Gets an object from the database"
        cls.ensure_connection()
        return model.objects.get(**filters)

    @classmethod
    @sync_to_async
    def _list(cls, model: Type[DjangoModel], _order_by: tuple = ("pk",), **filters) -> list:
        "Gets a list of objects matching the given filters from the database"
        cls.ensure_connection()
        return list(model.objects.filter(**filters).order_by(*_order_by))

    @classmethod
    @sync_to_async
    def _listdelete(cls, model: Type[DjangoModel], **filters) -> None:
        "Finds and deletes a Django queryset with given filters."
        cls.ensure_connection()
        model.objects.filter(**filters).delete()

    @classmethod
    async def _getdel(cls, model: Type[DjangoModel], **filters) -> bool:
        "Deletes an object with given filters if it exists and returns True, False otherwise"
        if await cls._has(model, **filters):
            obj = await cls._get(DB_Report, **filters)
            await cls._delete(obj)
            return True
        return False

    # General

    @classmethod
    async def fetch_user(cls, dc_user) -> DB_User:
        if not await cls._has(DB_User, id=str(dc_user.id)):
            user = await cls._create(DB_User, id=str(dc_user.id), name=dc_user.name)
        else:
            user = await cls._get(DB_User, id=str(dc_user.id))
            if not user.name == dc_user.name:
                user.name = dc_user.name
                await cls._save(user)
        return user

    async def get_user(self) -> DB_User:
        if self._db_user is None:
            self._db_user = await self.fetch_user(self.dc_user)
        return self._db_user

    @classmethod
    async def fetch_server(cls, dc_guild) -> DB_Server:
        if not await cls._has(DB_Server, id=str(dc_guild.id)):
            server = await cls._create(DB_Server, id=str(dc_guild.id), name=dc_guild.name)
        else:
            server = await cls._get(DB_Server, id=str(dc_guild.id))
            if not server.name == dc_guild.name:
                server.name = dc_guild.name
                await cls._save(server)
        return server

    async def get_server(self) -> DB_Server:
        if self._db_server is None:
            self._db_server = await self.fetch_server(self.dc_guild)
        return self._db_server

    async def get_member(self) -> DB_Member:
        if self._db_member is None:
            user = await self.get_user()
            server = await self.get_server()
            self._db_member = await user.joinServer(server)
        return self._db_member

    async def get_playlist(self):
        if self._db_playlist is None:
            server = await self.get_server()
            self._db_playlist = await server.getPlaylist()
        return self._db_playlist

    # Music

    @classmethod
    async def getOrCreateAudioSourceFromDict(cls, data):
        if await cls._exists(AudioSource, url_watch=data.get("webpage_url", data.get("url", None))):
            audio = await cls._get(AudioSource, url_watch=data.get("webpage_url", data.get("url")))
            audio.url_source = data.get("url", "")
            await cls._save(audio)
            return audio
        return await AudioSource.create_from_dict(data)

    # Reports

    async def create_report(self, dc_user, reason: str = ""):
        server = await self.get_server()
        user = await self.get_user()
        await user.joinServer(server)
        reported_user = await self.fetch_user(dc_user)
        await reported_user.joinServer(server)
        return await self._create(DB_Report, server=server, user=reported_user, reported_by=user, reason=reason)

    async def get_all_reports(self):
        description = ""
        async for member in DB_User.objects.prefetch_related('reports').filter(
                reports__server_id=self.dc_guild.id).annotate(
            reports_count=Count('reports')).order_by('-reports_count'):
            count = member.reports_count
            if count == 1:
                description += f"- 1 Report: {member.mention}\n"
            elif count > 1:
                description += f"- {count} Reports: {member.mention}\n"
        return description

    async def get_all_reports_for_member(self, dc_member: discord.Member):
        fields = []
        async for report in (DB_Report.objects.filter(server_id=self.dc_guild.id, user_id=dc_member.id).select_related(
                'reported_by').order_by("-timestamp")):
            fields.append((
                f"{report.timestamp.strftime('%Y/%m/%d %H:%M:%S')} ({report.pk})",
                f"{report.reported_by.mention} - {report.reason}",
                False
            ))
        return fields

    async def delete_report(self, report_id: int):
        server = await self.get_server()
        return await self._getdel(DB_Report, server=server, id=report_id)

    async def clear_reports(self, userid: int):
        server = await self.get_server()
        return await DB_Report.objects.filter(server=server, user_id=userid).adelete()
