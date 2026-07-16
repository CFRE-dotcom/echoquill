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

    ttk.Label(dlg, style="Dim.TLabel",
              text="Add a new question (Ctrl+Enter or the Add button):").pack(
              anchor="w", padx=14, pady=(4, 0))
    row = ttk.Frame(dlg); row.pack(fill="x", padx=14, pady=(0, 6))
    ent = theme.dark_text(row, wrap="word", height=3)
    ent.pack(side="left", fill="x", expand=True)

    def _mine():
        sel = lb.curselection()
        if not sel:
            return None
        label = lb.get(sel[0])
        return label.split("(mine)", 1)[1].strip() if "(mine)" in label else None

    def add():
        t = ent.get("1.0", "end").strip()
        if t:
            add_prompt(cfg, t); ent.delete("1.0", "end"); reload(); on_change()
    ent.bind("<Control-Return>", lambda e: (add(), "break")[1])
    ttk.Button(row, text="Add", command=add).pack(side="left", padx=(6, 0))

    def _ask_block(title, initial=""):
        d = tk.Toplevel(dlg); d.title(title); d.attributes("-topmost", True)
        d.geometry("540x300"); d.resizable(True, True); theme.apply(d)
        ttk.Label(d, style="Dim.TLabel",
                  text="Edit the question, then Save:").pack(
                  anchor="w", padx=14, pady=(12, 4))
        box = theme.dark_text(d, wrap="word", height=8)
        box.pack(fill="both", expand=True, padx=14, pady=(0, 8))
        box.insert("1.0", initial); box.focus_set()
        res = {"v": None}
        bar = ttk.Frame(d); bar.pack(fill="x", padx=14, pady=(0, 12))
        def _ok():
            res["v"] = box.get("1.0", "end").strip(); d.destroy()
        ttk.Button(bar, text="Save", style="Accent.TButton",
                   command=_ok).pack(side="right")
        ttk.Button(bar, text="Cancel", command=d.destroy).pack(
            side="right", padx=8)
        try:
            d.grab_set()
        except Exception:
            pass
        dlg.wait_window(d)
        return res["v"]

    def edit():
        q = _mine()
        if not q:
            messagebox.showinfo("Edit", "Pick one of YOUR presets (defaults are locked).", parent=dlg); return
        new = _ask_block("Edit preset", q)
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


# ---- saved question sets (named groups of presets you can re-run) ----

def get_sets(cfg):
    return cfg.get("prompt_sets") or []


def set_names(cfg):
    return [s.get("name", "") for s in get_sets(cfg) if s.get("name")]


def get_set(cfg, name):
    for s in get_sets(cfg):
        if s.get("name") == name:
            return list(s.get("questions") or [])
    return []


def save_set(cfg, name, questions):
    name = (name or "").strip()
    if not name:
        return
    sets = [s for s in get_sets(cfg) if s.get("name") != name]
    sets.append({"name": name, "questions": list(questions)})
    cfg["prompt_sets"] = sets
    try:
        from . import config as _c
        _c.save(cfg)
    except Exception:
        pass


def delete_set(cfg, name):
    cfg["prompt_sets"] = [s for s in get_sets(cfg) if s.get("name") != name]
    try:
        from . import config as _c
        _c.save(cfg)
    except Exception:
        pass
