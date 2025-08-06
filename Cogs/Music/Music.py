
import discord
from discord.ext import commands
from discord.commands import slash_command, Option
import asyncio
import random
import yt_dlp
import re
import os
import subprocess
import nacl

class MusicControls(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.button(emoji="⏸️", style=discord.ButtonStyle.secondary, custom_id="pause")
    async def pause_button(self, button: discord.ui.Button, interaction: discord.Interaction):
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

    @discord.ui.button(emoji="▶️", style=discord.ButtonStyle.success, custom_id="resume")
    async def resume_button(self, button: discord.ui.Button, interaction: discord.Interaction):
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

    @discord.ui.button(emoji="⏭️", style=discord.ButtonStyle.primary, custom_id="skip")
    async def skip_button(self, button: discord.ui.Button, interaction: discord.Interaction):
        voice = discord.utils.get(self.bot.voice_clients, guild=interaction.guild)
        if voice and voice.is_playing():
            voice.stop()
            embed = discord.Embed(
                title="⏭️ Song Skipped",
                description="Skipped to the next song in queue!",
                color=0x3498DB
            )
            await interaction.response.edit_message(embed=embed, view=self)
        else:
            await interaction.response.send_message("❌ No music is currently playing!", ephemeral=True)

    @discord.ui.button(emoji="⏹️", style=discord.ButtonStyle.danger, custom_id="stop")
    async def stop_button(self, button: discord.ui.Button, interaction: discord.Interaction):
        voice = discord.utils.get(self.bot.voice_clients, guild=interaction.guild)
        if voice:
            music_cog = self.bot.get_cog('Music')
            if music_cog and hasattr(music_cog, 'queue') and interaction.guild.id in music_cog.queue:
                music_cog.queue[interaction.guild.id].clear()
            await voice.disconnect()
            embed = discord.Embed(
                title="⏹️ Music Stopped",
                description="Music stopped and queue cleared. Disconnected from voice channel.",
                color=0xFF0000
            )
            await interaction.response.edit_message(embed=embed, view=None)
        else:
            await interaction.response.send_message("❌ Bot is not connected to a voice channel!", ephemeral=True)

    @discord.ui.button(emoji="🔀", style=discord.ButtonStyle.secondary, custom_id="shuffle")
    async def shuffle_button(self, button: discord.ui.Button, interaction: discord.Interaction):
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

    @slash_command(description="🎵 Play music from YouTube with interactive controls")
    async def play(self, ctx, *, query: Option(str, "Song name or YouTube URL")):
        """Play music with modern interactive controls"""
        
        # Check if user is in voice channel
        if not ctx.author.voice:
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

        # Search for the song
        ydl_opts = {
            'format': 'bestaudio/best',
            'quiet': True,
            'no_warnings': True,
            'extractflat': False,
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

        # Connect to voice channel
        voice_channel = ctx.author.voice.channel
        voice = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)

        if not voice:
            voice = await voice_channel.connect()
        elif voice.channel != voice_channel:
            await voice.move_to(voice_channel)

        # Initialize queue if not exists
        if ctx.guild.id not in self.queue:
            self.queue[ctx.guild.id] = []

        # Add to queue
        self.queue[ctx.guild.id].append((title, url))

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
        if ctx.guild.id not in self.queue or not self.queue[ctx.guild.id]:
            return

        title, url = self.queue[ctx.guild.id].pop(0)
        self.current_song[ctx.guild.id] = title

        # Get audio source
        ydl_opts = {
            'format': 'bestaudio/best',
            'quiet': True,
            'no_warnings': True,
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                audio_url = info['url']
                duration = info.get('duration', 0)
                thumbnail = info.get('thumbnail', '')

            # Create FFmpeg source
            ffmpeg_options = {
                'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
                'options': '-vn'
            }
            
            source = discord.FFmpegPCMAudio(audio_url, **ffmpeg_options)
            
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
            error_embed = discord.Embed(
                title="❌ Playback Error",
                description=f"Could not play: **{title}**\n\nError: {str(e)}",
                color=0xFF0000
            )
            await ctx.edit(embed=error_embed)
            # Try next song
            if self.queue[ctx.guild.id]:
                await self.play_next(ctx, voice)

    @slash_command(description="📝 View the music queue with interactive navigation")
    async def queue(self, ctx):
        """Display music queue with pagination"""
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

def setup(bot):
    bot.add_cog(Music(bot))
    print("Enhanced Music cog loaded with interactive controls")
