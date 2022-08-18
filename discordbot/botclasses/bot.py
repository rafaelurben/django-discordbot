import discord
from discord.ext import commands

from discordbot import config, botclasses
from discordbot.botmodules.serverdata import DjangoConnection
from discordbot.errors import ErrorMessage, SuccessMessage

class Bot(commands.Bot):
    def __init__(self, **kwargs):
        super().__init__(self.get_command_prefix, **kwargs)

    def get_command_prefix(self, client, message):
        if message.guild:
            prefixes = config.MAIN_PREFIXES
        else:
            prefixes = config.ALL_PREFIXES
        return commands.when_mentioned_or(*prefixes)(client, message)

    async def get_context(self, message, *, cls=botclasses.Context):
        return await super().get_context(message, cls=cls)

    def getEmbed(self, title: str, description: str = "", color: int = 0x000000, fields: list = [], inline=True, thumbnailurl: str = None, authorurl: str = "", authorname: str = None, footertext: str = None, footerurl: str = None, timestamp=False):
        emb = discord.Embed(title=title[:256], description=description[:2048], color=color)
        if footertext:
            if footerurl:
                emb.set_footer(text=footertext[:2048], icon_url=footerurl)
            else:
                emb.set_footer(text=footertext[:2048])

        if timestamp:
            emb.timestamp = discord.utils.utcnow() if timestamp is True else timestamp
        for field in fields:
            emb.add_field(name=field[0][:256], value=(field[1][:1018]+" [...]" if len(field[1]) > 1024 else field[1]), inline=bool(
                field[2] if len(field) > 2 else inline))
        if thumbnailurl:
            emb.set_thumbnail(url=thumbnailurl.strip())
        if authorname:
            if authorurl and ("https://" in authorurl or "http://" in authorurl):
                emb.set_author(name=authorname[:256], url=authorurl.strip())
            else:
                emb.set_author(name=authorname[:256])
        return emb

    # Events

    async def on_message(self, message):
        if message.author != self.user:
            is_bot = message.author.bot
            is_webhook = bool(message.webhook_id)

            if (not is_bot) or ((config.ALLOW_BOTS and not is_webhook) or (config.ALLOW_WEBHOOKS and is_webhook)):
                ctx = await self.get_context(message)
                await self.invoke(ctx)

    async def on_command(self, ctx: commands.Context):
        if config.DEBUG:
            print(f"[Command] - '{ctx.message.content}' von '{ctx.author.name}#{str(ctx.author.discriminator)}'")
        if ctx.guild is not None:
            try:
                await ctx.message.delete()
            except discord.DiscordException:
                ...

    async def on_ready(self):
        print(f"[Bot] - Logged in as '{self.user.name}' - '{self.user.id}'")
        for extension in config.EXTENSIONS:
            try:
                await self.load_extension(config.EXTENSIONFOLDER+"."+extension)
            except commands.errors.ExtensionAlreadyLoaded:
                pass
        print("[Bot] - Loaded extensions!")
        await self.tree.sync()

    async def on_connect(self):
        print("[Bot] - Connected!")

    async def on_disconnect(self):
        print("[Bot] - Disconnected!")

    async def on_guild_join(self, guild):
        print(f"[Bot] - Joined new guild: {guild.name} ({guild.id})")
        await DjangoConnection.fetch_server(guild)

    async def on_command_error(self, ctx, error):
        if isinstance(error, ErrorMessage):
            await ctx.sendEmbed(
                title="Fehler",
                color=0xff0000,
                description=str(error),
                fields=[("Nachricht", ctx.message.content)],
            )
        elif isinstance(error, SuccessMessage):
            await ctx.sendEmbed(
                title="Aktion erfolgreich",
                color=0x00ff00,
                description=error.description,
                **error.embedoptions,
            )
        else:
            emb = ctx.getEmbed(title="Fehler", color=0xff0000)

            if isinstance(error, commands.CommandError):
                if isinstance(error, commands.ConversionError):
                    emb.add_field(
                        name="Info", value="Beim Konvertieren von Parametern ist ein Fehler aufgetreten!")

                elif isinstance(error, commands.UserInputError):
                    if isinstance(error, commands.MissingRequiredArgument):
                        emb.add_field(
                            name="Info", value="Du hast einen benötigten Parameter weggelassen!")
                        emb.add_field(name="Parameter",
                                        value=error.param.name)
                    elif isinstance(error, commands.TooManyArguments):
                        emb.add_field(
                            name="Info", value="Du hast zu viele Parameter angegeben!")
                    elif isinstance(error, commands.BadArgument):
                        emb.add_field(
                            name="Info", value="Ein Parameter konnte nicht in den verwendeten Typen konvertiert werden!")
                        if hasattr(error, "argument"):
                            emb.add_field(name="Parameter",
                                            value=error.argument)
                        # [...]
                    elif isinstance(error, commands.BadUnionArgument):
                        emb.add_field(
                            name="Info", value="Ein Parameter konnte nicht in einen der verwendeten Typen konvertiert werden!")
                        emb.add_field(name="Parameter",
                                        value=error.param.name)
                    elif isinstance(error, commands.ArgumentParsingError):
                        emb.add_field(
                            name="Info", value="Dieser Fehler liegt womöglich an fehlenden oder falsch gesetzten Anführungszeichen!")
                    else:
                        emb.add_field(
                            name="Info", value="Ein Parameter konnte aufgrund eines Eingabefehlers nicht verarbeitet werden! Hast du alles richtig eingegeben?")

                elif isinstance(error, commands.CommandNotFound):
                    emb.add_field(
                        name="Info", value="Dieser Befehl wurde nicht gefunden!")

                elif isinstance(error, commands.CheckFailure):
                    if isinstance(error, commands.PrivateMessageOnly):
                        emb.add_field(
                            name="Info", value="Dieser Command kann nur in Direktnachrichten werden!")
                    elif isinstance(error, commands.NoPrivateMessage):
                        emb.add_field(
                            name="Info", value="Dieser Command kann nur auf einem Server verwendet werden!")
                    elif isinstance(error, commands.NotOwner):
                        emb.add_field(
                            name="Info", value="Du bist nicht Besitzer des Bots!")
                        return  # keine Nachricht senden!
                    elif isinstance(error, commands.MissingPermissions):
                        emb.add_field(
                            name="Info", value="Du hast nicht die nötigen Berechtigungen für diesen Command!")
                        emb.add_field(name="Berechtigung(en)",
                                        value=", ".join(error.missing_perms))
                    elif isinstance(error, commands.BotMissingPermissions):
                        emb.add_field(
                            name="Info", value="Ich habe nicht die nötigen Berechtigungen für diesen Command!")
                        emb.add_field(name="Berechtigung(en)",
                                        value=", ".join(error.missing_perms))
                    elif isinstance(error, commands.MissingRole):
                        emb.add_field(
                            name="Info", value="Du hast die benötigte Rolle nicht, um diesen Befehl auszuführen!")
                        emb.add_field(
                            name="Rolle", value=str(error.missing_role))
                    elif isinstance(error, commands.BotMissingRole):
                        emb.add_field(
                            name="Info", value="Ich habe die benötigte Rolle nicht, um diesen Befehl auszuführen!")
                        emb.add_field(
                            name="Rolle", value=str(error.missing_role))
                    elif isinstance(error, commands.MissingAnyRole):
                        emb.add_field(
                            name="Info", value="Du hast keine der benötigten Rollen, um diesen Befehl auszuführen!")
                        emb.add_field(
                            name="Rollen", value=", ".join(error.missing_roles))
                    elif isinstance(error, commands.BotMissingAnyRole):
                        emb.add_field(
                            name="Info", value="Ich habe keine der benötigten Rollen, um diesen Befehl auszuführen!")
                        emb.add_field(
                            name="Rollen", value=", ".join(error.missing_roles))
                    elif isinstance(error, commands.NSFWChannelRequired):
                        emb.add_field(
                            name="Info", value="Dieser Befehl darf nur in einem NSFW Kanal ausgeführt werden!")
                    else:
                        emb.add_field(
                            name="Info", value="Eine unbekannte Bedingung, welche für diesen Befehl wichtig ist, wurde nicht erfüllt.")

                elif isinstance(error, commands.DisabledCommand):
                    emb.add_field(
                        name="Info", value="Dieser Command ist aktuell deaktiviert!")

                elif isinstance(error, commands.CommandInvokeError):
                    emb.add_field(
                        name="Info", value="Beim Ausführen eines Befehls ist ein Fehler aufgetreten!")

                elif isinstance(error, commands.CommandOnCooldown):
                    emb.add_field(
                        name="Info", value="Warte, bis du diesen Befehl erneut benutzen kannst!")
                    emb.add_field(
                        name="Zeit", value=f"Versuche es in {int(error.retry_after)}s erneut!")

                else:
                    emb.add_field(
                        name="Info", value="Bei einem Befehl ist ein Fehler aufgetreten!")
            else:
                emb.add_field(
                    name="Info", value="Es ist ein unbekannter Fehler aufgetreten! Vermutlich liegt er nicht bei dir, also melde ihn am besten einem Admin.")
                if config.DEBUG:
                    print("[Command] - Bei '"+ctx.message.content+"' von '"+ctx.message.author.name +
                            "#"+ctx.message.author.discriminator+"' ist ein Fehler aufgetreten: "+str(error))

            if not error == "" and "OperationalError: (2006, 'MySQL server has gone away')" in str(error):
                emb.add_field(
                    name="Info", value="Leider konnte die Verbindung zur Datenbank nicht hergestellt werden. Bitte versuche es später noch einmal!")

            emb.add_field(name="Nachricht", value=ctx.message.content, inline=False)
            await ctx.send(embed=emb, delete_after=10.0)

            if config.DEBUG and not isinstance(error, config.DEBUG_NO_RAISE_FOR):
                raise error
