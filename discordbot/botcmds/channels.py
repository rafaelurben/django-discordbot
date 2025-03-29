import random
import typing

import discord
from discord import app_commands
from discord.app_commands import Choice
from discord.ext import commands

from discordbot.botmodules.serverdata import DjangoConnection
from discordbot.errors import ErrorMessage, SuccessMessage
from discordbot.models import Member as DB_Member

SETTING_SERVER_CAT_ID = "CHANNELS_CATEGORY_ID"
SETTING_SERVER_TXT_ID = "CHANNELS_TEXT_ID"
SETTING_SERVER_PUB_ID = "CHANNELS_PUBLIC_ID"
SETTING_SERVER_PRI_ID = "CHANNELS_PRIVATE_ID"

SETTING_MEMBER_TXT_ID = "CHANNELS_TEXT_ID"
SETTING_MEMBER_VOI_ID = "CHANNELS_VOICE_ID"

CATEGORY_NAME = "Benutzerkanäle"
CHANNEL_NAME_TEXT = "benutzerkanäle"
CHANNEL_NAME_PUBLIC = "Sprachkanal [offen]"
CHANNEL_NAME_PRIVATE = "Sprachkanal [privat]"

PERM_DEFAULT_NONE = discord.PermissionOverwrite(
    view_channel=False, read_messages=False, send_messages=False, connect=False)
PERM_BOT = discord.PermissionOverwrite(
    view_channel=True, read_messages=True, send_messages=True, connect=True)

PERM_CHANNEL_COMMANDS = discord.PermissionOverwrite(
    view_channel=True, read_messages=True, send_messages=True)
PERM_CHANNEL_AUTO_VOICE = discord.PermissionOverwrite(
    view_channel=True, send_messages=False, connect=True, speak=False)

PERM_VOICE_OWNER = discord.PermissionOverwrite(connect=True, speak=True, view_channel=True)
PERM_VOICE_GUEST = discord.PermissionOverwrite(connect=True, speak=True, view_channel=True)

PERM_TEXT_OWNER = discord.PermissionOverwrite(read_messages=True, send_messages=True, view_channel=True)
PERM_TEXT_GUEST = discord.PermissionOverwrite(read_messages=True, send_messages=True, view_channel=True)

CHANNEL_NAMES_RANDOM = ["RANDOM CHANNEL",
                        "[RANDOM CHANNEL]", "[HP] SORTING HAT", "SORTING HAT"]

CHANNELS_ACTIVATE_REASON = "Benutzerkanäle-Modul aktiviert."
CHANNELS_DEACTIVATE_REASON = "Benutzerkanäle-Modul deaktiviert."


# Helpers

async def get_category(dc_guild: discord.Guild, dj: DjangoConnection, raise_error=False):
    db_server = await dj.get_server()
    category_id = db_server.getSetting(SETTING_SERVER_CAT_ID)
    if category_id is None:
        if raise_error:
            raise ErrorMessage(
                "Dieses Modul wurde nicht aktiviert! Ein Administrator kann dieses Modul mit `/tmp-channels-config` aktivieren.")
        return None
    return dc_guild.get_channel(category_id)


async def get_voice_channel(dc_guild: discord.Guild, dj: DjangoConnection):
    db_member = await dj.get_member()
    channel_id = db_member.getSetting(SETTING_MEMBER_VOI_ID)
    if channel_id is None:
        return None
    return dc_guild.get_channel(channel_id)


async def get_text_channel(dc_guild: discord.Guild, dj: DjangoConnection):
    db_member = await dj.get_member()
    channel_id = db_member.getSetting(SETTING_MEMBER_TXT_ID)
    if channel_id is None:
        return None
    return dc_guild.get_channel(channel_id)


