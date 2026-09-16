import json
import os
from datetime import datetime, timezone
from pathlib import Path

import requests

import facebook

DATA_DIR = Path(__file__).parent / "data"
OFFSET_FILE = DATA_DIR / "telegram_offset.json"
API_BASE = "https://api.telegram.org/bot{token}/{method}"


def _load_offset():
    if OFFSET_FILE.exists():
        return json.loads(OFFSET_FILE.read_text()).get("offset", 0)
    return 0


def _save_offset(offset):
    DATA_DIR.mkdir(exist_ok=True)
    OFFSET_FILE.write_text(json.dumps({"offset": offset}))


def _call(token, method, payload):
    resp = requests.post(API_BASE.format(token=token, method=method), json=payload, timeout=10)
    resp.raise_for_status()
    return resp.json()


def main():
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        print("TELEGRAM_BOT_TOKEN non configuré, rien à traiter.")
        return

    offset = _load_offset()
    updates = _call(token, "getUpdates", {"offset": offset, "timeout": 0}).get("result", [])

    pending = facebook._load(facebook.PENDING_FILE)
    events = facebook._load(facebook.EVENTS_FILE)
    processed = {"add": 0, "skip": 0}
    max_update_id = offset - 1

    for update in updates:
        max_update_id = max(max_update_id, update["update_id"])
        callback = update.get("callback_query")
        if not callback:
            continue
        data = callback.get("data", "")
        if ":" not in data:
            continue
        action, pending_id = data.split(":", 1)

        if action == "add" and pending_id in pending:
            entry = pending.pop(pending_id)
            entry["added_at"] = datetime.now(timezone.utc).isoformat()
            events[pending_id] = entry
            processed["add"] += 1
            _call(token, "answerCallbackQuery", {"callback_query_id": callback["id"], "text": "Ajouté au dashboard ✅"})
        elif action == "skip" and pending_id in pending:
            pending.pop(pending_id)
            processed["skip"] += 1
            _call(token, "answerCallbackQuery", {"callback_query_id": callback["id"], "text": "Ignoré"})
        else:
            _call(token, "answerCallbackQuery", {"callback_query_id": callback["id"]})

    facebook._save(facebook.PENDING_FILE, pending)
    facebook._save(facebook.EVENTS_FILE, events)
    _save_offset(max_update_id + 1)

    print(f"{processed['add']} ajoutés au dashboard, {processed['skip']} ignorés.")


if __name__ == "__main__":
    main()
