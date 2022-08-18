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
