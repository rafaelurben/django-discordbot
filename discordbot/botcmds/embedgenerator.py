import json
from typing import Optional

import discord
from discord import Interaction, app_commands
from discord.ext import commands

from discordbot.errors import ErrorMessage
from discordbot.utils import getEmbed


def embed_to_str(embed: discord.Embed) -> str:
    data = embed.to_dict()
    return json.dumps(data, indent=2, ensure_ascii=False).replace(
        "```", "\\`\\`\\`"
    )


def str_to_embed(value: str) -> discord.Embed:
    data = json.loads(value.replace("\\`\\`\\`", "```"))
    return discord.Embed.from_dict(data)


class EmbedTransformer(app_commands.Transformer):
    def transform(
        self, interaction: Interaction, value: str, /
    ) -> discord.Embed:
        return str_to_embed(value)


class EmbedGenerator(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.color = 0x34B7EB

        self.ctx_menu_copy_embed = app_commands.ContextMenu(
            name="Embed(s) kopieren (JSON)",
            callback=self.copy_embed_contextmenu,
        )
        self.bot.tree.add_command(self.ctx_menu_copy_embed)

    def cog_unload(self) -> None:
        self.bot.tree.remove_command(
            self.ctx_menu_copy_embed.name, type=self.ctx_menu_copy_embed.type
        )

    @app_commands.allowed_installs(guilds=True, users=True)
    async def copy_embed_contextmenu(
        self, interaction: discord.interactions, message: discord.Message
    ):
        if not message.embeds:
            raise ErrorMessage("Keine Embeds gefunden!")

        description = f"Original-Nachricht: {message.jump_url}"
        for i, embed in enumerate(message.embeds):
            embed_str = embed_to_str(embed)
            description += f"\n### Embed {i + 1}\n```json\n{embed_str}\n```"

        await interaction.response.send_message(
            ephemeral=True,
            embed=getEmbed(
                title="Kopierte Embeds",
                description=description,
            ),
        )

    group = app_commands.Group(
        name="embeds",
        description="Clone, generate and update embeds",
        guild_only=True,
        allowed_installs=app_commands.AppInstallationType(guild=True),
    )

    @group.command(
        name="send", description="Sende Embeds in den aktuellen Kanal"
    )
    async def send_embed(
        self,
        interaction: discord.Interaction,
        embed1: app_commands.Transform[discord.Embed, EmbedTransformer],
        embed2: Optional[
            app_commands.Transform[discord.Embed, EmbedTransformer]
        ],
        embed3: Optional[
            app_commands.Transform[discord.Embed, EmbedTransformer]
        ],
        embed4: Optional[
            app_commands.Transform[discord.Embed, EmbedTransformer]
        ],
        embed5: Optional[
            app_commands.Transform[discord.Embed, EmbedTransformer]
        ],
        embed6: Optional[
            app_commands.Transform[discord.Embed, EmbedTransformer]
        ],
        embed7: Optional[
            app_commands.Transform[discord.Embed, EmbedTransformer]
        ],
        embed8: Optional[
            app_commands.Transform[discord.Embed, EmbedTransformer]
        ],
        embed9: Optional[
            app_commands.Transform[discord.Embed, EmbedTransformer]
        ],
        embed10: Optional[
            app_commands.Transform[discord.Embed, EmbedTransformer]
        ],
    ):
        embeds = [embed1]
        for emb in [
            embed2,
            embed3,
            embed4,
            embed5,
            embed6,
            embed7,
            embed8,
            embed9,
            embed10,
        ]:
            if emb:
                embeds.append(emb)

        await interaction.response.send_message(ephemeral=False, embeds=embeds)


async def setup(bot):
    await bot.add_cog(EmbedGenerator(bot))
