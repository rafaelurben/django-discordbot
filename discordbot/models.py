# pylint: disable=no-member, unsubscriptable-object

from django.db import models
from django.conf import settings
from django.urls import reverse
from django.utils import timezone

import time
import uuid

# Helper functions


def get_discordbot_domain():
    return getattr(settings, "DISCORDBOT_DOMAIN", None)


# Basic

class Member(models.Model):
    server = models.ForeignKey("Server", on_delete=models.CASCADE)
    user = models.ForeignKey("User", on_delete=models.CASCADE, related_name="servers")

    def __str__(self):
        return str(self.server.name)+" - "+str(self.user.name)
    __str__.short_description = "Mitglied"

    class Meta():
        verbose_name = "Mitglied"
        verbose_name_plural = "Mitglieder"

    objects = models.Manager()

class Server(models.Model):
    id = models.CharField("Discord ID", primary_key=True, max_length=20)
    name = models.CharField("Name", default="", blank=True, max_length=100)
    members = models.ManyToManyField("User", through="Member")

    def reportCount(self):
        return self.reports.count()
    reportCount.short_description = "Reports"

    def getReports(self, user=None):
        if user is None:
            reports = []
            for member in self.members.all():
                count = member.reportCount()
                if count > 0:
                    reports.append({
                        "name": str(count)+" Report(s)",
                        "value": member.mention,
                        "inline": False
                    })
            return reports
        else:
            return user.getReports(server=self)

    def memberCount(self):
        return self.members.count()

    def __str__(self):
        return self.name+" ("+str(self.id)+")"
    __str__.short_description = "Server"

    class Meta():
        verbose_name = "Server"
        verbose_name_plural = "Server"

    objects = models.Manager()

class User(models.Model):
    id = models.CharField("Discord ID", primary_key=True, max_length=20)
    name = models.CharField("Name", default="", blank=True, max_length=100)

    def reportCount(self):
        return self.reports.count()
    reportCount.short_description = "Reports"

    def createdReportCount(self):
        return self.created_reports.count()
    createdReportCount.short_description = "Erstellte Reports"

    def serverCount(self):
        return self.servers.count()
    serverCount.short_description = "Anzahl Server"

    def joinServer(self, server):
        if not server.members.filter(id=self.id).exists():
            server.members.add(self)

    def getReports(self, server=None):
        if server is None:
            reports = self.reports.all()
        else:
            reports = self.reports.filter(server=server)
        return [
            report.getEmbedField() for report in reports
        ]

    @property
    def mention(self):
        return "<@"+str(self.id)+">"

    def __str__(self):
        return self.name+" ("+str(self.id)+")"
    __str__.short_description = "User"

    class Meta():
        verbose_name = "Benutzer"
        verbose_name_plural = "Benutzer"
    
    objects = models.Manager()

# Support

class Report(models.Model):
    server = models.ForeignKey("Server", on_delete=models.CASCADE, related_name="reports")
    user = models.ForeignKey("User", on_delete=models.CASCADE, related_name="reports")
    reported_by = models.ForeignKey("User", on_delete=models.SET_NULL, null=True, related_name="created_reports", verbose_name="Gemeldet von")

    reason = models.CharField("Grund", default="", blank=True, max_length=250)
    timestamp = models.DateTimeField("Zeitpunkt", auto_now_add=True)

    def getEmbedField(self):
        return {
            "name": str(self.timestamp.strftime('%d.%m.%Y - %H:%M:%S')),
            "value": str(self.reason)+" - "+self.reported_by.mention,
            "inline": False
        }

    def __str__(self):
        return "Report #"+str(self.pk)
    __str__.short_description = "Report"

    class Meta():
        verbose_name = "Report"
        verbose_name_plural = "Reports"

    objects = models.Manager()

# Games

## AmongUs

