# pylint: disable=no-member

from discord.ext import commands, tasks
from discord import Embed, utils, PermissionOverwrite, Color

from django.utils import timezone

from datetime import timedelta

from discordbot.models import AmongUsGame, AMONGUS_PLAYER_COLORS

import requests
import os
import asyncio

#####

OVERRIDE_MUTED = PermissionOverwrite(
    read_messages=True, connect=True, speak=False, use_voice_activation=True)
OVERRIDE_TALK = PermissionOverwrite(
    read_messages=True, connect=True, speak=True, use_voice_activation=True)


ALIVE = '💚'
DEAD = '💀'
INEXISTENT = '❌'
YES = '✅'
NO = '❌'

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
        self.amongus_backgroundtasks.stop()

    @commands.command(
        brief="Erhalte Aktuelles zu Fortnite",
        description='Sieh dir den Shop, die Herausforderungen oder die Statistiken eines Spielers an',
        aliases=['fn'],
        help="Beachte bitte, das dies noch die alten Stats sind! (Platformen: pc/xbl/psn)",
        usage="store/challenges/stats <Plattform> <Spielername>"
    )
    async def fortnite(self, ctx, Unterbefehl:str, platform:str="", playername:str=""):
        api = ctx.apis.Fortnite

        try:
            if Unterbefehl == "store" or Unterbefehl == "shop": #Fortnite Store
                JSON = api.getStore()
                await ctx.sendEmbed(
                    title="Fortnite Item Shop",
                    color=self.color,
                    authorurl="http://fortnitetracker.com/",
                    authorname="Powered by Fortnitetracker"
                )
                for i in range(len(JSON)):
                    await ctx.sendEmbed(
                        title=str(JSON[i]["name"]),
                        description=("Rarity: %s \n vBucks: %s" % (JSON[i]["rarity"],JSON[i]["vBucks"])),
                        color=self.color,
                        thumbnailurl=str(JSON[i]["imageUrl"])
                    )

            elif Unterbefehl == "challenges" or Unterbefehl == "c": #Fortnite Challenges
                JSON = api.getChallenges()
                await ctx.sendEmbed(
                    title="Fortnite Challenges",
                    color=self.color,
                    fields=[((JSON[i]["metadata"][1]["value"]+" ("+JSON[i]["metadata"][3]["value"]+")"),(JSON[i]["metadata"][5]["value"]+" Battlepassstars")) for i in range(len(JSON))],
                    thumbnailurl=str(JSON[0]["metadata"][4]["value"]),
                    authorurl="http://fortnitetracker.com/",
                    authorname="Powered by Fortnitetracker",
                    inline=False
                )

            elif Unterbefehl == "stats": #Fortnite Stats
                if not platform == "" and not playername == "":
                    JSON = api.getStats(platform, playername)
                    try:
                        await ctx.sendEmbed(
                            title="Fortnite Stats von "+JSON["epicUserHandle"]+" auf "+JSON["platformNameLong"],
                            description=("Account Id: "+JSON["accountId"]),
                            color=self.color,
                            fields=[(JSON["lifeTimeStats"][i]["key"], JSON["lifeTimeStats"][i]["value"]) for i in range(len(JSON["lifeTimeStats"]))],
                            authorurl="http://fortnitetracker.com/",
                            authorname="Powered by Fortnitetracker"
                        )
                    except KeyError:
                        raise commands.BadArgument(message="Spieler wurde auf der angegebenen Platform nicht gefunden!")
                else:
                    raise commands.BadArgument(message="Platform und/oder Spieler wurde nicht angegeben!")
            else:
                raise commands.BadArgument(message="Unbekannter Unterbefehl!")
        except KeyError:
            raise commands.BadArgument(message="Scheinbar ist dieser Befehl nicht richtig konfiguriert.")





    @commands.group(
        brief="Hauptcommand für alle Minecraft Befehle",
        description='Alle Minecraft Befehle beginnen mit diesem Befehl',
        aliases=['mc'],
        help="Um eine Liste aller AmongUs-Befehle zu erhalten, gib den Command ohne Argumente ein.",
        usage="<Unterbefehl> <Argument>"
    )
    async def minecraft(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.sendEmbed(
                title="Minecraft Befehle",
                description=f"""Alle Minecraft Befehle können ebenfalls mit `/minecraft` verwendet werden.""",
                color=0x00AA00,
                inline=False,
                fields=[
                    ("/mc uuid <Name>",   "Erhalte die UUID eines Spielers"),
                    ("/mc names <UUID>",  "Erhalte alte Namen eines Spielers"),
                    ("/mc skin <UUID>",   "Erhalte den Skin eines Spielers"),
                    ("/mc player <Name>", "Erhalte alle Infos über einen Spieler"),
                ]
            )

    @minecraft.command(
        name="uuid",
        aliases=['id']
    )
    async def minecraft_uuid(self, ctx, name):
        api = ctx.apis.Minecraft

        JSON = api.getProfile(name)
        EMBED = ctx.getEmbed(title="Minecraft UUID", color=self.color, fields=[("UUID", JSON["id"], False),("Aktueller Name", JSON["name"], False)])
        if "legacy" in JSON:
            EMBED.add_field(name="Account",value="Alter Account")
        if "demo" in JSON:
            EMBED.add_field(name="Account",value="Demo Account")
        await ctx.send(embed=EMBED)

    @minecraft.command(
        name="names",
        aliases=['namen', 'name']
    )
    async def minecraft_names(self, ctx, uuid):
        api = ctx.apis.Minecraft

        if len(uuid) != 32:
            raise commands.BadArgument("Eine UUID ist genau 32 Zeichen lang!")

        JSON = api.getProfiles(uuid)
        EMBED = ctx.getEmbed(title="Minecraft Namen", color=self.color, description="Sortierung: Von neu bis alt.")
        for i in JSON[::-1]:
            if "changedToAt" in i:
                EMBED.add_field(name="Name seit "+str(i["changedToAt"]),value=i["name"], inline=False)
            else:
                EMBED.add_field(name="Ursprünglicher Name",value=i["name"], inline=False)
        await ctx.send(embed=EMBED)

    @minecraft.command(
        name="skin",
        aliases=[]
    )
    async def minecraft_skin(self, ctx, uuid):
        api = ctx.apis.Minecraft

        if len(uuid) != 32:
            raise commands.BadArgument("Eine UUID ist genau 32 Zeichen lang!")

        JSON = api.getSkin(uuid)
        EMBED = ctx.getEmbed(title="Minecraft Skin", color=self.color, fields=[("Aktueller Name", JSON["name"]), ("UUID", JSON["id"])])
        if JSON["skin"] is not None:
            EMBED.set_thumbnail(url=JSON["skin"])
        else:
            EMBED.add_field(name="Skin",value="Wurde nicht gefunden. (Steve/Alex)", inline=False)
        await ctx.send(embed=EMBED)

    @minecraft.command(
        name="player",
        aliases=['spieler']
    )
    async def minecraft_player(self, ctx, name):
        api = ctx.apis.Minecraft
        
        JSON = api.getProfile(name)
        UUID = JSON["id"]
        EMBED = ctx.getEmbed(title="Minecraft Spieler", color=self.color, fields=[("UUID", UUID)], inline=False)
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






    @tasks.loop(seconds=1.0)
    async def amongus_backgroundtasks(self):
        global amongus_last_update
        games = AmongUsGame.objects.filter(last_edited__gt=amongus_last_update)
        amongus_last_update = timezone.now()

        for game in games:
            try:
                print('[AmongUs Background Tasks] - Updated', game)

                textchannel = self.bot.get_channel(int(game.text_channel_id))
                voicechannel = self.bot.get_channel(int(game.voice_channel_id))

                if voicechannel is None:
                    game.delete()
                    continue
                elif textchannel is None:
                    category = await getAmongUsCategory(self.bot.get_guild(int(game.guild.id)))
                    textchannel = await category.create_text_channel(name=f"amongus-{ game.pk }", reason="Textkanal war nicht mehr vorhanden!", topic=f"AmongUs Spiel - { game.pk }")
                
                    embed = self.bot.getEmbed(
                        title=f"AmongUs Game { game.pk }",
                        color=0xFEDE29,
                    )
                    msg = await textchannel.send(embed=embed)

                    game.text_channel_id = str(textchannel.id)
                    game.text_message_id = str(msg.id)
                    game.save()

                try:
                    msg = await textchannel.fetch_message(int(game.text_message_id))
                except:
                    embed = self.bot.getEmbed(
                        title=f"AmongUs Game { game.pk }",
                        color=0xFEDE29,
                        footerurl=None
                    )
                    msg = await textchannel.send(embed=embed)

                    game.text_message_id = str(msg.id)
                    game.save()

                guild = textchannel.guild

                tracker_connected = (YES if game.tracker_connected else NO)
                last_edited = game.last_edited.strftime("%Y/%m/%d - %H:%M:%S %Z")
                code = (game.code or "unbekannt")
                ingame = (YES if game.state_ingame else NO)
                inmeeting = (YES if game.state_meeting else NO)

                embed = self.bot.getEmbed(
                    title=f"AmongUs Game { game.pk }",
                    description=(f"""Infos über Gruppe Nr. { game.pk }

                        Tracker verbunden - { tracker_connected }  
                        Letzte Aktualisierung - { last_edited }

                        Code - { code }                  

                        In game - { ingame }          
                        In meeting - { inmeeting }

                        Spieler:
                    """),
                    footertext=f"{INEXISTENT} = Nicht vorhanden - {DEAD} = Tot - {ALIVE} = Lebend",
                    color=0xFEDE29,
                    inline=True,
                    fields=list(
                        (
                            (((ALIVE if getattr(game, f"p_{c}_alive") else DEAD) if getattr(
                                game, f"p_{c}_exists") else INEXISTENT) + " " + c.upper()),
                            (getattr(game, f"p_{c}_name") or "-"),
                        ) for c in AMONGUS_PLAYER_COLORS
                    )
                )
                await msg.edit(embed=embed)

                # Mute etc.

                if game.state_ingame:
                    overwrites = {
                        guild.default_role: OVERRIDE_MUTED
                    }
                    
                    if game.state_meeting:
                        for c in AMONGUS_PLAYER_COLORS:
                            r = utils.get(guild.roles, name="[AU] - "+c.upper())
                            if r is not None and getattr(game, f"p_{c}_exists") and getattr(game, f"p_{c}_alive"):
                                overwrites[r] = OVERRIDE_TALK
                    await voicechannel.edit(overwrites=overwrites)
                else:
                    await voicechannel.edit(sync_permissions=True)
            except Exception as e:
                print('[AmongUs Background Tasks] -', e)


    @amongus_backgroundtasks.before_loop
    async def amongus_backgroundtasks_before(self):
        print('[AmongUs Background Tasks] - Waiting for bot to be ready...')
        await self.bot.wait_until_ready()
        print('[AmongUs Background Tasks] - Started!')

    @commands.group(
        brief="Hauptcommand für alle AmongUs Befehle",
        description='Alle AmongUs-Befehle beginnen mit diesem Befehl.',
        aliases=['au'],
        help="Um eine Liste aller AmongUs-Befehle zu erhalten, gib den Command ohne Argumente ein.",
        usage="<Unterbefehl> [Argumente]"
    )
    async def amongus(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.sendEmbed(
                title="AmongUs Befehle",
                description=f"""Alle AmongUs Befehle können ebenfalls mit `/amongus` verwendet werden.""",
                color=0xFEDE29,
                inline=False,
                fields=[
                    ("/au create",      "Erstelle einen AmongUs Kanal"),
                    ("/au delete",      "Erstelle deinen AmongUs Kanal"),
                    ("/au reset",       "Setze die Rollen in deinem Sprachkanal zurück"),
                    ("/au install",     "Erstelle alle benötigten Rollen - [ADMIN]"),
                    ("/au uninstall",   "Lösche alle benötigten Rollen - [ADMIN]"),
                ]
            )

    @amongus.command(
        name="install",
        aliases=[],
    )
    @commands.has_guild_permissions(manage_roles=True)
    async def amongus_install(self, ctx):
        for c in AMONGUS_PLAYER_COLORS:
            if utils.get(ctx.guild.roles, name="[AU] - "+c.upper()) is None:
                await ctx.guild.create_role(
                    name="[AU] - "+c.upper(), 
                    colour=Color.from_rgb(*AMONGUS_PLAYER_COLORS[c][1]),
                    reason="Admin used /amongus install command",
                    mentionable=True,
                )
        await ctx.sendEmbed(
            title="AmongUs Installed!", 
            color=0xFEDE29, 
            description="AmongUs roles were successfully created!"
        )

    @amongus.command(
        name="uninstall",
        aliases=['deinstall'],
    )
    @commands.has_guild_permissions(manage_roles=True)
    async def amongus_uninstall(self, ctx):
        for c in AMONGUS_PLAYER_COLORS:
            r = utils.get(ctx.guild.roles, name="[AU] - "+c.upper())
            if r is not None:
                await r.delete(reason="Admin used /amongus uninstall command")
        await ctx.sendEmbed(
            title="AmongUs Uninstalled!", 
            color=0xFEDE29, 
            description="AmongUs roles were successfully deleted!"
        )

    @amongus.command(
        name="roles",
        aliases=['getroles'],
    )
    async def amongus_roles(self, ctx):
        return

    @amongus.command(
        name="create",
        aliases=['open', 'add'],
    )
    async def amongus_create(self, ctx):
        if AmongUsGame.objects.filter(creator=ctx.database.user, guild=ctx.database.server).exists():
            game = AmongUsGame.objects.get(creator=ctx.database.user, guild=ctx.database.server)
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
            textchannel = await category.create_text_channel(name="amongus-loading", reason="Benutzer hat AmongUs-Spiel erstellt.", topic="Dieser AmongUS Kanal wird gerade erstellt...")
            voicechannel = await category.create_voice_channel(name="AmongUs LOADING", reason="Benutzer hat AmongUs-Spiel erstellt.")
            game = AmongUsGame.objects.create(creator=ctx.database.user, guild=ctx.database.server, text_channel_id=str(textchannel.id), voice_channel_id=str(voicechannel.id))
            await textchannel.edit(name=f"amongus-{ game.pk }", topic=f"AmongUs Spiel - { game.pk }")
            await voicechannel.edit(name=f"AmongUs - { game.pk }")

            embed = ctx.getEmbed(
                title=f"AmongUs Spiel erstellt ({ game.pk })", 
                description="Konfiguriere die Tracker-Software mit folgender URL und folgendem API Key:", 
                color=0xFEDE29,
                fields=[
                    ("Url", str(game.get_tracker_url())),
                    ("API-Key", str(game.api_key)),
                    ("Kanal", str(textchannel.mention))
                ]
            )
            await ctx.author.send(embed=embed)


    @amongus.command(
        name="close",
        aliases=['delete', 'del'],
    )
    async def amongus_close(self, ctx):
        if AmongUsGame.objects.filter(creator=ctx.database.user, guild=ctx.database.server).exists():
            game = AmongUsGame.objects.get(creator=ctx.database.user, guild=ctx.database.server)
            textchannel = ctx.guild.get_channel(int(game.text_channel_id))
            voicechannel = ctx.guild.get_channel(int(game.voice_channel_id))
            if textchannel is not None:
                await textchannel.delete(reason="AmongUs Spiel wurde gelöscht!")
            if voicechannel is not None:
                await voicechannel.delete(reason="AmongUs Spiel wurde gelöscht!")

            id = str(game.pk)
            game.delete()

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
        aliases=[],
    )
    async def amongus_reset(self, ctx):
        if AmongUsGame.objects.filter(creator=ctx.database.user, guild=ctx.database.server).exists():
            game = AmongUsGame.objects.get(creator=ctx.database.user, guild=ctx.database.server)
            voicechannel = ctx.guild.get_channel(int(game.voice_channel_id))

            if voicechannel is not None:
                await voicechannel.edit(sync_permissions=True)
                await ctx.sendEmbed(
                    title="AmongUs Reset!",
                    color=0xFEDE29,
                    description="Your AmongUs channel roles have been reset!"
                )
            else:
                raise commands.BadArgument(message="Der Sprachkanal zu deinem Spiel wurde nicht gefunden. Versuche dein Spiel mit `/amongus close` zu löschen")
        else:
            raise commands.BadArgument(message="Du hast kein AmongUs-Spiel auf diesem Server!")

def setup(bot):
    bot.add_cog(Games(bot))
