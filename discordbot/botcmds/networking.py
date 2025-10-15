import re
import socket
import typing

import discord
import dns.rdataclass
import dns.rdatatype
import dns.rdtypes
import dns.resolver
from discord import app_commands
from discord.ext import commands
from whois import whois
from whois.exceptions import PywhoisError

from discordbot import utils
from discordbot.errors import ErrorMessage, SuccessMessage

ALL_RDATA_TYPES: list[str] = [t.name for t in dns.rdatatype.RdataType]
DOMAIN_REGEX = r"^(((?!-))(xn--|_)?[a-z0-9-]{0,61}[a-z0-9]{1,1}\.)*(xn--)?([a-z0-9][a-z0-9\-]{0,60}|[a-z0-9-]{1,30}\.[a-z]{2,})$"


def ensure_valid_domain(domain_orig: str):
    domain_idna = domain_orig.encode("idna").decode("utf-8")
    if re.fullmatch(DOMAIN_REGEX, domain_idna) is None:
        raise ErrorMessage(
            "Dies sieht nicht nach einer Domain aus...",
            inline=False,
            fields=[("Domain", domain_orig), ("Domain (IDNA)", domain_idna)],
        )


class Networking(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.color = 0x5A03FC

    group = app_commands.Group(
        name="net", description="Eine Sammlung von Netzwerkfunktionen"
    )

    @group.command(
        name="ip",
        description="Frage die IP-Adresse ab, welche hinter einer Domain steckt.",
    )
    @app_commands.describe(domain="Domain, welche abgefragt werden soll.")
    @app_commands.checks.cooldown(5, 60)
    async def cmd_ip(self, interaction: discord.Interaction, domain: str):
        ensure_valid_domain(domain)

        await interaction.response.defer()
        try:
            ip = socket.gethostbyname(domain)
            raise SuccessMessage(
                f"Die IP-Adresse von [{domain}](https://{domain}) ist [{ip}](http://{ip}).",
                title=utils.CHECK + "IP-Info",
            )
        except socket.gaierror:
            raise ErrorMessage(
                f"Die Domain '{domain}' konnte nicht gefunden werden!"
            )

    @group.command(
        name="dns",
        description="Frage bestimmte DNS-Einträge einer Domain ab.",
    )
    @app_commands.describe(
        domain="Domain, welche abgefragt werden soll.",
        typ="Typ des DNS-Eintrags, welcher abgefragt werden soll. (z.B. A, CNAME, MX, etc.)",
    )
    @app_commands.checks.cooldown(3, 60)
    async def cmd_dns(
        self, interaction: discord.Interaction, domain: str, typ: str = "A"
    ):
        ensure_valid_domain(domain)

        await interaction.response.defer()
        typ = typ.upper()
        try:
            result: dns.resolver.Answer = dns.resolver.resolve(
                domain, typ, raise_on_no_answer=True
            )
            fields = []
            if typ == "A":
                val_a: dns.rdtypes.IN.A.A
                for val_a in result.rrset:
                    ip_addr = val_a.to_text()
                    fields.append(("IPv4", f"[{ip_addr}](http://{ip_addr})"))
            elif typ == "AAAA":
                val_aaaa: dns.rdtypes.IN.AAAAA.AAAAA
                for val_aaaa in result.rrset:
                    ip_addr = val_aaaa.to_text()
                    fields.append(("IPv6", f"[{ip_addr}](http://[{ip_addr}])"))
            elif typ == "CNAME":
                val_cname: dns.rdtypes.ANY.CNAME.CNAME
                for val_cname in result.rrset:
                    target = val_cname.to_text()
                    fields.append(
                        ("CNAME Target", f"[{target}](https://{target})")
                    )
            elif typ == "MX":
                val_mx: dns.rdtypes.ANY.MX.MX
                for val_mx in result.rrset:
                    fields.append(
                        (
                            "MX Record",
                            f"{val_mx.exchange} (Priorität {val_mx.preference})",
                        )
                    )
            else:
                for val in result.rrset:
                    fields.append((f"{typ}-Eintrag", str(val)))

            raise SuccessMessage(
                f"DNS-Einträge des Typs {typ} für [{domain}](https://{domain}):\n\n"
                + result.rrset.to_text()
                + "\n\nGeparst:",
                title=utils.CHECK + "DNS-Info",
                inline=False,
                fields=fields,
            )
        except dns.resolver.NXDOMAIN:
            raise ErrorMessage(
                f"Die Domain '{domain}' konnte nicht gefunden werden!"
            )
        except dns.resolver.NoAnswer:
            raise ErrorMessage(
                f"Für die Domain '{domain}' konnten keine DNS-Einträge des Typs '{typ}' gefunden werden!"
            )
        except dns.rdatatype.UnknownRdatatype:
            raise ErrorMessage(f"Unbekannter DNS-Record Typ: {typ}")

    @cmd_dns.autocomplete("typ")
    async def cmd_dns__typ_autocomplete(
        self,
        interaction: discord.Interaction,
        current: str,
    ) -> typing.List[app_commands.Choice[str]]:

        result = []
        for value in ALL_RDATA_TYPES:
            if current.lower() in value.lower():
                result.append(app_commands.Choice(name=value, value=value))
        return result[:25]

    @group.command(
        name="whois",
        description="Führe einen WHOIS-Lookup für eine Domain aus.",
    )
    @app_commands.describe(
        domain="Domain, welche abgefragt werden soll.",
    )
    @app_commands.checks.cooldown(1, 60)
    async def cmd_whois(self, interaction: discord.Interaction, domain: str):
        ensure_valid_domain(domain)

        await interaction.response.defer()

        try:
            result = whois(domain)
            if result["domain_name"] is None:
                raise ErrorMessage(
                    f"Antwort für Domain '{domain}':\n\n{result.text}"
                )
            raise SuccessMessage(
                f"Antwort für Domain '{domain}':\n\n{result.text}"
            )
        except PywhoisError as e:
            raise ErrorMessage("Fehler beim Abrufen: " + str(e))


async def setup(bot):
    await bot.add_cog(Networking(bot))
