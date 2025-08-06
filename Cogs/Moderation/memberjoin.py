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
                "goodbye_channel": None,
                "welcome_gif": None,
                "goodbye_gif": None,
                "welcome_embed_color": "#00D4FF"
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

                    # Parse color from settings or use default
                    color_hex = guild_settings.get("welcome_embed_color", "#00D4FF")
                    try:
                        color = discord.Color(int(color_hex.replace("#", ""), 16))
                    except:
                        color = discord.Color.green()

                    embed = discord.Embed(
                        title="🎉 Selamat Datang!",
                        description=welcome_msg,
                        color=color
                    )

                    # Set the user's avatar as the thumbnail
                    embed.set_thumbnail(url=member.display_avatar.url)

                    # Add GIF if configured
                    if guild_settings.get("welcome_gif"):
                        embed.set_image(url=guild_settings["welcome_gif"])

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
                    title="👋 Selamat Tinggal!",
                    description=goodbye_msg,
                    color=discord.Color.red()
                )

                # Add GIF if configured
                if guild_settings.get("goodbye_gif"):
                    embed.set_image(url=guild_settings["goodbye_gif"])

                # Set the user's avatar as the thumbnail with fallback
                try:
                    embed.set_thumbnail(url=member.display_avatar.url)
                except:
                    embed.set_thumbnail(url=member.default_avatar.url)
                await goodbye_channel.send(embed=embed)
            except Exception as e:
                print(f"Error sending goodbye message: {e}")

    @slash_command(name="setup_welcome_advanced")
    @commands.has_permissions(manage_guild=True)
    async def setup_welcome_advanced(self, ctx):
        """🎨 Advanced welcome setup with interactive buttons and GIF support"""
        guild_settings = self.get_guild_settings(ctx.guild.id)

        class WelcomeSetupView(discord.ui.View):
            def __init__(self, cog, guild_settings):
                super().__init__(timeout=300)
                self.cog = cog
                self.guild_settings = guild_settings

            @discord.ui.button(label="📝 Set Message", style=discord.ButtonStyle.primary, emoji="📝")
            async def set_message(self, button: discord.ui.Button, interaction: discord.Interaction):
                class MessageModal(discord.ui.Modal):
                    def __init__(self, guild_settings, cog):
                        super().__init__(title="Set Welcome Message")
                        self.guild_settings = guild_settings
                        self.cog = cog
                        self.message_input = discord.ui.InputText(
                            label="Welcome Message",
                            placeholder="Use {member} for mention, {guild} for server name",
                            value=self.guild_settings["welcome_message"],
                            style=discord.InputTextStyle.paragraph,
                            max_length=1000
                        )
                        self.add_item(self.message_input)

                    async def callback(self, interaction):
                        self.guild_settings["welcome_message"] = self.message_input.value
                        self.cog.save_settings()
                        await interaction.response.send_message("✅ Welcome message updated!", ephemeral=True)

                await interaction.response.send_modal(MessageModal(self.guild_settings, self.cog))

            @discord.ui.button(label="📺 Set Channel", style=discord.ButtonStyle.secondary, emoji="📺")
            async def set_channel(self, button: discord.ui.Button, interaction: discord.Interaction):
                class ChannelSelect(discord.ui.View):
                    def __init__(self, guild_settings, cog):
                        super().__init__(timeout=60)
                        self.guild_settings = guild_settings
                        self.cog = cog

                        select = discord.ui.Select(
                            placeholder="Choose welcome channel...",
                            options=[
                                discord.SelectOption(
                                    label=channel.name,
                                    value=str(channel.id),
                                    description=f"#{channel.name}",
                                    emoji="📺"
                                ) for channel in interaction.guild.text_channels[:25]
                            ]
                        )
                        select.callback = self.channel_callback
                        self.add_item(select)

                    async def channel_callback(self, interaction):
                        channel_id = int(interaction.data['values'][0])
                        channel = interaction.guild.get_channel(channel_id)
                        self.guild_settings["welcome_channel"] = channel_id
                        self.cog.save_settings()
                        await interaction.response.send_message(f"✅ Welcome channel set to {channel.mention}!", ephemeral=True)

                view = ChannelSelect(self.guild_settings, self.cog)
                await interaction.response.send_message("Select welcome channel:", view=view, ephemeral=True)

            @discord.ui.button(label="🎭 Set Role", style=discord.ButtonStyle.secondary, emoji="🎭")
            async def set_role(self, button: discord.ui.Button, interaction: discord.Interaction):
                class RoleSelect(discord.ui.View):
                    def __init__(self, guild_settings, cog):
                        super().__init__(timeout=60)
                        self.guild_settings = guild_settings
                        self.cog = cog

                        # Filter out @everyone and higher roles
                        assignable_roles = [
                            role for role in interaction.guild.roles
                            if role != interaction.guild.default_role and
                            role.position < interaction.guild.me.top_role.position
                        ][:25]

                        if assignable_roles:
                            select = discord.ui.Select(
                                placeholder="Choose auto-assign role...",
                                options=[
                                    discord.SelectOption(
                                        label=role.name,
                                        value=str(role.id),
                                        description=f"@{role.name}",
                                        emoji="🎭"
                                    ) for role in assignable_roles
                                ]
                            )
                            select.callback = self.role_callback
                            self.add_item(select)

                    async def role_callback(self, interaction):
                        role_id = int(interaction.data['values'][0])
                        role = interaction.guild.get_role(role_id)
                        self.guild_settings["auto_role"] = role_id
                        self.cog.save_settings()
                        await interaction.response.send_message(f"✅ Auto-assign role set to {role.mention}!", ephemeral=True)

                view = RoleSelect(self.guild_settings, self.cog)
                if not view.children:
                    await interaction.response.send_message("❌ No assignable roles found!", ephemeral=True)
                else:
                    await interaction.response.send_message("Select auto-assign role:", view=view, ephemeral=True)

            @discord.ui.button(label="🖼️ Set GIF", style=discord.ButtonStyle.secondary, emoji="🖼️")
            async def set_gif(self, button: discord.ui.Button, interaction: discord.Interaction):
                class GifModal(discord.ui.Modal):
                    def __init__(self, guild_settings, cog):
                        super().__init__(title="Set Welcome GIF")
                        self.guild_settings = guild_settings
                        self.cog = cog
                        self.gif_input = discord.ui.InputText(
                            label="GIF URL",
                            placeholder="Enter GIF URL (e.g., https://tenor.com/view/welcome.gif)",
                            value=self.guild_settings.get("welcome_gif", ""),
                            style=discord.InputTextStyle.short,
                            max_length=500,
                            required=False
                        )
                        self.add_item(self.gif_input)

                    async def callback(self, interaction):
                        gif_url = self.gif_input.value.strip()
                        if gif_url:
                            # Basic URL validation
                            if gif_url.startswith(('http://', 'https://')) and any(ext in gif_url.lower() for ext in ['.gif', '.png', '.jpg', '.jpeg', 'tenor.com', 'giphy.com']):
                                self.guild_settings["welcome_gif"] = gif_url
                                self.cog.save_settings()
                                await interaction.response.send_message("✅ Welcome GIF updated!", ephemeral=True)
                            else:
                                await interaction.response.send_message("❌ Invalid GIF URL! Please provide a valid image/GIF URL.", ephemeral=True)
                        else:
                            self.guild_settings["welcome_gif"] = None
                            self.cog.save_settings()
                            await interaction.response.send_message("✅ Welcome GIF removed!", ephemeral=True)

                await interaction.response.send_modal(GifModal(self.guild_settings, self.cog))

            @discord.ui.button(label="🎨 Set Color", style=discord.ButtonStyle.secondary, emoji="🎨")
            async def set_color(self, button: discord.ui.Button, interaction: discord.Interaction):
                class ColorModal(discord.ui.Modal):
                    def __init__(self, guild_settings, cog):
                        super().__init__(title="Set Embed Color")
                        self.guild_settings = guild_settings
                        self.cog = cog
                        self.color_input = discord.ui.InputText(
                            label="Hex Color Code",
                            placeholder="#00D4FF",
                            value=self.guild_settings.get("welcome_embed_color", "#00D4FF"),
                            style=discord.InputTextStyle.short,
                            max_length=7
                        )
                        self.add_item(self.color_input)

                    async def callback(self, interaction):
                        color_hex = self.color_input.value.strip()
                        if not color_hex.startswith("#"):
                            color_hex = "#" + color_hex

                        try:
                            # Validate hex color
                            int(color_hex[1:], 16)
                            self.guild_settings["welcome_embed_color"] = color_hex
                            self.cog.save_settings()
                            await interaction.response.send_message(f"✅ Embed color set to {color_hex}!", ephemeral=True)
                        except ValueError:
                            await interaction.response.send_message("❌ Invalid hex color! Use format: #00D4FF", ephemeral=True)

                await interaction.response.send_modal(ColorModal(self.guild_settings, self.cog))

            @discord.ui.button(label="👁️ Preview", style=discord.ButtonStyle.success, emoji="👁️")
            async def preview(self, button: discord.ui.Button, interaction: discord.Interaction):
                # Create preview embed
                welcome_msg = self.guild_settings["welcome_message"].format(
                    member=interaction.user.mention,
                    guild=interaction.guild.name
                )

                try:
                    color = discord.Color(int(self.guild_settings.get("welcome_embed_color", "#00D4FF").replace("#", ""), 16))
                except:
                    color = discord.Color.green()

                embed = discord.Embed(
                    title="🎉 Selamat Datang! (Preview)",
                    description=welcome_msg,
                    color=color
                )

                embed.set_thumbnail(url=interaction.user.display_avatar.url)

                if self.guild_settings.get("welcome_gif"):
                    embed.set_image(url=self.guild_settings["welcome_gif"])

                # Add configuration info
                channel = interaction.guild.get_channel(self.guild_settings["welcome_channel"]) if self.guild_settings["welcome_channel"] else None
                role = interaction.guild.get_role(self.guild_settings["auto_role"]) if self.guild_settings["auto_role"] else None

                embed.add_field(
                    name="📋 Current Settings",
                    value=f"**Channel:** {channel.mention if channel else 'System Channel'}\n"
                          f"**Auto Role:** {role.mention if role else 'None'}\n"
                          f"**GIF:** {'✅ Set' if self.guild_settings.get('welcome_gif') else '❌ None'}",
                    inline=False
                )

                embed.set_footer(text=f"Member #{interaction.guild.member_count} • Preview Mode")

                await interaction.response.send_message(embed=embed, ephemeral=True)

        embed = discord.Embed(
            title="🎨 Advanced Welcome Setup",
            description="**Configure your server's welcome system with stunning visuals!**\n\n"
                       "🔹 **Mobile Optimized** - Perfect for all devices\n"
                       "🔹 **GIF Support** - Add animated welcome GIFs\n"
                       "🔹 **Role Assignment** - Auto-assign roles to new members\n"
                       "🔹 **Custom Colors** - Match your server's theme",
            color=0x00D4FF
        )

        # Show current settings
        channel = ctx.guild.get_channel(guild_settings["welcome_channel"]) if guild_settings["welcome_channel"] else None
        role = ctx.guild.get_role(guild_settings["auto_role"]) if guild_settings["auto_role"] else None

        embed.add_field(
            name="📊 Current Configuration",
            value=f"**Channel:** {channel.mention if channel else 'System Channel'}\n"
                  f"**Auto Role:** {role.mention if role else 'None'}\n"
                  f"**Message:** {guild_settings['welcome_message'][:50]}...\n"
                  f"**GIF:** {'✅ Set' if guild_settings.get('welcome_gif') else '❌ None'}",
            inline=False
        )

        embed.set_footer(text="📱 Mobile-friendly interface • Touch the buttons below!")

        view = WelcomeSetupView(self, guild_settings)
        await ctx.respond(embed=embed, view=view, ephemeral=True)

    @slash_command()
    @commands.has_permissions(manage_guild=True)
    async def setup_welcome(self, ctx,
                           dm_enabled: Option(bool, "Aktifkan DM selamat datang untuk member baru", default=False),
                           channel_enabled: Option(bool, "Aktifkan pesan selamat datang di channel guild", default=True),
                           auto_nickname: Option(bool, "Aktifkan nickname otomatis", default=True),
                           role: Option(discord.Role, "Role otomatis yang akan diberikan", required=False) = None,
                           channel: Option(discord.TextChannel, "Channel guild untuk pesan selamat datang", required=False) = None,
                           welcome_message: Option(str, "Pesan selamat datang kustom (gunakan {member} dan {guild})", required=False) = None):
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
            title="📝 Basic Welcome Setup Complete",
            description="✅ Settings updated! Use `/setup_welcome_advanced` for GIF support and more options.",
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
                           enabled: Option(bool, "Aktifkan pesan perpisahan", default=True),
                           channel: Option(discord.TextChannel, "Channel guild untuk pesan perpisahan", required=False) = None,
                           goodbye_message: Option(str, "Pesan perpisahan kustom untuk channel guild (gunakan {member})", required=False) = None,
                           goodbye_gif: Option(str, "URL GIF untuk pesan perpisahan", required=False) = None):
        """Konfigurasi pesan perpisahan untuk member yang keluar di channel guild"""
        guild_settings = self.get_guild_settings(ctx.guild.id)

        guild_settings["goodbye_enabled"] = enabled
        if channel:
            guild_settings["goodbye_channel"] = channel.id
        if goodbye_message:
            guild_settings["goodbye_message"] = goodbye_message
        if goodbye_gif:
            if goodbye_gif.startswith(('http://', 'https://')) and any(ext in goodbye_gif.lower() for ext in ['.gif', '.png', '.jpg', '.jpeg', 'tenor.com', 'giphy.com']):
                guild_settings["goodbye_gif"] = goodbye_gif
            else:
                await ctx.respond("❌ Invalid GIF URL! Please provide a valid image/GIF URL.", ephemeral=True)
                return

        self.save_settings()

        embed = discord.Embed(
            title="👋 Goodbye Settings Updated",
            color=discord.Color.blue()
        )
        embed.add_field(name="Aktif", value="Ya" if enabled else "Tidak", inline=True)
        embed.add_field(name="Channel", value=channel.mention if channel else "Channel Sistem", inline=True)
        embed.add_field(name="GIF", value="✅ Set" if goodbye_gif else "❌ None", inline=True)

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
                  f"GIF: {'✅ Set' if guild_settings.get('welcome_gif') else '❌ None'}\n"
                  f"Color: {guild_settings.get('welcome_embed_color', '#00D4FF')}\n"
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
        cog_instance = self

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
                cog_instance.save_settings()

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