from discord.ext import commands
from discord import app_commands
import discord

from discordbot.botmodules import converters
from discordbot import utils

class Converters(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.color = 0xffffff

    @app_commands.command(
        name='convert',
        description="Verwandle Dinge in ein anderes Format.",
    )
    @app_commands.describe(fmt="Format", value="Wert")
    @app_commands.rename(fmt="format")
    @app_commands.choices(fmt=[
        app_commands.Choice(name='Morse -> Text', value="morse_text"),
        app_commands.Choice(name='Text -> Morse', value="test_morse"),
    ])
    async def convert(self, interaction: discord.Interaction, fmt: app_commands.Choice[str], value: str):
        if fmt.value == "morse_text":
            morse = value
            text = converters.morse_decrypt(morse.replace("_","-").replace(" | ", "  "))
            await interaction.response.send_message(embed=utils.getEmbed(
                title="Morsecode", fields=[("Morsecode", morse.replace("  "," | ")), ("Text", text)], inline=False
            ))
        elif fmt.value == "test_morse":
            text = value
            morse = converters.morse_encrypt(text)
            await interaction.response.send_message(embed=utils.getEmbed(
                title="Morsecode", fields=[("Morsecode", morse.replace("  "," | ")), ("Text", text)], inline=False
            ))

async def setup(bot):
    await bot.add_cog(Converters(bot))
