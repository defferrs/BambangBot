import discord
from discord.ext import commands
from discord.commands import slash_command, Option
import asyncio
import random
import yt_dlp
import re
import os
import subprocess

# Global flags - will be checked at runtime, not import time
VOICE_ENABLED = None
OPUS_ENABLED = None

def check_voice_dependencies():
    """Check voice dependencies at runtime only"""
    global VOICE_ENABLED, OPUS_ENABLED

    # Check PyNaCl
    if VOICE_ENABLED is None:
        try:
            import nacl
            import nacl.secret
            from nacl.encoding import Base64Encoder
            VOICE_ENABLED = True
        except ImportError:
            VOICE_ENABLED = False
            return False, "PyNaCl not available"

    # Check Opus
    if OPUS_ENABLED is None:
        # The 'opuslib' import has been removed to prevent import errors.
        # We will rely on discord.py's built-in Opus handling.
        OPUS_ENABLED = False # Initialize to False, will be updated if discord.py loads it

    # Try to load opus from discord.py
    if not discord.opus.is_loaded():
        opus_names = ['libopus.so.0', 'libopus.so', 'opus', 'libopus', 'libopus-0.dll', 'opus.dll']
        for opus_name in opus_names:
            try:
                discord.opus.load_opus(opus_name)
                if discord.opus.is_loaded():
                    OPUS_ENABLED = True
                    return True, "All dependencies ready"
            except Exception as e: # Catch specific exceptions if needed, but general catch is fine here
                # print(f"Failed to load opus with {opus_name}: {e}") # Optional: for debugging
                continue
        return False, "Opus library not available"

    # If discord.opus is already loaded, assume OPUS_ENABLED is True
    OPUS_ENABLED = True
    return True, "All dependencies ready"

# FFmpeg options for better audio quality
FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn'
}

# yt-dlp options
YDL_OPTIONS = {
    'format': 'bestaudio/best',
    'noplaylist': True,
    'extractaudio': True,
    'audioformat': 'mp3',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'no_warnings': True,
    'logtostderr': False,
    'ignoreerrors': False,
    'default_search': 'auto',
    'source_address': '0.0.0.0'
}

