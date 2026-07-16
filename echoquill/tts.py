"""Text-to-speech - turn text (or a document) into spoken audio.

Pro feature. Uses YOUR ElevenLabs account (bring your own API key), kept in
Windows Credential Manager. No ffmpeg needed: playback pulls raw PCM and plays
it with the built-in Windows player; saving concatenates MP3 chunks directly.
Long text is split at sentence boundaries.
"""

import os
import re
import traceback

ELEVEN_BASE = "https://api.elevenlabs.io/v1"
DEFAULT_VOICE = "21m00Tcm4TlvDq8ikWAM"   # "Rachel" - a stock ElevenLabs voice
DEFAULT_MODEL = "eleven_multilingual_v2"
CHUNK_LIMIT = 2400
PCM_RATE = 22050                          # pcm_22050 -> 16-bit mono


def _key(cfg):
    return (cfg.get("elevenlabs_api_key") or "").strip()


def log_error(where, exc):
    """Record a failure so we can always see what went wrong."""
    try:
        from .config import app_data_dir
        path = app_data_dir() / "tts_error.log"
        with open(path, "a", encoding="utf-8") as f:
            import datetime
            f.write(f"\n===== {datetime.datetime.now():%Y-%m-%d %H:%M:%S} "
                    f"[{where}] =====\n")
            if isinstance(exc, BaseException):
                f.write("".join(traceback.format_exception(
                    type(exc), exc, exc.__traceback__)))
            else:
                f.write(str(exc) + "\n")
    except Exception:
        pass


def list_voices(cfg):
    """[(name, voice_id), ...] from the user's ElevenLabs account (or [])."""
    import requests
    key = _key(cfg)
    if not key:
        return []
    r = requests.get(f"{ELEVEN_BASE}/voices",
                     headers={"xi-api-key": key}, timeout=30)
    if r.status_code != 200:
        raise RuntimeError(_friendly(r))
    return [(v.get("name", ""), v.get("voice_id", ""))
            for v in r.json().get("voices", []) if v.get("voice_id")]


def _chunks(text, limit=CHUNK_LIMIT):
    text = (text or "").strip()
    if len(text) <= limit:
        return [text] if text else []
    parts, cur = [], ""
    for sent in re.split(r'(?<=[.!?])\s+', text):
        if len(sent) > limit:
            if cur:
                parts.append(cur.strip()); cur = ""
            for i in range(0, len(sent), limit):
                parts.append(sent[i:i + limit])
            continue
        if len(cur) + len(sent) + 1 > limit and cur:
            parts.append(cur.strip()); cur = ""
        cur += (" " if cur else "") + sent
    if cur.strip():
        parts.append(cur.strip())
    return parts


def _synth_bytes(text, cfg, voice_id, output_format):
    """Raw audio bytes for one chunk in the requested output_format."""
    import requests
    body = {
        "text": text,
        "model_id": cfg.get("tts_model_id") or DEFAULT_MODEL,
        "voice_settings": {
            "stability": float(cfg.get("tts_stability", 0.5) or 0.5),
            "similarity_boost": float(cfg.get("tts_similarity", 0.75) or 0.75),
        },
    }
    url = f"{ELEVEN_BASE}/text-to-speech/{voice_id}?output_format={output_format}"
    r = requests.post(url, headers={"xi-api-key": _key(cfg),
                                    "content-type": "application/json"},
                      json=body, timeout=180)
    if r.status_code != 200:
        raise RuntimeError(_friendly(r))
    return r.content


def _prep(text, cfg, voice_id):
    if not _key(cfg):
        raise RuntimeError("Add your ElevenLabs API key first.")
    parts = _chunks(text)
    if not parts:
        raise RuntimeError("Nothing to read - the text is empty.")
    return parts, (voice_id or cfg.get("tts_voice_id") or DEFAULT_VOICE)


def synth_pcm(text, cfg, voice_id, status_cb=None):
    """Return raw 16-bit mono PCM (22050 Hz) for the whole text."""
    parts, voice_id = _prep(text, cfg, voice_id)
    pcm = bytearray()
    for i, p in enumerate(parts):
        if status_cb and len(parts) > 1:
            status_cb(f"Generating audio… ({i + 1}/{len(parts)})")
        pcm += _synth_bytes(p, cfg, voice_id, "pcm_22050")
    return bytes(pcm)


def pcm_to_wav(pcm, wav_path, rate=PCM_RATE):
    import wave
    with wave.open(wav_path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(pcm)
    return wav_path


def synthesize_to_mp3(text, cfg, voice_id, out_mp3, status_cb=None):
    """Write the whole text to one mp3 (chunks concatenated as a stream)."""
    parts, voice_id = _prep(text, cfg, voice_id)
    with open(out_mp3, "wb") as out:
        for i, p in enumerate(parts):
            if status_cb and len(parts) > 1:
                status_cb(f"Generating audio… ({i + 1}/{len(parts)})")
            out.write(_synth_bytes(p, cfg, voice_id, "mp3_44100_128"))
    return out_mp3


def read_document(path):
    """Pull plain text out of .txt/.md/.docx/.pdf for reading aloud."""
    ext = os.path.splitext(path)[1].lower()
    if ext in (".txt", ".md", ".text", ""):
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            return f.read()
    if ext == ".docx":
        try:
            import docx
        except Exception:
            raise RuntimeError("Reading .docx files needs the python-docx library.")
        return "\n".join(p.text for p in docx.Document(path).paragraphs)
    if ext == ".pdf":
        try:
            from pypdf import PdfReader
        except Exception:
            try:
                from PyPDF2 import PdfReader
            except Exception:
                raise RuntimeError("Reading .pdf files needs the pypdf library.")
        return "\n".join((pg.extract_text() or "") for pg in PdfReader(path).pages)
    raise RuntimeError(f"Unsupported file type: {ext or 'unknown'}")


def _friendly(r):
    try:
        detail = r.json().get("detail")
        if isinstance(detail, dict):
            msg = detail.get("message") or detail.get("status") or str(detail)
        else:
            msg = str(detail)
    except Exception:
        msg = (r.text or "")[:300]
    if r.status_code in (401, 403):
        return "ElevenLabs rejected the request (key or plan permission). " + str(msg)
    if r.status_code == 422:
        return f"ElevenLabs couldn't process that: {msg}"
    if r.status_code == 429:
        return "ElevenLabs quota/rate limit hit - check your plan usage."
    return f"ElevenLabs error {r.status_code}: {msg}"
