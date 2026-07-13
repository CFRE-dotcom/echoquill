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
    tail = "/VERYSILENT /NORESTART /FORCECLOSEAPPLICATIONS"
    # per-user installs must not silently stall on an elevation prompt
    if "appdata" in sys.executable.lower():
        tail += " /CURRENTUSER"
    # mark that an update is underway so the relaunched copy waits for the
    # old instance's single-instance lock to clear instead of refusing.
    try:
        from .config import app_data_dir
        (app_data_dir() / "update_in_progress").touch()
    except Exception:
        pass
    # Run the installer only AFTER EchoQuill has fully exited, so its files and
    # single-instance lock are released first (otherwise Setup says "close all
    # instances"). A HIDDEN wscript waiter handles the delay - no console/ping
    # window. EchoQuill quits itself right after this returns.
    setup = path.replace('"', '""')
    vbs = os.path.join(tempfile.gettempdir(), "echoquill_update.vbs")
    try:
        with open(vbs, "w", encoding="utf-8") as f:
            f.write('Set sh = CreateObject("WScript.Shell")\r\n')
            f.write('WScript.Sleep 2000\r\n')          # give EchoQuill time to exit
            f.write('sh.Run """%s"" %s", 0, False\r\n' % (setup, tail))
        subprocess.Popen(["wscript.exe", vbs], creationflags=0x08000000)  # CREATE_NO_WINDOW
    except Exception:
        try:
            subprocess.Popen([path] + tail.split())
        except Exception:
            os.startfile(path)   # last-ditch: visible wizard
    return True
