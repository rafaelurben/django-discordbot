# pylint: disable=no-member
import asyncio
import functools
import typing

import discord
from discord import User, Member
from discord import app_commands
from discord.ext import commands
from django.db.models import Q

from discordbot import utils
from discordbot.errors import ErrorMessage, SuccessMessage
from discordbot.models import VierGewinntGame, VIERGEWINNT_NUMBER_EMOJIS

UNKNOWN = '❓'
YES = '✅'
NO = '❌'

RUNNING = '⏰'


class Connect4View(discord.ui.View):
    def __init__(self, game: VierGewinntGame):
        super().__init__()
        self.game = game

        for i in range(self.game.width):
            btn = discord.ui.Button(emoji=VIERGEWINNT_NUMBER_EMOJIS[i])
            btn.callback = functools.partial(self.btn_callback, col=i)
            self.add_item(btn)

    def get_game_embed(self):
        return utils.getEmbed(
            title=f"Vier Gewinnt (#{self.game.pk})",
            color=0x0078D7,
            description=self.game.get_description()
        )

    async def btn_callback(self, interaction: discord.Interaction, col: int = None):
        await self.game.arefresh_from_db()

        if not self.game.is_players_turn(str(interaction.user.id)):
            return await interaction.response.send_message(embed=utils.getEmbed(
                title="Halt, stopp!",
                color=0xff0000,
                description="Du bist nicht an der Reihe!"
            ), ephemeral=True, delete_after=3)

        if self.game.process(col, interaction.user.id):
            await self.game.asave()
            await interaction.response.send_message(YES + " Spielzug erfolgreich!", ephemeral=True, delete_after=3)
        else:
            await interaction.response.send_message(NO + " Spielzug fehlgeschlagen!", ephemeral=True, delete_after=3)

        await interaction.message.edit(embed=self.get_game_embed())

        if self.game.is_bots_turn():
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(None, self.game.process_bot)

            await self.game.asave()
            await interaction.message.edit(embed=self.get_game_embed())

        if self.game.finished:
            await interaction.message.edit(view=None)


