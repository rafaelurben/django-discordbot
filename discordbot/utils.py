import discord

CHECK = "\N{WHITE HEAVY CHECK MARK} "
CROSS = "\N{CROSS MARK} "
STOP = "\N{OCTAGONAL SIGN} "

def chunks(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i:i + n]

def getEmbed(author=None, title:str="", description:str="", color:int=0x000000, fields:list=[], inline=True, thumbnailurl:str=None, authorurl:str="", authorname:str=None, footertext:str="Angefordert von USER", footerurl:str="AVATARURL", timestamp=False):
    emb = discord.Embed(title=title[:256], description=description[:2048], color=color)
    if author is not None:
        emb.set_footer(text=footertext.replace("USER", str(author.name+"#"+author.discriminator))[:2048], icon_url=footerurl.replace("AVATARURL", str(author.avatar)))
    if timestamp:
        emb.timestamp = discord.utils.utcnow() if timestamp is True else timestamp
    for field in fields[:25]:
        emb.add_field(name=field[0][:256], value=(field[1][:1018]+" [...]" if len(field[1]) > 1024 else field[1]), inline=bool(field[2] if len(field) > 2 else inline))
    if thumbnailurl:
        emb.set_thumbnail(url=thumbnailurl.strip())
    if authorname:
        if authorurl and ("https://" in authorurl or "http://" in authorurl):
            emb.set_author(name=authorname[:256], url=authorurl.strip())
        else:
            emb.set_author(name=authorname[:256])
    return emb

async def sendEmbed(receiver, title: str, *args, message: str = "", description: str = "", fields: list = list(), **kwargs):
    if len(description) > 2048:
        desc = list(chunks(description, 2042))
        for i in range(len(desc)):
            if i == 0:
                await receiver.send(message, embed=getEmbed(f"{title} ({i+1}/{len(desc)})", *args, description=desc[i]+" [...]", fields=fields, **kwargs))
            elif i == len(desc)-1:
                return await receiver.send(embed=getEmbed(f"{title} ({i+1}/{len(desc)})", *args, description=desc[i], **kwargs))
            else:
                await receiver.send(embed=getEmbed(f"{title} ({i+1}/{len(desc)})", *args, description=desc[i]+" [...]", **kwargs))
    elif len(fields) > 25:
        flds = list(chunks(fields, 25))
        for i in range(len(flds)):
            if i == 0:
                await receiver.send(message, embed=getEmbed(f"{title} ({i+1}/{len(flds)})", *args, description=description, fields=flds[i], **kwargs))
            elif i == len(flds)-1:
                return await receiver.send(embed=getEmbed(f"{title} ({i+1}/{len(flds)})", *args, fields=flds[i], **kwargs))
            else:
                await receiver.send(embed=getEmbed(f"{title} ({i+1}/{len(flds)})", *args, fields=flds[i], **kwargs))
    else:
        return await receiver.send(message, embed=getEmbed(title=title, *args, description=description, fields=fields, **kwargs))
