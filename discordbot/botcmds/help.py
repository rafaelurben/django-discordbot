from discord.ext import commands
from discord import app_commands
import discord

from discordbot import config, utils

class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.color = 0x000000

    @app_commands.command(
        name='help',
        description='Erhalte Hilfe zu einem Befehl',
    )
    @app_commands.describe(search='Befehl oder Kategorie', subsearch='Unterbefehl')
    async def help(self, interaction: discord.Interaction, search:str=None, subsearch:str=None):
        description = ["Syntax: `/help [Kategorie/Befehl/Befehl Unterbefehl]`\n\n"]
        fields = []

        def addCog(cog, include_subcommands=False, hide_cogs=config.HELP_HIDDEN_COGS):
            if not cog.qualified_name.lower() in hide_cogs:
                commands_list = ''
                for cmd in list(cog.walk_commands())+list(cog.walk_app_commands()):
                    if not getattr(cmd, 'hidden', False):
                        if include_subcommands:
                            depth = 0
                            currentcmd = cmd
                            while currentcmd.parent:
                                depth += 1
                                currentcmd = currentcmd.parent

                            if depth == 0:
                                commands_list += f'\n**{cmd.name}** - {cmd.brief}\n' if hasattr(cmd, 'brief') else f'\n**{cmd.name}**\n'
                            elif depth == 1:
                                commands_list += f'- {cmd.name} '
                            # else:
                            #    commands_list += "- "*depth + f'**{cmd.name}**\n'
                        elif not cmd.parent:
                            commands_list += f'**{cmd.name}** - {cmd.brief}\n' if hasattr(cmd, 'brief') else f'**{cmd.name}**\n'

                fields.append((cog.qualified_name, commands_list.replace("\n\n", "\n")+'\u200b'))

        def addGroup(grp):
            commands_list = ''
            for cmd in grp.walk_commands():
                if not getattr(cmd, 'hidden', False):
                    commands_list += f'**{cmd.name}** - {cmd.brief}\n' if hasattr(cmd, 'brief') else f'**{cmd.name}**\n'

            fields.append(("Unterbefehle von "+grp.qualified_name, commands_list+'\u200b'))

        def addCommand(cmd):
            if getattr(cmd, 'hidden', False):
                description[0] += "\n*Dies ist ein versteckter Befehl*\n\n"
            if isinstance(cmd, (commands.Group, app_commands.Group)):
                if subsearch:
                    subcmds = dict((alias, cmd) for cmd in cmd.commands for alias in cmd.aliases+[cmd.name.lower()])
                    if subsearch in subcmds:
                        addCommand(subcmds[subsearch])
                        return
                addGroup(cmd)

            cmdname = cmd.name
            currentcmd = cmd
            while currentcmd.parent:
                currentcmd = currentcmd.parent
                cmdname = currentcmd.name + " " + cmdname

            cmdbrief = " - "+cmd.brief if getattr(cmd, 'brief', None) else ""
            help_text = f'```/{cmdname}{cmdbrief}```\n'

            if getattr(cmd, 'aliases', None):
                help_text += f'Beschrieb: `{cmd.description}`\n\n'
            if getattr(cmd, 'help', None):
                help_text += f'Hilfe: `{cmd.help}`\n\n'
            if getattr(cmd, 'aliases', None):
                help_text += f'Alias: `{"`, `".join(cmd.aliases)}`'

            help_text += f'\nSyntax: `/{cmdname}{" "+cmd.usage if cmd.usage is not None else ""}`\n\u200b'
            description[0] += help_text

        cogs = dict((k.lower(), v) for k, v in dict(self.bot.cogs).items())
        cmds = dict((alias, cmd) for cmd in self.bot.commands for alias in cmd.aliases+[cmd.name.lower()])

        if search is None:
            for cog in cogs:
                addCog(cogs[cog])

        elif search in cmds:
            addCommand(cmds[search])

        elif search in cogs:
            addCog(cogs[search], include_subcommands=True, hide_cogs=[])

        else:
            return await interaction.response.send_message("Ungültige(r) Kategorie/Befehl.\nBenutze den `/help` Befehl um alle Kategorien und Befehle zu sehen.", ephemeral=True)

        await interaction.response.send_message(
            embed=utils.getEmbed(
                author=interaction.user,
                title='Hilfe',
                inline=False,
                description=description[0],
                fields=fields,
            ),
            ephemeral=True,
        )


async def setup(bot):
    await bot.add_cog(Help(bot))