class Connect4Cog(commands.Cog, name="Vier gewinnt"):
    def __init__(self, bot):
        self.bot = bot
        self.color = 0x1f871e

    group = app_commands.Group(name="connect4", description="Vier gewinnt in Discord")

    @group.command(
        name="duel",
        description="Duelliere einen anderen Spieler in Vier Gewinnt",
    )
    @app_commands.describe(opponent="Gegner",
                           width="Breite des Spielfeldes (4-10, Standard=7)",
                           height="Höhe des Spielfeldes (4-10, Standard=6)")
    async def cmd_duel(self, interaction: discord.Interaction, opponent: Member,
                       width: app_commands.Range[int, 4, 10] = 7, height: app_commands.Range[int, 4, 10] = 6):
        await interaction.response.defer()

        if opponent == interaction.user or opponent.bot:
            raise ErrorMessage(
                "Du kannst nicht gegen dich selbst oder Bots spielen... Wenn du einen Bot herausfordern möchtest, "
                "benutze bitte `/connect4 challenge`!")
        if interaction.guild_id is None:
            raise ErrorMessage(
                "Ohne Zuschauer spielen ist nicht lustig. Bitte verwendet den Befehl auf einem Server!"
            )

        emb = utils.getEmbed(
            title="Vier Gewinnt",
            color=0x0078D7,
            description=f"Duell gegen {opponent.mention} wird erstellt..."
        )
        msg = await interaction.followup.send(embed=emb, wait=True)
        msg_ref: discord.MessageReference = msg.to_reference()

        game = await VierGewinntGame.creategame(width=width, height=height,
                                                channel_id=str(msg_ref.channel_id),
                                                message_id=str(msg_ref.message_id),
                                                player_1_id=str(interaction.user.id),
                                                player_2_id=str(opponent.id))

        emb2 = utils.getEmbed(
            title=f"Vier Gewinnt (#{game.pk})",
            color=0x0078D7,
            description=game.get_description()
        )

        await msg.edit(embed=emb2, view=Connect4View(game))

    @group.command(
        name="challenge",
        description="Duelliere einen Bot in Vier Gewinnt",
    )
    @app_commands.describe(width="Breite des Spielfeldes (4-10, Standard=7)",
                           height="Höhe des Spielfeldes (4-10, Standard=6)")
    async def cmd_challenge(self, interaction: discord.Interaction,
                            width: app_commands.Range[int, 4, 10] = 7, height: app_commands.Range[int, 4, 10] = 6):
        await interaction.response.defer()

        emb = utils.getEmbed(
            title="Vier Gewinnt",
            color=0x0078D7,
            description=f"Challenge gegen einen Bot wird erstellt..."
        )
        msg = await interaction.followup.send(embed=emb, wait=True)
        msg_ref: discord.MessageReference = msg.to_reference()

        game = await VierGewinntGame.creategame(width=width, height=height,
                                                channel_id=str(msg_ref.channel_id),
                                                message_id=str(msg_ref.message_id),
                                                player_1_id=str(interaction.user.id),
                                                player_2_id=None)

        emb2 = utils.getEmbed(
            title=f"Vier Gewinnt (#{game.pk})",
            color=0x0078D7,
            description=game.get_description()
        )

        await msg.edit(embed=emb2, view=Connect4View(game))

    @group.command(
        name="games",
        description="Liste alle Vier Gewinnt Spiele von dir oder einem anderen Benutzer auf",
    )
    async def cmd_games(self, interaction: discord.Interaction, user: typing.Union[User, Member] = None):
        await interaction.response.defer()
        user = user or interaction.user

        challenges = VierGewinntGame.objects.filter(player_1_id=str(user.id),
                                                    player_2_id__isnull=True).order_by("-time_created")
        duels_created = VierGewinntGame.objects.filter(player_1_id=str(user.id),
                                                       player_2_id__isnull=False).order_by("-time_created")
        duels_invited = VierGewinntGame.objects.filter(player_2_id=str(user.id)).order_by("-time_created")

        text_challenge = "" if await challenges.aexists() else "Noch keine Challenges erstellt."
        async for g in challenges:
            text_challenge += ((UNKNOWN if g.winner_id is None else YES if g.winner_id == str(user.id) else NO)
                               if g.finished else RUNNING) + f" ({g.id}) BOT " + g.time_created.strftime(
                "%Y/%m/%d - %H:%M %Z") + "\n"
        text_duels_created = "" if await duels_created.aexists() else "Noch keine Duelle erstellt."
        async for g in duels_created:
            text_duels_created += ((UNKNOWN if g.winner_id is None else YES if g.winner_id == str(user.id) else NO)
                                   if g.finished else RUNNING) + f" ({g.id}) <@{g.player_2_id}> " + g.time_created.strftime(
                "%Y/%m/%d - %H:%M %Z") + "\n"
        text_duels_invited = "" if await duels_invited.aexists() else "Noch zu keinem Duell eingeladen."
        async for g in duels_invited:
            text_duels_invited += ((UNKNOWN if g.winner_id is None else YES if g.winner_id == str(user.id) else NO)
                                   if g.finished else RUNNING) + f" ({g.id}) <@{g.player_1_id}> " + g.time_created.strftime(
                "%Y/%m/%d - %H:%M %Z") + "\n"

        emb = utils.getEmbed(
            title="VierGewinnt Spiele",
            description="Vier Gewinnt Spiele von " + user.mention,
            color=0x0078D7,
            inline=False,
            fields=[
                ("Challenges", text_challenge + "\u200b"),
                ("Erstellte Spiele", text_duels_created + "\u200b"),
                ("Eingeladene Spiele", text_duels_invited + "\u200b")
            ]
        )
        await interaction.followup.send(embed=emb)

    @group.command(
        name="reset",
        description="Lösche alle deine Challenges und Duelle",
    )
    async def cmd_reset(self, interaction: discord.Interaction, user: typing.Union[User, Member] = None):
        await interaction.response.defer(ephemeral=True)

        if user is not None and user.id != interaction.user.id and not await self.bot.is_owner(interaction.user):
            raise ErrorMessage("Nur der Bot-Besitzer darf Spiele von anderen Spielern löschen!")

        user = user or interaction.user
        await VierGewinntGame.objects.filter(player_1_id=str(user.id)).adelete()

        raise SuccessMessage(f"Die VierGewinnt Spiele von {user.mention} wurden erfolgreich gelöscht!")

    @group.command(
        name="resume",
        description="Fahre ein Duell oder eine Challenge fort",
    )
    @app_commands.describe(game_id="ID des Spieles")
    async def cmd_resume(self, interaction: discord.Interaction, game_id: int):
        await interaction.response.defer()

        if not await VierGewinntGame.objects.filter(id=game_id).aexists():
            raise ErrorMessage("Ein Spiel mit dieser ID konnte nicht gefunden werden! Möglicherweise gelöscht?")

        game = await VierGewinntGame.objects.aget(id=game_id)

        if not game.finished and str(interaction.user.id) in [game.player_1_id, game.player_2_id]:
            msg = await interaction.followup.send(embed=utils.getEmbed(
                title=f"Vier Gewinnt (#{game.pk})",
                color=0x0078D7,
                description=game.get_description()
            ), view=Connect4View(game), wait=True)
            msg_ref: discord.MessageReference = msg.to_reference()

            old_channel_id = int(game.channel_id)
            old_message_id = int(game.message_id)

            game.channel_id = msg_ref.channel_id
            game.message_id = msg_ref.message_id
            await game.asave()

            try:
                channel = self.bot.get_channel(old_channel_id) or await self.bot.fetch_channel(old_channel_id)
                message = await channel.fetch_message(old_message_id)

                description = f"Dieses Spiel wurde in einer [neuen Nachricht]({msg_ref.jump_url}) weitergeführt!\n\n" \
                              + game.get_description()

                await message.edit(embed=utils.getEmbed(
                    title=f"Vier Gewinnt (#{game.pk})",
                    color=0x0078D7,
                    description=description
                ), view=None)
            except discord.NotFound:
                ...
        else:
            await interaction.followup.send(embed=utils.getEmbed(
                title=f"Vier Gewinnt (#{game.pk} - Readonly)",
                color=0x0078D7,
                description=game.get_description()
            ))

    @cmd_resume.autocomplete('game_id')
    async def cmd_resume__game_id_autocomplete(self,
                                               interaction: discord.Interaction,
                                               current: str,
                                               ) -> typing.List[app_commands.Choice[str]]:
        result = []
        async for game in VierGewinntGame.objects.filter(
                (Q(player_1_id=str(interaction.user.id)) | Q(player_2_id=str(interaction.user.id))),
                id__contains=f"{current}").order_by('finished')[:25]:
            name = f"(#{game.id}) Gestartet " + game.time_created.strftime("%Y/%m/%d - %H:%M %Z")
            if not game.finished:
                name += " " + RUNNING

            result.append(app_commands.Choice(name=name, value=game.id))
        return result
