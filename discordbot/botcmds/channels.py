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
        await category.create_text_channel(name="benutzerkanäle", overwrites=textchanneloverwrites, reason="Bereite Benutzerkanäle vor...", topic="Befehle: /textchannelcreate - /textchanneldelete")
        await category.create_voice_channel(name="Sprachkanal erstellen", overwrites=voicechanneloverwrites, reason="Bereite Benutzerkanäle vor...")
    return category

class Channels(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.color = 0xee00ff

        # Siehe Botevent -> on_voice_state_update

    @commands.command(
        brief='Erstelle deinen Textkanal',
        description='Erstelle deinen eigenen Textkanal',
        aliases=[],
        help="Benutze /textchannelcreate um deinen eigenen Textkanal zu erhalten",
        usage=""
    )
    @commands.bot_has_permissions(manage_channels = True)
    @commands.guild_only()
    async def textchannelcreate(self, ctx):
        category = await getUserChannelCategory(ctx.guild)
        channel = utils.get(ctx.guild.text_channels, name=(ctx.author.name+"-"+ctx.author.discriminator), category=category)
        if channel:
            raise commands.BadArgument(message="Du hast bereits einen Textkanal! <#"+str(channel.id)+">")
        else:
            overwrites = { ctx.guild.default_role: PermissionOverwrite(read_messages=False), ctx.author: PermissionOverwrite(read_messages=True,send_messages=True) }
            newchannel = await category.create_text_channel(name=(ctx.author.name+"-"+ctx.author.discriminator),overwrites=overwrites, reason="Benutzer hat den Textkanal erstellt")
            await ctx.sendEmbed(title="Textkanal erstellt", color=self.color, fields=[("Kanal", newchannel.mention)])


    @commands.command(
        brief='Lösche deinen Textkanal',
        description='Lösche deinen eigenen Textkanal',
        aliases=[],
        help="Benutze /textchanneldelete um deinen eigenen Textkanal zu löschen",
        usage=""
    )
    @commands.bot_has_permissions(manage_channels = True)
    @commands.guild_only()
    async def textchanneldelete(self, ctx):
        category = await getUserChannelCategory(ctx.guild)
        channel = utils.get(ctx.guild.text_channels, name=(ctx.author.name+"-"+ctx.author.discriminator), category=category)
        if channel:
            await channel.delete(reason="Benutzer hat den Textkanal gelöscht")
            await ctx.sendEmbed(title="Textkanal gelöscht", color=self.color, fields=[("Server", ctx.guild.name)])
        else:
            raise commands.BadArgument(message="Du hattest gar keinen Textkanal!")
        return



    # @commands.command(
    #     brief='Erstelle deinen Sprachkanal',
    #     description='Erstelle deinen eigenen Sprachkanal',
    #     aliases=[],
    #     help="Benutze /voicechannelcreate um deinen eigenen Sprachkanal zu erhalten",
    #     usage=""
    # )
    # @commands.bot_has_permissions(manage_channels = True)
    # @commands.guild_only()
    # async def voicechannelcreate(self, ctx):
    #     category = await getUserChannelCategory(ctx.guild)
    #     channel = utils.get(ctx.guild.voice_channels, name=(ctx.author.name+"#"+ctx.author.discriminator), category=category)
    #     if channel:
    #         if ctx.author.voice:
    #             await ctx.author.edit(voice_channel=channel,reason="Benutzer hat den Kanal erstellt")
    #         raise commands.BadArgument(message="Du hast bereits einen Sprachkanal!")
    #     else:
    #         overwrites = { ctx.guild.default_role: PermissionOverwrite(connect=False,speak=True,read_messages=False), ctx.author: PermissionOverwrite(connect=True,speak=True,read_messages=True,move_members=True,mute_members=True) }
    #         newchannel = await category.create_voice_channel(name=(ctx.author.name+"#"+ctx.author.discriminator),overwrites=overwrites,reason="Benutzer hat den Sprachkanal erstellt")
    #         EMBED = Embed(title="Sprachkanal erstellt!", color=self.color)
    #         EMBED.set_footer(text=f'Kanal von {ctx.author.name}',icon_url=ctx.author.avatar_url)
    #         await ctx.send(embed=EMBED)
    #         if ctx.author.voice:
    #             await ctx.author.edit(voice_channel=newchannel,reason="Benutzer hat den Sprachkanal erstellt")
    #     return
    #
    # @commands.command(
    #     brief='Lösche deinen Sprachkanal',
    #     description='Lösche deinen eigenen Sprachkanal',
    #     aliases=[],
    #     help="Benutze /voicechanneldelete um deinen eigenen Sprachkanal zu löschen",
    #     usage=""
    # )
    # @commands.bot_has_permissions(manage_channels = True)
    # @commands.guild_only()
    # async def voicechanneldelete(self, ctx):
    #     category = await getUserChannelCategory(ctx.guild)
    #     channel = utils.get(ctx.guild.voice_channels, name=(ctx.author.name+"#"+ctx.author.discriminator), category=category)
    #     if channel:
    #         await channel.delete(reason="Vom Benutzer gelöscht")
    #         EMBED = Embed(title="Sprachkanal gelöscht!", color=self.color)
    #         EMBED.set_footer(text=f'Kanal von {ctx.author.name}',icon_url=ctx.author.avatar_url)
    #         EMBED.add_field(name="Server",value=ctx.guild.name)
    #         await ctx.send(embed=EMBED)
    #     else:
    #         raise commands.BadArgument(message="Du hattest gar keinen Sprachkanal!")
    #     return


    @commands.command(
        brief='Lade jemanden in deinen Sprachkanal ein',
        description='Lade jemanden oder eine Rolle in deinen Sprachkanal ein',
        aliases=["voicechannelinvite","vcadd","vcinvite"],
        help="Benutze /voicechanneladd <Mitglied/Rolle> um jemanden in deinen Sprachkanal eingeladen",
        usage="<Mitglied/Rolle>"
    )
    @commands.bot_has_permissions(manage_channels = True)
    @commands.guild_only()
    async def voicechanneladd(self, ctx, wer: typing.Union[Member,Role]):
        category = await getUserChannelCategory(ctx.guild)
        channel = utils.get(ctx.guild.voice_channels, name=(ctx.author.name+"#"+ctx.author.discriminator), category=category)
        if not channel:
            raise commands.BadArgument(message="Du hast noch keinen Sprachkanal!")
        else:
            await channel.set_permissions(wer,reason="Benuter hat Benutzer/Rolle eingeladen",read_messages=True,connect=True,speak=True)
            if isinstance(wer, Member):
                await ctx.sendEmbed(title="Benutzer zu Sprachkanal eingeladen", color=self.color, fields=[("Benutzer", wer.mention)])
                EMBED = ctx.getEmbed(title="Benutzer zu Sprachkanal eingeladen", color=self.color, fields=[("Server", ctx.guild.name),("Benutzer", wer.mention)])
                await ctx.author.send(embed=EMBED)
                EMBED2 = ctx.getEmbed(title="Du wurdest zu einem Sprachkanal eingeladen", color=self.color, fields=[("Server", ctx.guild.name),("Von", ctx.author.mention)])
                if not wer.bot:
                    await wer.send(embed=EMBED2)
            elif isinstance(wer, Role):
                await ctx.sendEmbed(title="Rolle zu Sprachkanal eingeladen", color=self.color, fields=[("Rolle", wer.name)])
                EMBED = ctx.getEmbed(title="Rolle zu Sprachkanal eingeladen", color=self.color, fields=[("Server", ctx.guild.name),("Rolle", wer.name)])
                await ctx.author.send(embed=EMBED)
                await ctx.send("Alle mit der Rolle "+wer.mention+" wurden von "+ctx.author.mention+" zu seinem/ihrem Sprachkanal eingeladen.")
        return



def setup(bot):
    bot.add_cog(Channels(bot))
