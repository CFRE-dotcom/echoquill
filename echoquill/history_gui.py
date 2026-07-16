"""Recent transcriptions - works like the Clips tray: per-row ★ favorite,
✎ edit, ✕ delete, a Recent / Favorites tab, and a real search box.

Free keeps the last 10; Pro pages through everything.
"""

import ctypes
import threading
import time
import tkinter as tk
from tkinter import ttk, messagebox

from . import favorites, helptip, history, injector, theme, widgets
from .clips_gui import _cursor_pos, _click_at_cursor, DRAG_THRESHOLD


class ClipboardWindow:
    def __init__(self, root: tk.Tk):
        self.win = tk.Toplevel(root)
        self.win.title("EchoQuill — Recent transcriptions")
        self.win.geometry("720x560")
        self.win.minsize(560, 420)
        self.win.attributes("-topmost", True)
        self.win.protocol("WM_DELETE_WINDOW", self.win.destroy)
        theme.apply(self.win)

        try:
            from . import config as _cfg
            from . import license
            self._pro = license.is_pro(_cfg.load())
        except Exception:
            self._pro = False
        self._page_size = 50 if self._pro else 10
        self._page = 0
        self._tab = "recent"

        _title_row = tk.Frame(self.win, bg=theme.BG)
        _title_row.pack(fill="x", padx=16, pady=(12, 6))
        ttk.Label(_title_row, text="Recent transcriptions",
                  style="Title.TLabel").pack(side="left")
        helptip.attach(self.win, _title_row, "Recent transcriptions — help",
                       "Click a line to paste it into the app you were just in.\n"
                       "Drag a line onto any text box to drop the text there.\n"
                       "★  Favorite (click again to remove)\n"
                       "✎  Edit the text (with Ask AI)\n"
                       "✕  Delete\n\n"
                       "Use the Recent / Favorites tabs and the Search box to "
                       "find things. Hover any icon for a tip."
                       ).pack(side="left", padx=8)

        # ---- Recent / Favorites tabs ----
        tabs = tk.Frame(self.win, bg=theme.BG)
        tabs.pack(fill="x", padx=16)
        self._tab_recent = tk.Label(tabs, text=" Recent ", bg=theme.FIELD,
                                    fg=theme.FG, cursor="hand2", padx=10, pady=5,
                                    font=("Segoe UI Semibold", 9))
        self._tab_favs = tk.Label(tabs, text=" ★ Favorites ", bg=theme.BG,
                                  fg=theme.DIM, cursor="hand2", padx=10, pady=5,
                                  font=("Segoe UI Semibold", 9))
        self._tab_recent.pack(side="left")
        self._tab_favs.pack(side="left", padx=4)
        self._tab_recent.bind("<Button-1>", lambda e: self._switch("recent"))
        helptip.tip(self._tab_recent, "Show your recent transcriptions.")
        self._tab_favs.bind("<Button-1>", lambda e: self._switch("favs"))
        helptip.tip(self._tab_favs, "Show only the transcriptions you've starred.")

        # ---- search ----
        srow = tk.Frame(self.win, bg=theme.BG)
        srow.pack(fill="x", padx=16, pady=(8, 2))
        wrap, self._search_value = widgets.make_search(
            srow, "Search your transcriptions…", self.refresh)
        wrap.pack(fill="x")

        # ---- folder bar (both tabs) ----
        self._hist_folder = "All"
        self._folder_row = tk.Frame(self.win, bg=theme.BG)
        self._folder_row.pack(fill="x", padx=16, pady=(6, 0))

        # ---- paging row (Pro, Recent tab only) ----
        self._page_row = tk.Frame(self.win, bg=theme.BG)
        self._page_row.pack(fill="x", padx=16, pady=(6, 0))
        if self._pro:
            _b_newer = ttk.Button(self._page_row, text="← Newer", width=8,
                       command=lambda: self._flip(-1)); _b_newer.pack(side="left")
            helptip.tip(_b_newer, "Show the previous (newer) page.")
            _b_older = ttk.Button(self._page_row, text="Older →", width=8,
                       command=lambda: self._flip(1)); _b_older.pack(side="left", padx=(4, 10))
            helptip.tip(_b_older, "Show the next (older) page.")
        self.page_lbl = ttk.Label(self._page_row, text="", style="Dim.TLabel")
        self.page_lbl.pack(side="left")

        # ---- bottom bar (packed before the body so it stays visible) ----
        bar = tk.Frame(self.win, bg=theme.BG)
        bar.pack(side="bottom", fill="x", padx=16, pady=10)
        self.status = tk.Label(bar, text="", bg=theme.BG, fg=theme.DIM,
                               font=("Segoe UI", 9))
        self.status.pack(side="left")
        self._delall_btn = ttk.Button(bar, text="Delete all",
                                      command=self._delete_all)
        self._delall_btn.pack(side="right")
        helptip.tip(self._delall_btn, "Delete everything shown on this tab.")

        # ---- scrollable list of rows ----
        self._scroll = theme.Scrollable(self.win)
        self._scroll.pack(fill="both", expand=True, padx=16, pady=(4, 4))
        self.body = self._scroll.inner

        # clipboard-style drag/drop: remember the app you were last in
        self._last_target = None
        self._watching = True
        threading.Thread(target=self._watch_foreground, daemon=True).start()
        self.win.bind("<Destroy>", lambda e: setattr(self, "_watching", False))

        self.refresh()

    # ---------- data ----------

    def _recent_all(self):
        try:
            return history.entries(limit=100000 if self._pro else 10)
        except Exception:
            return []

    def refresh(self):
        for w in self.body.winfo_children():
            w.destroy()
        term = self._search_value().lower()
        from . import folders
        for w in self._folder_row.winfo_children():
            w.destroy()
        opts = ["All"] + folders.all_folders()
        if self._hist_folder not in opts:
            self._hist_folder = "All"
        tk.Label(self._folder_row, text="Folder:", bg=theme.BG, fg=theme.DIM,
                 font=("Segoe UI", 9)).pack(side="left")
        fv = tk.StringVar(value=self._hist_folder)
        ttk.OptionMenu(self._folder_row, fv, self._hist_folder, *opts,
                       command=self._set_hist_folder).pack(side="left", padx=6)
        _nf = tk.Label(self._folder_row, text="＋ New folder", bg=theme.BG,
                       fg=theme.ACCENT, font=("Segoe UI Semibold", 9),
                       cursor="hand2")
        _nf.pack(side="left", padx=6)
        _nf.bind("<Button-1>", lambda e: self._new_folder())
        _nf.bind("<Enter>", lambda e, w=_nf: w.configure(fg=theme.FG))
        _nf.bind("<Leave>", lambda e, w=_nf: w.configure(fg=theme.ACCENT))
        helptip.tip(_nf, "Create a new folder, then move transcriptions into it.")

        folder = self._hist_folder if self._hist_folder != "All" else None
        if self._tab == "favs":
            self._page_row.pack_forget()
            self._delall_btn.configure(text="Clear favorites")
            data = favorites.all_favorites()
            if term:
                data = [e for e in data if term in e.get("text", "").lower()]
            if folder:
                data = [e for e in data
                        if folders.folder_of(e.get("text", "")) == folder]
            page = data
        elif folder:
            # Folder filter: bypass paging, scan the full recent set client-side.
            self._page_row.pack_forget()
            self._delall_btn.configure(text="Delete all")
            data = self._recent_all()
            if term:
                data = [e for e in data if term in e.get("text", "").lower()]
            page = [e for e in data
                    if folders.folder_of(e.get("text", "")) == folder]
        else:
            if self._pro:
                self._page_row.pack(fill="x", padx=16, pady=(6, 0),
                                    before=self._scroll)
            self._delall_btn.configure(text="Delete all")
            # lazy: only the current page is JSON-parsed (snappy with 1000s)
            page, n = history.page(self._page, self._page_size, term or None)
            pages = max(1, (n + self._page_size - 1) // self._page_size)
            if self._page > pages - 1:
                self._page = pages - 1
                page, n = history.page(self._page, self._page_size, term or None)
            self.page_lbl.configure(
                text=(f"Page {self._page + 1} of {pages} · {n:,} total"
                      if n else "Nothing here yet"))

        if not page:
            msg = ("No favorites yet — tap a ☆ to star one."
                   if self._tab == "favs"
                   else ("No matches." if term else "No transcriptions yet."))
            tk.Label(self.body, text=msg, bg=theme.BG, fg=theme.DIM).pack(pady=24)
            return

        for e in page:
            self._build_row(e)

    def _build_row(self, e):
        text = e.get("text", "")
        ts = e.get("ts")
        when = str(e.get("date", ""))[:16]
        shown = text.replace("\n", " ")
        shown = shown if len(shown) <= 90 else shown[:87] + "…"
        row = tk.Frame(self.body, bg=theme.FIELD)
        row.pack(fill="x", pady=3)

        head = f" {when}   {shown}" if when else " " + shown
        lbl = tk.Label(row, text=head, anchor="w", bg=theme.FIELD, fg=theme.FG,
                       font=("Segoe UI", 9), justify="left", pady=7, padx=6,
                       cursor="hand2")
        lbl.pack(side="left", fill="x", expand=True)
        lbl.configure(cursor="hand2")
        lbl.bind("<ButtonPress-1>", lambda ev, t=text: self._press(ev, t))
        lbl.bind("<B1-Motion>", self._maybe_drag)
        lbl.bind("<ButtonRelease-1>", self._release)

        star_on = favorites.is_favorite(text)
        st = tk.Label(row, text="★" if star_on else "☆", bg=theme.FIELD,
                      fg="#ffd60a" if star_on else theme.DIM,
                      font=("Segoe UI", 11), padx=5, cursor="hand2")
        st.pack(side="right")
        st.bind("<Button-1>", lambda ev, t=text: self._star(t))
        helptip.tip(st, "Favorite / unfavorite (click again to remove)")

        from . import folders
        fname = folders.folder_of(text)
        if fname:
            tag = fname if len(fname) <= 16 else fname[:15] + "…"
            tk.Label(row, text="🗂 " + tag, bg=theme.FIELD, fg=theme.DIM,
                     font=("Segoe UI", 8)).pack(side="right", padx=(0, 2))
        fo = tk.Label(row, text="🗂", bg=theme.FIELD, fg=theme.DIM,
                      font=("Segoe UI", 11), padx=5, cursor="hand2")
        fo.pack(side="right")
        fo.bind("<Button-1>", lambda ev, t=text: self._assign_folder(t))
        fo.bind("<Enter>", lambda ev, w=fo: w.configure(fg=theme.ACCENT))
        fo.bind("<Leave>", lambda ev, w=fo: w.configure(fg=theme.DIM))
        helptip.tip(fo, "Move to a folder")

        ed = tk.Label(row, text="✎", bg=theme.FIELD, fg=theme.DIM,
                      font=("Segoe UI", 11), padx=5, cursor="hand2")
        ed.pack(side="right")
        ed.bind("<Button-1>", lambda ev, t=text, s=ts: self._edit_one(t, s))
        ed.bind("<Enter>", lambda ev, w=ed: w.configure(fg=theme.ACCENT))
        ed.bind("<Leave>", lambda ev, w=ed: w.configure(fg=theme.DIM))
        helptip.tip(ed, "Edit this text (with Ask AI)")

        x = tk.Label(row, text="✕", bg=theme.FIELD, fg=theme.DIM,
                     font=("Segoe UI", 11), padx=8, cursor="hand2")
        x.pack(side="right")
        if self._tab == "favs":
            x.bind("<Button-1>",
                   lambda ev, t=text: (favorites.remove(t), self.refresh()))
        else:
            x.bind("<Button-1>", lambda ev, s=ts: self._delete_one(s))
        x.bind("<Enter>", lambda ev, w=x: w.configure(fg="#ff453a"))
        x.bind("<Leave>", lambda ev, w=x: w.configure(fg=theme.DIM))
        helptip.tip(x, "Delete")

    # ---------- actions ----------

    def _switch(self, tab):
        self._tab = tab
        self._page = 0
        on, off = ((self._tab_recent, self._tab_favs) if tab == "recent"
                   else (self._tab_favs, self._tab_recent))
        on.configure(bg=theme.FIELD, fg=theme.FG)
        off.configure(bg=theme.BG, fg=theme.DIM)
        self.refresh()

    def _flip(self, d):
        self._page += d
        self.refresh()

    def _set_hist_folder(self, v):
        self._hist_folder = v
        self._page = 0
        self.refresh()

    def _new_folder(self):
        from . import folder_dialog, folders
        name = folder_dialog.new_folder(self.win)
        if not name:
            return
        folders.create(name)
        self._hist_folder = name
        self._flash(f"Folder '{name}' created")
        self.refresh()

    def _assign_folder(self, text):
        from . import folder_dialog, folders
        cur = folders.folder_of(text)
        name = folder_dialog.move_to_folder(
            self.win, current=cur, names=folders.all_folders())
        if name is None:
            return
        folders.assign(text, name)
        self._flash(f"Moved to '{name}'" if name else "Removed from folder")
        self.refresh()

    def _flash(self, msg):
        self.status.configure(text=msg)
        self.win.after(1600, lambda: self.status.configure(text=""))

    def _copy_one(self, text):
        try:
            import pyperclip
            pyperclip.copy(text)
            self._flash("Copied ✓")
        except Exception:
            self._flash("Copy failed")

    # ---------- clipboard-style click-to-paste / drag-to-drop ----------

    def _own_hwnd(self):
        try:
            return ctypes.windll.user32.GetParent(self.win.winfo_id())
        except Exception:
            return None

    def _watch_foreground(self):
        u32 = ctypes.windll.user32
        while getattr(self, "_watching", False):
            try:
                fg = u32.GetForegroundWindow()
                if fg and fg != self._own_hwnd():
                    self._last_target = fg
            except Exception:
                pass
            time.sleep(0.4)

    def _press(self, e, text):
        self._drag_text = text
        self._press_x, self._press_y = e.x_root, e.y_root
        self._dragging = False

    def _maybe_drag(self, e):
        if not self._dragging and (abs(e.x_root - self._press_x) > DRAG_THRESHOLD
                                   or abs(e.y_root - self._press_y) > DRAG_THRESHOLD):
            self._dragging = True
            self.win.configure(cursor="hand2")
            self._flash("Carrying it — release over any text box")

    def _release(self, e):
        self.win.configure(cursor="")
        if not getattr(self, "_dragging", False):
            self._paste_to_last_app(getattr(self, "_drag_text", ""))
            return
        try:
            pt = _cursor_pos()
            hwnd = ctypes.windll.user32.WindowFromPoint(pt)
            root_hwnd = ctypes.windll.user32.GetAncestor(hwnd, 2)   # GA_ROOT
            if not hwnd or root_hwnd == self._own_hwnd():
                self._flash("Dropped on this window — click a line to paste instead")
                return
            import pyperclip
            pyperclip.copy(self._drag_text)
            ctypes.windll.user32.SetForegroundWindow(root_hwnd)
            time.sleep(0.15)
            _click_at_cursor()
            time.sleep(0.10)
            injector.press_ctrl_v()
            self._flash("Dropped ✓")
        except Exception:
            self._flash("Copied ✓ — Ctrl+V to paste")

    def _paste_to_last_app(self, text):
        if not text:
            return
        try:
            import pyperclip
            pyperclip.copy(text)
        except Exception:
            self._flash("Copy failed")
            return
        target = self._last_target
        if target:
            try:
                ctypes.windll.user32.SetForegroundWindow(target)
                time.sleep(0.20)
                injector.press_ctrl_v()
                self._flash("Pasted into your last app ✓")
            except Exception:
                self._flash("Copied ✓ — Ctrl+V to paste")
        else:
            self._flash("Copied ✓ — Ctrl+V to paste")

    def _star(self, text):
        favorites.toggle(text)
        self.refresh()

    def _edit_one(self, text, ts):
        from . import edit_dialog

        def _save(new_text):
            history.update(ts, new_text)
            self.refresh()
            self._flash("Saved ✓")

        def _del():
            try:
                history.delete(ts)
                favorites.remove(text)
            except Exception:
                pass
            self.refresh()
            self._flash("Deleted")
        edit_dialog.open_editor(self.win, text, _save, cfg=None,
                                title="Edit transcription", anchor=self.win,
                                on_delete=_del)

    def _delete_one(self, ts):
        history.delete(ts)
        self.refresh()

    def _delete_all(self):
        if self._tab == "favs":
            if favorites.all_favorites() and messagebox.askyesno(
                    "Clear favorites", "Remove ALL favorites?", parent=self.win):
                for e in list(favorites.all_favorites()):
                    favorites.remove(e.get("text", ""))
                self.refresh()
            return
        if messagebox.askyesno("Delete all",
                               "Delete ALL transcriptions?", parent=self.win):
            history.clear()
            self.refresh()