AMONGUS_PLAYER_COLORS = {
    'red':      ("#C51111", (179, 17, 17),   ":heart:",                 '❤'),
    'blue':     ("#132FD2", (19, 47, 210),   ":blue_heart:",            '💙'),
    'green':    ("#127F2D", (18, 127, 45),   ":green_heart:",           '💚'),
    'pink':     ("#ED53B9", (237, 83, 185),  ":heartpulse:",            '💗'),
    'orange':   ("#EF7D0E", (239, 125, 14),  ":orange_heart:",          '🧡'),
    'yellow':   ("#F3F558", (243, 246, 88),  ":yellow_heart:",          '💛'),
    'black':    ("#3F484E", (63, 72, 78),    ":black_heart:",           '🖤'),
    'white':    ("#D5E0EF", (213, 224, 239), ":white_heart:",           '🤍'),
    'purple':   ("#6B30BC", (107, 48, 188),  ":purple_heart:",          '💜'),
    'brown':    ("#72491E", (114, 37, 30),   ":brown_heart:",           '🤎'),
    'cyan':     ("#39FEDB", (57, 254, 219),  ":regional_indicator_c:",  '🇨'),
    'lime':     ("#50EF3A", (80, 239, 58),   ":regional_indicator_l:",  '🇱'),
}

AMONGUS_EMOJI_COLORS = {v[3]: k for k, v in AMONGUS_PLAYER_COLORS.items()}

