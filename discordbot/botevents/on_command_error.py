# pylint: disable=unused-variable

import asyncio

from discord.ext import commands
from discord import Embed, ChannelType

from discordbot.config import DEBUG
from discordbot.errors import ErrorMessage, SuccessMessage

DEBUG_NO_RAISE_FOR = [
    commands.DisabledCommand,
    commands.CommandOnCooldown,
    commands.CommandNotFound,
    commands.UserInputError,
    commands.CheckFailure,
]


def setup(bot):
    @bot.event
    async def on_command_error(ctx, error):
        if isinstance(error, ErrorMessage):
            msg = await ctx.sendEmbed(
                title="Fehler",
                color=0xff0000,
                description=str(error),
                fields=[("Nachricht", ctx.message.content)],
            )
        elif isinstance(error, SuccessMessage):
            msg = await ctx.sendEmbed(
                title="Aktion erfolgreich",
                color=0x00ff00,
                description=error.description,
                **error.embedoptions,
            )
        else:
            errorembed = ctx.getEmbed(title="Fehler", color=0xff0000)

            if isinstance(error, commands.CommandError):
                if isinstance(error, commands.ConversionError):
                    errorembed.add_field(
                        name="Info", value="Beim Konvertieren von Parametern ist ein Fehler aufgetreten!")

                elif isinstance(error, commands.UserInputError):
                    if isinstance(error, commands.MissingRequiredArgument):
                        errorembed.add_field(
                            name="Info", value="Du hast einen benötigten Parameter weggelassen!")
                        errorembed.add_field(name="Parameter",
                                        value=error.param.name)
                    elif isinstance(error, commands.TooManyArguments):
                        errorembed.add_field(
                            name="Info", value="Du hast zu viele Parameter angegeben!")
                    elif isinstance(error, commands.BadArgument):
                        errorembed.add_field(
                            name="Info", value="Ein Parameter konnte nicht in den verwendeten Typen konvertiert werden!")
                        if hasattr(error, "argument"):
                            errorembed.add_field(name="Parameter",
                                            value=error.argument)
                        # [...]
                    elif isinstance(error, commands.BadUnionArgument):
                        errorembed.add_field(
                            name="Info", value="Ein Parameter konnte nicht in einen der verwendeten Typen konvertiert werden!")
                        errorembed.add_field(name="Parameter",
                                        value=error.param.name)
                    elif isinstance(error, commands.ArgumentParsingError):
                        errorembed.add_field(
                            name="Info", value="Dieser Fehler liegt womöglich an fehlenden oder falsch gesetzten Anführungszeichen!")
                    else:
                        errorembed.add_field(
                            name="Info", value="Ein Parameter konnte aufgrund eines Eingabefehlers nicht verarbeitet werden! Hast du alles richtig eingegeben?")

                elif isinstance(error, commands.CommandNotFound):
                    errorembed.add_field(
                        name="Info", value="Dieser Befehl wurde nicht gefunden!")

                elif isinstance(error, commands.CheckFailure):
                    if isinstance(error, commands.PrivateMessageOnly):
                        errorembed.add_field(
                            name="Info", value="Dieser Command kann nur in Direktnachrichten werden!")
                    elif isinstance(error, commands.NoPrivateMessage):
                        errorembed.add_field(
                            name="Info", value="Dieser Command kann nur auf einem Server verwendet werden!")
                    elif isinstance(error, commands.NotOwner):
                        errorembed.add_field(
                            name="Info", value="Du bist nicht Besitzer des Bots!")
                        return  # keine Nachricht senden!
                    elif isinstance(error, commands.MissingPermissions):
                        errorembed.add_field(
                            name="Info", value="Du hast nicht die nötigen Berechtigungen für diesen Command!")
                        errorembed.add_field(name="Berechtigung(en)",
                                        value=", ".join(error.missing_perms))
                    elif isinstance(error, commands.BotMissingPermissions):
                        errorembed.add_field(
                            name="Info", value="Ich habe nicht die nötigen Berechtigungen für diesen Command!")
                        errorembed.add_field(name="Berechtigung(en)",
                                        value=", ".join(error.missing_perms))
                    elif isinstance(error, commands.MissingRole):
                        errorembed.add_field(
                            name="Info", value="Du hast die benötigte Rolle nicht, um diesen Befehl auszuführen!")
                        errorembed.add_field(
                            name="Rolle", value=str(error.missing_role))
                    elif isinstance(error, commands.BotMissingRole):
                        errorembed.add_field(
                            name="Info", value="Ich habe die benötigte Rolle nicht, um diesen Befehl auszuführen!")
                        errorembed.add_field(
                            name="Rolle", value=str(error.missing_role))
                    elif isinstance(error, commands.MissingAnyRole):
                        errorembed.add_field(
                            name="Info", value="Du hast keine der benötigten Rollen, um diesen Befehl auszuführen!")
                        errorembed.add_field(
                            name="Rollen", value=", ".join(error.missing_roles))
                    elif isinstance(error, commands.BotMissingAnyRole):
                        errorembed.add_field(
                            name="Info", value="Ich habe keine der benötigten Rollen, um diesen Befehl auszuführen!")
                        errorembed.add_field(
                            name="Rollen", value=", ".join(error.missing_roles))
                    elif isinstance(error, commands.NSFWChannelRequired):
                        errorembed.add_field(
                            name="Info", value="Dieser Befehl darf nur in einem NSFW Kanal ausgeführt werden!")
                    else:
                        errorembed.add_field(
                            name="Info", value="Eine unbekannte Bedingung, welche für diesen Befehl wichtig ist, wurde nicht erfüllt.")

                elif isinstance(error, commands.DisabledCommand):
                    errorembed.add_field(
                        name="Info", value="Dieser Command ist aktuell deaktiviert!")

                elif isinstance(error, commands.CommandInvokeError):
                    errorembed.add_field(
                        name="Info", value="Beim Ausführen eines Befehls ist ein Fehler aufgetreten!")

                elif isinstance(error, commands.CommandOnCooldown):
                    errorembed.add_field(
                        name="Info", value="Warte, bis du diesen Befehl erneut benutzen kannst!")
                    errorembed.add_field(
                        name="Zeit", value=f"Versuche es in {int(error.retry_after)}s erneut!")

                else:
                    errorembed.add_field(
                        name="Info", value="Bei einem Befehl ist ein Fehler aufgetreten!")
            else:
                errorembed.add_field(
                    name="Info", value="Es ist ein unbekannter Fehler aufgetreten! Vermutlich liegt er nicht bei dir, also melde ihn am besten einem Admin.")
                if DEBUG:
                    print("[Command] - Bei '"+ctx.message.content+"' von '"+ctx.message.author.name +
                          "#"+ctx.message.author.discriminator+"' ist ein Fehler aufgetreten: "+str(error))

            if not error == "" and "OperationalError: (2006, 'MySQL server has gone away')" in str(error):
                errorembed.add_field(
                    name="Info", value="Leider konnte die Verbindung zur Datenbank nicht hergestellt werden. Bitte versuche es später noch einmal!")

            errorembed.add_field(name="Nachricht",
                            value=ctx.message.content, inline=False)
            msg = await ctx.send(embed=errorembed, delete_after=10.0)

            if DEBUG and not True in [isinstance(error, cls) for cls in DEBUG_NO_RAISE_FOR]:
                raise error
