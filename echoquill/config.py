"""Configuration management for EchoQuill.

Settings are stored as JSON in %APPDATA%\\EchoQuill\\config.json.
Everything is optional and privacy-first: no cloud features are enabled
unless the user explicitly turns them on.
"""

import json
import os
from pathlib import Path

APP_NAME = "EchoQuill"


def app_data_dir() -> Path:
    base = os.environ.get("APPDATA", str(Path.home()))
    d = Path(base) / APP_NAME
    d.mkdir(parents=True, exist_ok=True)
    return d


CONFIG_PATH = app_data_dir() / "config.json"

# Model choices = the "different speeds". Smaller = faster, larger = more
# accurate. All run 100% locally and free. Shown to users in plain English.
MODEL_CHOICES = {
    "tiny":   "Fastest - good for quick notes (~75 MB)",
    "base":   "Fast - great everyday balance (~140 MB)",
    "small":  "Accurate - slightly slower (~460 MB)",
    "medium": "Very accurate - needs a decent PC (~1.5 GB)",
    "large-v3": "Best accuracy - slowest, 99 languages (~3 GB)",
}

# Plain-English names shown in Settings (internal id -> label)
MODEL_LABELS = {
    "tiny":     "Fastest — quick notes, less accurate",
    "base":     "Balanced — recommended default",
    "small":    "Accurate — slightly slower",
    "medium":   "Very accurate — noticeably slower, strong PC",
    "large-v3": "Maximum accuracy — slow, best for videos/files",
}
MODEL_IDS = {v: k for k, v in MODEL_LABELS.items()}

PREVIEW_LABELS = {
    "tiny":  "Fastest (recommended)",
    "base":  "Balanced",
    "small": "Accurate (slower live words)",
}
PREVIEW_IDS = {v: k for k, v in PREVIEW_LABELS.items()}

# AI Enhancement providers. All use the same OpenAI-compatible chat API.
# Model lists are starting points - the model box stays editable for new ones.
AI_PROVIDERS = {
    "Anthropic (Claude)": {
        "oauth_auth_url": "", "oauth_token_url": "",
        "base_url": "https://api.anthropic.com/v1",
        "models": ["claude-fable-5 (thinking)", "claude-haiku-4-5",
                   "claude-opus-4-8 (thinking)", "claude-sonnet-5"],
        "default_model": "claude-haiku-4-5",
        "key_hint": "Key from console.anthropic.com. Haiku is fastest; Opus/Fable think (slower).",
        "needs_key": True,
    },
    "Custom / other": {
        "base_url": "", "models": [], "default_model": "",
        "key_hint": "Any OpenAI-compatible service: enter base URL, key, and model.",
        "needs_key": True,
    },
    "DeepSeek": {
        "base_url": "https://api.deepseek.com/v1",
        "models": ["deepseek-v4-flash", "deepseek-v4-pro (thinking)"],
        "default_model": "deepseek-v4-flash",
        "key_hint": "Key from platform.deepseek.com. Flash is fast; Pro thinks.",
        "needs_key": True,
    },
    "Groq (fast)": {
        "base_url": "https://api.groq.com/openai/v1",
        "models": ["gpt-oss-120b", "gpt-oss-20b", "llama-3.3-70b-versatile",
                   "qwen3-32b (thinking)"],
        "default_model": "gpt-oss-20b",
        "key_hint": "Free tier at console.groq.com. Blazing fast (900+ tokens/sec).",
        "needs_key": True,
    },
    "Ollama (local, free)": {
        "base_url": "http://localhost:11434/v1",
        "models": ["gemma4", "gpt-oss", "llama3.3", "qwen3.5"],
        "default_model": "qwen3.5",
        "key_hint": "No key. Install from ollama.com, then e.g. `ollama pull qwen3.5`. Runs on your PC.",
        "needs_key": False,
    },
    "Ollama Cloud": {
        "base_url": "https://ollama.com/api",
        "models": ["deepseek-v4-flash", "deepseek-v4-pro (thinking)",
                   "gemini-3-flash-preview", "glm-5.2 (thinking)",
                   "gpt-oss", "kimi-k2.7-code (thinking)", "qwen3.5",
                   "qwen3-coder"],
        "default_model": "gemini-3-flash-preview",
        "key_hint": "Key from ollama.com. Flash/gpt-oss/qwen are fast; glm/deepseek/kimi think (slower, smarter).",
        "needs_key": True,
    },
    "OpenAI": {
        "oauth_auth_url": "https://auth.openai.com/oauth/authorize",
        "oauth_token_url": "https://auth.openai.com/oauth/token",
        "base_url": "https://api.openai.com/v1",
        "models": ["gpt-5.4-mini", "gpt-5.4-nano", "gpt-5.5 (thinking)",
                   "gpt-5.5-pro (thinking)"],
        "default_model": "gpt-5.4-mini",
        "key_hint": "Key from platform.openai.com. Mini/nano are fast; 5.5 thinks.",
        "needs_key": True,
    },
    "Qwen": {
        "base_url": "https://dashscope-intl.aliyuncs.com/compatible-mode/v1",
        "models": ["qwen3.5", "qwen3.7-max", "qwen3.7-plus", "qwen3-coder"],
        "default_model": "qwen3.5",
        "key_hint": "Key from Alibaba DashScope. qwen3.5 is a fast all-rounder.",
        "needs_key": True,
    },
    "Z.AI (GLM)": {
        "base_url": "https://api.z.ai/api/paas/v4",
        "models": ["glm-4.7", "glm-5.1 (thinking)", "glm-5.2 (thinking)"],
        "default_model": "glm-4.7",
        "key_hint": "Key from z.ai. 5.1/5.2 think (slower, smarter); 4.7 is faster.",
        "needs_key": True,
    },
}

