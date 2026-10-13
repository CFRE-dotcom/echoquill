"""Local ChatGPT-subscription models via the Codex CLI (no API key).

This ONLY works on the user's own machine: the official Codex client generates
a local device attestation the OpenAI edge requires, so the subscription path
can't run from cloud/datacenter IPs. EchoQuill runs locally, so shelling out to
`codex exec` gives GPT-5.5 on the user's ChatGPT plan with no key and no
in-app OAuth. One-time setup on the user's side: install Codex, run `codex login`.
"""

import os
import shutil
import subprocess
import tempfile


def available() -> bool:
    return shutil.which("codex") is not None


def status():
    """Return (ok, message) describing the local Codex CLI state."""
    if not available():
        return (False, "Codex CLI not found on PATH. Install it, then run: "
                       "codex login")
    try:
        r = subprocess.run(["codex", "login", "status"],
                           capture_output=True, text=True, timeout=25)
        out = (r.stdout + r.stderr).strip()
        if r.returncode == 0 or "logged in" in out.lower():
            return (True, out or "Logged in with ChatGPT")
        return (False, out or "Not logged in — run: codex login")
    except Exception as e:
        return (False, f"Codex check failed: {e}")


def chat(system: str, user: str, model: str = "gpt-5.5", timeout: int = 180):
    """Returns (ok, text). Runs one headless Codex task and reads its output."""
    if not available():
        return (False, "Codex CLI not found. Install Codex and run "
                       "'codex login' once, then Test again.")
    prompt = (f"{system}\n\n{user}".strip() if system else (user or "")).strip()
    fh = tempfile.NamedTemporaryFile(mode="r", suffix=".txt",
                                     delete=False, encoding="utf-8")
    fh.close()
    try:
        r = subprocess.run(
            ["codex", "exec", "--skip-git-repo-check", "-m", model,
             "-o", fh.name, prompt],
            capture_output=True, text=True, timeout=timeout)
        out = ""
        try:
            with open(fh.name, encoding="utf-8") as f:
                out = f.read().strip()
        except Exception:
            pass
        if out:
            return (True, out)
        err = (r.stderr or r.stdout or "").strip()
        return (False, f"Codex returned nothing. {err[:300]}")
    except subprocess.TimeoutExpired:
        return (False, "Codex timed out.")
    except Exception as e:
        return (False, f"Codex call failed: {e}")
    finally:
        try:
            os.unlink(fh.name)
        except Exception:
            pass
