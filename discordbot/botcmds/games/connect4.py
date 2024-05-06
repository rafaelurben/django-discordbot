# pylint: disable=no-member

import typing

from discord import NotFound, User, Member, DiscordException
from discord.ext import commands

from discordbot.botmodules.serverdata import DjangoConnection
from discordbot.errors import ErrorMessage, SuccessMessage
from discordbot.models import VierGewinntGame, VIERGEWINNT_NUMBER_EMOJIS

UNKNOWN = '❓'
YES = '✅'
NO = '❌'

RUNNING = '⏰'


class Connect4Cog(commands.Cog, name="Vier gewinnt"):
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

                if (emoji in VIERGEWINNT_NUMBER_EMOJIS) and await DjangoConnection._has(VierGewinntGame,
                                                                                        message_id=payload.message_id):
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

            game = await VierGewinntGame.creategame(width=width, height=height, channel_id=str(ctx.channel.id),
                                                    message_id=str(msg.id), player_1_id=str(ctx.author.id),
                                                    player_2_id=str(user.id))

            embed = ctx.bot.getEmbed(
                title=f"Vier Gewinnt (#{game.pk})",
                color=0x0078D7,
                description=game.get_description()
            )

            await msg.edit(embed=embed)

            for emoji in VIERGEWINNT_NUMBER_EMOJIS[:game.width]:
                await msg.add_reaction(emoji)
        else:
            raise ErrorMessage(
                "Du kannst nicht gegen dich selbst oder Bots spielen... Wenn du einen Bot herausfordern möchtest, benutze bitte `/viergewinnt challenge`!")

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

        game = await VierGewinntGame.creategame(width=width, height=height, channel_id=str(ctx.channel.id),
                                                message_id=str(msg.id), player_1_id=str(ctx.author.id),
                                                player_2_id=None)

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
        challenges = await ctx.database._list(VierGewinntGame, _order_by=("-time_created",), player_1_id=str(user.id),
                                              player_2_id__isnull=True)
        duels_created = await ctx.database._list(VierGewinntGame, _order_by=("-time_created",),
                                                 player_1_id=str(user.id), player_2_id__isnull=False)
        duels_invited = await ctx.database._list(VierGewinntGame, _order_by=("-time_created",),
                                                 player_2_id=str(user.id))
        challengetext = "" if challenges else "Noch keine Challenges erstellt."
        for g in challenges:
            challengetext += ((UNKNOWN if g.winner_id is None else YES if g.winner_id == str(user.id) else NO)
                              if g.finished else RUNNING) + f" ({g.id}) BOT " + g.time_created.strftime(
                "%Y/%m/%d - %H:%M %Z") + "\n"
        duelscreatedtext = "" if duels_created else "Noch keine Duelle erstellt."
        for g in duels_created:
            duelscreatedtext += ((UNKNOWN if g.winner_id is None else YES if g.winner_id == str(user.id) else NO)
                                 if g.finished else RUNNING) + f" ({g.id}) <@{g.player_2_id}> " + g.time_created.strftime(
                "%Y/%m/%d - %H:%M %Z") + "\n"
        duelsinvitedtext = "" if duels_invited else "Noch zu keinem Duell eingeladen."
        for g in duels_invited:
            duelsinvitedtext += ((UNKNOWN if g.winner_id is None else YES if g.winner_id == str(user.id) else NO)
                                 if g.finished else RUNNING) + f" ({g.id}) <@{g.player_1_id}> " + g.time_created.strftime(
                "%Y/%m/%d - %H:%M %Z") + "\n"

        await ctx.sendEmbed(
            title="VierGewinnt Spiele",
            description="Vier Gewinnt Spiele von " + user.mention,
            color=0x0078D7,
            inline=False,
            fields=[
                ("Challenges", challengetext + "\u200b"),
                ("Erstellte Spiele", duelscreatedtext + "\u200b"),
                ("Eingeladene Spiele", duelsinvitedtext + "\u200b")
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
        raise SuccessMessage(f"Die VierGewinnt Spiele von {user.mention} wurden erfolgreich gelöscht!")

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
                            description="Dieses Spiel wurde in einer neuen Nachricht weitergeführt!\n\n" + game.get_description()
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
