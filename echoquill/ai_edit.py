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
    """Returns (ok, result). Rewrites/answers using the configured provider."""
    from . import ai_call
    system = (
        "You are an in-line text editor. Apply the user's instruction to the "
        "TEXT they provide. Return ONLY the resulting text - no preamble, no "
        "explanation, no surrounding quotes. Keep the user's meaning; change "
        "only what the instruction asks. If the instruction is a question "
        "about the text rather than an edit, answer it directly and concisely."
    )
    user = f"INSTRUCTION:\n{instruction.strip()}\n\nTEXT:\n{text}"
    return ai_call.chat(cfg, system, user, temperature=0.3)
