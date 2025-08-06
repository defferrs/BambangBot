
import discord
from discord.ext import commands
from discord import app_commands

class CategorySelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(
                label="🛡️ Moderation",
                description="Server moderation commands",
                emoji="🛡️",
                value="moderation"
            ),
            discord.SelectOption(
                label="🎵 Music",
                description="Music player commands",
                emoji="🎵",
                value="music"
            ),
            discord.SelectOption(
                label="👤 Role Management",
                description="Role and reaction role commands",
                emoji="👤",
                value="role"
            ),
            discord.SelectOption(
                label="🔍 Search",
                description="Google search commands",
                emoji="🔍",
                value="search"
            ),
            discord.SelectOption(
                label="⚙️ Server Settings",
                description="Server configuration commands",
                emoji="⚙️",
                value="server"
            )
        ]
        super().__init__(placeholder="🎯 Select a category to explore...", options=options, min_values=1, max_values=1)

    async def callback(self, interaction: discord.Interaction):
        category = self.values[0]
        
        if category == "moderation":
            embed = self.create_moderation_embed()
        elif category == "music":
            embed = self.create_music_embed()
        elif category == "role":
            embed = self.create_role_embed()
        elif category == "search":
            embed = self.create_search_embed()
        elif category == "server":
            embed = self.create_server_embed()
        
        view = CategoryView()
        await interaction.response.edit_message(embed=embed, view=view)

    def create_moderation_embed(self):
        embed = discord.Embed(
            title="🛡️ Moderation Commands",
            description="Powerful moderation tools to keep your server safe and organized",
            color=0xFF4B4B
        )
        
        commands_data = [
            ("🧹 /clear", "Bulk delete messages", "amount (1-100)"),
            ("👢 /kick", "Remove member from server", "member, reason (optional)"),
            ("🔨 /ban", "Permanently ban member", "member, reason (optional)"),
            ("🔓 /unban", "Unban member by ID", "member_id"),
            ("🔇 /mute", "Mute member in server", "member, reason (optional)"),
            ("🔊 /unmute", "Unmute member", "member"),
            ("⏰ /timeout", "Timeout member", "member, minutes (1-40320)"),
            ("⚠️ /warn", "Issue warning to member", "member, reason"),
            ("📋 /warnings", "View member warnings", "member (optional)")
        ]
        
        for emoji_cmd, desc, params in commands_data:
            embed.add_field(
                name=emoji_cmd,
                value=f"**Function:** {desc}\n**Parameters:** {params}",
                inline=True
            )
        
        embed.set_footer(text="🛡️ Requires appropriate permissions • Mobile optimized", icon_url="https://cdn.discordapp.com/emojis/852564304993501244.png")
        return embed

    def create_music_embed(self):
        embed = discord.Embed(
            title="🎵 Music Commands",
            description="High-quality music streaming from YouTube with queue management",
            color=0x1DB954
        )
        
        commands_data = [
            ("▶️ /play", "Play music from YouTube", "query (song name or URL)"),
            ("⏹️ /stop", "Stop music and clear queue", "None"),
            ("⏭️ /skip", "Skip to next song", "None"),
            ("⏸️ /pause", "Pause current song", "None"),
            ("▶️ /resume", "Resume paused song", "None"),
            ("📝 /queue", "Show music queue", "None"),
            ("🔀 /shuffle", "Shuffle queue order", "None"),
            ("🗑️ /remove", "Remove song from queue", "position (1-∞)")
        ]
        
        for emoji_cmd, desc, params in commands_data:
            embed.add_field(
                name=emoji_cmd,
                value=f"**Function:** {desc}\n**Parameters:** {params}",
                inline=True
            )
        
        embed.set_footer(text="🎵 Join a voice channel first • High quality audio", icon_url="https://cdn.discordapp.com/emojis/852564304993501244.png")
        return embed

    def create_role_embed(self):
        embed = discord.Embed(
            title="👤 Role Management",
            description="Advanced role management with reaction roles and automation",
            color=0x9B59B6
        )
        
        commands_data = [
            ("➕ /addrole", "Add role to member", "member, role"),
            ("➖ /removerole", "Remove role from member", "member, role"),
            ("🎭 /add_reaction_role", "Create reaction role", "role, channel, emoji"),
            ("🗑️ /remove_reaction_role", "Delete reaction role", "role"),
            ("📋 /list_reaction_roles", "List all reaction roles", "None")
        ]
        
        for emoji_cmd, desc, params in commands_data:
            embed.add_field(
                name=emoji_cmd,
                value=f"**Function:** {desc}\n**Parameters:** {params}",
                inline=True
            )
        
        embed.set_footer(text="👤 Bot must have Manage Roles permission", icon_url="https://cdn.discordapp.com/emojis/852564304993501244.png")
        return embed

    def create_search_embed(self):
        embed = discord.Embed(
            title="🔍 Search Commands",
            description="Instant Google search results with smart formatting",
            color=0xF39C12
        )
        
        embed.add_field(
            name="🔍 /search",
            value="**Function:** Search Google for information\n**Parameters:** query (search terms)\n**Results:** Top 5 results with descriptions",
            inline=False
        )
        
        embed.add_field(
            name="✨ Features",
            value="• Smart result filtering\n• Mobile-friendly formatting\n• Instant results\n• Safe search enabled",
            inline=True
        )
        
        embed.set_footer(text="🔍 Powered by Google Search API", icon_url="https://cdn.discordapp.com/emojis/852564304993501244.png")
        return embed

    def create_server_embed(self):
        embed = discord.Embed(
            title="⚙️ Server Settings",
            description="Comprehensive server management and configuration tools",
            color=0xE67E22
        )
        
        commands_data = [
            ("👥 /member_count", "Show server member count", "None"),
            ("👋 /setup_goodbye", "Configure goodbye messages", "enabled, channel, message"),
            ("🔄 /sync_commands", "Sync slash commands", "None (Admin only)")
        ]
        
        for emoji_cmd, desc, params in commands_data:
            embed.add_field(
                name=emoji_cmd,
                value=f"**Function:** {desc}\n**Parameters:** {params}",
                inline=True
            )
        
        embed.add_field(
            name="🤖 Auto Features",
            value="• Welcome DM for new members\n• Join/leave logging\n• Auto-settings per server\n• Mobile notifications",
            inline=False
        )
        
        embed.set_footer(text="⚙️ Settings saved automatically per server", icon_url="https://cdn.discordapp.com/emojis/852564304993501244.png")
        return embed