class ChannelsCog(commands.Cog, name="Channels"):
    def __init__(self, bot):
        self.bot = bot
        self.color = 0xee00ff

    # Event handlers

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState,
                                    after: discord.VoiceState):
        dj = DjangoConnection(member, member.guild)
        db_server = await dj.get_server()

        category_id = db_server.getSetting(SETTING_SERVER_CAT_ID)
        public_id = db_server.getSetting(SETTING_SERVER_PUB_ID)
        private_id = db_server.getSetting(SETTING_SERVER_PRI_ID)

        # Delete temp channel if empty
        if before.channel and before.channel.category and before.channel.members == [] and before.channel.category.id == category_id and before.channel.id not in [
            private_id, public_id
        ]:
            try:
                db_member = await DB_Member.objects.filter(server_id=member.guild.id, **{
                    f'settings__{SETTING_MEMBER_VOI_ID}': before.channel.id}).aget()
                db_member.setSetting(SETTING_MEMBER_VOI_ID, None)
                await db_member.asave()

                await before.channel.delete(reason="Benutzerkanal war leer")
            except DB_Member.DoesNotExist:
                # Do not delete channel if it is not stored in any member
                ...

        # Create new temp channel
        if after.channel and after.channel.category and after.channel.category.id == category_id and after.channel.id in [
            private_id, public_id
        ]:
            category = after.channel.category

            # Check if already exists
            channel = await get_voice_channel(member.guild, dj)
            if channel:
                await member.edit(voice_channel=channel,
                                  reason="Benutzer wollte einen Kanal erstellen, besass aber bereits einen Kanal")

            # Create new
            else:
                is_public = after.channel.id == public_id
                new_channel = await category.create_voice_channel(
                    name="user-" + member.name,
                    overwrites={
                        member: PERM_VOICE_OWNER,
                        self.bot.user: PERM_BOT,
                        member.guild.default_role: PERM_VOICE_GUEST if is_public else PERM_DEFAULT_NONE
                    },
                    reason="Benutzer hat den Sprachkanal erstellt")

                await member.edit(voice_channel=new_channel, reason="Benutzer hat den Sprachkanal erstellt")

                db_member = await dj.get_member()
                db_member.setSetting(SETTING_MEMBER_VOI_ID, new_channel.id)
                await db_member.asave()

        # Join random channel
        if after.channel and after.channel.category and (
                "[RND]" in after.channel.name.upper() or "[RANDOM]" in after.channel.name.upper() or after.channel.name.upper() in CHANNEL_NAMES_RANDOM):
            channellist = after.channel.category.voice_channels
            channellist.remove(after.channel)
            channel = random.choice(channellist)
            await member.edit(voice_channel=channel, reason="Random channel")

    # Text-channels

    tc_group = app_commands.Group(name="tmp-text",
                                  description="Erstelle deinen eigenen Textkanal und lade deine Freunde oder den ganzen Server dazu ein",
                                  guild_only=True)

    @tc_group.command(
        name="create",
        description='Erstelle deinen eigenen Textkanal',
    )
    @app_commands.checks.bot_has_permissions(manage_channels=True)
    @app_commands.describe(permission_type="Berechtigungstyp")
    @app_commands.choices(permission_type=[
        Choice(name='public (öffentlich)', value="public"),
        Choice(name='private (privat)', value="private"),
    ])
    async def text_channel_create(self, interaction: discord.Interaction, permission_type: Choice[str]):
        await interaction.response.defer(ephemeral=True)

        user = interaction.user
        guild = interaction.guild
        dj = DjangoConnection.from_interaction(interaction)

        channel = await get_text_channel(guild, dj)
        if channel:
            raise ErrorMessage("Du hast bereits einen Textkanal!", fields=[("Kanal", channel.mention)])

        category = await get_category(guild, dj, raise_error=True)

        created_channel = await category.create_text_channel(
            name=f"user-{user.name.lower()}",
            overwrites={
                guild.default_role: PERM_TEXT_GUEST if permission_type.value == "public" else PERM_DEFAULT_NONE,
                user: PERM_TEXT_OWNER,
                self.bot.user: PERM_BOT,
            },
            reason="Benutzer hat den Textkanal erstellt"
        )

        db_member = await dj.get_member()
        db_member.setSetting(SETTING_MEMBER_TXT_ID, created_channel.id)
        await db_member.asave()

        raise SuccessMessage("Textkanal erstellt!", fields=[
            ("Erstellter Kanal", created_channel.mention)])

    @tc_group.command(
        name="delete",
        description='Lösche deinen eigenen Textkanal',
    )
    @app_commands.checks.bot_has_permissions(manage_channels=True)
    async def text_channel_delete(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        dj = DjangoConnection.from_interaction(interaction)
        channel = await get_text_channel(interaction.guild, dj)

        if not channel:
            raise ErrorMessage("Du hattest gar keinen Textkanal!")

        await channel.delete(reason="Vom Benutzer gelöscht")

        db_member = await dj.get_member()
        db_member.setSetting(SETTING_MEMBER_TXT_ID, None)
        await db_member.asave()

        raise SuccessMessage("Sprachkanal gelöscht!")

    @tc_group.command(
        name="permissions",
        description='Lade jemanden in deinen Textkanal ein oder aus',
    )
    @app_commands.checks.bot_has_permissions(manage_channels=True)
    @app_commands.describe(action="Aktion", target="Benutzer/Rolle")
    @app_commands.choices(action=[
        Choice(name='add (hinzufügen)', value="add"),
        Choice(name='remove (entfernen)', value="remove"),
    ])
    async def text_channel_permissions(self, interaction: discord.Interaction, action: Choice[str],
                                       target: typing.Union[discord.Member, discord.Role]):
        await interaction.response.defer(ephemeral=True)

        if target.id == self.bot.user.id:
            raise ErrorMessage("Stopp! Lass mich selbst für meine Berechtigungen schauen!")

        dj = DjangoConnection.from_interaction(interaction)
        channel = await get_text_channel(interaction.guild, dj)

        if not channel:
            raise ErrorMessage("Du hast noch keinen Textkanal!")

        if action.value == "add":
            await channel.set_permissions(target, overwrite=PERM_TEXT_GUEST,
                                          reason="Benutzer hat Benutzer/Rolle eingeladen")

            raise SuccessMessage("Zu Textkanal eingeladen", fields=[
                ("Rolle" if isinstance(target, discord.Role) else "Benutzer", target.mention),
                ("Kanal", channel.mention)
            ])
        elif action.value == "remove":
            await channel.set_permissions(target, overwrite=PERM_DEFAULT_NONE,
                                          reason="Benutzer hat Benutzer/Rolle entfernt")

            raise SuccessMessage("Einladung zu Textkanal entzogen", fields=[
                ("Rolle" if isinstance(target, discord.Role) else "Benutzer", target.mention),
                ("Kanal", channel.mention)
            ])

    # Voice-channels

    vc_group = app_commands.Group(name="tmp-voice",
                                  description="Erstelle deinen eigenen Sprachkanal und lade deine Freunde oder den ganzen Server dazu ein",
                                  guild_only=True)

    @vc_group.command(
        name="create",
        description='Erstelle deinen eigenen Sprachkanal',
    )
    @app_commands.checks.bot_has_permissions(manage_channels=True)
    @app_commands.describe(permission_type="Berechtigungstyp")
    @app_commands.choices(permission_type=[
        Choice(name='public (öffentlich)', value="public"),
        Choice(name='private (privat)', value="private"),
    ])
    async def voice_channel_create(self, interaction: discord.Interaction, permission_type: Choice[str]):
        await interaction.response.defer(ephemeral=True)

        user = interaction.user
        guild = interaction.guild
        dj = DjangoConnection.from_interaction(interaction)

        channel = await get_voice_channel(guild, dj)
        if channel:
            if user.voice:
                await user.edit(voice_channel=channel,
                                reason="Benutzer wollte einen Kanal erstellen, besass aber bereits einen.")
            raise ErrorMessage("Du hast bereits einen Sprachkanal!", fields=[("Kanal", channel.mention)])

        category = await get_category(guild, dj, raise_error=True)

        created_channel = await category.create_voice_channel(
            name=f"user-{user.name.lower()}",
            overwrites={
                guild.default_role: PERM_TEXT_GUEST if permission_type.value == "public" else PERM_DEFAULT_NONE,
                user: PERM_TEXT_OWNER,
                self.bot.user: PERM_BOT,
            },
            reason="Benutzer hat den Sprachkanal erstellt"
        )

        db_member = await dj.get_member()
        db_member.setSetting(SETTING_MEMBER_VOI_ID, created_channel.id)
        await db_member.asave()

        if user.voice:
            await user.edit(voice_channel=created_channel, reason="Benutzer hat den Sprachkanal erstellt")
        raise SuccessMessage("Sprachkanal erstellt!", fields=[
            ("Erstellter Kanal", created_channel.mention)])

    @vc_group.command(
        name="delete",
        description='Lösche deinen eigenen Sprachkanal',
    )
    @app_commands.checks.bot_has_permissions(manage_channels=True)
    async def voice_channel_delete(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        dj = DjangoConnection.from_interaction(interaction)
        channel = await get_voice_channel(interaction.guild, dj)

        if not channel:
            raise ErrorMessage("Du hattest gar keinen Sprachkanal!")

        await channel.delete(reason="Vom Benutzer gelöscht")

        db_member = await dj.get_member()
        db_member.setSetting(SETTING_MEMBER_VOI_ID, None)
        await db_member.asave()

        raise SuccessMessage("Sprachkanal gelöscht!")

    @vc_group.command(
        name="permissions",
        description='Lade jemanden in deinen Sprachkanal ein oder aus',
    )
    @app_commands.checks.bot_has_permissions(manage_channels=True)
    @app_commands.describe(action="Aktion", target="Benutzer/Rolle")
    @app_commands.choices(action=[
        Choice(name='add', value="add"),
        Choice(name='remove', value="remove"),
    ])
    async def voice_channel_permissions(self, interaction: discord.Interaction, action: Choice[str],
                                        target: typing.Union[discord.Member, discord.Role]):
        await interaction.response.defer(ephemeral=True)

        if target.id == self.bot.user.id:
            raise ErrorMessage("Stopp! Lass mich selbst für meine Berechtigungen schauen!")

        dj = DjangoConnection.from_interaction(interaction)
        channel = await get_voice_channel(interaction.guild, dj)

        if not channel:
            raise ErrorMessage("Du hast noch keinen Sprachkanal!")

        if action.value == "add":
            await channel.set_permissions(target, overwrite=PERM_VOICE_GUEST,
                                          reason="Benutzer hat Benutzer/Rolle eingeladen")

            raise SuccessMessage("Zu Sprachkanal eingeladen", fields=[
                ("Rolle" if isinstance(target, discord.Role) else "Benutzer", target.mention),
                ("Kanal", channel.mention)
            ])
        elif action.value == "remove":
            await channel.set_permissions(target, overwrite=PERM_DEFAULT_NONE,
                                          reason="Benutzer hat Benutzer/Rolle entfernt")

            raise SuccessMessage("Einladung zu Sprachkanal entzogen", fields=[
                ("Rolle" if isinstance(target, discord.Role) else "Benutzer", target.mention),
                ("Kanal", channel.mention)
            ])

    # Channels (General)

    @app_commands.command(
        name="tmp-channels-config",
        description="Konfiguriere das Benutzerkanäle-Modul",
        extras={'help': "Verwende diesen Befehl, um das Modul 'Benutzerkanäle' zu aktivieren oder deaktivieren."}
    )
    @app_commands.guild_only
    @app_commands.default_permissions(manage_channels=True)
    @app_commands.checks.bot_has_permissions(manage_channels=True)
    @app_commands.describe(action="Die auszuführende Aktion")
    @app_commands.choices(action=[
        Choice(name='activate (alle Kanäle erstellen)', value="activate"),
        Choice(name='deactivate (alle Kanäle löschen)', value="deactivate"),
    ])
    async def channels_config(self, interaction: discord.Interaction, action: Choice[str]):
        await interaction.response.defer()

        dj = DjangoConnection.from_interaction(interaction)
        db_server = await dj.get_server()

        if action.value == 'activate':
            if db_server.getSetting(SETTING_SERVER_CAT_ID):
                raise ErrorMessage(
                    "Bereits eingerichtet! Falls die erstellen Kanäle aus Versehen gelöscht wurden, muss du das Modul zuerst deaktivieren und anschliessend wieder aktivieren.")

            category = await interaction.guild.create_category_channel(
                name=CATEGORY_NAME,
                overwrites={
                    interaction.guild.default_role: PERM_DEFAULT_NONE,
                    self.bot.user: PERM_BOT},
                reason=CHANNELS_ACTIVATE_REASON)
            channel_text = await category.create_text_channel(
                name=CHANNEL_NAME_TEXT,
                overwrites={interaction.guild.default_role: PERM_CHANNEL_COMMANDS},
                reason=CHANNELS_ACTIVATE_REASON,
                topic="Hilfe: /help channels")
            channel_public = await category.create_voice_channel(
                name=CHANNEL_NAME_PUBLIC,
                overwrites={interaction.guild.default_role: PERM_CHANNEL_AUTO_VOICE},
                reason=CHANNELS_ACTIVATE_REASON)
            channel_private = await category.create_voice_channel(
                name=CHANNEL_NAME_PRIVATE,
                overwrites={interaction.guild.default_role: PERM_CHANNEL_AUTO_VOICE},
                reason=CHANNELS_ACTIVATE_REASON)

            db_server.setSetting(SETTING_SERVER_CAT_ID, category.id)
            db_server.setSetting(SETTING_SERVER_TXT_ID, channel_text.id)
            db_server.setSetting(SETTING_SERVER_PUB_ID, channel_public.id)
            db_server.setSetting(SETTING_SERVER_PRI_ID, channel_private.id)
            await db_server.asave()

            raise SuccessMessage(
                "Die erforderlichen Kanäle wurden erfolgreich erstellt! "
                "Die Kategorie und Kanäle dürfen nach Belieben umbenannt werden.", fields=[
                    ("Erstellte Kategorie", category.mention),
                    ("Erstellter Textkanal für Befehle", channel_text.mention),
                    ("Erstellter Sprachkanal für automatische öffentliche Kanäle", channel_public.mention),
                    ("Erstellter Sprachkanal für automatische private Kanäle", channel_private.mention)
                ], inline=False)
        elif action.value == 'deactivate':
            if not db_server.getSetting(SETTING_SERVER_CAT_ID):
                raise ErrorMessage(
                    "Nicht eingerichtet! Dieses Modul wurde nicht eingerichtet.")

            for setting_name in [SETTING_SERVER_PRI_ID, SETTING_SERVER_PUB_ID, SETTING_SERVER_TXT_ID,
                                 SETTING_SERVER_CAT_ID]:
                category = interaction.guild.get_channel(db_server.getSetting(setting_name))
                if category:
                    await category.delete(reason=CHANNELS_DEACTIVATE_REASON)
                db_server.setSetting(setting_name, None)

            await db_server.asave()

            # Clear existing channels
            for var_name in [SETTING_MEMBER_VOI_ID, SETTING_MEMBER_TXT_ID]:
                async for member in DB_Member.objects.filter(
                        server_id=interaction.guild.id,
                        settings__has_key=var_name,
                        **{f'settings__{var_name}__isnull': False}
                ):
                    channel_id = member.getSetting(var_name)
                    member.setSetting(var_name, None)
                    await member.asave()

                    channel = interaction.guild.get_channel(channel_id)
                    if channel:
                        await channel.delete()

            raise SuccessMessage("Kanäle erfolgreich gelöscht!")
        else:
            raise ErrorMessage("Unbekannte Aktion: " + action.value)


async def setup(bot):
    await bot.add_cog(ChannelsCog(bot))
