"""
scripts/telegram_approval.py - Telegram inline-keyboard approval flow for
the jewellery design studio.

Sends a design render to Telegram with Approve / Iterate / Reject buttons,
then polls getUpdates until the user taps one. Verdict and optional iteration
notes are persisted to a per-piece sidecar (approval.json).

No third-party Telegram libraries. Pure stdlib + requests.

Usage (CLI):
    python scripts/telegram_approval.py send \\
        --piece brands/my-brand/proposed/albion-garland \\
        --image brands/my-brand/proposed/albion-garland/render-v1-tg.jpg \\
        --caption "PROPOSED: Albion Garland (high-jewellery, £8,500, 6 weeks)"

    python scripts/telegram_approval.py poll \\
        --piece brands/my-brand/proposed/albion-garland \\
        --timeout 1800

    python scripts/telegram_approval.py mark-done \\
        --piece brands/my-brand/proposed/albion-garland

The last line printed by "send" is the approval_id. The SKILL captures it:
    approval_id=$(python scripts/telegram_approval.py send ... | tail -1)

"poll" prints a JSON verdict to stdout:
    {"verdict": "approve|iterate|reject|timeout", "notes": "", "approval_id": "..."}
"""

from __future__ import annotations

import argparse
import json
import os
import secrets
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from config import config  # noqa: E402

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_API_BASE = "https://api.telegram.org/bot{token}"
_PREFIX = "jds"
_SIDECAR_NAME = "approval.json"
_CAPTION_LIMIT = 1024

# Action labels -> canonical callback token.
_BUTTON_ACTIONS: dict[str, str] = {
    "Approve": "approve",
    "Iterate": "iterate",
    "Reject": "reject",
}

# Default window (seconds) to listen for a text reply after "Iterate".
_DEFAULT_ITERATE_WINDOW_S: int = int(
    os.environ.get("JDS_ITERATE_NOTES_WINDOW_S", "90")
)

EXIT_OK = 0
EXIT_ERROR = 1


# ---------------------------------------------------------------------------
# Credentials
# ---------------------------------------------------------------------------


def _require_credentials() -> tuple[str, str]:
    """Return (token, chat_id) from config, or fail fast."""
    token = config.telegram_bot_token
    chat_id = config.telegram_chat_id
    if not token:
        print(
            "telegram_approval: TELEGRAM_BOT_TOKEN is not set in .env. "
            "See README section 'Telegram approval' for setup instructions.",
            file=sys.stderr,
        )
        sys.exit(EXIT_ERROR)
    if not chat_id:
        print(
            "telegram_approval: TELEGRAM_CHAT_ID is not set in .env. "
            "See README section 'Telegram approval' for setup instructions.",
            file=sys.stderr,
        )
        sys.exit(EXIT_ERROR)
    # Log only a truncated preview of the token for safety.
    print(
        f"telegram_approval: using bot token ***{token[-6:]} "
        f"for chat {chat_id}",
        file=sys.stderr,
    )
    return token, chat_id


def _api_url(token: str, method: str) -> str:
    return f"{_API_BASE.format(token=token)}/{method}"


# ---------------------------------------------------------------------------
# Sidecar helpers
# ---------------------------------------------------------------------------


def _sidecar_path(piece_dir: Path) -> Path:
    return piece_dir / _SIDECAR_NAME


def _read_sidecar(piece_dir: Path) -> dict:
    p = _sidecar_path(piece_dir)
    if not p.exists():
        raise FileNotFoundError(
            f"telegram_approval: sidecar not found at {p}. "
            "Run 'send' first to create it."
        )
    return json.loads(p.read_text(encoding="utf-8"))


def _write_sidecar(piece_dir: Path, data: dict) -> None:
    """Atomic write: temp file in the same directory + os.replace."""
    p = _sidecar_path(piece_dir)
    p.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=p.parent, prefix=".approval-tmp-")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2, ensure_ascii=False)
            fh.write("\n")
        os.replace(tmp, p)
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def _patch_sidecar(piece_dir: Path, **kwargs) -> dict:
    """Read, update the given keys, write atomically, return updated dict."""
    data = _read_sidecar(piece_dir)
    data.update(kwargs)
    _write_sidecar(piece_dir, data)
    return data


# ---------------------------------------------------------------------------
# Telegram API calls
# ---------------------------------------------------------------------------


def _post(token: str, method: str, **kwargs) -> dict:
    """POST to the Telegram Bot API. Returns the JSON response dict."""
    import requests as _req

    url = _api_url(token, method)
    try:
        r = _req.post(url, timeout=35, **kwargs)
    except _req.exceptions.RequestException as exc:
        raise RuntimeError(f"telegram_approval: network error on {method}: {exc}") from exc
    body = r.json()
    if not body.get("ok"):
        raise RuntimeError(
            f"telegram_approval: API error on {method} "
            f"(status {r.status_code}): {body.get('description', r.text)}"
        )
    return body


