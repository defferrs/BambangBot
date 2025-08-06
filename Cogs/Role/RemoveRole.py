
import discord
from discord.ext import commands
from discord.commands import slash_command, Option

class RemoveRole(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @slash_command(description="Hapus role dari member")
    async def removerole(self, ctx, member: Option(discord.Member, "Member yang akan dihapus rolenya"), role: Option(discord.Role, "Role yang akan dihapus")):
        await member.remove_roles(role)
        await ctx.respond(f"✅ Role {role.mention} telah dihapus dari {member.mention}")
        try:
            await member.send(f"Role {role.name} Anda telah dihapus dari server {ctx.guild.name}")
        except discord.Forbidden:
            pass  # User has DMs disabled

def setup(bot):
    bot.add_cog(RemoveRole(bot))
    print("RemoveRole cog loaded")
