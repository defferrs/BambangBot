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
            'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
            'restrictfilenames': True,
            'noplaylist': True,
            'nocheckcertificate': True,
            'ignoreerrors': False,
            'logtostderr': False,
            'quiet': True,
            'no_warnings': True,
            'default_search': 'ytsearch',
            'source_address': '0.0.0.0',
            'extractaudio': True,
            'audioformat': 'mp3',
            'age_limit': 21
        }
        self.ffmpeg_options = {
            'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5 -nostdin',
            'options': '-vn -filter:a "volume=0.5"'
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
            source = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(url, **self.ffmpeg_options))
            return source, title
        except Exception as e:
            print(f"Error getting audio source: {e}")
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
                    print(f'Player error: {error}')
                self.bot.loop.call_soon_threadsafe(self.play_next_song.set)

            ctx.voice_client.play(source, after=after_playing)

            await ctx.followup.send(f"Now playing: {title}")

            await self.play_next_song.wait()
            self.play_next_song.clear()

            if ctx.voice_client and ctx.voice_client.is_playing():
                return
            if ctx.guild.id in self.music_queue and self.music_queue[ctx.guild.id]:
                await self.play_song(ctx, self.music_queue[ctx.guild.id].pop(0))
            else:
                if ctx.voice_client:
                    await ctx.voice_client.disconnect()
        except Exception as e:
            print(f"Error playing song: {str(e)}")
            await ctx.followup.send(f"Error playing song: {str(e)}")
            if ctx.guild.id in self.music_queue and self.music_queue[ctx.guild.id]:
                await self.play_song(ctx, self.music_queue[ctx.guild.id].pop(0))

    @slash_command()
    async def play(self, ctx, query: str):
        if not ctx.author.voice:
            await ctx.respond("Anda sedang tidak berada di voice channel.")
            return
        if not ctx.voice_client:
            await ctx.author.voice.channel.connect()
            await ctx.respond("Bot telah bergabung ke voice channel.")
        else:
            await ctx.voice_client.move_to(ctx.author.voice.channel)

        if ctx.guild.id not in self.music_queue:
            self.music_queue[ctx.guild.id] = []

        # Check if it's a URL or search query
        if self.is_url(query):
            display_text = f"URL: {query}"
        else:
            display_text = f"Search: {query}"

        song_info = {"query": query, "display": display_text}
        self.music_queue[ctx.guild.id].append(song_info)

        await ctx.respond(f"Ditambahkan ke antrian: {display_text}")
        if not ctx.voice_client.is_playing():
            await self.play_song(ctx, self.music_queue[ctx.guild.id].pop(0))

    @slash_command()
    async def stop(self, ctx):
        if ctx.voice_client:
            await ctx.voice_client.disconnect()
            if ctx.guild.id in self.music_queue:
                self.music_queue[ctx.guild.id] = []
            await ctx.respond("Bot telah meninggalkan voice channel dan antrian telah dihapus.")
        else:
            await ctx.respond("Bot tidak sedang berada di voice channel.")

    @slash_command()
    async def skip(self, ctx):
        if ctx.voice_client and ctx.voice_client.is_playing():
            ctx.voice_client.stop()
            await ctx.respond("Lagu telah dilewati.")
        else:
            await ctx.respond("Tidak ada lagu yang sedang diputar.")

    @slash_command()
    async def pause(self, ctx):
        if ctx.voice_client and ctx.voice_client.is_playing():
            ctx.voice_client.pause()
            await ctx.respond("Lagu telah dijeda")
        else:
            await ctx.respond("Tidak ada lagu yang sedang diputar.")

    @slash_command()
    async def resume(self, ctx):
        if ctx.voice_client and ctx.voice_client.is_paused():
            ctx.voice_client.resume()
            await ctx.respond("Lagu telah dilanjutkan")
        else:
            await ctx.respond("Tidak ada lagu yang sedang diputar.")

    @slash_command()
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

    @slash_command()
    async def shuffle(self, ctx):
        if ctx.guild.id in self.music_queue and self.music_queue[ctx.guild.id]:
            random.shuffle(self.music_queue[ctx.guild.id])
            await ctx.respond("Antrian telah diacak.")
        else:
            await ctx.respond("Antrian kosong.")

    @slash_command()
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