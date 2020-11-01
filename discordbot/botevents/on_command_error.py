# pylint: disable=unused-variable

from discord.ext import commands
from discord import Embed

def setup(bot):
    @bot.event
    async def on_command_error(ctx, error):
        EMBED = Embed(title="Fehler", color=0xff0000)
        EMBED.set_footer(text=f'Angefordert von {ctx.message.author.name}#{ctx.message.author.discriminator}',icon_url=ctx.author.avatar_url)
        if isinstance(error, commands.BadArgument):
            EMBED.add_field(name="Beschreibung", value="Du hast ungültige Argumente angegeben!")
        elif isinstance(error, commands.MissingRequiredArgument):
            EMBED.add_field(name="Beschreibung", value="Du hast ein benötigtes Argument weggelassen!")
        elif isinstance(error, commands.CommandNotFound):
            EMBED.add_field(name="Beschreibung", value="Dieser Command existiert nicht!")
            print("[Command] - '"+ctx.message.content+"' von '"+ctx.message.author.name+"' wurde nicht gefunden")
            return # keine Nachricht senden!
        elif isinstance(error, commands.CommandError):
            EMBED.add_field(name="Beschreibung", value="Bei einem Befehl ist ein Fehler aufgetreten!")
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
        else:
            EMBED.add_field(name="Beschreibung", value="Es ist ein unbekannter Fehler aufgetreten! Vermutlich liegt er nicht bei dir, also melde ihn am besten einen Admin.")
            print("[Command] - Bei '"+ctx.message.content+"' von '"+ctx.message.author.name+"#"+ctx.message.author.discriminator+"' ist ein Fehler aufgetreten: "+str(error))
        
        if not error == "":
            EMBED.add_field(name="Text", value=str(error) if len(str(error)) < 1024 else str(error)[-1024:-1])
        EMBED.add_field(name="Nachricht", value=ctx.message.content, inline=False)
        await ctx.send(embed=EMBED)

        if type(error) in [commands.CommandError]:
            raise error
