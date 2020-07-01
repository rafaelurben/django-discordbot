from discord.ext import commands
from discord import Embed, Message, Color
import random

par = "//"
opt = "/!/"

class EmbedGenerator(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.color = 0x34b7eb

    @commands.has_permissions(manage_messages = True)
    @commands.bot_has_permissions(manage_messages = True)
    @commands.command(
        name='createembed',
        brief='Erstelle einen Embed',
        description='Erstelle einen Embed im Chat!',
        aliases=["cemb","embedcreate"],
        help="Benutze /createembed für Erklärungen.",
        usage="<Titel> [Argumente]"
    )
    async def createembed(self, ctx):
        text = ctx.getargs()
        if not text:
            await ctx.sendEmbed(title="Embed-Creator", description=f"""
Verwendung des Chat-Embed-Generators:
```/createembed <Titel>
[Beschreibung]
[Parameter1]
[Parameter2]
[...]
```
Parameter brauchen je eine Zeile und beginnen immer mit `{par}`.
Optionen werden immer mit `{opt}` getrennt.

Verfügbare Parameter:""", color=self.color, inline=False, fields=[
        ("Feld (bis zu 25)",f"{par}field{opt}<Titel>{opt}<Inhalt>{opt}[Inline]"),
        ("Footer",          f"{par}footer{opt}<Titel>{opt}[Bild-URL]"),
        ("Author",          f"{par}author{opt}<Name>{opt}[Link]"),
        ("Thumbnail",       f"{par}thumbnail{opt}<Bild-URL>"),
        ("Color",           f"{par}color{opt}<RED>{opt}<GREEN>{opt}<BLUE>")
        ])
        else:
            lines = text.split("\n")
            data = {
                "title": lines.pop(0),
                "description": "",
                "color": self.color,
                "footertext": "",
                "footerurl": "",
                "authorname": "",
                "authorurl": "",
                "fields": [],
                "thumbnailurl": "",
                "timestamp": False
            }

            for line in lines:
                if len(line) >= 4 and line.startswith(par):
                    line = line[2::]
                    options = line.split(opt)
                    command = options.pop(0).lower().strip()
                    if command in ["field","f","field"] and len(options) >= 2:
                        data["fields"].append((options[0],options[1]) if (len(options) < 3 or not (options[2].lower() in ["f","false","no"])) else (options[0],options[1],False))
                    elif command in ["footer","foot"] and len(options) >= 1:
                        data["footertext"] = options[0]
                        data["footerurl"] = options[1] if len(options) > 1 else ""
                    elif command in ["author"] and len(options) >= 1:
                        data["authorname"] = options[0]
                        data["authorurl"] = options[1] if len(options) > 1 else ""
                    elif command in ["thumbnailurl", "thumbnail", "thumb"] and len(options) >= 1:
                        data["thumbnailurl"] = options[0]
                    elif command in ["color", "c"] and len(options) >= 3:
                        try:
                            data["color"] = Color.from_rgb(int(options[0]),int(options[1]),int(options[2]))
                        except ValueError:
                            pass
                else:
                    data["description"] += "\n"+line

            await ctx.sendEmbed(**data)

    @commands.command(
        name='getembed',
        brief='Erhalte einen Embed',
        description='Erhalte den Command, um einen bestehenden Embed zu erstellen.',
        aliases=["gemb","getemb"],
        help="Benutze /getembed <NachrichtenID>",
        usage="<NachrichtenID>"
    )
    async def getembed(self, ctx, msg:Message):
        if msg.embeds:
            emb = msg.embeds[0]
            text = "/createembed "+emb.title
            if emb.description:
                text += f"\n{emb.description}"
            if emb.footer:
                text += f"\n{par}footer{opt}{emb.footer.text}{(opt+emb.footer.icon_url) if emb.footer.icon_url else ''}"
            if emb.thumbnail:
                text += f"\n{par}thumbnail{opt}{emb.thumbnail.url}"
            if emb.author:
                text += f"\n{par}author{opt}{emb.author.name}{(opt+emb.author.url) if emb.author.url else ''}"
            if emb.fields:
                for field in emb.fields:
                    text += f"\n{par}field{opt}{field.name}{opt}{field.value}{(opt+'False') if not field.inline else ''}"
            if emb.color:
                text += f"\n{par}color{opt}{str(emb.color.r)}{opt}{str(emb.color.g)}{opt}{str(emb.color.b)}"
            await ctx.sendEmbed(title="Embed Command", color=self.color, description=text)
        else:
            raise commands.BadArgument("Diese Nachricht hat kein Embed!")

def setup(bot):
    bot.add_cog(EmbedGenerator(bot))
