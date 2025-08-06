
import discord
from discord.ext import commands
from discord import app_commands

class RemoveRole(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="removerole", description="Hapus role dari member")
    @app_commands.describe(member="Member yang akan dihapus rolenya", role="Role yang akan dihapus")
    async def removerole(self, interaction: discord.Interaction, member: discord.Member, role: discord.Role):
        await member.remove_roles(role)
        await interaction.response.send_message(f"✅ Role {role.mention} telah dihapus dari {member.mention}")
        try:
            await member.send(f"Role {role.name} Anda telah dihapus dari server {interaction.guild.name}")
        except discord.Forbidden:
            pass  # User has DMs disabled

def setup(bot):
    bot.add_cog(RemoveRole(bot))
    print("RemoveRole cog loaded")
