from discord.ext import commands

class ErrorMessage(commands.CommandError):
    pass

class SuccessMessage(commands.CommandError):
    def __init__(self, description, **embedoptions):
        super().__init__(message="")
        self.description = description
        self.embedoptions = embedoptions