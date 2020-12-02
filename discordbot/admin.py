from django.contrib import admin
from .models import Server, User, Report, Member, AmongUsGame, AMONGUS_PLAYER_COLORS, VierGewinntGame, NotifierSub

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
    fields = ("id","name")
    readonly_fields = ("id","name")

    list_display = ("id","name","reportCount")

    inlines = [ServerAdminReportInline, ServerAdminMemberInline]

    def has_add_permission(self, request, obj=None):
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
    fields = ("id","name")
    readonly_fields = ("id","name")

    list_display = ("id","name","reportCount","createdReportCount")

    inlines = [UserAdminReportInline, UserAdminReportCreatedInline, UserAdminServerInline]

    def has_add_permission(self, request, obj=None):
        return False

# Games

@admin.register(AmongUsGame)
class AmongUsGameAdmin(admin.ModelAdmin):
    list_display = ('id', 'code', 'state_ingame', 'state_meeting', 'creator')
    ordering = ('code', )

    readonly_fields = ("last_tracking_data", "last_edited",)

    fieldsets = [
        ('Info', {'fields': ('code', )}),
        ('Times', {'fields': ('last_tracking_data', 'last_edited')}),
        ('State', {'fields': ('state_ingame', 'state_meeting', )}),
        ('Players', {'fields': 
            tuple((f'p_{c}_name', f'p_{c}_alive', f'p_{c}_exists', f'p_{c}_userid') 
            for c in AMONGUS_PLAYER_COLORS)
        }),
    ]

    def has_add_permission(self, request, obj=None):
        return False

@admin.register(VierGewinntGame)
class VierGewinntAdmin(admin.ModelAdmin):
    list_display = ('id', 'player_1_id', 'player_2_id', 'finished', 'winner_id', 'time_edited', 'time_created')
    ordering = ('id',)

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    fields = ('get_description',)
    readonly_fields = ('get_description',)

@admin.register(NotifierSub)
class NotifierSubAdmin(admin.ModelAdmin):
    list_display = ('name', 'where_type', 'where_id', 'frequency', 'url', 'must_contain_regex',)
    ordering = ('id',)

    fieldsets = [
        ("",        {"fields": ('name',)}),
        ("Ziel",    {"fields": ('where_type', 'where_id',)}),
        ("Herkunft",{"fields": ('url', 'frequency')}),
        ("Filter",  {"fields": ('must_contain_regex',)})
    ]
