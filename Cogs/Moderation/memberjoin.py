import discord
from discord.ext import commands


intents = discord.Intents.default()
intents.members = True
intents.guilds = True
intents.message_content = True

class memberjoin(commands.Cog):
  def __init__(self, bot):
    self.bot = bot
    self.intents = intents
    self.bot = commands.Bot(command_prefix='~', intents=self.intents)
    self.bot.remove_command('help')

  
  

@commands.Cog.listener()
async def on_member_join(member):
  print(f'{member} Telah bergabung dengan server ini!')
  await member.send(f'Selamat datang di server ini, {member.name}!')
  await member.add_roles(discord.utils.get(member.guild.roles, name='Member'))
  await member.edit(nick=f'[member] {member.name}')
  await member.guild.system_channel.send(f'Selamat datang {member.mention} di server ini!')
  await member.guild.system_channel.send(f'Silahkan baca rules di {member.guild.rules_channel.mention} terlebih dahulu')
  await member.guild.system_channel.send('Selamat bermain!')


@commands.Cog.listener()
async def on_member_remove(member):
  print(f'{member} Telah keluar dari server')
  await member.guild.system_channel.send(f'{member.mention} Telah keluar dari server')
  await member.guild.system_channel.send(f'Selamat tinggal {member.mention}!')
  await member.guild.system_channel.send(f'Kami akan merindukanmu {member.mention}!')

@commands.slash_command()

@slash_command()
async def membercount(self, ctx):
  await ctx.respond(ctx.guild.member_count)
  print(f'Member count: {ctx.guild.member_count}')

@slash_command()
async def memberlist(self, ctx):
  await ctx.respond(ctx.guild.members)
  print(f'Member list: {ctx.guild.members}')

@slash_command()
async def memberinfo(self, ctx):
  await ctx.respond(ctx.guild.members)
  print(f'Member info: {ctx.guild.members}', ctx.guild.members.name, ctx.guild.members.id, ctx.guild.members.joined_at, ctx.guild.members.roles, ctx.guild.members.status, ctx.guild.members.activity, ctx.guild.members.top_role,)


def setup(bot):
    bot.add_cog(memberjoin(bot))
    print('memberjoin.py loaded')
  