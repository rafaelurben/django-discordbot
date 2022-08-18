import socket
import dns.rdatatype
import dns.resolver

from discord import app_commands
from discord.ext import commands
import discord

from discordbot import utils

class Domains(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.color = 0x5a03fc

    @app_commands.command(
        name='ip',
        description="Frage die IP-Adresse ab, welche hinter einer Domain steckt.",
    )
    @app_commands.describe(domain="Domain, welche abgefragt werden soll.")
    async def cmd_ip(self, interaction: discord.Interaction, domain: str):
        try:
            ip = socket.gethostbyname(domain)
            await interaction.response.send_message(f"Die IP-Adresse von {domain} ist {ip}.")
        except socket.gaierror:
            await interaction.response.send_message(f"Die Domain '{domain}' konnte nicht gefunden werden!", ephemeral=True)

    @app_commands.command(
        name='dns',
        description="Frage bestimmte DNS-Einträge einer Domain ab.",
    )
    @app_commands.describe(
        domain="Domain, welche abgefragt werden soll.",
        typ="Typ des DNS-Eintrags, welcher abgefragt werden soll. (z.B. A, CNAME, MX, etc.)",
    )
    async def cmd_dns(self, interaction: discord.Interaction, domain: str, typ: str="A"):
        typ = typ.upper()
        try:
            result = dns.resolver.resolve(domain, typ)
            if typ == "A":
                fields=[
                    ("IP", ipval.to_text()) for ipval in result
                ]
            elif typ == "CNAME":
                fields=[
                    ("CNAME Target", cnameval.target) for cnameval in result
                ]
            elif typ == "MX":
                fields=[
                    ("MX Record", mxdata.exchange) for mxdata in result
                ]
            else:
                fields=[
                    ("Eintrag", str(data)) for data in result
                ]
            emb = utils.getEmbed(
                title=utils.CHECK+"DNS-Info",
                description=f"DNS-Einträge des Typs '{typ}' für '{domain}'!",
                inline=False,
                fields=fields
            )
            await interaction.response.send_message(embed=emb)
        except dns.resolver.NXDOMAIN:
            await interaction.response.send_message(
                f"Die Domain '{domain}' konnte nicht gefunden werden!", ephemeral=True)
        except dns.resolver.NoAnswer:
            await interaction.response.send_message(
                f"Für die Domain '{domain}' konnten keine DNS-Einträge des Typs '{typ}' gefunden werden!", ephemeral=True)
        except dns.rdatatype.UnknownRdatatype:
            await interaction.response.send_message(
                f"Unbekannter DNS-Record Typ: {typ}", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Domains(bot))
