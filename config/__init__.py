"""Runtime configuration. Everything tunable lives here, never hard-coded in engines."""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="SLABSPREAD_", extra="ignore")

    database_url: str = "sqlite:///./slabspread.db"

    # Identity (plan §3). Fuzzy matches are *candidates* only; nothing is auto-trusted
    # above `fuzzy_candidate_min` — it merely decides what is worth a human's time.
    fuzzy_candidate_min: float = Field(0.70, ge=0, le=1)
    # Below this the pair is not even recorded.
    fuzzy_record_min: float = Field(0.55, ge=0, le=1)


settings = Settings()
