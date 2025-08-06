
import discord
from discord.ext import commands
from discord.commands import slash_command, Option

class RoleConfirmationView(discord.ui.View):
    def __init__(self, member, role, action_type, moderator):
        super().__init__(timeout=60)
        self.member = member
        self.role = role
        self.action_type = action_type
        self.moderator = moderator
        self.confirmed = False

    @discord.ui.button(label="✅ Confirm", style=discord.ButtonStyle.success)
    async def confirm(self, button: discord.ui.Button, interaction: discord.Interaction):
        if interaction.user != self.moderator:
            await interaction.response.send_message("❌ Only the moderator can confirm this action!", ephemeral=True)
            return
        
        self.confirmed = True
        self.stop()
        
        try:
            if self.action_type == "add":
                await self.member.add_roles(self.role)
                embed = discord.Embed(
                    title="✅ Role Added",
                    description=f"Successfully added {self.role.mention} to {self.member.mention}",
                    color=0x00FF00
                )
            else:
                await self.member.remove_roles(self.role)
                embed = discord.Embed(
                    title="✅ Role Removed", 
                    description=f"Successfully removed {self.role.mention} from {self.member.mention}",
                    color=0x00FF00
                )
            
            embed.add_field(name="Moderator", value=self.moderator.mention, inline=True)
            embed.add_field(name="Member Roles", value=f"{len(self.member.roles)-1} roles", inline=True)
            embed.set_footer(text="👤 Role management completed successfully")
            
            await interaction.response.edit_message(embed=embed, view=None)
            
            # Send DM to member
            try:
                dm_embed = discord.Embed(
                    title=f"👤 Role {'Added' if self.action_type == 'add' else 'Removed'}",
                    description=f"You have been {'given' if self.action_type == 'add' else 'removed from'} the **{self.role.name}** role in **{interaction.guild.name}**",
                    color=0x00FF00
                )
                dm_embed.add_field(name="Moderator", value=self.moderator.name, inline=True)
                await self.member.send(embed=dm_embed)
            except discord.Forbidden:
                pass  # User has DMs disabled
                
        except Exception as e:
            embed = discord.Embed(
                title="❌ Role Action Failed",
                description=f"Could not {'add' if self.action_type == 'add' else 'remove'} role {self.role.mention}\n\nError: {str(e)}",
                color=0xFF0000
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
            description=f"Role {'addition' if self.action_type == 'add' else 'removal'} has been cancelled.",
            color=0xFF0000
        )
        await interaction.response.edit_message(embed=embed, view=None)

class RoleManagerView(discord.ui.View):
    def __init__(self, member):
        super().__init__(timeout=300)
        self.member = member

    @discord.ui.button(label="➕ Add Role", style=discord.ButtonStyle.success, emoji="➕")
    async def add_role_menu(self, button: discord.ui.Button, interaction: discord.Interaction):
        if not interaction.user.guild_permissions.manage_roles:
            await interaction.response.send_message("❌ You don't have permission to manage roles!", ephemeral=True)
            return

        # Create role select menu
        available_roles = [role for role in interaction.guild.roles if role != interaction.guild.default_role and role not in self.member.roles and role < interaction.user.top_role]
        
        if not available_roles:
            await interaction.response.send_message("❌ No roles available to add!", ephemeral=True)
            return

        options = []
        for role in available_roles[:25]:  # Discord limit
            options.append(discord.SelectOption(
                label=role.name,
                description=f"Color: {str(role.color)} • Members: {len(role.members)}",
                value=str(role.id),
                emoji="👤"
            ))

        select = discord.ui.Select(placeholder="Choose a role to add...", options=options)
        
        async def role_callback(select_interaction):
            role_id = int(select.values[0])
            role = interaction.guild.get_role(role_id)
            
            embed = discord.Embed(
                title="➕ Confirm Role Addition",
                description=f"Add {role.mention} to {self.member.mention}?",
                color=role.color
            )
            embed.add_field(name="Role Info", value=f"**Members:** {len(role.members)}\n**Color:** {str(role.color)}", inline=True)
            embed.set_thumbnail(url=self.member.display_avatar.url)
            
            view = RoleConfirmationView(self.member, role, "add", interaction.user)
            await select_interaction.response.edit_message(embed=embed, view=view)

        select.callback = role_callback
        view = discord.ui.View()
        view.add_item(select)
        
        embed = discord.Embed(
            title="➕ Add Role to Member",
            description=f"Select a role to add to {self.member.mention}",
            color=0x00FF00
        )
        await interaction.response.edit_message(embed=embed, view=view)

    @discord.ui.button(label="➖ Remove Role", style=discord.ButtonStyle.danger, emoji="➖")
    async def remove_role_menu(self, button: discord.ui.Button, interaction: discord.Interaction):
        if not interaction.user.guild_permissions.manage_roles:
            await interaction.response.send_message("❌ You don't have permission to manage roles!", ephemeral=True)
            return

        # Get removable roles
        removable_roles = [role for role in self.member.roles if role != interaction.guild.default_role and role < interaction.user.top_role]
        
        if not removable_roles:
            await interaction.response.send_message("❌ No roles available to remove!", ephemeral=True)
            return

        options = []
        for role in removable_roles[:25]:  # Discord limit
            options.append(discord.SelectOption(
                label=role.name,
                description=f"Color: {str(role.color)} • Members: {len(role.members)}",
                value=str(role.id),
                emoji="👤"
            ))

        select = discord.ui.Select(placeholder="Choose a role to remove...", options=options)
        
        async def role_callback(select_interaction):
            role_id = int(select.values[0])
            role = interaction.guild.get_role(role_id)
            
            embed = discord.Embed(
                title="➖ Confirm Role Removal",
                description=f"Remove {role.mention} from {self.member.mention}?",
                color=role.color
            )
            embed.add_field(name="Role Info", value=f"**Members:** {len(role.members)}\n**Color:** {str(role.color)}", inline=True)
            embed.set_thumbnail(url=self.member.display_avatar.url)
            
            view = RoleConfirmationView(self.member, role, "remove", interaction.user)
            await select_interaction.response.edit_message(embed=embed, view=view)

        select.callback = role_callback
        view = discord.ui.View()
        view.add_item(select)
        
        embed = discord.Embed(
            title="➖ Remove Role from Member",
            description=f"Select a role to remove from {self.member.mention}",
            color=0xFF0000
        )
        await interaction.response.edit_message(embed=embed, view=view)

    @discord.ui.button(label="📋 View Roles", style=discord.ButtonStyle.secondary, emoji="📋")
    async def view_roles(self, button: discord.ui.Button, interaction: discord.Interaction):
        member_roles = [role for role in self.member.roles if role != interaction.guild.default_role]
        
        embed = discord.Embed(
            title="📋 Member Roles",
            description=f"**Member:** {self.member.mention}\n**Total Roles:** {len(member_roles)}",
            color=0x3498DB
        )
        
        if member_roles:
            role_list = []
            for role in sorted(member_roles, key=lambda r: r.position, reverse=True):
                role_list.append(f"• {role.mention} ({len(role.members)} members)")
            
            # Split into chunks if too long
            role_text = "\n".join(role_list)
            if len(role_text) > 1024:
                role_text = "\n".join(role_list[:10]) + f"\n... and {len(member_roles) - 10} more roles"
            
            embed.add_field(name="Roles", value=role_text, inline=False)
        else:
            embed.add_field(name="Roles", value="No roles assigned", inline=False)
        
        embed.set_thumbnail(url=self.member.display_avatar.url)
        embed.set_footer(text="📋 Role management • Mobile optimized")
        
        await interaction.response.edit_message(embed=embed, view=self)

