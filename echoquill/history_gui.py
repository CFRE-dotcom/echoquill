"""Pop-up browser of recent transcriptions (free: last 10, deletable)."""

import tkinter as tk
from tkinter import ttk, messagebox

from . import history, theme


class ClipboardWindow:
    def __init__(self, root: tk.Tk):
        self.win = tk.Toplevel(root)
        self.win.title("EchoQuill — Recent transcriptions")
        self.win.geometry("740x460")
        self.win.minsize(700, 380)
        self.win.attributes("-topmost", True)
        self.win.protocol("WM_DELETE_WINDOW", self.win.destroy)
        theme.apply(self.win)

        ttk.Label(self.win, text="Recent transcriptions",
                  style="Title.TLabel").pack(anchor="w", padx=16, pady=(14, 2))
        ttk.Label(self.win, style="Dim.TLabel",
                  text="Click to select · Shift/Ctrl-click for many · double-click to copy. "
                       "Free shows your last 10 — Pro keeps unlimited + Favorites."
                  ).pack(anchor="w", padx=16, pady=(0, 8))

        bar = ttk.Frame(self.win)
        bar.pack(side="bottom", fill="x", padx=16, pady=10)
        self.status = ttk.Label(bar, text="", style="Dim.TLabel")
        self.status.pack(side="left")
        # per-item actions on the LEFT (always visible), bulk actions on the RIGHT
        ttk.Button(bar, text="Edit…", command=self._edit).pack(side="left", padx=(12, 4))
        ttk.Button(bar, text="Copy", style="Accent.TButton", command=self._copy).pack(side="left", padx=4)
        ttk.Button(bar, text="Delete all", command=self._delete_all).pack(side="right", padx=(4, 0))
        ttk.Button(bar, text="Delete selected", command=self._delete_selected).pack(side="right", padx=4)
        ttk.Button(bar, text="Select all", command=self._select_all).pack(side="right", padx=4)

        self.listbox = theme.dark_listbox(self.win, activestyle="none",
                                          selectmode="extended")
        self.listbox.pack(fill="both", expand=True, padx=16)
        self.listbox.bind("<Double-Button-1>", lambda e: self._copy())
        self.entries = []
        self._fill()

    def _fill(self):
        self.listbox.delete(0, "end")
        try:
            self.entries = history.entries(limit=10)
        except Exception:
            self.entries = []
        if not self.entries:
            self.listbox.insert("end", "  No transcriptions yet.")
        for e in self.entries:
            text = e.get("text", "").replace("\n", " ")
            when = str(e.get("date", ""))[:16]
            shown = text if len(text) <= 76 else text[:73] + "…"
            self.listbox.insert("end", f" {when}   {shown}")
        self.status.configure(text=f"{len(self.entries)} shown" if self.entries else "")

    def _select_all(self):
        if self.entries:
            self.listbox.select_set(0, "end")

    def _selected_entries(self):
        return [self.entries[i] for i in self.listbox.curselection()
                if i < len(self.entries)]

    def _delete_selected(self):
        chosen = self._selected_entries()
        if not chosen:
            self.status.configure(text="Nothing selected")
            return
        history.delete_many(e.get("ts") for e in chosen)
        self._fill()
        self.status.configure(text=f"Deleted {len(chosen)}")

    def _delete_all(self):
        if not self.entries:
            return
        if messagebox.askyesno("Delete all",
                               "Delete all transcription history? This can't be undone.",
                               parent=self.win):
            history.clear()
            self._fill()
            self.status.configure(text="All deleted")

    def _edit(self):
        sel = self.listbox.curselection()
        if not sel or not self.entries or sel[0] >= len(self.entries):
            self.status.configure(text="Select one entry to edit")
            return
        entry = self.entries[sel[0]]
        ts = entry.get("ts")
        dlg = tk.Toplevel(self.win)
        dlg.title("Edit transcription")
        dlg.geometry("560x300")
        dlg.attributes("-topmost", True)
        dlg.protocol("WM_DELETE_WINDOW", dlg.destroy)
        theme.apply(dlg)
        ttk.Label(dlg, text="Edit the text, then Save:",
                  style="Dim.TLabel").pack(anchor="w", padx=14, pady=(12, 4))
        box = theme.dark_text(dlg, wrap="word")
        box.pack(fill="both", expand=True, padx=14)
        box.insert("1.0", entry.get("text", ""))
        row = ttk.Frame(dlg); row.pack(fill="x", padx=14, pady=10)

        def save():
            new_text = box.get("1.0", "end").strip()
            history.update(ts, new_text)
            self._reload() if hasattr(self, "_reload") else None
            self._fill()
            dlg.destroy()
            self.status.configure(text="Saved ✓")

        ttk.Button(row, text="Save", style="Accent.TButton",
                   command=save).pack(side="right")
        ttk.Button(row, text="Cancel", command=dlg.destroy).pack(side="right", padx=6)

    def _copy(self):
        chosen = self._selected_entries()
        if not chosen:
            return
        try:
            import pyperclip
            pyperclip.copy("\n\n".join(e.get("text", "") for e in chosen))
            self.status.configure(text=f"Copied {len(chosen)} ✓")
            self.win.after(1500, lambda: self.status.configure(text=""))
        except Exception:
            self.status.configure(text="Copy failed")
