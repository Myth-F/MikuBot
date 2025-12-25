import os
import sys
from dataclasses import dataclass


@dataclass
class Config:
    discord_token: str
    fish_api_key: str
    fish_model_id: str
    max_message_length: int = 150
    cache_dir: str = "cache"

    @classmethod
    def from_env(cls) -> "Config":
        discord_token = os.environ.get("DISCORD_TOKEN")
        fish_api_key = os.environ.get("FISH_API_KEY")

        missing = []
        if not discord_token:
            missing.append("DISCORD_TOKEN")
        if not fish_api_key:
            missing.append("FISH_API_KEY")

        if missing:
            print(f"ERROR: Missing required environment variables: {', '.join(missing)}")
            sys.exit(1)

        return cls(
            discord_token=discord_token,
            fish_api_key=fish_api_key,
            fish_model_id=os.environ.get("FISH_MODEL_ID", ""),
            max_message_length=int(os.environ.get("MAX_MESSAGE_LENGTH", "150")),
            cache_dir=os.environ.get("CACHE_DIR", "cache"),
        )