class AddRole(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @slash_command(description="👤 Interactive role management panel")
    async def rolemanager(self, ctx, member: Option(discord.Member, "Member to manage roles for")):
        """Interactive role management with modern UI"""
        if not ctx.author.guild_permissions.manage_roles:
            embed = discord.Embed(
                title="❌ Permission Denied",
                description="You don't have permission to manage roles!",
                color=0xFF0000
            )
            await ctx.respond(embed=embed, ephemeral=True)
            return

        embed = discord.Embed(
            title="👤 Role Management Panel",
            description=f"**Target:** {member.mention}\n**Manager:** {ctx.author.mention}",
            color=0x9B59B6
        )
        
        member_roles = [role for role in member.roles if role != ctx.guild.default_role]
        embed.add_field(
            name="📊 Current Status",
            value=f"**Current Roles:** {len(member_roles)}\n**Joined:** {member.joined_at.strftime('%Y-%m-%d')}\n**Top Role:** {member.top_role.mention if member.top_role != ctx.guild.default_role else 'None'}",
            inline=True
        )
        
        embed.add_field(
            name="🛠️ Available Actions",
            value="Use the buttons below to manage this member's roles",
            inline=True
        )
        
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_footer(text="👤 Interactive role management • Mobile friendly")

        view = RoleManagerView(member)
        await ctx.respond(embed=embed, view=view)

    @slash_command(description="➕ Add role to member (classic command)")
    async def addrole(self, ctx, member: Option(discord.Member, "Member to give role to"), role: Option(discord.Role, "Role to give")):
        """Add role with confirmation dialog"""
        if not ctx.author.guild_permissions.manage_roles:
            embed = discord.Embed(
                title="❌ Permission Denied",
                description="You don't have permission to manage roles!",
                color=0xFF0000
            )
            await ctx.respond(embed=embed, ephemeral=True)
            return

        if role >= ctx.author.top_role and ctx.author != ctx.guild.owner:
            embed = discord.Embed(
                title="❌ Cannot Add Role",
                description="You cannot assign a role equal to or higher than your highest role!",
                color=0xFF0000
            )
            await ctx.respond(embed=embed, ephemeral=True)
            return

        if role in member.roles:
            embed = discord.Embed(
                title="❌ Role Already Assigned",
                description=f"{member.mention} already has the {role.mention} role!",
                color=0xFF0000
            )
            await ctx.respond(embed=embed)
            return

        embed = discord.Embed(
            title="➕ Confirm Role Addition",
            description=f"Add {role.mention} to {member.mention}?",
            color=role.color
        )
        embed.add_field(name="Role Info", value=f"**Members:** {len(role.members)}\n**Color:** {str(role.color)}", inline=True)
        embed.set_thumbnail(url=member.display_avatar.url)

        view = RoleConfirmationView(member, role, "add", ctx.author)
        await ctx.respond(embed=embed, view=view)

def setup(bot):
    bot.add_cog(AddRole(bot))
    print("Enhanced AddRole cog loaded with interactive controls")
