
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
            with open("Cogs/Role/RoleData/reaction_roles.json", "w") as f:
                json.dump(self.reaction_roles, f)
            await asyncio.sleep(60)
            print("Reaction roles saved")

    async def check_reaction_roles(self):
        while True:
            for guild_id, roles in self.reaction_roles.items():
                for role_id, message_id in roles.items():
                    guild = self.bot.get_guild(guild_id)
                    if guild:
                        role = guild.get_role(role_id)
                        if role:
                            message = await guild.get_channel(message_id[0]).fetch_message(message_id[1])
                            if message:
                                for reaction in message.reactions:
                                    if reaction.emoji == message_id[2]:
                                        async for user in reaction.users():
                                            if user != self.bot.user:
                                                await user.add_roles(role)
                                                print(f"Added role {role.name} to {user.name}")
                                        await asyncio.sleep(1)
            print("Checked reaction roles")
            await asyncio.sleep(10)

    def load_reaction_roles(self):
        if os.path.exists("Cogs/Role/RoleData/reaction_roles.json"):
            with open("Cogs/Role/RoleData/reaction_roles.json", "r") as f:
                self.reaction_roles = json.load(f)
            print("Reaction roles loaded")
        
        self.bot.loop.create_task(self.check_reaction_roles())

    @slash_command()
    async def add_reaction_role(self, ctx, role: discord.Role, channel: discord.TextChannel, message_id: int, emoji: str):
        if ctx.author.guild_permissions.manage_roles:
            if ctx.guild.id not in self.reaction_roles:
                self.reaction_roles[ctx.guild.id] = {}
            self.reaction_roles[ctx.guild.id][role.id] = [channel.id, message_id, emoji]
            await ctx.respond(f"Added reaction role {role.name} to message {message_id} in channel {channel.name} with emoji {emoji}")
            print(f"Added reaction role {role.name} to message {message_id} in channel {channel.name} with emoji {emoji}")

    @slash_command()
    async def remove_reaction_role(self, ctx, role: discord.Role):
        if ctx.author.guild_permissions.manage_roles:
            if ctx.guild.id in self.reaction_roles:
                if role.id in self.reaction_roles[ctx.guild.id]:
                    del self.reaction_roles[ctx.guild.id][role.id]
                    await ctx.respond(f"Removed reaction role {role.name}")
                    print(f"Removed reaction role {role.name}")
                else:
                    await ctx.respond(f"Reaction role {role.name} not found")
            else:
                await ctx.respond("No reaction roles found for this guild")

    @slash_command()
    async def list_reaction_roles(self, ctx):
        if ctx.author.guild_permissions.manage_roles:
            if ctx.guild.id in self.reaction_roles:
                roles = self.reaction_roles[ctx.guild.id]
                if roles:
                    embed = discord.Embed(title="Reaction Roles", color=discord.Color.blue())
                    for role_id, message_id in roles.items():
                        role = ctx.guild.get_role(role_id)
                        channel = ctx.guild.get_channel(message_id[0])
                        message = await channel.fetch_message(message_id[1])
                        embed.add_field(name=role.name, value=f"Message: {message.jump_url}\nEmoji: {message_id[2]}", inline=False)
                    await ctx.respond(embed=embed)
                    print(f"Listed reaction roles for guild {ctx.guild.name}")
                else:
                    await ctx.respond("No reaction roles found")
                    print("No reaction roles found")
            else:
                await ctx.respond("No reaction roles found for this guild")

def setup(bot):
    bot.add_cog(ReactionRole(bot))
    print("ReactionRole cog loaded")