def _get_updates(token: str, offset: int, timeout_s: int = 25) -> list[dict]:
    """Long-poll getUpdates. Returns a (possibly empty) list of update dicts."""
    import requests as _req

    url = _api_url(token, "getUpdates")
    params = {"timeout": timeout_s, "offset": offset, "allowed_updates": ["callback_query", "message"]}
    try:
        r = _req.get(url, params=params, timeout=timeout_s + 10)
    except _req.exceptions.RequestException as exc:
        raise RuntimeError(f"telegram_approval: getUpdates network error: {exc}") from exc
    body = r.json()
    if not body.get("ok"):
        raise RuntimeError(
            f"telegram_approval: getUpdates API error: {body.get('description', r.text)}"
        )
    return body.get("result", [])


def _send_photo(
    token: str,
    chat_id: str,
    image_path: Path,
    caption: str,
    inline_keyboard: list[list[dict]],
) -> int:
    """Upload a photo with an inline keyboard. Returns message_id."""
    import requests as _req

    if len(caption) > _CAPTION_LIMIT:
        print(
            f"telegram_approval: caption is {len(caption)} chars, "
            f"truncating to {_CAPTION_LIMIT}.",
            file=sys.stderr,
        )
        caption = caption[:_CAPTION_LIMIT]

    data = {
        "chat_id": chat_id,
        "caption": caption,
        "reply_markup": json.dumps({"inline_keyboard": inline_keyboard}),
    }
    url = _api_url(token, "sendPhoto")
    with image_path.open("rb") as fh:
        try:
            r = _req.post(url, data=data, files={"photo": fh}, timeout=60)
        except _req.exceptions.RequestException as exc:
            raise RuntimeError(
                f"telegram_approval: sendPhoto network error: {exc}"
            ) from exc
    body = r.json()
    if not body.get("ok"):
        raise RuntimeError(
            f"telegram_approval: sendPhoto error: {body.get('description', r.text)}"
        )
    return body["result"]["message_id"]


def _answer_callback(token: str, callback_query_id: str, text: str) -> None:
    try:
        _post(token, "answerCallbackQuery", data={"callback_query_id": callback_query_id, "text": text})
    except RuntimeError as exc:
        # Non-fatal: the button press is already recorded.
        print(f"telegram_approval: answerCallbackQuery failed (non-fatal): {exc}", file=sys.stderr)


def _strip_keyboard(token: str, chat_id: str, message_id: int) -> None:
    """Remove the inline keyboard from a message."""
    try:
        _post(
            token,
            "editMessageReplyMarkup",
            data={
                "chat_id": chat_id,
                "message_id": message_id,
                "reply_markup": json.dumps({}),
            },
        )
    except RuntimeError as exc:
        print(f"telegram_approval: strip keyboard failed (non-fatal): {exc}", file=sys.stderr)


def _append_caption(token: str, chat_id: str, message_id: int, original_caption: str, suffix: str) -> None:
    """Edit the photo caption to append a verdict line."""
    new_caption = (original_caption + suffix)[:_CAPTION_LIMIT]
    try:
        _post(
            token,
            "editMessageCaption",
            data={
                "chat_id": chat_id,
                "message_id": message_id,
                "caption": new_caption,
            },
        )
    except RuntimeError as exc:
        print(f"telegram_approval: editMessageCaption failed (non-fatal): {exc}", file=sys.stderr)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def send_for_approval(
    image_path: Path,
    caption: str,
    piece_dir: Path,
    buttons: tuple[str, ...] = ("Approve", "Iterate", "Reject"),
) -> str:
    """Send a design render to Telegram with approval buttons.

    Creates approval.json in piece_dir. Returns the approval_id.
    Prints the approval_id as the last line of stdout (SKILL contract).
    """
    token, chat_id = _require_credentials()

    if not image_path.exists():
        print(
            f"telegram_approval: image not found: {image_path}",
            file=sys.stderr,
        )
        sys.exit(EXIT_ERROR)

    approval_id = f"{_PREFIX}-{secrets.token_hex(4)}"

    # Build inline keyboard: one row, one button per label.
    keyboard_row: list[dict] = []
    for label in buttons:
        action = _BUTTON_ACTIONS.get(label, label.lower().split()[0])
        keyboard_row.append(
            {"text": label, "callback_data": f"{_PREFIX}:{action}:{approval_id}"}
        )
    inline_keyboard = [keyboard_row]

    message_id = _send_photo(token, chat_id, image_path, caption, inline_keyboard)

    sidecar: dict = {
        "approval_id": approval_id,
        "message_id": message_id,
        "chat_id": chat_id,
        "image_path": str(image_path),
        "caption": caption,
        "state": "pending",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updates_offset": 0,
        "notes": "",
        "resolved_at": None,
    }
    _write_sidecar(piece_dir, sidecar)

    print(
        f"telegram_approval: sent (message_id={message_id}, approval_id={approval_id})",
        file=sys.stderr,
    )
    # Contract: approval_id is the LAST line on stdout.
    print(approval_id)
    return approval_id


