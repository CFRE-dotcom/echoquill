"""Start EchoQuill automatically when Windows starts (per-user registry key).
No admin rights needed. Works for both the .exe and running from source.
"""

import os
import sys

RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
VALUE = "EchoQuill"


def _launch_command() -> str:
    if getattr(sys, "frozen", False):          # packaged .exe
        return f'"{sys.executable}"'
    run_py = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "run.py"))
    pythonw = sys.executable.replace("python.exe", "pythonw.exe")
    return f'"{pythonw}" "{run_py}"'


def set_autostart(enabled: bool) -> bool:
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY, 0,
                            winreg.KEY_SET_VALUE) as k:
            if enabled:
                winreg.SetValueEx(k, VALUE, 0, winreg.REG_SZ, _launch_command())
            else:
                try:
                    winreg.DeleteValue(k, VALUE)
                except FileNotFoundError:
                    pass
        return True
    except Exception:
        return False


def is_enabled() -> bool:
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY) as k:
            winreg.QueryValueEx(k, VALUE)
        return True
    except Exception:
        return False
