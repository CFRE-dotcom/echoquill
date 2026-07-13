"""Small '?' help icon that opens a themed how-to popover for a window."""

import tkinter as tk
from tkinter import ttk

from . import theme


def _show(parent, title, text):
    win = tk.Toplevel(parent)
    win.title(title)
    win.geometry("460x420")
    win.attributes("-topmost", True)
    win.protocol("WM_DELETE_WINDOW", win.destroy)
    theme.apply(win)
    ttk.Label(win, text=title, style="Title.TLabel").pack(anchor="w", padx=16, pady=(14, 6))
    box = theme.dark_text(win, wrap="word")
    box.pack(fill="both", expand=True, padx=16, pady=(0, 8))
    box.insert("1.0", text)
    box.configure(state="disabled")
    ttk.Button(win, text="Got it", style="Accent.TButton",
               command=win.destroy).pack(pady=(0, 12))


def attach(parent_win, container, title, text):
    """Add a clickable '?' to `container` that opens the help popover."""
    lbl = tk.Label(container, text=" ? ", bg=theme.ACCENT, fg="#ffffff",
                   font=("Segoe UI Semibold", 10), cursor="hand2")
    lbl.bind("<Button-1>", lambda e: _show(parent_win, title, text))
    lbl.bind("<Enter>", lambda e: lbl.configure(bg="#3396ff"))
    lbl.bind("<Leave>", lambda e: lbl.configure(bg=theme.ACCENT))
    return lbl
