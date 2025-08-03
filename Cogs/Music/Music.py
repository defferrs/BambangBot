import discord
from discord.ext import commands
from discord.commands import slash_command
import asyncio
import random
import yt_dlp
import re

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.voice_clients = {}
        self.music_queue = {}
        self.play_next_song = asyncio.Event()
        self.play_next_song.set()
        self.ytdl_format_options = {
            'format': 'bestaudio/best',
            'restrictfilenames': True,
            'noplaylist': True,
            'nocheckcertificate': True,
            'ignoreerrors': False,
            'logtostderr': False,
            'quiet': True,
            'no_warnings': True,
            'default_search': 'ytsearch',
            'source_address': '0.0.0.0'
        }
        self.ffmpeg_options = {
            'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5 -nostdin',
            'options': '-vn'
        }
        self.ytdl = yt_dlp.YoutubeDL(self.ytdl_format_options)

    def is_url(self, string):
        url_pattern = re.compile(
            r'^https?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        return url_pattern.match(string) is not None

    async def search_youtube(self, query):
        try:
            loop = asyncio.get_event_loop()
            data = await loop.run_in_executor(None, lambda: self.ytdl.extract_info(f"ytsearch:{query}", download=False))
            
            if 'entries' in data and len(data['entries']) > 0:
                return data['entries'][0]
            else:
                return None
        except Exception as e:
            print(f"Error searching YouTube: {e}")
            return None

    async def get_audio_source(self, url_or_query):
        try:
            if self.is_url(url_or_query):
                loop = asyncio.get_event_loop()
                data = await loop.run_in_executor(None, lambda: self.ytdl.extract_info(url_or_query, download=False))
                if 'entries' in data:
                    data = data['entries'][0]
            else:
                data = await self.search_youtube(url_or_query)
                if not data:
                    return None, None
            
            url = data['url']
            title = data.get('title', 'Unknown')
            print(f"Creating audio source for: {title}")
            print(f"Audio URL: {url}")
            
            # Check if opus is loaded
            if not discord.opus.is_loaded():
                print("Opus not loaded, trying to load...")
                # Try different opus library paths for Replit/Nix environment
                opus_paths = [
                    'libopus.so.0',
                    'libopus.so.0.8.0',
                    'libopus.so', 
                    '/nix/store/*/lib/libopus.so.0',
                    '/nix/store/*/lib/libopus.so',
                    '/usr/lib/x86_64-linux-gnu/libopus.so.0',
                    '/usr/lib/libopus.so.0',
                    'opus'
                ]
                
                opus_loaded = False
                for opus_path in opus_paths:
                    try:
                        if '*' in opus_path:
                            # Skip wildcard paths for now
                            continue
                        discord.opus.load_opus(opus_path)
                        print(f"Successfully loaded opus from: {opus_path}")
                        opus_loaded = True
                        break
                    except Exception as e:
                        print(f"Failed to load opus from {opus_path}: {e}")
                        continue
                
                if not opus_loaded:
                    print("WARNING: Could not load opus library - trying alternative approach...")
                    # Try to use the system opus that should be available in Replit
                    try:
                        import ctypes.util
                        opus_lib = ctypes.util.find_library('opus')
                        if opus_lib:
                            discord.opus.load_opus(opus_lib)
                            print(f"Successfully loaded opus using ctypes.util: {opus_lib}")
                            opus_loaded = True
                    except Exception as e:
                        print(f"Failed to load opus using ctypes.util: {e}")
                
                if not opus_loaded:
                    print("WARNING: Could not load opus library - voice may not work properly")
            
            source = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(url, before_options=self.ffmpeg_options['before_options'], options=self.ffmpeg_options['options']))
            return source, title
        except Exception as e:
            print(f"Error getting audio source: {str(e)}")
            import traceback
            traceback.print_exc()
            return None, None

    async def play_song(self, ctx, song_info):
        try:
            if isinstance(song_info, dict):
                query = song_info['query']
                source, title = await self.get_audio_source(query)
            else:
                source, title = await self.get_audio_source(song_info)
                query = song_info

            if not source:
                await ctx.followup.send(f"Could not find or play: {query}")
                if ctx.guild.id in self.music_queue and self.music_queue[ctx.guild.id]:
                    await self.play_song(ctx, self.music_queue[ctx.guild.id].pop(0))
                return

            def after_playing(error):
                if error:
                    print(f'Player error: {str(error)}')
                else:
                    print('Song finished playing')
                
                # Check if there are more songs in queue
                coro = self.handle_next_song(ctx)
                asyncio.run_coroutine_threadsafe(coro, self.bot.loop)

            # Check if voice client is still connected
            if not ctx.voice_client or not ctx.voice_client.is_connected():
                await ctx.followup.send("Voice client disconnected unexpectedly")
                return

            print(f"Starting playback of: {title}")
            ctx.voice_client.play(source, after=after_playing)
            await ctx.followup.send(f"Now playing: {title}")
            print(f"Voice client is playing: {ctx.voice_client.is_playing()}")

        except Exception as e:
            error_msg = str(e) if str(e) else "Unknown error occurred"
            print(f"Error playing song: {error_msg}")
            await ctx.followup.send(f"Error playing song: {error_msg}")
            if ctx.guild.id in self.music_queue and self.music_queue[ctx.guild.id]:
                await self.play_song(ctx, self.music_queue[ctx.guild.id].pop(0))

    async def handle_next_song(self, ctx):
        try:
            # Wait a moment to ensure the current song has finished
            await asyncio.sleep(1)
            
            if ctx.guild.id in self.music_queue and self.music_queue[ctx.guild.id]:
                next_song = self.music_queue[ctx.guild.id].pop(0)
                await self.play_song(ctx, next_song)
            else:
                # Only disconnect after a delay to allow for new songs to be added
                await asyncio.sleep(5)
                if ctx.voice_client and not ctx.voice_client.is_playing():
                    if ctx.guild.id not in self.music_queue or not self.music_queue[ctx.guild.id]:
                        await ctx.voice_client.disconnect()
                        print("Disconnected due to empty queue")
        except Exception as e:
            print(f"Error handling next song: {e}")

    @slash_command(contexts={discord.InteractionContextType.guild})
    async def play(self, ctx, query: str):
        # Ensure we're in a guild and author is a Member
        if not hasattr(ctx.author, 'voice') or not ctx.author.voice:
            await ctx.respond("Anda sedang tidak berada di voice channel.")
            return
        
        # Handle voice connection
        if not ctx.voice_client:
            await ctx.author.voice.channel.connect()
            await ctx.respond("Bot telah bergabung ke voice channel dan memproses lagu...")
        else:
            await ctx.voice_client.move_to(ctx.author.voice.channel)
            await ctx.respond("Memproses lagu...")

        if ctx.guild.id not in self.music_queue:
            self.music_queue[ctx.guild.id] = []

        # Check if it's a URL or search query
        if self.is_url(query):
            display_text = f"URL: {query}"
        else:
            display_text = f"Search: {query}"

        song_info = {"query": query, "display": display_text}
        self.music_queue[ctx.guild.id].append(song_info)

        await ctx.followup.send(f"Ditambahkan ke antrian: {display_text}")
        if not ctx.voice_client.is_playing():
            await self.play_song(ctx, self.music_queue[ctx.guild.id].pop(0))

    @slash_command(contexts={discord.InteractionContextType.guild})
    async def stop(self, ctx):
        if ctx.voice_client:
            await ctx.voice_client.disconnect()
            if ctx.guild.id in self.music_queue:
                self.music_queue[ctx.guild.id] = []
            await ctx.respond("Bot telah meninggalkan voice channel dan antrian telah dihapus.")
        else:
            await ctx.respond("Bot tidak sedang berada di voice channel.")

    @slash_command(contexts={discord.InteractionContextType.guild})
    async def skip(self, ctx):
        if ctx.voice_client and ctx.voice_client.is_playing():
            ctx.voice_client.stop()
            await ctx.respond("Lagu telah dilewati.")
        else:
            await ctx.respond("Tidak ada lagu yang sedang diputar.")

    @slash_command(contexts={discord.InteractionContextType.guild})
    async def pause(self, ctx):
        if ctx.voice_client and ctx.voice_client.is_playing():
            ctx.voice_client.pause()
            await ctx.respond("Lagu telah dijeda")
        else:
            await ctx.respond("Tidak ada lagu yang sedang diputar.")

    @slash_command(contexts={discord.InteractionContextType.guild})
    async def resume(self, ctx):
        if ctx.voice_client and ctx.voice_client.is_paused():
            ctx.voice_client.resume()
            await ctx.respond("Lagu telah dilanjutkan")
        else:
            await ctx.respond("Tidak ada lagu yang sedang diputar.")

    @slash_command(contexts={discord.InteractionContextType.guild})
    async def queue(self, ctx):
        if ctx.guild.id in self.music_queue and self.music_queue[ctx.guild.id]:
            queue_list = []
            for i, song in enumerate(self.music_queue[ctx.guild.id]):
                if isinstance(song, dict):
                    display = song.get('display', song.get('query', 'Unknown'))
                else:
                    display = song
                queue_list.append(f"{i+1}. {display}")
            await ctx.respond(f"Antrian:\n" + "\n".join(queue_list))
        else:
            await ctx.respond("Antrian kosong.")

    @slash_command(contexts={discord.InteractionContextType.guild})
    async def shuffle(self, ctx):
        if ctx.guild.id in self.music_queue and self.music_queue[ctx.guild.id]:
            random.shuffle(self.music_queue[ctx.guild.id])
            await ctx.respond("Antrian telah diacak.")
        else:
            await ctx.respond("Antrian kosong.")

    @slash_command(contexts={discord.InteractionContextType.guild})
    async def remove(self, ctx, position: int):
        if ctx.guild.id not in self.music_queue:
            self.music_queue[ctx.guild.id] = []

        if position < 1 or position > len(self.music_queue[ctx.guild.id]):
            await ctx.respond("Posisi tidak valid.")
            return
        if self.music_queue[ctx.guild.id]:
            removed_song = self.music_queue[ctx.guild.id].pop(position - 1)
            if isinstance(removed_song, dict):
                display = removed_song.get('display', removed_song.get('query', 'Unknown'))
            else:
                display = removed_song
            await ctx.respond(f"Lagu {display} telah dihapus dari antrian.")
        else:
            await ctx.respond("Antrian kosong.")

def setup(bot):
    bot.add_cog(Music(bot))
    print("Music cog loaded")