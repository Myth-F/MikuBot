FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for discord.py voice support. We want to send voice clips
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files
COPY pyproject.toml .

# Install Python dependencies
RUN pip install --no-cache-dir .

# Copy application code
COPY src/ ./src/

# Run the bot
CMD ["python", "-m", "src.bot"]
