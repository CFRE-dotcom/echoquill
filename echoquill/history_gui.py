"""Pop-up browser of recent transcriptions.

Every dictation is kept here (locally). Double-click any line - or select it
and hit Copy - to put it back on the clipboard, for when text didn't land
where you wanted it.
"""

import tkinter as tk
from tkinter import ttk

from . import history, theme


class ClipboardWindow:
    def __init__(self, root: tk.Tk):
        self.win = tk.Toplevel(root)
        self.win.title("EchoQuill — Recent transcriptions")
        self.win.geometry("560x420")
        self.win.minsize(460, 340)
        self.win.attributes("-topmost", True)
        theme.apply(self.win)

        ttk.Label(self.win, text="Recent transcriptions",
                  style="Title.TLabel").pack(anchor="w", padx=16, pady=(14, 2))
        ttk.Label(self.win, style="Dim.TLabel",
                  text="Double-click a line to copy it to the clipboard."
                  ).pack(anchor="w", padx=16, pady=(0, 8))

        bar = ttk.Frame(self.win)
        bar.pack(side="bottom", fill="x", padx=16, pady=10)
        self.status = ttk.Label(bar, text="", style="Dim.TLabel")
        self.status.pack(side="left")
        ttk.Button(bar, text="Copy selected", style="Accent.TButton",
                   command=self._copy).pack(side="right")

        self.entries = history.entries(limit=50)
        self.listbox = theme.dark_listbox(self.win, activestyle="none")
        self.listbox.pack(fill="both", expand=True, padx=16)
        for e in self.entries:
            text = e.get("text", "").replace("\n", " ")
            when = str(e.get("date", ""))[11:16]
            shown = text if len(text) <= 80 else text[:77] + "…"
            self.listbox.insert("end", f" {when}   {shown}")
        self.listbox.bind("<Double-Button-1>", lambda e: self._copy())

    def _copy(self):
        sel = self.listbox.curselection()
        if not sel:
            return
        entry = self.entries[sel[0]]
        try:
            import pyperclip
            pyperclip.copy(entry.get("text", ""))
            self.status.configure(text="Copied ✓")
            self.win.after(1500, lambda: self.status.configure(text=""))
        except Exception:
            self.status.configure(text="Copy failed")
