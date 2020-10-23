# pylint: disable=no-member

from django.db import models
from django.conf import settings
from django.urls import reverse
from django.utils import timezone

import time
import uuid

###


def get_discordbot_domain():
    return getattr(settings, "DISCORDBOT_DOMAIN", None)


# Create your models here.

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
            return domain+reverse("discordbot:amongus-tracker-post", args=(self.pk ,))
        else:
            return None

    def reset(self, save=False):
        self.code = ""
        self.state_ingame = False
        self.state_meeting = False
        for c in AMONGUS_PLAYER_COLORS:
            setattr(self, f'p_{c}_name', "")
            setattr(self, f'p_{c}_exists', False)
            setattr(self, f'p_{c}_alive', True)
        
        if save:
            self.save()

    def post_data(self, data:dict):
        if "api_key" in data and data["api_key"] == str(self.api_key):
            if "code" in data:
                self.code = str(data["code"])
            if "state" in data:
                if "ingame" in data["state"]:
                    self.state_ingame = bool(data["state"]["ingame"])
                if "meeting" in data["state"]:
                    self.state_meeting = bool(data["state"]["ingame"])
            if "reset" in data and data["reset"]:
                self.reset()
            if "players" in data:
                for c in data["players"]:
                    if c in AMONGUS_PLAYER_COLORS:
                        if "name" in data["players"][c]:
                            setattr(self, f'p_{c}_name', data["players"][c]["name"])
                        if "alive" in data["players"][c]:
                            setattr(self, f'p_{c}_alive', data["players"][c]["alive"])
                        if "exists" in data["players"][c]:
                            setattr(self, f'p_{c}_exists', data["players"][c]["exists"])
                            
            self.tracker_connected = True
            self.last_tracking_data = timezone.now()
            self.save()
            return {"success": True}
        else:
            return {"error": "invalid-api-key", "error_message": "API Key is missing or wrong!"}

    def get_data(self):
        players = {}

        for c in AMONGUS_PLAYER_COLORS:
            if getattr(self, f'p_{c}_exists'):
                players[c] = {
                   "name": getattr(self, f'p_{c}_name'),
                   "alive": getattr(self, f'p_{c}_alive'),
                   "userid": getattr(self, f'p_{c}_userid'),
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
