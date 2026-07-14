"""Pro: Ask AI about a transcript - answers grounded in the video's own words,
with timestamps cited, using whichever AI provider the user configured."""


def _bearer(cfg: dict) -> str:
    if cfg.get("ai_auth_method", "api_key") == "oauth":
        from . import oauth, config as cfgmod
        return oauth.get_access_token(cfg, save_cb=cfgmod.save)
    return (cfg.get("ai_api_key", "") or "").strip()


def ask(question: str, segments, cfg: dict) -> str:
    """segments: list of (seconds, text). Returns the answer or an error note."""
    import requests
    base_url = (cfg.get("ai_base_url", "") or "").rstrip("/")
    if not base_url:
        return "Set up AI Enhancement first (Settings → AI Enhancement)."

    def stamp(sec):
        sec = int(sec or 0)
        h, m, s2 = sec // 3600, (sec % 3600) // 60, sec % 60
        return f"{h}:{m:02d}:{s2:02d}" if h else f"{m:02d}:{s2:02d}"

    lines = [f"[{stamp(sec)}] {text}" for sec, text in segments]
    context = "\n".join(lines)
    if len(context) > 24000:                      # keep within model limits
        context = context[:12000] + "\n[...]\n" + context[-12000:]

    system = (
        "You answer questions about a video using ONLY its transcript below. "
        "Cite the timestamp(s) where the answer appears, like [12:34]. "
        "If the transcript doesn't contain the answer, say exactly: "
        "\"The video doesn't cover that.\" Do not use outside knowledge.\n\n"
        "TRANSCRIPT:\n" + context)
    from . import ai_call
    ok, out = ai_call.chat(cfg, system, question, temperature=0.1, timeout=180)
    return out
