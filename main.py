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
    print(f'\n🤖 {bot.user} sekarang ONLINE dan siap!')
    print(f'📱 UI dioptimalkan untuk mobile telah aktif')
    print(f'🌟 Semua fitur bot All-in-One telah dimuat')
    print(f'🏠 Terhubung ke {len(bot.guilds)} server')
    print(f'👥 Melayani {len(bot.users)} pengguna')
    
    # Check voice capabilities
    try:
        import nacl
        print("✅ Dukungan voice diaktifkan (PyNaCl terinstal)")
    except ImportError:
        print("⚠️ Dukungan voice dinonaktifkan (PyNaCl tidak terinstal)")
    
    # Check Opus library
    try:
        if not discord.opus.is_loaded():
            # Try different opus library names
            opus_loaded = False
            for opus_name in ['libopus.so.0', 'libopus.so', 'opus', 'libopus']:
                try:
                    discord.opus.load_opus(opus_name)
                    opus_loaded = True
                    print(f"✅ Library Opus dimuat ({opus_name})")
                    break
                except:
                    continue
            
            if not opus_loaded:
                print("⚠️ Library Opus tidak ditemukan - fitur musik mungkin tidak berfungsi")
        else:
            print("✅ Library Opus sudah dimuat")
    except Exception as e:
        print(f"⚠️ Pemeriksaan Opus gagal: {e}")
    
    try:
        synced = await bot.sync_commands()
        if synced is not None:
            print(f"✅ Disinkronkan {len(synced)} slash command")
        else:
            print("✅ Command berhasil disinkronkan")
        print(f'🚀 Bot sepenuhnya operasional dengan fitur interaktif!')
    except Exception as e:
        print(f"❌ Gagal menyinkronkan command: {e}")

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
            title="🤖 Terima kasih telah menambahkan saya!",
            description="**Saya bot Discord all-in-one baru Anda dengan visual menakjubkan dan optimasi mobile!**",
            color=0x00D4FF
        )
        
        embed.add_field(
            name="🌟 Apa yang bisa saya lakukan:",
            value="```\n🛡️ Moderasi Canggih\n🎵 Musik Berkualitas Tinggi\n👤 Manajemen Role\n🔍 Pencarian Google\n⚙️ Pengaturan Server```",
            inline=True
        )
        
        embed.add_field(
            name="📱 Fitur Mobile:",
            value="```\n✅ Tombol ramah sentuh\n✅ Menu interaktif\n✅ Desain responsif\n✅ Layout yang dioptimalkan```",
            inline=True
        )
        
        embed.add_field(
            name="🚀 Mulai:",
            value="Gunakan `/bantuan` untuk melihat semua fitur saya!\nSemua command berfungsi sempurna di perangkat mobile.",
            inline=False
        )
        
        embed.set_footer(text="🎯 Ketik /bantuan untuk menjelajahi semua fitur • Dioptimalkan untuk mobile")
        
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