def poll_for_verdict(
    approval_id: str,
    piece_dir: Path,
    timeout_s: int = 1800,
    poll_interval_s: int = 3,
) -> dict:
    """Long-poll until the user taps a button or the timeout expires.

    Returns a dict: {"verdict": str, "notes": str, "approval_id": str}.
    Patches approval.json as state evolves (offset, resolved_at, notes, state).
    """
    token, _chat_id = _require_credentials()

    sidecar = _read_sidecar(piece_dir)
    message_id: int = sidecar["message_id"]
    chat_id: str = sidecar["chat_id"]
    caption: str = sidecar.get("caption", "")
    offset: int = sidecar.get("updates_offset", 0)

    deadline = time.monotonic() + timeout_s
    print(
        f"telegram_approval: polling for {approval_id} "
        f"(timeout {timeout_s}s) ...",
        file=sys.stderr,
    )

    while time.monotonic() < deadline:
        remaining = deadline - time.monotonic()
        lp_timeout = min(25, int(remaining))
        if lp_timeout <= 0:
            break

        try:
            updates = _get_updates(token, offset=offset, timeout_s=lp_timeout)
        except RuntimeError as exc:
            print(f"telegram_approval: poll error (retrying): {exc}", file=sys.stderr)
            time.sleep(poll_interval_s)
            continue

        for upd in updates:
            new_offset = upd["update_id"] + 1
            if new_offset > offset:
                offset = new_offset
                _patch_sidecar(piece_dir, updates_offset=offset)

            # Check for our callback.
            cb = upd.get("callback_query")
            if cb and cb.get("data", "").startswith(f"{_PREFIX}:"):
                parts = cb["data"].split(":", 2)
                if len(parts) == 3 and parts[2] == approval_id:
                    action = parts[1]
                    ts = datetime.now(timezone.utc).strftime("%H:%M UTC")
                    _answer_callback(token, cb["id"], f"Got it: {action}")
                    _strip_keyboard(token, chat_id, message_id)
                    _append_caption(token, chat_id, message_id, caption, f"\n\n[{action} at {ts}]")

                    notes = ""
                    if action == "iterate":
                        notes = _collect_iterate_notes(
                            token=token,
                            chat_id=chat_id,
                            message_id=message_id,
                            current_offset=offset,
                            piece_dir=piece_dir,
                            window_s=_DEFAULT_ITERATE_WINDOW_S,
                        )

                    resolved_at = datetime.now(timezone.utc).isoformat()
                    _patch_sidecar(
                        piece_dir,
                        state=action,
                        notes=notes,
                        resolved_at=resolved_at,
                        updates_offset=offset,
                    )

                    verdict = {
                        "verdict": action,
                        "notes": notes,
                        "approval_id": approval_id,
                    }
                    print(json.dumps(verdict))
                    return verdict

        if not updates:
            # Long poll returned empty: sleep briefly before re-entering.
            time.sleep(poll_interval_s)

    # Timeout reached.
    _patch_sidecar(piece_dir, state="timeout", updates_offset=offset)
    verdict = {"verdict": "timeout", "notes": "", "approval_id": approval_id}
    print(json.dumps(verdict))
    return verdict


def _collect_iterate_notes(
    token: str,
    chat_id: str,
    message_id: int,
    current_offset: int,
    piece_dir: Path,
    window_s: int,
) -> str:
    """Listen for a text reply to the approval message for up to window_s seconds.

    Returns the note text, or "" if no reply arrives within the window.
    """
    print(
        f"telegram_approval: waiting up to {window_s}s for iteration notes ...",
        file=sys.stderr,
    )
    deadline = time.monotonic() + window_s
    offset = current_offset

    while time.monotonic() < deadline:
        remaining = deadline - time.monotonic()
        lp_timeout = min(25, int(remaining))
        if lp_timeout <= 0:
            break
        try:
            updates = _get_updates(token, offset=offset, timeout_s=lp_timeout)
        except RuntimeError as exc:
            print(f"telegram_approval: note-collection error: {exc}", file=sys.stderr)
            time.sleep(2)
            continue

        for upd in updates:
            new_offset = upd["update_id"] + 1
            if new_offset > offset:
                offset = new_offset
                _patch_sidecar(piece_dir, updates_offset=offset)

            msg = upd.get("message", {})
            # Accept a text reply-to the original message, or any text from the correct chat.
            if msg.get("chat", {}).get("id") == int(chat_id) and "text" in msg:
                reply_target = (msg.get("reply_to_message") or {}).get("message_id")
                if reply_target == message_id or reply_target is None:
                    notes = msg["text"]
                    print(
                        f"telegram_approval: iteration notes received: {notes!r}",
                        file=sys.stderr,
                    )
                    return notes

    print("telegram_approval: no iteration notes received within window.", file=sys.stderr)
    return ""


