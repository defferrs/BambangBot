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
        await ctx.defer()
        
        embed = discord.Embed(
            title="🔍 Hasil Pencarian Google", 
            description=f"**Pencarian:** {query}", 
            color=discord.Color.blue()
        )
        
        try:
            results = []
            # Use simple search without advanced parameters
            search_results = search(query, num=5, stop=5, pause=2)
            
            for result in search_results:
                results.append(str(result))
                if len(results) >= 5:
                    break

            if not results:
                embed.add_field(
                    name="❌ Tidak Ada Hasil", 
                    value="Tidak ada hasil ditemukan untuk pencarian ini.", 
                    inline=False
                )
            else:
                for i, result in enumerate(results, 1):
                    # Truncate long URLs for better display
                    result_str = str(result)
                    display_url = result_str if len(result_str) <= 100 else result_str[:97] + "..."
                    embed.add_field(
                        name=f"🔗 Hasil {i}", 
                        value=f"[Klik untuk membuka]({result_str})\n`{display_url}`", 
                        inline=False
                    )
                    
        except Exception as e:
            print(f"Search error: {e}")  # Log error to console
            embed.add_field(
                name="⚠️ Error", 
                value=f"Terjadi kesalahan saat mencari:\n```{str(e)}```", 
                inline=False
            )
            embed.add_field(
                name="💡 Saran", 
                value="• Coba kata kunci yang berbeda\n• Periksa koneksi internet\n• Tunggu beberapa saat sebelum mencoba lagi", 
                inline=False
            )
        
        embed.set_footer(text="Powered by Google Search")
        await ctx.followup.send(embed=embed)



def setup(bot):
    bot.add_cog(Search(bot))
    print("Search cog loaded")
    