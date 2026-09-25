"""Runtime configuration. Everything tunable lives here, never hard-coded in engines or workers."""

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

    # --- Ingestion (plan §4) -------------------------------------------------------------
    raw_dir: str = "data/raw"  # compressed raw responses for replay; gitignored
    polygon_rpc_url: str = "https://polygon-rpc.com"
    solana_rpc_url: str = "https://api.mainnet-beta.solana.com"
    polygon_log_chunk_blocks: int = 2000  # eth_getLogs range per call; most public RPCs cap here
    polygon_start_block: int = 88_000_000  # first block to scan when no cursor exists
    solana_sig_page: int = 1000

    # Per-source token buckets: requests per second and burst. JSON in env, e.g.
    #   SLABSPREAD_RATE_LIMITS='{"polygon_rpc": [5, 10]}'
    rate_limits: dict[str, tuple[float, int]] = {
        "polygon_rpc": (4.0, 8),
        "solana_rpc": (4.0, 8),
        "courtyard_metadata": (1.0, 2),
        "collectorcrypt_api": (0.5, 1),
    }
    max_retries: int = 5
    backoff_base_s: float = 1.0
    backoff_max_s: float = 60.0

    # Schedules (seconds between runs) per worker key.
    schedules: dict[str, int] = {
        "onchain_courtyard": 300,
        "onchain_collectorcrypt": 300,
        "onchain_phygitals": 300,
        "platform_odds": 1800,
    }

    # Gates for sources whose docs/data-licenses.md row is not `approved`. Default off.
    # Flipping one on is a statement that its license question was resolved and logged.
    courtyard_metadata_enabled: bool = False  # tokenURI enrichment (Q3)
    collectorcrypt_api_enabled: bool = False  # api.collectorcrypt.com / gacha API (Q1)
    phygitals_api_enabled: bool = False  # api.phygitals.com (Q2)


settings = Settings()
