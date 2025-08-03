
import discord
from discord.ext import commands
from discord.commands import slash_command
from discord.commands import Option

class RemoveRole(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @slash_command()
    async def removerole(self, ctx, member: Option(discord.Member), role: Option(discord.Role)):
        await member.remove_roles(role)
        await ctx.respond(f"Removed {role} from {member}")
        try:
            await member.send(f"You have been removed the role {role} in {ctx.guild.name}")
        except discord.Forbidden:
            pass  # User has DMs disabled

def setup(bot):
    bot.add_cog(RemoveRole(bot))
    print("RemoveRole cog loaded")