class MusicControls(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.button(emoji="⏸️", style=discord.ButtonStyle.secondary, custom_id="pause")
    async def pause_button(self, button: discord.ui.Button, interaction: discord.Interaction):
        try:
            voice = discord.utils.get(self.bot.voice_clients, guild=interaction.guild)
            if voice and voice.is_playing():
                voice.pause()
                embed = discord.Embed(
                    title="⏸️ Music Paused",
                    description="Music has been paused. Click ▶️ to resume.",
                    color=0xFFA500
                )
                await interaction.response.edit_message(embed=embed, view=self)
            else:
                await interaction.response.send_message("❌ No music is currently playing!", ephemeral=True)
        except discord.NotFound:
            # Interaction already responded to or expired
            pass
        except Exception as e:
            print(f"Pause button error: {e}")
            try:
                await interaction.response.send_message("❌ An error occurred!", ephemeral=True)
            except:
                pass

    @discord.ui.button(emoji="▶️", style=discord.ButtonStyle.success, custom_id="resume")
    async def resume_button(self, button: discord.ui.Button, interaction: discord.Interaction):
        try:
            voice = discord.utils.get(self.bot.voice_clients, guild=interaction.guild)
            if voice and voice.is_paused():
                voice.resume()
                embed = discord.Embed(
                    title="▶️ Music Resumed",
                    description="Music playback has been resumed!",
                    color=0x00FF00
                )
                await interaction.response.edit_message(embed=embed, view=self)
            else:
                await interaction.response.send_message("❌ No music is currently paused!", ephemeral=True)
        except discord.NotFound:
            # Interaction already responded to or expired
            pass
        except Exception as e:
            print(f"Resume button error: {e}")
            try:
                await interaction.response.send_message("❌ An error occurred!", ephemeral=True)
            except:
                pass

    @discord.ui.button(emoji="⏭️", style=discord.ButtonStyle.primary, custom_id="skip")
    async def skip_button(self, button: discord.ui.Button, interaction: discord.Interaction):
        try:
            voice = discord.utils.get(self.bot.voice_clients, guild=interaction.guild)
            if voice and (voice.is_playing() or voice.is_paused()):
                # Check if auto-play is active
                music_cog = self.bot.get_cog('Music')
                is_auto_play = (music_cog and hasattr(music_cog, 'auto_play_mode') and 
                               interaction.guild.id in music_cog.auto_play_mode)
                
                voice.stop()
                
                # If auto-play is active and queue is low, get more recommendations
                if is_auto_play and music_cog and interaction.guild.id in music_cog.queue:
                    if len(music_cog.queue[interaction.guild.id]) <= 2:  # When queue is getting low
                        try:
                            last_played = music_cog.auto_play_mode.get(interaction.guild.id)
                            if last_played:
                                # Add small delay to prevent rate limiting
                                await asyncio.sleep(1)
                                recommendations = await music_cog.get_youtube_recommendations(last_played)
                                for rec in recommendations[:3]:  # Add 3 more songs to prevent overwhelming
                                    music_cog.queue[interaction.guild.id].append((rec['title'], rec['webpage_url']))
                                print(f"Auto-play: Added {len(recommendations)} more recommendations")
                        except Exception as rec_error:
                            print(f"Auto-play recommendation error: {rec_error}")
                
                embed = discord.Embed(
                    title="⏭️ Song Skipped",
                    description="Skipped to the next song in queue!" + 
                               ("\n🎲 Auto-play: Getting more recommendations..." if is_auto_play else ""),
                    color=0x3498DB
                )
                await interaction.response.edit_message(embed=embed, view=self)
            else:
                await interaction.response.send_message("❌ No music is currently playing!", ephemeral=True)
        except discord.NotFound:
            # Interaction already responded to or expired
            pass
        except Exception as e:
            print(f"Skip button error: {e}")
            try:
                await interaction.response.send_message("❌ An error occurred while skipping!", ephemeral=True)
            except:
                pass

    @discord.ui.button(emoji="⏹️", style=discord.ButtonStyle.danger, custom_id="stop")
    async def stop_button(self, button: discord.ui.Button, interaction: discord.Interaction):
        try:
            voice = discord.utils.get(self.bot.voice_clients, guild=interaction.guild)
            if voice:
                music_cog = self.bot.get_cog('Music')
                if music_cog and hasattr(music_cog, 'queue') and interaction.guild.id in music_cog.queue:
                    music_cog.queue[interaction.guild.id].clear()
                if music_cog and hasattr(music_cog, 'auto_play_mode') and interaction.guild.id in music_cog.auto_play_mode:
                    del music_cog.auto_play_mode[interaction.guild.id]
                await voice.disconnect()
                embed = discord.Embed(
                    title="⏹️ Music Stopped",
                    description="Music stopped and queue cleared. Disconnected from voice channel.",
                    color=0xFF0000
                )
                await interaction.response.edit_message(embed=embed, view=None)
            else:
                await interaction.response.send_message("❌ Bot is not connected to a voice channel!", ephemeral=True)
        except discord.NotFound:
            # Interaction already responded to or expired
            pass
        except Exception as e:
            print(f"Stop button error: {e}")
            try:
                await interaction.response.send_message("❌ An error occurred!", ephemeral=True)
            except:
                pass

    @discord.ui.button(emoji="🔀", style=discord.ButtonStyle.secondary, custom_id="shuffle")
    async def shuffle_button(self, button: discord.ui.Button, interaction: discord.Interaction):
        try:
            music_cog = self.bot.get_cog('Music')
            if music_cog and hasattr(music_cog, 'queue') and interaction.guild.id in music_cog.queue:
                if len(music_cog.queue[interaction.guild.id]) > 1:
                    random.shuffle(music_cog.queue[interaction.guild.id])
                    embed = discord.Embed(
                        title="🔀 Queue Shuffled",
                        description=f"Shuffled {len(music_cog.queue[interaction.guild.id])} songs in the queue!",
                        color=0x9B59B6
                    )
                    await interaction.response.edit_message(embed=embed, view=self)
                else:
                    await interaction.response.send_message("❌ Need at least 2 songs in queue to shuffle!", ephemeral=True)
            else:
                await interaction.response.send_message("❌ No songs in queue!", ephemeral=True)
        except discord.NotFound:
            # Interaction already responded to or expired
            pass
        except Exception as e:
            print(f"Shuffle button error: {e}")
            try:
                await interaction.response.send_message("❌ An error occurred!", ephemeral=True)
            except:
                pass

class QueueView(discord.ui.View):
    def __init__(self, bot, guild_id, page=0):
        super().__init__(timeout=300)
        self.bot = bot
        self.guild_id = guild_id
        self.page = page

    @discord.ui.button(emoji="⬅️", style=discord.ButtonStyle.secondary)
    async def previous_page(self, button: discord.ui.Button, interaction: discord.Interaction):
        if self.page > 0:
            self.page -= 1
            embed = self.create_queue_embed()
            await interaction.response.edit_message(embed=embed, view=self)
        else:
            await interaction.response.send_message("❌ Already on the first page!", ephemeral=True)

    @discord.ui.button(emoji="➡️", style=discord.ButtonStyle.secondary)
    async def next_page(self, button: discord.ui.Button, interaction: discord.Interaction):
        music_cog = self.bot.get_cog('Music')
        if music_cog and hasattr(music_cog, 'queue') and self.guild_id in music_cog.queue:
            total_pages = (len(music_cog.queue[self.guild_id]) - 1) // 10 + 1
            if self.page < total_pages - 1:
                self.page += 1
                embed = self.create_queue_embed()
                await interaction.response.edit_message(embed=embed, view=self)
            else:
                await interaction.response.send_message("❌ Already on the last page!", ephemeral=True)

    def create_queue_embed(self):
        music_cog = self.bot.get_cog('Music')
        if not music_cog or not hasattr(music_cog, 'queue') or self.guild_id not in music_cog.queue:
            return discord.Embed(title="📝 Queue Empty", description="No songs in queue!", color=0xFF0000)

        queue = music_cog.queue[self.guild_id]
        if not queue:
            return discord.Embed(title="📝 Queue Empty", description="No songs in queue!", color=0xFF0000)

        start = self.page * 10
        end = start + 10
        page_queue = queue[start:end]

        embed = discord.Embed(
            title="📝 Music Queue",
            description=f"**Total songs:** {len(queue)} | **Page:** {self.page + 1}/{(len(queue) - 1) // 10 + 1}",
            color=0x1DB954
        )

        for i, (title, url) in enumerate(page_queue, start=start + 1):
            embed.add_field(
                name=f"**{i}.** {title[:50]}{'...' if len(title) > 50 else ''}",
                value=f"[🔗 YouTube Link]({url})",
                inline=False
            )

        embed.set_footer(text="🎵 Use the buttons to navigate • Mobile optimized")
        return embed

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.queue = {}
        self.current_song = {}
        self.auto_play_mode = {}

    async def search_youtube(self, query):
        """Search for music on YouTube"""
        try:
            with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
                info = ydl.extract_info(f"ytsearch:{query}", download=False)
                if 'entries' in info and len(info['entries']) > 0:
                    entry = info['entries'][0]
                    return {
                        'title': entry.get('title', 'Unknown'),
                        'url': entry.get('webpage_url', ''),
                        'duration': entry.get('duration', 0),
                        'uploader': entry.get('uploader', 'Unknown')
                    }
        except Exception as e:
            print(f"Search error: {e}")
            return None

    @slash_command(description="🎵 Play music from YouTube with interactive controls")
    async def play(self, ctx, *, query: Option(str, "Song name or YouTube URL")):
        """Play music with modern interactive controls"""

        # Check all dependencies at runtime
        deps_ready, deps_message = check_voice_dependencies()
        if not deps_ready:
            embed = discord.Embed(
                title="❌ Voice Dependencies Missing",
                description=f"{deps_message}\n\nMusic functionality is currently unavailable.",
                color=0xFF0000
            )
            await ctx.respond(embed=embed)
            return

        # Check if user is in voice channel with proper error handling
        if not ctx.author.voice or not ctx.author.voice.channel:
            embed = discord.Embed(
                title="❌ Voice Channel Required",
                description="You need to join a voice channel first!",
                color=0xFF0000
            )
            await ctx.respond(embed=embed)
            return

        # Loading embed
        loading_embed = discord.Embed(
            title="🔍 Searching...",
            description=f"Looking for: **{query}**",
            color=0xFFA500
        )
        await ctx.respond(embed=loading_embed)

        # Search for the song with enhanced options and bot detection avoidance
        ydl_opts = {
            'format': 'bestaudio[ext=m4a]/bestaudio[ext=webm]/bestaudio/best',
            'quiet': True,
            'no_warnings': True,
            'extractflat': False,
            'nocheckcertificate': True,
            'ignoreerrors': True,
            'default_search': 'ytsearch',
            'extract_flat': False,
            'age_limit': 18,
            'cookiefile': None,
            'extractor_args': {
                'youtube': {
                    'skip': ['dash', 'hls'],
                    'player_skip': ['configs', 'webpage'],
                    'player_client': ['android', 'web']
                }
            },
            'user_agent': 'Mozilla/5.0 (Linux; Android 11; SM-G973F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.120 Mobile Safari/537.36',
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Linux; Android 11; SM-G973F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.120 Mobile Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-us,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                if 'youtube.com' in query or 'youtu.be' in query:
                    info = ydl.extract_info(query, download=False)
                else:
                    search_query = f"ytsearch:{query}"
                    info = ydl.extract_info(search_query, download=False)
                    info = info['entries'][0]

                title = info['title']
                url = info['webpage_url']
                duration = info.get('duration', 0)
                thumbnail = info.get('thumbnail', '')

        except Exception as e:
            error_embed = discord.Embed(
                title="❌ Search Failed",
                description=f"Could not find or play: **{query}**\n\nError: {str(e)}",
                color=0xFF0000
            )
            await ctx.edit(embed=error_embed)
            return

        # Connect to voice channel with better error handling
        voice_channel = ctx.author.voice.channel
        voice = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)

        try:
            if not voice:
                voice = await voice_channel.connect(reconnect=True, timeout=60.0)
            elif voice.channel != voice_channel:
                await voice.move_to(voice_channel)
        except discord.ClientException as e:
            if "already connected to a voice channel" in str(e).lower():
                try:
                    await voice.disconnect(force=True)
                    await asyncio.sleep(1)
                    voice = await voice_channel.connect(reconnect=True, timeout=60.0)
                except Exception as reconnect_error:
                    error_embed = discord.Embed(
                        title="❌ Voice Connection Failed",
                        description=f"Could not connect to voice channel: {str(reconnect_error)}",
                        color=0xFF0000
                    )
                    await ctx.edit(embed=error_embed)
                    return
            else:
                error_embed = discord.Embed(
                    title="❌ Voice Connection Failed",
                    description=f"Could not connect to voice channel: {str(e)}",
                    color=0xFF0000
                )
                await ctx.edit(embed=error_embed)
                return
        except Exception as e:
            error_embed = discord.Embed(
                title="❌ Voice Connection Failed",
                description=f"Could not connect to voice channel: {str(e)}",
                color=0xFF0000
            )
            await ctx.edit(embed=error_embed)
            return

        # Initialize queue if not exists
        if ctx.guild.id not in self.queue:
            self.queue[ctx.guild.id] = []

        # Add to queue
        self.queue[ctx.guild.id].append((title, url))
        
        # Track the song for potential auto-play recommendations
        if not hasattr(self, 'last_played'):
            self.last_played = {}
        self.last_played[ctx.guild.id] = url

        # If not currently playing, start playing
        if not voice.is_playing() and not voice.is_paused():
            await self.play_next(ctx, voice)
        else:
            # Song added to queue
            embed = discord.Embed(
                title="📝 Added to Queue",
                description=f"**{title}**\n\nPosition in queue: **{len(self.queue[ctx.guild.id])}**",
                color=0x00FF00
            )
            embed.add_field(name="Duration", value=f"{duration//60}:{duration%60:02d}" if duration else "Unknown", inline=True)
            embed.add_field(name="Queue Length", value=f"{len(self.queue[ctx.guild.id])} songs", inline=True)
            if thumbnail:
                embed.set_thumbnail(url=thumbnail)
            embed.set_footer(text="🎵 Your song will play when queue reaches it")

            view = MusicControls(self.bot)
            await ctx.edit(embed=embed, view=view)

    async def play_next(self, ctx, voice):
        """Play the next song in queue"""
        # Check if voice is still connected
        if not voice or not voice.is_connected():
            print("Voice client disconnected, cannot continue playing")
            return
            
        if ctx.guild.id not in self.queue or not self.queue[ctx.guild.id]:
            # Auto-play mode: If queue is empty, try to get more recommendations
            if hasattr(self, 'auto_play_mode') and ctx.guild.id in getattr(self, 'auto_play_mode', {}):
                last_played = getattr(self, 'auto_play_mode', {}).get(ctx.guild.id)
                if last_played:
                    print(f"Auto-play mode: Getting recommendations for {last_played}")
                    new_recommendations = await self.get_youtube_recommendations(last_played)
                    if new_recommendations:
                        # Initialize queue if it doesn't exist
                        if ctx.guild.id not in self.queue:
                            self.queue[ctx.guild.id] = []
                        for rec in new_recommendations[:5]:  # Add 5 more songs for better continuity
                            self.queue[ctx.guild.id].append((rec['title'], rec['webpage_url']))
                        print(f"Auto-play: Added {len(new_recommendations)} recommendations")
                        # Continue playing
                        if self.queue[ctx.guild.id]:
                            await self.play_next(ctx, voice)
                    else:
                        print("Auto-play: No recommendations found, stopping")
            return

        title, url = self.queue[ctx.guild.id].pop(0)
        self.current_song[ctx.guild.id] = title

        # Track for auto-play mode
        if not hasattr(self, 'auto_play_mode'):
            self.auto_play_mode = {}
        if ctx.guild.id in getattr(self, 'auto_play_mode', {}):
            self.auto_play_mode[ctx.guild.id] = url

        # Get audio source with multiple fallback methods and bot detection avoidance
        ydl_opts_play = {
            'format': 'bestaudio[ext=m4a]/bestaudio[ext=webm]/bestaudio/best',
            'quiet': True,
            'no_warnings': True,
            'extractaudio': False,
            'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
            'restrictfilenames': True,
            'noplaylist': True,
            'nocheckcertificate': True,
            'ignoreerrors': True,
            'logtostderr': False,
            'age_limit': 18,
            'default_search': 'auto',
            'cookiefile': None,
            'extractor_args': {
                'youtube': {
                    'skip': ['dash', 'hls'],
                    'player_client': ['android', 'web']
                }
            },
            'user_agent': 'Mozilla/5.0 (Linux; Android 11; SM-G973F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.120 Mobile Safari/537.36',
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Linux; Android 11; SM-G973F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.120 Mobile Safari/537.36',
                'Accept': '*/*',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Origin': 'https://www.youtube.com',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Sec-Fetch-Dest': 'empty',
                'Sec-Fetch-Mode': 'cors',
                'Sec-Fetch-Site': 'same-origin',
            }
        }

        audio_url = None
        duration = 0
        thumbnail = ''

        # Try multiple extraction methods
        extraction_methods = [ydl_opts_play]

        for i, opts in enumerate(extraction_methods):
            try:
                with yt_dlp.YoutubeDL(opts) as ydl:
                    info = ydl.extract_info(url, download=False)

                    # Get the best audio format
                    if 'formats' in info:
                        for format in info['formats']:
                            if format.get('acodec') != 'none' and format.get('url'):
                                audio_url = format['url']
                                break

                    if not audio_url and 'url' in info:
                        audio_url = info['url']

                    if audio_url:
                        duration = info.get('duration', 0)
                        thumbnail = info.get('thumbnail', '')
                        break

            except Exception as extraction_error:
                print(f"Extraction method {i+1} failed: {str(extraction_error)}")
                continue

        if not audio_url:
            raise Exception("Could not extract audio URL from any method")

        try:
            # Enhanced FFmpeg options with multiple fallbacks
            ffmpeg_options_list = [
                {
                    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5 -nostdin -user_agent "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"',
                    'options': '-vn -filter:a "volume=0.5"'
                },
                {
                    'before_options': '-nostdin',
                    'options': '-vn'
                },
                {}  # No options fallback
            ]

            source = None
            for i, ffmpeg_options in enumerate(ffmpeg_options_list):
                try:
                    if ffmpeg_options:
                        source = discord.FFmpegPCMAudio(audio_url, **ffmpeg_options)
                    else:
                        source = discord.FFmpegPCMAudio(audio_url)
                    break
                except Exception as ffmpeg_error:
                    print(f"FFmpeg method {i+1} failed: {str(ffmpeg_error)}")
                    continue

            if not source:
                raise Exception("Could not create audio source with any FFmpeg options")

            # Play audio
            voice.play(source, after=lambda e: asyncio.run_coroutine_threadsafe(self.play_next(ctx, voice), self.bot.loop))

            # Now playing embed
            embed = discord.Embed(
                title="🎵 Now Playing",
                description=f"**{title}**",
                color=0x1DB954
            )
            embed.add_field(name="Duration", value=f"{duration//60}:{duration%60:02d}" if duration else "Unknown", inline=True)
            embed.add_field(name="Remaining", value=f"{len(self.queue[ctx.guild.id])} songs", inline=True)
            embed.add_field(name="Requested by", value=ctx.author.mention, inline=True)

            if thumbnail:
                embed.set_thumbnail(url=thumbnail)
            embed.set_footer(text="🎵 Use the buttons below to control playback • Mobile optimized")

            view = MusicControls(self.bot)
            await ctx.edit(embed=embed, view=view)

        except Exception as e:
            error_msg = str(e)
            print(f"Playback error for {title}: {error_msg}")

            # Provide user-friendly error messages
            if "Sign in to confirm you're not a bot" in error_msg or "not a bot" in error_msg.lower():
                user_error = "YouTube is temporarily blocking requests. Skipping to next song..."
            elif "Video unavailable" in error_msg:
                user_error = "This video is not available. It may be region-locked or private."
            elif "Private video" in error_msg:
                user_error = "This video is private and cannot be played."
            elif "HTTP Error 429" in error_msg:
                user_error = "Rate limited by YouTube. Please wait a moment before trying again."
            else:
                user_error = f"Playback failed: {error_msg[:80]}..."

            error_embed = discord.Embed(
                title="❌ Playback Error",
                description=f"Could not play: **{title}**\n\n**Issue:** {user_error}",
                color=0xFF0000
            )

            # Check if there are more songs in queue
            if self.queue[ctx.guild.id]:
                error_embed.add_field(
                    name="🔄 Auto-Skip",
                    value=f"Trying next song... ({len(self.queue[ctx.guild.id])} remaining)",
                    inline=False
                )
                await ctx.edit(embed=error_embed)

                # Wait a moment before trying next song
                await asyncio.sleep(3)
                await self.play_next(ctx, voice)
            else:
                error_embed.add_field(
                    name="💡 Suggestion",
                    value="Try searching for a different song or check if the video is publicly available.",
                    inline=False
                )
                await ctx.edit(embed=error_embed)

                # Disconnect after error if no more songs
                if voice and voice.is_connected():
                    await asyncio.sleep(5)
                    await voice.disconnect()

    @slash_command(description="📝 View the music queue with interactive navigation")
    async def queue(self, ctx):
        """Display music queue with pagination"""
        try:
            if ctx.guild.id not in self.queue or not self.queue[ctx.guild.id]:
                embed = discord.Embed(
                    title="📝 Queue Empty",
                    description="No songs in the queue! Use `/play` to add some music.",
                    color=0xFF0000
                )
                await ctx.respond(embed=embed)
                return

            view = QueueView(self.bot, ctx.guild.id)
            embed = view.create_queue_embed()
            await ctx.respond(embed=embed, view=view)
        except discord.NotFound:
            # Interaction already responded to or expired
            pass
        except Exception as e:
            print(f"Queue command error: {e}")
            try:
                await ctx.respond("❌ An error occurred while displaying the queue!", ephemeral=True)
            except:
                pass

    @slash_command(description="⏹️ Stop music and clear queue")
    async def stop(self, ctx):
        """Stop music with confirmation"""
        voice = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
        if voice:
            if ctx.guild.id in self.queue:
                self.queue[ctx.guild.id].clear()
            await voice.disconnect()

            embed = discord.Embed(
                title="⏹️ Music Stopped",
                description="Music stopped, queue cleared, and disconnected from voice channel.",
                color=0xFF0000
            )
            await ctx.respond(embed=embed)
        else:
            embed = discord.Embed(
                title="❌ Not Connected",
                description="Bot is not connected to a voice channel!",
                color=0xFF0000
            )
            await ctx.respond(embed=embed)

    @slash_command(description="🗑️ Remove a song from the queue")
    async def remove(self, ctx, position: Option(int, "Position of song to remove (starting from 1)")):
        """Remove song from queue by position"""
        if ctx.guild.id not in self.queue or not self.queue[ctx.guild.id]:
            embed = discord.Embed(
                title="❌ Queue Empty",
                description="No songs in the queue to remove!",
                color=0xFF0000
            )
            await ctx.respond(embed=embed)
            return

        if position < 1 or position > len(self.queue[ctx.guild.id]):
            embed = discord.Embed(
                title="❌ Invalid Position",
                description=f"Please provide a position between 1 and {len(self.queue[ctx.guild.id])}",
                color=0xFF0000
            )
            await ctx.respond(embed=embed)
            return

        removed_song = self.queue[ctx.guild.id].pop(position - 1)
        embed = discord.Embed(
            title="🗑️ Song Removed",
            description=f"Removed **{removed_song[0]}** from position {position}",
            color=0x00FF00
        )
        embed.add_field(name="Remaining Songs", value=f"{len(self.queue[ctx.guild.id])} in queue", inline=True)
        await ctx.respond(embed=embed)

    async def get_youtube_recommendations(self, video_url):
        """Get YouTube recommendations based on a video URL with improved error handling"""
        try:
            # Enhanced options to avoid bot detection
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'extractflat': False,
                'nocheckcertificate': True,
                'ignoreerrors': True,
                'cookiefile': None,
                'extractor_args': {
                    'youtube': {
                        'skip': ['dash', 'hls'],
                        'player_client': ['android', 'web']
                    }
                },
                'user_agent': 'Mozilla/5.0 (Linux; Android 11; SM-G973F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.120 Mobile Safari/537.36',
                'http_headers': {
                    'User-Agent': 'Mozilla/5.0 (Linux; Android 11; SM-G973F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.120 Mobile Safari/537.36',
                    'Accept-Language': 'en-US,en;q=0.5',
                    'Accept-Encoding': 'gzip, deflate'
                }
            }

            related_videos = []
            
            # Method 1: Try to extract video info for recommendations
            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(video_url, download=False)
                    
                    # Check if we have title and uploader info
                    if info and 'title' in info:
                        title = info['title']
                        uploader = info.get('uploader', '')
                        
                        # Method 2: Search for similar content based on title and uploader
                        if title:
                            # Create more refined search queries
                            search_queries = []
                            
                            # Extract key words from title (remove common words)
                            title_words = title.lower().split()
                            common_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', '-', 'official', 'video', 'music', 'ft', 'feat', 'featuring'}
                            key_words = [word for word in title_words if word not in common_words and len(word) > 2]
                            
                            if key_words:
                                # Use key words for better search
                                search_queries.append(' '.join(key_words[:3]))  # Top 3 key words
                                
                            if uploader:
                                search_queries.append(f"{uploader}")
                                
                            # Fallback searches
                            search_queries.append(f"{title[:30]}")  # First 30 chars of title
                            
                            # Try each search query
                            for query in search_queries[:2]:  # Limit to 2 searches
                                try:
                                    await asyncio.sleep(0.5)  # Small delay to avoid rate limiting
                                    search_info = ydl.extract_info(f"ytsearch3:{query}", download=False)
                                    if search_info and 'entries' in search_info:
                                        for entry in search_info['entries']:
                                            if (entry and 'webpage_url' in entry and 
                                                entry['webpage_url'] != video_url and 
                                                entry.get('title')):  # Don't recommend the same video and ensure title exists
                                                related_videos.append({
                                                    'title': entry['title'],
                                                    'webpage_url': entry['webpage_url'],
                                                    'uploader': entry.get('uploader', 'Unknown')
                                                })
                                                if len(related_videos) >= 5:
                                                    break
                                except Exception as search_error:
                                    print(f"Search query '{query}' failed: {search_error}")
                                    continue

                                if len(related_videos) >= 5:
                                    break
                                    
            except Exception as info_error:
                print(f"Info extraction failed: {info_error}")
                
            # Method 3: Fallback generic music search if no recommendations found
            if not related_videos:
                try:
                    fallback_queries = ['popular music 2024', 'trending songs', 'top hits']
                    for query in fallback_queries[:1]:  # Just try one fallback
                        try:
                            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                                search_info = ydl.extract_info(f"ytsearch3:{query}", download=False)
                                if search_info and 'entries' in search_info:
                                    for entry in search_info['entries']:
                                        if (entry and 'webpage_url' in entry and 
                                            entry.get('title')):
                                            related_videos.append({
                                                'title': entry['title'],
                                                'webpage_url': entry['webpage_url'],
                                                'uploader': entry.get('uploader', 'Unknown')
                                            })
                                            if len(related_videos) >= 3:  # Less for fallback
                                                break
                        except Exception as fallback_error:
                            print(f"Fallback search failed: {fallback_error}")
                            break
                except Exception as fallback_method_error:
                    print(f"Fallback method failed: {fallback_method_error}")

            return related_videos[:5]  # Return max 5 recommendations

        except Exception as e:
            print(f"Recommendation error: {e}")
            return []

    @slash_command(description="🎲 Auto-play with YouTube recommendations")
    async def auto_play(self, ctx, *, seed_query: Option(str, "Starting song or search term for recommendations")):
        """Auto-play system with YouTube recommendations"""

        # Check dependencies first
        deps_ready, deps_message = check_voice_dependencies()
        if not deps_ready:
            embed = discord.Embed(
                title="❌ Voice Dependencies Missing",
                description=f"{deps_message}\n\nMusic functionality is currently unavailable.",
                color=0xFF0000
            )
            await ctx.respond(embed=embed)
            return

        # Check if user is in voice channel with proper error handling
        if not ctx.author.voice or not ctx.author.voice.channel:
            embed = discord.Embed(
                title="❌ Voice Channel Required",
                description="You need to join a voice channel first!",
                color=0xFF0000
            )
            await ctx.respond(embed=embed)
            return

        # Loading embed
        loading_embed = discord.Embed(
            title="🎲 Auto-Play Starting...",
            description=f"Finding **{seed_query}** and getting recommendations...",
            color=0x9B59B6
        )
        await ctx.respond(embed=loading_embed)

        # Search for the seed song with enhanced bot detection avoidance
        ydl_opts = {
            'format': 'bestaudio[ext=m4a]/bestaudio[ext=webm]/bestaudio/best',
            'quiet': True,
            'no_warnings': True,
            'extractflat': False,
            'nocheckcertificate': True,
            'ignoreerrors': True,
            'default_search': 'ytsearch',
            'extract_flat': False,
            'age_limit': 18,
            'cookiefile': None,
            'extractor_args': {
                'youtube': {
                    'skip': ['dash', 'hls'],
                    'player_client': ['android', 'web']
                }
            },
            'user_agent': 'Mozilla/5.0 (Linux; Android 11; SM-G973F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.120 Mobile Safari/537.36',
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Linux; Android 11; SM-G973F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.120 Mobile Safari/537.36',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate'
            }
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                if 'youtube.com' in seed_query or 'youtu.be' in seed_query:
                    info = ydl.extract_info(seed_query, download=False)
                else:
                    search_query = f"ytsearch:{seed_query}"
                    info = ydl.extract_info(search_query, download=False)
                    info = info['entries'][0]

                seed_title = info['title']
                seed_url = info['webpage_url']
                duration = info.get('duration', 0)
                thumbnail = info.get('thumbnail', '')

        except Exception as e:
            error_embed = discord.Embed(
                title="❌ Auto-Play Failed",
                description=f"Could not find: **{seed_query}**\n\nError: {str(e)}",
                color=0xFF0000
            )
            await ctx.edit(embed=error_embed)
            return

        # Connect to voice channel
        voice_channel = ctx.author.voice.channel
        voice = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)

        try:
            if not voice:
                voice = await voice_channel.connect()
            elif voice.channel != voice_channel:
                await voice.move_to(voice_channel)
        except Exception as e:
            error_embed = discord.Embed(
                title="❌ Voice Connection Failed",
                description=f"Could not connect to voice channel: {str(e)}",
                color=0xFF0000
            )
            await ctx.edit(embed=error_embed)
            return

        # Initialize queue if not exists
        if ctx.guild.id not in self.queue:
            self.queue[ctx.guild.id] = []

        # Clear existing queue for auto-play mode
        self.queue[ctx.guild.id].clear()

        # Add seed song to queue
        self.queue[ctx.guild.id].append((seed_title, seed_url))
        
        # Enable auto-play mode for this guild
        if not hasattr(self, 'auto_play_mode'):
            self.auto_play_mode = {}
        self.auto_play_mode[ctx.guild.id] = seed_url

        # Get recommendations based on the seed song
        update_embed = discord.Embed(
            title="🎲 Getting Recommendations...",
            description=f"Added **{seed_title}** to queue\nFinding similar songs...\n\n🎲 **Auto-play mode activated!**",
            color=0x9B59B6
        )
        await ctx.edit(embed=update_embed)

        recommendations = await self.get_youtube_recommendations(seed_url)

        # Add recommendations to queue
        for rec in recommendations:
            self.queue[ctx.guild.id].append((rec['title'], rec['webpage_url']))

        # Start playing
        if not voice.is_playing() and not voice.is_paused():
            await self.play_next(ctx, voice)

        # Auto-play started embed
        embed = discord.Embed(
            title="🎲 Auto-Play Started!",
            description=f"**Now Playing:** {seed_title}\n\n**Recommendations Added:** {len(recommendations)} songs",
            color=0x9B59B6
        )
        embed.add_field(name="Queue Length", value=f"{len(self.queue[ctx.guild.id])} songs", inline=True)
        embed.add_field(name="Mode", value="🎲 Auto-Play", inline=True)
        embed.add_field(name="Based on", value=f"**{seed_title}**", inline=True)

        if thumbnail:
            embed.set_thumbnail(url=thumbnail)

        # Show some recommendations
        if recommendations:
            rec_list = "\n".join([f"• {rec['title'][:40]}{'...' if len(rec['title']) > 40 else ''}" for rec in recommendations[:3]])
            embed.add_field(name="🎵 Coming Up", value=rec_list, inline=False)

        embed.set_footer(text="🎲 Auto-Play will continue with recommendations • Use buttons to control")

        view = MusicControls(self.bot)
        await ctx.edit(embed=embed, view=view)

def setup(bot):
    """Setup function that never fails"""
    try:
        music_cog = Music(bot)
        bot.add_cog(music_cog)
        print("✅ Music cog loaded successfully")
        print("  ↳ Dependencies will be checked when commands are used")
    except Exception as e:
        print(f"⚠️ Music cog failed to load: {e}")
        # Don't raise the exception to prevent bot startup failure