DEFAULTS = {
    # Activation: "toggle" = press hotkey to start, again to stop.
    #             "hold"   = hold the hold_key down while talking (like the Mac app).
    "activation_mode": "toggle",
    "hotkey": "ctrl+alt+space",
    "hold_key": "right alt",
    # Live preview: words appear in the overlay while you speak.
    # Uses its own ultra-fast model so preview never lags behind your voice;
    # the final text still comes from your main (accurate) model.
    "live_preview": True,
    "preview_model": "tiny",
    # Whisper model size (speed vs accuracy)
    "model": "base",
    # Language code like "en", or "auto" to detect
    "language": "auto",
    "yt_cookies_browser": "",
    "custom_prompts": [],   # "" off, else chrome/edge/firefox/brave for member-only videos
    # How text is inserted: "type" (keystrokes), "paste" (Ctrl+V),
    # "clipboard" (copy only - community-requested clipboard-only mode)
    "insertion_mode": "paste",
    # Community-requested improvements, all on by default:
    "tail_ms": 400,           # keep recording briefly after stop so the last word isn't cut off
    "start_cue": True,        # beep only AFTER the mic is truly ready so the first word isn't missed
    "end_cue": True,
    "duck_media": True,       # lower other apps' audio while dictating (instead of pausing)
    "preferred_mic": "",      # lock to a specific microphone by name ("" = system default)
    # Local cleanup (always offline)
    "local_cleanup": True,        # capitalization, spacing, sentence punctuation
    "spoken_punctuation": True,   # say "period", "comma", "new line" to insert them
    # Custom dictionary + learning from corrections
    "dictionary_enabled": True,
    "learn_corrections": True,    # suggest dictionary entries from repeated corrections
    # Optional cloud AI enhancement - OFF by default, bring your own key
    "ai_enhancement": False,
    "ai_on_dictation": False,
    "ai_provider": "OpenAI",
    # Auth: "api_key" or "oauth" (sign in with your provider account).
    # OAuth needs a Client ID from the provider's developer program.
    "ai_auth_method": "api_key",
    "ai_oauth_client_id": "",
    "ai_oauth_auth_url": "",
    "ai_oauth_token_url": "",
    "ai_oauth_scope": "openid profile email offline_access",
    "ai_oauth_tokens": {},
    "ai_base_url": "https://api.openai.com/v1",   # any OpenAI-compatible API (OpenAI, Groq, local LLM, ...)
    "ai_api_key": "",
    "ai_model": "gpt-4o-mini",
    "ai_prompt": (
        "You format dictated speech into properly structured text. Fix "
        "punctuation, capitalization, and dictation stumbles. Structure it: "
        "break into paragraphs where natural; when the speaker lists items, "
        "facts, or data points, format them as bullet points; when they "
        "dictate an email (greeting, body, sign-off), lay it out as one. "
        "Never invent content, names, or facts that were not spoken. "
        "Return only the formatted text."
    ),
    # Per-app tone profiles: map process name -> extra prompt
    "per_app_prompts": {
        # "slack.exe": "Casual tone, lowercase ok, friendly.",
        # "outlook.exe": "Formal business email tone.",
    },
    # Safety net: every transcription is ALSO left on the clipboard, so if
    # text didn't land where you wanted, just press Ctrl+V.
    "always_copy": True,
    # History & stats (local only)
    "history_enabled": True,
    "history_max_entries": 5000,
    # Overlay
    "overlay_enabled": True,
    "theme": "dark",
    "keep_audio": False,
    "audio_max_mb": 500,
    "auto_check_updates": True,
    "admin_mode": False,
    # Start EchoQuill automatically with Windows (in-app toggle)
    "autostart": False,
    # Command Mode: control the PC by voice ("open chrome", "press enter"...)
    "command_mode": True,
    "command_hotkey": "ctrl+alt+c",
    # Write Mode: select text anywhere, speak, and it gets rewritten/replaced
    "write_mode": True,
    "write_hotkey": "ctrl+alt+w",
    # Magic word: start a NORMAL dictation with this word to run a command
    # instead ("computer, open chrome"). The natural way in.
    "prefix_commands": True,
    "command_prefix": "computer",
    # Where batch video transcripts are saved
    "transcripts_dir": "",
    # Free version: lifetime video-transcription allowance
    "transcriptions_used": 0,
    "transcription_limit": 5,
    # Where the Upgrade links point (swap to your website when it's live)
    "upgrade_url": "https://echo-quill.com/#pricing",
}


