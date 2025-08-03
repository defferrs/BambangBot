import discord
from discord.ext import commands
from discord.commands import slash_command
from discord.commands import Option

class AddRole(commands.Cog):
  def __init__(self, bot)
  self.bot = bot

@slash_command()
async def addrole(self, ctx, member: Option(discord.Member), role: Option(discord.Role)):
  await member.add_roles(role)
  await ctx.respond(f"Added {role} to {member}")
  await member.send(f"You have been given the role {role} in {ctx.guild.name}")
  await ctx.respond(f"Added {role} to {member}")

def setup(bot):
  bot.add_cog(AddRole(bot)):
  print("AddRole cog loaded")



-- Cogs/Role/RemoveRole.py
import discord
from discord.ext import commands
from discord.commands import slash_command
from discord.commands import Option

class RemoveRole(commands.Cog)
  def __init__(self, bot):
    self.bot = bot
  @slash_command():
  async def removerole(self, ctx, member: Option(discord.Member),
        role: Option(discord.Role)):
    await member.remove_roles(role)
    await ctx.respond(f"Removed {role} from {member}")
    await member.send(f"You have been removed the role {role} in {ctx.guild.name}")

def setup(bot):
  bot.add_cog(RemoveRole(bot))
  print("RemoveRole cog loaded")
  print("Role cog loaded")


-- Cogs/Role/ReactionRole.py
import discord
from discord.ext import commands
from discord.commands import slash_command
from discord.commands import Option

def to_upper(string): 
  
          return string.upper()
  if string == None:
    return string
  else:
    return string.upper() 







# Note that you have to copy and paste all this code into yours or if you are more advanced feel free to do whatever you want. Enjoy~!
# This code is not specifically for 1 server your bot can execute this code on any server 

class Roles(discord.ui.View):
  def __init__(self, role_n):
    self.role_n = role_n
    super().__init__(timeout = None)
  

  @discord.ui.button(label= '✅', custom_id = "Announcement", style = discord.ButtonStyle.gray)
  async def button1(self, interaction, button):
    _role = discord.utils.get(interaction.guild.roles, name= self.role_n)
    role = _role.id #put your role id here
    user = interaction.user
    if role in [y.id for y in user.roles]:
      await user.remove_roles(user.guild.get_role(role))
      await interaction.response.send_message(f"You have removed a {_role} role!", ephemeral = True)
    else:
      await user.add_roles(user.guild.get_role(role))
      await interaction.response.send_message(f"You have added a {_role} role!", ephemeral = True)



@Raiden.tree.command(name='reaction_role', description='Provide the role name') # kindly replace @Raiden with your client name or leave it as @bot instead
async def reaction_role(ctx: discord.Interaction, role_name: str, description_of_role: str):
  embed = discord.Embed(title = to_upper(role_name), description = description_of_role)
  r = discord.utils.get(ctx.guild.roles, name= role_name)
  if r == None:
      await ctx.response.send_message(ValueError('provide valid name of role. Please recheck the name of role'))
  else:
    
    await ctx.response.send_message(embed = embed, view = Roles(role_name))  