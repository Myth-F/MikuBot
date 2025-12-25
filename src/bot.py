import logging

import discord
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

    @bot.command(name="miku")
    async def miku_speak(ctx: commands.Context, *, text: str):
        """Generate a Miku voice clip from text."""
        if len(text) > config.max_message_length:
            await ctx.reply(
                f"Message trop long ! Max {config.max_message_length} caractères."
            )
            return

        async with ctx.typing():
            try:
                audio_path = await tts.generate(text)
                await ctx.reply(file=discord.File(audio_path))
            except Exception as e:
                await ctx.reply(f"Erreur lors de la génération : {e}")

    @bot.command(name="mikuvc")
    async def miku_voice(ctx: commands.Context, *, text: str):
        """Generate and play Miku voice in voice channel."""
        if not ctx.author.voice:
            await ctx.reply("Tu dois être dans un salon vocal !")
            return

        if len(text) > config.max_message_length:
            await ctx.reply(
                f"Message trop long :/ Max {config.max_message_length} caractères."
            )
            return

        async with ctx.typing():
            try:
                audio_path = await tts.generate(text)

                vc = ctx.voice_client
                if not vc:
                    vc = await ctx.author.voice.channel.connect()

                vc.play(discord.FFmpegPCMAudio(str(audio_path)))

                while vc.is_playing():
                    await discord.utils.sleep_until(discord.utils.utcnow())

                await vc.disconnect()
            except Exception as e:
                await ctx.reply(f"Erreur : {e}")

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
