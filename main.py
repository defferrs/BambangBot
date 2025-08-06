import discord
from discord.ext import commands
import os

TOKEN = os.environ.get('TOKEN')
if not TOKEN:
    print("ERROR: No TOKEN environment variable found!")
    exit(1)
intents = discord.Intents.all() #need to enable
# Ensure voice intents are enabled
intents.voice_states = True
intents.guilds = True

bot = commands.Bot(
    command_prefix='~', 
    intents=intents,
    help_command=None,
    case_insensitive=True
)

@bot.event
async def on_ready():
    print(f'\n🤖 {bot.user} is now ONLINE and ready!')
    print(f'📱 Mobile-optimized UI activated')
    print(f'🌟 All-in-One bot features loaded')
    print(f'🏠 Connected to {len(bot.guilds)} servers')
    print(f'👥 Serving {len(bot.users)} users')
    
    # Check voice capabilities
    try:
        import nacl
        print("✅ Voice support enabled (PyNaCl installed)")
    except ImportError:
        print("⚠️ Voice support disabled (PyNaCl not installed)")
    
    # Check Opus library
    try:
        if not discord.opus.is_loaded():
            # Try different opus library names
            opus_loaded = False
            for opus_name in ['libopus.so.0', 'libopus.so', 'opus', 'libopus']:
                try:
                    discord.opus.load_opus(opus_name)
                    opus_loaded = True
                    print(f"✅ Opus library loaded ({opus_name})")
                    break
                except:
                    continue
            
            if not opus_loaded:
                print("⚠️ Opus library not found - music features may not work")
        else:
            print("✅ Opus library already loaded")
    except Exception as e:
        print(f"⚠️ Opus check failed: {e}")
    
    try:
        synced = await bot.tree.sync()
        print(f"✅ Synced {len(synced)} slash commands")
        print(f'🚀 Bot is fully operational with interactive features!')
    except Exception as e:
        print(f"❌ Failed to sync commands: {e}")

@bot.event
async def on_guild_join(guild):
    """Send welcome message when bot joins a server"""
    # Find the best channel to send welcome message
    channel = None
    
    # Try to find system channel first
    if guild.system_channel and guild.system_channel.permissions_for(guild.me).send_messages:
        channel = guild.system_channel
    else:
        # Find first text channel we can send to
        for text_channel in guild.text_channels:
            if text_channel.permissions_for(guild.me).send_messages:
                channel = text_channel
                break
    
    if channel:
        embed = discord.Embed(
            title="🤖 Thank you for adding me!",
            description="**I'm your new all-in-one Discord bot with stunning visuals and mobile optimization!**",
            color=0x00D4FF
        )
        
        embed.add_field(
            name="🌟 What I can do:",
            value="```\n🛡️ Advanced Moderation\n🎵 High-Quality Music\n👤 Role Management\n🔍 Google Search\n⚙️ Server Settings```",
            inline=True
        )
        
        embed.add_field(
            name="📱 Mobile Features:",
            value="```\n✅ Touch-friendly buttons\n✅ Interactive menus\n✅ Responsive design\n✅ Optimized layouts```",
            inline=True
        )
        
        embed.add_field(
            name="🚀 Get Started:",
            value="Use `/help` to see all my features!\nAll commands work perfectly on mobile devices.",
            inline=False
        )
        
        embed.set_footer(text="🎯 Type /help to explore all features • Mobile optimized")
        
        try:
            await channel.send(embed=embed)
        except:
            pass  # If we can't send, that's okay

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