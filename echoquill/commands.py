"""Command Mode: say what you want, EchoQuill does it.

Examples: "open chrome" · "search for best pizza near me" · "go to amazon.com"
· "press enter" · "select all" · "copy" · "paste" · "volume up" · "mute"
· "new tab" · "close tab" · "minimize window" · "take a screenshot"
· "lock the computer"

Deliberately conservative: only known-safe actions, no arbitrary shell
commands, and anything unrecognized is shown back to you instead of run.
"""

import re
import subprocess
import webbrowser

APP_ALIASES = {
    "chrome": "chrome", "google chrome": "chrome",
    "edge": "msedge", "microsoft edge": "msedge",
    "firefox": "firefox",
    "notepad": "notepad",
    "calculator": "calc", "calc": "calc",
    "paint": "mspaint",
    "word": "winword", "microsoft word": "winword",
    "excel": "excel", "microsoft excel": "excel",
    "powerpoint": "powerpnt",
    "outlook": "outlook",
    "file explorer": "explorer", "explorer": "explorer", "files": "explorer",
    "task manager": "taskmgr",
    "settings": "ms-settings:",
    "control panel": "control",
    "terminal": "wt", "command prompt": "cmd",
    "spotify": "spotify",
    "vlc": "vlc",
}

KEY_COMMANDS = {
    "press enter": "enter", "hit enter": "enter",
    "press tab": "tab", "press escape": "esc", "press space": "space",
    "select all": "ctrl+a", "copy": "ctrl+c", "paste": "ctrl+v",
    "cut": "ctrl+x", "undo": "ctrl+z", "redo": "ctrl+y",
    "save": "ctrl+s", "find": "ctrl+f", "print": "ctrl+p",
    "new tab": "ctrl+t", "close tab": "ctrl+w", "reopen tab": "ctrl+shift+t",
    "next tab": "ctrl+tab", "previous tab": "ctrl+shift+tab",
    "refresh": "f5", "full screen": "f11",
    "volume up": "volume up", "volume down": "volume down",
    "mute": "volume mute", "unmute": "volume mute",
    "play": "play/pause media", "pause": "play/pause media",
    "next song": "next track", "previous song": "previous track",
    "minimize window": "win+down", "maximize window": "win+up",
    "show desktop": "win+d", "take a screenshot": "win+shift+s",
    "switch window": "alt+tab",
}


SINGLE_WORD = {
    "minimize": "minimize window", "maximize": "maximize window",
    "screenshot": "take a screenshot", "fullscreen": "full screen",
    "desktop": "show desktop", "lock": "lock the computer",
    "enter": "press enter", "escape": "press escape",
}


def _clean(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[.!?,;:_]+", "", text).strip()
    text = text.replace("-", " ")
    text = re.sub(r"\s+", " ", text)
    # forgive politeness and filler
    text = re.sub(r"^(please|hey|ok|okay|can you|could you|would you)\s+", "", text)
    text = re.sub(r"^(please|hey)\s+", "", text)
    # normalize verb forms: "opened chrome" / "opening chrome" -> "open chrome"
    text = re.sub(r"^open(ed|ing)\b", "open", text)
    text = re.sub(r"\bopen up\b", "open", text)
    return text.strip()


def execute(text: str) -> str:
    """Run a voice command. Returns human-readable feedback."""
    cmd = _clean(text)
    if not cmd:
        return "(heard nothing)"

    # open / launch an app
    m = re.match(r"^(?:open|launch|start|run)\s+(.+)$", cmd)
    if m:
        name = m.group(1).strip()
        exe = APP_ALIASES.get(name)
        if exe:
            try:
                subprocess.Popen(f'start "" "{exe}"', shell=True)
                return f"Opening {name}"
            except Exception as e:
                return f"Couldn't open {name}: {e}"
        if re.match(r"^[\w.-]+\.(com|org|net|io|gov|edu|co|dev)(/\S*)?$", name):
            webbrowser.open("https://" + name)
            return f"Opening {name}"
        # fuzzy: "crome", "google grome" etc.
        import difflib
        close = difflib.get_close_matches(name, APP_ALIASES.keys(), n=1, cutoff=0.72)
        if close:
            try:
                subprocess.Popen(f'start "" "{APP_ALIASES[close[0]]}"', shell=True)
                return f"Opening {close[0]}"
            except Exception as e:
                return f"Couldn't open {close[0]}: {e}"
        # "open my web browser chrome" - any known app mentioned anywhere
        for alias, exe in APP_ALIASES.items():
            if re.search(r"\b" + re.escape(alias) + r"\b", name):
                subprocess.Popen(f'start "" "{exe}"', shell=True)
                return f"Opening {alias}"
        return f'I don\'t know the app "{name}" — try Chrome, Word, Notepad…'

    # web search
    m = re.match(r"^(?:search(?: the web)?(?: for)?|google)\s+(.+)$", cmd)
    if m:
        q = m.group(1).strip()
        webbrowser.open("https://www.google.com/search?q=" + q.replace(" ", "+"))
        return f'Searching for "{q}"'

    # go to a website
    m = re.match(r"^(?:go to|visit)\s+(.+)$", cmd)
    if m:
        site = m.group(1).strip().replace(" ", "")
        if "." not in site:
            site += ".com"
        webbrowser.open("https://" + site)
        return f"Opening {site}"

    # single-word shortcuts: "minimize", "screenshot", "lock"...
    cmd = SINGLE_WORD.get(cmd, cmd)

    # keyboard / media commands - exact, then contained, then fuzzy
    def _run_keys(phrase):
        try:
            import keyboard
            keyboard.send(KEY_COMMANDS[phrase])
            return phrase.capitalize()
        except Exception as e:
            return f"Couldn't do that: {e}"

    for phrase in KEY_COMMANDS:
        if cmd == phrase or cmd == phrase.replace("press ", ""):
            return _run_keys(phrase)
    # "please select all now" - every word of a command appears in what you said
    cmd_words = set(cmd.split())
    for phrase in KEY_COMMANDS:
        if set(phrase.split()) <= cmd_words:
            return _run_keys(phrase)

    # bare app name: just saying "chrome" opens it
    if cmd in APP_ALIASES:
        try:
            subprocess.Popen(f'start "" "{APP_ALIASES[cmd]}"', shell=True)
            return f"Opening {cmd}"
        except Exception as e:
            return f"Couldn't open {cmd}: {e}"

    # fuzzy match against key commands ("push enter" ~ "press enter")
    import difflib
    close = difflib.get_close_matches(cmd, KEY_COMMANDS.keys(), n=1, cutoff=0.6)
    if close:
        return _run_keys(close[0])

    if cmd in ("lock the computer", "lock computer", "lock my pc", "lock screen"):
        try:
            import ctypes
            ctypes.windll.user32.LockWorkStation()
            return "Locking"
        except Exception as e:
            return f"Couldn't lock: {e}"

    return f'Didn\'t recognize: "{text}" — full list: Settings → Help → Voice commands'
