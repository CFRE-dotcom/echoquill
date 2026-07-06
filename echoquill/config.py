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
        "base_url": "https://api.anthropic.com/v1",
        "models": sorted([
            "claude-fable-5", "claude-haiku-4-5", "claude-opus-4-8",
            "claude-sonnet-5",
        ]),
        "default_model": "claude-haiku-4-5",
        "key_hint": "Get a key at console.anthropic.com → API keys",
        "needs_key": True,
    },
    "Custom / other": {
        "base_url": "",
        "models": [],
        "default_model": "",
        "key_hint": "Any OpenAI-compatible service: enter its base URL, key, and model",
        "needs_key": True,
    },
    "Groq (fast & cheap)": {
        "base_url": "https://api.groq.com/openai/v1",
        "models": sorted([
            "gemma2-9b-it", "llama-3.1-8b-instant", "llama-3.3-70b-versatile",
            "qwen-2.5-32b",
        ]),
        "default_model": "llama-3.1-8b-instant",
        "key_hint": "Free tier available at console.groq.com",
        "needs_key": True,
    },
    "Ollama Cloud": {
        "base_url": "https://ollama.com/v1",
        "models": sorted([
            "deepseek-v3.1:671b", "gpt-oss:120b", "gpt-oss:20b",
            "qwen3-coder:480b",
        ]),
        "default_model": "gpt-oss:20b",
        "key_hint": "API key from ollama.com → settings. Runs Ollama's biggest models in their cloud.",
        "needs_key": True,
    },
    "Ollama (local, free)": {
        "base_url": "http://localhost:11434/v1",
        "models": sorted([
            "gemma3", "llama3.2", "mistral", "phi4", "qwen2.5",
        ]),
        "default_model": "llama3.2",
        "key_hint": "No key needed - install from ollama.com, then `ollama pull llama3.2`. 100% on your PC.",
        "needs_key": False,
    },
    "OpenAI": {
        "oauth_auth_url": "https://auth.openai.com/oauth/authorize",
        "oauth_token_url": "https://auth.openai.com/oauth/token",
        "base_url": "https://api.openai.com/v1",
        "models": sorted([
            "gpt-4.1", "gpt-4.1-mini", "gpt-4o", "gpt-4o-mini", "o3-mini",
        ]),
        "default_model": "gpt-4o-mini",
        "key_hint": "Get a key at platform.openai.com → API keys",
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
        "You clean up dictated text. Fix punctuation, capitalization, and "
        "obvious dictation stumbles. Keep the meaning and wording; do not add content. "
        "Return only the cleaned text."
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
    return cfg


def save(cfg: dict) -> None:
    try:
        out = dict(cfg)
        out["ai_api_key"] = _encrypt_key(out.get("ai_api_key", ""))
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(out, f, indent=2, ensure_ascii=False)
    except Exception:
        pass
