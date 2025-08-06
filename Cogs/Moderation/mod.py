
import discord
from discord.ext import commands
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

def setup(bot):
    bot.add_cog(Moderation(bot))
    print("Enhanced Moderation cog loaded with interactive controls")
