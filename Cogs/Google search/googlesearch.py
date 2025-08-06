
import discord
from discord.ext import commands
from discord.commands import slash_command, Option
import asyncio
from googlesearch import search
import requests
from bs4 import BeautifulSoup

class Search(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @slash_command(description="🔍 Search Google for information")
    async def search(self, ctx, *, query: Option(str, "Search query")):
        """Search Google and return top 5 results with descriptions"""
        
        # Loading embed
        loading_embed = discord.Embed(
            title="🔍 Searching...",
            description=f"Looking for: **{query}**",
            color=0xFFA500
        )
        await ctx.respond(embed=loading_embed)
        
        try:
            # Get search results
            search_results = []
            
            # Use googlesearch-python to get URLs
            for url in search(query, num_results=5, lang='en'):
                try:
                    # Try to get page title and description
                    headers = {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                    }
                    
                    response = requests.get(url, headers=headers, timeout=5)
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    title = soup.find('title')
                    title = title.text.strip() if title else "No title"
                    
                    # Get meta description
                    description = soup.find('meta', attrs={'name': 'description'})
                    if description:
                        description = description.get('content', 'No description available')
                    else:
                        # Fallback to first paragraph
                        p_tag = soup.find('p')
                        description = p_tag.text[:150] + "..." if p_tag else "No description available"
                    
                    search_results.append({
                        'title': title[:100] + "..." if len(title) > 100 else title,
                        'url': url,
                        'description': description[:200] + "..." if len(description) > 200 else description
                    })
                    
                    # Add small delay to prevent rate limiting
                    await asyncio.sleep(0.5)
                    
                except Exception as e:
                    print(f"Error fetching {url}: {e}")
                    continue
            
            if not search_results:
                embed = discord.Embed(
                    title="❌ No Results Found",
                    description=f"Could not find any results for: **{query}**",
                    color=0xFF0000
                )
                await ctx.edit(embed=embed)
                return
            
            # Create results embed
            embed = discord.Embed(
                title="🔍 Search Results",
                description=f"Top results for: **{query}**",
                color=0xF39C12
            )
            
            for i, result in enumerate(search_results, 1):
                embed.add_field(
                    name=f"{i}. {result['title']}",
                    value=f"**Description:** {result['description']}\n**Link:** [🔗 Click here]({result['url']})",
                    inline=False
                )
            
            embed.set_footer(text="🔍 Powered by Google Search • Mobile optimized")
            await ctx.edit(embed=embed)
            
        except Exception as e:
            error_embed = discord.Embed(
                title="❌ Search Failed",
                description=f"An error occurred while searching: {str(e)}",
                color=0xFF0000
            )
            await ctx.edit(embed=error_embed)

def setup(bot):
    bot.add_cog(Search(bot))
    print("Google Search cog loaded")
