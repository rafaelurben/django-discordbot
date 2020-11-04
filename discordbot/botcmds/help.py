from discord.ext import commands
from discord import Embed
import random

class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.color = 0x000000

    @commands.command(
        name='help',
        brief='Erhalte Hilfe zu Commands',
        aliases=["hilfe", "commands", "command", "?", "cmds"],
        help="Benutze diesen Command für genauere Hilfe zur jeweiligen Kategorie / zum jeweiligen Befehl/Unterbefehl",
        usage="[Kategorie/Befehl/Befehl Unterbefehl]"
    )
    async def help(self, ctx, search:str='*', subsearch:str=None):
        help_embed = ctx.getEmbed(title='Hilfe', color=self.color, inline=False)
        help_embed.description = "Syntax: `/help [Kategorie/Befehl/Befehl Unterbefehl]`\n\n"

        def addCog(cog, include_subcommands=False, hide_cogs=["Owneronly"]):
            if not cog.qualified_name in hide_cogs:
                commands_list = ''
                for cmd in cog.walk_commands():
                    if include_subcommands:
                        depth = 0
                        currentcmd = cmd
                        while currentcmd.parent:
                            depth += 1
                            currentcmd = currentcmd.parent 

                        commands_list += "- "*depth + f'**{cmd.name}** - *{cmd.brief}*\n'
                    elif not cmd.parent:
                        commands_list += f'**{cmd.name}** - *{cmd.brief}*\n'

                help_embed.add_field(
                    name=cog.qualified_name,
                    value=commands_list+'\u200b',
                    inline=False
                )

        def addGroup(grp):
            commands_list = ''
            for cmd in grp.commands:
                commands_list += f'**{cmd.name}** - *{cmd.brief}*\n'

            help_embed.add_field(
                name="Unterbefehle von "+grp.qualified_name,
                value=commands_list+'\u200b',
                inline=False
            )

        def addCommand(cmd):
            if not cmd.hidden:
                if isinstance(cmd, commands.Group):
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

                cmdbrief = " - "+cmd.brief if cmd.brief else ""
                help_text = f'```/{cmdname}{cmdbrief}```\n' 

                if cmd.description:
                    help_text += f'Beschrieb: `{cmd.description}`\n\n'
                if cmd.help:
                    help_text += f'Hilfe: `{cmd.help}`\n\n'
                if cmd.aliases:
                    help_text += f'Alias: `{"`, `".join(cmd.aliases)}`'

                help_text += f'\nSyntax: `/{cmdname}{" "+cmd.usage if cmd.usage is not None else ""}`\n\u200b'
                help_embed.description += help_text
    

        cogs = dict((k.lower(), v) for k, v in dict(self.bot.cogs).items())
        cmds = dict((alias, cmd) for cmd in self.bot.commands for alias in cmd.aliases+[cmd.name.lower()])

        if search == '*':
            for cog in cogs:
                addCog(cogs[cog])

        elif search in cmds:
            addCommand(cmds[search])

        elif search in cogs:
            addCog(cogs[search], include_subcommands=True, hide_cogs=[])

        else:
            raise commands.BadArgument("Ungültige(r) Kategorie/Befehl.\nBenutze den `/help` Befehl um alle Kategorien und Befehle zu sehen.")

        await ctx.send(embed=help_embed)
        return


def setup(bot):
    bot.add_cog(Help(bot))
