from pathlib import Path
from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache

ENV_FILE = Path(__file__).resolve().parent.parent / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ENV_FILE, extra="ignore")

    openai_api_key: SecretStr
    openai_model: str = "gpt-6-luna"
    openai_timeout: float = 30.0


@lru_cache
def get_settings() -> Settings:
    return Settings()
