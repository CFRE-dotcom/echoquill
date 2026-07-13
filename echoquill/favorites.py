"""Pro: pin your best clips to a Favorites list (up to 50)."""

import json
import time

from .config import app_data_dir

FAV_PATH = app_data_dir() / "favorites.json"
MAX_FAVS = 50


def _load() -> list:
    try:
        with open(FAV_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except Exception:
        return []


def _save(items: list):
    try:
        with open(FAV_PATH, "w", encoding="utf-8") as f:
            json.dump(items[:MAX_FAVS], f, indent=1, ensure_ascii=False)
    except Exception:
        pass


def all_favorites() -> list:
    return _load()


def is_favorite(text: str) -> bool:
    return any(f.get("text") == text for f in _load())


def toggle(text: str) -> bool:
    """Star/unstar a clip. Returns True if now starred."""
    items = _load()
    for f in items:
        if f.get("text") == text:
            items.remove(f)
            _save(items)
            return False
    items.insert(0, {"text": text, "ts": time.time()})
    _save(items)
    return True


def remove(text: str):
    _save([f for f in _load() if f.get("text") != text])