class CategoryView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=300)
        self.add_item(CategorySelect())

    @discord.ui.button(label="🏠 Main Menu", style=discord.ButtonStyle.secondary, emoji="🏠")
    async def main_menu(self, button: discord.ui.Button, interaction: discord.Interaction):
        embed = discord.Embed(
            title="🤖 All-in-One Discord Bot",
            description="**Your complete server management solution**\n\n✨ Select a category below to explore available commands",
            color=0x00D4FF
        )
        
        embed.add_field(
            name="🌟 Features",
            value="```\n🛡️ Advanced Moderation\n🎵 High-Quality Music\n👤 Smart Role Management\n🔍 Instant Search\n⚙️ Server Automation```",
            inline=True
        )
        
        embed.add_field(
            name="📱 Mobile Optimized",
            value="```\n✅ Touch-friendly buttons\n✅ Responsive layouts\n✅ Quick interactions\n✅ Smooth performance```",
            inline=True
        )
        
        embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/123456789/bot-icon.png")
        embed.set_footer(text="🚀 Powered by advanced AI • Optimized for mobile", icon_url="https://cdn.discordapp.com/emojis/852564304993501244.png")
        
        view = CategoryView()
        await interaction.response.edit_message(embed=embed, view=view)

    @discord.ui.button(label="📊 Bot Stats", style=discord.ButtonStyle.success, emoji="📊")
    async def bot_stats(self, button: discord.ui.Button, interaction: discord.Interaction):
        bot = interaction.client
        
        embed = discord.Embed(
            title="📊 Bot Statistics",
            description="Real-time performance metrics",
            color=0x00FF88
        )
        
        embed.add_field(name="🏠 Servers", value=f"```{len(bot.guilds)}```", inline=True)
        embed.add_field(name="👥 Users", value=f"```{len(bot.users)}```", inline=True)
        embed.add_field(name="🔗 Latency", value=f"```{round(bot.latency * 1000)}ms```", inline=True)
        embed.add_field(name="⚡ Commands", value="```50+ Commands```", inline=True)
        embed.add_field(name="🎵 Music Quality", value="```320kbps```", inline=True)
        embed.add_field(name="📱 Mobile Ready", value="```100%```", inline=True)
        
        embed.set_footer(text="📊 Updated in real-time", icon_url="https://cdn.discordapp.com/emojis/852564304993501244.png")
        
        view = CategoryView()
        await interaction.response.edit_message(embed=embed, view=view)

    @discord.ui.button(label="🆘 Support", style=discord.ButtonStyle.danger, emoji="🆘")
    async def support(self, button: discord.ui.Button, interaction: discord.Interaction):
        embed = discord.Embed(
            title="🆘 Need Help?",
            description="Get support and learn more about the bot",
            color=0xFF3366
        )
        
        embed.add_field(
            name="📝 Quick Tips",
            value="• Use `/help` for command categories\n• Check permissions if commands fail\n• Join voice channel for music\n• Report bugs via DM to bot owner",
            inline=False
        )
        
        embed.add_field(
            name="🔗 Useful Links",
            value="[📚 Documentation](https://example.com/docs)\n[🐛 Report Bug](https://example.com/bug)\n[💡 Suggest Feature](https://example.com/feature)",
            inline=True
        )
        
        embed.add_field(
            name="⚡ Status",
            value="🟢 **Online**\n🔄 Auto-updates\n📱 Mobile optimized",
            inline=True
        )
        
        embed.set_footer(text="🆘 Support available 24/7", icon_url="https://cdn.discordapp.com/emojis/852564304993501244.png")
        
        view = CategoryView()
        await interaction.response.edit_message(embed=embed, view=view)

class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @slash_command(description="🎯 Interactive help menu with categories and buttons")
    async def help(self, ctx):
        """Modern interactive help system with categories and buttons"""
        
        embed = discord.Embed(
            title="🤖 All-in-One Discord Bot",
            description="**Your complete server management solution**\n\n✨ Select a category below to explore available commands",
            color=0x00D4FF
        )
        
        embed.add_field(
            name="🌟 Features",
            value="```\n🛡️ Advanced Moderation\n🎵 High-Quality Music\n👤 Smart Role Management\n🔍 Instant Search\n⚙️ Server Automation```",
            inline=True
        )
        
        embed.add_field(
            name="📱 Mobile Optimized",
            value="```\n✅ Touch-friendly buttons\n✅ Responsive layouts\n✅ Quick interactions\n✅ Smooth performance```",
            inline=True
        )
        
        embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/123456789/bot-icon.png")
        embed.set_footer(text="🚀 Powered by advanced AI • Optimized for mobile", icon_url="https://cdn.discordapp.com/emojis/852564304993501244.png")
        
        view = CategoryView()
        await ctx.respond(embed=embed, view=view)

def setup(bot):
    bot.add_cog(Help(bot))
    print("Enhanced Help cog loaded with interactive UI")
