from discord.ext import commands
from discord import app_commands


class EmbedException(commands.CommandError, app_commands.AppCommandError):
    def __init__(self, **embed_options):
        super().__init__()
        self.embed_options = embed_options


class ErrorMessage(EmbedException):
    def __init__(self, description: str, /, **embed_options):
        super().__init__(**{
            "title": "❌ Fehler",
            "color": 0xff0000,
            "description": description,
            **embed_options
        })


class SuccessMessage(EmbedException):
    def __init__(self, description: str, /, **embed_options):
        super().__init__(**{
            "title": "✅ Aktion erfolgreich",
            "color": 0x00ff00,
            "description": description,
            **embed_options
        })
