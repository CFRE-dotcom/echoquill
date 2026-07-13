"""Recent transcriptions browser (free: last 10, editable, deletable).

Per-line actions work the same way as the Clips tray:
  - double-click a line   -> edit
  - right-click a line    -> menu (Edit / Copy / Favorite / Delete)
  - toolbar buttons mirror the menu for discoverability
"""

import tkinter as tk
from tkinter import ttk, messagebox

from . import favorites, history, theme


class ClipboardWindow:
    def __init__(self, root: tk.Tk):
        self.win = tk.Toplevel(root)
        self.win.title("EchoQuill - Recent transcriptions")
        self.win.geometry("740x480")
        self.win.minsize(600, 380)
        self.win.attributes("-topmost", True)
        self.win.protocol("WM_DELETE_WINDOW", self.win.destroy)
        theme.apply(self.win)

        self._reload()

        ttk.Label(self.win, text="Recent transcriptions",
                  style="Title.TLabel").pack(anchor="w", padx=16, pady=(12, 2))
        ttk.Label(self.win, style="Dim.TLabel",
                  text="Double-click a line to edit · right-click for menu · "
                       "Ctrl/Shift-click selects many · Free keeps the last 10"
                  ).pack(anchor="w", padx=16, pady=(0, 6))

        # top toolbar: label (left) . item actions (right)
        top = ttk.Frame(self.win)
        top.pack(fill="x", padx=16, pady=(0, 6))
        self.page_lbl = ttk.Label(top, text="", style="Dim.TLabel")
        self.page_lbl.pack(side="left")
        ttk.Button(top, text="✎ Edit", width=8,
                   command=self._edit).pack(side="right")
        ttk.Button(top, text="★ Favorite", width=11,
                   command=self._favorite).pack(side="right", padx=4)
        ttk.Button(top, text="⧉ Copy", width=8,
                   command=self._copy).pack(side="right")

        # list
        self.listbox = theme.dark_listbox(self.win, activestyle="none",
                                          selectmode="extended")
        self.listbox.pack(fill="both", expand=True, padx=16)
        self.listbox.bind("<Double-Button-1>", lambda e: self._edit())
        self.listbox.bind("<Button-3>", self._menu)

        self.menu = tk.Menu(self.win, tearoff=0)
        self.menu.add_command(label="✎  Edit", command=self._edit)
        self.menu.add_command(label="⧉  Copy", command=self._copy)
        self.menu.add_command(label="★  Favorite / Unfavorite", command=self._favorite)
        self.menu.add_separator()
        self.menu.add_command(label="\U0001f5d1  Delete", command=self._delete_selected)

        bar = ttk.Frame(self.win)
        bar.pack(side="bottom", fill="x", padx=16, pady=10)
        self.status = ttk.Label(bar, text="", style="Dim.TLabel")
        self.status.pack(side="left")
        ttk.Button(bar, text="Delete all", width=10,
                   command=self._delete_all).pack(side="right", padx=(4, 0))
        ttk.Button(bar, text="Delete selected", width=14,
                   command=self._delete_selected).pack(side="right", padx=4)
        ttk.Button(bar, text="Select all", width=10,
                   command=self._select_all).pack(side="right", padx=4)

        self.entries = []
        self._fill()

    def _reload(self):
        try:
            self._all = history.entries(limit=10)
        except Exception:
            self._all = []

    def _fill(self):
        self.listbox.delete(0, "end")
        self.entries = self._all
        if not self.entries:
            self.listbox.insert("end", "  No transcriptions yet.")
        for e in self.entries:
            text = e.get("text", "").replace("\n", " ")
            when = str(e.get("date", ""))[:16]
            star = "★ " if favorites.is_favorite(e.get("text", "")) else ""
            shown = text if len(text) <= 82 else text[:79] + "…"
            self.listbox.insert("end", f" {when}   {star}{shown}")
        self.page_lbl.configure(
            text=(f"{len(self._all)} shown (last 10)"
                  if self._all else "No transcriptions"))
        self.status.configure(text="")

    def _menu(self, event):
        idx = self.listbox.nearest(event.y)
        if idx not in self.listbox.curselection():
            self.listbox.selection_clear(0, "end")
            self.listbox.selection_set(idx)
            self.listbox.activate(idx)
        try:
            self.menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.menu.grab_release()

    def _select_all(self):
        if self.entries:
            self.listbox.select_set(0, "end")

    def _selected(self):
        return [self.entries[i] for i in self.listbox.curselection()
                if i < len(self.entries)]

    def _favorite(self):
        chosen = self._selected()
        if not chosen:
            self.status.configure(text="Select a line first"); return
        added = removed = 0
        for e in chosen:
            t = e.get("text", "")
            if not t:
                continue
            if favorites.toggle(t):      # click again to un-favorite
                added += 1
            else:
                removed += 1
        self._fill()
        if added and removed:
            self.status.configure(text=f"★ {added} added, {removed} removed")
        elif added:
            self.status.configure(text=f"Added {added} to Favorites ★")
        else:
            self.status.configure(text=f"Removed {removed} from Favorites")

    def _edit(self):
        chosen = self._selected()
        if len(chosen) != 1:
            self.status.configure(text="Select exactly one line to edit")
            return
        entry = chosen[0]
        ts = entry.get("ts")
        from . import edit_dialog

        def _save(new_text):
            history.update(ts, new_text)
            self._reload(); self._fill()
            self.status.configure(text="Saved \u2713")
        edit_dialog.open_editor(self.win, entry.get("text", ""), _save,
                                cfg=None, title="Edit transcription",
                                anchor=self.win)

    def _delete_selected(self):
        chosen = self._selected()
        if not chosen:
            self.status.configure(text="Nothing selected"); return
        history.delete_many(e.get("ts") for e in chosen)
        self._reload(); self._fill()
        self.status.configure(text=f"Deleted {len(chosen)}")

    def _delete_all(self):
        if self._all and messagebox.askyesno(
                "Delete all", "Delete ALL transcriptions?",
                parent=self.win):
            history.clear(); self._reload(); self._fill()

    def _copy(self):
        chosen = self._selected()
        if not chosen:
            self.status.configure(text="Select a line first"); return
        try:
            import pyperclip
            pyperclip.copy("\n\n".join(e.get("text", "") for e in chosen))
            self.status.configure(text=f"Copied {len(chosen)} ✓")
            self.win.after(1500, lambda: self.status.configure(text=""))
        except Exception:
            self.status.configure(text="Copy failed")
