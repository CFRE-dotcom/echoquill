"""Small custom dialogs for naming / choosing a folder.

A modest popup with a ~30-character-wide input (not the tiny system default,
not a huge window). Used by the Clips tray and Recent-transcriptions window.
"""

import tkinter as tk
from tkinter import ttk

from . import theme


def new_folder(parent):
    """Prompt for a brand-new folder name. Returns the name, or None."""
    return _FolderDialog(parent, mode="new").result


def move_to_folder(parent, current="", names=None):
    """Pick an existing folder or type a new one.
    Returns the folder name, '' to remove from any folder, or None if cancelled.
    """
    return _FolderDialog(parent, mode="move", current=current,
                         names=names or []).result


class _FolderDialog:
    def __init__(self, parent, mode="new", current="", names=None):
        self.result = None          # None == cancelled
        names = names or []
        win = tk.Toplevel(parent)
        self.win = win
        win.title("New folder" if mode == "new" else "Move to folder")
        win.attributes("-topmost", True)
        win.resizable(False, False)
        try:
            win.transient(parent)
        except Exception:
            pass
        theme.apply(win)

        pad = ttk.Frame(win)
        pad.pack(fill="both", expand=True, padx=16, pady=14)

        prompt = ("Name your new folder:" if mode == "new"
                  else "Pick a folder below, or type a new name:")
        ttk.Label(pad, text=prompt, style="Dim.TLabel").pack(anchor="w")

        self.var = tk.StringVar(value=current or "")
        ent = ttk.Entry(pad, textvariable=self.var, width=30)   # ~30 chars wide
        ent.pack(anchor="w", pady=(6, 8))
        ent.focus_set()
        ent.bind("<Return>", lambda e: self._ok())
        ent.bind("<Escape>", lambda e: self._cancel())

        if mode == "move" and names:
            lb = tk.Listbox(pad, height=min(6, len(names)), width=30,
                            bg=theme.FIELD, fg=theme.FG, borderwidth=1,
                            relief="solid", activestyle="none",
                            highlightthickness=0,
                            selectbackground=theme.ACCENT, exportselection=False)
            for n in names:
                lb.insert("end", n)
            lb.pack(anchor="w", pady=(0, 8))
            lb.bind("<<ListboxSelect>>", lambda e: self._pick_list(lb))
            lb.bind("<Double-Button-1>", lambda e: self._ok())

        btns = ttk.Frame(pad)
        btns.pack(anchor="e", pady=(2, 0))
        if mode == "move":
            ttk.Button(btns, text="None",
                       command=self._none).pack(side="left", padx=(0, 8))
        ttk.Button(btns, text="Cancel",
                   command=self._cancel).pack(side="left", padx=(0, 8))
        ttk.Button(btns, text="OK", style="Accent.TButton",
                   command=self._ok).pack(side="left")

        try:
            win.grab_set()
        except Exception:
            pass
        parent.wait_window(win)

    def _pick_list(self, lb):
        sel = lb.curselection()
        if sel:
            self.var.set(lb.get(sel[0]))

    def _ok(self):
        self.result = self.var.get().strip()
        self.win.destroy()

    def _none(self):
        self.result = ""            # remove from any folder
        self.win.destroy()

    def _cancel(self):
        self.result = None
        self.win.destroy()
