
import discord
from discord.ext import commands
import json
import datetime
from discord.commands import slash_command, Option
import datetime
import json
import os
import asyncio

class ConfirmationView(discord.ui.View):
    def __init__(self, action_type, target, moderator):
        super().__init__(timeout=60)
        self.action_type = action_type
        self.target = target
        self.moderator = moderator
        self.confirmed = False

    @discord.ui.button(label="✅ Confirm", style=discord.ButtonStyle.success)
    async def confirm(self, button: discord.ui.Button, interaction: discord.Interaction):
        if interaction.user != self.moderator:
            await interaction.response.send_message("❌ Only the moderator can confirm this action!", ephemeral=True)
            return
        
        self.confirmed = True
        self.stop()
        
        embed = discord.Embed(
            title="✅ Action Confirmed",
            description=f"{self.action_type} action against {self.target.mention} will proceed.",
            color=0x00FF00
        )
        await interaction.response.edit_message(embed=embed, view=None)

    @discord.ui.button(label="❌ Cancel", style=discord.ButtonStyle.danger)
    async def cancel(self, button: discord.ui.Button, interaction: discord.Interaction):
        if interaction.user != self.moderator:
            await interaction.response.send_message("❌ Only the moderator can cancel this action!", ephemeral=True)
            return
        
        self.stop()
        
        embed = discord.Embed(
            title="❌ Action Cancelled",
            description=f"{self.action_type} action against {self.target.mention} has been cancelled.",
            color=0xFF0000
        )
        await interaction.response.edit_message(embed=embed, view=None)

