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
         timeout: int = 180):
    """Returns (ok, text). text is the reply on success, else an error note."""
    from .config import AI_PROVIDERS, api_model as _am
    _prov = AI_PROVIDERS.get(cfg.get("ai_provider", ""), {})
    if _prov.get("backend") == "codex_cli":
        from . import codex_cli
        return codex_cli.chat(system, user,
                              model=_am(cfg.get("ai_model", "gpt-5.5")) or "gpt-5.5",
                              timeout=max(timeout, 180))
    # Use Python's BUILT-IN HTTP (urllib), NOT requests. requests rides on
    # urllib3, which yt-dlp monkey-patches ('Urllib3PercentREOverride'); once
    # yt-dlp runs in-process that patch breaks every requests call, which was
    # failing the AI with "object has no attribute 'sub'". Stdlib urllib is
    # independent of urllib3, so the AI calls can't be broken by the video
    # engine.
    import urllib.error
    from . import nethttp
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
            j = nethttp.post_json(root + "/api/chat", headers=headers,
                                  json_body={"model": model,
                                             "messages": messages,
                                             "stream": False}, timeout=timeout)
            out = ((j or {}).get("message") or {}).get("content", "").strip()
        else:
            j = nethttp.post_json(base + "/chat/completions", headers=headers,
                                  json_body={"model": model,
                                             "messages": messages,
                                             "temperature": temperature,
                                             "keep_alive": "30m"},
                                  timeout=timeout)
            out = j["choices"][0]["message"]["content"].strip()
        return (True, out) if out else (False, "AI returned nothing.")
    except urllib.error.HTTPError as e:
        try:
            body = e.read().decode("utf-8", "replace")[:200]
        except Exception:
            body = ""
        return (False, f"AI request failed: HTTP {e.code} {body}".strip())
    except Exception as e:
        return (False, f"AI request failed: {e}")
