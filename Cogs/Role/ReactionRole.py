
import discord
from discord.ext import commands
from discord.commands import slash_command
import os
import json
import asyncio


class ReactionRole(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.reaction_roles = {}
        self.load_reaction_roles()
        self.bot.loop.create_task(self.save_reaction_roles())

    async def save_reaction_roles(self):
        while True:
            try:
                with open("Cogs/Role/RoleData/reaction_roles.json", "w") as f:
                    json.dump(self.reaction_roles, f)
                await asyncio.sleep(60)
                print("Reaction roles saved")
            except Exception as e:
                print(f"Error saving reaction roles: {e}")
                await asyncio.sleep(60)

    async def check_reaction_roles(self):
        while True:
            try:
                for guild_id_str, roles in self.reaction_roles.items():
                    guild_id = int(guild_id_str)
                    for role_id_str, message_data in roles.items():
                        role_id = int(role_id_str)
                        guild = self.bot.get_guild(guild_id)
                        if guild:
                            role = guild.get_role(role_id)
                            if role and len(message_data) >= 3:
                                try:
                                    channel_id, message_id, emoji = message_data[0], message_data[1], message_data[2]
                                    channel = guild.get_channel(channel_id)
                                    if channel:
                                        message = await channel.fetch_message(message_id)
                                        if message:
                                            for reaction in message.reactions:
                                                if str(reaction.emoji) == emoji:
                                                    async for user in reaction.users():
                                                        if user != self.bot.user and role not in user.roles:
                                                            await user.add_roles(role)
                                                            print(f"Added role {role.name} to {user.name}")
                                except Exception as e:
                                    print(f"Error processing reaction role: {e}")
                                await asyncio.sleep(1)
                print("Checked reaction roles")
            except Exception as e:
                print(f"Error in check_reaction_roles: {e}")
            await asyncio.sleep(10)

    def load_reaction_roles(self):
        try:
            if os.path.exists("Cogs/Role/RoleData/reaction_roles.json"):
                with open("Cogs/Role/RoleData/reaction_roles.json", "r") as f:
                    content = f.read().strip()
                    if content:
                        self.reaction_roles = json.loads(content)
                    else:
                        self.reaction_roles = {}
                print("Reaction roles loaded")
            else:
                self.reaction_roles = {}
                print("No reaction roles file found, creating empty dict")
        except Exception as e:
            print(f"Error loading reaction roles: {e}")
            self.reaction_roles = {}
        
        self.bot.loop.create_task(self.check_reaction_roles())

    @slash_command()
    async def add_reaction_role(self, ctx, role: discord.Role, channel: discord.TextChannel, emoji: str):
        if ctx.author.guild_permissions.manage_roles:
            try:
                # Get the latest message from the channel
                async for message in channel.history(limit=1):
                    latest_message = message
                    break
                else:
                    await ctx.respond(f"No messages found in {channel.name}", ephemeral=True)
                    return
                
                guild_id_str = str(ctx.guild.id)
                role_id_str = str(role.id)
                
                if guild_id_str not in self.reaction_roles:
                    self.reaction_roles[guild_id_str] = {}
                self.reaction_roles[guild_id_str][role_id_str] = [channel.id, latest_message.id, emoji]
                
                # Add the reaction to the message
                await latest_message.add_reaction(emoji)
                
                await ctx.respond(f"Added reaction role {role.name} to the latest message in {channel.name} with emoji {emoji}", ephemeral=True)
                print(f"Added reaction role {role.name} to message {latest_message.id} in channel {channel.name} with emoji {emoji}")
            except Exception as e:
                await ctx.respond(f"Error setting up reaction role: {str(e)}", ephemeral=True)
                print(f"Error in add_reaction_role: {e}")
        else:
            await ctx.respond("You don't have permission to manage roles.", ephemeral=True)

    @slash_command()
    async def remove_reaction_role(self, ctx, role: discord.Role):
        if ctx.author.guild_permissions.manage_roles:
            guild_id_str = str(ctx.guild.id)
            role_id_str = str(role.id)
            
            if guild_id_str in self.reaction_roles:
                if role_id_str in self.reaction_roles[guild_id_str]:
                    del self.reaction_roles[guild_id_str][role_id_str]
                    await ctx.respond(f"Removed reaction role {role.name}", ephemeral=True)
                    print(f"Removed reaction role {role.name}")
                else:
                    await ctx.respond(f"Reaction role {role.name} not found", ephemeral=True)
            else:
                await ctx.respond("No reaction roles found for this guild", ephemeral=True)
        else:
            await ctx.respond("You don't have permission to manage roles.", ephemeral=True)

    @slash_command()
    async def list_reaction_roles(self, ctx):
        if ctx.author.guild_permissions.manage_roles:
            guild_id_str = str(ctx.guild.id)
            if guild_id_str in self.reaction_roles:
                roles = self.reaction_roles[guild_id_str]
                if roles:
                    embed = discord.Embed(title="Reaction Roles", color=discord.Color.blue())
                    for role_id_str, message_data in roles.items():
                        try:
                            role_id = int(role_id_str)
                            role = ctx.guild.get_role(role_id)
                            if role and len(message_data) >= 3:
                                channel_id, message_id, emoji = message_data[0], message_data[1], message_data[2]
                                channel = ctx.guild.get_channel(channel_id)
                                if channel:
                                    message = await channel.fetch_message(message_id)
                                    embed.add_field(name=role.name, value=f"Message: {message.jump_url}\nEmoji: {emoji}", inline=False)
                        except Exception as e:
                            print(f"Error listing reaction role: {e}")
                    await ctx.respond(embed=embed, ephemeral=True)
                    print(f"Listed reaction roles for guild {ctx.guild.name}")
                else:
                    await ctx.respond("No reaction roles found", ephemeral=True)
                    print("No reaction roles found")
            else:
                await ctx.respond("No reaction roles found for this guild", ephemeral=True)
        else:
            await ctx.respond("You don't have permission to manage roles.", ephemeral=True)

def setup(bot):
    bot.add_cog(ReactionRole(bot))
    print("ReactionRole cog loaded")