class ModerationActions(discord.ui.View):
    def __init__(self, member):
        super().__init__(timeout=300)
        self.member = member

    @discord.ui.button(label="⚠️ Warn", style=discord.ButtonStyle.secondary, emoji="⚠️")
    async def warn_member(self, button: discord.ui.Button, interaction: discord.Interaction):
        if not interaction.user.guild_permissions.kick_members:
            await interaction.response.send_message("❌ You don't have permission to warn members!", ephemeral=True)
            return

        # Load warnings
        warnings_file = "Cogs/Moderation/reports.json"
        try:
            with open(warnings_file, 'r') as f:
                warnings = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            warnings = {}

        guild_id = str(interaction.guild.id)
        member_id = str(self.member.id)

        if guild_id not in warnings:
            warnings[guild_id] = {}
        if member_id not in warnings[guild_id]:
            warnings[guild_id][member_id] = []

        # Add warning
        warning_data = {
            "moderator": str(interaction.user.id),
            "reason": "Quick warning via button",
            "timestamp": datetime.datetime.now().isoformat()
        }
        warnings[guild_id][member_id].append(warning_data)

        # Save warnings
        os.makedirs("Cogs/Moderation", exist_ok=True)
        with open(warnings_file, 'w') as f:
            json.dump(warnings, f, indent=2)

        embed = discord.Embed(
            title="⚠️ Warning Issued",
            description=f"{self.member.mention} has been warned by {interaction.user.mention}",
            color=0xFFA500
        )
        embed.add_field(name="Total Warnings", value=len(warnings[guild_id][member_id]), inline=True)
        embed.add_field(name="Reason", value="Quick warning via button", inline=True)
        
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="🔇 Mute", style=discord.ButtonStyle.secondary, emoji="🔇")
    async def mute_member(self, button: discord.ui.Button, interaction: discord.Interaction):
        if not interaction.user.guild_permissions.manage_roles:
            await interaction.response.send_message("❌ You don't have permission to mute members!", ephemeral=True)
            return

        muted_role = discord.utils.get(interaction.guild.roles, name="Muted")
        if not muted_role:
            await interaction.response.send_message("❌ No 'Muted' role found! Please create one first.", ephemeral=True)
            return

        if muted_role in self.member.roles:
            await interaction.response.send_message("❌ Member is already muted!", ephemeral=True)
            return

        await self.member.add_roles(muted_role)
        
        embed = discord.Embed(
            title="🔇 Member Muted",
            description=f"{self.member.mention} has been muted by {interaction.user.mention}",
            color=0xFF0000
        )
        embed.add_field(name="Duration", value="Permanent (use unmute button)", inline=True)
        
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="🔊 Unmute", style=discord.ButtonStyle.success, emoji="🔊")
    async def unmute_member(self, button: discord.ui.Button, interaction: discord.Interaction):
        if not interaction.user.guild_permissions.manage_roles:
            await interaction.response.send_message("❌ You don't have permission to unmute members!", ephemeral=True)
            return

        muted_role = discord.utils.get(interaction.guild.roles, name="Muted")
        if not muted_role or muted_role not in self.member.roles:
            await interaction.response.send_message("❌ Member is not muted!", ephemeral=True)
            return

        await self.member.remove_roles(muted_role)
        
        embed = discord.Embed(
            title="🔊 Member Unmuted",
            description=f"{self.member.mention} has been unmuted by {interaction.user.mention}",
            color=0x00FF00
        )
        
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="⏰ Timeout", style=discord.ButtonStyle.danger, emoji="⏰")
    async def timeout_member(self, button: discord.ui.Button, interaction: discord.Interaction):
        if not interaction.user.guild_permissions.moderate_members:
            await interaction.response.send_message("❌ You don't have permission to timeout members!", ephemeral=True)
            return

        if self.member.is_timed_out():
            await interaction.response.send_message("❌ Member is already timed out!", ephemeral=True)
            return

        # Default 10 minute timeout
        timeout_until = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=10)
        
        try:
            await self.member.timeout(timeout_until, reason=f"Timed out by {interaction.user} via quick action")
            
            embed = discord.Embed(
                title="⏰ Member Timed Out",
                description=f"{self.member.mention} has been timed out for 10 minutes by {interaction.user.mention}",
                color=0xFF0000
            )
            embed.add_field(name="Duration", value="10 minutes", inline=True)
            
            await interaction.response.edit_message(embed=embed, view=self)
            
        except Exception as e:
            await interaction.response.send_message(f"❌ Could not timeout member: {str(e)}", ephemeral=True)

    @discord.ui.button(label="🔨 Ban", style=discord.ButtonStyle.danger, emoji="🔨")
    async def ban_member(self, button: discord.ui.Button, interaction: discord.Interaction):
        if not interaction.user.guild_permissions.ban_members:
            await interaction.response.send_message("❌ You don't have permission to ban members!", ephemeral=True)
            return

        if self.member.top_role >= interaction.user.top_role and interaction.user != interaction.guild.owner:
            await interaction.response.send_message("❌ You cannot ban someone with a role equal to or higher than yours!", ephemeral=True)
            return

        # Create confirmation for ban
        embed = discord.Embed(
            title="🔨 Confirm Ban",
            description=f"Are you sure you want to ban {self.member.mention}?",
            color=0xFFA500
        )
        embed.add_field(name="⚠️ Warning", value="This action is permanent! Use /unban to reverse.", inline=False)

        view = ConfirmationView("Ban", self.member, interaction.user)
        await interaction.response.edit_message(embed=embed, view=view)
        
        await view.wait()
        
        if view.confirmed:
            try:
                await self.member.ban(reason=f"Banned by {interaction.user} via quick action")
                
                embed = discord.Embed(
                    title="🔨 Member Banned",
                    description=f"{self.member.mention} has been banned by {interaction.user.mention}",
                    color=0x00FF00
                )
                
                await interaction.edit_original_response(embed=embed, view=None)
                
            except Exception as e:
                embed = discord.Embed(
                    title="❌ Ban Failed",
                    description=f"Could not ban {self.member.mention}\n\nError: {str(e)}",
                    color=0xFF0000
                )
                await interaction.edit_original_response(embed=embed, view=None)

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @slash_command(description="🛡️ Quick moderation panel for a member")
    async def modpanel(self, ctx, member: Option(discord.Member, "Member to moderate")):
        """Interactive moderation panel"""
        if not ctx.author.guild_permissions.kick_members:
            embed = discord.Embed(
                title="❌ Permission Denied",
                description="You don't have permission to use moderation commands!",
                color=0xFF0000
            )
            await ctx.respond(embed=embed, ephemeral=True)
            return

        embed = discord.Embed(
            title="🛡️ Moderation Panel",
            description=f"**Target:** {member.mention}\n**Moderator:** {ctx.author.mention}",
            color=0x3498DB
        )
        
        embed.add_field(
            name="👤 Member Info",
            value=f"**ID:** {member.id}\n**Joined:** {member.joined_at.strftime('%Y-%m-%d')}\n**Roles:** {len(member.roles)-1}",
            inline=True
        )
        
        embed.add_field(
            name="📱 Quick Actions",
            value="Use the buttons below for quick moderation actions",
            inline=True
        )
        
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_footer(text="🛡️ Mobile optimized moderation • Quick and secure")

        view = ModerationActions(member)
        await ctx.respond(embed=embed, view=view)

    @slash_command(description="🧹 Clear messages with confirmation")
    async def clear(self, ctx, amount: Option(int, "Number of messages to delete (1-100)", min_value=1, max_value=100)):
        """Clear messages with interactive confirmation"""
        if not ctx.author.guild_permissions.manage_messages:
            embed = discord.Embed(
                title="❌ Permission Denied",
                description="You don't have permission to manage messages!",
                color=0xFF0000
            )
            await ctx.respond(embed=embed, ephemeral=True)
            return

        embed = discord.Embed(
            title="🧹 Confirm Message Deletion",
            description=f"Are you sure you want to delete **{amount}** messages from {ctx.channel.mention}?",
            color=0xFFA500
        )
        embed.add_field(name="⚠️ Warning", value="This action cannot be undone!", inline=False)

        view = ConfirmationView("Clear messages", ctx.channel, ctx.author)
        await ctx.respond(embed=embed, view=view)
        
        await view.wait()
        
        if view.confirmed:
            deleted = await ctx.channel.purge(limit=amount + 1)  # +1 to include the command message
            
            embed = discord.Embed(
                title="🧹 Messages Cleared",
                description=f"Successfully deleted **{len(deleted)-1}** messages from {ctx.channel.mention}",
                color=0x00FF00
            )
            embed.set_footer(text="🧹 Channel cleaned successfully")
            
            # Send temporary message that deletes itself
            message = await ctx.followup.send(embed=embed)
            await asyncio.sleep(5)
            try:
                await message.delete()
            except:
                pass

    @slash_command(description="👢 Kick member with confirmation")
    async def kick(self, ctx, member: Option(discord.Member, "Member to kick"), reason: Option(str, "Reason for kick", required=False, default="No reason provided")):
        """Kick member with interactive confirmation"""
        if not ctx.author.guild_permissions.kick_members:
            embed = discord.Embed(
                title="❌ Permission Denied",
                description="You don't have permission to kick members!",
                color=0xFF0000
            )
            await ctx.respond(embed=embed, ephemeral=True)
            return

        if member.top_role >= ctx.author.top_role and ctx.author != ctx.guild.owner:
            embed = discord.Embed(
                title="❌ Cannot Kick",
                description="You cannot kick someone with a role equal to or higher than yours!",
                color=0xFF0000
            )
            await ctx.respond(embed=embed, ephemeral=True)
            return

        embed = discord.Embed(
            title="👢 Confirm Kick",
            description=f"Are you sure you want to kick {member.mention}?",
            color=0xFFA500
        )
        embed.add_field(name="Reason", value=reason, inline=False)
        embed.add_field(name="⚠️ Warning", value="They can rejoin with a new invite!", inline=False)

        view = ConfirmationView("Kick", member, ctx.author)
        await ctx.respond(embed=embed, view=view)
        
        await view.wait()
        
        if view.confirmed:
            try:
                await member.kick(reason=f"Kicked by {ctx.author} - {reason}")
                
                embed = discord.Embed(
                    title="👢 Member Kicked",
                    description=f"{member.mention} has been kicked from the server",
                    color=0x00FF00
                )
                embed.add_field(name="Moderator", value=ctx.author.mention, inline=True)
                embed.add_field(name="Reason", value=reason, inline=True)
                
                await ctx.edit(embed=embed, view=None)
                
            except Exception as e:
                embed = discord.Embed(
                    title="❌ Kick Failed",
                    description=f"Could not kick {member.mention}\n\nError: {str(e)}",
                    color=0xFF0000
                )
                await ctx.edit(embed=embed, view=None)

    @slash_command(description="📊 View member warnings")
    async def warnings(self, ctx, member: Option(discord.Member, "Member to check warnings for", required=False)):
        """View warnings with enhanced display"""
        target = member or ctx.author
        
        warnings_file = "Cogs/Moderation/reports.json"
        try:
            with open(warnings_file, 'r') as f:
                warnings = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            warnings = {}

        guild_id = str(ctx.guild.id)
        member_id = str(target.id)

        if guild_id not in warnings or member_id not in warnings[guild_id]:
            embed = discord.Embed(
                title="📊 No Warnings",
                description=f"{target.mention} has no warnings on record",
                color=0x00FF00
            )
            embed.set_thumbnail(url=target.display_avatar.url)
            await ctx.respond(embed=embed)
            return

        member_warnings = warnings[guild_id][member_id]
        
        embed = discord.Embed(
            title="📊 Warning History",
            description=f"**Member:** {target.mention}\n**Total Warnings:** {len(member_warnings)}",
            color=0xFFA500 if len(member_warnings) < 3 else 0xFF0000
        )
        
        # Show recent warnings
        recent_warnings = member_warnings[-5:]  # Last 5 warnings
        for i, warning in enumerate(reversed(recent_warnings), 1):
            moderator = self.bot.get_user(int(warning['moderator']))
            mod_name = moderator.name if moderator else "Unknown"
            timestamp = datetime.datetime.fromisoformat(warning['timestamp'])
            
            embed.add_field(
                name=f"⚠️ Warning #{len(member_warnings) - i + 1}",
                value=f"**Moderator:** {mod_name}\n**Reason:** {warning['reason']}\n**Date:** {timestamp.strftime('%Y-%m-%d %H:%M')}",
                inline=False
            )
        
        if len(member_warnings) > 5:
            embed.add_field(
                name="📝 Note",
                value=f"Showing 5 most recent warnings out of {len(member_warnings)} total",
                inline=False
            )
        
        embed.set_thumbnail(url=target.display_avatar.url)
        embed.set_footer(text="📊 Warning system • Keep your server safe")
        
        await ctx.respond(embed=embed)

    @slash_command(description="⏰ Timeout member for specified duration")
    async def timeout(self, ctx, member: Option(discord.Member, "Member to timeout"), minutes: Option(int, "Duration in minutes (1-40320)", min_value=1, max_value=40320), reason: Option(str, "Reason for timeout", required=False, default="No reason provided")):
        """Timeout member with interactive confirmation"""
        if not ctx.author.guild_permissions.moderate_members:
            embed = discord.Embed(
                title="❌ Permission Denied",
                description="You don't have permission to timeout members!",
                color=0xFF0000
            )
            await ctx.respond(embed=embed, ephemeral=True)
            return

        if member.top_role >= ctx.author.top_role and ctx.author != ctx.guild.owner:
            embed = discord.Embed(
                title="❌ Cannot Timeout",
                description="You cannot timeout someone with a role equal to or higher than yours!",
                color=0xFF0000
            )
            await ctx.respond(embed=embed, ephemeral=True)
            return

        if member.is_timed_out():
            embed = discord.Embed(
                title="❌ Already Timed Out",
                description=f"{member.mention} is already timed out!",
                color=0xFF0000
            )
            await ctx.respond(embed=embed, ephemeral=True)
            return

        # Calculate timeout duration
        timeout_until = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=minutes)
        
        embed = discord.Embed(
            title="⏰ Confirm Timeout",
            description=f"Are you sure you want to timeout {member.mention}?",
            color=0xFFA500
        )
        embed.add_field(name="Duration", value=f"{minutes} minutes", inline=True)
        embed.add_field(name="Until", value=timeout_until.strftime('%Y-%m-%d %H:%M UTC'), inline=True)
        embed.add_field(name="Reason", value=reason, inline=False)

        view = ConfirmationView("Timeout", member, ctx.author)
        await ctx.respond(embed=embed, view=view)
        
        await view.wait()
        
        if view.confirmed:
            try:
                await member.timeout(timeout_until, reason=f"Timed out by {ctx.author} - {reason}")
                
                embed = discord.Embed(
                    title="⏰ Member Timed Out",
                    description=f"{member.mention} has been timed out",
                    color=0x00FF00
                )
                embed.add_field(name="Moderator", value=ctx.author.mention, inline=True)
                embed.add_field(name="Duration", value=f"{minutes} minutes", inline=True)
                embed.add_field(name="Reason", value=reason, inline=False)
                
                await ctx.edit(embed=embed, view=None)
                
            except Exception as e:
                embed = discord.Embed(
                    title="❌ Timeout Failed",
                    description=f"Could not timeout {member.mention}\n\nError: {str(e)}",
                    color=0xFF0000
                )
                await ctx.edit(embed=embed, view=None)

    @slash_command(description="🔓 Remove timeout from member")
    async def untimeout(self, ctx, member: Option(discord.Member, "Member to remove timeout from"), reason: Option(str, "Reason for removing timeout", required=False, default="No reason provided")):
        """Remove timeout from member"""
        if not ctx.author.guild_permissions.moderate_members:
            embed = discord.Embed(
                title="❌ Permission Denied",
                description="You don't have permission to manage timeouts!",
                color=0xFF0000
            )
            await ctx.respond(embed=embed, ephemeral=True)
            return

        if not member.is_timed_out():
            embed = discord.Embed(
                title="❌ Not Timed Out",
                description=f"{member.mention} is not currently timed out!",
                color=0xFF0000
            )
            await ctx.respond(embed=embed, ephemeral=True)
            return

        try:
            await member.timeout(None, reason=f"Timeout removed by {ctx.author} - {reason}")
            
            embed = discord.Embed(
                title="🔓 Timeout Removed",
                description=f"Timeout has been removed from {member.mention}",
                color=0x00FF00
            )
            embed.add_field(name="Moderator", value=ctx.author.mention, inline=True)
            embed.add_field(name="Reason", value=reason, inline=True)
            
            await ctx.respond(embed=embed)
            
        except Exception as e:
            embed = discord.Embed(
                title="❌ Untimeout Failed",
                description=f"Could not remove timeout from {member.mention}\n\nError: {str(e)}",
                color=0xFF0000
            )
            await ctx.respond(embed=embed, ephemeral=True)

    @slash_command(description="🔨 Ban member permanently")
    async def ban(self, ctx, member: Option(discord.Member, "Member to ban"), reason: Option(str, "Reason for ban", required=False, default="No reason provided"), delete_messages: Option(int, "Delete messages from last X days (0-7)", min_value=0, max_value=7, required=False, default=0)):
        """Ban member with interactive confirmation"""
        if not ctx.author.guild_permissions.ban_members:
            embed = discord.Embed(
                title="❌ Permission Denied",
                description="You don't have permission to ban members!",
                color=0xFF0000
            )
            await ctx.respond(embed=embed, ephemeral=True)
            return

        if member.top_role >= ctx.author.top_role and ctx.author != ctx.guild.owner:
            embed = discord.Embed(
                title="❌ Cannot Ban",
                description="You cannot ban someone with a role equal to or higher than yours!",
                color=0xFF0000
            )
            await ctx.respond(embed=embed, ephemeral=True)
            return

        embed = discord.Embed(
            title="🔨 Confirm Ban",
            description=f"Are you sure you want to ban {member.mention}?",
            color=0xFFA500
        )
        embed.add_field(name="Reason", value=reason, inline=False)
        embed.add_field(name="Delete Messages", value=f"Last {delete_messages} days" if delete_messages > 0 else "None", inline=True)
        embed.add_field(name="⚠️ Warning", value="This is permanent! Use /unban to reverse.", inline=False)

        view = ConfirmationView("Ban", member, ctx.author)
        await ctx.respond(embed=embed, view=view)
        
        await view.wait()
        
        if view.confirmed:
            try:
                await member.ban(reason=f"Banned by {ctx.author} - {reason}", delete_message_days=delete_messages)
                
                embed = discord.Embed(
                    title="🔨 Member Banned",
                    description=f"{member.mention} has been banned from the server",
                    color=0x00FF00
                )
                embed.add_field(name="Moderator", value=ctx.author.mention, inline=True)
                embed.add_field(name="Reason", value=reason, inline=True)
                embed.add_field(name="Messages Deleted", value=f"Last {delete_messages} days" if delete_messages > 0 else "None", inline=True)
                
                await ctx.edit(embed=embed, view=None)
                
            except Exception as e:
                embed = discord.Embed(
                    title="❌ Ban Failed",
                    description=f"Could not ban {member.mention}\n\nError: {str(e)}",
                    color=0xFF0000
                )
                await ctx.edit(embed=embed, view=None)

    @slash_command(description="🔓 Unban user by ID")
    async def unban(self, ctx, user_id: Option(str, "User ID to unban"), reason: Option(str, "Reason for unban", required=False, default="No reason provided")):
        """Unban user by ID"""
        if not ctx.author.guild_permissions.ban_members:
            embed = discord.Embed(
                title="❌ Permission Denied",
                description="You don't have permission to unban members!",
                color=0xFF0000
            )
            await ctx.respond(embed=embed, ephemeral=True)
            return

        try:
            user_id = int(user_id)
        except ValueError:
            embed = discord.Embed(
                title="❌ Invalid User ID",
                description="Please provide a valid user ID (numbers only)!",
                color=0xFF0000
            )
            await ctx.respond(embed=embed, ephemeral=True)
            return

        try:
            user = await self.bot.fetch_user(user_id)
            await ctx.guild.unban(user, reason=f"Unbanned by {ctx.author} - {reason}")
            
            embed = discord.Embed(
                title="🔓 User Unbanned",
                description=f"{user.mention} (`{user.id}`) has been unbanned",
                color=0x00FF00
            )
            embed.add_field(name="Moderator", value=ctx.author.mention, inline=True)
            embed.add_field(name="Reason", value=reason, inline=True)
            embed.set_thumbnail(url=user.display_avatar.url)
            
            await ctx.respond(embed=embed)
            
        except discord.NotFound:
            embed = discord.Embed(
                title="❌ User Not Found",
                description="User not found or not banned!",
                color=0xFF0000
            )
            await ctx.respond(embed=embed, ephemeral=True)
        except Exception as e:
            embed = discord.Embed(
                title="❌ Unban Failed",
                description=f"Could not unban user\n\nError: {str(e)}",
                color=0xFF0000
            )
            await ctx.respond(embed=embed, ephemeral=True)

    @slash_command(description="⚠️ Issue warning to member")
    async def warn(self, ctx, member: Option(discord.Member, "Member to warn"), reason: Option(str, "Reason for warning")):
        """Issue warning to member"""
        if not ctx.author.guild_permissions.kick_members:
            embed = discord.Embed(
                title="❌ Permission Denied",
                description="You don't have permission to warn members!",
                color=0xFF0000
            )
            await ctx.respond(embed=embed, ephemeral=True)
            return

        # Load warnings
        warnings_file = "Cogs/Moderation/reports.json"
        try:
            with open(warnings_file, 'r') as f:
                warnings = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            warnings = {}

        guild_id = str(ctx.guild.id)
        member_id = str(member.id)

        if guild_id not in warnings:
            warnings[guild_id] = {}
        if member_id not in warnings[guild_id]:
            warnings[guild_id][member_id] = []

        # Add warning
        warning_data = {
            "moderator": str(ctx.author.id),
            "reason": reason,
            "timestamp": datetime.datetime.now().isoformat()
        }
        warnings[guild_id][member_id].append(warning_data)

        # Save warnings
        os.makedirs("Cogs/Moderation", exist_ok=True)
        with open(warnings_file, 'w') as f:
            json.dump(warnings, f, indent=2)

        embed = discord.Embed(
            title="⚠️ Warning Issued",
            description=f"{member.mention} has been warned",
            color=0xFFA500
        )
        embed.add_field(name="Moderator", value=ctx.author.mention, inline=True)
        embed.add_field(name="Total Warnings", value=len(warnings[guild_id][member_id]), inline=True)
        embed.add_field(name="Reason", value=reason, inline=False)
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_footer(text="⚠️ Warning system • Keep track of member behavior")
        
        await ctx.respond(embed=embed)

    @slash_command(description="🐌 Set slowmode for channel")
    async def slowmode(self, ctx, seconds: Option(int, "Slowmode delay in seconds (0-21600)", min_value=0, max_value=21600), channel: Option(discord.TextChannel, "Channel to apply slowmode to", required=False)):
        """Set slowmode for channel"""
        if not ctx.author.guild_permissions.manage_channels:
            embed = discord.Embed(
                title="❌ Permission Denied",
                description="You don't have permission to manage channels!",
                color=0xFF0000
            )
            await ctx.respond(embed=embed, ephemeral=True)
            return

        target_channel = channel or ctx.channel

        try:
            await target_channel.edit(slowmode_delay=seconds)
            
            if seconds == 0:
                embed = discord.Embed(
                    title="🚀 Slowmode Disabled",
                    description=f"Slowmode has been disabled in {target_channel.mention}",
                    color=0x00FF00
                )
            else:
                embed = discord.Embed(
                    title="🐌 Slowmode Enabled",
                    description=f"Slowmode set to **{seconds} seconds** in {target_channel.mention}",
                    color=0x00FF00
                )
                
            embed.add_field(name="Moderator", value=ctx.author.mention, inline=True)
            embed.add_field(name="Channel", value=target_channel.mention, inline=True)
            
            await ctx.respond(embed=embed)
            
        except Exception as e:
            embed = discord.Embed(
                title="❌ Slowmode Failed",
                description=f"Could not set slowmode\n\nError: {str(e)}",
                color=0xFF0000
            )
            await ctx.respond(embed=embed, ephemeral=True)

    @slash_command(description="📋 View banned users")
    async def banlist(self, ctx):
        """View list of banned users"""
        if not ctx.author.guild_permissions.ban_members:
            embed = discord.Embed(
                title="❌ Permission Denied",
                description="You don't have permission to view banned members!",
                color=0xFF0000
            )
            await ctx.respond(embed=embed, ephemeral=True)
            return

        try:
            banned_users = []
            async for ban_entry in ctx.guild.bans():
                banned_users.append(ban_entry)

            if not banned_users:
                embed = discord.Embed(
                    title="📋 No Banned Users",
                    description="There are no banned users in this server",
                    color=0x00FF00
                )
                await ctx.respond(embed=embed)
                return

            embed = discord.Embed(
                title="📋 Banned Users",
                description=f"Total banned users: **{len(banned_users)}**",
                color=0xFF0000
            )

            # Show first 10 banned users
            for i, ban_entry in enumerate(banned_users[:10]):
                user = ban_entry.user
                reason = ban_entry.reason or "No reason provided"
                embed.add_field(
                    name=f"🔨 {user.name}#{user.discriminator}",
                    value=f"**ID:** {user.id}\n**Reason:** {reason[:100]}{'...' if len(reason) > 100 else ''}",
                    inline=False
                )

            if len(banned_users) > 10:
                embed.add_field(
                    name="📝 Note",
                    value=f"Showing 10 out of {len(banned_users)} banned users",
                    inline=False
                )

            embed.set_footer(text="📋 Use /unban with user ID to unban")
            
            await ctx.respond(embed=embed)
            
        except Exception as e:
            embed = discord.Embed(
                title="❌ Failed to Load Ban List",
                description=f"Could not retrieve ban list\n\nError: {str(e)}",
                color=0xFF0000
            )
            await ctx.respond(embed=embed, ephemeral=True)

def setup(bot):
    bot.add_cog(Moderation(bot))
    print("Enhanced Moderation cog loaded with interactive controls")
