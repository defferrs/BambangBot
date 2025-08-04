import discord
from discord.ext import commands
import os

TOKEN = os.environ.get('TOKEN')
if not TOKEN:
    print("ERROR: No TOKEN environment variable found!")
    exit(1)
intents = discord.Intents.all() #need to enable
bot = commands.Bot(command_prefix='~', intents=intents)

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')
    try:
        synced = await bot.sync_commands()
        print(f"Synced {len(synced)} commands")
    except Exception as e:
        print(f"Failed to sync commands: {e}")

for foldername in os.listdir('./Cogs'): #for every folder in cogs
    for filename in os.listdir(f'./Cogs/{foldername}'):# for every file in a folder in cogs
        if filename.endswith('.py') and not filename in ['util.py', 'error.py']: #if the file is a python file and if the file is a cog
            try:
                bot.load_extension(f'Cogs.{foldername}.{filename[:-3]}')#load the extension
                print(f"Loaded {foldername}.{filename[:-3]}")
            except Exception as e:
                print(f"Failed to load {foldername}.{filename[:-3]}: {e}")



try:
    bot.run(TOKEN)
except discord.LoginFailure:
    print("ERROR: Invalid TOKEN provided!")
except Exception as e:
    print(f"ERROR: Bot failed to start: {e}")