"""Shared 'Edit text' dialog used by clips + recent transcriptions.

- Save / Cancel are pinned to the bottom so they're ALWAYS visible.
- Opens right next to the window it came from (deterministic placement).
- Ask AI: type an instruction ('make it professional', 'turn into an email',
  'summarize', 'fix grammar') and the AI rewrites the text in place.
"""

import tkinter as tk

from . import theme


def open_editor(parent, text, on_save, cfg=None, title="Edit", anchor=None):
    dlg = tk.Toplevel(parent)
    dlg.title(title)
    dlg.configure(bg=theme.PANEL)
    dlg.attributes("-topmost", True)
    dlg.protocol("WM_DELETE_WINDOW", dlg.destroy)
    W, H = 520, 380
    dlg.geometry(f"{W}x{H}")
    dlg.minsize(420, 320)
    _place_next_to(dlg, anchor, W, H)

    tk.Label(dlg, text="Edit the text, then Save:", bg=theme.PANEL,
             fg=theme.DIM, font=("Segoe UI", 10)).pack(anchor="w", padx=12, pady=(12, 4))

    # ---- bottom button bar (packed FIRST so it can never be pushed off) ----
    bar = tk.Frame(dlg, bg=theme.PANEL)
    bar.pack(side="bottom", fill="x", padx=12, pady=(6, 10))

    def save():
        on_save(box.get("1.0", "end").strip())
        dlg.destroy()

    tk.Button(bar, text="Save", command=save, bg=theme.ACCENT, fg="#ffffff",
              borderwidth=0, padx=16, pady=5, cursor="hand2",
              font=("Segoe UI Semibold", 10)).pack(side="right")
    tk.Button(bar, text="Cancel", command=dlg.destroy, bg=theme.FIELD,
              fg=theme.FG, borderwidth=0, padx=14, pady=5, cursor="hand2"
              ).pack(side="right", padx=6)

    # ---- Ask AI row (also above the text, pinned near the bottom) ----
    ai = tk.Frame(dlg, bg=theme.PANEL)
    ai.pack(side="bottom", fill="x", padx=12, pady=(0, 4))
    tk.Label(ai, text="Ask AI:", bg=theme.PANEL, fg=theme.DIM,
             font=("Segoe UI", 9)).pack(side="left")
    instr = tk.Entry(ai, bg=theme.FIELD, fg=theme.FG, insertbackground=theme.FG,
                     borderwidth=0, font=("Segoe UI", 10))
    instr.pack(side="left", fill="x", expand=True, padx=6, ipady=3)
    instr.insert(0, "")
    status = tk.Label(ai, text="", bg=theme.PANEL, fg=theme.DIM,
                      font=("Segoe UI", 9))

    def ask_ai(_e=None):
        instruction = instr.get().strip()
        if not instruction:
            _set_status(status, "Type what you want AI to do (e.g. 'make it professional')")
            return
        current = box.get("1.0", "end").strip()
        if not current:
            _set_status(status, "Nothing to work with")
            return
        _set_status(status, "Thinking…")
        ai_btn.configure(state="disabled")
        import threading

        def run():
            _cfg = cfg
            if _cfg is None:
                try:
                    from . import config as _c
                    _cfg = _c.load()
                except Exception:
                    _cfg = {}
            from . import ai_edit
            ok, result = ai_edit.transform(current, instruction, _cfg)

            def apply():
                ai_btn.configure(state="normal")
                if ok:
                    box.delete("1.0", "end")
                    box.insert("1.0", result)
                    _set_status(status, "Done ✓ (edit more or Save)")
                else:
                    _set_status(status, result)
            try:
                dlg.after(0, apply)
            except Exception:
                pass
        threading.Thread(target=run, daemon=True).start()

    ai_btn = tk.Button(ai, text="Ask AI", command=ask_ai, bg=theme.ACCENT,
                       fg="#ffffff", borderwidth=0, padx=12, pady=3,
                       cursor="hand2", font=("Segoe UI Semibold", 9))
    ai_btn.pack(side="right")
    status.pack(side="bottom", anchor="w", padx=12)
    instr.bind("<Return>", ask_ai)

    # ---- the editable text fills the rest ----
    box = tk.Text(dlg, wrap="word", bg=theme.FIELD, fg=theme.FG,
                  insertbackground=theme.FG, borderwidth=0, height=8,
                  font=("Segoe UI", 10))
    box.pack(side="top", fill="both", expand=True, padx=12, pady=(0, 4))
    box.insert("1.0", text)
    box.focus_set()

    try:
        dlg.transient(parent)
    except Exception:
        pass
    return dlg


def _set_status(lbl, msg):
    try:
        lbl.configure(text=msg)
    except Exception:
        pass


def _place_next_to(dlg, anchor, w, h):
    """Open right beside the window it came from; flip side if it won't fit."""
    dlg.update_idletasks()
    try:
        sw = dlg.winfo_screenwidth()
        sh = dlg.winfo_screenheight()
    except Exception:
        sw, sh = 1920, 1080
    margin = 14
    if anchor is not None:
        try:
            anchor.update_idletasks()
            ax, ay = anchor.winfo_rootx(), anchor.winfo_rooty()
            aw = anchor.winfo_width()
        except Exception:
            ax = ay = aw = None
    else:
        ax = ay = aw = None
    if ax is None:
        x = (sw - w) // 2
        y = (sh - h) // 3
    else:
        # prefer the right of the anchor; if it would run off, go left
        if ax + aw + margin + w <= sw:
            x = ax + aw + margin
        else:
            x = ax - margin - w
        if x < 0:
            x = margin
        y = ay
        if y + h > sh:
            y = max(margin, sh - h - margin)
    dlg.geometry(f"{w}x{h}+{int(x)}+{int(y)}")
