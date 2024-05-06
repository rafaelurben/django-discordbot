# pylint: disable=no-member

import base64
import datetime
import requests
from discord.ext import commands

from discordbot.errors import ErrorMessage


class MinecraftAPI:
    @classmethod
    def getProfile(cls, NAME: str):
        r = requests.get(
            'https://api.mojang.com/users/profiles/minecraft/' + NAME)
        if not r.status_code == 204:
            return r.json()
        else:
            raise ErrorMessage(message="Spieler wurde nicht gefunden!")

    @classmethod
    def getProfiles(cls, UUID: str):
        r = requests.get(
            'https://api.mojang.com/user/profiles/' + str(UUID) + '/names')
        if not r.status_code == 204:
            data = r.json()
            for i in data:
                if "changedToAt" in i:
                    i["changedToAt"] = datetime.datetime.fromtimestamp(
                        int(i["changedToAt"]) / 1000)
            return data
        else:
            raise ErrorMessage(message="UUID wurde nicht gefunden!")

    @classmethod
    def getSkin(cls, UUID: str):
        r = requests.get(
            'https://sessionserver.mojang.com/session/minecraft/profile/' + str(UUID))
        if not r.status_code == 204:
            data = r.json()
            if not "error" in data:
                ppty = data["properties"][0]
                base64_message = ppty["value"]
                base64_bytes = base64_message.encode('ascii')
                message_bytes = base64.b64decode(base64_bytes)
                message = message_bytes.decode('ascii')
                dictmessage = eval(message)
                if not dictmessage["textures"] == {}:
                    skinurl = dictmessage["textures"]["SKIN"]["url"]
                    data["skin"] = skinurl
                else:
                    data["skin"] = None
                data.pop("properties")
                return data
            raise ErrorMessage(
                message="Abfrage für einen Skin kann pro UUID maximal ein Mal pro Minute erfolgen!")
        raise ErrorMessage(message="UUID wurde nicht gefunden!")


class MinecraftCog(commands.Cog, name="Minecraft"):
    def __init__(self, bot):
        self.bot = bot
        self.color = 0x1f871e

    # Minecraft

    @commands.group(
        brief="Hauptcommand für alle Minecraft Befehle",
        description='Erhalte Infos über Minecraft-Spieler',
        aliases=['mc'],
        usage="<Unterbefehl> <Argument>"
    )
    async def minecraft(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send_help()

    @minecraft.command(
        name="uuid",
        brief="Erhalte die UUID eines Spielers",
        aliases=['id'],
        usage="<Spielername>",
    )
    async def minecraft_uuid(self, ctx, name):
        JSON = MinecraftAPI.getProfile(name)
        EMBED = ctx.getEmbed(title="Minecraft UUID",
                             fields=[("UUID", JSON["id"], False), ("Aktueller Name", JSON["name"], False)])
        if "legacy" in JSON:
            EMBED.add_field(name="Account", value="Alter Account")
        if "demo" in JSON:
            EMBED.add_field(name="Account", value="Demo Account")
        await ctx.send(embed=EMBED)

    @minecraft.command(
        name="names",
        brief="Erhalte alte Namen eines Spielers",
        aliases=['namen', 'name'],
        usage="<UUID>",
    )
    async def minecraft_names(self, ctx, uuid):
        if len(uuid) != 32:
            raise ErrorMessage("Eine UUID ist genau 32 Zeichen lang!")

        JSON = MinecraftAPI.getProfiles(uuid)
        EMBED = ctx.getEmbed(title="Minecraft Namen", description="Sortierung: Von neu bis alt.")
        for i in JSON[::-1]:
            if "changedToAt" in i:
                EMBED.add_field(name="Name seit " + str(i["changedToAt"]), value=i["name"], inline=False)
            else:
                EMBED.add_field(name="Ursprünglicher Name", value=i["name"], inline=False)
        await ctx.send(embed=EMBED)

    @minecraft.command(
        name="skin",
        brief="Erhalte den Skin eines Spielers",
        aliases=[],
        usage="<UUID>",
    )
    async def minecraft_skin(self, ctx, uuid):
        if len(uuid) != 32:
            raise ErrorMessage("Eine UUID ist genau 32 Zeichen lang!")

        JSON = MinecraftAPI.getSkin(uuid)
        EMBED = ctx.getEmbed(title="Minecraft Skin", fields=[("Aktueller Name", JSON["name"]), ("UUID", JSON["id"])])
        if JSON["skin"] is not None:
            EMBED.set_thumbnail(url=JSON["skin"])
        else:
            EMBED.add_field(name="Skin", value="Wurde nicht gefunden. (Steve/Alex)", inline=False)
        await ctx.send(embed=EMBED)

    @minecraft.command(
        name="player",
        brief="Erhalte alle Infos über einen Spieler",
        description="Dies ist eine Zusammenfassung von UUID, Namen und Skin",
        aliases=['spieler'],
        usage="<Spielername>",
    )
    async def minecraft_player(self, ctx, name):
        JSON = MinecraftAPI.getProfile(name)
        UUID = JSON["id"]
        EMBED = ctx.getEmbed(title="Minecraft Spieler", fields=[("UUID", UUID)], inline=False)
        if "legacy" in JSON:
            EMBED.add_field(name="Account", value="Alter Account")
        if "demo" in JSON:
            EMBED.add_field(name="Account", value="Demo Account")
        JSON2 = MinecraftAPI.getProfiles(UUID)
        for i in JSON2[::-1]:
            if "changedToAt" in i:
                EMBED.add_field(name="Name seit " + str(i["changedToAt"]), value=i["name"], inline=False)
            else:
                EMBED.add_field(name="Ursprünglicher Name", value=i["name"], inline=False)
        JSON3 = MinecraftAPI.getSkin(UUID)
        if JSON3["skin"] is not None:
            EMBED.set_thumbnail(url=JSON3["skin"])
        else:
            EMBED.add_field(name="Skin", value="Wurde nicht gefunden. (Steve/Alex)", inline=False)
        await ctx.send(embed=EMBED)
