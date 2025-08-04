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
            search_results = search(query, num_results=5, lang='id', advanced=True, sleep_interval=1)
            
            for result in search_results:
                results.append(result)
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
                    display_url = result if len(result) <= 100 else result[:97] + "..."
                    embed.add_field(
                        name=f"🔗 Hasil {i}", 
                        value=f"[Klik untuk membuka]({result})\n`{display_url}`", 
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
    