<div align="center">
  <h1>MikuBot</h1>
  <p><strong>Make Hatsune Miku speak directly inside Discord.</strong></p>

  <p>
    <a href="https://github.com/Myth-F/MikuBot"><img alt="GitHub" src="https://img.shields.io/badge/GitHub-Myth--F%2FMikuBot-181717?logo=github" /></a>
    <img alt="Python" src="https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white" />
    <img alt="Discord" src="https://img.shields.io/badge/Discord.py-2.4+-5865F2?logo=discord&logoColor=white" />
    <img alt="Fish Audio" src="https://img.shields.io/badge/TTS-Fish_Audio-00AFA5" />
    <img alt="Docker" src="https://img.shields.io/badge/Docker-ready-2496ED?logo=docker&logoColor=white" />
  </p>

  <p>
    <a href="#quick-start">Quick start</a>
    ·
    <a href="#usage">Usage</a>
    ·
    <a href="#configuration">Configuration</a>
    ·
    <a href="#how-it-works">How it works</a>
  </p>
</div>

---

## About

MikuBot is a Discord bot that turns a short message into a voice clip through Fish Audio. It accompanies the audio file with a Hatsune Miku image captioned with the requested text.

Generated audio is cached to avoid synthesizing the same message twice.

## Features

- simple `/miku` slash command;
- text-to-speech through Fish Audio;
- local or remotely fetched Miku images;
- automatic text overlay;
- image-aware text sizing and wrapping;
- local MP3 cache;
- configurable message length limit;
- containerized runtime with Discord voice dependencies.

## Usage

In a server where the bot is installed:

```text
/miku text: Hello everyone!
```

The bot responds with:

1. an MP3 clip generated with the configured voice;
2. a captioned Miku image.

If image generation fails, the audio clip is still sent.

## Quick start

### Requirements

- an application in the [Discord Developer Portal](https://discord.com/developers/applications);
- a Fish Audio API key and voice model;
- Docker and Docker Compose.

Clone and configure the project:

```bash
git clone https://github.com/Myth-F/MikuBot.git
cd MikuBot
cp .env.example .env
```

Set at least `DISCORD_TOKEN`, `FISH_API_KEY`, and `FISH_MODEL_ID`, then run:

```bash
docker compose up --build -d
docker compose logs -f mikubot
```

The `cache/` directory is mounted into the container so clips survive restarts.

> Never commit `.env`, your Discord token, or your Fish Audio key.

## Configuration

| Variable | Description | Default |
| --- | --- | --- |
| `DISCORD_TOKEN` | Secret Discord bot token | required |
| `FISH_API_KEY` | Fish Audio API key | required |
| `FISH_MODEL_ID` | Voice model identifier | required for the target voice |
| `MAX_MESSAGE_LENGTH` | Maximum message length | `150` |
| `CACHE_DIR` | Generated clip directory | `cache` |
| `MIKU_IMAGE_DIR` | Optional local image directory | — |
| `MIKU_IMAGE_API_URLS` | Comma-separated image API list | built-in providers |
| `MIKU_IMAGE_API_URL` | Single fallback image provider | — |
| `MIKU_FONT_PATH` | TTF font used for captions | system font |

Local PNG, JPEG, and WebP images take priority over remote providers.

## How it works

```text
Discord command
      │
      ├──► Fish Audio ──► MP3 clip ──► cache/
      │
      └──► local image or API ──► Pillow composition
                                   │
                                   ▼
                            Discord response
```

```text
src/
├── bot.py            # Bot and /miku command
├── config.py         # Environment loading
├── tts.py            # Audio generation and cache
├── image_service.py  # Image selection and composition
└── __main__.py       # Python entry point
```

## Local development

Python 3.11 and FFmpeg are required:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
python -m src
```

Available quality commands:

```bash
ruff check .
pytest
```

## Disclaimer

This project is not affiliated with Crypton Future Media. Follow the applicable rights and terms of service for every voice, model, image, and provider you configure.
