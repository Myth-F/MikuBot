import discord
from discord.ext import commands

from .config import Config
from .tts import TTSService


def create_bot(config: Config) -> commands.Bot:
    intents = discord.Intents.default()
    intents.message_content = True

    bot = commands.Bot(command_prefix="!", intents=intents)
    tts = TTSService(config.fish_api_key, config.fish_model_id, config.cache_dir)

    @bot.event
    async def on_ready():
        print(f"MikuBot connected as {bot.user}")

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
    config = Config.from_env()
    bot = create_bot(config)
    bot.run(config.discord_token)


if __name__ == "__main__":
    main()
