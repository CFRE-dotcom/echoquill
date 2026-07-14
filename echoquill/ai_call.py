"""One place that actually talks to the AI provider.

Handles BOTH shapes:
- OpenAI-compatible  -> POST {base}/chat/completions   (OpenAI, Groq, DeepSeek,
  local Ollama at :11434/v1, etc.)
- Ollama Cloud native -> POST https://ollama.com/api/chat   (ollama.com does NOT
  serve /v1, so the OpenAI path 404s — this is the fix for that.)
"""


def _bearer(cfg: dict) -> str:
    if cfg.get("ai_auth_method", "api_key") == "oauth":
        from . import oauth, config as cfgmod
        return oauth.get_access_token(cfg, save_cb=cfgmod.save)
    return (cfg.get("ai_api_key", "") or "").strip()


def chat(cfg: dict, system: str, user: str, temperature: float = 0.3,
         timeout: int = 60):
    """Returns (ok, text). text is the reply on success, else an error note."""
    import requests
    base = (cfg.get("ai_base_url", "") or "").rstrip("/")
    if not base:
        return (False, "Set up AI Enhancement first (Settings > AI Enhancement).")
    from .config import api_model
    model = api_model(cfg.get("ai_model", "gpt-4o-mini"))
    key = _bearer(cfg)
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    messages = [{"role": "system", "content": system},
                {"role": "user", "content": user}]
    # Native Ollama /api/chat: ollama.com (cloud) or any base ending in /api.
    native = base.endswith("/api") or (("ollama.com" in base) and not base.endswith("/v1"))
    try:
        if native:
            root = base[:-4] if base.endswith("/api") else base
            r = requests.post(root + "/api/chat", headers=headers,
                              json={"model": model, "messages": messages,
                                    "stream": False}, timeout=timeout)
            r.raise_for_status()
            out = ((r.json() or {}).get("message") or {}).get("content", "").strip()
        else:
            r = requests.post(base + "/chat/completions", headers=headers,
                              json={"model": model, "messages": messages,
                                    "temperature": temperature,
                                    "keep_alive": "30m"}, timeout=timeout)
            r.raise_for_status()
            out = r.json()["choices"][0]["message"]["content"].strip()
        return (True, out) if out else (False, "AI returned nothing.")
    except Exception as e:
        return (False, f"AI request failed: {e}")
