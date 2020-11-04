from discordbot.botevents.on_command_error import setup as setup_on_command_error
from discordbot.botevents.on_command import setup as setup_on_command

def setup(bot):
    setup_on_command_error(bot)
    setup_on_command(bot)
