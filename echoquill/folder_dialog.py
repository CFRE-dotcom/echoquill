"""Small custom dialogs for naming / choosing / deleting a folder.

A modest popup with a ~30-character-wide input (not the tiny system default,
not a huge window). Used everywhere folders appear: the Clips tray, the
Recent-transcriptions window, and the edit dialog - so the folder process is
identical no matter where you are.
"""

import tkinter as tk
from tkinter import ttk, messagebox

from . import theme


def new_folder(parent):
    """Prompt for a brand-new folder name. Returns the name, or None."""
    return _FolderDialog(parent, mode="new").result


def move_to_folder(parent, current="", names=None):
    """Pick / create / remove-from / delete a folder.

    Returns:
      - a folder name  -> file the item there (creating it if new)
      - ""             -> remove the item from any folder
      - None           -> cancelled (also returned after only deleting folders)
    Deleting a whole folder is handled inside the dialog immediately.
    """
    return _FolderDialog(parent, mode="move", current=current,
                         names=names or []).result


class _FolderDialog:
    def __init__(self, parent, mode="new", current="", names=None):
        self.result = None          # None == cancelled
        names = list(names or [])
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
                  else "Pick a folder, type a new name, or delete one:")
        ttk.Label(pad, text=prompt, style="Dim.TLabel").pack(anchor="w")

        self.var = tk.StringVar(value=current or "")
        ent = ttk.Entry(pad, textvariable=self.var, width=30)   # ~30 chars wide
        ent.pack(anchor="w", pady=(6, 8))
        ent.focus_set()
        ent.bind("<Return>", lambda e: self._ok())
        ent.bind("<Escape>", lambda e: self._cancel())

        self._lb = None
        if mode == "move" and names:
            lbrow = ttk.Frame(pad)
            lbrow.pack(anchor="w", pady=(0, 8), fill="x")
            lb = tk.Listbox(lbrow, height=min(6, len(names)), width=26,
                            bg=theme.FIELD, fg=theme.FG, borderwidth=1,
                            relief="solid", activestyle="none",
                            highlightthickness=0,
                            selectbackground=theme.ACCENT, exportselection=False)
            for n in names:
                lb.insert("end", n)
            lb.pack(side="left")
            lb.bind("<<ListboxSelect>>", lambda e: self._pick_list(lb))
            lb.bind("<Double-Button-1>", lambda e: self._ok())
            self._lb = lb
            _del = ttk.Button(lbrow, text="Delete folder",
                              command=self._delete_folder)
            _del.pack(side="left", padx=(8, 0), anchor="n")

        btns = ttk.Frame(pad)
        btns.pack(anchor="e", pady=(2, 0))
        if mode == "move":
            ttk.Button(btns, text="Remove from folder",
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

    def _delete_folder(self):
        lb = self._lb
        if lb is None:
            return
        sel = lb.curselection()
        name = lb.get(sel[0]) if sel else self.var.get().strip()
        if not name:
            return
        if not messagebox.askyesno(
                "Delete folder",
                f"Delete the folder “{name}”?\n\n"
                "Items in it aren't deleted - they just stop being filed here.",
                parent=self.win):
            return
        from . import folders
        folders.delete_folder(name)
        # refresh listbox
        remaining = folders.all_folders()
        lb.delete(0, "end")
        for n in remaining:
            lb.insert("end", n)
        if self.var.get().strip() == name:
            self.var.set("")
        if not remaining:
            self._lb = None

    def _ok(self):
        self.result = self.var.get().strip()
        self.win.destroy()

    def _none(self):
        self.result = ""            # remove from any folder
        self.win.destroy()

    def _cancel(self):
        self.result = None
        self.win.destroy()
