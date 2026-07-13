"""Shared 'Edit text' dialog used by clips + recent transcriptions.

Layout is built bottom-up so every control is always visible without resizing:
  [ title ]
  [ text box .............. fills ]
  [ Ask AI: (instruction) [Ask AI] ]
  [ status line ]
  [           Cancel  Save ]
"""

import tkinter as tk

from . import theme

_PLACEHOLDER = "what you want AI to do (e.g. 'make it professional', 'turn into an email')"


def _tooltip(widget, text):
    st = {"t": None}

    def show(_e=None):
        if st["t"] is not None:
            return
        t = tk.Toplevel(widget)
        t.overrideredirect(True)
        t.attributes("-topmost", True)
        tk.Label(t, text=text, bg=theme.SIDEBAR, fg=theme.FG,
                 font=("Segoe UI", 9), justify="left", wraplength=300,
                 padx=9, pady=6, highlightthickness=1,
                 highlightbackground=theme.ACCENT).pack()
        t.update_idletasks()
        x = widget.winfo_rootx()
        y = widget.winfo_rooty() - t.winfo_reqheight() - 5
        if y < 8:
            y = widget.winfo_rooty() + widget.winfo_height() + 5
        t.geometry(f"+{int(x)}+{int(y)}")
        st["t"] = t

    def hide(_e=None):
        if st["t"] is not None:
            try:
                st["t"].destroy()
            except Exception:
                pass
            st["t"] = None

    widget.bind("<Enter>", show)
    widget.bind("<Leave>", hide)


