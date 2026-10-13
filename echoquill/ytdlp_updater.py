"""Keep the yt-dlp engine current WITHOUT rebuilding the app.

YouTube changes constantly and the yt-dlp team ships fixes almost daily. Our
bundled copy goes stale the moment that happens. This downloads the latest
yt-dlp (pure-python wheel) into %APPDATA%/EchoQuill/ytdlp and puts it first on
sys.path, so `import yt_dlp` uses the newest version automatically.
"""

import os
import sys
import time

from .config import app_data_dir

PYPI = "https://pypi.org/pypi/yt-dlp/json"
# Nightly builds get YouTube fixes days/weeks before stable. Latest release of
# the nightly repo; its assets include the pure-python wheel.
NIGHTLY_API = ("https://api.github.com/repos/yt-dlp/"
               "yt-dlp-nightly-builds/releases/latest")
# YouTube now requires a JS runtime to solve the n-challenge; without it
# downloads are throttled/blocked. We auto-install Deno (official, recommended)
# into AppData and put it on PATH so yt-dlp finds it.
DENO_URL = ("https://github.com/denoland/deno/releases/latest/download/"
            "deno-x86_64-pc-windows-msvc.zip")


def _add_path(d):
    try:
        cur = os.environ.get("PATH", "")
        if d and d not in cur.split(os.pathsep):
            os.environ["PATH"] = d + os.pathsep + cur
    except Exception:
        pass


def _deno_dir():
    d = app_data_dir() / "deno"
    d.mkdir(parents=True, exist_ok=True)
    return d


def deno_path() -> str:
    p = _deno_dir() / "deno.exe"
    return str(p) if p.exists() else ""


def ensure_deno(status_cb=lambda s: None, max_age_days=30) -> str:
    """Download the Deno JS runtime (needed to solve YouTube's JS challenges)
    into AppData and add it to PATH so yt-dlp can use it. Cached; refreshed
    about monthly. Returns the deno.exe path or ''."""
    try:
        exe = _deno_dir() / "deno.exe"
        stamp = _deno_dir() / "stamp"
        if exe.exists():
            try:
                if (stamp.exists() and (time.time() - stamp.stat().st_mtime)
                        < max_age_days * 86400):
                    _add_path(str(_deno_dir()))
                    return str(exe)
            except Exception:
                pass
        import tempfile
        import zipfile
        import shutil
        import urllib.request
        status_cb("Setting up YouTube JS runtime (Deno)…")
        zp = os.path.join(tempfile.gettempdir(), "deno_win.zip")
        req = urllib.request.Request(DENO_URL,
                                     headers={"User-Agent": "EchoQuill"})
        with urllib.request.urlopen(req, timeout=180) as resp, \
                open(zp, "wb") as fh:
            shutil.copyfileobj(resp, fh)
        with zipfile.ZipFile(zp) as zz:
            zz.extractall(str(_deno_dir()))
        try:
            stamp.write_text(str(time.time()))
        except Exception:
            pass
        _add_path(str(_deno_dir()))
        return str(exe) if exe.exists() else ""
    except Exception as e:
        status_cb(f"Deno setup skipped: {e}")
        _add_path(str(_deno_dir()))
        return deno_path()


def _latest_nightly():
    """(version, wheel_url) for the newest nightly, or (None, None)."""
    import json
    import urllib.request
    try:
        req = urllib.request.Request(
            NIGHTLY_API, headers={"User-Agent": "EchoQuill",
                                  "Accept": "application/vnd.github+json"})
        with urllib.request.urlopen(req, timeout=25) as r:
            data = json.load(r)
        ver = (data.get("tag_name") or "").strip()
        url = None
        for a in (data.get("assets") or []):
            n = a.get("name") or ""
            if n.endswith("-py3-none-any.whl"):
                url = a.get("browser_download_url")
                break
        return (ver or None, url)
    except Exception:
        return (None, None)


