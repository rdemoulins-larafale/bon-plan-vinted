import os

import requests

API_BASE = "https://api.telegram.org/bot{token}/{method}"


def _post(method, payload):
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        return None
    resp = requests.post(
        API_BASE.format(token=token, method=method),
        json={"chat_id": chat_id, **payload},
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json()


def send_message(text):
    result = _post(
        "sendMessage",
        {"text": text, "parse_mode": "HTML", "disable_web_page_preview": True},
    )
    return result is not None


def send_candidate(pending_id, text):
    reply_markup = {
        "inline_keyboard": [[
            {"text": "✅ Ajouter au dashboard", "callback_data": f"add:{pending_id}"},
            {"text": "✕ Ignorer", "callback_data": f"skip:{pending_id}"},
        ]]
    }
    result = _post(
        "sendMessage",
        {
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": True,
            "reply_markup": reply_markup,
        },
    )
    return result is not None
