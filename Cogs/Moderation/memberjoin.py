
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
                "welcome_enabled": True,
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
        
        if not guild_settings["welcome_enabled"]:
            return

        print(f'{member} joined {member.guild.name}!')
        
        # Send welcome DM
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

        # Send welcome message to channel
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
                    title="Welcome!",
                    description=welcome_msg,
                    color=discord.Color.green()
                )
                
                # Add rules field if rules channel exists
                if member.guild.rules_channel:
                    embed.add_field(
                        name="📋 Rules",
                        value=f'Please read the rules in {member.guild.rules_channel.mention} first',
                        inline=False
                    )
                
                embed.add_field(
                    name="🎉 Have fun!",
                    value='Enjoy your time in the server!',
                    inline=False
                )
                
                embed.set_footer(text=f"Member #{member.guild.member_count}")
                await welcome_channel.send(embed=embed)
            except Exception as e:
                print(f"Error sending welcome message: {e}")

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        """Handle message edits to update welcome messages"""
        # Only process if the message was edited by someone with manage_guild permissions
        if not after.author.guild_permissions.manage_guild:
            return
        
        # Check if this message is in a welcome channel
        guild_settings = self.get_guild_settings(after.guild.id)
        welcome_channel_id = guild_settings.get("welcome_channel")
        
        if not welcome_channel_id or after.channel.id != welcome_channel_id:
            return
        
        # Check if the bot sent this message and it's a template message
        if after.author != self.bot.user:
            return
        
        # Check if this is a template message by looking for the footer
        if not after.embeds or not after.embeds[0].footer or "editable template" not in after.embeds[0].footer.text.lower():
            return
        
        # Update the welcome message template based on the edit
        embed = after.embeds[0]
        if embed.description:
            # Replace @SampleUser with {member} placeholder for template
            import re
            new_message = embed.description
            new_message = re.sub(r'@SampleUser', '{member}', new_message)
            new_message = re.sub(r'<@!?\d+>', '{member}', new_message)
            
            if new_message != guild_settings["welcome_message"]:
                guild_settings["welcome_message"] = new_message
                self.save_settings()
                
                # Send confirmation
                try:
                    confirmation = await after.channel.send(
                        f"✅ Welcome message template updated! New members will see:\n```{new_message}```",
                        delete_after=10
                    )
                except:
                    pass

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
                    title="Goodbye!",
                    description=goodbye_msg,
                    color=discord.Color.red()
                )
                await goodbye_channel.send(embed=embed)
            except Exception as e:
                print(f"Error sending goodbye message: {e}")

    @slash_command()
    @commands.has_permissions(manage_guild=True)
    async def setup_welcome(self, ctx, 
                           enabled: Option(bool, "Enable welcome messages"),
                           role: Option(discord.Role, "Auto role to assign", required=False),
                           channel: Option(discord.TextChannel, "Guild channel for welcome messages", required=False),
                           auto_nickname: Option(bool, "Enable auto nickname", default=True),
                           welcome_message: Option(str, "Custom welcome message for guild channel (use {member} and {guild})", required=False)):
        """Configure complete welcome settings for new members (DM + Guild Channel)"""
        guild_settings = self.get_guild_settings(ctx.guild.id)
        
        guild_settings["welcome_enabled"] = enabled
        if role:
            guild_settings["auto_role"] = role.id
        if channel:
            guild_settings["welcome_channel"] = channel.id
        guild_settings["auto_nickname"] = auto_nickname
        if welcome_message:
            guild_settings["welcome_message"] = welcome_message
        
        self.save_settings()
        
        embed = discord.Embed(
            title="Welcome Settings Updated",
            color=discord.Color.blue()
        )
        embed.add_field(name="Enabled", value=enabled, inline=True)
        embed.add_field(name="Auto Role", value=role.mention if role else "None", inline=True)
        embed.add_field(name="Channel", value=channel.mention if channel else "System Channel", inline=True)
        embed.add_field(name="Auto Nickname", value=auto_nickname, inline=True)
        
        await ctx.respond(embed=embed, ephemeral=True)

    @slash_command()
    @commands.has_permissions(manage_guild=True)
    async def setup_goodbye(self, ctx,
                           enabled: Option(bool, "Enable goodbye messages"),
                           channel: Option(discord.TextChannel, "Guild channel for goodbye messages", required=False),
                           goodbye_message: Option(str, "Custom goodbye message for guild channel (use {member})", required=False)):
        """Configure goodbye messages for leaving members in guild channel"""
        guild_settings = self.get_guild_settings(ctx.guild.id)
        
        guild_settings["goodbye_enabled"] = enabled
        if channel:
            guild_settings["goodbye_channel"] = channel.id
        if goodbye_message:
            guild_settings["goodbye_message"] = goodbye_message
        
        self.save_settings()
        
        embed = discord.Embed(
            title="Goodbye Settings Updated",
            color=discord.Color.blue()
        )
        embed.add_field(name="Enabled", value=enabled, inline=True)
        embed.add_field(name="Channel", value=channel.mention if channel else "System Channel", inline=True)
        
        await ctx.respond(embed=embed, ephemeral=True)

    @slash_command(name="member_count")
    async def membercount(self, ctx):
        """Get the current member count"""
        await ctx.respond(f"This server has {ctx.guild.member_count} members")

    @slash_command(name="member_settings")
    @commands.has_permissions(manage_guild=True)
    async def view_settings(self, ctx):
        """View current member join/leave settings"""
        guild_settings = self.get_guild_settings(ctx.guild.id)
        
        embed = discord.Embed(
            title="Member Join/Leave Settings",
            color=discord.Color.blue()
        )
        
        # Welcome settings
        welcome_channel = ctx.guild.get_channel(guild_settings["welcome_channel"]) if guild_settings["welcome_channel"] else None
        auto_role = ctx.guild.get_role(guild_settings["auto_role"]) if guild_settings["auto_role"] else None
        
        embed.add_field(
            name="Welcome Settings",
            value=f"Enabled: {guild_settings['welcome_enabled']}\n"
                  f"Auto Role: {auto_role.mention if auto_role else 'None'}\n"
                  f"Channel: {welcome_channel.mention if welcome_channel else 'System Channel'}\n"
                  f"Auto Nickname: {guild_settings['auto_nickname']}\n"
                  f"Message: {guild_settings['welcome_message'][:100]}...",
            inline=False
        )
        
        # Goodbye settings
        goodbye_channel = ctx.guild.get_channel(guild_settings["goodbye_channel"]) if guild_settings["goodbye_channel"] else None
        
        embed.add_field(
            name="Goodbye Settings", 
            value=f"Enabled: {guild_settings['goodbye_enabled']}\n"
                  f"Channel: {goodbye_channel.mention if goodbye_channel else 'System Channel'}\n"
                  f"Message: {guild_settings['goodbye_message'][:100]}...",
            inline=False
        )
        
        await ctx.respond(embed=embed, ephemeral=True)

    @slash_command(name="set_welcome_channel")
    @commands.has_permissions(manage_guild=True)
    async def set_welcome_channel(self, ctx,
                                 channel: Option(discord.TextChannel, "Channel for welcome messages"),
                                 welcome_message: Option(str, "Custom welcome message for the channel (use {member} and {guild})", required=False)):
        """Set the guild channel where welcome messages will be sent"""
        guild_settings = self.get_guild_settings(ctx.guild.id)
        
        guild_settings["welcome_channel"] = channel.id
        if welcome_message:
            guild_settings["welcome_message"] = welcome_message
        
        self.save_settings()
        
        embed = discord.Embed(
            title="Welcome Channel Set",
            description=f"Welcome messages will now be sent to {channel.mention}",
            color=discord.Color.green()
        )
        if welcome_message:
            embed.add_field(name="Custom Message", value=welcome_message, inline=False)
        
        await ctx.respond(embed=embed, ephemeral=True)

    @slash_command(name="edit_welcome_template")
    @commands.has_permissions(manage_guild=True)
    async def edit_welcome_template(self, ctx):
        """Send an editable welcome message template that you can modify directly"""
        guild_settings = self.get_guild_settings(ctx.guild.id)
        
        welcome_channel_id = guild_settings["welcome_channel"]
        welcome_channel = None
        
        if welcome_channel_id:
            welcome_channel = ctx.guild.get_channel(welcome_channel_id)
        
        if not welcome_channel:
            welcome_channel = ctx.guild.system_channel
            
        if not welcome_channel:
            await ctx.respond("❌ No welcome channel configured and no system channel available!", ephemeral=True)
            return
        
        # Create a sample welcome message that can be edited
        sample_message = guild_settings["welcome_message"].format(
            member="@SampleUser",
            guild=ctx.guild.name
        )
        
        embed = discord.Embed(
            title="🎨 Welcome Template Editor",
            description=sample_message,
            color=discord.Color.blue()
        )
        embed.add_field(
            name="📝 How to Edit",
            value="1. Click the **Edit Message** button (three dots)\n"
                  "2. Modify the description text above\n"
                  "3. Keep `@SampleUser` as placeholder for new members\n"
                  "4. Changes will be saved automatically!",
            inline=False
        )
        embed.add_field(
            name="💡 Tips",
            value="• Use `{member}` in your template for member mentions\n"
                  "• Use `{guild}` for server name\n"
                  "• Current template will be used for new members",
            inline=False
        )
        embed.set_footer(text="Editable template message - Edit this directly!")
        
        try:
            template_msg = await welcome_channel.send(embed=embed)
            await ctx.respond(
                f"✅ Editable welcome template sent to {welcome_channel.mention}!\n"
                f"Edit the message description directly to update the template.",
                ephemeral=True
            )
        except Exception as e:
            await ctx.respond(f"❌ Error sending template: {e}", ephemeral=True)

    @slash_command(name="sync_commands")
    @commands.has_permissions(administrator=True)
    async def sync_commands(self, ctx):
        """Manually sync slash commands (Admin only)"""
        try:
            synced = await self.bot.sync_commands()
            if synced is not None:
                await ctx.respond(f"Synced {len(synced)} commands!", ephemeral=True)
            else:
                await ctx.respond("Commands synced successfully!", ephemeral=True)
        except Exception as e:
            await ctx.respond(f"Failed to sync commands: {e}", ephemeral=True)

def setup(bot):
    bot.add_cog(memberjoin(bot))
    print('memberjoin.py loaded')
