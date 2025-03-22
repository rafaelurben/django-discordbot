from discord import app_commands, Interaction

from discordbot.errors import ErrorMessage, SuccessMessage
from discordbot.utils import getEmbed


class CommandTree(app_commands.CommandTree):
    async def on_error(
            self,
            interaction: Interaction,
            error: app_commands.AppCommandError
    ):
        if isinstance(error, ErrorMessage):
            emb = getEmbed(
                title="❌ Fehler",
                color=0xff0000,
                description=str(error),
            )
        elif isinstance(error, SuccessMessage):
            emb = getEmbed(
                title="✅ Aktion erfolgreich",
                color=0x00ff00,
                description=error.description,
                **error.embedoptions,
            )
        else:
            emb = getEmbed(
                title="Oh nein!",
                color=0xff0000,
                description="Beim Ausführen deines Befehls ist leider ein Fehler aufgetreten!"
            )
            print(error)

        if not interaction.response.is_done():
            await interaction.response.send_message(embed=emb, ephemeral=True)
        else:
            await interaction.followup.send(embed=emb, ephemeral=True)
