import discord
from discord.ext import commands
from discord.commands import slash_command
from discord.commands import Option

class AddRole(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @slash_command()
    async def addrole(self, ctx, member: Option(discord.Member), role: Option(discord.Role)):
        await member.add_roles(role)
        await ctx.respond(f"Added {role} to {member}")
        try:
            await member.send(f"You have been given the role {role} in {ctx.guild.name}")
        except discord.Forbidden:
            pass  # User has DMs disabled

def setup(bot):
    bot.add_cog(AddRole(bot))
    print("AddRole cog loaded")