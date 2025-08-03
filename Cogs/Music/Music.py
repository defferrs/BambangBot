import discord
from discord.ext import commands
from discord.commands import slash_command
import youtube_dl
import os 
import asyncio
import time
import datetime
import random
import string
import pyffmpeg
import ffmpeg

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.voice_clients = {}
        self.music_queue = {}
        self.play_next_song = asyncio.Event()
        self.play_next_song.set()

    async def play_song(self, ctx, song):
        source = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(song))

        ctx.voice_client.play(source, after=lambda e: self.bot.loop.call_soon_threadsafe(self.play_next_song.set))

        ctx.voice_client.source = discord.PCMVolumeTransformer(ctx.voice_client.source)

        ctx.voice_client.source.volume = 0.5

        await ctx.respond(f"Now playing: {song}")

        await self.play_next_song.wait()

        self.play_next_song.clear()

        if ctx.voice_client.is_playing():
            return
        if not self.music_queue[ctx.guild.id]:
            await ctx.voice_client.disconnect()
            return
        await self.play_song(ctx, self.music_queue[ctx.guild.id].pop(0))

    @slash_command()
    async def play(self, ctx, url: str):
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

        self.music_queue[ctx.guild.id].append(url)

        await ctx.respond(f"Ditambahkan ke antrian: {url}")
        if not ctx.voice_client.is_playing():
            await self.play_song(ctx, self.music_queue[ctx.guild.id].pop(0))

    @slash_command()
    async def stop(self, ctx):
        if ctx.voice_client:
            await ctx.voice_client.disconnect()
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
            queue_list = "\n".join([f"{i+1}. {song}" for i, song in enumerate(self.music_queue[ctx.guild.id])])
            await ctx.respond(f"Antrian:\n{queue_list}")
        else:
            await ctx.respond("Antrian kosong.")

    @slash_command()
    async def autoplay(self, ctx):
        if ctx.voice_client and ctx.voice_client.is_playing():
            await ctx.respond("Autoplay telah diaktifkan")

            while True:
                if not ctx.voice_client.is_playing():
                    if not self.music_queue[ctx.guild.id]:
                        await ctx.voice_client.disconnect()
                        return
                    await self.play_song(ctx, self.music_queue[ctx.guild.id].pop(0))
                    await self.play_next_song.wait()
                    self.play_next_song.clear()
        else:
            await ctx.respond("Tidak ada lagu yang sedang diputar.")

    @slash_command()
    async def move(self, ctx, channel: discord.VoiceChannel):
        if ctx.voice_client:
            await ctx.voice_client.move_to(channel)
            await ctx.respond(f"Bot telah dipindahkan ke {channel.name}")
        else:
            await ctx.respond("Bot tidak sedang berada di voice channel.")

    @slash_command()
    async def movesong(self, ctx, position: int, new_position: int):
        if ctx.guild.id not in self.music_queue:
            self.music_queue[ctx.guild.id] = []

        if position < 1 or position > len(self.music_queue[ctx.guild.id]) or new_position < 1 or new_position > len(self.music_queue[ctx.guild.id]):
            await ctx.respond("Posisi tidak valid.")
            return
        if self.music_queue[ctx.guild.id]:
            song = self.music_queue[ctx.guild.id].pop(position - 1)
            self.music_queue[ctx.guild.id].insert(new_position - 1, song)
            await ctx.respond(f"Lagu telah dipindahkan dari posisi {position} ke posisi {new_position}.")
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
    async def repeat(self, ctx):
        if ctx.voice_client and ctx.voice_client.is_playing():
            if ctx.guild.id in self.music_queue and self.music_queue[ctx.guild.id]:
                current_song = self.music_queue[ctx.guild.id][0]
                self.music_queue[ctx.guild.id].insert(0, current_song)
                await ctx.respond("Lagu akan diulang.")
            else:
                await ctx.respond("Tidak ada lagu dalam antrian.")
        else:
            await ctx.respond("Tidak ada lagu yang sedang diputar.")

    @slash_command()
    async def loop(self, ctx):
        if ctx.voice_client and ctx.voice_client.is_playing():
            if ctx.guild.id in self.music_queue and self.music_queue[ctx.guild.id]:
                current_song = self.music_queue[ctx.guild.id][0]
                self.music_queue[ctx.guild.id].insert(0, current_song)
                await ctx.respond("Lagu akan diputar secara berulang.")
            else:
                await ctx.respond("Tidak ada lagu dalam antrian.")
        else:
            await ctx.respond("Tidak ada lagu yang sedang diputar.")

    @slash_command()
    async def remove(self, ctx, position: int):
        if ctx.guild.id not in self.music_queue:
            self.music_queue[ctx.guild.id] = []

        if position < 1 or position > len(self.music_queue[ctx.guild.id]):
            await ctx.respond("Posisi tidak valid.")
            return
        if self.music_queue[ctx.guild.id]:
            removed_song = self.music_queue[ctx.guild.id].pop(position - 1)
            await ctx.respond(f"Lagu {removed_song} telah dihapus dari antrian.")
        else:
            await ctx.respond("Antrian kosong.")

def setup(bot):
    bot.add_cog(Music(bot))
    print("Music cog loaded")