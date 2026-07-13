"""Reusable UI bits shared across windows."""

import tkinter as tk

from . import theme


def make_search(parent, placeholder, on_change):
    """A proper search box: bordered, with grey placeholder text that clears
    when you click in and comes back when you leave it empty.

    Returns (frame, value_fn). value_fn() -> the current query ('' if empty)."""
    wrap = tk.Frame(parent, bg=theme.FIELD, highlightthickness=1,
                    highlightbackground=theme.BORDER, highlightcolor=theme.ACCENT)
    tk.Label(wrap, text="Search", bg=theme.FIELD, fg=theme.DIM,
             font=("Segoe UI", 9)).pack(side="left", padx=(10, 4))
    ent = tk.Entry(wrap, bg=theme.FIELD, fg=theme.DIM, insertbackground=theme.FG,
                   borderwidth=0, font=("Segoe UI", 10))
    ent.pack(side="left", fill="x", expand=True, padx=(0, 10), ipady=6)
    ent.insert(0, placeholder)
    state = {"ph": True}

    def clear(_e=None):
        if state["ph"]:
            ent.delete(0, "end")
            ent.configure(fg=theme.FG)
            state["ph"] = False

    def restore(_e=None):
        if not ent.get().strip():
            ent.delete(0, "end")
            ent.insert(0, placeholder)
            ent.configure(fg=theme.DIM)
            state["ph"] = True

    ent.bind("<FocusIn>", clear)
    ent.bind("<FocusOut>", restore)
    ent.bind("<KeyRelease>", lambda e: on_change())

    def value():
        return "" if state["ph"] else ent.get().strip()

    return wrap, value
