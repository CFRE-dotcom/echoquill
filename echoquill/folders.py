"""Clip / transcription folders - a light label store shared by the Clips tray
and the Recent-transcriptions window.

Folders are independent of Favorites: any clip (recent OR starred) can be filed
in a folder, and empty folders persist so you can create one first and move
things into it afterwards. Assignments are keyed by the clip's text, matching
how favorites.py identifies clips.
"""

import json

from .config import app_data_dir

PATH = app_data_dir() / "folders.json"


def _load() -> dict:
    try:
        with open(PATH, "r", encoding="utf-8") as f:
            d = json.load(f)
        if isinstance(d, dict):
            d.setdefault("names", [])
            d.setdefault("map", {})
            return d
    except Exception:
        pass
    return {"names": [], "map": {}}


def _save(d: dict):
    try:
        with open(PATH, "w", encoding="utf-8") as f:
            json.dump(d, f, indent=1, ensure_ascii=False)
    except Exception:
        pass


def all_folders() -> list:
    """Every folder name that exists, sorted (includes empty ones)."""
    return sorted(_load()["names"])


def create(name: str):
    """Create an (initially empty) folder."""
    name = (name or "").strip()
    if not name:
        return
    d = _load()
    if name not in d["names"]:
        d["names"].append(name)
        _save(d)


def assign(text: str, folder: str):
    """File a clip in a folder. Empty folder removes it from any folder."""
    folder = (folder or "").strip()
    d = _load()
    if folder:
        if folder not in d["names"]:
            d["names"].append(folder)
        d["map"][text] = folder
    else:
        d["map"].pop(text, None)
    _save(d)


def folder_of(text: str) -> str:
    return _load()["map"].get(text, "") or ""


def delete_folder(name: str):
    name = (name or "").strip()
    d = _load()
    if name in d["names"]:
        d["names"].remove(name)
    d["map"] = {k: v for k, v in d["map"].items() if v != name}
    _save(d)
