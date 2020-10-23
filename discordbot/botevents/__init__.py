from discordbot.botevents.on_voice_state_update import setup as setup_on_voice_state_update
from discordbot.botevents.on_command_error import setup as setup_on_command_error
from discordbot.botevents.on_reaction_add import setup as setup_on_reaction_add

def setup(bot):
    setup_on_voice_state_update(bot)
    setup_on_command_error(bot)
    setup_on_reaction_add(bot)
