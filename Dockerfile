FROM python:3.11-slim

# Install ffmpeg, nodejs (for yt-dlp JS execution), and required system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg curl nodejs && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install them
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy bot source code
COPY . /app/

# Run the bot
CMD ["python", "main.py"]
