from . import minecraft, connect4


async def setup(bot):
    await bot.add_cog(minecraft.MinecraftCog(bot))
    await bot.add_cog(connect4.Connect4Cog(bot))
