import traceback

from discord import Interaction, app_commands

from discordbot.errors import EmbedException
from discordbot.utils import getEmbed


class CommandTree(app_commands.CommandTree):
    async def on_error(
        self, interaction: Interaction, error: app_commands.AppCommandError
    ):
        if isinstance(error, EmbedException):
            emb = getEmbed(**error.embed_options)
        elif isinstance(error, app_commands.AppCommandError):
            emb = getEmbed(
                title="⚠️ Uups! Befehl nicht erfolgreich!",
                color=0xF6C54A,
                description=str(error),
            )
        else:
            emb = getEmbed(
                title="🐞 Oh nein!",
                color=0xFF0000,
                description="Beim Ausführen deines Befehls ist leider ein Fehler aufgetreten!",
            )
            print(error)

        if not interaction.response.is_done():
            await interaction.response.send_message(embed=emb, ephemeral=True)
        else:
            await interaction.followup.send(embed=emb, ephemeral=True)
