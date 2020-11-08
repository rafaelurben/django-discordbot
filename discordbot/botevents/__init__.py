from discordbot.botevents.on_command_error import setup as setup_on_command_error
from discordbot.botevents.on_command import setup as setup_on_command
from discordbot.botevents.on_message import setup as setup_on_message

def setup(bot):
    setup_on_command_error(bot)
    setup_on_command(bot)
    setup_on_message(bot)
