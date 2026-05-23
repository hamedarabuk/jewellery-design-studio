"""Lightweight config loader for jewellery-design-studio.

Loads environment variables from .env in the project root via python-dotenv,
then exposes them as a small typed object. Single source of truth: this is
the only module that reads `.env`.

Usage:
    from config import config
    api_key = config.openai_api_key
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

# Load .env from the project root (the directory containing this file).
# override=True so the .env wins over any stale shell env vars.
PROJECT_ROOT = Path(__file__).resolve().parent
load_dotenv(PROJECT_ROOT / ".env", override=True)


@dataclass(frozen=True)
class Config:
    """Frozen view of project configuration."""

    # Required for gpt-image-2 (the default generator).
    openai_api_key: str

    # Optional: Telegram one-tap approval previews.
    telegram_bot_token: str
    telegram_chat_id: str

    # Optional: Google Gemini (nano-banana) for low-cost iteration fallback.
    gemini_api_key: str

    # Project paths.
    project_root: Path
    brands_root: Path
    templates_root: Path
    scripts_root: Path

    @classmethod
    def from_env(cls) -> "Config":
        return cls(
            openai_api_key=os.environ.get("OPENAI_API_KEY", ""),
            telegram_bot_token=os.environ.get("TELEGRAM_BOT_TOKEN", ""),
            telegram_chat_id=os.environ.get("TELEGRAM_CHAT_ID", ""),
            gemini_api_key=os.environ.get("GEMINI_API_KEY", ""),
            project_root=PROJECT_ROOT,
            brands_root=PROJECT_ROOT / "brands",
            templates_root=PROJECT_ROOT / "templates",
            scripts_root=PROJECT_ROOT / "scripts",
        )

    def require_openai(self) -> str:
        """Return the OpenAI API key, raising if missing."""
        if not self.openai_api_key:
            raise RuntimeError(
                "OPENAI_API_KEY is required. Set it in .env at the project root. "
                "Copy .env.example to .env if you have not already."
            )
        return self.openai_api_key

    def telegram_ready(self) -> bool:
        """True when Telegram delivery is configured."""
        return bool(self.telegram_bot_token and self.telegram_chat_id)


config = Config.from_env()
