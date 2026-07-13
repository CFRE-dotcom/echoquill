"""Ask AI to rewrite / reformat / answer about a piece of text in place.

Used by the Edit dialogs (clips, recent transcriptions). Uses whichever
AI provider the user configured under Settings -> AI Enhancement.
"""


def _bearer(cfg: dict) -> str:
    if cfg.get("ai_auth_method", "api_key") == "oauth":
        from . import oauth, config as cfgmod
        return oauth.get_access_token(cfg, save_cb=cfgmod.save)
    return (cfg.get("ai_api_key", "") or "").strip()


def transform(text: str, instruction: str, cfg: dict):
    """Returns (ok, result). On success result is the revised text (or an
    answer); on failure result is a short error message."""
    import requests
    base_url = (cfg.get("ai_base_url", "") or "").rstrip("/")
    if not base_url:
        return (False, "Set up AI Enhancement first (Settings > AI Enhancement).")
    system = (
        "You are an in-line text editor. Apply the user's instruction to the "
        "TEXT they provide. Return ONLY the resulting text - no preamble, no "
        "explanation, no surrounding quotes. Keep the user's meaning; change "
        "only what the instruction asks. If the instruction is a question "
        "about the text rather than an edit, answer it directly and concisely."
    )
    user = f"INSTRUCTION:\n{instruction.strip()}\n\nTEXT:\n{text}"
    try:
        from .config import api_model
        r = requests.post(
            f"{base_url}/chat/completions",
            headers={"Authorization": f"Bearer {_bearer(cfg)}",
                     "Content-Type": "application/json"},
            json={"model": api_model(cfg.get("ai_model", "gpt-4o-mini")),
                  "messages": [{"role": "system", "content": system},
                               {"role": "user", "content": user}],
                  "temperature": 0.3, "keep_alive": "30m"},
            timeout=60)
        r.raise_for_status()
        out = r.json()["choices"][0]["message"]["content"].strip()
        return (True, out) if out else (False, "AI returned nothing.")
    except Exception as e:
        return (False, f"AI request failed: {e}")
