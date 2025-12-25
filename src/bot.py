import logging
import re

import discord
from discord import app_commands
from discord.ext import commands

from .config import Config
from .image_service import MikuImageService
from .tts import TTSService

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("mikubot")


def _build_filename_prefix(text: str, max_length: int = 32) -> str:
    prefix = text.strip()
    if not prefix:
        return "miku"
    prefix = prefix[:max_length]
    prefix = re.sub(r"\s+", "_", prefix)
    prefix = re.sub(r"[^A-Za-z0-9_-]", "", prefix)
    prefix = prefix.strip("._-")
    return prefix or "miku"


def create_bot(config: Config) -> commands.Bot:
    logger.info("Creating bot...")
    intents = discord.Intents.default()
    intents.message_content = True

    bot = commands.Bot(command_prefix="!", intents=intents)
    logger.info("Initializing TTS service...")
    tts = TTSService(config.fish_api_key, config.fish_model_id, config.cache_dir)
    logger.info("TTS service initialized")
    image_service = MikuImageService(
        config.miku_image_dir,
        config.miku_image_api_url,
        config.miku_font_path,
    )

    @bot.event
    async def on_ready():
        logger.info(f"MikuBot connected as {bot.user}")
        try:
            synced = await bot.tree.sync()
            logger.info(f"Synced {len(synced)} slash commands")
        except Exception as e:
            logger.error(f"Failed to sync commands: {e}")

    @bot.tree.command(name="miku", description="Generate a Miku voice clip from text")
    @app_commands.describe(text="The text for Miku to say")
    async def miku_speak(interaction: discord.Interaction, text: str):
        """Generate a Miku voice clip from text."""
        if len(text) > config.max_message_length:
            await interaction.response.send_message(
                f"Message trop long ! Max {config.max_message_length} caractères.",
                ephemeral=True,
            )
            return

        await interaction.response.defer()
        try:
            audio_path = await tts.generate(text)
            filename_prefix = _build_filename_prefix(text)
            audio_filename = f"{filename_prefix}.mp3"
            audio_file = discord.File(audio_path, filename=audio_filename)
            image_file = None
            try:
                image_bytes = await image_service.generate(text)
                image_filename = f"{filename_prefix}.png"
                image_file = discord.File(image_bytes, filename=image_filename)
            except Exception as image_error:
                logger.warning("Image generation failed: %s", image_error)

            if image_file:
                await interaction.followup.send(files=[audio_file, image_file])
            else:
                await interaction.followup.send(file=audio_file)
        except Exception as e:
            logger.exception(f"Error generating TTS: {e}")
            await interaction.followup.send(f"Erreur lors de la génération : {e}")

    @bot.tree.command(
        name="mikuvc", description="Generate and play Miku voice in voice channel"
    )
    @app_commands.describe(text="The text for Miku to say")
    async def miku_voice(interaction: discord.Interaction, text: str):
        """Generate and play Miku voice in voice channel."""
        if not interaction.user.voice:
            await interaction.response.send_message(
                "Tu dois être dans un salon vocal !", ephemeral=True
            )
            return

        if len(text) > config.max_message_length:
            await interaction.response.send_message(
                f"Message trop long ! Max {config.max_message_length} caractères.",
                ephemeral=True,
            )
            return

        await interaction.response.defer()
        try:
            audio_path = await tts.generate(text)

            vc = interaction.guild.voice_client
            if not vc:
                vc = await interaction.user.voice.channel.connect()

            vc.play(discord.FFmpegPCMAudio(str(audio_path)))

            await interaction.followup.send(f"Playing: {text}")

            while vc.is_playing():
                await discord.utils.sleep_until(discord.utils.utcnow())

            await vc.disconnect()
        except Exception as e:
            logger.exception(f"Error in voice playback: {e}")
            await interaction.followup.send(f"Erreur : {e}")

    return bot


def main():
    logger.info("Starting MikuBot...")
    try:
        config = Config.from_env()
        logger.info("Config loaded successfully")
        bot = create_bot(config)
        logger.info("Bot created, connecting to Discord...")
        bot.run(config.discord_token)
    except Exception as e:
        logger.exception(f"Fatal error: {e}")
        raise


if __name__ == "__main__":
    main()
