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
        description='Hilfe kommt!',
        aliases=["hilfe","commands","command","?","cmds"],
        help="Benutze /help <Kategorie/Befehl> für genauere Hilfe.",
        usage="<Kategorie/Befehl>"
    )
    async def help(self, ctx, search:str='*'):
        help_embed = ctx.getEmbed(title='Hilfe', color=self.color, inline=False)

        def addCog(cog):
            if not cog.qualified_name in ["Owneronly"]:
                cog_commands = cog.get_commands()
                commands_list = ''
                for comm in cog_commands:
                    commands_list += f'**{comm.name}** - *{comm.brief}*\n'

                help_embed.add_field(
                    name=cog.qualified_name,
                    value=commands_list+'\u200b',
                    inline=False
                )

        def addCommand(cmd):
            help_text = ''
            help_text += f'```/{cmd.name} - {cmd.brief}```\n' + f'Kurzbeschreibung: `{cmd.description}`\n' + f'Beschreibung: `{cmd.help}`\n\n'

            if len(cmd.aliases) > 0:
                help_text += f'Aliases: `/{"`, `/".join(cmd.aliases)}`\n'
            else:
                help_text += '\n'

            help_text += f'Format: `/{cmd.name}{" "+cmd.usage if cmd.usage is not None else ""}`\n\n'
            help_embed.description += help_text


        cogs = dict((k.lower(), v) for k, v in dict(self.bot.cogs).items())
        cmds = dict((c.name.lower(),c) for c in self.bot.commands)

        if search == '*':
            for cog in cogs:
                addCog(cogs[cog])

        elif search in cmds:
            addCommand(cmds[search])

        elif search in cogs:
            addCog(cogs[search])

        else:
            raise commands.BadArgument("Ungültige(r) Kategorie/Befehl.\nBenutze den `/help` Befehl um alle Kategorien und Befehle zu sehen.")

        await ctx.send(embed=help_embed)
        return


def setup(bot):
    bot.add_cog(Help(bot))
