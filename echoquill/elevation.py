"""Admin mode helpers: detect when the focused app is elevated (so we can
warn the user), and register/remove a scheduled task that launches EchoQuill
elevated without a UAC prompt every time."""

import ctypes
import os
import subprocess
import sys

TASK_NAME = "EchoQuillAdminMode"


def is_self_elevated() -> bool:
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def foreground_is_elevated() -> bool:
    """True if the focused window belongs to a higher-privilege process.
    Detected by being denied access to query it (classic elevation tell)."""
    try:
        import ctypes.wintypes as wt
        u32, k32 = ctypes.windll.user32, ctypes.windll.kernel32
        hwnd = u32.GetForegroundWindow()
        pid = wt.DWORD()
        u32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
        h = k32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid.value)
        if not h:
            return True   # access denied => target is elevated
        k32.CloseHandle(h)
        return False
    except Exception:
        return False


def _exe_path() -> str:
    if getattr(sys, "frozen", False):
        return sys.executable
    run_py = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "run.py"))
    return sys.executable.replace("python.exe", "pythonw.exe") + f' "{run_py}"'


def enable() -> bool:
    """Create a Task Scheduler entry that runs EchoQuill elevated, no UAC nag.
    Creating the task itself needs one admin approval."""
    try:
        cmd = ['schtasks', '/Create', '/TN', TASK_NAME, '/SC', 'ONLOGON',
               '/RL', 'HIGHEST', '/F', '/TR', _exe_path()]
        subprocess.run(cmd, check=True, capture_output=True,
                       creationflags=0x08000000)
        return True
    except Exception:
        return False


def disable() -> bool:
    try:
        subprocess.run(['schtasks', '/Delete', '/TN', TASK_NAME, '/F'],
                       check=False, capture_output=True, creationflags=0x08000000)
        return True
    except Exception:
        return False
