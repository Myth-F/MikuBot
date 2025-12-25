FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for discord.py voice support
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libffi-dev \
    libsodium-dev \
    libopus0 \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files
COPY pyproject.toml .

# Install Python dependencies
RUN pip install --no-cache-dir .

COPY src/ ./src/

CMD ["python", "-m", "src.bot"]
