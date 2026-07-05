"""Insert transcribed text into whatever app is focused.

Three modes (community-requested):
- "paste":     put text on the clipboard, press Ctrl+V, restore old clipboard. Fast.
- "type":      simulate keystrokes. Works in apps that block pasting.
- "clipboard": copy only - user pastes when and where they want.
"""

import time


def press_ctrl_v():
    """Reliable paste: press keys individually with timing, so apps never
    receive a bare 'v' when Ctrl fails to register in a combined stroke."""
    import keyboard
    time.sleep(0.12)
    keyboard.press("ctrl")
    time.sleep(0.04)
    keyboard.press("v")
    time.sleep(0.04)
    keyboard.release("v")
    time.sleep(0.02)
    keyboard.release("ctrl")


def _get_clipboard() -> str:
    try:
        import pyperclip
        return pyperclip.paste()
    except Exception:
        return ""


def _set_clipboard(text: str):
    import pyperclip
    pyperclip.copy(text)


def insert(text: str, mode: str = "paste"):
    if not text:
        return
    if mode == "clipboard":
        _set_clipboard(text)
        return
    if mode == "type":
        import keyboard
        keyboard.write(text, delay=0.005)
        return
    # default: paste
    old = _get_clipboard()
    _set_clipboard(text)
    press_ctrl_v()
    time.sleep(0.15)
    # restore the user's previous clipboard so we don't clobber it
    try:
        _set_clipboard(old)
    except Exception:
        pass
