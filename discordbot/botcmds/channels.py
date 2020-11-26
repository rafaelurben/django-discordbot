from discord.ext import commands
from discord import Embed, User, Member, utils, PermissionOverwrite, Role
import typing

CHANNEL_NAMES_DEFAULT = ["Sprachkanal", "Sprachkanal erstellen", "Neuer Sprachkanal", ]
CHANNEL_NAMES_PUBLIC = ["Sprachkanal [offen]", "Sprachkanal erstellen [offen]", "Neuer Sprackanal [offen]", ]
CHANNEL_NAMES_PRIVATE = ["Sprachkanal [privat]", "Sprachkanal erstellen [privat]", "Neuer Sprachkanal [privat]", ]

CATEGORY_NAMES = ["BENUTZERKANÄLE", ]

PERM_VOICE_OWNER = PermissionOverwrite(connect=True, speak=True, view_channel=True, move_members=True, mute_members=True, deafen_members=True, stream=True, priority_speaker=True, use_voice_activation=True, create_instant_invite=True)
PERM_VOICE_PRIVATE = PermissionOverwrite(connect=False, speak=True, view_channel=True)
PERM_VOICE_PUBLIC = PermissionOverwrite(connect=True, speak=True, view_channel=True)

PERM_TEXT_OWNER = PermissionOverwrite(read_messages=True, read_message_history=True, send_messages=True, manage_messages=True, send_tts_messages=True, manage_webhooks=True, add_reactions=True, embed_links=True, attach_files=True, create_instant_invite=True, external_emojis=True)
PERM_TEXT_PRIVATE = PermissionOverwrite(read_messages=False)

async def getUserChannelCategory(guild):
    category = utils.get(guild.categories, name="Benutzerkanäle")
    if not category:
        categoryoverwrites = { guild.default_role: PermissionOverwrite(read_messages=False, send_messages=False, connect=False, speak=False, move_members=False, use_voice_activation=True) }
        textchanneloverwrites = { guild.default_role: PermissionOverwrite(read_messages=True, send_messages=True) }
        voicechanneloverwrites = { guild.default_role: PermissionOverwrite(view_channel=True, connect=True, speak=False) }
        category = await guild.create_category_channel(name="Benutzerkanäle", overwrites=categoryoverwrites, reason="Bereite Benutzerkanäle vor...")
        await category.create_text_channel(name="benutzerkanäle", overwrites=textchanneloverwrites, reason="Bereite Benutzerkanäle vor...", topic="Hilfe: /help channels")
        await category.create_voice_channel(name=CHANNEL_NAMES_PUBLIC[0], overwrites=voicechanneloverwrites, reason="Bereite Benutzerkanäle vor...")
        await category.create_voice_channel(name=CHANNEL_NAMES_PRIVATE[0], overwrites=voicechanneloverwrites, reason="Bereite Benutzerkanäle vor...")
    return category

