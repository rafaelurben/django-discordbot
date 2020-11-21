# pylint: disable=unused-variable

from discord.ext import commands
from discord import Embed

from discordbot.config import DEBUG
from discordbot.errors import ErrorMessage

DEBUG_NO_RAISE_FOR = [
    commands.CommandNotFound, 
    commands.MissingRequiredArgument, 
    commands.BadArgument, 
    commands.CommandOnCooldown,
    commands.MissingAnyRole,
    commands.MissingRole,
]

def setup(bot):
    @bot.event
    async def on_command_error(ctx, error):
        if isinstance(error, ErrorMessage):
            await ctx.sendEmbed(title="Fehler", color=0xff0000, description=str(error), fields=[("Nachricht", ctx.message.content)])
        else:
            EMBED = ctx.getEmbed(title="Fehler", color=0xff0000)
            if isinstance(error, commands.BadArgument):
                EMBED.add_field(name="Beschreibung", value="Du hast ungültige Argumente angegeben!")
            elif isinstance(error, commands.MissingRequiredArgument):
                EMBED.add_field(name="Beschreibung", value="Du hast ein benötigtes Argument weggelassen!")
            elif isinstance(error, commands.CommandNotFound):
                EMBED.add_field(name="Beschreibung", value="Dieser Befehl wurde nicht gefunden!")
            elif isinstance(error, commands.CommandOnCooldown):
                EMBED.add_field(name="Beschreibung", value="Warte, bis du diesen Befehl erneut benutzen kannst!")
            elif isinstance(error, commands.DisabledCommand):
                EMBED.add_field(name="Beschreibung", value="Dieser Command ist aktuell deaktiviert!")
            elif isinstance(error, commands.TooManyArguments):
                EMBED.add_field(name="Beschreibung", value="Du hast zu viele Argumente angegeben!")
            elif isinstance(error, commands.MissingPermissions):
                EMBED.add_field(name="Beschreibung", value="Du hast nicht die nötigen Berechtigungen für diesen Command!")
            elif isinstance(error, commands.BotMissingPermissions):
                EMBED.add_field(name="Beschreibung", value="Ich habe nicht die nötigen Berechtigungen für diesen Command!")
            elif isinstance(error, commands.NoPrivateMessage):
                EMBED.add_field(name="Beschreibung", value="Dieser Command kann nur auf einem Server verwendet werden!")
            elif isinstance(error, commands.PrivateMessageOnly):
                EMBED.add_field(name="Beschreibung", value="Dieser Command kann nur in Direktnachrichten werden!")
            elif isinstance(error, commands.MissingRole):
                EMBED.add_field(name="Beschreibung", value="Du hast die benötigten Rollen nicht, um diesen Befehl auszuführen!")
            elif isinstance(error, commands.MissingAnyRole):
                EMBED.add_field(name="Beschreibung", value="Du hast die benötigten Rollen nicht, um diesen Befehl auszuführen!")
            elif isinstance(error, commands.NotOwner):
                EMBED.add_field(name="Beschreibung", value="Du bist nicht Besitzer des Bots!")
                return # keine Nachricht senden!
            elif isinstance(error, commands.CommandError):
                EMBED.add_field(name="Beschreibung", value="Bei einem Befehl ist ein Fehler aufgetreten!")
            else:
                EMBED.add_field(name="Beschreibung", value="Es ist ein unbekannter Fehler aufgetreten! Vermutlich liegt er nicht bei dir, also melde ihn am besten einem Admin.")
                if DEBUG:
                    print("[Command] - Bei '"+ctx.message.content+"' von '"+ctx.message.author.name+"#"+ctx.message.author.discriminator+"' ist ein Fehler aufgetreten: "+str(error))
            
            if not error == "":
                if "OperationalError: (2006, 'MySQL server has gone away')" in str(error):
                    EMBED.add_field(name="Info", value="Leider konnte die Verbindung zur Datenbank nicht hergestellt werden. Bitte versuche es später noch einmal!")
                else:
                    EMBED.add_field(name="Error", value=str(error) if len(str(error)) < 1024 else str(error)[-1024:-1])
            EMBED.add_field(name="Nachricht", value=ctx.message.content, inline=False)
            await ctx.send(embed=EMBED)

            if DEBUG and not True in [isinstance(error, cls) for cls in DEBUG_NO_RAISE_FOR]:
                raise error
