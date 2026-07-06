"""Text cleanup: local rules (always offline) + optional cloud AI enhancement.

Local cleanup handles capitalization, spacing, and spoken punctuation.
AI enhancement is optional, off by default, and works with any
OpenAI-compatible API (OpenAI, Groq, or a local LLM server like Ollama/LM Studio).
Per-app tone: different prompt per focused application, like the Mac original.
"""

import re

# Spoken punctuation commands ("period", "comma", "new line", ...)
SPOKEN_PUNCTUATION = [
    (r"\b(new line|newline)\b\.?", "\n"),
    (r"\b(new paragraph)\b\.?", "\n\n"),
    (r"\bperiod\b", "."),
    (r"\bfull stop\b", "."),
    (r"\bcomma\b", ","),
    (r"\bquestion mark\b", "?"),
    (r"\bexclamation (mark|point)\b", "!"),
    (r"\bsemicolon\b", ";"),
    (r"\bcolon\b", ":"),
    (r"\bopen quote\b", '"'),
    (r"\bclose quote\b", '"'),
    (r"\bopen paren(thesis)?\b", "("),
    (r"\bclose paren(thesis)?\b", ")"),
    (r"\bhyphen\b", "-"),
    (r"\bdash\b", " - "),
    (r"\bellipsis\b", "..."),
]


def apply_spoken_punctuation(text: str) -> str:
    for pattern, repl in SPOKEN_PUNCTUATION:
        text = re.sub(pattern, repl, text, flags=re.IGNORECASE)
    # tidy space before punctuation inserted by voice
    text = re.sub(r"\s+([.,!?;:)])", r"\1", text)
    text = re.sub(r"([(])\s+", r"\1", text)
    return text


def local_cleanup(text: str) -> str:
    """Rule-based tidy-up that never needs the internet."""
    text = re.sub(r"[ \t]+", " ", text).strip()
    text = re.sub(r" *\n *", "\n", text)  # no stray spaces around line breaks
    # Capitalize sentence starts
    def cap(match):
        return match.group(1) + match.group(2).upper()
    text = re.sub(r"(^|[.!?]\s+|\n\s*)([a-z])", cap, text)
    # Capitalize standalone "i"
    text = re.sub(r"\bi\b", "I", text)
    # Ensure ending punctuation for multi-word dictation
    if len(text.split()) > 2 and text[-1:] not in ".!?\n:;,":
        text += "."
    return text


# Sensible built-in tones - active only when AI Enhancement is on, and the
# user's own per-app entries always win over these.
DEFAULT_TONES = {
    "outlook.exe": ("Format as an email: greeting on its own line if one was "
                    "spoken, short paragraphs, sign-off on its own line if "
                    "spoken. Use only what was said."),
    "thunderbird.exe": ("Format as an email: greeting line, paragraphs, "
                        "sign-off — only from what was spoken."),
    "winword.exe": ("Format as a document: clear paragraphs; use bullet "
                    "points when items or facts are listed."),
    "slack.exe": "Format as a chat message: tight, minimal.",
    "discord.exe": "Format as a chat message: tight, minimal.",
    "teams.exe": "Format as a chat message: concise paragraphs.",
    "ms-teams.exe": "Format as a chat message: concise paragraphs.",
    "notepad.exe": ("Format as notes: each distinct fact, number, or data "
                    "point becomes its own bullet line."),
    "onenote.exe": ("Format as notes: bullet each distinct fact or data "
                    "point."),
    "obsidian.exe": ("Format as notes: bullet each distinct fact or data "
                     "point."),
}
BROWSERS = {"chrome.exe", "msedge.exe", "firefox.exe", "brave.exe", "opera.exe"}
EMAIL_TITLE_WORDS = ("gmail", "outlook", "mail", "compose")


def get_foreground_title() -> str:
    try:
        import ctypes
        hwnd = ctypes.windll.user32.GetForegroundWindow()
        buf = ctypes.create_unicode_buffer(256)
        ctypes.windll.user32.GetWindowTextW(hwnd, buf, 256)
        return buf.value.lower()
    except Exception:
        return ""


def auto_tone(app_name: str) -> str:
    """Recognize the writing context automatically (email vs chat vs doc)."""
    if app_name in BROWSERS:
        title = get_foreground_title()
        if any(w in title for w in EMAIL_TITLE_WORDS):
            return ("Format as an email: greeting line if spoken, short "
                    "paragraphs, sign-off if spoken. Use only what was said.")
        return ""
    return DEFAULT_TONES.get(app_name, "")


def get_foreground_app() -> str:
    """Name of the focused app's process (e.g. 'slack.exe'), for per-app tone."""
    try:
        import ctypes
        import ctypes.wintypes
        import psutil
        hwnd = ctypes.windll.user32.GetForegroundWindow()
        pid = ctypes.wintypes.DWORD()
        ctypes.windll.user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        return psutil.Process(pid.value).name().lower()
    except Exception:
        return ""


def ai_enhance(text: str, cfg: dict) -> str:
    """Optional cloud/local-LLM polish. Returns original text on any failure."""
    if cfg.get("ai_auth_method", "api_key") == "oauth":
        from . import oauth, config as _cfgmod
        api_key = oauth.get_access_token(cfg, save_cb=_cfgmod.save)
    else:
        api_key = cfg.get("ai_api_key", "")
    base_url = cfg.get("ai_base_url", "").rstrip("/")
    if not base_url:
        return text
    prompt = cfg.get("ai_prompt", "Clean up this dictated text.")
    # Per-app tone, matching the Mac app's adaptive-tone feature
    app_name = get_foreground_app()
    extra = cfg.get("per_app_prompts", {}).get(app_name, "")
    if not extra:
        extra = auto_tone(app_name)   # built-in smart context recognition
    if extra:
        prompt += " " + extra
    try:
        import requests
        resp = requests.post(
            f"{base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": cfg.get("ai_model", "gpt-4o-mini"),
                # Instructions belong in the system role (community-reported fix)
                "messages": [
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": text},
                ],
                "temperature": 0.2,
            },
            timeout=20,
        )
        resp.raise_for_status()
        out = resp.json()["choices"][0]["message"]["content"].strip()
        return out or text
    except Exception:
        return text  # never lose the user's words


def process(text: str, cfg: dict, dictionary=None) -> str:
    """Full pipeline: dictionary -> spoken punctuation -> local rules -> AI."""
    if not text:
        return text
    if dictionary is not None and cfg.get("dictionary_enabled", True):
        text = dictionary.apply(text)
    if cfg.get("spoken_punctuation", True):
        text = apply_spoken_punctuation(text)
    if cfg.get("local_cleanup", True):
        text = local_cleanup(text)
    if cfg.get("ai_enhancement", False):
        text = ai_enhance(text, cfg)
    return text