def _latest_stable():
    """(version, wheel_url) from PyPI, or (None, None)."""
    import json
    import urllib.request
    try:
        with urllib.request.urlopen(PYPI, timeout=25) as r:
            data = json.load(r)
        ver = data["info"]["version"]
        url = None
        for f in data["releases"].get(ver, []):
            if f["filename"].endswith("-py3-none-any.whl"):
                url = f["url"]
                break
        return (ver, url)
    except Exception:
        return (None, None)


def _dir():
    d = app_data_dir() / "ytdlp"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _site():
    return _dir() / "site"          # holds the extracted yt_dlp/ package


def installed_version() -> str:
    try:
        return (_dir() / "version.txt").read_text(encoding="utf-8").strip()
    except Exception:
        return ""


def activate() -> bool:
    """Put the downloaded yt-dlp first on sys.path (before any import yt_dlp)."""
    try:
        if (_site() / "yt_dlp" / "__init__.py").exists():
            p = str(_site())
            if p not in sys.path:
                sys.path.insert(0, p)
            return True
    except Exception:
        pass
    return False


def ensure(status_cb=lambda s: None, force=False, max_age_hours=12) -> str:
    """Download the newest yt-dlp if missing or stale. Prefers the NIGHTLY
    channel (YouTube fixes land there first), falling back to PyPI stable.
    Returns the installed version. max_age_hours=0 forces a fresh check."""
    try:
        stamp = _dir() / "stamp"
        have = (_site() / "yt_dlp" / "__init__.py").exists()
        if have and not force and max_age_hours:
            try:
                if (stamp.exists()
                        and (time.time() - stamp.stat().st_mtime)
                        < max_age_hours * 3600):
                    return installed_version()
            except Exception:
                pass
        status_cb("Checking video engine…")
        ver, url = _latest_nightly()
        if not (ver and url):
            ver, url = _latest_stable()        # fallback
        if not (ver and url):
            return installed_version()
        if have and ver == installed_version() and not force:
            try:
                stamp.write_text(str(time.time()))
            except Exception:
                pass
            return ver
        import tempfile
        import zipfile
        import shutil
        import urllib.request
        status_cb(f"Updating video engine to {ver}…")
        whl = os.path.join(tempfile.gettempdir(), "ytdlp_latest.whl")
        req = urllib.request.Request(url, headers={"User-Agent": "EchoQuill"})
        with urllib.request.urlopen(req, timeout=60) as resp, \
                open(whl, "wb") as fh:
            shutil.copyfileobj(resp, fh)
        newsite = _dir() / "site.new"
        if newsite.exists():
            shutil.rmtree(str(newsite), ignore_errors=True)
        newsite.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(whl) as z:
            for n in z.namelist():
                if n.startswith("yt_dlp/"):
                    z.extract(n, str(newsite))
        if not (newsite / "yt_dlp" / "__init__.py").exists():
            return installed_version()
        if _site().exists():
            shutil.rmtree(str(_site()), ignore_errors=True)
        os.replace(str(newsite), str(_site()))
        (_dir() / "version.txt").write_text(ver, encoding="utf-8")
        stamp.write_text(str(time.time()))
        return ver
    except Exception as e:
        status_cb(f"Engine update skipped: {e}")
        return installed_version()


def reload() -> bool:
    """Drop the cached yt_dlp modules and re-point sys.path at the downloaded
    engine, so a freshly-downloaded version takes effect IN-PROCESS — no app
    restart. Safe to call before a scan (nothing is importing yt_dlp then)."""
    try:
        for m in list(sys.modules):
            if m == "yt_dlp" or m.startswith("yt_dlp."):
                del sys.modules[m]
        return activate()
    except Exception:
        return False


def refresh(status_cb=lambda s: None) -> str:
    """Pull the newest engine right now (ignoring the 12h throttle) and
    hot-reload it so this process uses it immediately. Call before each
    scheduled watcher cycle."""
    ver = ensure(status_cb, force=False, max_age_hours=0)
    try:
        ensure_deno(status_cb)
    except Exception:
        pass
    reload()
    return ver


def update_now(status_cb=lambda s: None) -> str:
    ver = ensure(status_cb, force=True)
    reload()
    return ver