class Channels(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.color = 0xee00ff
        
    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        category = await getUserChannelCategory(member.guild)

        # Delete channel if empty
        if before.channel and before.channel.category and before.channel.category.name.upper() in CATEGORY_NAMES and "#" in before.channel.name and before.channel.members == []:
            await before.channel.delete(reason="Kanal war leer")

        # Create new channel
        if after.channel and after.channel.category and after.channel.category.name.upper() in CATEGORY_NAMES and after.channel.name in CHANNEL_NAMES_DEFAULT+CHANNEL_NAMES_PRIVATE+CHANNEL_NAMES_PUBLIC:
            channel = utils.get(member.guild.voice_channels, name=(member.name+"#"+member.discriminator))
            if channel:
                await member.edit(voice_channel=channel,reason="Benutzer wollte einen Kanal erstellen, besitzte aber bereits einen Kanal")
            else:
                if after.channel.name in CHANNEL_NAMES_PRIVATE:
                    overwrites = { member.guild.default_role: PERM_VOICE_PRIVATE, member: PERM_VOICE_OWNER}
                else:
                    overwrites = { member.guild.default_role: PERM_VOICE_PUBLIC, member: PERM_TEXT_OWNER }
                newchannel = await category.create_voice_channel(name=(member.name+"#"+member.discriminator),overwrites=overwrites,reason="Benutzer hat den Sprachkanal erstellt")
                await member.edit(voice_channel=newchannel,reason="Benutzer hat den Sprachkanal erstellt")

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


    @textchannel.command(
        name="create",
        brief='Erstelle deinen Textkanal',
        aliases=[],
    )
    async def textchannel_create(self, ctx):
        category = await getUserChannelCategory(ctx.guild)
        channel = utils.get(ctx.guild.text_channels, name=(ctx.author.name+"-"+ctx.author.discriminator), category=category)
        if channel:
            raise commands.BadArgument(message="Du hast bereits einen Textkanal! <#"+str(channel.id)+">")
        else:
            overwrites = { ctx.guild.default_role: PERM_TEXT_PRIVATE, ctx.author: PERM_TEXT_OWNER }
            newchannel = await category.create_text_channel(name=(ctx.author.name+"-"+ctx.author.discriminator), overwrites=overwrites, reason="Benutzer hat den Textkanal erstellt")
            await ctx.sendEmbed(title="Textkanal erstellt", fields=[("Kanal", newchannel.mention)])


    @textchannel.command(
        name="delete",
        brief='Lösche deinen Textkanal',
        aliases=['del'],
    )
    async def textchannel_delete(self, ctx):
        category = await getUserChannelCategory(ctx.guild)
        channel = utils.get(ctx.guild.text_channels, name=(ctx.author.name+"-"+ctx.author.discriminator), category=category)
        if channel:
            await channel.delete(reason="Benutzer hat den Textkanal gelöscht")
            if not ctx.channel == channel:
                await ctx.sendEmbed(title="Textkanal gelöscht", fields=[("Server", ctx.guild.name)])
        else:
            raise commands.BadArgument(message="Du hattest gar keinen Textkanal!")
        return

    @textchannel.command(
        name="invite",
        brief='Lade jemanden in deinen Textkanal ein',
        description='Lade ein Mitglied oder eine Rolle in deinen Textkanal ein',
        aliases=["add", "+"],
        usage="<Mitglied/Rolle>",
    )
    async def textchannel_invite(self, ctx, wer: typing.Union[Member, Role]):
        category = await getUserChannelCategory(ctx.guild)
        channel = utils.get(ctx.guild.text_channels, name=(
            ctx.author.name+"-"+ctx.author.discriminator), category=category)
        if not channel:
            raise commands.BadArgument(
                message="Du hast noch keinen Textkanal!")
        else:
            await channel.set_permissions(wer, reason="Benuter hat Benutzer/Rolle eingeladen", read_messages=True, send_messages=True)
            if isinstance(wer, Member):
                await ctx.sendEmbed(title="Benutzer zu Textkanal eingeladen", fields=[("Benutzer", wer.mention)])
                #EMBED = ctx.getEmbed(title="Benutzer zu Textkanal eingeladen", fields=[("Server", ctx.guild.name), ("Benutzer", wer.mention)])
                #await ctx.author.send(embed=EMBED)
                await channel.send(wer.mention+" wurde zu diesem Textkanal hinzugefügt.")
            elif isinstance(wer, Role):
                await ctx.sendEmbed(title="Rolle zu Textkanal eingeladen", fields=[("Rolle", wer.name)])
                #EMBED = ctx.getEmbed(title="Rolle zu Textkanal eingeladen", fields=[("Server", ctx.guild.name), ("Rolle", wer.name)])
                #await ctx.author.send(embed=EMBED)
                await channel.send("Alle mit der Rolle "+wer.mention+" wurden zu diesem Textkanal hinzugefügt.")
        return

    @textchannel.command(
        name="open",
        brief='Öffne deinen Textkanal für alle Mitglieder dieses Servers',
        aliases=["publish", "pub"],
    )
    async def textchannel_open(self, ctx):
        category = await getUserChannelCategory(ctx.guild)
        channel = utils.get(ctx.guild.text_channels, name=(
            ctx.author.name+"-"+ctx.author.discriminator), category=category)
        if not channel:
            raise commands.BadArgument(
                message="Du hast noch keinen Textkanal!")
        else:
            await channel.set_permissions(ctx.guild.default_role, reason="Benuter hat den Kanal für alle Geöffnet", read_messages=True, send_messages=True)
            await ctx.sendEmbed(title="Kanal geöffnet", description="Der Kanal ist nun für alle auf diesem Server geöffnet!")

    @textchannel.command(
        name="close",
        brief='Schliesse deinen Textkanal für alle Mitglieder dieses Servers',
        aliases=["unpublish", "unpub"],
    )
    async def textchannel_close(self, ctx):
        category = await getUserChannelCategory(ctx.guild)
        channel = utils.get(ctx.guild.text_channels, name=(
            ctx.author.name+"-"+ctx.author.discriminator), category=category)
        if not channel:
            raise commands.BadArgument(
                message="Du hast noch keinen Textkanal!")
        else:
            await channel.set_permissions(ctx.guild.default_role, reason="Benuter hat den Kanal nicht mehr für alle geöffnet!", read_messages=False, send_messages=False)
            await ctx.sendEmbed(title="Kanal geschlossen", description="Der Kanal ist nun nicht mehr für alle auf diesem Server geöffnet!")

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

    @voicechannel.command(
        name="create",
        brief='Erstelle deinen Sprachkanal',
        aliases=[],
    )
    async def voicechannel_create(self, ctx):
        category = await getUserChannelCategory(ctx.guild)
        channel = utils.get(ctx.guild.voice_channels, name=(ctx.author.name+"#"+ctx.author.discriminator), category=category)
        if channel:
            if ctx.author.voice:
                await ctx.author.edit(voice_channel=channel,reason="Benutzer hat den Kanal erstellt")
            raise commands.BadArgument(message="Du hast bereits einen Sprachkanal!")
        else:
            overwrites = {ctx.guild.default_role: PERM_VOICE_PRIVATE, ctx.author: PERM_VOICE_OWNER}
            newchannel = await category.create_voice_channel(name=(ctx.author.name+"#"+ctx.author.discriminator), overwrites=overwrites, reason="Benutzer hat den Sprachkanal erstellt")
            await ctx.sendEmbed(
                title="Sprachkanal erstellt!",
                footertext="Kanal von USER"
            )
            if ctx.author.voice:
                await ctx.author.edit(voice_channel=newchannel,reason="Benutzer hat den Sprachkanal erstellt")
        return
    
    @voicechannel.command(
        name="delete",
        brief='Lösche deinen Sprachkanal',
        aliases=['del'],
    )
    async def voicechannel_delete(self, ctx):
        category = await getUserChannelCategory(ctx.guild)
        channel = utils.get(ctx.guild.voice_channels, name=(ctx.author.name+"#"+ctx.author.discriminator), category=category)
        if channel:
            await channel.delete(reason="Vom Benutzer gelöscht")
            await ctx.sendEmbed(
                title="Sprachkanal gelöscht!",
                footertext="Kanal von USER",
                fields=[
                    ("Server", ctx.guild.name)
                ]
            )
        else:
            raise commands.BadArgument(message="Du hattest gar keinen Sprachkanal!")
        return


    @voicechannel.command(
        name="invite",
        brief='Lade jemanden in deinen Sprachkanal ein',
        description='Lade ein Mitglied oder eine Rolle in deinen Sprachkanal ein',
        aliases=["add", "+"],
        usage="<Mitglied/Rolle>",
    )
    async def voicechannel_invite(self, ctx, wer: typing.Union[Member,Role]):
        category = await getUserChannelCategory(ctx.guild)
        channel = utils.get(ctx.guild.voice_channels, name=(ctx.author.name+"#"+ctx.author.discriminator), category=category)
        if not channel:
            raise commands.BadArgument(message="Du hast noch keinen Sprachkanal!")
        else:
            await channel.set_permissions(wer,reason="Benuter hat Benutzer/Rolle eingeladen", read_messages=True, connect=True, speak=True)
            if isinstance(wer, Member):
                await ctx.sendEmbed(title="Benutzer zu Sprachkanal eingeladen", fields=[("Benutzer", wer.mention)])
                #EMBED = ctx.getEmbed(title="Benutzer zu Sprachkanal eingeladen", fields=[("Server", ctx.guild.name),("Benutzer", wer.mention)])
                #await ctx.author.send(embed=EMBED)
                if not wer.bot:
                    EMBED2 = ctx.getEmbed(title="Du wurdest zu einem Sprachkanal eingeladen", fields=[("Server", ctx.guild.name),("Von", ctx.author.mention)])
                    await wer.send(embed=EMBED2)
            elif isinstance(wer, Role):
                await ctx.sendEmbed(title="Rolle zu Sprachkanal eingeladen", fields=[("Rolle", wer.name)])
                #EMBED = ctx.getEmbed(title="Rolle zu Sprachkanal eingeladen", fields=[("Server", ctx.guild.name),("Rolle", wer.name)])
                #await ctx.author.send(embed=EMBED)
                await ctx.send("Alle mit der Rolle "+wer.mention+" wurden von "+ctx.author.mention+" zu seinem/ihrem Sprachkanal eingeladen.")
        return

    @voicechannel.command(
        name="open",
        brief='Öffne deinen Sprachkanal für alle Mitglieder dieses Servers',
        aliases=["publish", "pub"],
    )
    async def voicechannel_open(self, ctx):
        category = await getUserChannelCategory(ctx.guild)
        channel = utils.get(ctx.guild.voice_channels, name=(
            ctx.author.name+"#"+ctx.author.discriminator), category=category)
        if not channel:
            raise commands.BadArgument(
                message="Du hast noch keinen Sprachkanal!")
        else:
            await channel.set_permissions(ctx.guild.default_role, reason="Benuter hat den Kanal für alle Geöffnet", read_messages=True, connect=True, speak=True)
            await ctx.sendEmbed(title="Kanal geöffnet", description="Der Sprachkanal ist nun für alle auf diesem Server geöffnet!")

    @voicechannel.command(
        name="close",
        brief='Schliesse deinen Sprachkanal für alle Mitglieder dieses Servers',
        aliases=["unpublish", "unpub"],
    )
    async def voicechannel_close(self, ctx):
        category = await getUserChannelCategory(ctx.guild)
        channel = utils.get(ctx.guild.voice_channels, name=(
            ctx.author.name+"#"+ctx.author.discriminator), category=category)
        if not channel:
            raise commands.BadArgument(
                message="Du hast noch keinen Sprachkanal!")
        else:
            await channel.set_permissions(ctx.guild.default_role, reason="Benuter hat den Kanal nicht mehr für alle geöffnet!", read_messages=True, connect=False, speak=True)
            await ctx.sendEmbed(title="Kanal geschlossen", description="Der Sprachkanal ist nun für alle auf diesem Server geöffnet!")



def setup(bot):
    bot.add_cog(Channels(bot))
