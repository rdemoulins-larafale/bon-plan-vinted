import json
import sys
from datetime import datetime, timezone
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"
PENDING_FILE = DATA_DIR / "facebook_pending.json"
EVENTS_FILE = DATA_DIR / "facebook_events.json"


def _load(path):
    if path.exists():
        return json.loads(path.read_text())
    return {}


def _save(path, data):
    DATA_DIR.mkdir(exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False, sort_keys=True))


def add_pending(pending_id, group_name, snippet, link):
    pending = _load(PENDING_FILE)
    events = _load(EVENTS_FILE)
    if pending_id in pending or pending_id in events:
        return False
    pending[pending_id] = {
        "group_name": group_name,
        "snippet": snippet,
        "link": link,
        "detected_at": datetime.now(timezone.utc).isoformat(),
    }
    _save(PENDING_FILE, pending)
    return True


if __name__ == "__main__":
    _, pending_id, group_name, snippet, link = sys.argv
    added = add_pending(pending_id, group_name, snippet, link)
    print("ajouté" if added else "déjà vu, ignoré")
