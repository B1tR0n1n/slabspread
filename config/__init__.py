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
    polygon_rpc_url: str = "https://polygon-bor-rpc.publicnode.com"  # polygon-rpc.com went key-only
    solana_rpc_url: str = "https://api.mainnet-beta.solana.com"
    polygon_log_chunk_blocks: int = 2000  # eth_getLogs range per call; most public RPCs cap here
    polygon_address_chunk: int = 4  # public nodes block eth_getLogs with long address lists
    polygon_backfill_blocks: int = 43_200  # ~1 day of Polygon blocks scanned on the very first run
    solana_sig_page: int = 100  # getTransaction per signature; keep runs under the interval

    # Per-source token buckets: requests per second and burst. JSON in env, e.g.
    #   SLABSPREAD_RATE_LIMITS='{"polygon_rpc": [5, 10]}'
    rate_limits: dict[str, tuple[float, int]] = {
        "polygon_rpc": (4.0, 8),
        "solana_rpc": (
            2.0,
            2,
        ),  # public mainnet-beta allows ~40 req/10 s per method per IP; three workers share it
        "courtyard_metadata": (1.0, 2),
        "collectorcrypt_api": (2.0, 2),  # published limit is 300/min; we use ≤120/min (pool sampling)
        "phygitals_api": (0.5, 1),
    }
    max_retries: int = 5
    backoff_base_s: float = 1.0
    backoff_max_s: float = 60.0

    # Schedules (seconds between runs) per worker key.
    schedules: dict[str, int] = {
        "onchain_courtyard": 300,
        "onchain_collectorcrypt": 300,
        "onchain_phygitals": 300,
        "cc_marketplace": 600,
        "cc_gacha_odds": 3600,  # ≈700 requests per run at ≤2/s
        "phygitals_packs": 1800,
        "phygitals_listings": 600,
        "alerts": 300,
    }

    # Gates for sources whose docs/data-licenses.md row is not `approved`. Default off.
    # Flipping one on is a statement that its license question was resolved and logged.
    courtyard_metadata_enabled: bool = False  # tokenURI enrichment (Q3)

    # --- Phase 3 engine defaults (plan §5); every value shows on the dashboard -------------
    spread_shipping: float = 5.00
    spread_sales_tax_rate: float = 0.00
    spread_vault_intake_cost: float = 0.00
    spread_grading_cost: float = 25.00
    spread_platform_fee_rate: float = 0.06
    spread_min_sales: int = 3
    spread_sales_window_days: int = 30
    spread_max_age_ask_hours: int = 24
    spread_max_age_floor_hours: int = 24
    # Buyback as a fraction of the platform's stated value, per source (Phase 0 §2–3).
    buyback_pct: dict[str, float] = {"collector_crypt": 0.85, "phygitals": 0.85, "courtyard": 0.90}
    lag_drop_pct: float = 0.15
    lag_flat_hours: int = 48
    lag_flat_tolerance_pct: float = 0.02

    # --- Phase 4: owner auth, alerts ---------------------------------------------------------
    # "local": owner_email + owner_password_hash (pbkdf2, see app/auth.py make_hash)
    # "supabase": verify Supabase Auth JWT (HS256) and require email == owner_email
    # "off": no auth — tests only; refused outside DEBUG
    auth_mode: str = "local"
    debug: bool = False
    owner_email: str = ""
    owner_password_hash: str = ""
    session_secret: str = "change-me"  # itsdangerous signing key for the session cookie
    supabase_url: str = ""
    supabase_anon_key: str = ""
    supabase_jwt_secret: str = ""
    alert_floor_margin_min: float = 10.00  # alert when floor_margin >= this
    alert_cooldown_hours: int = 12  # don't re-alert the same listing inside this window
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    alert_email_to: str = ""
    alert_email_from: str = ""

    # --- Phase 5: public site ---------------------------------------------------------------
    site_base_url: str = "https://example.com"
    site_name: str = "SlabSpread"
    site_out_dir: str = "public"
    analytics_snippet: str = ""  # e.g. a Plausible <script> tag; empty = none
    affiliate_links: dict[str, str] = {}  # platform key → link; only where terms allow (Q7)

    # --- Phase 6: paid tier — gated behind evidence and paperwork (plan §8) ----------------
    paid_tier_enabled: bool = False
    stripe_secret_key: str = ""
    stripe_webhook_secret: str = ""
    stripe_price_id: str = ""
    launch_licenses_confirmed: bool = False  # every data license permits a commercial derived product
    launch_terms_reviewed: bool = False  # ToS + privacy reviewed by a professional
    launch_min_calibrated_trades: int = 30  # ledger evidence required before selling alerts
    fanout_per_listing_cap: int = 5  # max subscribers alerted about one listing
    fanout_stagger_seconds: int = 90
    # Q1 resolved 2026-09-26: documented public API, published rate limits, no credential needed.
    collectorcrypt_api_enabled: bool = True
    collectorcrypt_api_key: str = ""  # optional bearer key from support@collectorcrypt.com (raises limits)
    collectorcrypt_step: int = 100
    collectorcrypt_pages_per_run: int = 3
    collectorcrypt_sample_pools: bool = (
        True  # measure each tier's public prize pool (≈8 paged calls per machine)
    )
    collectorcrypt_pool_max_pages: int = 60  # 100 cards per page; largest tier seen ≈ 4,300 cards
    # Q2: docs invite tooling, ToS demands *written* consent — off until the owner has it.
    phygitals_api_enabled: bool = False
    phygitals_pages_per_run: int = 2
    user_agent: str = "SlabSpread/0.1 (owner-run analytics; contact via repo)"


settings = Settings()
