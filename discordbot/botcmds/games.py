# pylint: disable=no-member

from asgiref.sync import sync_to_async

from discord.ext import commands, tasks
from discord import Embed, utils, PermissionOverwrite, Color, NotFound, User, Member

from django.utils import timezone

from datetime import timedelta

from discordbot.models import AmongUsGame, AMONGUS_PLAYER_COLORS, AMONGUS_EMOJI_COLORS, VierGewinntGame, VIERGEWINNT_NUMBER_EMOJIS
from discordbot.botmodules.serverdata import DjangoConnection
from discordbot.botmodules import apis

import requests
import os
import asyncio
import typing

#####

OVERRIDE_MUTED = PermissionOverwrite(
    read_messages=True, connect=True, speak=False, use_voice_activation=True)
OVERRIDE_TALK = PermissionOverwrite(
    read_messages=True, connect=True, speak=True, use_voice_activation=True)


ALIVE = '❤'
DEAD = '💀'
UNKNOWN = '❓'

YES = '✅'
NO = '❌'

DELETE = '❌'

RUNNING = '⏰'

AMONGUS_TRACKER_INSTALL = """Konfiguriere den Tracker mit folgenden Daten:
                
Der Tracker kann [hier](https://raw.githubusercontent.com/rafaelurben/django-discordbot/master/discordbot/files/amongus/tracker.py) heruntergeladen werden. Er funktioniert vorerst nur für Windows uns ist (noch) buggy!
Bisher ist er auch auf die Bildschirmgrösse 1920x1080p beschränkt. Getestet wurde mit LDPlayer im Vollbildmodus.
Benötigt werden Python, Pip und alle [requirements](https://raw.githubusercontent.com/rafaelurben/django-discordbot/master/discordbot/files/amongus/requirements.txt)."""

amongus_last_update = timezone.now()-timedelta(days=1)

#####

async def getAmongUsCategory(guild):
    category = utils.get(guild.categories, name="AmongUs")
    if not category:
        categoryoverwrites = {guild.default_role: PermissionOverwrite(read_messages=True, send_messages=False, connect=True, speak=True, use_voice_activation=True)}
        category = await guild.create_category_channel(name="AmongUs", overwrites=categoryoverwrites, reason="Bereite AmongUs-Kanäle vor...")
    return category


