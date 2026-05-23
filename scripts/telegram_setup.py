"""
scripts/telegram_setup.py - Interactive Telegram setup wizard for
jewellery-design-studio.

Walks new users through BotFather bot creation, validates the token,
auto-detects the chat id via a live getUpdates long-poll, and writes
TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID into .env atomically.

Existing keys in .env (OPENAI_API_KEY, GEMINI_API_KEY, etc.) are preserved.
Before any overwrite, the current .env is copied to .env.bak-YYYYMMDD-HHMMSS.

Usage:
    python scripts/telegram_setup.py            # interactive wizard
    python scripts/telegram_setup.py --check    # verify existing .env config
    python scripts/telegram_setup.py --help
"""

from __future__ import annotations

import argparse
import os
import shutil
import sys
import tempfile
import time
from datetime import datetime
from pathlib import Path

# ---------------------------------------------------------------------------
# Project root + .env location (matches config.py convention).
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENV_PATH = PROJECT_ROOT / ".env"

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_API_BASE = "https://api.telegram.org/bot{token}"
_WIZARD_TIMEOUT_S = 300     # 5 minutes to wait for first message
_LONG_POLL_TIMEOUT_S = 25   # per getUpdates call
_MAX_TOKEN_RETRIES = 3
_SETUP_DONE_MSG = (
    "Setup complete. The Jewellery Design Studio will send design previews here "
    "for your approval."
)
_CHECK_OK_MSG = "Jewellery Design Studio setup check OK."

EXIT_OK = 0
EXIT_ERROR = 1
EXIT_CANCELLED = 130

# ---------------------------------------------------------------------------
# Token truncation (never log the full token).
# ---------------------------------------------------------------------------


def _truncate_token(token: str) -> str:
    """Return a safe preview: first 8 chars + '...' + last 4 chars."""
    if len(token) <= 12:
        return token[:4] + "..."
    return token[:8] + "..." + token[-4:]


# ---------------------------------------------------------------------------
# .env reader / writer
# ---------------------------------------------------------------------------


def _read_env() -> dict[str, str]:
    """Parse .env into an ordered dict of key -> raw-value pairs.

    Lines that are blank, comments, or unparseable are stored as-is under
    a sentinel key so they survive a round-trip write.
    """
    lines: dict[str, str] = {}
    if not ENV_PATH.exists():
        return lines
    for idx, raw in enumerate(ENV_PATH.read_text(encoding="utf-8").splitlines()):
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            # Preserve comment and blank lines keyed by position.
            lines[f"__comment_{idx}__"] = raw
            continue
        if "=" in raw:
            key, _, val = raw.partition("=")
            lines[key.strip()] = val
        else:
            lines[f"__raw_{idx}__"] = raw
    return lines


def _write_env(pairs: dict[str, str]) -> None:
    """Write pairs back to .env atomically. Preserves file mode if .env exists."""
    lines: list[str] = []
    for key, val in pairs.items():
        if key.startswith("__comment_") or key.startswith("__raw_"):
            lines.append(val)
        else:
            lines.append(f"{key}={val}")
    content = "\n".join(lines) + "\n"

    # Write to a temp file in the same directory, then os.replace (atomic).
    fd, tmp = tempfile.mkstemp(dir=PROJECT_ROOT, prefix=".env-tmp-")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(content)
        # Preserve permissions if .env already exists.
        if ENV_PATH.exists():
            try:
                shutil.copymode(str(ENV_PATH), tmp)
            except OSError:
                pass
        os.replace(tmp, ENV_PATH)
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def _backup_env() -> str:
    """Copy .env to .env.bak-YYYYMMDD-HHMMSS. Returns the backup path."""
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = PROJECT_ROOT / f".env.bak-{stamp}"
    shutil.copy2(str(ENV_PATH), str(backup))
    return str(backup)


# ---------------------------------------------------------------------------
# Telegram API helpers (no third-party Telegram libraries).
# ---------------------------------------------------------------------------


def _api_url(token: str, method: str) -> str:
    return f"{_API_BASE.format(token=token)}/{method}"


def _get_me(token: str) -> dict:
    """Call getMe. Returns the bot dict on success, raises RuntimeError on failure."""
    import requests

    url = _api_url(token, "getMe")
    try:
        r = requests.get(url, timeout=15)
    except requests.exceptions.RequestException as exc:
        raise RuntimeError(f"Network error calling getMe: {exc}") from exc
    body = r.json()
    if not body.get("ok"):
        raise RuntimeError(
            f"getMe failed (HTTP {r.status_code}): "
            f"{body.get('description', r.text)}"
        )
    return body["result"]


def _get_updates(token: str, offset: int, timeout_s: int = _LONG_POLL_TIMEOUT_S) -> list[dict]:
    """Long-poll getUpdates. Returns a list of update dicts (may be empty)."""
    import requests

    url = _api_url(token, "getUpdates")
    params = {
        "timeout": timeout_s,
        "offset": offset,
        "allowed_updates": ["message"],
    }
    try:
        r = requests.get(url, params=params, timeout=timeout_s + 10)
    except requests.exceptions.RequestException as exc:
        raise RuntimeError(f"getUpdates network error: {exc}") from exc
    body = r.json()
    if not body.get("ok"):
        raise RuntimeError(
            f"getUpdates API error: {body.get('description', r.text)}"
        )
    return body.get("result", [])


