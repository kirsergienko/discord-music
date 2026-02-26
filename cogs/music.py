import asyncio
import discord
from discord.ext import commands
from discord import app_commands
import yt_dlp
import logging
from collections import deque

logger = logging.getLogger(__name__)

# Suppress noise about console usage from errors
yt_dlp.utils.bug_reports_message = lambda *args, **kwargs: ''

ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0',  # bind to ipv4 since ipv6 addresses cause issues sometimes
}

ffmpeg_options = {
    'options': '-vn',
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5'
}

ytdl = yt_dlp.YoutubeDL(ytdl_format_options)


class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')
        self.url = data.get('url')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=True):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))

        if 'entries' in data:
            # take first item from a playlist
            data = data['entries'][0]

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)


class MusicQueue:
    def __init__(self):
        self.queue = deque()
        self.current = None

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Maps guild IDs to their queues
        self.queues = {}

    def get_queue(self, guild_id):
        if guild_id not in self.queues:
            self.queues[guild_id] = MusicQueue()
        return self.queues[guild_id]

    def play_next(self, ctx):
        queue_state = self.get_queue(ctx.guild.id)
        if len(queue_state.queue) > 0:
            next_song, next_url = queue_state.queue.popleft()
            queue_state.current = next_song
            
            try:
                # We need to recreate the source because Discord closes the stream
                source = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(next_url, **ffmpeg_options))
                # using ctx.voice_client.play and calling next on end
                ctx.voice_client.play(source, after=lambda e: self.play_next(ctx) if e is None else logger.error(f'Player error: {e}'))
                
                # Send message async (need event loop)
                fut = asyncio.run_coroutine_threadsafe(
                    ctx.send(f'Now playing: **{next_song}**'),
                    self.bot.loop
                )
            except Exception as e:
                logger.error(f'Error playing next song: {e}')
                self.play_next(ctx)
        else:
            queue_state.current = None

    @app_commands.command(name="join", description="Joins your voice channel")
    async def join(self, interaction: discord.Interaction):
        if not interaction.user.voice:
            return await interaction.response.send_message("You are not connected to a voice channel.")
        
        channel = interaction.user.voice.channel
        if interaction.guild.voice_client is not None:
            await interaction.guild.voice_client.move_to(channel)
        else:
            await channel.connect()
            
        await interaction.response.send_message(f"Joined {channel.name}")

    @app_commands.command(name="play", description="Plays a song from YouTube (Search or URL)")
    @app_commands.describe(query="The search term or YouTube URL to play")
    async def play(self, interaction: discord.Interaction, query: str):
        # Defers response as downloading takes time
        await interaction.response.defer()
        
        if not interaction.user.voice:
            return await interaction.followup.send("You are not connected to a voice channel.")

        channel = interaction.user.voice.channel
        voice_client = interaction.guild.voice_client

        if voice_client is None:
            voice_client = await channel.connect()

        try:
            # We use typing context manager for visuals, though it's slash command so defer applies
            player = await YTDLSource.from_url(query, loop=self.bot.loop, stream=True)
            
            queue_state = self.get_queue(interaction.guild.id)
            
            if voice_client.is_playing() or voice_client.is_paused():
                queue_state.queue.append((player.title, player.url))
                await interaction.followup.send(f'Added to queue: **{player.title}**')
            else:
                queue_state.current = player.title
                
                # To support after callback with ctx.send, we need a ctx mock or just use send_message
                ctx = await self.bot.get_context(interaction)
                
                voice_client.play(player, after=lambda e: self.play_next(ctx) if e is None else logger.error(f'Player error: {e}'))
                await interaction.followup.send(f'Now playing: **{player.title}**')
                
        except Exception as e:
            import traceback
            traceback_str = ''.join(traceback.format_exception(None, e, e.__traceback__))
            logger.error(f"Error checking out {query}: {e}\n{traceback_str}")
            await interaction.followup.send("An error occurred while trying to play the song. Maybe restricted or private via yt-dlp.")

    @app_commands.command(name="queue", description="Shows the current music queue")
    async def queue(self, interaction: discord.Interaction):
        queue_state = self.get_queue(interaction.guild.id)
        
        if not queue_state.current and len(queue_state.queue) == 0:
            return await interaction.response.send_message("The queue is currently empty.")
            
        embed = discord.Embed(title="Music Queue", color=discord.Color.blue())
        
        if queue_state.current:
            embed.add_field(name="Now Playing", value=f"🎶 **{queue_state.current}**", inline=False)
            
        if len(queue_state.queue) > 0:
            q_list = ""
            for i, (title, _) in enumerate(list(queue_state.queue)[:10]):
                q_list += f"{i+1}. {title}\n"
            
            if len(queue_state.queue) > 10:
                q_list += f"\n*... and {len(queue_state.queue) - 10} more*"
                
            embed.add_field(name="Up Next", value=q_list, inline=False)
            
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="skip", description="Skips the currently playing song")
    async def skip(self, interaction: discord.Interaction):
        voice_client = interaction.guild.voice_client
        if voice_client is None or not voice_client.is_playing():
            return await interaction.response.send_message("Not playing any music right now.")
            
        voice_client.stop()
        # The play_next function is automatically called by the `after` callback of voice_client.play()
        await interaction.response.send_message("⏭️ Skipped!")

    @app_commands.command(name="pause", description="Pauses the music")
    async def pause(self, interaction: discord.Interaction):
        voice_client = interaction.guild.voice_client
        if voice_client is None or not voice_client.is_playing():
             return await interaction.response.send_message("Not playing any music right now.")
             
        voice_client.pause()
        await interaction.response.send_message("⏸️ Paused.")

    @app_commands.command(name="resume", description="Resumes the music")
    async def resume(self, interaction: discord.Interaction):
        voice_client = interaction.guild.voice_client
        if voice_client is None or not voice_client.is_paused():
             return await interaction.response.send_message("Music is not paused.")
             
        voice_client.resume()
        await interaction.response.send_message("▶️ Resumed.")
        
    @app_commands.command(name="stop", description="Stops music and clears the queue")
    async def stop(self, interaction: discord.Interaction):
        voice_client = interaction.guild.voice_client
        if voice_client is None:
            return await interaction.response.send_message("I am not connected to a voice channel.")
            
        queue_state = self.get_queue(interaction.guild.id)
        queue_state.queue.clear()
        queue_state.current = None
        
        voice_client.stop()
        await voice_client.disconnect()
        
        await interaction.response.send_message("⏹️ Stopped and disconnected.")

async def setup(bot):
    await bot.add_cog(Music(bot))
