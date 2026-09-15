"""
Configuration module for the AI Reviews Summarizer.

Loads environment variables from .env and validates that all required
values are present and well-formed before the pipeline starts.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv


# ---------------------------------------------------------------------------
# Locate and load .env
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENV_PATH = PROJECT_ROOT / ".env"

if not ENV_PATH.exists():
    print(
        "❌ .env file not found.\n"
        "   Copy .env.example to .env and fill in your keys:\n"
        f"   cp {PROJECT_ROOT / '.env.example'} {ENV_PATH}"
    )
    sys.exit(1)

load_dotenv(ENV_PATH)


# ---------------------------------------------------------------------------
# Helper: read a required env var
# ---------------------------------------------------------------------------
_PLACEHOLDERS = {"your-key-here", "your-langsmith-key-here"}


def _require(name: str) -> str:
    """Return the env var *name* or abort with a clear message."""
    value = os.getenv(name)
    if not value or value.strip() in _PLACEHOLDERS:
        print(f"❌ {name} is not configured. Update your .env file.")
        sys.exit(1)
    return value.strip()


def _optional(name: str, default: str = "") -> str:
    """Return the env var *name* or *default* if unset / placeholder."""
    value = os.getenv(name, default)
    if not value or value.strip() in _PLACEHOLDERS:
        return default
    return value.strip()


def _int_in_range(name: str, default: int, lo: int, hi: int) -> int:
    """Return the env var *name* as an int clamped to [lo, hi]."""
    raw = os.getenv(name, str(default))
    try:
        val = int(raw)
    except ValueError:
        print(f"⚠️  Invalid {name}={raw}. Defaulting to {default}.")
        return default
    if not (lo <= val <= hi):
        print(f"⚠️  {name}={val} out of range [{lo}, {hi}]. Defaulting to {default}.")
        return default
    return val


# ---------------------------------------------------------------------------
# Python version gate
# ---------------------------------------------------------------------------
if sys.version_info < (3, 11):
    print(
        f"❌ Python 3.11+ required. Current: {sys.version_info.major}.{sys.version_info.minor}"
    )
    sys.exit(1)


# ---------------------------------------------------------------------------
# Required config values
# ---------------------------------------------------------------------------
GEMINI_API_KEY: str = _require("GEMINI_API_KEY")

# ---------------------------------------------------------------------------
# Optional config values
# ---------------------------------------------------------------------------
LANGCHAIN_TRACING_V2: str = _optional("LANGCHAIN_TRACING_V2", "false")
LANGCHAIN_API_KEY: str = _optional("LANGCHAIN_API_KEY", "")

# ---------------------------------------------------------------------------
# App IDs
# ---------------------------------------------------------------------------
GOOGLE_PLAY_APP_ID: str = _optional("GOOGLE_PLAY_APP_ID", "com.noon.buyerapp")

# ---------------------------------------------------------------------------
# Review window
# ---------------------------------------------------------------------------
REVIEW_WEEKS: int = _int_in_range("REVIEW_WEEKS", default=10, lo=1, hi=52)

# ---------------------------------------------------------------------------
# MCP Servers
# ---------------------------------------------------------------------------
MCP_SERVER_SSE_URL: str = _optional("MCP_SERVER_SSE_URL", "https://google-workspace-mcp-production-c1aa.up.railway.app/sse")
TARGET_GOOGLE_DOC_ID: str = _optional("TARGET_GOOGLE_DOC_ID", "")


# ---------------------------------------------------------------------------
# Delivery
# ---------------------------------------------------------------------------
PULSE_DOC_TITLE: str = _optional("PULSE_DOC_TITLE", "Noon App Pulse")
EMAIL_RECIPIENT: str = _optional("EMAIL_RECIPIENT", "team@example.com")
EMAIL_SUBJECT: str = _optional("EMAIL_SUBJECT", "Weekly Noon App Pulse — {date}")

# ---------------------------------------------------------------------------
# Data directories (auto-created)
# ---------------------------------------------------------------------------
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
PULSES_DIR = DATA_DIR / "pulses"

for _dir in (RAW_DIR, PROCESSED_DIR, PULSES_DIR):
    _dir.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# Summary (for debug / startup logging)
# ---------------------------------------------------------------------------
def print_config_summary() -> None:
    """Print a masked summary of the loaded configuration."""
    mask = lambda s: f"***{s[-4:]}" if len(s) > 4 else "***"
    print("=" * 50)
    print("  AI Reviews Summarizer — Configuration")
    print("=" * 50)
    print(f"  GEMINI_API_KEY       : {mask(GEMINI_API_KEY)}")
    print(f"  GOOGLE_PLAY_APP_ID   : {GOOGLE_PLAY_APP_ID}")
    print(f"  REVIEW_WEEKS         : {REVIEW_WEEKS}")
    print(f"  MCP_DOCS_SERVER_URL  : {MCP_DOCS_SERVER_URL}")
    print(f"  MCP_GMAIL_SERVER_URL : {MCP_GMAIL_SERVER_URL}")
    print(f"  PULSE_DOC_TITLE      : {PULSE_DOC_TITLE}")
    print(f"  EMAIL_RECIPIENT      : {EMAIL_RECIPIENT}")
    print(f"  LANGCHAIN_TRACING    : {LANGCHAIN_TRACING_V2}")
    print(f"  DATA_DIR             : {DATA_DIR}")
    print("=" * 50)
