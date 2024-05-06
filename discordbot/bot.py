import discord

from discordbot import config, botclasses

# Create Bot

intents = discord.Intents.default()
intents.message_content = True

bot = botclasses.Bot(
    description='Das ist eine Beschreibung!',
    case_insensitive=True,
    activity=discord.Activity(type=discord.ActivityType.listening,
                              name=(config.MAIN_PREFIXES[0] if config.MAIN_PREFIXES else "/") + "help"),
    intents=intents,
    status=discord.Status.idle,
    help_command=None,
    strip_after_prefix=True,
    tree_cls=botclasses.CommandTree
)


@bot.before_invoke
async def before_invoke(ctx):
    await ctx.typing()


# Start

def run(token):
    print("[Bot] - Starting with DEBUG", config.DEBUG)
    bot.run(token, reconnect=True)


if __name__ == "__main__":
    print("[Bot] - You must run this bot via your manage.py file: python3.8 manage.py run-discorbot")
