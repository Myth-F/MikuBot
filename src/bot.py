import logging

import discord
from discord import app_commands
from discord.ext import commands

from .config import Config
from .tts import TTSService

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("mikubot")


def create_bot(config: Config) -> commands.Bot:
    logger.info("Creating bot...")
    intents = discord.Intents.default()
    intents.message_content = True

    bot = commands.Bot(command_prefix="!", intents=intents)
    logger.info("Initializing TTS service...")
    tts = TTSService(config.fish_api_key, config.fish_model_id, config.cache_dir)
    logger.info("TTS service initialized")

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
            await interaction.followup.send(file=discord.File(audio_path))
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