class AmongUsGame(models.Model):
    api_key = models.UUIDField("API Key", default=uuid.uuid4)

    creator = models.ForeignKey("User", on_delete=models.CASCADE)
    guild = models.ForeignKey("Server", on_delete=models.CASCADE)
    
    voice_channel_id = models.CharField("Voice channel ID", max_length=20)
    text_channel_id = models.CharField("Text channel ID", max_length=20)
    text_message_id = models.CharField("Text message ID", max_length=20, default=None, null=True)

    code = models.CharField("Gamecode", max_length=6, default="", blank=True)

    last_edited = models.DateTimeField("Last edited", auto_now=True)
    last_tracking_data = models.DateTimeField("Last tracking data", default=None, null=True)

    state_ingame = models.BooleanField("In game", default=False)
    state_meeting = models.BooleanField("Meeting ongoing", default=False)

    p_red_name = models.CharField("Red's name", max_length=50, default="", blank=True)
    p_red_alive = models.BooleanField("Red's alive", default=True)
    p_red_exists = models.BooleanField("Red exists", default=False)
    p_red_userid = models.CharField("Red's Discord ID", max_length=50, default="", blank=True)
    p_blue_name = models.CharField("Blue's name", max_length=50, default="", blank=True)
    p_blue_alive = models.BooleanField("Blue's alive", default=True)
    p_blue_exists = models.BooleanField("Blue exists", default=False)
    p_blue_userid = models.CharField("Blue's Discord ID", max_length=50, default="", blank=True)
    p_green_name = models.CharField("Green's name", max_length=50, default="", blank=True)
    p_green_alive = models.BooleanField("Green's alive", default=True)
    p_green_exists = models.BooleanField("Green exists", default=False)
    p_green_userid = models.CharField("Green's Discord ID", max_length=50, default="", blank=True)
    p_pink_name = models.CharField("Pink's name", max_length=50, default="", blank=True)
    p_pink_alive = models.BooleanField("Pink's alive", default=True)
    p_pink_exists = models.BooleanField("Pink exists", default=False)
    p_pink_userid = models.CharField("Pink's Discord ID", max_length=50, default="", blank=True)
    p_orange_name = models.CharField("Orange's name", max_length=50, default="", blank=True)
    p_orange_alive = models.BooleanField("Orange's alive", default=True)
    p_orange_exists = models.BooleanField("Orange exists", default=False)
    p_orange_userid = models.CharField("Orange's Discord ID", max_length=50, default="", blank=True)
    p_yellow_name = models.CharField("Yellow's name", max_length=50, default="", blank=True)
    p_yellow_alive = models.BooleanField("Yellow's alive", default=True)
    p_yellow_exists = models.BooleanField("Yellow exists", default=False)
    p_yellow_userid = models.CharField("Yellow's Discord ID", max_length=50, default="", blank=True)
    p_black_name = models.CharField("Black's name", max_length=50, default="", blank=True)
    p_black_alive = models.BooleanField("Black's alive", default=True)
    p_black_exists = models.BooleanField("Black exists", default=False)
    p_black_userid = models.CharField("Black's Discord ID", max_length=50, default="", blank=True)
    p_white_name = models.CharField("White's name", max_length=50, default="", blank=True)
    p_white_alive = models.BooleanField("White's alive", default=True)
    p_white_exists = models.BooleanField("White exists", default=False)
    p_white_userid = models.CharField("White's Discord ID", max_length=50, default="", blank=True)
    p_purple_name = models.CharField("Purple's name", max_length=50, default="", blank=True)
    p_purple_alive = models.BooleanField("Purple's alive", default=True)
    p_purple_exists = models.BooleanField("Purple exists", default=False)
    p_purple_userid = models.CharField("Purple's Discord ID", max_length=50, default="", blank=True)
    p_brown_name = models.CharField("Brown's name", max_length=50, default="", blank=True)
    p_brown_alive = models.BooleanField("Brown's alive", default=True)
    p_brown_exists = models.BooleanField("Brown exists", default=False)
    p_brown_userid = models.CharField("Brown's Discord ID", max_length=50, default="", blank=True)
    p_cyan_name = models.CharField("Cyan's name", max_length=50, default="", blank=True)
    p_cyan_alive = models.BooleanField("Cyan's alive", default=True)
    p_cyan_exists = models.BooleanField("Cyan exists", default=False)
    p_cyan_userid = models.CharField("Cyan's Discord ID", max_length=50, default="", blank=True)
    p_lime_name = models.CharField("Lime's name", max_length=50, default="", blank=True)
    p_lime_alive = models.BooleanField("Lime's alive", default=True)
    p_lime_exists = models.BooleanField("Lime exists", default=False)
    p_lime_userid = models.CharField("Lime's Discord ID", max_length=50, default="", blank=True)

    
    def get_tracker_url(self):
        domain = get_discordbot_domain()
        if domain:
            return domain+reverse("discordbot:amongus-tracker-post")
        else:
            return "Frage den Bot-Owner!"

    def reset(self):
        self.code = ""
        self.state_ingame = False
        self.state_meeting = False
        for c in AMONGUS_PLAYER_COLORS:
            setattr(self, f'p_{c}_name', "")
            setattr(self, f'p_{c}_exists', False)
            setattr(self, f'p_{c}_alive', True)

    def post_data(self, data:dict):
        if "api_key" in data and data["api_key"] == str(self.api_key):
            if "reset" in data and data["reset"]:
                self.reset()
            if "code" in data:
                self.code = str(data["code"])
            if "state" in data:
                if "ingame" in data["state"]:
                    self.state_ingame = bool(data["state"]["ingame"])
                if "meeting" in data["state"]:
                    self.state_meeting = bool(data["state"]["meeting"])
            if "players" in data:
                for c in data["players"]:
                    if c in AMONGUS_PLAYER_COLORS:
                        if "name" in data["players"][c]:
                            setattr(self, f'p_{c}_name', data["players"][c]["name"])
                        if "alive" in data["players"][c]:
                            setattr(self, f'p_{c}_alive', data["players"][c]["alive"])
                        if "exists" in data["players"][c]:
                            setattr(self, f'p_{c}_exists', data["players"][c]["exists"])
                            
            self.last_tracking_data = timezone.now()
            self.save()
            return {"success": True}
        else:
            return {"error": "invalid-api-key", "error_message": "API Key is missing or wrong!"}

    def get_data(self):
        players = {c: {
                "name": getattr(self, f'p_{c}_name'),
                "alive": getattr(self, f'p_{c}_alive'),
                "userid": getattr(self, f'p_{c}_userid'),
                "exists": getattr(self, f'p_{c}_exists'),
            } for c in AMONGUS_PLAYER_COLORS
        }

        return {
            "id": self.pk,
            "code": self.code,
            "state": {
                "ingame": self.state_ingame,
                "meeting": self.state_meeting,
            },
            "players": players,
            "last_edited": self.last_edited,
            "last_tracking_data": self.last_tracking_data,
        }

    # User

    def remove_user(self, userid, save=False):
        for c in AMONGUS_PLAYER_COLORS:
            if getattr(self, f'p_{c}_userid') == str(userid):
                setattr(self, f'p_{c}_userid', "")

        if save:
            self.save()

    def set_user(self, userid, color, save=False):
        self.remove_user(userid)
        setattr(self, f'p_{color}_userid', str(userid))

        if save:
            self.save()


    def __str__(self):
        return "AmongUs #"+str(self.pk)

    class Meta:
        verbose_name = 'AmongUs Game'
        verbose_name_plural = 'AmongUs Games'
        unique_together = ('guild', 'creator',)

    objects = models.Manager()