def open_editor(parent, text, on_save, cfg=None, title="Edit", anchor=None):
    dlg = tk.Toplevel(parent)
    dlg.title(title)
    dlg.configure(bg=theme.PANEL)
    dlg.attributes("-topmost", True)
    dlg.protocol("WM_DELETE_WINDOW", dlg.destroy)
    W, H = 560, 470
    dlg.minsize(500, 430)
    _place_next_to(dlg, anchor, W, H)

    tk.Label(dlg, text="Edit the text, then Save:", bg=theme.PANEL,
             fg=theme.DIM, font=("Segoe UI", 10)
             ).pack(anchor="w", padx=14, pady=(12, 4))

    # ---- bottom button bar (packed FIRST so it can never be pushed off) ----
    bar = tk.Frame(dlg, bg=theme.PANEL)
    bar.pack(side="bottom", fill="x", padx=14, pady=(8, 12))

    def save():
        on_save(box.get("1.0", "end").strip())
        dlg.destroy()

    tk.Button(bar, text="Save", command=save, bg=theme.ACCENT, fg="#ffffff",
              activebackground="#3396ff", activeforeground="#ffffff",
              borderwidth=0, padx=20, pady=6, cursor="hand2",
              font=("Segoe UI Semibold", 10)).pack(side="right")
    tk.Button(bar, text="Cancel", command=dlg.destroy, bg=theme.FIELD,
              fg=theme.FG, activebackground=theme.SIDEBAR, activeforeground=theme.FG,
              borderwidth=0, padx=16, pady=6, cursor="hand2",
              font=("Segoe UI", 10)).pack(side="right", padx=8)

    # ---- status line (its own row, always visible) ----
    status = tk.Label(dlg, text="", bg=theme.PANEL, fg=theme.DIM,
                      font=("Segoe UI", 9), anchor="w", justify="left",
                      wraplength=W - 40)
    status.pack(side="bottom", fill="x", padx=14, pady=(0, 2))

    # ---- Ask AI row ----
    ai = tk.Frame(dlg, bg=theme.PANEL)
    ai.pack(side="bottom", fill="x", padx=14, pady=(8, 2))
    tk.Label(ai, text="Ask AI:", bg=theme.PANEL, fg=theme.FG,
             font=("Segoe UI Semibold", 9)).pack(side="left")

    ai_btn = tk.Button(ai, text="Ask AI", bg=theme.ACCENT, fg="#ffffff",
                       activebackground="#3396ff", activeforeground="#ffffff",
                       borderwidth=0, padx=16, pady=4, cursor="hand2",
                       font=("Segoe UI Semibold", 9))
    ai_btn.pack(side="right")
    _tooltip(ai_btn, "Rewrite or reformat the text using your instruction "
                     "(or ask a question about it). Uses your AI provider from "
                     "Settings > AI Enhancement.")

    instr = tk.Entry(ai, bg=theme.FIELD, fg=theme.DIM, insertbackground=theme.FG,
                     borderwidth=0, font=("Segoe UI", 10),
                     highlightthickness=1, highlightbackground=theme.DIM,
                     highlightcolor=theme.ACCENT)
    instr.pack(side="left", fill="x", expand=True, padx=8, ipady=5)
    instr.insert(0, _PLACEHOLDER)
    _ph = {"on": True}

    def _clear_ph(_e=None):
        if _ph["on"]:
            instr.delete(0, "end")
            instr.configure(fg=theme.FG)
            _ph["on"] = False

    def _restore_ph(_e=None):
        if not instr.get().strip():
            instr.delete(0, "end")
            instr.insert(0, _PLACEHOLDER)
            instr.configure(fg=theme.DIM)
            _ph["on"] = True

    instr.bind("<FocusIn>", _clear_ph)
    instr.bind("<FocusOut>", _restore_ph)

    def ask_ai(_e=None):
        instruction = "" if _ph["on"] else instr.get().strip()
        if not instruction:
            status.configure(text="Type what you want AI to do, then click Ask AI.",
                             fg="#ff9f0a")
            instr.focus_set()
            return
        current = box.get("1.0", "end").strip()
        if not current:
            status.configure(text="Nothing to work with.", fg="#ff9f0a")
            return
        status.configure(text="Thinking…", fg=theme.DIM)
        ai_btn.configure(state="disabled", text="…")
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
                ai_btn.configure(state="normal", text="Ask AI")
                if ok:
                    box.delete("1.0", "end")
                    box.insert("1.0", result)
                    status.configure(text="Done ✓  — edit more if you like, then Save.",
                                     fg="#30d158")
                else:
                    status.configure(text=result, fg="#ff453a")
            try:
                dlg.after(0, apply)
            except Exception:
                pass
        threading.Thread(target=run, daemon=True).start()

    ai_btn.configure(command=ask_ai)
    instr.bind("<Return>", ask_ai)

    # ---- the editable text fills whatever space is left ----
    box = tk.Text(dlg, wrap="word", bg=theme.FIELD, fg=theme.FG,
                  insertbackground=theme.FG, borderwidth=0, height=8,
                  font=("Segoe UI", 10))
    box.pack(side="top", fill="both", expand=True, padx=14, pady=(0, 2))
    box.insert("1.0", text)
    box.focus_set()

    try:
        dlg.transient(parent)
    except Exception:
        pass
    return dlg


def _place_next_to(dlg, anchor, w, h):
    """Open right beside the window it came from; flip side if it won't fit."""
    dlg.update_idletasks()
    try:
        sw = dlg.winfo_screenwidth()
        sh = dlg.winfo_screenheight()
    except Exception:
        sw, sh = 1920, 1080
    margin = 14
    ax = ay = aw = None
    if anchor is not None:
        try:
            anchor.update_idletasks()
            ax, ay = anchor.winfo_rootx(), anchor.winfo_rooty()
            aw = anchor.winfo_width()
        except Exception:
            ax = ay = aw = None
    if ax is None:
        x = (sw - w) // 2
        y = (sh - h) // 3
    else:
        if ax + aw + margin + w <= sw:
            x = ax + aw + margin
        else:
            x = ax - margin - w
        x = max(margin, min(x, sw - w - margin))
        y = ay
        if y + h > sh:
            y = max(margin, sh - h - margin)
    dlg.geometry(f"{w}x{h}+{int(x)}+{int(y)}")
