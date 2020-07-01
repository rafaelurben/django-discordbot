from django.db import models

import time

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
