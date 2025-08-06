from googlesearch import search
import discord
from discord.ext import commands
from discord import app_commands
import datetime

class Search(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="search", description="Cari informasi di Google")
    @app_commands.describe(query="Kata kunci pencarian")
    async def search(self, interaction: discord.Interaction, *, query: str):
        await interaction.response.defer()
        
        embed = discord.Embed(
            title="🔍 Hasil Pencarian Google", 
            description=f"**Pencarian:** {query}", 
            color=discord.Color.blue()
        )
        
        try:
            results = []
            # Use most basic search function
            search_results = search(query)
            
            count = 0
            for result in search_results:
                if count >= 5:
                    break
                results.append(str(result))
                count += 1

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
        await interaction.followup.send(embed=embed)



def setup(bot):
    bot.add_cog(Search(bot))
    print("Search cog loaded")
    