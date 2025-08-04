
import discord
from discord.ext import commands
from discord.commands import slash_command, Option
import json
import os

class memberjoin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.settings = {}
        self.load_settings()

    def load_settings(self):
        """Load settings from JSON file"""
        try:
            os.makedirs("Cogs/Moderation/data", exist_ok=True)
            if os.path.exists("Cogs/Moderation/data/memberjoin_settings.json"):
                with open("Cogs/Moderation/data/memberjoin_settings.json", "r") as f:
                    self.settings = json.load(f)
            else:
                self.settings = {}
        except Exception as e:
            print(f"Error loading member join settings: {e}")
            self.settings = {}

    def save_settings(self):
        """Save settings to JSON file"""
        try:
            os.makedirs("Cogs/Moderation/data", exist_ok=True)
            with open("Cogs/Moderation/data/memberjoin_settings.json", "w") as f:
                json.dump(self.settings, f, indent=2)
        except Exception as e:
            print(f"Error saving member join settings: {e}")

    def get_guild_settings(self, guild_id):
        """Get settings for a specific guild"""
        guild_id_str = str(guild_id)
        if guild_id_str not in self.settings:
            self.settings[guild_id_str] = {
                "welcome_dm_enabled": False,
                "welcome_channel_enabled": True,
                "goodbye_enabled": True,
                "auto_role": None,
                "auto_nickname": True,
                "welcome_message": "Selamat datang di server ini, {member}!",
                "goodbye_message": "Selamat tinggal {member}! Kami akan merindukanmu!",
                "welcome_channel": None,
                "goodbye_channel": None
            }
        return self.settings[guild_id_str]

    @commands.Cog.listener()
    async def on_member_join(self, member):
        """Handle member join events"""
        guild_settings = self.get_guild_settings(member.guild.id)
        
        print(f'{member} joined {member.guild.name}!')
        
        # Send welcome DM if enabled
        if guild_settings["welcome_dm_enabled"]:
            try:
                welcome_msg = guild_settings["welcome_message"].format(
                    member=member.name,
                    guild=member.guild.name
                )
                await member.send(welcome_msg)
            except discord.Forbidden:
                print(f"Could not send DM to {member}")

        # Add auto role if configured
        if guild_settings["auto_role"]:
            try:
                role = member.guild.get_role(guild_settings["auto_role"])
                if role:
                    await member.add_roles(role, reason="Auto role on join")
                    print(f"Added role {role.name} to {member}")
                else:
                    print(f"Auto role {guild_settings['auto_role']} not found")
            except discord.Forbidden:
                print(f"Missing permissions to add role to {member}")
            except Exception as e:
                print(f"Error adding role to {member}: {e}")

        # Set auto nickname if enabled
        if guild_settings["auto_nickname"]:
            try:
                await member.edit(nick=f'[member] {member.name}')
            except discord.Forbidden:
                print(f"Could not set nickname for {member}")

        # Send welcome message to channel if enabled
        if guild_settings["welcome_channel_enabled"]:
            welcome_channel_id = guild_settings["welcome_channel"]
            welcome_channel = None
            
            if welcome_channel_id:
                welcome_channel = member.guild.get_channel(welcome_channel_id)
            
            if not welcome_channel:
                welcome_channel = member.guild.system_channel

            if welcome_channel:
                try:
                    # Use the customizable welcome message from settings
                    welcome_msg = guild_settings["welcome_message"].format(
                        member=member.mention,
                        guild=member.guild.name
                    )
                    
                    embed = discord.Embed(
                        title="Selamat Datang!",
                        description=welcome_msg,
                        color=discord.Color.green()
                    )
                    
                    # Set the user's avatar as the thumbnail
                    embed.set_thumbnail(url=member.display_avatar.url)
                    
                    # Add rules field if rules channel exists
                    if member.guild.rules_channel:
                        embed.add_field(
                            name="📋 Peraturan",
                            value=f'Silakan baca peraturan di {member.guild.rules_channel.mention} terlebih dahulu',
                            inline=False
                        )
                    
                    embed.add_field(
                        name="🎉 Selamat bersenang-senang!",
                        value='Nikmati waktu Anda di server ini!',
                        inline=False
                    )
                    
                    embed.set_footer(text=f"Member #{member.guild.member_count}")
                    await welcome_channel.send(embed=embed)
                except Exception as e:
                    print(f"Error sending welcome message: {e}")

    

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        """Handle member leave events"""
        guild_settings = self.get_guild_settings(member.guild.id)
        
        if not guild_settings["goodbye_enabled"]:
            return

        print(f'{member} left {member.guild.name}')
        
        # Send goodbye message to channel
        goodbye_channel_id = guild_settings["goodbye_channel"]
        goodbye_channel = None
        
        if goodbye_channel_id:
            goodbye_channel = member.guild.get_channel(goodbye_channel_id)
        
        if not goodbye_channel:
            goodbye_channel = member.guild.system_channel

        if goodbye_channel:
            try:
                goodbye_msg = guild_settings["goodbye_message"].format(
                    member=member.mention
                )
                embed = discord.Embed(
                    title="Selamat Tinggal!",
                    description=goodbye_msg,
                    color=discord.Color.red()
                )
                await goodbye_channel.send(embed=embed)
            except Exception as e:
                print(f"Error sending goodbye message: {e}")

    @slash_command()
    @commands.has_permissions(manage_guild=True)
    async def setup_welcome(self, ctx, 
                           dm_enabled: Option(bool, "Aktifkan DM selamat datang untuk member baru", default=False),
                           channel_enabled: Option(bool, "Aktifkan pesan selamat datang di channel guild", default=True),
                           role: discord.Role = Option(None, "Role otomatis yang akan diberikan", required=False),
                           channel: discord.TextChannel = Option(None, "Channel guild untuk pesan selamat datang", required=False),
                           auto_nickname: Option(bool, "Aktifkan nickname otomatis", default=True),
                           welcome_message: str = Option(None, "Pesan selamat datang kustom (gunakan {member} dan {guild})", required=False)):
        """Konfigurasi lengkap pengaturan selamat datang untuk member baru"""
        guild_settings = self.get_guild_settings(ctx.guild.id)
        
        guild_settings["welcome_dm_enabled"] = dm_enabled
        guild_settings["welcome_channel_enabled"] = channel_enabled
        if role:
            guild_settings["auto_role"] = role.id
        if channel:
            guild_settings["welcome_channel"] = channel.id
        guild_settings["auto_nickname"] = auto_nickname
        if welcome_message:
            guild_settings["welcome_message"] = welcome_message
        
        self.save_settings()
        
        embed = discord.Embed(
            title="Pengaturan Selamat Datang Diperbarui",
            color=discord.Color.blue()
        )
        embed.add_field(name="DM Aktif", value="Ya" if dm_enabled else "Tidak", inline=True)
        embed.add_field(name="Channel Aktif", value="Ya" if channel_enabled else "Tidak", inline=True)
        embed.add_field(name="Role Otomatis", value=role.mention if role else "Tidak ada", inline=True)
        embed.add_field(name="Channel", value=channel.mention if channel else "Channel Sistem", inline=True)
        embed.add_field(name="Nickname Otomatis", value="Ya" if auto_nickname else "Tidak", inline=True)
        
        await ctx.respond(embed=embed, ephemeral=True)

    @slash_command()
    @commands.has_permissions(manage_guild=True)
    async def setup_goodbye(self, ctx,
                           enabled: Option(bool, "Aktifkan pesan perpisahan"),
                           channel: discord.TextChannel = Option(None, "Channel guild untuk pesan perpisahan", required=False),
                           goodbye_message: str = Option(None, "Pesan perpisahan kustom untuk channel guild (gunakan {member})", required=False)):
        """Konfigurasi pesan perpisahan untuk member yang keluar di channel guild"""
        guild_settings = self.get_guild_settings(ctx.guild.id)
        
        guild_settings["goodbye_enabled"] = enabled
        if channel:
            guild_settings["goodbye_channel"] = channel.id
        if goodbye_message:
            guild_settings["goodbye_message"] = goodbye_message
        
        self.save_settings()
        
        embed = discord.Embed(
            title="Pengaturan Perpisahan Diperbarui",
            color=discord.Color.blue()
        )
        embed.add_field(name="Aktif", value="Ya" if enabled else "Tidak", inline=True)
        embed.add_field(name="Channel", value=channel.mention if channel else "Channel Sistem", inline=True)
        
        await ctx.respond(embed=embed, ephemeral=True)

    @slash_command(name="member_count")
    async def membercount(self, ctx):
        """Dapatkan jumlah member saat ini"""
        await ctx.respond(f"Server ini memiliki {ctx.guild.member_count} member")

    @slash_command(name="member_settings")
    @commands.has_permissions(manage_guild=True)
    async def view_settings(self, ctx):
        """Lihat pengaturan join/leave member saat ini"""
        guild_settings = self.get_guild_settings(ctx.guild.id)
        
        embed = discord.Embed(
            title="Pengaturan Join/Leave Member",
            color=discord.Color.blue()
        )
        
        # Welcome settings
        welcome_channel = ctx.guild.get_channel(guild_settings["welcome_channel"]) if guild_settings["welcome_channel"] else None
        auto_role = ctx.guild.get_role(guild_settings["auto_role"]) if guild_settings["auto_role"] else None
        
        embed.add_field(
            name="Pengaturan Selamat Datang",
            value=f"DM Aktif: {'Ya' if guild_settings['welcome_dm_enabled'] else 'Tidak'}\n"
                  f"Channel Aktif: {'Ya' if guild_settings['welcome_channel_enabled'] else 'Tidak'}\n"
                  f"Role Otomatis: {auto_role.mention if auto_role else 'Tidak ada'}\n"
                  f"Channel: {welcome_channel.mention if welcome_channel else 'Channel Sistem'}\n"
                  f"Nickname Otomatis: {'Ya' if guild_settings['auto_nickname'] else 'Tidak'}\n"
                  f"Pesan: {guild_settings['welcome_message'][:100]}...",
            inline=False
        )
        
        # Goodbye settings
        goodbye_channel = ctx.guild.get_channel(guild_settings["goodbye_channel"]) if guild_settings["goodbye_channel"] else None
        
        embed.add_field(
            name="Pengaturan Perpisahan", 
            value=f"Aktif: {'Ya' if guild_settings['goodbye_enabled'] else 'Tidak'}\n"
                  f"Channel: {goodbye_channel.mention if goodbye_channel else 'Channel Sistem'}\n"
                  f"Pesan: {guild_settings['goodbye_message'][:100]}...",
            inline=False
        )
        
        await ctx.respond(embed=embed, ephemeral=True)

    

    @slash_command(name="edit_welcome_message")
    @commands.has_permissions(manage_guild=True)
    async def edit_welcome_message(self, ctx):
        """Edit template pesan selamat datang menggunakan modal input teks"""
        guild_settings = self.get_guild_settings(ctx.guild.id)
        
        class WelcomeMessageModal(discord.ui.Modal):
            def __init__(self):
                super().__init__(title="Edit Pesan Selamat Datang")
                
                self.message_input = discord.ui.InputText(
                    label="Pesan Selamat Datang",
                    placeholder="Masukkan pesan selamat datang Anda di sini...",
                    value=guild_settings["welcome_message"],
                    style=discord.InputTextStyle.paragraph,
                    max_length=1000
                )
                self.add_item(self.message_input)
                
                self.tips_input = discord.ui.InputText(
                    label="Tips (Hanya Baca)",
                    placeholder="Gunakan {member} untuk mention user, {guild} untuk nama server",
                    value="Gunakan {member} untuk mention user, {guild} untuk nama server",
                    style=discord.InputTextStyle.short,
                    required=False
                )
                self.add_item(self.tips_input)
            
            async def callback(self, interaction):
                new_message = self.message_input.value
                
                if not new_message.strip():
                    await interaction.response.send_message("❌ Pesan selamat datang tidak boleh kosong!", ephemeral=True)
                    return
                
                # Update the settings
                guild_settings["welcome_message"] = new_message
                self.parent.save_settings()
                
                # Show preview
                preview_message = new_message.format(
                    member="@ContohUser",
                    guild=interaction.guild.name
                )
                
                embed = discord.Embed(
                    title="✅ Pesan Selamat Datang Diperbarui!",
                    description=f"**Pratinjau:**\n{preview_message}",
                    color=discord.Color.green()
                )
                embed.add_field(
                    name="📝 Template Baru",
                    value=f"`{new_message}`",
                    inline=False
                )
                
                await interaction.response.send_message(embed=embed, ephemeral=True)
        
        modal = WelcomeMessageModal()
        modal.parent = self
        await ctx.send_modal(modal)

    @slash_command(name="sync_commands")
    @commands.has_permissions(administrator=True)
    async def sync_commands(self, ctx):
        """Sinkronisasi manual slash commands (Khusus Admin)"""
        try:
            synced = await self.bot.sync_commands()
            if synced is not None:
                await ctx.respond(f"Berhasil menyinkronkan {len(synced)} command!", ephemeral=True)
            else:
                await ctx.respond("Command berhasil disinkronkan!", ephemeral=True)
        except Exception as e:
            await ctx.respond(f"Gagal menyinkronkan command: {e}", ephemeral=True)

def setup(bot):
    bot.add_cog(memberjoin(bot))
    print('memberjoin.py loaded')
