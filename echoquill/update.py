"""One-click updates. Checks the GitHub Releases page, and if a newer
version exists, downloads the installer and launches it."""

import os
import re
import tempfile

REPO = "CFRE-dotcom/echoquill"
API_LATEST = f"https://api.github.com/repos/{REPO}/releases/latest"


def _ver_tuple(v: str):
    nums = re.findall(r"\d+", v or "")
    return tuple(int(n) for n in nums[:3]) or (0,)


def check():
    """Returns (latest_version, installer_url) if newer than current, else None."""
    from . import __version__
    import requests
    r = requests.get(API_LATEST, timeout=15,
                     headers={"Accept": "application/vnd.github+json"})
    r.raise_for_status()
    data = r.json()
    latest = data.get("tag_name", "")
    if _ver_tuple(latest) <= _ver_tuple(__version__):
        return None
    url = None
    for a in data.get("assets", []):
        if a.get("name", "").endswith("Setup.exe"):
            url = a.get("browser_download_url")
            break
    if not url:  # fall back to portable exe
        for a in data.get("assets", []):
            if a.get("name", "").endswith(".exe"):
                url = a.get("browser_download_url")
                break
    return (latest.lstrip("v"), url) if url else None


def download_and_run(url: str, status_cb=lambda s: None) -> bool:
    """Download the installer to temp and launch it. Returns True on launch."""
    import requests
    status_cb("Downloading update…")
    path = os.path.join(tempfile.gettempdir(), os.path.basename(url))
    with requests.get(url, stream=True, timeout=60) as r:
        r.raise_for_status()
        with open(path, "wb") as f:
            for chunk in r.iter_content(chunk_size=1 << 16):
                f.write(chunk)
    status_cb("Updating…")
    import subprocess
    import sys
    args = [path, "/VERYSILENT", "/NORESTART", "/FORCECLOSEAPPLICATIONS"]
    # per-user installs must not silently stall on an elevation prompt
    if "appdata" in sys.executable.lower():
        args.append("/CURRENTUSER")
    try:
        subprocess.Popen(args)
    except Exception:
        os.startfile(path)   # fall back to the visible wizard
        return True
    # the installer relaunches EchoQuill itself (see installer.iss [Run]) -
    # no console/ping window is spawned.
    return True
