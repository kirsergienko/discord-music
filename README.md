# Discord Music Bot 🎵

A robust, easy-to-deploy Discord music bot built using `discord.py` and `yt-dlp`. It supports playing audio from YouTube, maintaining a queue, and common player controls (pause, resume, skip).

## Features

- **High Reliability**: Uses `yt-dlp` to bypass standard playback blocks.
- **Easy Deployment**: Fully dockerized. No need to install FFmpeg or Python manually!
- **Slash Commands**: Modern Discord slash commands (`/play`, `/pause`, etc.)

## 🚀 Easy Deployment (Docker)

The absolute easiest way to deploy this bot is via Docker.

### Prerequisites
- [Docker](https://docs.docker.com/get-docker/) installed.
- [Docker Compose](https://docs.docker.com/compose/install/) installed.

### Setup

1. Rename `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   # or just rename it in your file explorer
   ```
2. Open `.env` and paste your Bot Token from the [Discord Developer Portal](https://discord.com/developers/applications).
3. Ensure your bot has the **Message Content Intent** enabled in the Developer Portal.
4. **YouTube Bot Protection Bypass (Cookies):** YouTube blocks generic server traffic. For the bot to play videos effectively, you should export your YouTube cookies:
   - Install a browser extension like [Get cookies.txt LOCALLY](https://chrome.google.com/webstore/detail/get-cookiestxt-locally/ccpbcjhkecglkamamajpjjoaleodaqhk) for Chrome or Firefox.
   - Go to YouTube.com (make sure you're logged in).
   - Click the extension and export the cookies. Save the file exactly as `cookies.txt` inside the `discord-music` folder alongside the bot code.

### Run

```bash
docker compose up -d
```

That's it! The bot is now running in the background.

To view logs:
```bash
docker logs -f discord-music-bot
```

To stop:
```bash
docker compose down
```

## 💻 Manual Local Deployment

If you prefer running without Docker:

1. Install Python 3.10+
2. Install [FFmpeg](https://ffmpeg.org/download.html) and ensure it's in your system PATH.
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Setup your `.env` file as described above.
5. Run the bot:
   ```bash
   python main.py
   ```

## Commands

- `/join`: Joins your active voice channel.
- `/play <url or search_term>`: Plays a song from YouTube or adds it to the queue.
- `/pause`: Pauses currently playing music.
- `/resume`: Resumes paused music.
- `/skip`: Skips to the next song in the queue.
- `/queue`: Displays the current music queue.
- `/stop`: Stops music, clears queue, and disconnects the bot.
