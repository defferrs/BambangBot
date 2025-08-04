import discord
from discord.ext import commands
from discord.commands import slash_command
from discord.commands import Option

class AddRole(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @slash_command(description="Tambahkan role kepada member")
    async def addrole(self, ctx, member: Option(discord.Member, "Member yang akan diberi role"), role: Option(discord.Role, "Role yang akan diberikan")):
        await member.add_roles(role)
        await ctx.respond(f"✅ Role {role.mention} telah diberikan kepada {member.mention}")
        try:
            await member.send(f"Anda telah diberi role {role.name} di server {ctx.guild.name}")
        except discord.Forbidden:
            pass  # User has DMs disabled

def setup(bot):
    bot.add_cog(AddRole(bot))
    print("AddRole cog loaded")