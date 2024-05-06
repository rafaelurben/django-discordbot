# pylint: disable=no-member

from discord.ext import commands, tasks
from discord import Embed, utils, PermissionOverwrite, Color, NotFound, User, Member, ChannelType, DiscordException

from django.utils import timezone

from datetime import timedelta

from discordbot.models import VierGewinntGame, VIERGEWINNT_NUMBER_EMOJIS
from discordbot.botmodules.serverdata import DjangoConnection
from discordbot.botmodules import apis
from discordbot.errors import ErrorMessage, SuccessMessage

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

#####


class Games(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.color = 0x1f871e

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if not payload.user_id == self.bot.user.id:
            emoji = payload.emoji.name
            channel = await self.bot.fetch_channel(payload.channel_id)
            message = await channel.fetch_message(payload.message_id)

            if message.author.id == self.bot.user.id:

                ### VierGewinnt

                if (emoji in VIERGEWINNT_NUMBER_EMOJIS) and await DjangoConnection._has(VierGewinntGame, message_id=payload.message_id):
                    try:
                        await message.remove_reaction(emoji, payload.member)
                    except (AttributeError, DiscordException):
                        ...

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

        if ctx.channel.type == ChannelType.private or ctx.channel.permissions_for(ctx.author).manage_messages:
            receiver = ctx.channel
        else:
            receiver = ctx.author
            await ctx.sendEmbed(
                title="Fortnite Item Shop",
                description="Please check your direct messages.",
                color=0x1f871e
            )

        emb = ctx.getEmbed(
            title="Fortnite Item Shop",
            authorurl="http://fortnitetracker.com/",
            authorname="Powered by Fortnitetracker"
        )
        await receiver.send(embed=emb)
        for i in range(len(JSON)):
            emb = ctx.getEmbed(
                title=str(JSON[i]["name"]),
                description=("Rarity: %s \n vBucks: %s" % (JSON[i]["rarity"],JSON[i]["vBucks"])),
                thumbnailurl=str(JSON[i]["imageUrl"]),
                footertext="",
                footerurl="",
            )
            await receiver.send(embed=emb)

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
            raise ErrorMessage(message="Spieler wurde auf der angegebenen Platform nicht gefunden!")


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
            raise ErrorMessage("Eine UUID ist genau 32 Zeichen lang!")

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
            raise ErrorMessage("Eine UUID ist genau 32 Zeichen lang!")

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

            game = await VierGewinntGame.creategame(width=width, height=height, channel_id=str(ctx.channel.id), message_id=str(msg.id), player_1_id=str(ctx.author.id), player_2_id=str(user.id))

            embed = ctx.bot.getEmbed(
                title=f"Vier Gewinnt (#{game.pk})",
                color=0x0078D7,
                description=game.get_description()
            )

            await msg.edit(embed=embed)

            for emoji in VIERGEWINNT_NUMBER_EMOJIS[:game.width]:
                await msg.add_reaction(emoji)
        else:
            raise ErrorMessage("Du kannst nicht gegen dich selbst oder Bots spielen... Wenn du einen Bot herausfordern möchtest, benutze bitte `/viergewinnt challenge`!")

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

        game = await VierGewinntGame.creategame(width=width, height=height, channel_id=str(ctx.channel.id), message_id=str(msg.id), player_1_id=str(ctx.author.id), player_2_id=None)

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
        challengetext = "" if challenges else "Noch keine Challenges erstellt."
        for g in challenges:
            challengetext += ((UNKNOWN if g.winner_id is None else YES if g.winner_id == str(user.id) else NO)
                              if g.finished else RUNNING) + f" ({ g.id }) BOT " + g.time_created.strftime("%Y/%m/%d - %H:%M %Z") + "\n"
        duelscreatedtext = "" if duels_created else "Noch keine Duelle erstellt."
        for g in duels_created:
            duelscreatedtext += ((UNKNOWN if g.winner_id is None else YES if g.winner_id == str(user.id) else NO) 
                                 if g.finished else RUNNING) + f" ({ g.id }) <@{ g.player_2_id }> " + g.time_created.strftime("%Y/%m/%d - %H:%M %Z") + "\n"
        duelsinvitedtext = "" if duels_invited else "Noch zu keinem Duell eingeladen."
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
        await ctx.database._listdelete(VierGewinntGame, player_1_id=str(user.id))
        raise SuccessMessage(f"Die VierGewinnt Spiele von { user.mention } wurden erfolgreich gelöscht!")

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
            raise ErrorMessage("Ein Spiel mit dieser ID konnte nicht gefunden werden! Möglicherweise gelöscht?")

async def setup(bot):
    await bot.add_cog(Games(bot))
