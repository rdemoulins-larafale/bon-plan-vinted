import json
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path

import requests

SOURCES = {
    "vide-greniers": "https://vide-greniers.org/evenements/Paris-75",
    "vente-solidaire": "https://vente-solidaire.org/evenements/Paris-75",
}

HEADERS = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}

JSONLD_RE = re.compile(r'<script type="application/ld\+json">(.*?)</script>', re.S)
POSTAL_CODE_RE = re.compile(r"\b750(0[1-9]|1[0-9]|20)\b")
ARRONDISSEMENT_RE = re.compile(r"paris[\s\-]?(\d{1,2})(?:er|e|ème|eme)?\b", re.I)

DATA_FILE = Path(__file__).parent / "data" / "events.json"
HORIZON_WEEKS = 8


def fetch_page(url):
    resp = requests.get(url, headers=HEADERS, timeout=15)
    resp.raise_for_status()
    return resp.text


def parse_events(html):
    events = []
    for block in JSONLD_RE.findall(html):
        try:
            data = json.loads(block)
        except json.JSONDecodeError:
            continue
        if isinstance(data, dict) and data.get("@type") == "Event":
            events.append(data)
    return events


def is_paris_intra_muros(event):
    address = event.get("location", {}).get("address", {})
    return address.get("addressLocality") == "Paris-75"


def guess_arrondissement(event):
    location = event.get("location", {})
    text = f"{location.get('name', '')} {event.get('name', '')} {event.get('description', '')[:300]}"
    postal_match = POSTAL_CODE_RE.search(text)
    if postal_match:
        return int(postal_match.group(1))
    name_match = ARRONDISSEMENT_RE.search(text)
    if name_match:
        arr = int(name_match.group(1))
        if 1 <= arr <= 20:
            return arr
    return None


def normalize(event, source):
    location = event.get("location", {})
    return {
        "id": event.get("@id"),
        "source": source,
        "name": event.get("name"),
        "start_date": event.get("startDate"),
        "end_date": event.get("endDate"),
        "arrondissement": guess_arrondissement(event),
        "location_name": location.get("name"),
        "lat": location.get("geo", {}).get("latitude"),
        "lon": location.get("geo", {}).get("longitude"),
        "organizer": event.get("organizer", {}).get("name"),
        "url": event.get("url"),
    }


def scrape_source(base_url, weeks_ahead=HORIZON_WEEKS):
    events = []
    offset = None
    for _ in range(weeks_ahead):
        url = base_url if offset is None else f"{base_url}?offset={offset}"
        html = fetch_page(url)
        page_events = parse_events(html)
        if not page_events:
            break
        events.extend(page_events)
        latest = max(datetime.strptime(e["startDate"], "%d/%m/%Y") for e in page_events)
        offset = (latest + timedelta(days=1)).strftime("%Y-%m-%d")
    return events


def scrape_all():
    results = {}
    for source, base_url in SOURCES.items():
        for event in scrape_source(base_url):
            if not is_paris_intra_muros(event):
                continue
            normalized = normalize(event, source)
            results[normalized["id"]] = normalized
    return results


def load_previous():
    if DATA_FILE.exists():
        return json.loads(DATA_FILE.read_text())
    return {}


def save(events):
    DATA_FILE.parent.mkdir(exist_ok=True)
    DATA_FILE.write_text(json.dumps(events, indent=2, ensure_ascii=False, sort_keys=True))


def main():
    previous = load_previous()
    current = scrape_all()
    new_ids = sorted(set(current) - set(previous))
    save(current)

    print(f"{len(current)} événements Paris intra-muros ({HORIZON_WEEKS} semaines), {len(new_ids)} nouveaux.")
    for event_id in new_ids:
        e = current[event_id]
        arr = f"{e['arrondissement']}e" if e["arrondissement"] else "?"
        print(f"NOUVEAU [{e['source']}] {e['name']} — {e['start_date']} — {e['location_name']} (Paris {arr}) — {e['url']}")


if __name__ == "__main__":
    sys.exit(main())
