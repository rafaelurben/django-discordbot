from django.contrib import admin

from .models import (
    Member,
    NotifierSource,
    NotifierTarget,
    Report,
    Server,
    User,
    VierGewinntGame,
)

# General


class ServerAdminMemberInline(admin.TabularInline):
    model = Member
    extra = 0

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class ServerAdminReportInline(admin.TabularInline):
    model = Report
    fk_name = "server"
    extra = 0
    verbose_name_plural = "Reports auf diesem Server"

    readonly_fields = ("reported_by",)

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(Server)
class ServerAdmin(admin.ModelAdmin):
    fields = ("id", "name", "settings")
    readonly_fields = ("id", "name")

    list_display = ("id", "name", "reportCount")

    inlines = [ServerAdminReportInline, ServerAdminMemberInline]

    def has_add_permission(self, request):
        return False


class UserAdminReportInline(admin.TabularInline):
    model = Report
    fk_name = "user"
    extra = 0
    verbose_name_plural = "Reports gegen diesen Benutzer"

    readonly_fields = ("reported_by",)

    def has_change_permission(self, request, obj=None):
        return False


class UserAdminReportCreatedInline(admin.TabularInline):
    model = Report
    fk_name = "reported_by"
    extra = 0
    verbose_name_plural = "Reports von diesem Benutzer"

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False


class UserAdminServerInline(admin.TabularInline):
    model = Member
    extra = 0
    verbose_name_plural = "Server"

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    fields = ("id", "name", "settings")
    readonly_fields = ("id", "name")

    list_display = ("id", "name", "reportCount", "createdReportCount")

    inlines = [
        UserAdminReportInline,
        UserAdminReportCreatedInline,
        UserAdminServerInline,
    ]

    def has_add_permission(self, request):
        return False


# Games


@admin.register(VierGewinntGame)
class VierGewinntAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "player_1_id",
        "player_2_id",
        "finished",
        "winner_id",
        "time_edited",
        "time_created",
    )
    ordering = ("id",)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    fields = ("get_description",)
    readonly_fields = ("get_description",)


# Notifier


class NotifierSourceTargetInline(admin.TabularInline):
    model = NotifierTarget
    extra = 0

    fields = ("where_type", "where_id", "must_contain_regex")


@admin.register(NotifierSource)
class NotifierSourceAdmin(admin.ModelAdmin):
    list_display = ("name", "frequency", "url")
    ordering = ("id",)

    inlines = [NotifierSourceTargetInline]

    fieldsets = [
        (None, {"fields": ("name",)}),
        ("Herkunft", {"fields": ("url",)}),
        ("Einstellungen", {"fields": ("frequency",)}),
    ]