## VierGewinnt

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

    current_player = models.PositiveSmallIntegerField("Current player", default=1)

    player_1_id = models.CharField("Player 1 ID", max_length=32)
    player_2_id = models.CharField("Player 2 ID", max_length=32, default=None, null=True)
    winner_id = models.CharField("Winner ID", max_length=32, default=None, null=True)

    channel_id = models.CharField("Channel ID", max_length=32)
    message_id = models.CharField("Message ID", max_length=32)

    time_created = models.DateTimeField("Time created", auto_now_add=True)
    time_edited = models.DateTimeField("Time edited", auto_now=True)

    # Create

    @classmethod
    def create(self, width:int=7, height:int=6, **kwargs):
        width = 10 if width > 10 else 4 if width < 4 else width
        height = 4 if height < 4 else 14 if height > 14 else height
        kwargs["game"] = [[0 for _ in range(width)] for _ in range(height)]
        return self.objects.create(width=width, height=height, **kwargs)

    # Show

    def _get_gameboard(self):
        W = VIERGEWINNT_WALL_EMOJI
        P = VIERGEWINNT_PLAYER_EMOJIS
        N = VIERGEWINNT_NUMBER_EMOJIS

        numberline = (W+"".join(N[:int(self.width)])+W+"\n")
        gamelines = "\n".join([(W+"".join([P[p] for p in row])+W) for row in self.rows])+"\n"
        
        return numberline + gamelines + numberline

    def _get_players(self):
        return "\n".join([
            VIERGEWINNT_PLAYER_EMOJIS[i]+" <@"+getattr(self, "player_"+str(i)+"_id")+">" 
            for i in range(1, 2+1)
        ])

    def _get_game_info(self):
        if self.finished:
            if self.winner_id:
                return f"Das Spiel ist beendet! Gewonnen hat <@{self.winner_id}>"
            return "Das Spiel ist beendet! Unentschieden!"
        else:
            return VIERGEWINNT_PLAYER_EMOJIS[self.current_player]+" ist an der Reihe!" 

    def get_description(self):
        return self._get_game_info()+"\n\n"+self._get_players()+"\n\n"+self._get_gameboard()

    # Get

    @property
    def rows(self):
        return self.game

    @property
    def cols(self):
        return [[self.rows[h][w] for h in range(self.height)] for w in range(self.width)]

    @property
    def dias(self):
        dias = []
        w = 0 
        h = self.height-1
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
            if h < self.height-1:
                h += 1
            else:
                w += 1
        return dias

    # Functions

    def _next_player(self):
        self.current_player = (self.current_player+1 if self.current_player < 2 else 1)

    def _can_add_to_column(self, n: int):
        if n >= self.width:
            return None
        return not self.rows[0][n]

    def _add_to_column(self, n:int):
        if self._can_add_to_column(n):
            for h in range(self.height-1, -1, -1):
                if not self.game[h][n]:
                    self.rows[h][n] = self.current_player
                    self._next_player()
                    return True
        else:
            return False

    # Checks

    def _is_full(self):
        return not 0 in self.rows[0]

    def _get_winner(self):
        for ls in [self.rows, self.cols, self.dias]:
            for l in ls:
                for i in range(len(l)-3):
                    if (not l[i] == 0) and (l[i] == l[i+1]) and (l[i+1] == l[i+2]) and (l[i+2] == l[i+3]):
                        return l[i]
        return 0

    # Process Input

    def process(self, col:int, playerid):
        if not (self.finished or self.winner_id):
            if getattr(self, "player_"+str(self.current_player)+"_id", None) == str(playerid):
                if self._add_to_column(col):
                    w = self._get_winner()
                    if w:
                        self.winner_id = getattr(self, "player_"+str(w)+"_id", None)
                        self.finished = True
                    elif self._is_full():
                        self.finished = True
                    return True
        return False

    # Meta

    class Meta:
        verbose_name = 'VierGewinnt Game'
        verbose_name_plural = 'VierGewinnt Games'

    objects = models.Manager()
