from discord.ext import commands
from discord import Embed, User, Member, utils, PermissionOverwrite, Role
import typing

async def getUserChannelCategory(guild):
    category = utils.get(guild.categories, name="Benutzerkanäle")
    if not category:
        categoryoverwrites = { guild.default_role: PermissionOverwrite(read_messages=False, send_messages=False, connect=False, speak=False, move_members=False, use_voice_activation=True) }
        textchanneloverwrites = { guild.default_role: PermissionOverwrite(read_messages=True, send_messages=True) }
        voicechanneloverwrites = { guild.default_role: PermissionOverwrite(read_messages=True, connect=True, speak=False, move_members=False) }
        category = await guild.create_category_channel(name="Benutzerkanäle", overwrites=categoryoverwrites, reason="Bereite Benutzerkanäle vor...")
        await category.create_text_channel(name="benutzerkanäle", overwrites=textchanneloverwrites, reason="Bereite Benutzerkanäle vor...", topic="Hilfe: /help channels")
        await category.create_voice_channel(name="Sprachkanal erstellen", overwrites=voicechanneloverwrites, reason="Bereite Benutzerkanäle vor...")
    return category

class Channels(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.color = 0xee00ff
        
    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        category = await getUserChannelCategory(member.guild)

        # Delete channel if empty
        if before.channel and before.channel.category and before.channel.category.name.upper() == "BENUTZERKANÄLE" and "#" in before.channel.name and before.channel.members == []:
            await before.channel.delete(reason="Kanal war leer")

        # Create new channel
        if after.channel and after.channel.name == "Sprachkanal erstellen":
            channel = utils.get(member.guild.voice_channels, name=(member.name+"#"+member.discriminator))
            if channel:
                await member.edit(voice_channel=channel,reason="Benutzer wollte einen Kanal erstellen, besitzte aber bereits einen Kanal")
            else:
                overwrites = { member.guild.default_role: PermissionOverwrite(connect=False,speak=True,read_messages=True), member: PermissionOverwrite(connect=True,speak=True,read_messages=True,move_members=True,mute_members=True) }
                newchannel = await category.create_voice_channel(name=(member.name+"#"+member.discriminator),overwrites=overwrites,reason="Benutzer hat den Sprachkanal erstellt")
                await member.edit(voice_channel=newchannel,reason="Benutzer hat den Sprachkanal erstellt")

    # Textchannels

    @commands.group(
        brief="Hauptcommand für alle Textchannel Befehle",
        description='Erstelle deinen eigenen Textkanal und lade deine Freunde oder den ganzen Server dazu ein',
        aliases=['tc'],
        usage="<Unterbefehl> [Argument(e)]"
    )
    async def textchannel(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send_help()


    @textchannel.command(
        name="create",
        brief='Erstelle deinen Textkanal',
        aliases=[],
    )
    @commands.bot_has_permissions(manage_channels = True)
    @commands.guild_only()
    async def textchannel_create(self, ctx):
        category = await getUserChannelCategory(ctx.guild)
        channel = utils.get(ctx.guild.text_channels, name=(ctx.author.name+"-"+ctx.author.discriminator), category=category)
        if channel:
            raise commands.BadArgument(message="Du hast bereits einen Textkanal! <#"+str(channel.id)+">")
        else:
            overwrites = { ctx.guild.default_role: PermissionOverwrite(read_messages=False), ctx.author: PermissionOverwrite(read_messages=True,send_messages=True) }
            newchannel = await category.create_text_channel(name=(ctx.author.name+"-"+ctx.author.discriminator),overwrites=overwrites, reason="Benutzer hat den Textkanal erstellt")
            await ctx.sendEmbed(title="Textkanal erstellt", color=self.color, fields=[("Kanal", newchannel.mention)])


    @textchannel.command(
        name="delete",
        brief='Lösche deinen Textkanal',
        aliases=['del'],
    )
    @commands.bot_has_permissions(manage_channels = True)
    @commands.guild_only()
    async def textchannel_delete(self, ctx):
        category = await getUserChannelCategory(ctx.guild)
        channel = utils.get(ctx.guild.text_channels, name=(ctx.author.name+"-"+ctx.author.discriminator), category=category)
        if channel:
            await channel.delete(reason="Benutzer hat den Textkanal gelöscht")
            await ctx.sendEmbed(title="Textkanal gelöscht", color=self.color, fields=[("Server", ctx.guild.name)])
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
    @commands.bot_has_permissions(manage_channels=True)
    @commands.guild_only()
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
                await ctx.sendEmbed(title="Benutzer zu Textkanal eingeladen", color=self.color, fields=[("Benutzer", wer.mention)])
                #EMBED = ctx.getEmbed(title="Benutzer zu Textkanal eingeladen", color=self.color, fields=[("Server", ctx.guild.name), ("Benutzer", wer.mention)])
                #await ctx.author.send(embed=EMBED)
                await channel.send(wer.mention+" wurde zu diesem Textkanal hinzugefügt.")
            elif isinstance(wer, Role):
                await ctx.sendEmbed(title="Rolle zu Textkanal eingeladen", color=self.color, fields=[("Rolle", wer.name)])
                #EMBED = ctx.getEmbed(title="Rolle zu Textkanal eingeladen", color=self.color, fields=[("Server", ctx.guild.name), ("Rolle", wer.name)])
                #await ctx.author.send(embed=EMBED)
                await channel.send("Alle mit der Rolle "+wer.mention+" wurden zu diesem Textkanal hinzugefügt.")
        return

    @textchannel.command(
        name="open",
        brief='Öffne deinen Textkanal für alle Mitglieder dieses Servers',
        aliases=["publish", "pub"],
    )
    @commands.bot_has_permissions(manage_channels=True)
    @commands.guild_only()
    async def textchannel_open(self, ctx):
        category = await getUserChannelCategory(ctx.guild)
        channel = utils.get(ctx.guild.text_channels, name=(
            ctx.author.name+"-"+ctx.author.discriminator), category=category)
        if not channel:
            raise commands.BadArgument(
                message="Du hast noch keinen Textkanal!")
        else:
            await channel.set_permissions(ctx.guild.default_role, reason="Benuter hat den Kanal für alle Geöffnet", read_messages=True, send_messages=True)
            await ctx.sendEmbed(title="Kanal geöffnet", color=self.color, description="Der Kanal ist nun für alle auf diesem Server geöffnet!")

    @textchannel.command(
        name="close",
        brief='Schliesse deinen Textkanal für alle Mitglieder dieses Servers',
        aliases=["unpublish", "unpub"],
    )
    @commands.bot_has_permissions(manage_channels=True)
    @commands.guild_only()
    async def textchannel_close(self, ctx):
        category = await getUserChannelCategory(ctx.guild)
        channel = utils.get(ctx.guild.text_channels, name=(
            ctx.author.name+"-"+ctx.author.discriminator), category=category)
        if not channel:
            raise commands.BadArgument(
                message="Du hast noch keinen Textkanal!")
        else:
            await channel.set_permissions(ctx.guild.default_role, reason="Benuter hat den Kanal nicht mehr für alle geöffnet!", read_messages=False, send_messages=False)
            await ctx.sendEmbed(title="Kanal geschlossen", color=self.color, description="Der Kanal ist nun nicht mehr für alle auf diesem Server geöffnet!")

    # Voicechannels

    @commands.group(
        brief="Hauptcommand für alle Voicechannel Befehle",
        description='Erstelle deinen eigenen Sprachkanal und lade deine Freunde oder den ganzen Server dazu ein',
        aliases=['vc'],
        usage="<Unterbefehl> [Argument(e)]"
    )
    async def voicechannel(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send_help()

    @voicechannel.command(
        name="create",
        brief='Erstelle deinen Sprachkanal',
        aliases=[],
    )
    @commands.bot_has_permissions(manage_channels = True)
    @commands.guild_only()
    async def voicechannel_create(self, ctx):
        category = await getUserChannelCategory(ctx.guild)
        channel = utils.get(ctx.guild.voice_channels, name=(ctx.author.name+"#"+ctx.author.discriminator), category=category)
        if channel:
            if ctx.author.voice:
                await ctx.author.edit(voice_channel=channel,reason="Benutzer hat den Kanal erstellt")
            raise commands.BadArgument(message="Du hast bereits einen Sprachkanal!")
        else:
            overwrites = { ctx.guild.default_role: PermissionOverwrite(connect=False,speak=True,read_messages=False), ctx.author: PermissionOverwrite(connect=True,speak=True,read_messages=True,move_members=True,mute_members=True) }
            newchannel = await category.create_voice_channel(name=(ctx.author.name+"#"+ctx.author.discriminator),overwrites=overwrites,reason="Benutzer hat den Sprachkanal erstellt")
            EMBED = Embed(title="Sprachkanal erstellt!", color=self.color)
            EMBED.set_footer(text=f'Kanal von {ctx.author.name}',icon_url=ctx.author.avatar_url)
            await ctx.send(embed=EMBED)
            if ctx.author.voice:
                await ctx.author.edit(voice_channel=newchannel,reason="Benutzer hat den Sprachkanal erstellt")
        return
    
    @voicechannel.command(
        name="delete",
        brief='Lösche deinen Sprachkanal',
        aliases=['del'],
    )
    @commands.bot_has_permissions(manage_channels = True)
    @commands.guild_only()
    async def voicechannel_delete(self, ctx):
        category = await getUserChannelCategory(ctx.guild)
        channel = utils.get(ctx.guild.voice_channels, name=(ctx.author.name+"#"+ctx.author.discriminator), category=category)
        if channel:
            await channel.delete(reason="Vom Benutzer gelöscht")
            EMBED = Embed(title="Sprachkanal gelöscht!", color=self.color)
            EMBED.set_footer(text=f'Kanal von {ctx.author.name}',icon_url=ctx.author.avatar_url)
            EMBED.add_field(name="Server",value=ctx.guild.name)
            await ctx.send(embed=EMBED)
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
    @commands.bot_has_permissions(manage_channels = True)
    @commands.guild_only()
    async def voicechannel_invite(self, ctx, wer: typing.Union[Member,Role]):
        category = await getUserChannelCategory(ctx.guild)
        channel = utils.get(ctx.guild.voice_channels, name=(ctx.author.name+"#"+ctx.author.discriminator), category=category)
        if not channel:
            raise commands.BadArgument(message="Du hast noch keinen Sprachkanal!")
        else:
            await channel.set_permissions(wer,reason="Benuter hat Benutzer/Rolle eingeladen",read_messages=True,connect=True,speak=True)
            if isinstance(wer, Member):
                await ctx.sendEmbed(title="Benutzer zu Sprachkanal eingeladen", color=self.color, fields=[("Benutzer", wer.mention)])
                #EMBED = ctx.getEmbed(title="Benutzer zu Sprachkanal eingeladen", color=self.color, fields=[("Server", ctx.guild.name),("Benutzer", wer.mention)])
                #await ctx.author.send(embed=EMBED)
                if not wer.bot:
                    EMBED2 = ctx.getEmbed(title="Du wurdest zu einem Sprachkanal eingeladen", color=self.color, fields=[("Server", ctx.guild.name),("Von", ctx.author.mention)])
                    await wer.send(embed=EMBED2)
            elif isinstance(wer, Role):
                await ctx.sendEmbed(title="Rolle zu Sprachkanal eingeladen", color=self.color, fields=[("Rolle", wer.name)])
                #EMBED = ctx.getEmbed(title="Rolle zu Sprachkanal eingeladen", color=self.color, fields=[("Server", ctx.guild.name),("Rolle", wer.name)])
                #await ctx.author.send(embed=EMBED)
                await ctx.send("Alle mit der Rolle "+wer.mention+" wurden von "+ctx.author.mention+" zu seinem/ihrem Sprachkanal eingeladen.")
        return

    @voicechannel.command(
        name="open",
        brief='Öffne deinen Sprachkanal für alle Mitglieder dieses Servers',
        aliases=["publish", "pub"],
    )
    @commands.bot_has_permissions(manage_channels=True)
    @commands.guild_only()
    async def voicechannel_open(self, ctx):
        category = await getUserChannelCategory(ctx.guild)
        channel = utils.get(ctx.guild.voice_channels, name=(
            ctx.author.name+"#"+ctx.author.discriminator), category=category)
        if not channel:
            raise commands.BadArgument(
                message="Du hast noch keinen Sprachkanal!")
        else:
            await channel.set_permissions(ctx.guild.default_role, reason="Benuter hat den Kanal für alle Geöffnet", read_messages=True, connect=True, speak=True)
            await ctx.sendEmbed(title="Kanal geöffnet", color=self.color, description="Der Sprachkanal ist nun für alle auf diesem Server geöffnet!")

    @voicechannel.command(
        name="close",
        brief='Schliesse deinen Sprachkanal für alle Mitglieder dieses Servers',
        aliases=["unpublish", "unpub"],
    )
    @commands.bot_has_permissions(manage_channels=True)
    @commands.guild_only()
    async def voicechannel_close(self, ctx):
        category = await getUserChannelCategory(ctx.guild)
        channel = utils.get(ctx.guild.voice_channels, name=(
            ctx.author.name+"#"+ctx.author.discriminator), category=category)
        if not channel:
            raise commands.BadArgument(
                message="Du hast noch keinen Sprachkanal!")
        else:
            await channel.set_permissions(ctx.guild.default_role, reason="Benuter hat den Kanal nicht mehr für alle geöffnet!", read_messages=False, connect=False, speak=False)
            await ctx.sendEmbed(title="Kanal geschlossen", color=self.color, description="Der Sprachkanal ist nun für alle auf diesem Server geöffnet!")



def setup(bot):
    bot.add_cog(Channels(bot))
