from __future__ import annotations

import os
from functools import lru_cache
from typing import List, Optional

from pydantic import Field, ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict


def _parse_csv(value: Optional[str]) -> List[str]:
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


class Settings(BaseSettings):
    """Application configuration loaded from environment variables.

    Fails fast when required variables are missing.
    """

    model_config = SettingsConfigDict(env_file=None, extra="ignore", populate_by_name=True)

    # Database
    supabase_db_url: str = Field(min_length=1, alias="SUPABASE_DB_URL")

    # CORS (raw CSV env value)
    allowed_origins_csv: str = Field(default="", alias="ALLOWED_ORIGINS")

    # Optional embedding defaults
    embed_provider: Optional[str] = Field(default=None, alias="EMBED_PROVIDER")
    hf_api_key: Optional[str] = Field(default=None, alias="HF_API_KEY")

    @classmethod
    def from_environ(cls) -> "Settings":
        # dotenv loading is handled in main.py; let BaseSettings read from env.
        try:
            instance = cls()
        except ValidationError as ve:
            raise RuntimeError(
                "Invalid or missing environment variables. Please set SUPABASE_DB_URL and ALLOWED_ORIGINS in your .env"
            ) from ve
        return instance

    @property
    def allowed_origins(self) -> List[str]:
        return _parse_csv(self.allowed_origins_csv)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings.from_environ()


