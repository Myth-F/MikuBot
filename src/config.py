import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


@dataclass
class Config:
    discord_token: str
    fish_api_key: str
    fish_model_id: str
    max_message_length: int = 150
    cache_dir: str = "cache"

    @classmethod
    def from_env(cls) -> "Config":
        return cls(
            discord_token=os.environ["DISCORD_TOKEN"],
            fish_api_key=os.environ["FISH_API_KEY"],
            fish_model_id=os.environ.get("FISH_MODEL_ID", ""),
            max_message_length=int(os.environ.get("MAX_MESSAGE_LENGTH", "150")),
            cache_dir=os.environ.get("CACHE_DIR", "cache"),
        )
