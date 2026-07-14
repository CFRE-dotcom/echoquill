"""Recent transcriptions - works like the Clips tray: per-row ★ favorite,
✎ edit, ✕ delete, a Recent / Favorites tab, and a real search box.

Free keeps the last 10; Pro pages through everything.
"""

import tkinter as tk
from tkinter import ttk, messagebox

from . import favorites, helptip, history, theme, widgets


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
                       "Click a line to copy it.\n"
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

        if self._tab == "favs":
            self._page_row.pack_forget()
            self._delall_btn.configure(text="Clear favorites")
            data = favorites.all_favorites()
            if term:
                data = [e for e in data if term in e.get("text", "").lower()]
            page = data
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
        lbl.bind("<Button-1>", lambda ev, t=text: self._copy_one(t))
        lbl.bind("<Double-Button-1>", lambda ev, t=text, s=ts: self._edit_one(t, s))

        star_on = favorites.is_favorite(text)
        st = tk.Label(row, text="★" if star_on else "☆", bg=theme.FIELD,
                      fg="#ffd60a" if star_on else theme.DIM,
                      font=("Segoe UI", 11), padx=5, cursor="hand2")
        st.pack(side="right")
        st.bind("<Button-1>", lambda ev, t=text: self._star(t))
        helptip.tip(st, "Favorite / unfavorite (click again to remove)")

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

    def _star(self, text):
        favorites.toggle(text)
        self.refresh()

    def _edit_one(self, text, ts):
        from . import edit_dialog

        def _save(new_text):
            history.update(ts, new_text)
            self.refresh()
            self._flash("Saved ✓")
        edit_dialog.open_editor(self.win, text, _save, cfg=None,
                                title="Edit transcription", anchor=self.win)

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