class Games(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.color = 0x1f871e

        self.amongus_backgroundtasks.start() 

    def cog_unload(self):
        print("[AmongUs Background Tasks] - Stopped!")
        self.amongus_backgroundtasks.cancel()

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if not payload.user_id == self.bot.user.id:
            emoji = payload.emoji.name
            channel = await self.bot.fetch_channel(payload.channel_id)
            message = await channel.fetch_message(payload.message_id)

            ### AmongUs

            if (emoji in AMONGUS_EMOJI_COLORS or emoji == DELETE) and await DjangoConnection._hasAmongUsGame(text_message_id=payload.message_id):
                try:
                    await message.remove_reaction(emoji, payload.member)
                except:
                    pass

                game = await DjangoConnection._getAmongUsGame(text_message_id=payload.message_id)

                if emoji == DELETE:
                    await game.remove_user(userid=payload.user_id)
                else:
                    c = AMONGUS_EMOJI_COLORS[payload.emoji.name]
                    await game.set_user(userid=payload.user_id, color=c)

            ### VierGewinnt

            if (emoji in VIERGEWINNT_NUMBER_EMOJIS) and await DjangoConnection._has(VierGewinntGame, message_id=payload.message_id):
                try:
                    await message.remove_reaction(emoji, payload.member)
                except:
                    pass

                game = await DjangoConnection._get(VierGewinntGame, message_id=payload.message_id)

                if not game.finished:
                    n = VIERGEWINNT_NUMBER_EMOJIS.index(emoji)

                    if game.process(n, payload.user_id):
                        await DjangoConnection._save(game)

                        embed = self.bot.getEmbed(
                            title=f"Vier Gewinnt (#{game.pk})",
                            color=0x0078D7,
                            description=game.get_description()
                        )

                        await message.edit(embed=embed)

                    if game.process_bot():
                        await DjangoConnection._save(game)

                        embed = self.bot.getEmbed(
                            title=f"Vier Gewinnt (#{game.pk})",
                            color=0x0078D7,
                            description=game.get_description()
                        )

                        await message.edit(embed=embed)

                    if game.finished:
                        for emoji in VIERGEWINNT_NUMBER_EMOJIS[:game.width]:
                            await message.remove_reaction(emoji, self.bot.user)


    # Fortnite

    @commands.group(
        brief="Hauptcommand für alle Fortnite Befehle",
        description='Erhalte aktuelle Fortnite-Infos',
        aliases=['fn'],
        usage="<Unterbefehl> [Argument(e)]"
    )
    async def fortnite(self, ctx):  
        if ctx.invoked_subcommand is None:
            await ctx.send_help()

    @fortnite.command(
        name="store",
        brief="Erhalte den aktuellen Fortnite Store",
        aliases=['shop']
    )
    async def fortnite_store(self, ctx):
        JSON = apis.Fortnite.getStore()
        await ctx.sendEmbed(
            title="Fortnite Item Shop",
            authorurl="http://fortnitetracker.com/",
            authorname="Powered by Fortnitetracker"
        )
        for i in range(len(JSON)):
            await ctx.sendEmbed(
                title=str(JSON[i]["name"]),
                description=("Rarity: %s \n vBucks: %s" % (JSON[i]["rarity"],JSON[i]["vBucks"])),
                thumbnailurl=str(JSON[i]["imageUrl"]),
                footertext="",
                footerurl="",
            )

    @fortnite.command(
        name="challenges",
        brief="Erhalte die aktuellen Challenges",
        aliases=[]
    )
    async def fortnite_challenges(self, ctx):
        JSON = apis.Fortnite.getChallenges()
        await ctx.sendEmbed(
            title="Fortnite Challenges",
            fields=[((JSON[i]["metadata"][1]["value"]+" ("+JSON[i]["metadata"][3]["value"]+")"),(JSON[i]["metadata"][5]["value"]+" Battlepassstars")) for i in range(len(JSON))],
            thumbnailurl=str(JSON[0]["metadata"][4]["value"]),
            authorurl="http://fortnitetracker.com/",
            authorname="Powered by Fortnitetracker",
            inline=False
        )

    @fortnite.command(
        name="stats",
        brief="Erhalte die Stats eines Spielers",
        aliases=[],
        help="Mögliche Plattformen: [kbm, gamepad, mouse]",
        usage="<Plattform> <Spielername>",
    )
    async def fortnite_stats(self, ctx, platform:str, playername:str):
        JSON = apis.Fortnite.getStats(platform, playername)
        try:
            await ctx.sendEmbed(
                title="Fortnite Stats von "+JSON["epicUserHandle"]+" auf "+JSON["platformNameLong"],
                description=("Account Id: "+JSON["accountId"]),
                fields=[(JSON["lifeTimeStats"][i]["key"], JSON["lifeTimeStats"][i]["value"]) for i in range(len(JSON["lifeTimeStats"]))],
                authorurl="http://fortnitetracker.com/",
                authorname="Powered by Fortnitetracker"
            )
        except KeyError:
            raise commands.BadArgument(message="Spieler wurde auf der angegebenen Platform nicht gefunden!")


    # Minecraft

    @commands.group(
        brief="Hauptcommand für alle Minecraft Befehle",
        description='Erhalte Infos über Minecraft-Spieler',
        aliases=['mc'],
        usage="<Unterbefehl> <Argument>"
    )
    async def minecraft(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send_help()

    @minecraft.command(
        name="uuid",
        brief="Erhalte die UUID eines Spielers",
        aliases=['id'],
        usage="<Spielername>",
    )
    async def minecraft_uuid(self, ctx, name):
        api = apis.Minecraft

        JSON = api.getProfile(name)
        EMBED = ctx.getEmbed(title="Minecraft UUID", fields=[("UUID", JSON["id"], False),("Aktueller Name", JSON["name"], False)])
        if "legacy" in JSON:
            EMBED.add_field(name="Account",value="Alter Account")
        if "demo" in JSON:
            EMBED.add_field(name="Account",value="Demo Account")
        await ctx.send(embed=EMBED)

    @minecraft.command(
        name="names",
        brief="Erhalte alte Namen eines Spielers",
        aliases=['namen', 'name'],
        usage="<UUID>",
    )
    async def minecraft_names(self, ctx, uuid):
        api = apis.Minecraft

        if len(uuid) != 32:
            raise commands.BadArgument("Eine UUID ist genau 32 Zeichen lang!")

        JSON = api.getProfiles(uuid)
        EMBED = ctx.getEmbed(title="Minecraft Namen", description="Sortierung: Von neu bis alt.")
        for i in JSON[::-1]:
            if "changedToAt" in i:
                EMBED.add_field(name="Name seit "+str(i["changedToAt"]),value=i["name"], inline=False)
            else:
                EMBED.add_field(name="Ursprünglicher Name",value=i["name"], inline=False)
        await ctx.send(embed=EMBED)

    @minecraft.command(
        name="skin",
        brief="Erhalte den Skin eines Spielers",
        aliases=[],
        usage="<UUID>",
    )
    async def minecraft_skin(self, ctx, uuid):
        api = apis.Minecraft

        if len(uuid) != 32:
            raise commands.BadArgument("Eine UUID ist genau 32 Zeichen lang!")

        JSON = api.getSkin(uuid)
        EMBED = ctx.getEmbed(title="Minecraft Skin", fields=[("Aktueller Name", JSON["name"]), ("UUID", JSON["id"])])
        if JSON["skin"] is not None:
            EMBED.set_thumbnail(url=JSON["skin"])
        else:
            EMBED.add_field(name="Skin",value="Wurde nicht gefunden. (Steve/Alex)", inline=False)
        await ctx.send(embed=EMBED)

    @minecraft.command(
        name="player",
        brief="Erhalte alle Infos über einen Spieler",
        description="Dies ist eine Zusammenfassung von UUID, Namen und Skin",
        aliases=['spieler'],
        usage="<Spielername>",
    )
    async def minecraft_player(self, ctx, name):
        api = apis.Minecraft
        
        JSON = api.getProfile(name)
        UUID = JSON["id"]
        EMBED = ctx.getEmbed(title="Minecraft Spieler", fields=[("UUID", UUID)], inline=False)
        if "legacy" in JSON:
            EMBED.add_field(name="Account",value="Alter Account")
        if "demo" in JSON:
            EMBED.add_field(name="Account",value="Demo Account")
        JSON2 = api.getProfiles(UUID)
        for i in JSON2[::-1]:
            if "changedToAt" in i:
                EMBED.add_field(name="Name seit "+str(i["changedToAt"]),value=i["name"], inline=False)
            else:
                EMBED.add_field(name="Ursprünglicher Name",value=i["name"], inline=False)
        JSON3 = api.getSkin(UUID)
        if JSON3["skin"] is not None:
            EMBED.set_thumbnail(url=JSON3["skin"])
        else:
            EMBED.add_field(name="Skin",value="Wurde nicht gefunden. (Steve/Alex)", inline=False)
        await ctx.send(embed=EMBED)



    # AmongUs
    ## AmongUs Tasks

    @tasks.loop(seconds=0.5)
    async def amongus_backgroundtasks(self):
        def log(*args):
            print('[AmongUs Background Tasks] -', *args)

        global amongus_last_update
        games = await DjangoConnection._list(AmongUsGame, last_edited__gt=amongus_last_update)
        amongus_last_update = timezone.now()

        for game in games:
            try:
                log(f'Updating AmongUs #{ game.pk }...')

                # Get channels / Create channels

                textchannel = self.bot.get_channel(int(game.text_channel_id))
                voicechannel = self.bot.get_channel(int(game.voice_channel_id))

                if voicechannel is None:
                    log(f"- Deleted AmongUs #{ game.pk } because voicechannel was not found!")
                    await DjangoConnection._delete(game)
                    if textchannel is not None:
                        await textchannel.delete()
                    continue
                elif textchannel is None:
                    log(f"- Created new textchannel for AmongUs #{ game.pk }!")
                    category = await getAmongUsCategory(voicechannel.guild)
                    textchannel = await category.create_text_channel(name=f"amongus-{ game.pk }", reason="Textkanal war nicht mehr vorhanden!", topic=f"AmongUs Spiel - ID: { game.pk }")
                
                    game.text_channel_id = str(textchannel.id)
                    await DjangoConnection._save(game)

                try:
                    msg = await textchannel.fetch_message(int(game.text_message_id))
                except:
                    log(f"- Created new message for AmongUs #{ game.pk }!")
                    embed = self.bot.getEmbed(
                        title=f"AmongUs Game { game.pk }",
                        color=0xFEDE29,
                        footerurl=None
                    )
                    msg = await textchannel.send(embed=embed)

                    game.text_message_id = str(msg.id)
                    await DjangoConnection._save(game)

                    for emoji in AMONGUS_EMOJI_COLORS:
                        await msg.add_reaction(emoji)
                    await msg.add_reaction(DELETE)

                guild = textchannel.guild

                # Mute / Unmute

                vss = voicechannel.voice_states

                if game.state_ingame:
                    if game.state_meeting:
                        # Unmute alive players
                        for c in AMONGUS_PLAYER_COLORS:
                            if getattr(game, f"p_{c}_exists") and getattr(game, f"p_{c}_alive"):
                                m_id = getattr(game, f"p_{c}_userid")
                                if m_id and (int(m_id) in vss):
                                    vs = vss[int(m_id)]
                                    if vs.mute:
                                        m = vs.channel.guild.get_member(int(m_id))
                                        if m is None:
                                            m = await vs.channel.guild.fetch_member(int(m_id))
                                        await m.edit(mute=False)
                    else:
                        # Mute all players
                        for m_id in vss:
                            vs = vss[m_id]
                            if not vs.mute:
                                m = vs.channel.guild.get_member(m_id)
                                if m is None:
                                    m = await vs.channel.guild.fetch_member(m_id)
                                if not m.bot:
                                    await m.edit(mute=True)

                    # Don't allow new players to speak
                    overwrites = {
                        guild.default_role: OVERRIDE_MUTED
                    }
                    await voicechannel.edit(overwrites=overwrites)
                else:
                    # Unmute all players
                    for m_id in vss:
                        vs = vss[m_id]
                        if vs.mute:
                            m = vs.channel.guild.get_member(m_id)
                            if m is None:
                                m = await vs.channel.guild.fetch_member(m_id)
                            await m.edit(mute=False)

                    # Allow new players to speak
                    await voicechannel.edit(sync_permissions=True)

                # Message

                d = game.get_data()

                id = d["id"]
                last_tracking_data = str(d["last_tracking_data"].strftime("%Y/%m/%d - %H:%M:%S %Z") if d["last_tracking_data"] is not None else NO)
                last_edited = d["last_edited"].strftime("%Y/%m/%d - %H:%M:%S %Z")
                code = (d["code"] or "unbekannt")
                ingame = (YES if d["state"]["ingame"] else NO)
                inmeeting = (YES if d["state"]["meeting"] else NO)

                p_alive = []
                p_dead = []
                p_unknown = []

                for c, i in d["players"].items():
                    if i["userid"]:
                        try:
                            member = self.bot.get_user(int(i["userid"])) or await self.bot.fetch_user(int(i["userid"]))
                            mention = member.mention
                        except NotFound:
                            mention = None
                    else:
                        mention = None

                    description = AMONGUS_PLAYER_COLORS[c][2] + " " + c.upper() + " "
                    description += ("- " + (mention if mention else "") + (" ('"+i["name"]+"')" if i["name"] else "")) if mention or i["name"] else ""

                    if i["exists"]:
                        if i["alive"]:
                            p_alive.append("- "+description)
                        else:
                            p_dead.append("- "+description)
                    else:
                        p_unknown.append("- "+description)

                t_alive = "\n".join(p_alive)
                t_dead = "\n".join(p_dead)
                t_unknown = "\n".join(p_unknown)

                embed = self.bot.getEmbed(
                    title=f"AmongUs Spiel (ID: { id })",
                    description=(f"""Infos über dieses Spiel

                        Letzte Trackerdaten - { last_tracking_data }  
                        Letzte Aktualisierung - { last_edited }

                        Code - { code }                  

                        In game - { ingame }          
                        In meeting - { inmeeting }

                        Spieler:
                    \u200b"""),
                    color=0xFEDE29,
                    inline=False,
                    fields=[
                        (f"{ALIVE} Lebend",      
                         '\u200b\n'+t_alive+'\n\u200b'),
                        (f"{DEAD} Tot",
                         '\u200b\n'+t_dead+'\n\u200b'),
                        (f"{UNKNOWN} Unbekannt",  
                         '\u200b\n'+t_unknown+'\n\u200b'),
                    ]
                )
                await msg.edit(embed=embed)
            except Exception as e:
                log('Error:', e)

    @amongus_backgroundtasks.before_loop
    async def amongus_backgroundtasks_before(self):
        print('[AmongUs Background Tasks] - Waiting for bot to be ready...')
        await self.bot.wait_until_ready()
        print('[AmongUs Background Tasks] - Started!')

    ## AmongUs Commands

    @commands.group(
        brief="Hauptcommand für alle AmongUs Befehle",
        description='Mute und entmute dich und deine Freunde automatisch während eines AmongUs-Spiels.',
        aliases=['au'],
        usage="<Unterbefehl> [Argumente]"
    )
    @commands.guild_only()
    async def amongus(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send_help()

    @amongus.command(
        name="create",
        brief="Erstelle ein AmongUs Spiel",
        aliases=['open', 'add', '+'],
    )
    @commands.guild_only()
    async def amongus_create(self, ctx):
        if await ctx.database.hasAmongUsGame():
            game = await ctx.database.getAmongUsGame()
            textchannel = ctx.guild.get_channel(int(game.text_channel_id))
            voicechannel = ctx.guild.get_channel(int(game.voice_channel_id))
            if textchannel and voicechannel:
                raise commands.BadArgument(message=f"Du hast bereits ein AmongUs-Spiel auf diesem Server! (ID { game.pk } - { textchannel.mention })")
            elif textchannel:
                raise commands.BadArgument(message=f"Du hast bereits ein AmongUs-Spiel auf diesem Server, jedoch konnte der Sprachkanal nicht mehr gefunden werden! Versuche dein Game mit `/au delete` zu löschen. (ID { game.pk } - { textchannel.mention })")
            else:
                raise commands.BadArgument(message=f"Du hast bereits ein AmongUs-Spiel auf diesem Server, jedoch konnte der Textkanal nicht mehr gefunden werden! (ID { game.pk })")
        else:
            category = await getAmongUsCategory(ctx.guild)
            textchannel = await category.create_text_channel(name=f"au-{ctx.author.name}#{ctx.author.discriminator}", reason="Benutzer hat AmongUs-Spiel erstellt.", topic=f"AmongUs Spiel von {ctx.author.name}#{ctx.author.discriminator}")
            voicechannel = await category.create_voice_channel(name=f"[AU] - {ctx.author.name}#{ctx.author.discriminator}", reason="Benutzer hat AmongUs-Spiel erstellt.")
            game = await ctx.database.createAmongUsGame(text_channel_id=str(textchannel.id), voice_channel_id=str(voicechannel.id))

            embed = ctx.getEmbed(
                title=f"AmongUs Spiel erstellt", 
                description=AMONGUS_TRACKER_INSTALL,
                color=0xFEDE29,
                fields=[
                    ("Url", str(game.get_tracker_url())),
                    ("ID", str(game.pk)),
                    ("API-Key", str(game.api_key)),
                    ("Kanal", str(textchannel.mention))
                ]
            )
            await ctx.author.send(embed=embed)

    @amongus.command(
        name="close",
        brief="Lösche dein AmongUs Spiel",
        aliases=['delete', 'del', '-'],
    )
    @commands.guild_only()
    async def amongus_close(self, ctx):
        if await ctx.database.hasAmongUsGame():
            game = await ctx.database.getAmongUsGame()
            textchannel = ctx.guild.get_channel(int(game.text_channel_id))
            voicechannel = ctx.guild.get_channel(int(game.voice_channel_id))
            if textchannel is not None:
                await textchannel.delete(reason="AmongUs Spiel wurde gelöscht!")
            if voicechannel is not None:
                await voicechannel.delete(reason="AmongUs Spiel wurde gelöscht!")

            id = str(game.pk)
            await ctx.database._delete(game)

            embed = ctx.getEmbed(
                title=f"AmongUs Spiel gelöscht! ({ id })",
                description="Dein AmongUs Spiel wurde erfolgreich gelöscht!",
                color=0xFEDE29,
            )
            await ctx.author.send(embed=embed)
        else:
            raise commands.BadArgument(message="Du hast kein AmongUs-Spiel auf diesem Server!")

    @amongus.command(
        name="reset",
        brief="Setze dein AmongUs Spiel zurück",
        aliases=[],
    )
    @commands.guild_only()
    async def amongus_reset(self, ctx):
        if await ctx.database.hasAmongUsGame():
            game = await ctx.database.getAmongUsGame()
            voicechannel = ctx.guild.get_channel(int(game.voice_channel_id))

            if voicechannel is not None:
                game.reset()
                await ctx.database._save(game)
                await voicechannel.edit(sync_permissions=True)
                await ctx.sendEmbed(
                    title="AmongUs Spiel zurückgesetzt!",
                    color=0xFEDE29,
                    description="Dein AmongUs Spiel wurde erfolgreich zurückgesetzt!"
                )
            else:
                raise commands.BadArgument(message="Der Sprachkanal zu deinem Spiel wurde nicht gefunden. Versuche dein Spiel mit `/amongus close` zu löschen")
        else:
            raise commands.BadArgument(message="Du hast kein AmongUs-Spiel auf diesem Server!")

    @amongus.command(
        name="apikey",
        brief="Erhalte nochmals die Konfigurationsdaten für den Tracker",
        aliases=['resend', 'config', 'tracker', 'key'],
    )
    @commands.guild_only()
    async def amongus_apikey(self, ctx):
        if await ctx.database.hasAmongUsGame():
            game = await ctx.database.getAmongUsGame()

            embed = ctx.getEmbed(
                title=f"AmongUs Tracker Konfiguration",
                description=AMONGUS_TRACKER_INSTALL,
                color=0xFEDE29,
                fields=[
                    ("Url", str(game.get_tracker_url())),
                    ("ID", str(game.pk)),
                    ("API-Key", str(game.api_key)),
                ]
            )
            await ctx.author.send(embed=embed)
        else:
            raise commands.BadArgument("Du hast kein AmongUs Spiel!")


    # VierGewinnt

    @commands.group(
        brief="Hauptcommand für alle VierGewinnt Befehle",
        description='Spiele Vier Gewinnt direkt in Discord.',
        aliases=['fourinarow', '4gewinnt', '4inarow', '4row', '4win'],
        help="Um eine Liste aller VierGewinnt-Befehle zu erhalten, gib den Command ohne Argumente ein.",
        usage="<Unterbefehl> [Argumente]"
    )
    async def viergewinnt(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send_help()

    @viergewinnt.command(
        name="duell",
        brief="Duelliere einen anderen Spieler",
        aliases=['battle', 'duel'],
        usage="<Mitglied> [Breite (4-10)] [Höhe (4-14)]",
    )
    @commands.guild_only()
    async def viergewinnt_duell(self, ctx, user: typing.Union[User, Member], width: int = 7, height: int = 6):
        if not (user == ctx.author or user.bot):
            msg = await ctx.sendEmbed(
                title="Vier Gewinnt",
                color=0x0078D7,
                description=f"Duell gegen {user.mention} wird erstellt..."
            )

            game = await ctx.database._create(VierGewinntGame, channel_id=str(ctx.channel.id), message_id=str(msg.id), player_1_id=str(ctx.author.id), player_2_id=str(user.id), width=width, height=height)

            embed = ctx.bot.getEmbed(
                title=f"Vier Gewinnt (#{game.pk})",
                color=0x0078D7,
                description=game.get_description()
            )

            await msg.edit(embed=embed)

            for emoji in VIERGEWINNT_NUMBER_EMOJIS[:game.width]:
                await msg.add_reaction(emoji)
        else:
            raise commands.BadArgument("Du kannst nicht gegen dich selbst oder Bots spielen... Wenn du einen Bot herausfordern möchtest, benutze bitte `/viergewinnt challenge`!")

    @viergewinnt.command(
        name="challenge",
        brief="Duelliere einen Bot",
        aliases=['bot', 'botduel', 'botduell'],
        usage="[Breite (4-10)] [Höhe (4-14)]",
    )
    async def viergewinnt_challenge(self, ctx, width: int = 7, height: int = 6):
        msg = await ctx.sendEmbed(
            title="Vier Gewinnt",
            color=0x0078D7,
            description=f"Challenge gegen einen Bot wird erstellt..."
        )

        game = await ctx.database._create(VierGewinntGame, channel_id=str(ctx.channel.id), message_id=str(msg.id), player_1_id=str(ctx.author.id), player_2_id=None, width=width, height=height)

        embed = ctx.bot.getEmbed(
            title=f"Vier Gewinnt (#{game.pk})",
            color=0x0078D7,
            description=game.get_description()
        )

        await msg.edit(embed=embed)

        for emoji in VIERGEWINNT_NUMBER_EMOJIS[:game.width]:
            await msg.add_reaction(emoji)

    @viergewinnt.command(
        name="games",
        brief="Liste alle deine Spiele auf",
        aliases=["list"],
        usage="[User]",
    )
    async def viergewinnt_games(self, ctx, user: typing.Union[User, Member] = None):
        user = user or ctx.author
        challenges = await ctx.database._list(VierGewinntGame, _order_by=("-time_created",), player_1_id=str(user.id), player_2_id__isnull=True)
        duels_created = await ctx.database._list(VierGewinntGame, _order_by=("-time_created",), player_1_id=str(user.id), player_2_id__isnull=False)
        duels_invited = await ctx.database._list(VierGewinntGame, _order_by=("-time_created",), player_2_id=str(user.id))
        challengetext = "" if challenges else "Du hast noch keine Challenges erstellt."
        for g in challenges:
            challengetext += ((UNKNOWN if g.winner_id is None else YES if g.winner_id == str(user.id) else NO)
                              if g.finished else RUNNING) + f" ({ g.id }) BOT " + g.time_created.strftime("%Y/%m/%d - %H:%M %Z") + "\n"
        duelscreatedtext = "" if duels_created else "Du hast noch keine Duelle erstellt."
        for g in duels_created:
            duelscreatedtext += ((UNKNOWN if g.winner_id is None else YES if g.winner_id == str(user.id) else NO) 
                                 if g.finished else RUNNING) + f" ({ g.id }) <@{ g.player_2_id }> " + g.time_created.strftime("%Y/%m/%d - %H:%M %Z") + "\n"
        duelsinvitedtext = "" if duels_invited else "Du wurdest noch nicht zu einem Duell eingeladen."
        for g in duels_invited:
            duelsinvitedtext += ((UNKNOWN if g.winner_id is None else YES if g.winner_id == str(user.id) else NO)
                                 if g.finished else RUNNING) + f" ({ g.id }) <@{ g.player_1_id }> " + g.time_created.strftime("%Y/%m/%d - %H:%M %Z") + "\n"

        await ctx.sendEmbed(
            title="VierGewinnt Spiele", 
            description="Vier Gewinnt Spiele von "+user.mention, 
            color=0x0078D7, 
            inline=False,
            fields=[
                ("Challenges", challengetext+"\u200b"), 
                ("Erstellte Spiele", duelscreatedtext+"\u200b"), 
                ("Eingeladene Spiele", duelsinvitedtext+"\u200b")
            ]
        )

    @viergewinnt.command(
        name="reset",
        brief="Lösche alle deine Challenges und Duelle",
        description="Hinweis: Dies beinhaltet nicht Duelle, welche ein anderer Spieler gestartet hat!",
        aliases=[],
        usage="[NUR BESITZER: Spieler]"
    )
    async def viergewinnt_reset(self, ctx, user: typing.Union[User, Member] = None):
        user = ctx.author if user is None else user if await self.bot.is_owner(user) else ctx.author
        await ctx.database._delete(await ctx.database._list(VierGewinntGame, get_as_queryset=True, player_1_id=str(user.id)))
        await ctx.sendEmbed(
            title="VierGewinnt Spiele gelöscht!",
            description=f"Die VierGewinnt Spiele von { user.mention } wurden erfolgreich gelöscht!",
            color=0x0078D7, 
        )

    @viergewinnt.command(
        name="resume",
        brief="Fahre ein Duell oder eine Challenge fort",
        description="Wenn du die Nachricht eines Duells oder einer Challenge nicht mehr finden kannst, kannst du sie mit diesem Befehl noch einmal senden lassen. Hiermit können auch Spiele von anderen Spielern angesehen werden.",
        aliases=["continue", "wiederaufnehmen", "resend", "view"],
        usage="<ID>",
        help="Um die ID herauszufinden, benutze `/viergewinnt games`",
    )
    async def viergewinnt_resume(self, ctx, id: int):
        if await ctx.database._has(VierGewinntGame, id=id):
            game = await ctx.database._get(VierGewinntGame, id=id)

            if str(ctx.author.id) in [game.player_1_id, game.player_2_id]:
                msg = await ctx.sendEmbed(
                    title=f"Vier Gewinnt (#{game.pk})",
                    color=0x0078D7,
                    description=game.get_description()
                )

                oldchannelid = int(game.channel_id)
                oldmessageid = int(game.message_id)

                game.channel_id = msg.channel.id
                game.message_id = msg.id

                await ctx.database._save(game)

                if not game.finished:
                    for emoji in VIERGEWINNT_NUMBER_EMOJIS[:game.width]:
                        await msg.add_reaction(emoji)

                    try:
                        channel = self.bot.get_channel(oldchannelid) or await self.bot.fetch_channel(oldchannelid)
                        message = await channel.fetch_message(oldmessageid)

                        await message.edit(embed=self.bot.getEmbed(
                            title=f"Vier Gewinnt (#{game.pk})",
                            color=0x0078D7,
                            description="Dieses Spiel wurde in einer neuen Nachricht weitergeführt!\n\n"+game.get_description()
                        ))

                        for emoji in VIERGEWINNT_NUMBER_EMOJIS[:game.width]:
                            await message.remove_reaction(emoji, self.bot.user)
                    except NotFound as e:
                        print(e)
            else:
                msg = await ctx.sendEmbed(
                    title=f"Vier Gewinnt (#{game.pk} - Readonly)",
                    color=0x0078D7,
                    description=game.get_description()
                )
        else:
            raise commands.BadArgument("Ein Spiel mit dieser ID konnte nicht gefunden werden! Möglicherweise gelöscht?")

def setup(bot):
    bot.add_cog(Games(bot))
