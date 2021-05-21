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
            EMBED = ctx.getEmbed(title="Fehler", color=0xff0000)

            if isinstance(error, commands.CommandError):
                if isinstance(error, commands.ConversionError):
                    EMBED.add_field(
                        name="Info", value="Beim Konvertieren von Parametern ist ein Fehler aufgetreten!")

                elif isinstance(error, commands.UserInputError):
                    if isinstance(error, commands.MissingRequiredArgument):
                        EMBED.add_field(
                            name="Info", value="Du hast einen benötigten Parameter weggelassen!")
                        EMBED.add_field(name="Parameter",
                                        value=error.param.name)
                    elif isinstance(error, commands.TooManyArguments):
                        EMBED.add_field(
                            name="Info", value="Du hast zu viele Parameter angegeben!")
                    elif isinstance(error, commands.BadArgument):
                        EMBED.add_field(
                            name="Info", value="Ein Parameter konnte nicht in den verwendeten Typen konvertiert werden!")
                        if hasattr(error, "argument"):
                            EMBED.add_field(name="Parameter",
                                            value=error.argument)
                        # [...]
                    elif isinstance(error, commands.BadUnionArgument):
                        EMBED.add_field(
                            name="Info", value="Ein Parameter konnte nicht in einen der verwendeten Typen konvertiert werden!")
                        EMBED.add_field(name="Parameter",
                                        value=error.param.name)
                    elif isinstance(error, commands.ArgumentParsingError):
                        EMBED.add_field(
                            name="Info", value="Dieser Fehler liegt womöglich an fehlenden oder falsch gesetzten Anführungszeichen!")
                    else:
                        EMBED.add_field(
                            name="Info", value="Ein Parameter konnte aufgrund eines Eingabefehlers nicht verarbeitet werden! Hast du alles richtig eingegeben?")

                elif isinstance(error, commands.CommandNotFound):
                    EMBED.add_field(
                        name="Info", value="Dieser Befehl wurde nicht gefunden!")

                elif isinstance(error, commands.CheckFailure):
                    if isinstance(error, commands.PrivateMessageOnly):
                        EMBED.add_field(
                            name="Info", value="Dieser Command kann nur in Direktnachrichten werden!")
                    elif isinstance(error, commands.NoPrivateMessage):
                        EMBED.add_field(
                            name="Info", value="Dieser Command kann nur auf einem Server verwendet werden!")
                    elif isinstance(error, commands.NotOwner):
                        EMBED.add_field(
                            name="Info", value="Du bist nicht Besitzer des Bots!")
                        return  # keine Nachricht senden!
                    elif isinstance(error, commands.MissingPermissions):
                        EMBED.add_field(
                            name="Info", value="Du hast nicht die nötigen Berechtigungen für diesen Command!")
                        EMBED.add_field(name="Berechtigung(en)",
                                        value=", ".join(error.missing_perms))
                    elif isinstance(error, commands.BotMissingPermissions):
                        EMBED.add_field(
                            name="Info", value="Ich habe nicht die nötigen Berechtigungen für diesen Command!")
                        EMBED.add_field(name="Berechtigung(en)",
                                        value=", ".join(error.missing_perms))
                    elif isinstance(error, commands.MissingRole):
                        EMBED.add_field(
                            name="Info", value="Du hast die benötigte Rolle nicht, um diesen Befehl auszuführen!")
                        EMBED.add_field(
                            name="Rolle", value=str(error.missing_role))
                    elif isinstance(error, commands.BotMissingRole):
                        EMBED.add_field(
                            name="Info", value="Ich habe die benötigte Rolle nicht, um diesen Befehl auszuführen!")
                        EMBED.add_field(
                            name="Rolle", value=str(error.missing_role))
                    elif isinstance(error, commands.MissingAnyRole):
                        EMBED.add_field(
                            name="Info", value="Du hast keine der benötigten Rollen, um diesen Befehl auszuführen!")
                        EMBED.add_field(
                            name="Rollen", value=", ".join(error.missing_roles))
                    elif isinstance(error, commands.BotMissingAnyRole):
                        EMBED.add_field(
                            name="Info", value="Ich habe keine der benötigten Rollen, um diesen Befehl auszuführen!")
                        EMBED.add_field(
                            name="Rollen", value=", ".join(error.missing_roles))
                    elif isinstance(error, commands.NSFWChannelRequired):
                        EMBED.add_field(
                            name="Info", value="Dieser Befehl darf nur in einem NSFW Kanal ausgeführt werden!")
                    else:
                        EMBED.add_field(
                            name="Info", value="Eine unbekannte Bedingung, welche für diesen Befehl wichtig ist, wurde nicht erfüllt.")

                elif isinstance(error, commands.DisabledCommand):
                    EMBED.add_field(
                        name="Info", value="Dieser Command ist aktuell deaktiviert!")

                elif isinstance(error, commands.CommandInvokeError):
                    EMBED.add_field(
                        name="Info", value="Beim Ausführen eines Befehls ist ein Fehler aufgetreten!")

                elif isinstance(error, commands.CommandOnCooldown):
                    EMBED.add_field(
                        name="Info", value="Warte, bis du diesen Befehl erneut benutzen kannst!")
                    EMBED.add_field(
                        name="Zeit", value=f"Versuche es in {int(error.retry_after)}s erneut!")

                else:
                    EMBED.add_field(
                        name="Info", value="Bei einem Befehl ist ein Fehler aufgetreten!")
            else:
                EMBED.add_field(
                    name="Info", value="Es ist ein unbekannter Fehler aufgetreten! Vermutlich liegt er nicht bei dir, also melde ihn am besten einem Admin.")
                if DEBUG:
                    print("[Command] - Bei '"+ctx.message.content+"' von '"+ctx.message.author.name +
                          "#"+ctx.message.author.discriminator+"' ist ein Fehler aufgetreten: "+str(error))

            if not error == "" and "OperationalError: (2006, 'MySQL server has gone away')" in str(error):
                EMBED.add_field(
                    name="Info", value="Leider konnte die Verbindung zur Datenbank nicht hergestellt werden. Bitte versuche es später noch einmal!")

            EMBED.add_field(name="Nachricht",
                            value=ctx.message.content, inline=False)
            msg = await ctx.send(embed=EMBED)

            if DEBUG and not True in [isinstance(error, cls) for cls in DEBUG_NO_RAISE_FOR]:
                raise error

        try:
            await asyncio.sleep(10)
            await msg.delete()
        except commands.MessageNotFound:
            pass
