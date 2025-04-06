import discord
from discord import app_commands
from discord.ext import commands

from discordbot import config
from discordbot.errors import ErrorMessage, SuccessMessage


def get_cog_field(cog: commands.Cog) -> tuple[str, str]:
    title = cog.qualified_name
    description = (cog.description + "\n") if cog.description else ""

    cmd: app_commands.Command | commands.Command
    command_counts: dict[app_commands.Command | commands.Command, int] = {}
    for cmd in list(cog.walk_commands()) + list(cog.walk_app_commands()):
        if cmd.parent is None:
            command_counts[cmd] = 0
        elif cmd.parent in command_counts:
            command_counts[cmd.parent] += 1

    for cmd, count in command_counts.items():
        if getattr(cmd, "hidden", False):
            continue

        if count:
            description += f"**/{cmd.name}** <+{count}>, "
        else:
            description += f"**/{cmd.name}**, "

    return title, description.rstrip(", ")


def get_cog_detail_description(cog: commands.Cog) -> str:
    description = (cog.description + "\n\n") if cog.description else ""

    cmd: app_commands.Command | commands.Command
    for cmd in list(cog.walk_commands()) + list(cog.walk_app_commands()):
        brief = (
            cmd.description
            if isinstance(cmd, (app_commands.Command, app_commands.Group))
            else cmd.brief
        )

        if cmd.parent is None:
            description += f"\n**/{cmd.name}** - {brief}\n"
        else:
            description += f"... **{cmd.name}** - {brief}\n"

    return description


def get_command_detail_description(
    cmd: (
        commands.Command
        | app_commands.Command
        | commands.Group
        | app_commands.Group
    ),
) -> str:
    description = ""
    if getattr(cmd, "hidden", False):
        description += "\n*Dies ist ein versteckter Befehl*\n\n"
    if isinstance(cmd, app_commands.Group):
        description += "Dies ist eine Befehlsgruppe und kann nur zusammen mit einem Unterbefehl aufgerufen werden.\n\n"

    cmd_name = cmd.name
    current_cmd = cmd
    while current_cmd.parent:
        current_cmd = current_cmd.parent
        cmd_name = current_cmd.name + " " + cmd_name

    cmd_usage = f" {cmd.usage}" if hasattr(cmd, "usage") else ""
    description = f"```/{cmd_name}{cmd_usage}```\n"

    if getattr(cmd, "brief", None):
        description += f"Kurzbeschrieb: `{cmd.brief}`\n"
    if getattr(cmd, "description", None):
        description += f"Beschrieb: `{cmd.description}`\n"
    cmd_help = getattr(cmd, "help", None) or cmd.extras.get("help", None)
    if cmd_help:
        description += f"Hilfe: `{cmd_help}`\n"
    if getattr(cmd, "aliases", None):
        description += f'Alias: `{"`, `".join(cmd.aliases)}`\n'

    if isinstance(cmd, (commands.Group, app_commands.Group)) and getattr(
        cmd, "commands", None
    ):
        description += "### Unterbefehle\n\n"
        for sub_cmd in cmd.commands:
            brief = (
                sub_cmd.description
                if isinstance(
                    sub_cmd, (app_commands.Command, app_commands.Group)
                )
                else sub_cmd.brief
            )

            description += f"**/{cmd_name} {sub_cmd.name}** - {brief}\n"

    return description


class Help(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.color = 0x000000

    @app_commands.command(
        name="help",
        description="Erhalte Hilfe zu Befehlen",
        extras={
            "help": "Verwende den Befehl ohne Optionen, um alle Befehle anzuzeigen."
        },
    )
    @app_commands.rename(
        category_search="category",
        command_search="command",
        subcommand_search="subcommand",
    )
    @app_commands.describe(
        category_search="Kategorie",
        command_search="Befehl",
        subcommand_search="Unterbefehl",
    )
    async def help(
        self,
        interaction: discord.Interaction,
        category_search: str = None,
        command_search: str = None,
        subcommand_search: str = None,
    ):
        if category_search is not None:
            if command_search is not None or subcommand_search is not None:
                raise ErrorMessage(
                    "Du kannst die Option _category_ nicht gemeinsam mit _command_ und _subcommand_ verwenden."
                )
            # Single cog
            all_cogs = dict(
                (k.lower(), v) for k, v in dict(self.bot.cogs).items()
            )
            if category_search.lower() in all_cogs:
                cog = all_cogs[category_search.lower()]
                raise SuccessMessage(
                    get_cog_detail_description(cog),
                    title=f"Hilfe - Kategorie '{cog.qualified_name}'",
                    color=self.color,
                )
        elif command_search is not None:
            command_search = command_search.lower().strip(" /")
            # Single command
            cmd = self.bot.get_command(
                command_search
            ) or self.bot.tree.get_command(command_search)
            if cmd is not None:
                if subcommand_search is None:
                    raise SuccessMessage(
                        get_command_detail_description(cmd),
                        title=f"Hilfe - Befehl '/{cmd.name}'",
                        color=self.color,
                    )
                elif not isinstance(cmd, (commands.Group, app_commands.Group)):
                    raise ErrorMessage("Dieser Befehl hat keine Unterbefehle!")

                # Single subcommand
                sub_cmd = cmd.get_command(
                    subcommand_search.lower().strip(" /")
                )
                if sub_cmd:
                    raise SuccessMessage(
                        get_command_detail_description(sub_cmd),
                        title=f"Hilfe - Unterbefehl '/{cmd.name} {sub_cmd.name}'",
                        color=self.color,
                    )
        elif subcommand_search is not None:
            raise ErrorMessage(
                "Du kannst die Option _subcommand_ nur in Verbindung mit _command_ verwenden."
            )
        else:
            # All cogs
            raise SuccessMessage(
                f"Verwende /help mit Argumenten, um spezifischere Infos zu erhalten.",
                title="Hilfe - Alle Kategorien",
                inline=False,
                fields=[
                    get_cog_field(cog)
                    for k, cog in self.bot.cogs.items()
                    if k.lower() not in config.HELP_HIDDEN_COGS
                ],
                color=self.color,
            )

        raise ErrorMessage("Kein passender Inhalt gefunden!")


async def setup(bot):
    await bot.add_cog(Help(bot))
