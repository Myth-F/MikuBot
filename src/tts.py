import hashlib
import os
from pathlib import Path

from fish_audio_sdk import Session, TTSRequest


class TTSService:
    def __init__(self, api_key: str, model_id: str, cache_dir: str = "cache"):
        self.session = Session(api_key)
        self.model_id = model_id
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)

    def _get_cache_path(self, text: str) -> Path:
        text_hash = hashlib.md5(text.encode()).hexdigest()[:16]
        return self.cache_dir / f"{text_hash}.mp3"

    async def generate(self, text: str) -> Path:
        """Generate TTS audio and return path to the audio file."""
        cache_path = self._get_cache_path(text)

        if cache_path.exists():
            return cache_path

        request = TTSRequest(
            text=text,
            reference_id=self.model_id,
        )

        with open(cache_path, "wb") as f:
            async for chunk in self.session.tts.awaitable(request):
                f.write(chunk)

        return cache_path
