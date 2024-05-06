from discord.ext import commands
from discord import app_commands

class ErrorMessage(commands.CommandError, app_commands.AppCommandError):
    pass

class SuccessMessage(commands.CommandError, app_commands.AppCommandError):
    def __init__(self, description, **embedoptions):
        super().__init__(message="")
        self.description = description
        self.embedoptions = embedoptions