def _dpapi(data: bytes, decrypt: bool) -> bytes:
    """Encrypt/decrypt with the Windows Data Protection API (per-user)."""
    import ctypes
    import ctypes.wintypes as wt

    class BLOB(ctypes.Structure):
        _fields_ = [("cbData", wt.DWORD), ("pbData", ctypes.POINTER(ctypes.c_char))]

    buf = ctypes.create_string_buffer(data, len(data))
    blob_in = BLOB(len(data), ctypes.cast(buf, ctypes.POINTER(ctypes.c_char)))
    blob_out = BLOB()
    fn = (ctypes.windll.crypt32.CryptUnprotectData if decrypt
          else ctypes.windll.crypt32.CryptProtectData)
    if not fn(ctypes.byref(blob_in), None, None, None, None, 0, ctypes.byref(blob_out)):
        raise OSError("DPAPI failed")
    try:
        return ctypes.string_at(blob_out.pbData, blob_out.cbData)
    finally:
        ctypes.windll.kernel32.LocalFree(blob_out.pbData)


def _encrypt_key(key: str) -> str:
    """API key -> 'dpapi:<base64>' so it is never stored readable on disk."""
    if not key or key.startswith("dpapi:"):
        return key
    try:
        import base64
        return "dpapi:" + base64.b64encode(_dpapi(key.encode("utf-8"), False)).decode()
    except Exception:
        return key  # non-Windows or DPAPI unavailable: store as-is


def _decrypt_key(key: str) -> str:
    if not key.startswith("dpapi:"):
        return key
    try:
        import base64
        return _dpapi(base64.b64decode(key[6:]), True).decode("utf-8")
    except Exception:
        return ""


def api_model(name: str) -> str:
    """Drop the human-friendly ' (thinking)' tag before sending to the API."""
    return (name or "").split(" (")[0].strip()


KEYRING_MARK = "__stored_in_credential_manager__"
_SECRET_KEYS = ("ai_api_key", "pro_license_key")


def _kr_backend():
    import keyring
    try:
        from keyring.backends import Windows
        if Windows.WinVaultKeyring.viable:
            keyring.set_keyring(Windows.WinVaultKeyring())
    except Exception:
        pass
    return keyring


def _kr_set(name: str, value: str) -> bool:
    """Store a secret in Windows Credential Manager. True if it worked."""
    try:
        keyring = _kr_backend()
        if value:
            keyring.set_password("EchoQuill", name, value)
        else:
            try:
                keyring.delete_password("EchoQuill", name)
            except Exception:
                pass
        return True
    except Exception:
        return False


def _kr_get(name: str) -> str:
    try:
        keyring = _kr_backend()
        return keyring.get_password("EchoQuill", name) or ""
    except Exception:
        return ""


def load() -> dict:
    cfg = dict(DEFAULTS)
    try:
        if CONFIG_PATH.exists():
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                saved = json.load(f)
            if isinstance(saved, dict):
                cfg.update(saved)
    except Exception:
        pass  # fall back to defaults on any corruption
    for k in _SECRET_KEYS:
        v = cfg.get(k, "")
        if v == KEYRING_MARK:
            cfg[k] = _kr_get(k)                 # read from Credential Manager
        else:
            plain = _decrypt_key(v)             # migrate any legacy DPAPI value
            if plain and _kr_set(k, plain):
                cfg[k] = plain
            else:
                cfg[k] = plain or ""
    # migrate old Ollama Cloud base (ollama.com/v1 -> native /api, which works)
    if (cfg.get("ai_base_url", "") or "").rstrip("/") == "https://ollama.com/v1":
        cfg["ai_base_url"] = "https://ollama.com/api"
    return cfg


def save(cfg: dict) -> None:
    try:
        out = dict(cfg)
        for k in _SECRET_KEYS:
            val = out.get(k, "")
            if not val:
                existing = _kr_get(k)          # don't blank an existing stored key
                if existing:
                    out[k] = KEYRING_MARK
                    continue
            if _kr_set(k, val):
                out[k] = KEYRING_MARK if val else ""
            else:
                out[k] = _encrypt_key(val)
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(out, f, indent=2, ensure_ascii=False)
    except Exception:
        pass
