"""Environment-based runtime configuration."""

import os

from app.common.paths import DISCORD_MESSAGES_FILE
from app.config.runtime import load_dotenv

load_dotenv()

# Tradier Account IDs (no fallback - fail fast if not set)
PAPER_ACCOUNT_ID = os.getenv("TRADIER_PAPER_ACCOUNT_ID")
LIVE_ACCOUNT_ID = os.getenv("TRADIER_LIVE_ACCOUNT_ID")

# Tradier API Keys
TRADIER_SANDBOX_KEY = os.getenv("TRADIER_SANDBOX_KEY")
TRADIER_LIVE_KEY = os.getenv("TRADIER_LIVE_KEY")

# Validate required credentials (fail fast on startup)
if not TRADIER_SANDBOX_KEY:
    raise EnvironmentError("TRADIER_SANDBOX_KEY not set in environment or .env")
if not TRADIER_LIVE_KEY:
    raise EnvironmentError("TRADIER_LIVE_KEY not set in environment or .env")
if not PAPER_ACCOUNT_ID:
    raise EnvironmentError("TRADIER_PAPER_ACCOUNT_ID not set in environment or .env")
if not LIVE_ACCOUNT_ID:
    raise EnvironmentError("TRADIER_LIVE_ACCOUNT_ID not set in environment or .env")

# Defaults (runtime code will override by mode)
DEFAULT_ACCOUNT_ID = PAPER_ACCOUNT_ID
DEFAULT_KEY = TRADIER_SANDBOX_KEY

# Discord Webhook Settings
DISCORD_ENABLED = os.getenv("GAMMA_DISCORD_ENABLED", "1").lower() not in {"0", "false", "no"}
DISCORD_WEBHOOK_LIVE_URL = os.getenv("GAMMA_DISCORD_WEBHOOK_LIVE_URL", "")
DISCORD_WEBHOOK_PAPER_URL = os.getenv("GAMMA_DISCORD_WEBHOOK_PAPER_URL", "")


def _validate_discord_url(env_name: str, value: str) -> None:
    if value and not value.startswith("https://discord.com/api/webhooks/"):
        raise ValueError(
            f"Invalid {env_name} format: must start with 'https://discord.com/api/webhooks/'\n"
            f"Got: {value[:50]}..."
        )


_validate_discord_url("GAMMA_DISCORD_WEBHOOK_LIVE_URL", DISCORD_WEBHOOK_LIVE_URL)
_validate_discord_url("GAMMA_DISCORD_WEBHOOK_PAPER_URL", DISCORD_WEBHOOK_PAPER_URL)

# Delayed webhook (7 min delay) - for free tier
DISCORD_DELAYED_ENABLED = os.getenv("GAMMA_DISCORD_DELAYED_ENABLED", "1").lower() not in {"0", "false", "no"}
DISCORD_DELAYED_WEBHOOK_URL = os.getenv("GAMMA_DISCORD_DELAYED_WEBHOOK_URL", "")
_validate_discord_url("GAMMA_DISCORD_DELAYED_WEBHOOK_URL", DISCORD_DELAYED_WEBHOOK_URL)
DISCORD_DELAY_SECONDS = int(os.getenv("GAMMA_DISCORD_DELAY_SECONDS", "420"))

# Discord Auto-Delete Settings
DISCORD_AUTODELETE_ENABLED = os.getenv("GAMMA_DISCORD_AUTODELETE_ENABLED", "1").lower() not in {"0", "false", "no"}
DISCORD_AUTODELETE_STORAGE = os.getenv("GAMMA_DISCORD_AUTODELETE_STORAGE", str(DISCORD_MESSAGES_FILE))

# TTL (time-to-live) in seconds for different message types
DISCORD_TTL_SIGNALS = int(os.getenv("GAMMA_DISCORD_TTL_SIGNALS", str(24 * 3600)))
DISCORD_TTL_CRASHES = int(os.getenv("GAMMA_DISCORD_TTL_CRASHES", str(1 * 3600)))
DISCORD_TTL_HEARTBEAT = int(os.getenv("GAMMA_DISCORD_TTL_HEARTBEAT", str(30 * 60)))
DISCORD_TTL_DEFAULT = int(os.getenv("GAMMA_DISCORD_TTL_DEFAULT", str(2 * 3600)))

# Healthcheck.io heartbeat URLs
HEALTHCHECK_LIVE_URL = os.getenv("GAMMA_HEALTHCHECK_LIVE_URL", "")
HEALTHCHECK_PAPER_URL = os.getenv("GAMMA_HEALTHCHECK_PAPER_URL", "")