def _send_message(token: str, chat_id: str | int, text: str) -> None:
    """Send a plain text message."""
    import requests

    url = _api_url(token, "sendMessage")
    try:
        r = requests.post(url, data={"chat_id": str(chat_id), "text": text}, timeout=15)
    except requests.exceptions.RequestException as exc:
        raise RuntimeError(f"sendMessage network error: {exc}") from exc
    body = r.json()
    if not body.get("ok"):
        raise RuntimeError(
            f"sendMessage error: {body.get('description', r.text)}"
        )


# ---------------------------------------------------------------------------
# Wizard steps
# ---------------------------------------------------------------------------


def _step_intro() -> None:
    print()
    print("=" * 64)
    print("  Jewellery Design Studio: Telegram setup wizard")
    print("=" * 64)
    print()
    print(
        "This wizard will:\n"
        "  1. Walk you through creating a Telegram bot via @BotFather.\n"
        "  2. Validate the bot token.\n"
        "  3. Detect your chat id automatically (no manual URL-hunting).\n"
        "  4. Write TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID into your .env.\n"
        "  5. Send a confirmation message so you know it worked.\n"
    )
    print(
        "IMPORTANT: use a dedicated bot for this studio.\n"
        "Telegram getUpdates is single-consumer: if you reuse a token\n"
        "already polled by another service, that service will consume\n"
        "the approval callbacks and the studio poller will time out.\n"
        "Create a fresh bot in BotFather just for the studio.\n"
    )


def _step_check_existing() -> str:
    """Return 'keep', 'overwrite', or 'new' depending on user choice."""
    pairs = _read_env()
    has_token = bool(pairs.get("TELEGRAM_BOT_TOKEN", "").strip())
    has_chat = bool(pairs.get("TELEGRAM_CHAT_ID", "").strip())

    if not (has_token or has_chat):
        return "new"

    print("Existing Telegram credentials found in .env.")
    while True:
        choice = input("  [k]eep existing  /  [o]verwrite  /  [c]ancel: ").strip().lower()
        if choice in ("k", "keep"):
            return "keep"
        if choice in ("o", "overwrite"):
            return "overwrite"
        if choice in ("c", "cancel"):
            return "cancel"
        print("  Please type k, o, or c.")


def _step_botfather() -> None:
    print()
    print("Step 1: create a new Telegram bot via BotFather")
    print("-" * 48)
    print("  1. Open Telegram on any device.")
    print("  2. Search for @BotFather and start a chat.")
    print("  3. Send: /newbot")
    print("  4. Choose a display name, e.g. 'Jewellery Design Studio'.")
    print("  5. Choose a unique username ending in 'bot',")
    print("     e.g. 'my_jds_approval_bot'.")
    print("  6. BotFather replies with a token shaped like:")
    print("     123456789:ABCdef...")
    print("     Copy that token.")
    print()


def _step_read_token() -> str:
    """Prompt the user to paste the token. Returns the validated token."""
    for attempt in range(1, _MAX_TOKEN_RETRIES + 1):
        raw = input("Paste your bot token here: ").strip()
        if not raw:
            print("  Token cannot be blank. Try again.")
            continue
        print(f"  Validating token {_truncate_token(raw)} ...")
        try:
            bot = _get_me(raw)
        except RuntimeError as exc:
            print(f"  Validation failed: {exc}")
            if attempt < _MAX_TOKEN_RETRIES:
                print(f"  ({_MAX_TOKEN_RETRIES - attempt} attempt(s) remaining)")
            continue
        username = bot.get("username", "<unknown>")
        print(f"  Token valid. Bot username: @{username}")
        return raw

    print("\nToo many failed attempts. Exiting.")
    sys.exit(EXIT_ERROR)


def _step_detect_chat_id(token: str, bot_username: str) -> str:
    """Long-poll getUpdates until a message arrives. Returns the chat_id string."""
    print()
    print("Step 2: detect your chat id automatically")
    print("-" * 48)
    print(f"  Open Telegram and find @{bot_username}.")
    print("  Send it any text message, e.g. 'hello'.")
    print(f"  Waiting up to {_WIZARD_TIMEOUT_S // 60} minutes for that message ...")
    print("  (Press Ctrl+C to cancel.)\n")

    offset = 0
    deadline = time.monotonic() + _WIZARD_TIMEOUT_S

    while time.monotonic() < deadline:
        remaining = int(deadline - time.monotonic())
        lp_timeout = min(_LONG_POLL_TIMEOUT_S, remaining)
        if lp_timeout <= 0:
            break

        try:
            updates = _get_updates(token, offset=offset, timeout_s=lp_timeout)
        except RuntimeError as exc:
            print(f"  Network error (retrying in 3 s): {exc}")
            time.sleep(3)
            continue

        for upd in updates:
            new_offset = upd["update_id"] + 1
            if new_offset > offset:
                offset = new_offset

            msg = upd.get("message", {})
            chat = msg.get("chat", {})
            chat_id = chat.get("id")
            if chat_id is not None:
                chat_type = chat.get("type", "")
                first_name = chat.get("first_name") or chat.get("title") or ""
                print(f"  Message received from {first_name!r} ({chat_type}).")
                print(f"  Chat id detected: {chat_id}")
                return str(chat_id)

    print()
    print("Timed out waiting for a message.")
    print(
        "If you sent a message and nothing happened, make sure you sent it\n"
        "AFTER starting this wizard, not before. Then run the wizard again."
    )
    sys.exit(EXIT_ERROR)


