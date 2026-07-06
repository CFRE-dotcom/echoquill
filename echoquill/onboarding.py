"""First-run welcome - so nobody has to guess the hotkey."""

import tkinter as tk
from tkinter import ttk

from . import config as cfgmod
from . import theme


def maybe_show(root, cfg):
    if cfg.get("onboarded"):
        return
    win = tk.Toplevel(root)
    win.title("Welcome to EchoQuill")
    win.geometry("560x460")
    win.attributes("-topmost", True)
    theme.apply(win)

    ttk.Label(win, text="Welcome to EchoQuill 👋",
              style="Title.TLabel").pack(anchor="w", padx=24, pady=(20, 4))
    ttk.Label(win, style="Dim.TLabel", wraplength=500, justify="left", text=(
        "Free, private voice typing. Everything runs on this computer — "
        "your voice never goes online.")).pack(anchor="w", padx=24)

    body = ttk.Frame(win)
    body.pack(fill="both", expand=True, padx=24, pady=14)
    steps = [
        ("1.  Click into any text box", "Email, Word, browser — anywhere you can type."),
        (f"2.  Press {cfg.get('hotkey', 'ctrl+alt+space').upper()}", "Or click the blue mic pill at the bottom of the screen."),
        ("3.  Talk, then press it again", "Your words appear live, then land at your cursor."),
        ("🎧  Bonus: say \"computer, open chrome\"", "Starting dictation with the word 'computer' runs commands."),
        ("🎬  Bonus: transcribe videos", "Right-click the mic pill → Transcribe video / URL."),
    ]
    for title, sub in steps:
        ttk.Label(body, text=title, font=("Segoe UI Semibold", 11)).pack(anchor="w", pady=(8, 0))
        ttk.Label(body, text=sub, style="Dim.TLabel").pack(anchor="w")

    def done():
        cfg["onboarded"] = True
        cfgmod.save(cfg)
        win.destroy()

    ttk.Button(win, text="Let's go", style="Accent.TButton",
               command=done).pack(pady=(0, 18))
    win.protocol("WM_DELETE_WINDOW", done)
