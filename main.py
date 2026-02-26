import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
import logging
import asyncio

# Setup basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(name)s - %(message)s')

# Load environment variables
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

# Initialize Bot
intents = discord.Intents.default()
intents.message_content = True  # Required for reading commands if not using slash exclusively
intents.voice_states = True     # Required for voice channel support

bot = commands.Bot(command_prefix=os.getenv('CMD_PREFIX', '!'), intents=intents)

@bot.event
async def on_ready():
    logging.info(f'Logged in as {bot.user.name} ({bot.user.id})')
    logging.info('------')
    # Sync slash commands
    try:
        synced = await bot.tree.sync()
        logging.info(f"Synced {len(synced)} command(s)")
    except Exception as e:
        logging.error(f"Failed to sync commands: {e}")

async def load_extensions():
    # Load cogs
    for filename in os.listdir('./cogs'):
        if filename.endswith('.py'):
            await bot.load_extension(f'cogs.{filename[:-3]}')
            logging.info(f'Loaded cog: {filename}')

async def main():
    if not TOKEN or TOKEN == "your_bot_token_here_do_not_share":
        logging.error("No valid DISCORD_TOKEN found in environment variables. Please check your .env file.")
        return
        
    async with bot:
        # Create cogs dir if it doesn't exist
        os.makedirs('./cogs', exist_ok=True)
        await load_extensions()
        await bot.start(TOKEN)

if __name__ == "__main__":
    asyncio.run(main())
