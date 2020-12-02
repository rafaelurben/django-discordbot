from discord.ext import commands
from discord import utils
import typing
import socket
import dns

#from discordbot.config import 
from discordbot.errors import ErrorMessage

class Domains(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.color = 0x5a03fc

    @commands.command(
        brief="Erhalte die IP einer Domain",
        description="Frage die IP-Adresse ab, welche hinter einer Domain steckt.",
        aliases=["ip"],
        help="",
        usage="<Domain>"
        )
    async def getip(self, ctx, domain:str):
        try:
            ip = socket.gethostbyname(domain)
            await ctx.sendEmbed(
                title="IP-Info",
                description=f"Die IP hinter '{domain}' lautet '{ip}'!",
            )
        except socket.gaierror:
            raise ErrorMessage(f"Die Domain '{domain}' konnte nicht gefunden werden!")

    @commands.command(
        brief="Frage DNS-Einträge ab",
        description="Frage bestimmte DNS-Einträge einer Domain ab.",
        aliases=["getdns"],
        help="",
        usage="<Domain> <Typ (CNAME, A, MX)>"
    )
    async def dns(self, ctx, domain: str, typ: str):
        typ = typ.upper()
        try:
            result = dns.resolver.query(domain, typ)
            if typ == "A":
                await ctx.sendEmbed(
                    title="DNS-Info",
                    description=f"DNS-Einträge des Typs A für '{domain}'!",
                    inline=False,
                    fields=[
                        ("IP", ipval.to_text()) for ipval in result
                    ]
                )
            elif typ == "CNAME":
                await ctx.sendEmbed(
                    title="DNS-Info",
                    description=f"DNS-Einträge des Typs CNAME für '{domain}'!",
                    inline=False,
                    fields=[
                        ("CNAME Target", cnameval.target) for cnameval in result
                    ]
                )
            elif typ == "MX":
                await ctx.sendEmbed(
                    title="DNS-Info",
                    description=f"DNS-Einträge des Typs MX für '{domain}'!",
                    inline=False,
                    fields=[
                        ("MX Record", mxdata.exchange) for mxdata in result
                    ]
                )
            else:
                await ctx.sendEmbed(
                    title="DNS-Info",
                    description=f"DNS-Einträge des Typs '{typ}' für '{domain}'!",
                    inline=False,
                    fields=[
                        ("Eintrag", str(data)) for data in result
                    ]
                )
        except dns.resolver.NXDOMAIN:
            raise ErrorMessage(
                f"Die Domain '{domain}' konnte nicht gefunden werden!")
        except dns.resolver.NoAnswer:
            raise ErrorMessage(
                f"Für die Domain '{domain}' konnten keine DNS-Einträge des Typs '{typ}' gefunden werden!")
        except dns.rdatatype.UnknownRdatatype:
            raise ErrorMessage(
                f"Unbekannter DNS-Record Typ: {typ}")

def setup(bot):
    bot.add_cog(Domains(bot))
