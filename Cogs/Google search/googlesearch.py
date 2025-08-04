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
        try:
            results = []
            for j in search(query, lang='id', safe='off', num=5, pause=2):
                results.append(j)
                if len(results) >= 5:
                    break

            if not results:
                embed.add_field(name="Hasil:", value="Tidak ada hasil ditemukan", inline=False)
            else:
                for result in results:
                    embed.add_field(name="Hasil:", value=result, inline=False)
        except Exception as e:
            embed.add_field(name="Error:", value=f"Terjadi kesalahan: {str(e)}", inline=False)



def setup(bot):
    bot.add_cog(Search(bot))
    print("Search cog loaded")