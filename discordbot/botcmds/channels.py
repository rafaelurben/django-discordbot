from discord.ext import commands
from discord import Member, utils, PermissionOverwrite, Role, CategoryChannel
from discordbot.errors import ErrorMessage, SuccessMessage

from discordbot.botmodules.serverdata import DjangoConnection

import typing
import random

CHANNEL_NAMES_DEFAULT = ["SPRACHKANAL",
                         "SPRACHKANAL ERSTELLEN", "NEUER SPRACHKANAL", ]
CHANNEL_NAMES_PUBLIC = ["SPRACHKANAL [OFFEN]",
                        "SPRACHKANAL ERSTELLEN [OFFEN]", "NEUER SPRACHKANAL [OFFEN]", ]
CHANNEL_NAMES_PRIVATE = ["SPRACHKANAL [PRIVAT]",
                         "SPRACHKANAL ERSTELLEN [PRIVAT]", "NEUER SPRACHKANAL [PRIVAT]", ]

CHANNEL_NAME_TEXT = "benutzerkanäle"
CHANNEL_NAME_PUBLIC = "Sprachkanal [offen]"
CHANNEL_NAME_PRIVATE = "Sprachkanal [privat]"

CATEGORY_NAMES = ["BENUTZERKANÄLE", "USERCHANNELS", "USER CHANNELS",
                  "Benutzerkanäle", "Userchannels", "User channels"]
CATEGORY_NAME = "Benutzerkanäle"

PERM_VOICE_OWNER = PermissionOverwrite(connect=True, speak=True, view_channel=True, move_members=True, mute_members=True,
                                       deafen_members=True, stream=True, priority_speaker=True, use_voice_activation=True, create_instant_invite=True)
PERM_VOICE_PRIVATE = PermissionOverwrite(
    connect=False, speak=True, view_channel=True)
PERM_VOICE_PUBLIC = PermissionOverwrite(
    connect=True, speak=True, view_channel=True)

PERM_TEXT_OWNER = PermissionOverwrite(read_messages=True, read_message_history=True, send_messages=True, manage_messages=True, send_tts_messages=True,
                                      manage_webhooks=True, add_reactions=True, embed_links=True, attach_files=True, create_instant_invite=True, external_emojis=True)
PERM_TEXT_PRIVATE = PermissionOverwrite(read_messages=False)

CHANNEL_NAMES_RANDOM = ["RANDOM CHANNEL",
                        "[RANDOM CHANNEL]", "[HP] SORTING HAT", "SORTING HAT"]


async def getUserChannelCategory(guild) -> CategoryChannel:
    category = None
    for cname in CATEGORY_NAMES:
        category = utils.get(guild.categories, name=cname)
        if category is not None:
            break
    return category