def mark_done(approval_id: str, piece_dir: Path) -> None:
    """Strip keyboard and archive the sidecar if still pending."""
    token, _chat_id = _require_credentials()
    sidecar = _read_sidecar(piece_dir)
    if sidecar.get("state") == "pending":
        _strip_keyboard(token, sidecar["chat_id"], sidecar["message_id"])
        _patch_sidecar(piece_dir, state="archived")
        print(
            f"telegram_approval: {approval_id} marked as archived.",
            file=sys.stderr,
        )
    else:
        print(
            f"telegram_approval: {approval_id} state is '{sidecar.get('state')}', no action taken.",
            file=sys.stderr,
        )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _cmd_send(args: argparse.Namespace) -> int:
    piece_dir = Path(args.piece)
    image_path = Path(args.image)

    if args.dry_run:
        approval_id = f"{_PREFIX}-{secrets.token_hex(4)}"
        keyboard_row = [
            {"text": btn, "callback_data": f"{_PREFIX}:{_BUTTON_ACTIONS.get(btn, btn.lower())}:{approval_id}"}
            for btn in ("Approve", "Iterate", "Reject")
        ]
        payload = {
            "chat_id": config.telegram_chat_id or "<TELEGRAM_CHAT_ID not set>",
            "caption": args.caption,
            "reply_markup": {"inline_keyboard": [keyboard_row]},
            "photo": str(image_path),
            "_approval_id": approval_id,
            "_sidecar": str(piece_dir / _SIDECAR_NAME),
        }
        print(json.dumps(payload, indent=2))
        # Still emit the approval_id as the last line (SKILL contract).
        print(approval_id)
        return EXIT_OK

    send_for_approval(
        image_path=image_path,
        caption=args.caption,
        piece_dir=piece_dir,
    )
    return EXIT_OK


def _cmd_poll(args: argparse.Namespace) -> int:
    piece_dir = Path(args.piece)
    sidecar = _read_sidecar(piece_dir)
    approval_id = sidecar["approval_id"]
    poll_for_verdict(
        approval_id=approval_id,
        piece_dir=piece_dir,
        timeout_s=args.timeout,
    )
    return EXIT_OK


def _cmd_mark_done(args: argparse.Namespace) -> int:
    piece_dir = Path(args.piece)
    sidecar = _read_sidecar(piece_dir)
    mark_done(sidecar["approval_id"], piece_dir)
    return EXIT_OK


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="telegram_approval",
        description=(
            "Telegram inline-keyboard approval flow for jewellery-design-studio. "
            "Sends a render with Approve / Iterate / Reject buttons and polls for "
            "the verdict. Verdict is written to a per-piece approval.json sidecar."
        ),
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # -- send --
    p_send = sub.add_parser(
        "send",
        help=(
            "Send a render to Telegram with approval buttons. "
            "Prints the approval_id as the last line of stdout."
        ),
    )
    p_send.add_argument(
        "--piece",
        required=True,
        metavar="DIR",
        help="Path to the proposed piece folder (e.g. brands/my-brand/proposed/albion-garland).",
    )
    p_send.add_argument(
        "--image",
        required=True,
        metavar="PATH",
        help="Path to the JPEG preview to send.",
    )
    p_send.add_argument(
        "--caption",
        required=True,
        help="Telegram caption (structured approval prompt).",
    )
    p_send.add_argument(
        "--dry-run",
        action="store_true",
        dest="dry_run",
        help=(
            "Build and print the API payload as JSON without calling the API. "
            "Useful for verifying keyboard layout and callback_data shape."
        ),
    )
    p_send.set_defaults(func=_cmd_send)

    # -- poll --
    p_poll = sub.add_parser(
        "poll",
        help="Poll for the user's verdict. Prints JSON verdict to stdout.",
    )
    p_poll.add_argument(
        "--piece",
        required=True,
        metavar="DIR",
        help="Path to the proposed piece folder.",
    )
    p_poll.add_argument(
        "--timeout",
        type=int,
        default=1800,
        metavar="SECONDS",
        help="Maximum seconds to wait for a verdict (default: 1800).",
    )
    p_poll.set_defaults(func=_cmd_poll)

    # -- mark-done --
    p_done = sub.add_parser(
        "mark-done",
        help="Strip keyboard from the approval message and archive the sidecar.",
    )
    p_done.add_argument(
        "--piece",
        required=True,
        metavar="DIR",
        help="Path to the proposed piece folder.",
    )
    p_done.set_defaults(func=_cmd_mark_done)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