def _step_write_env(token: str, chat_id: str, mode: str) -> None:
    """Write token and chat_id to .env. Back up first if overwriting."""
    pairs = _read_env()

    if mode == "overwrite" and ENV_PATH.exists():
        backup = _backup_env()
        print(f"  Current .env backed up to: {backup}")

    pairs["TELEGRAM_BOT_TOKEN"] = token
    pairs["TELEGRAM_CHAT_ID"] = chat_id
    _write_env(pairs)
    print(f"  .env updated at: {ENV_PATH}")


def _step_send_confirmation(token: str, chat_id: str) -> None:
    print("  Sending confirmation message to your Telegram chat ...")
    try:
        _send_message(token, chat_id, _SETUP_DONE_MSG)
        print("  Confirmation sent.")
    except RuntimeError as exc:
        print(f"  Warning: could not send confirmation: {exc}")
        print("  The .env has been written. Run --check to verify later.")


# ---------------------------------------------------------------------------
# Wizard entry point
# ---------------------------------------------------------------------------


def run_wizard() -> int:
    try:
        _step_intro()

        mode = _step_check_existing()
        if mode == "cancel":
            print("Cancelled.")
            return EXIT_OK
        if mode == "keep":
            print("Keeping existing credentials. Nothing changed.")
            print("Run `python scripts/telegram_setup.py --check` to verify them.")
            return EXIT_OK

        _step_botfather()
        token = _step_read_token()

        # Re-call getMe to get the username (already validated above).
        bot = _get_me(token)
        bot_username = bot.get("username", "your_bot")

        chat_id = _step_detect_chat_id(token, bot_username)

        print()
        print("Writing credentials to .env ...")
        _step_write_env(token, chat_id, mode)
        _step_send_confirmation(token, chat_id)

        print()
        print("Done. Run `python scripts/telegram_setup.py --check` any time to verify.")
        return EXIT_OK

    except KeyboardInterrupt:
        print("\nCancelled.")
        return EXIT_CANCELLED


# ---------------------------------------------------------------------------
# Check mode
# ---------------------------------------------------------------------------


def run_check() -> int:
    """Read .env, validate token, send a test message. Non-interactive."""
    pairs = _read_env()
    token = pairs.get("TELEGRAM_BOT_TOKEN", "").strip()
    chat_id = pairs.get("TELEGRAM_CHAT_ID", "").strip()

    ok = True

    if not token:
        print("ERROR: TELEGRAM_BOT_TOKEN is not set in .env.", file=sys.stderr)
        ok = False
    if not chat_id:
        print("ERROR: TELEGRAM_CHAT_ID is not set in .env.", file=sys.stderr)
        ok = False
    if not ok:
        print(
            "Run `python scripts/telegram_setup.py` to configure Telegram.",
            file=sys.stderr,
        )
        return EXIT_ERROR

    print(f"Token: {_truncate_token(token)}")
    print(f"Chat id: {chat_id}")

    print("Calling getMe ...")
    try:
        bot = _get_me(token)
    except RuntimeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return EXIT_ERROR
    print(f"Bot: @{bot.get('username')} (id {bot.get('id')})")

    print("Sending test message ...")
    try:
        _send_message(token, chat_id, _CHECK_OK_MSG)
    except RuntimeError as exc:
        print(f"ERROR: sendMessage failed: {exc}", file=sys.stderr)
        return EXIT_ERROR

    print("Setup check passed.")
    return EXIT_OK


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="telegram_setup",
        description=(
            "Telegram setup wizard for jewellery-design-studio. "
            "Without flags, runs the interactive wizard (BotFather walkthrough, "
            "auto chat-id detection, .env writer). "
            "Pass --check to verify an existing configuration non-interactively."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python scripts/telegram_setup.py           # interactive wizard\n"
            "  python scripts/telegram_setup.py --check   # verify existing .env\n"
        ),
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help=(
            "Non-interactive: read .env, validate token via getMe, send a test "
            "message. Exits 0 on success, 1 on any failure."
        ),
    )
    args = parser.parse_args()

    if args.check:
        return run_check()
    return run_wizard()


if __name__ == "__main__":
    sys.exit(main())
