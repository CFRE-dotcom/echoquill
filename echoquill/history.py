"""Local dictation history + daily stats. Nothing leaves the machine.

History lives in %APPDATA%\\EchoQuill\\history.jsonl (one JSON per line).
Stats mirror the Mac app's "today usage" card: words dictated, dictations,
and estimated minutes saved vs typing (~40 wpm typing vs ~150 wpm speaking).
"""

import json
import time
from datetime import datetime

from .config import app_data_dir

HISTORY_PATH = app_data_dir() / "history.jsonl"


def add(text: str, duration_sec: float, cfg: dict):
    if not cfg.get("history_enabled", True) or not text:
        return
    entry = {
        "ts": time.time(),
        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "text": text,
        "words": len(text.split()),
        "duration_sec": round(duration_sec, 2),
    }
    try:
        with open(HISTORY_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception:
        pass
    _trim(cfg.get("history_max_entries", 5000))


def _trim(max_entries: int):
    try:
        with open(HISTORY_PATH, "r", encoding="utf-8") as f:
            lines = f.readlines()
        if len(lines) > max_entries:
            with open(HISTORY_PATH, "w", encoding="utf-8") as f:
                f.writelines(lines[-max_entries:])
    except Exception:
        pass


def entries(limit: int = 100):
    out = []
    try:
        with open(HISTORY_PATH, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        out.append(json.loads(line))
                    except Exception:
                        continue
    except FileNotFoundError:
        pass
    return out[-limit:][::-1]  # newest first


def today_stats() -> dict:
    today = datetime.now().strftime("%Y-%m-%d")
    words = count = 0
    for e in entries(limit=100000):
        if str(e.get("date", "")).startswith(today):
            words += e.get("words", 0)
            count += 1
    minutes_saved = max(0.0, words / 40.0 - words / 150.0)  # typing vs speaking
    return {"words": words, "dictations": count,
            "minutes_saved": round(minutes_saved, 1)}


def delete(ts) -> None:
    """Remove one entry by its timestamp."""
    try:
        with open(HISTORY_PATH, "r", encoding="utf-8") as f:
            lines = f.readlines()
        kept = []
        for line in lines:
            try:
                if json.loads(line).get("ts") == ts:
                    continue
            except Exception:
                pass
            kept.append(line)
        with open(HISTORY_PATH, "w", encoding="utf-8") as f:
            f.writelines(kept)
    except FileNotFoundError:
        pass


def period_stats() -> dict:
    """Words / dictations / minutes saved for today, 7 days, 30 days, all time."""
    from datetime import timedelta
    now = datetime.now()
    cutoffs = {
        "Today": now.strftime("%Y-%m-%d"),
        "This week": (now - timedelta(days=7)),
        "This month": (now - timedelta(days=30)),
        "All time": None,
    }
    out = {k: {"words": 0, "dictations": 0} for k in cutoffs}
    for e in entries(limit=1000000):
        d = str(e.get("date", ""))[:10]
        try:
            when = datetime.strptime(d, "%Y-%m-%d")
        except Exception:
            continue
        w = e.get("words", 0)
        if d == cutoffs["Today"]:
            out["Today"]["words"] += w
            out["Today"]["dictations"] += 1
        if when >= cutoffs["This week"]:
            out["This week"]["words"] += w
            out["This week"]["dictations"] += 1
        if when >= cutoffs["This month"]:
            out["This month"]["words"] += w
            out["This month"]["dictations"] += 1
        out["All time"]["words"] += w
        out["All time"]["dictations"] += 1
    for k, v in out.items():
        v["minutes_saved"] = round(max(0.0, v["words"] / 40.0 - v["words"] / 150.0), 1)
    return out


def delete_many(ts_set) -> None:
    """Delete every entry whose timestamp is in ts_set (one file rewrite)."""
    ts_set = set(ts_set)
    try:
        with open(HISTORY_PATH, "r", encoding="utf-8") as f:
            lines = f.readlines()
        kept = []
        for line in lines:
            try:
                if json.loads(line).get("ts") in ts_set:
                    continue
            except Exception:
                pass
            kept.append(line)
        with open(HISTORY_PATH, "w", encoding="utf-8") as f:
            f.writelines(kept)
    except FileNotFoundError:
        pass


def clear():
    try:
        HISTORY_PATH.unlink(missing_ok=True)
    except Exception:
        pass
