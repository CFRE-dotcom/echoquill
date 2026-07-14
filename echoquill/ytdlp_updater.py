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
    """Download the newest yt-dlp if missing or stale. Returns the version."""
    try:
        stamp = _dir() / "stamp"
        have = (_site() / "yt_dlp" / "__init__.py").exists()
        if have and not force:
            try:
                if stamp.exists() and (time.time() - stamp.stat().st_mtime) < max_age_hours * 3600:
                    return installed_version()
            except Exception:
                pass
        import json
        import urllib.request
        status_cb("Checking video engine…")
        with urllib.request.urlopen(PYPI, timeout=25) as r:
            data = json.load(r)
        ver = data["info"]["version"]
        if have and ver == installed_version() and not force:
            try:
                stamp.write_text(str(time.time()))
            except Exception:
                pass
            return ver
        url = None
        for f in data["releases"].get(ver, []):
            if f["filename"].endswith("-py3-none-any.whl"):
                url = f["url"]; break
        if not url:
            return installed_version()
        import tempfile
        import zipfile
        import shutil
        status_cb(f"Updating video engine to {ver}…")
        whl = os.path.join(tempfile.gettempdir(), "ytdlp_latest.whl")
        urllib.request.urlretrieve(url, whl)
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


def update_now(status_cb=lambda s: None) -> str:
    ver = ensure(status_cb, force=True)
    activate()
    return ver
