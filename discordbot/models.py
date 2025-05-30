# pylint: disable=no-member, unsubscriptable-object

import re

from asgiref.sync import sync_to_async
from django.contrib import admin
from django.db import models

from discordbot.botmodules.bots import VierGewinntBot
from discordbot.botmodules.parser import HTMLCleaner

# Basic


class Member(models.Model):
    server = models.ForeignKey("Server", on_delete=models.CASCADE)
    user = models.ForeignKey(
        "User", on_delete=models.CASCADE, related_name="servers"
    )

    settings = models.JSONField("Settings", default=dict)

    # Settings

    def getSetting(self, key, default=None):
        return self.settings.get(key, default)

    def setSetting(self, key, value):
        self.settings[key] = value

    # Others

    @admin.display(description="Mitglied")
    def __str__(self):
        return f"{self.server_id} <-> {self.user_id}"

    class Meta:
        verbose_name = "Mitglied"
        verbose_name_plural = "Mitglieder"

    objects = models.Manager()


class Server(models.Model):
    id = models.CharField("Discord ID", primary_key=True, max_length=20)
    name = models.CharField("Name", default="", blank=True, max_length=100)
    members = models.ManyToManyField("User", through="Member")

    playlist = models.ForeignKey(
        "Playlist",
        on_delete=models.SET_NULL,
        default=None,
        blank=True,
        null=True,
        related_name="+",
    )

    settings = models.JSONField("Settings", default=dict)

    # Settings

    def getSetting(self, key, default=None):
        return self.settings.get(key, default)

    def setSetting(self, key, value):
        self.settings[key] = value

    # Playlist

    @sync_to_async
    def getPlaylist(self):
        if self.playlist is None:
            self.playlist = Playlist.objects.create(
                server=self, title="Playlist in " + self.name
            )
            self.save()
        return self.playlist

    # Reports

    @admin.display(description="Reports")
    def reportCount(self):
        return self.reports.count()

    # Others

    @admin.display(description="Mitglieder")
    def memberCount(self):
        return self.members.count()

    @admin.display(description="Guild")
    def __str__(self):
        return f"{self.name} ({self.id})"

    class Meta:
        verbose_name = "Guild"
        verbose_name_plural = "Guilds"

    objects = models.Manager()


class User(models.Model):
    id = models.CharField("Discord ID", primary_key=True, max_length=20)
    name = models.CharField("Name", default="", blank=True, max_length=100)

    settings = models.JSONField("Settings", default=dict)

    # Settings

    def getSetting(self, key, default=None):
        return self.settings.get(key, default)

    def setSetting(self, key, value):
        self.settings[key] = value

    # Reports

    @admin.display(description="Reports")
    def reportCount(self, **filters):
        return self.reports.filter(**filters).count()

    @admin.display(description="Created reports")
    def createdReportCount(self, **filters):
        return self.created_reports.filter(**filters).count()

    # Servers

    @admin.display(description="Server count")
    def serverCount(self, **filters):
        return self.servers.filter(**filters).count()

    @sync_to_async
    def joinServer(self, server) -> Member:
        if not server.members.filter(id=self.id).exists():
            server.members.add(self)
        return server.members.through.objects.get(
            server__id=server.id, user__id=self.id
        )

    @property
    def mention(self):
        return "<@" + str(self.id) + ">"

    @admin.display(description="User")
    def __str__(self):
        return f"{self.name} ({self.id})"

    class Meta:
        verbose_name = "Benutzer"
        verbose_name_plural = "Benutzer"

    objects = models.Manager()


# Music


