"""Preset 'Ask AI' questions for the transcriber and meeting areas.

Ships with sensible defaults; the user (admin) can add or remove their own,
stored locally in the config so they persist."""

DEFAULTS = [
    "Summarize this into concise key points.",
    "List every action item and next step.",
    "Extract all the steps or instructions mentioned, in order.",
    "Pull out all names, tools, links and resources referenced.",
    "Write a short professional summary I could paste into an email.",
    "What are the key takeaways, and why do they matter?",
    "Turn this into a clean bulleted outline.",
]


def all_prompts(cfg):
    custom = (cfg or {}).get("custom_prompts") or []
    return list(DEFAULTS) + [c for c in custom if c not in DEFAULTS]


def add_prompt(cfg, text):
    text = (text or "").strip()
    if not text or text in DEFAULTS:
        return
    lst = list((cfg or {}).get("custom_prompts") or [])
    if text not in lst:
        lst.append(text)
        cfg["custom_prompts"] = lst
        _save(cfg)


def remove_prompt(cfg, text):
    lst = [t for t in ((cfg or {}).get("custom_prompts") or []) if t != text]
    cfg["custom_prompts"] = lst
    _save(cfg)


def _save(cfg):
    try:
        from . import config as _c
        _c.save(cfg)
    except Exception:
        pass


MANAGE_LABEL = "\u2699  Add / edit my presets\u2026"


def menu_items(cfg):
    """Preset questions plus the 'manage' entry at the very bottom."""
    return all_prompts(cfg) + [MANAGE_LABEL]


def manage_dialog(parent, cfg, on_change=lambda: None):
    """Add / edit / delete YOUR presets. Built-in defaults stay locked."""
    import tkinter as tk
    from tkinter import ttk, simpledialog, messagebox
    from . import theme
    dlg = tk.Toplevel(parent)
    dlg.title("Ask-AI presets")
    dlg.geometry("540x440")
    dlg.attributes("-topmost", True)
    theme.apply(dlg)
    ttk.Label(dlg, text="Ask-AI questions", style="Title.TLabel"
              ).pack(anchor="w", padx=14, pady=(12, 4))
    ttk.Label(dlg, style="Dim.TLabel", wraplength=500, text=(
        "The (default) ones are built in. Add your own below, and edit or "
        "delete the ones you added.")).pack(anchor="w", padx=14)
    lb = theme.dark_listbox(dlg, height=12)
    lb.pack(fill="both", expand=True, padx=14, pady=6)

    def reload():
        lb.delete(0, "end")
        for q in DEFAULTS:
            lb.insert("end", "  (default)  " + q)
        for q in (cfg.get("custom_prompts") or []):
            lb.insert("end", "  (mine)  " + q)
    reload()

    row = ttk.Frame(dlg); row.pack(fill="x", padx=14, pady=(0, 6))
    var = tk.StringVar()
    ent = ttk.Entry(row, textvariable=var)
    ent.pack(side="left", fill="x", expand=True, ipady=3)

    def _mine():
        sel = lb.curselection()
        if not sel:
            return None
        label = lb.get(sel[0])
        return label.split("(mine)", 1)[1].strip() if "(mine)" in label else None

    def add():
        add_prompt(cfg, var.get()); var.set(""); reload(); on_change()
    ent.bind("<Return>", lambda e: add())
    ttk.Button(row, text="Add", command=add).pack(side="left", padx=(6, 0))

    def edit():
        q = _mine()
        if not q:
            messagebox.showinfo("Edit", "Pick one of YOUR presets (defaults are locked).", parent=dlg); return
        new = simpledialog.askstring("Edit preset", "Rewrite the question:",
                                     initialvalue=q, parent=dlg)
        if new and new.strip():
            remove_prompt(cfg, q); add_prompt(cfg, new.strip()); reload(); on_change()

    def delete():
        q = _mine()
        if not q:
            messagebox.showinfo("Delete", "Pick one of YOUR presets (defaults can't be deleted).", parent=dlg); return
        remove_prompt(cfg, q); reload(); on_change()
    brow = ttk.Frame(dlg); brow.pack(fill="x", padx=14, pady=(0, 10))
    ttk.Button(brow, text="Edit selected", command=edit).pack(side="left")
    ttk.Button(brow, text="Delete selected", command=delete).pack(side="left", padx=6)
    ttk.Button(brow, text="Done", style="Accent.TButton",
               command=dlg.destroy).pack(side="right")
