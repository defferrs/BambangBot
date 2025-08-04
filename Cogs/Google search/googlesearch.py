from googlesearch import search
import discord
from discord.ext import commands
from discord.commands import Option  #Importing the packages
import datetime
from discord.commands import slash_command

class Search(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @slash_command(description="Cari informasi di Google")
    async def search(self, ctx, query: Option(str, "Kata kunci pencarian")):
        msg = await ctx.respond(f"Mencari informasi...🔍")
        embed = discord.Embed(title=f"Hasil Pencarian Google", description=f"Pencarian: {query}", color=discord.Color.blue())
        for j in search(query, num=5, stop=5, pause=2):
            embed.add_field(name="Hasil:", value=j, inline=False)
        await msg.edit(embed=embed)



def setup(bot):
    bot.add_cog(Search(bot))
    print("Search cog loaded")
    