class AudioSource(models.Model):
    url_source = models.TextField("Url (Source)")

    url_watch = models.URLField("Url (Watch)", default="", blank=True)
    url_thumbnail = models.URLField("Url (Thumbnail)", default="", blank=True)

    title = models.CharField("Title", max_length=256)
    description = models.TextField("Description", max_length=2048)
    duration = models.IntegerField("Duration", default=0, blank=True)

    uploader_name = models.CharField(
        "Uploader name", max_length=256, default="", blank=True
    )
    uploader_url = models.URLField("Uploader Url", default="", blank=True)

    @classmethod
    @sync_to_async
    def create_from_dict(self, data: dict):
        # if "formats" in data:
        #     data.pop("formats")
        # if "thumbnails" in data:
        #     data.pop("thumbnails")
        # print(data)

        if not data is None:
            url_source = data.get("url", "")

            url_watch = data.get("webpage_url", url_source)[:200]
            url_thumbnail = data.get("thumbnail", "")[:200]

            title = data.get("title", "Unbekannter Titel")[:256]
            description = data.get(
                "description", "Keine Beschreibung gefunden."
            )[:2048]
            duration = int(data.get("duration", 0))

            uploader_name = data.get("uploader", "")[:256]
            uploader_url = data.get("uploader_url", "")[:200]

            return self.objects.create(
                url_source=url_source,
                url_watch=url_watch,
                url_thumbnail=url_thumbnail,
                title=title,
                description=description,
                duration=duration,
                uploader_name=uploader_name,
                uploader_url=uploader_url,
            )
        return None

    @property
    def clickable(self):
        return f"[{self.title}]({self.url_watch}) [{self.duration_calc}]"

    @property
    def duration_calc(self):
        h = str(self.duration // 3600)
        m = str(self.duration % 3600 // 60)
        s = str(self.duration % 3600 % 60)
        return f"{h}:{m}:{s}" if h != "0" else f"{m}:{s}"

    @admin.display(description="Audio source")
    def __str__(self):
        return f"{self.title} [{self.duration_calc}]"

    class Meta:
        verbose_name = "Audio source"
        verbose_name_plural = "Audio sources"

    objects = models.Manager()


class PlaylistPosition(models.Model):
    source = models.ForeignKey("AudioSource", on_delete=models.PROTECT)
    queue = models.ForeignKey("Playlist", on_delete=models.CASCADE)
    position = models.PositiveSmallIntegerField("Position")

    class Meta:
        verbose_name = "Audio queue position"
        verbose_name_plural = "Audio queue positions"

    objects = models.Manager()


class Playlist(models.Model):
    server = models.ForeignKey(
        "Server", on_delete=models.CASCADE, related_name="playlists"
    )
    title = models.CharField("Title", max_length=256, default="Server default")

    sources = models.ManyToManyField("AudioSource", through="PlaylistPosition")
    current_pos = models.PositiveSmallIntegerField(
        "Current position", default=0
    )

    @sync_to_async
    def addSource(self, source):
        pos = self.sources.count() + 1
        self.sources.add(source, through_defaults={"position": pos})
        return pos

    @sync_to_async
    def removePosition(self, pos: int):
        if (
            pos > 0
            and pos <= self.sources.count()
            and not self.current_pos == pos
        ):
            self.sources.through.objects.filter(position=pos).delete()
            for s in self.sources.through.objects.filter(position__gt=pos):
                s.position -= 1
                s.save()

    @sync_to_async
    def switchPositions(self, pos1: int, pos2: int):
        if self.sources.count() > max(pos1, pos2):
            o1 = self.sources.through.objects.get(playlist=self, position=pos1)
            o2 = self.sources.through.objects.get(playlist=self, position=pos2)
            o1.position = pos2
            o2.position = pos1
            o1.save()
            o2.save()
            return True
        return False

    @sync_to_async
    def getAll(self):
        return list(self.sources.all().order_by("position"))

    @sync_to_async
    def hasNext(self):
        return self.sources.through.objects.filter(
            playlist=self, position__gt=self.current_pos
        ).exists()

    @sync_to_async
    def next(self):
        self.current_pos += 1
        obj = self.sources.through.objects.get(
            playlist=self, position=self.current_pos
        )
        self.save()
        return obj

    class Meta:
        verbose_name = "Audio queue"
        verbose_name_plural = "Audio queues"

    objects = models.Manager()


# Support


class Report(models.Model):
    server = models.ForeignKey(
        "Server", on_delete=models.CASCADE, related_name="reports"
    )
    user = models.ForeignKey(
        "User", on_delete=models.CASCADE, related_name="reports"
    )
    reported_by = models.ForeignKey(
        "User",
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_reports",
        verbose_name="Gemeldet von",
    )

    reason = models.CharField("Grund", default="", blank=True, max_length=250)
    timestamp = models.DateTimeField("Zeitpunkt", auto_now_add=True)

    @admin.display(description="Report")
    def __str__(self):
        return "Report #" + str(self.pk)

    class Meta:
        verbose_name = "Report"
        verbose_name_plural = "Reports"

    objects = models.Manager()


# Games

# VierGewinnt

VIERGEWINNT_PLAYER_EMOJIS = ["⬛", "🟥", "🟨"]
VIERGEWINNT_WALL_EMOJI = "🟦"
VIERGEWINNT_NUMBER_EMOJIS = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]


def VIERGEWINNT_DEFAULT_GAME():
    return [[0 for _ in range(7)] for _ in range(6)]


class VierGewinntGame(models.Model):
    width = models.PositiveSmallIntegerField("Width", default=7)
    height = models.PositiveSmallIntegerField("Height", default=6)

    game = models.JSONField("Game", default=VIERGEWINNT_DEFAULT_GAME)

    finished = models.BooleanField("Finished", default=False)

    current_player = models.PositiveSmallIntegerField(
        "Current player", default=1
    )

    player_1_id = models.CharField("Player 1 ID", max_length=32)
    player_2_id = models.CharField(
        "Player 2 ID", max_length=32, default=None, null=True
    )
    winner_id = models.CharField(
        "Winner ID", max_length=32, default=None, null=True
    )

    channel_id = models.CharField("Channel ID", max_length=32)
    message_id = models.CharField("Message ID", max_length=32)

    time_created = models.DateTimeField("Time created", auto_now_add=True)
    time_edited = models.DateTimeField("Time edited", auto_now=True)

    # Create

    @classmethod
    @sync_to_async
    def creategame(self, width: int = 7, height: int = 6, **kwargs):
        width = 10 if width > 10 else 4 if width < 4 else width
        height = 4 if height < 4 else 14 if height > 14 else height
        game = [[0 for _ in range(width)] for _ in range(height)]
        print("create game", width, height, game, kwargs)
        return self.objects.create(
            width=width, height=height, game=game, **kwargs
        )

    # Show

    def _get_gameboard(self):
        W = VIERGEWINNT_WALL_EMOJI
        P = VIERGEWINNT_PLAYER_EMOJIS
        N = VIERGEWINNT_NUMBER_EMOJIS

        numberline = W + "".join(N[: int(self.width)]) + W + "\n"
        gamelines = (
            "\n".join(
                [(W + "".join([P[p] for p in row]) + W) for row in self.rows]
            )
            + "\n"
        )

        return numberline + gamelines + numberline

    def _get_players(self):
        pl = []
        for i in range(1, 2 + 1):
            pid = getattr(self, f"player_{i}_id")
            if pid is None:
                pl.append(VIERGEWINNT_PLAYER_EMOJIS[i] + " BOT")
            else:
                pl.append(VIERGEWINNT_PLAYER_EMOJIS[i] + " <@" + pid + ">")
        return "\n".join(pl)

    def _get_game_info(self):
        if self.finished:
            if self.winner_id:
                if self.winner_id == "BOT":
                    return "Das Spiel ist beendet! Du hast leider verloren!"
                return (
                    f"Das Spiel ist beendet! Gewonnen hat <@{self.winner_id}>!"
                )
            return "Das Spiel ist beendet! Unentschieden!"

        p = getattr(self, f"player_{self.current_player}_id")
        if p is None:
            return f"{VIERGEWINNT_PLAYER_EMOJIS[self.current_player]} Ich bin an der Reihe! (Berechne einen guten Zug...)"
        return f"{VIERGEWINNT_PLAYER_EMOJIS[self.current_player]} <@{p}> ist an der Reihe!"

    def get_description(self):
        return (
            self._get_game_info()
            + "\n\n"
            + self._get_players()
            + "\n\n"
            + self._get_gameboard()
        )

    get_description.short_description = "Game"

    # Get

    @property
    def rows(self):
        return self.game

    @property
    def cols(self):
        return [
            [self.rows[h][w] for h in range(self.height)]
            for w in range(self.width)
        ]

    @property
    def dias(self):
        dias = []
        w = 0
        h = self.height - 1
        while w < self.width:
            dia = []
            _w, _h = w, h

            while _w < self.width and _h < self.height:
                dia.append(self.rows[_h][_w])
                _w += 1
                _h += 1

            dias.append(dia)
            if h > 0:
                h -= 1
            else:
                w += 1
        w = 0
        h = 0
        while w < self.width:
            dia = []
            _w, _h = w, h

            while _w < self.width and _h >= 0:
                dia.append(self.rows[_h][_w])
                _w += 1
                _h -= 1

            dias.append(dia)
            if h < self.height - 1:
                h += 1
            else:
                w += 1
        return dias

    # Functions

    def _next_player(self):
        self.current_player = (
            self.current_player + 1 if self.current_player < 2 else 1
        )

    def _can_add_to_column(self, n: int):
        if n >= self.width:
            return None
        return not self.rows[0][n]

    def _add_to_column(self, n: int):
        if self._can_add_to_column(n):
            for h in range(self.height - 1, -1, -1):
                if not self.game[h][n]:
                    self.rows[h][n] = self.current_player
                    self._next_player()
                    return True
        return False

    # Checks

    def _is_full(self):
        return not 0 in self.rows[0]

    def _get_winner(self):
        for ls in [self.rows, self.cols, self.dias]:
            for l in ls:
                for i in range(len(l) - 3):
                    if (
                        (not l[i] == 0)
                        and (l[i] == l[i + 1])
                        and (l[i + 1] == l[i + 2])
                        and (l[i + 2] == l[i + 3])
                    ):
                        return l[i]
        return 0

    def is_players_turn(self, player_id):
        return getattr(
            self, "player_" + str(self.current_player) + "_id", None
        ) == str(player_id)

    def is_bots_turn(self):
        return (
            getattr(self, "player_" + str(self.current_player) + "_id", None)
            is None
        )

    # Process Input

    def process(self, col: int, playerid):
        if not (self.finished or self.winner_id):
            if self.is_players_turn(playerid):
                if self._add_to_column(col):
                    w = self._get_winner()
                    if w:
                        self.winner_id = getattr(
                            self, "player_" + str(w) + "_id", None
                        )
                        self.finished = True
                    elif self._is_full():
                        self.finished = True
                    return True
        return False

    def process_bot(self):
        if not self.finished and self.is_bots_turn():
            if self._add_to_column(
                VierGewinntBot.get_best_move(
                    board=self.game, botnr=self.current_player, maxdepth=4
                )
            ):
                w = self._get_winner()
                if w:
                    self.winner_id = "BOT"
                    self.finished = True
                elif self._is_full():
                    self.finished = True
                return True
        return False

    # Meta

    class Meta:
        verbose_name = "VierGewinnt Game"
        verbose_name_plural = "VierGewinnt Games"

    objects = models.Manager()


# Notifier


NOTIFIER_WHERE_TYPES = [
    ("channel", "Kanal"),
    ("member", "Mitglied (DM)"),
]

NOTIFIER_FREQUENCIES = [
    ("hour", "Stündlich"),
    ("minute", "Minütlich"),
]


class NotifierSource(models.Model):
    name = models.CharField(
        verbose_name="Name", default="Unbenannte Quelle", max_length=50
    )

    url = models.URLField(verbose_name="URL")

    frequency = models.CharField(
        verbose_name="Abfragehäufigkeit",
        max_length=8,
        choices=NOTIFIER_FREQUENCIES,
        default="hour",
    )

    last_hash = models.CharField("Letzter Hash", max_length=32, editable=False)

    @sync_to_async
    def fetch_update(self) -> (bool, str, list):
        "Fetches the source and returns a tuple of (updated?, data, matched_targets)"

        cleaner = HTMLCleaner.from_url(self.url)
        new_hash = cleaner.get_hash_str()
        last_hash = str(self.last_hash)
        if new_hash != last_hash:
            self.last_hash = new_hash
            self.save()

            if last_hash != "":  # Don't send on first fetch
                data = cleaner.get_data()
                targets = [
                    t for t in self.targets.all() if t.check_regex(data)
                ]
                return True, data, targets
        return False, "", []

    def __str__(self):
        return self.name

    __str__.short_description = "NotifierSource"

    class Meta:
        verbose_name = "NotifierSource"
        verbose_name_plural = "NotifierSources"

    objects = models.Manager()


class NotifierTarget(models.Model):
    source = models.ForeignKey(
        to="NotifierSource", on_delete=models.CASCADE, related_name="targets"
    )

    must_contain_regex = models.CharField(
        verbose_name="Muss Regex enthalten",
        default="",
        blank=True,
        max_length=32,
    )

    where_type = models.CharField(
        verbose_name="Wohin: Typ", max_length=8, choices=NOTIFIER_WHERE_TYPES
    )
    where_id = models.CharField(verbose_name="Wohin: ID", max_length=32)

    def check_regex(self, data):
        return (not self.must_contain_regex) or re.search(
            self.must_contain_regex, data
        )

    def __str__(self):
        return ""

    class Meta:
        verbose_name = "NotifierTarget"
        verbose_name_plural = "NotifierTargets"
