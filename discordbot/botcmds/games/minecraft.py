# pylint: disable=no-member

import base64

import discord
import json
import requests
from discord import app_commands
from discord.ext import commands

from discordbot import utils
from discordbot.errors import ErrorMessage


class MinecraftAPI:
    @classmethod
    def get_uuid(cls, name: str):
        r = requests.get(
            'https://api.mojang.com/users/profiles/minecraft/' + name)

        if r.status_code == 204 or r.status_code == 404:
            raise ErrorMessage(message="Spieler wurde nicht gefunden!")
        if r.status_code == 400:
            raise ErrorMessage(message="Ungültiger Spielername!")
        if r.status_code == 429:
            raise ErrorMessage(message="Mojangs Server wollen nicht antworten. Versuche es in einer Minute erneut!")

        return r.json()["id"]

    @classmethod
    def get_name(cls, uuid: str):
        r = requests.get(
            'https://api.mojang.com/user/profile/' + uuid)

        if r.status_code == 204 or r.status_code == 404:
            raise ErrorMessage(message="Spieler wurde nicht gefunden!")
        if r.status_code == 400:
            raise ErrorMessage(message="Ungültige UUID!")
        if r.status_code == 429:
            raise ErrorMessage(message="Mojangs Server wollen nicht antworten. Versuche es in einer Minute erneut!")

        return r.json()["name"]

    @classmethod
    def get_profile(cls, uuid: str):
        r = requests.get(
            'https://sessionserver.mojang.com/session/minecraft/profile/' + str(uuid))

        if r.status_code == 204 or r.status_code == 404:
            raise ErrorMessage(message="Spieler wurde nicht gefunden!")
        if r.status_code == 400:
            raise ErrorMessage(message="Ungültige UUID!")
        if r.status_code == 429:
            raise ErrorMessage(message="Mojangs Server wollen nicht antworten. Versuche es in einer Minute erneut!")

        data = r.json()
        if "error" in data:
            raise ErrorMessage(
                message="Abfrage für einen Skin kann pro UUID maximal ein Mal pro Minute erfolgen!")

        ppty = data["properties"][0]
        base64_message = ppty["value"]
        base64_bytes = base64_message.encode('ascii')
        message_bytes = base64.b64decode(base64_bytes)
        message_string = message_bytes.decode('ascii')
        message_dict = json.loads(message_string)

        data["textures"] = message_dict.get("textures", None)
        return data


class MinecraftCog(commands.Cog, name="Minecraft"):
    def __init__(self, bot):
        self.bot = bot
        self.color = 0x1f871e

    group = app_commands.Group(name="minecraft", description="Erhalte Infos über Minecraft-Spieler")

    @group.command(
        name="uuid",
        description="Erhalte die UUID eines Minecraft-Spielers",
    )
    @app_commands.describe(name="Name des Spielers")
    async def cmd_uuid(self, interaction: discord.Interaction, name: str):
        await interaction.response.defer()

        uuid = MinecraftAPI.get_uuid(name)
        embed = utils.getEmbed(title="Minecraft Spieler",
                               fields=[("Name", name, False), ("UUID", uuid, False)])
        await interaction.followup.send(embed=embed)

    @group.command(
        name="name",
        description="Erhalte den Namen eines Minecraft-Spielers mithilfe seiner UUID",
    )
    @app_commands.describe(uuid="UUID des Spielers")
    async def cmd_uuid(self, interaction: discord.Interaction, uuid: str):
        await interaction.response.defer()

        name = MinecraftAPI.get_name(uuid)
        embed = utils.getEmbed(title="Minecraft Spieler",
                               fields=[("Name", name, False), ("UUID", uuid, False)])
        await interaction.followup.send(embed=embed)

    @group.command(
        name="playerinfo",
        description="Erhalte alle Infos über einen Minecraft-Spieler",
    )
    @app_commands.describe(name_or_uuid="Name oder UUID des Spielers")
    @app_commands.rename(name_or_uuid="player")
    async def cmd_playerinfo(self, interaction: discord.Interaction, name_or_uuid: str):
        await interaction.response.defer()

        if len(name_or_uuid) == 32:  # uuid
            uuid = name_or_uuid
        elif 1 <= len(name_or_uuid) <= 25:  # player name
            uuid = MinecraftAPI.get_uuid(name_or_uuid)
        else:
            raise ErrorMessage("Ungültiger Name oder UUID!")

        embed = utils.getEmbed(title="Minecraft Spieler")

        data = MinecraftAPI.get_profile(uuid)
        embed.add_field(name="Name", value=data["name"], inline=False)
        embed.add_field(name="UUID", value=data["id"], inline=False)
        if "legacy" in data:
            embed.add_field(name="Account-Typ", value="Legacy Account (2010-2012)")
        if "demo" in data:
            embed.add_field(name="Account-Typ", value="Demo Account")

        textures = data["textures"]
        if "SKIN" in textures:
            if "metadata" in textures["SKIN"] and "model" in textures["SKIN"]["metadata"]:
                if textures["SKIN"]["metadata"]["model"] == "slim":
                    embed.add_field(name="Skin-Typ", value="Alex (schlank)", inline=False)
                else:
                    embed.add_field(name="Skin-Typ", value="Steve (klassisch)", inline=False)

            if "url" in textures["SKIN"]:
                data["skin_url"] = textures["SKIN"]["url"]
                embed.add_field(name="Skin", value=f"[Skin]({textures['SKIN']['url']})", inline=False)
                embed.set_thumbnail(url=textures['SKIN']['url'])

        if "CAPE" in textures:
            embed.add_field(name="Skin", value=f"[Cape]({textures['CAPE']['url']})", inline=False)

        await interaction.followup.send(embed=embed)
