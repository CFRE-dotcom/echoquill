"""Preset 'Ask AI' questions for the transcriber and meeting areas.

Ships with sensible defaults; the user (admin) can add or remove their own,
stored locally in the config so they persist."""

DEFAULTS = [
    "Summarize this into concise key points.",
    "List every action item and next step.",
    "Extract all the steps or instructions mentioned, in order.",
    "Pull out all names, tools, links and resources referenced.",
    "Write a short professional summary I could paste into an email.",
    "What are the key takeaways, and why do they matter?",
    "Turn this into a clean bulleted outline.",
]


def all_prompts(cfg):
    custom = (cfg or {}).get("custom_prompts") or []
    return list(DEFAULTS) + [c for c in custom if c not in DEFAULTS]


def add_prompt(cfg, text):
    text = (text or "").strip()
    if not text or text in DEFAULTS:
        return
    lst = list((cfg or {}).get("custom_prompts") or [])
    if text not in lst:
        lst.append(text)
        cfg["custom_prompts"] = lst
        _save(cfg)


def remove_prompt(cfg, text):
    lst = [t for t in ((cfg or {}).get("custom_prompts") or []) if t != text]
    cfg["custom_prompts"] = lst
    _save(cfg)


def _save(cfg):
    try:
        from . import config as _c
        _c.save(cfg)
    except Exception:
        pass