class Channels(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.color = 0xee00ff

    async def get_voice_channel(self, member, category=None):
        if not category:
            category = await getUserChannelCategory(member.guild)
        channel = utils.get(member.guild.voice_channels, name=(
            member.name+"#"+member.discriminator))
        return channel

    async def get_text_channel(self, ctx):
        member = await ctx.database.get_member()
        channelid = member.getSetting("CHANNELS_TEXT_ID")
        if channelid is None:
            return None
        return ctx.guild.get_channel(channelid)

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        # Delete channel if empty
        if before.channel and before.channel.category and before.channel.category.name.upper() in CATEGORY_NAMES and "#" in before.channel.name and before.channel.members == []:
            await before.channel.delete(reason="Kanal war leer")

        # Create new channel
        if after.channel and after.channel.category and after.channel.category.name.upper() in CATEGORY_NAMES and after.channel.name.upper() in CHANNEL_NAMES_DEFAULT+CHANNEL_NAMES_PRIVATE+CHANNEL_NAMES_PUBLIC:
            category = after.channel.category
            if category:
                channel = await self.get_voice_channel(member, category)
                if channel:
                    await member.edit(voice_channel=channel, reason="Benutzer wollte einen Kanal erstellen, besitzte aber bereits einen Kanal")
                else:
                    if after.channel.name.upper() in CHANNEL_NAMES_PRIVATE:
                        overwrites = {
                            member.guild.default_role: PERM_VOICE_PRIVATE, member: PERM_VOICE_OWNER}
                    else:
                        overwrites = {
                            member.guild.default_role: PERM_VOICE_PUBLIC, member: PERM_TEXT_OWNER}
                    newchannel = await category.create_voice_channel(name=(member.name+"#"+member.discriminator), overwrites=overwrites, reason="Benutzer hat den Sprachkanal erstellt")
                    await member.edit(voice_channel=newchannel, reason="Benutzer hat den Sprachkanal erstellt")

        # Join random channel
        if after.channel and after.channel.category and ("[RND]" in after.channel.name.upper() or "[RANDOM]" in after.channel.name.upper() or after.channel.name.upper() in CHANNEL_NAMES_RANDOM):
            channellist = after.channel.category.voice_channels
            channellist.remove(after.channel)
            channel = random.choice(channellist)
            await member.edit(voice_channel=channel, reason="Random channel")

    # Textchannels

    @commands.group(
        brief="Hauptcommand für alle Textchannel Befehle",
        description='Erstelle deinen eigenen Textkanal und lade deine Freunde oder den ganzen Server dazu ein',
        aliases=['tc'],
        usage="<Unterbefehl> [Argument(e)]"
    )
    @commands.bot_has_permissions(manage_channels=True)
    @commands.guild_only()
    async def textchannel(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send_help()
        elif await getUserChannelCategory(ctx.guild) is None:
            raise ErrorMessage(
                "Dieses Modul wurde nicht aktiviert! Ein Administrator kann dieses Modul mit `/channelsetup` aktivieren.")

    @textchannel.command(
        name="create",
        brief='Erstelle deinen Textkanal',
        aliases=[],
    )
    async def textchannel_create(self, ctx):
        category = await getUserChannelCategory(ctx.guild)
        channel = await self.get_text_channel(ctx)
        if channel:
            raise ErrorMessage(
                message="Du hast bereits einen Textkanal! <#"+str(channel.id)+">")
        overwrites = {ctx.guild.default_role: PERM_TEXT_PRIVATE,
                      ctx.author: PERM_TEXT_OWNER}
        newchannel = await category.create_text_channel(name=(ctx.author.name.lower()+"-"+ctx.author.discriminator), overwrites=overwrites, reason="Benutzer hat den Textkanal erstellt")
        await ctx.sendEmbed(title="Textkanal erstellt", fields=[("Kanal", newchannel.mention)])
        
        member = await ctx.database.get_member()
        member.setSetting("CHANNELS_TEXT_ID", newchannel.id)
        await ctx.database._save(member)

    @textchannel.command(
        name="delete",
        brief='Lösche deinen Textkanal',
        aliases=['del'],
    )
    async def textchannel_delete(self, ctx):
        channel = await self.get_text_channel(ctx)
        if channel:
            await channel.delete(reason="Benutzer hat den Textkanal gelöscht")

            member = await ctx.database.get_member()
            member.setSetting("CHANNELS_TEXT_ID", None)
            await ctx.database._save(member)

            if not ctx.channel == channel:
                raise SuccessMessage("Textkanal gelöscht")
        else:
            raise ErrorMessage(message="Du hattest gar keinen Textkanal!")

    @textchannel.command(
        name="invite",
        brief='Lade jemanden in deinen Textkanal ein',
        description='Lade ein Mitglied oder eine Rolle in deinen Textkanal ein',
        aliases=["add", "+"],
        usage="<Mitglied/Rolle>",
    )
    async def textchannel_invite(self, ctx, wer: typing.Union[Member, Role]):
        channel = await self.get_text_channel(ctx)
        if not channel:
            raise ErrorMessage(
                message="Du hast noch keinen Textkanal!")
        await channel.set_permissions(wer, reason="Benuter hat Benutzer/Rolle eingeladen", read_messages=True, send_messages=True)
        if isinstance(wer, Member):
            #EMBED = ctx.getEmbed(title="Benutzer zu Textkanal eingeladen", fields=[("Server", ctx.guild.name), ("Benutzer", wer.mention)])
            # await ctx.author.send(embed=EMBED)
            await channel.send(wer.mention+" wurde zu diesem Textkanal hinzugefügt.")
            raise SuccessMessage("Benutzer zu Textkanal eingeladen", fields=[
                                    ("Benutzer", wer.mention)])
        if isinstance(wer, Role):
            #EMBED = ctx.getEmbed(title="Rolle zu Textkanal eingeladen", fields=[("Server", ctx.guild.name), ("Rolle", wer.name)])
            # await ctx.author.send(embed=EMBED)
            await channel.send("Alle mit der Rolle "+wer.mention+" wurden zu diesem Textkanal hinzugefügt.")
            raise SuccessMessage("Rolle zu Textkanal eingeladen", fields=[
                                    ("Rolle", wer.name)])

    @textchannel.command(
        name="open",
        brief='Öffne deinen Textkanal für alle Mitglieder dieses Servers',
        aliases=["publish", "pub"],
    )
    async def textchannel_open(self, ctx):
        channel = await self.get_text_channel(ctx)
        if not channel:
            raise ErrorMessage(
                message="Du hast noch keinen Textkanal!")
        await channel.set_permissions(ctx.guild.default_role, reason="Benuter hat den Kanal für alle Geöffnet", read_messages=True, send_messages=True)
        raise SuccessMessage("Der Kanal ist nun für alle auf diesem Server geöffnet!")

    @textchannel.command(
        name="close",
        brief='Schliesse deinen Textkanal für alle Mitglieder dieses Servers',
        aliases=["unpublish", "unpub"],
    )
    async def textchannel_close(self, ctx):
        channel = await self.get_text_channel(ctx)
        if not channel:
            raise ErrorMessage(
                message="Du hast noch keinen Textkanal!")
        await channel.set_permissions(ctx.guild.default_role, reason="Benuter hat den Kanal nicht mehr für alle geöffnet!", read_messages=False, send_messages=False)
        raise SuccessMessage("Der Kanal ist nun nicht mehr für alle auf diesem Server geöffnet!")

    # Voicechannels

    @commands.group(
        brief="Hauptcommand für alle Voicechannel Befehle",
        description='Erstelle deinen eigenen Sprachkanal und lade deine Freunde oder den ganzen Server dazu ein',
        aliases=['vc'],
        usage="<Unterbefehl> [Argument(e)]"
    )
    @commands.bot_has_permissions(manage_channels=True)
    @commands.guild_only()
    async def voicechannel(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send_help()
        elif await getUserChannelCategory(ctx.guild) is None:
            raise ErrorMessage(
                "Dieses Modul wurde nicht aktiviert! Ein Administrator kann dieses Modul mit `/channelsetup` aktivieren.")

    @voicechannel.command(
        name="create",
        brief='Erstelle deinen Sprachkanal',
        aliases=[],
    )
    async def voicechannel_create(self, ctx):
        category = await getUserChannelCategory(ctx.guild)
        channel = await self.get_voice_channel(ctx.author, category)
        if channel:
            if ctx.author.voice:
                await ctx.author.edit(voice_channel=channel, reason="Benutzer hat den Kanal erstellt")
            raise ErrorMessage(message="Du hast bereits einen Sprachkanal!")
        overwrites = {ctx.guild.default_role: PERM_VOICE_PRIVATE,
                        ctx.author: PERM_VOICE_OWNER}
        newchannel = await category.create_voice_channel(name=(ctx.author.name.lower()+"#"+ctx.author.discriminator), overwrites=overwrites, reason="Benutzer hat den Sprachkanal erstellt")
        if ctx.author.voice:
            await ctx.author.edit(voice_channel=newchannel, reason="Benutzer hat den Sprachkanal erstellt")
        raise SuccessMessage("Sprachkanal erstellt!")

    @voicechannel.command(
        name="delete",
        brief='Lösche deinen Sprachkanal',
        aliases=['del'],
    )
    async def voicechannel_delete(self, ctx):
        channel = await self.get_voice_channel(ctx.author)
        if channel:
            await channel.delete(reason="Vom Benutzer gelöscht")
            raise SuccessMessage("Sprachkanal gelöscht!")
        raise ErrorMessage(message="Du hattest gar keinen Sprachkanal!")

    @voicechannel.command(
        name="invite",
        brief='Lade jemanden in deinen Sprachkanal ein',
        description='Lade ein Mitglied oder eine Rolle in deinen Sprachkanal ein',
        aliases=["add", "+"],
        usage="<Mitglied/Rolle>",
    )
    async def voicechannel_invite(self, ctx, wer: typing.Union[Member, Role]):
        channel = await self.get_voice_channel(ctx.author)
        if not channel:
            raise ErrorMessage(message="Du hast noch keinen Sprachkanal!")
        await channel.set_permissions(wer, reason="Benuter hat Benutzer/Rolle eingeladen", read_messages=True, connect=True, speak=True)
        if isinstance(wer, Member):
            #EMBED = ctx.getEmbed(title="Benutzer zu Sprachkanal eingeladen", fields=[("Server", ctx.guild.name),("Benutzer", wer.mention)])
            # await ctx.author.send(embed=EMBED)
            if not wer.bot:
                EMBED2 = ctx.getEmbed(title="Du wurdest zu einem Sprachkanal eingeladen", fields=[
                    ("Server", ctx.guild.name), ("Von", ctx.author.mention)])
                await wer.send(embed=EMBED2)
            raise SuccessMessage("Benutzer zu Sprachkanal eingeladen", fields=[
                                 ("Benutzer", wer.mention)])
        if isinstance(wer, Role):
            #EMBED = ctx.getEmbed(title="Rolle zu Sprachkanal eingeladen", fields=[("Server", ctx.guild.name),("Rolle", wer.name)])
            # await ctx.author.send(embed=EMBED)
            await ctx.send("Alle mit der Rolle "+wer.mention+" wurden von "+ctx.author.mention+" zu seinem/ihrem Sprachkanal eingeladen.")
            raise SuccessMessage("Rolle zu Sprachkanal eingeladen", fields=[
                                 ("Rolle", wer.name)])

    @voicechannel.command(
        name="open",
        brief='Öffne deinen Sprachkanal für alle Mitglieder dieses Servers',
        aliases=["publish", "pub"],
    )
    async def voicechannel_open(self, ctx):
        channel = await self.get_voice_channel(ctx.author)
        if not channel:
            raise ErrorMessage(
                message="Du hast noch keinen Sprachkanal!")
        await channel.set_permissions(ctx.guild.default_role, reason="Benuter hat den Kanal für alle geöffnet", read_messages=True, connect=True, speak=True)
        raise SuccessMessage(
            "Der Sprachkanal ist nun für alle auf diesem Server geöffnet!")

    @voicechannel.command(
        name="close",
        brief='Schliesse deinen Sprachkanal für alle Mitglieder dieses Servers',
        aliases=["unpublish", "unpub"],
    )
    async def voicechannel_close(self, ctx):
        channel = await self.get_voice_channel(ctx.author)
        if not channel:
            raise ErrorMessage(
                message="Du hast noch keinen Sprachkanal!")
        await channel.set_permissions(ctx.guild.default_role, reason="Benuter hat den Kanal nicht mehr für alle geöffnet!", read_messages=True, connect=False, speak=True)
        raise SuccessMessage(
            "Der Sprachkanal ist nun nicht mehr für alle auf diesem Server geöffnet!")

    # Channels (General)

    @commands.command(
        name="channelsetup",
        brief="Aktiviere dieses Modul",
        help="Erstelle die Standardkanäle und Kategorie für dieses Modul",
        hidden=True,
    )
    @commands.bot_has_permissions(manage_channels=True)
    @commands.has_permissions(manage_channels=True)
    async def channelsetup(self, ctx):
        category = await getUserChannelCategory(ctx.guild)
        if category:
            raise ErrorMessage(
                "Kategorie existiert bereits! Lösche sie zuerst um sie neu aufzusetzen!")
        categoryoverwrites = {ctx.guild.default_role: PermissionOverwrite(
            read_messages=False, send_messages=False, connect=False, speak=False, move_members=False, use_voice_activation=True)}
        textchanneloverwrites = {ctx.guild.default_role: PermissionOverwrite(
            read_messages=True, send_messages=True)}
        voicechanneloverwrites = {ctx.guild.default_role: PermissionOverwrite(
            view_channel=True, connect=True, speak=False)}
        category = await ctx.guild.create_category_channel(name=CATEGORY_NAME, overwrites=categoryoverwrites, reason="Bereite Benutzerkanäle vor...")
        await category.create_text_channel(name=CHANNEL_NAME_TEXT, overwrites=textchanneloverwrites, reason="Bereite Benutzerkanäle vor...", topic="Hilfe: /help channels")
        await category.create_voice_channel(name=CHANNEL_NAME_PUBLIC, overwrites=voicechanneloverwrites, reason="Bereite Benutzerkanäle vor...")
        await category.create_voice_channel(name=CHANNEL_NAME_PRIVATE, overwrites=voicechanneloverwrites, reason="Bereite Benutzerkanäle vor...")
        raise SuccessMessage(
            "Die erforderlichen Kanäle wurden erfolgreich erstellt!")


def setup(bot):
    bot.add_cog(Channels(bot))
