"""EchoQuill settings - dark, sidebar-style window (modeled on modern
settings panes like the app that inspired this project).

Sections: General · Dictation · Dictionary · AI Enhancement · History · About
"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog

from . import config as cfgmod
from . import history as historymod
from . import theme


class SettingsWindow:
    SECTIONS = ["General", "AI Enhancement", "Clipboard", "Dictation",
                "Dictionary", "Meeting", "Read aloud", "Transcription",
                "History", "Stats", "Help", "Feedback", "About",
                "What\u2019s New"]

    def __init__(self, root: tk.Tk, cfg: dict, dictionary, on_save,
                 on_media=None, on_clips=None, on_history=None,
                 on_quit=None, on_restart=None, initial_section=None):
        self.cfg = cfg
        self.dictionary = dictionary
        self.on_save = on_save
        self.on_media = on_media
        self.on_clips = on_clips
        self.on_history = on_history
        self.on_quit = on_quit
        self.on_restart = on_restart

        self.win = tk.Toplevel(root)
        self.win.title("EchoQuill Settings")
        self.win.geometry("880x620")
        self.win.minsize(760, 540)
        self.win.attributes("-topmost", True)
        theme.apply(self.win)

        # ----- layout: sidebar | content -----
        self.sidebar = tk.Frame(self.win, bg=theme.SIDEBAR, width=180)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        tk.Label(self.sidebar, text="EchoQuill", bg=theme.SIDEBAR,
                 fg=theme.FG, font=("Segoe UI Semibold", 14)
                 ).pack(anchor="w", padx=18, pady=(18, 14))

        # everything right of the sidebar: content on top, save bar below it
        right = ttk.Frame(self.win)
        right.pack(side="left", fill="both", expand=True)
        self._save_bar = ttk.Frame(right)
        self._save_bar.pack(side="bottom", fill="x")
        ttk.Button(self._save_bar, text="Save changes", style="Accent.TButton",
                   command=self._save).pack(side="right", padx=16, pady=10)
        self.content = ttk.Frame(right)
        self.content.pack(side="top", fill="both", expand=True)
        # green "update available" banner (hidden until a check finds one)
        self._update_banner = tk.Frame(right, bg="#30d158")

        up = tk.Label(self.sidebar, text="⭐ Upgrade to Pro",
                      bg=theme.SIDEBAR, fg="#ffd60a",
                      font=("Segoe UI Semibold", 10), cursor="hand2", pady=10)
        up.pack(side="bottom", fill="x")
        up.bind("<Button-1>", lambda e: self._open_upgrade())
        tk.Label(self.sidebar, text="$5/mo · $39/yr", bg=theme.SIDEBAR,
                 fg=theme.DIM, font=("Segoe UI", 8)).pack(side="bottom")

        navwrap = tk.Frame(self.sidebar, bg=theme.SIDEBAR)
        navwrap.pack(side="top", fill="both", expand=True)
        self._navcanvas = tk.Canvas(navwrap, bg=theme.SIDEBAR,
                                    highlightthickness=0, width=180)
        _navsb = ttk.Scrollbar(navwrap, orient="vertical",
                               command=self._navcanvas.yview,
                               style="Sidebar.Vertical.TScrollbar")
        self._navinner = tk.Frame(self._navcanvas, bg=theme.SIDEBAR)
        _nid = self._navcanvas.create_window((0, 0), window=self._navinner,
                                             anchor="nw")
        self._navcanvas.configure(yscrollcommand=_navsb.set)
        self._navcanvas.pack(side="left", fill="both", expand=True)

        def _nav_cfg(_e=None):
            try:
                self._navcanvas.configure(scrollregion=self._navcanvas.bbox("all"))
                need = (self._navinner.winfo_reqheight()
                        > self._navcanvas.winfo_height() + 1)
                if need and not _navsb.winfo_ismapped():
                    _navsb.pack(side="right", fill="y")
                elif not need and _navsb.winfo_ismapped():
                    _navsb.pack_forget()
            except Exception:
                pass
        self._navinner.bind("<Configure>", _nav_cfg)
        self._navcanvas.bind("<Configure>", lambda e: (
            self._navcanvas.itemconfigure(_nid, width=e.width), _nav_cfg()))
        self._navcanvas.bind("<Enter>", lambda e: self._navcanvas.bind_all(
            "<MouseWheel>", lambda ev: self._navcanvas.yview_scroll(
                int(-ev.delta / 120), "units")))
        self._navcanvas.bind("<Leave>",
                             lambda e: self._navcanvas.unbind_all("<MouseWheel>"))

        self._nav_buttons = {}
        self._frames = {}
        for name in self.SECTIONS:
            b = tk.Label(self._navinner, text=name, bg=theme.SIDEBAR,
                         fg=theme.DIM, font=("Segoe UI", 11), anchor="w",
                         padx=18, pady=8, cursor="hand2")
            b.pack(fill="x")
            b.bind("<Button-1>", lambda e, n=name: self._show(n))
            self._nav_buttons[name] = b

        body = {"General": self._build_general,
                "Dictation": self._build_dictation,
                "Transcription": self._build_transcription,
                "Meeting": self._build_meeting,
                "Read aloud": self._build_read_aloud,
                "Clipboard": self._build_clipboard,
                "Dictionary": self._build_dictionary,
                "AI Enhancement": self._build_ai,
                "Stats": self._build_stats,
                "History": self._build_history,
                "Help": self._build_help,
                "Feedback": self._build_feedback,
                "About": self._build_about,
                "What\u2019s New": self._build_whatsnew}
        _noscroll = {"Meeting", "Read aloud", "Transcription", "History",
                     "Help", "Feedback", "Dictionary", "What\u2019s New"}
        for name, builder in body.items():
            if name in _noscroll:
                fr = ttk.Frame(self.content)
                builder(fr)
                self._frames[name] = fr
            else:
                sc = theme.Scrollable(self.content)
                builder(sc.inner)
                self._frames[name] = sc

        self._show(initial_section if initial_section in self.SECTIONS
                   else "General")
        self._snapshot = self._collect_state()
        self.win.protocol("WM_DELETE_WINDOW", self._on_close)
        self._start_update_autocheck()

    def show_section(self, name=None):
        if name in self.SECTIONS:
            self._show(name)          # only switch tabs when explicitly asked
        self.raise_window()
        self._start_update_autocheck()

    def raise_window(self):
        """Actually bring the window to the front (Windows fights this)."""
        try:
            self.win.deiconify()
            self.win.lift()
            self.win.attributes("-topmost", True)
            self.win.focus_force()
            # nudge Windows' foreground lock with a quick topmost pulse
            self.win.after(150, lambda: self.win.attributes("-topmost", True))
        except Exception:
            pass

    # ---------- navigation ----------

    # only these tabs have anything to save
    SAVE_SECTIONS = {"General", "Dictation", "Dictionary", "AI Enhancement"}

    def _show(self, name):
        if name in self.SAVE_SECTIONS:
            self._save_bar.pack(side="bottom", fill="x")
        else:
            self._save_bar.pack_forget()
        for n, b in self._nav_buttons.items():
            active = (n == name)
            b.configure(bg=theme.PANEL if active else theme.SIDEBAR,
                        fg=theme.FG if active else theme.DIM)
        for n, f in self._frames.items():
            f.pack_forget()
        self._frames[name].pack(fill="both", expand=True, padx=24, pady=18)

    def _title(self, parent, text, sub=""):
        ttk.Label(parent, text=text, style="Title.TLabel").pack(anchor="w")
        if sub:
            ttk.Label(parent, text=sub, style="Dim.TLabel",
                      wraplength=460).pack(anchor="w", pady=(2, 0))
        ttk.Frame(parent, height=12).pack()

    def _row(self, parent, label):
        r = ttk.Frame(parent)
        r.pack(fill="x", pady=5)
        ttk.Label(r, text=label, width=30).pack(side="left")
        return r

    # ---------- sections ----------

    def _build_general(self, f):
        self._title(f, "General", "How you start dictating and where text goes.")

        r = self._row(f, "Activation")
        self.actmode_var = tk.StringVar(value=self.cfg.get("activation_mode", "toggle"))
        ttk.Combobox(r, textvariable=self.actmode_var, width=24, state="readonly",
                     values=["toggle", "hold"]).pack(side="left")
        ttk.Label(f, style="Dim.TLabel", wraplength=460, text=(
            "toggle: press the hotkey to start, again to stop · "
            "hold: keep the hold-key pressed while you talk")).pack(anchor="w")

        r = self._row(f, "Hotkey (toggle mode)")
        self.hotkey_var = tk.StringVar(value=self.cfg["hotkey"])
        ttk.Entry(r, textvariable=self.hotkey_var, width=26).pack(side="left")

        r = self._row(f, "Hold key (hold mode)")
        self.holdkey_var = tk.StringVar(value=self.cfg.get("hold_key", "right alt"))
        ttk.Entry(r, textvariable=self.holdkey_var, width=26).pack(side="left")

        r = self._row(f, "Insert text by")
        self.insert_var = tk.StringVar(value=self.cfg["insertion_mode"])
        ttk.Combobox(r, textvariable=self.insert_var, width=24, state="readonly",
                     values=["paste", "type", "clipboard"]).pack(side="left")

        self.always_copy_var = tk.BooleanVar(value=self.cfg.get("always_copy", True))
        ttk.Checkbutton(f, variable=self.always_copy_var, text=(
            "Also keep every transcription on the clipboard (paste anywhere with Ctrl+V)"
        )).pack(anchor="w", pady=(8, 2))

        self.overlay_var = tk.BooleanVar(value=self.cfg["overlay_enabled"])
        ttk.Checkbutton(f, text="Show the on-screen microphone pill",
                        variable=self.overlay_var).pack(anchor="w", pady=2)

        r = self._row(f, "Appearance")
        self.theme_var = tk.StringVar(value=self.cfg.get("theme", "dark"))
        ttk.Combobox(r, textvariable=self.theme_var, width=24, state="readonly",
                     values=["dark", "light", "system"]).pack(side="left")
        ttk.Label(f, style="Dim.TLabel",
                  text="Reopen windows to see a theme change take full effect."
                  ).pack(anchor="w")

        self.autostart_var = tk.BooleanVar(value=self.cfg.get("autostart", False))
        ttk.Checkbutton(f, text="Start EchoQuill automatically when Windows starts",
                        variable=self.autostart_var).pack(anchor="w", pady=2)

        self.adminmode_var = tk.BooleanVar(value=self.cfg.get("admin_mode", False))
        ttk.Checkbutton(f, variable=self.adminmode_var,
                        text="Administrator mode — type into apps that run as administrator"
                        ).pack(anchor="w", pady=(6, 0))
        ttk.Label(f, style="Dim.TLabel", wraplength=460, text=(
            "Some programs run with administrator rights, and Windows blocks "
            "normal apps from typing into them. If your dictated words won't "
            "appear in a specific program, turn this on. Enabling asks for a "
            "one-time Windows approval; leave it off unless you need it.")
            ).pack(anchor="w")

        ttk.Frame(f, height=8).pack()
        ttk.Label(f, text="VOICE MODES", style="Section.TLabel").pack(anchor="w", pady=(4, 4))

        self.cmdmode_var = tk.BooleanVar(value=self.cfg.get("command_mode", True))
        r = ttk.Frame(f); r.pack(fill="x", pady=2)
        ttk.Checkbutton(r, text="Command Mode — control the PC by voice, hotkey:",
                        variable=self.cmdmode_var).pack(side="left")
        self.cmdkey_var = tk.StringVar(value=self.cfg.get("command_hotkey", "ctrl+alt+c"))
        ttk.Entry(r, textvariable=self.cmdkey_var, width=14).pack(side="left", padx=6)

        self.writemode_var = tk.BooleanVar(value=self.cfg.get("write_mode", True))
        r = ttk.Frame(f); r.pack(fill="x", pady=2)
        ttk.Checkbutton(r, text="Write Mode — select text, speak to rewrite it, hotkey:",
                        variable=self.writemode_var).pack(side="left")
        self.writekey_var = tk.StringVar(value=self.cfg.get("write_hotkey", "ctrl+alt+w"))
        ttk.Entry(r, textvariable=self.writekey_var, width=14).pack(side="left", padx=6)
        ttk.Label(f, style="Dim.TLabel", wraplength=460, text=(
            'Command Mode examples: "open chrome", "search for tax deadlines", '
            '"press enter", "volume up", "lock the computer". Write Mode with AI '
            "enhancement rewrites your selection; without AI it replaces the "
            "selection with what you say.")).pack(anchor="w", pady=(2, 0))

    def _build_dictation(self, f):
        self._title(f, "Dictation",
                    "Speed, accuracy, language, microphone, and fine-tuning.")

        r = self._row(f, "Dictation quality")
        cur_label = cfgmod.MODEL_LABELS.get(self.cfg["model"],
                                            cfgmod.MODEL_LABELS["base"])
        self.model_var = tk.StringVar(value=cur_label)
        cb = ttk.Combobox(r, textvariable=self.model_var, width=42, state="readonly",
                          values=list(cfgmod.MODEL_LABELS.values()))
        cb.pack(side="left")
        self.model_hint = ttk.Label(f, style="Dim.TLabel", wraplength=460)
        self.model_hint.pack(anchor="w")

        def _model_hint(*_):
            mid = cfgmod.MODEL_IDS.get(self.model_var.get(), "base")
            hint = cfgmod.MODEL_CHOICES.get(mid, "")
            if mid in ("medium", "large-v3"):
                hint += "  ⚠ Not recommended for live dictation — words will lag. Great for video transcription."
            self.model_hint.configure(text=hint)
        _model_hint()
        cb.bind("<<ComboboxSelected>>", _model_hint)

        r = self._row(f, "Live words speed")
        cur_p = cfgmod.PREVIEW_LABELS.get(self.cfg.get("preview_model", "tiny"),
                                          cfgmod.PREVIEW_LABELS["tiny"])
        self.preview_var = tk.StringVar(value=cur_p)
        ttk.Combobox(r, textvariable=self.preview_var, width=42, state="readonly",
                     values=list(cfgmod.PREVIEW_LABELS.values())).pack(side="left")
        ttk.Label(f, style="Dim.TLabel", wraplength=460, text=(
            "Controls only the words shown while you're still talking. "
            "Your final text always uses the Dictation quality model above."
            )).pack(anchor="w")

        r = self._row(f, "Language")
        self.lang_var = tk.StringVar(value=self.cfg["language"])
        ttk.Entry(r, textvariable=self.lang_var, width=26).pack(side="left")
        ttk.Label(f, style="Dim.TLabel",
                  text='"auto" or a code: en, es, fr, de, pt, zh …').pack(anchor="w")

        r = self._row(f, "Microphone")
        from .audio import list_input_devices
        names = ["(system default)"] + [n for _, n in list_input_devices()]
        cur = self.cfg["preferred_mic"] or "(system default)"
        self.mic_var = tk.StringVar(value=cur)
        ttk.Combobox(r, textvariable=self.mic_var, width=38,
                     values=names).pack(side="left")

        ttk.Frame(f, height=10).pack()
        ttk.Label(f, text="FINE-TUNING", style="Section.TLabel").pack(anchor="w", pady=(4, 4))

        self.livepreview_var = tk.BooleanVar(value=self.cfg.get("live_preview", True))
        ttk.Checkbutton(f, text="Show words live while I speak",
                        variable=self.livepreview_var).pack(anchor="w", pady=2)
        self.start_cue_var = tk.BooleanVar(value=self.cfg["start_cue"])
        ttk.Checkbutton(f, text="Ready-cue when the mic is live (never miss the first word)",
                        variable=self.start_cue_var).pack(anchor="w", pady=2)
        self.end_cue_var = tk.BooleanVar(value=self.cfg["end_cue"])
        ttk.Checkbutton(f, text="Cue when dictation stops",
                        variable=self.end_cue_var).pack(anchor="w", pady=2)
        self.duck_var = tk.BooleanVar(value=self.cfg["duck_media"])
        ttk.Checkbutton(f, text="Lower other apps' audio while dictating",
                        variable=self.duck_var).pack(anchor="w", pady=2)
        self.local_cleanup_var = tk.BooleanVar(value=self.cfg["local_cleanup"])
        ttk.Checkbutton(f, text="Auto capitalization, spacing, and punctuation (offline)",
                        variable=self.local_cleanup_var).pack(anchor="w", pady=2)
        self.spoken_punct_var = tk.BooleanVar(value=self.cfg["spoken_punctuation"])
        ttk.Checkbutton(f, text='Spoken punctuation ("period", "comma", "new line")',
                        variable=self.spoken_punct_var).pack(anchor="w", pady=2)

        r = self._row(f, "Tail recording (ms)")
        self.tail_var = tk.IntVar(value=self.cfg["tail_ms"])
        ttk.Spinbox(r, from_=0, to=2000, increment=50,
                    textvariable=self.tail_var, width=8).pack(side="left")
        ttk.Label(f, style="Dim.TLabel",
                  text="Keeps recording briefly after stop so the last word isn't cut off."
                  ).pack(anchor="w")

    def _build_transcription(self, f):
        self._title(f, "Transcription",
                    "Turn videos and audio into text — one at a time or in bulk.")
        ttk.Label(f, style="Dim.TLabel", wraplength=460, text=(
            "Paste a URL (YouTube and most sites) or pick a file from this PC. "
            "Batch mode takes a whole list of URLs, transcribes them one by "
            "one, and auto-saves each as its video title in "
            "Documents\\EchoQuill Transcriptions.")).pack(anchor="w", pady=(0, 12))
        if self.on_media:
            ttk.Button(f, text="Open the transcriber", style="Accent.TButton",
                       command=self.on_media).pack(anchor="w")
        ttk.Label(f, style="Dim.TLabel", wraplength=460, text=(
            "\nTip: it's also one right-click away — right-click the mic pill "
            "→ Transcribe video / URL.")).pack(anchor="w")

        ttk.Label(f, style="Section.TLabel",
                  text="SIGN IN (YouTube bot-checks, Skool & member-only videos)"
                  ).pack(anchor="w", pady=(16, 4))
        ttk.Label(f, style="Dim.TLabel", wraplength=470, text=(
            "Some sites need you signed in (YouTube's bot check, Skool, private "
            "Vimeo). Install the \"Get cookies.txt LOCALLY\" extension and use "
            "its \"Export All Cookies\" - one file then covers EVERY site you're "
            "logged into (YouTube AND Skool AND the rest). Paste that whole file "
            "here, then Save. The top \"generated file, do not edit\" line is "
            "normal - leave it in; it's just the cookies.txt format.")).pack(anchor="w")
        self.cookie_box = theme.dark_text(f, wrap="none", height=6)
        self.cookie_box.pack(fill="x", pady=(4, 4))
        try:
            import os as _os
            _cfp = self.cfg.get("yt_cookies_file", "")
            if _cfp and _os.path.exists(_cfp):
                with open(_cfp, encoding="utf-8", errors="ignore") as _fh:
                    self.cookie_box.insert("1.0", _fh.read())
        except Exception:
            pass
        crow2 = ttk.Frame(f); crow2.pack(anchor="w")
        self.cookie_status = ttk.Label(crow2, text="", style="Dim.TLabel")

        def _save_cookies():
            import os as _os
            from . import config as _c
            txt = self.cookie_box.get("1.0", "end").strip()
            path = _os.path.join(str(cfgmod.app_data_dir()), "youtube_cookies.txt")
            if not txt:
                self.cookie_status.configure(text="Paste your cookies first"); return
            try:
                with open(path, "w", encoding="utf-8") as fh:
                    fh.write(txt + "\n")
                self.cfg["yt_cookies_file"] = path; _c.save(self.cfg)
                self.cookie_status.configure(text="Saved \u2713")
            except Exception as e:
                self.cookie_status.configure(text=f"Save failed: {e}")

        def _clear_cookies():
            from . import config as _c
            self.cookie_box.delete("1.0", "end")
            self.cfg["yt_cookies_file"] = ""; _c.save(self.cfg)
            self.cookie_status.configure(text="Cleared")
        ttk.Button(crow2, text="Save cookies", style="Accent.TButton",
                   command=_save_cookies).pack(side="left")
        ttk.Button(crow2, text="Clear", command=_clear_cookies).pack(side="left", padx=6)
        self.cookie_status.pack(side="left", padx=8)


    def _build_read_aloud(self, f):
        from . import helptip, player
        ttk.Label(f, text="Read aloud (Text-to-speech)",
                  style="Title.TLabel").pack(anchor="w")
        ttk.Label(f, style="Dim.TLabel", wraplength=560, text=(
            "Turn text into spoken audio.  1) Paste text below, or load a "
            "document.  2) Pick a voice.  3) Click \u201cConvert to audio.\u201d  "
            "Then play it, save an MP3, or send it to your phone. Uses your own "
            "ElevenLabs account (key kept in Windows Credential Manager)."
            )).pack(anchor="w", pady=(2, 8))

        frow = ttk.Frame(f); frow.pack(fill="x", pady=(0, 6))
        ttk.Label(frow, text="Save narrations to:").pack(side="left")
        ttk.Button(frow, text="Change\u2026",
                   command=self._ra_choose_folder).pack(side="right")
        self._ra_folder_ent = ttk.Entry(frow)
        self._ra_folder_ent.pack(side="left", fill="x", expand=True,
                                 padx=(8, 8), ipady=2)
        self._ra_set_folder_entry()

        self._ra_voice_id = self.cfg.get("tts_voice_id", "") or ""
        self._ra_voices = []
        self._ra_busy = False

        krow = ttk.Frame(f); krow.pack(fill="x", pady=(2, 2))
        ttk.Label(krow, text="ElevenLabs API key:").pack(side="left")
        self._ra_key = tk.StringVar(value=self.cfg.get("elevenlabs_api_key", ""))
        ttk.Entry(krow, textvariable=self._ra_key, show="\u2022").pack(
            side="left", fill="x", expand=True, padx=(8, 8), ipady=2)
        _ks = ttk.Button(krow, text="Save key", command=self._ra_save_key)
        _ks.pack(side="left")
        helptip.tip(_ks, "Store your ElevenLabs key (kept in Windows Credential "
                    "Manager) and load your voices.")

        vrow = ttk.Frame(f); vrow.pack(fill="x", pady=(6, 2))
        ttk.Label(vrow, text="Voice:").pack(side="left")
        self._ra_voice = tk.StringVar(value="(add key, then Load voices)")
        _lv = ttk.Button(vrow, text="Load voices", command=self._ra_load_voices)
        _lv.pack(side="right")
        helptip.tip(_lv, "Fetch the voices on your ElevenLabs account.")
        self._ra_menu = ttk.OptionMenu(vrow, self._ra_voice,
                                       "(add key, then Load voices)")
        self._ra_menu.pack(side="left", fill="x", expand=True, padx=(6, 8))

        drow = ttk.Frame(f); drow.pack(fill="x", pady=(8, 0))
        _od = ttk.Button(drow, text="\U0001f4c4 Load a document\u2026",
                         command=self._ra_open_doc)
        _od.pack(side="left")
        helptip.tip(_od, "Pull the text out of a .txt, .md, .docx or .pdf into "
                    "the box, so you can convert it to audio.")
        _conv = ttk.Button(drow, text="\U0001f399 Convert to audio",
                           style="Accent.TButton", command=self._ra_do_play)
        _conv.pack(side="left", fill="x", expand=True, padx=(8, 0))
        helptip.tip(_conv, "Turn the text into audio. Then use the player to "
                    "listen, or Save as MP3.")

        _trow = ttk.Frame(f); _trow.pack(fill="x", pady=(8, 0))
        ttk.Label(_trow, text="Text to convert to audio:").pack(side="left")
        self._ra_charlbl = ttk.Label(_trow, style="Dim.TLabel", text="0 characters")
        self._ra_charlbl.pack(side="right")
        self._ra_box = theme.dark_text(f, wrap="word", height=10)
        self._ra_box.pack(fill="both", expand=True, pady=(2, 6))
        self._ra_box.bind("<KeyRelease>", lambda e: (self._ra_count(), self._ra_player.invalidate()))

        prow = ttk.Frame(f); prow.pack(fill="x", pady=(0, 4))
        self._ra_player = player.AudioPlayer(prow, self.win)
        self._ra_player.pack(fill="x")
        helptip.tip(self._ra_player.play_btn, "Play/pause the converted audio. "
                    "Drag the bar to scrub; replays are free.")
        arow = ttk.Frame(f); arow.pack(fill="x", pady=(2, 4))
        _save = ttk.Button(arow, text="Save as MP3\u2026", command=self._ra_do_save)
        _save.pack(side="left")
        helptip.tip(_save, "Generate the audio and save it as an MP3 file.")
        _open = ttk.Button(arow, text="Open folder", command=self._ra_open_folder)
        _open.pack(side="left", padx=8)
        helptip.tip(_open, "Open your EchoQuill\\Narration folder.")
        _clear = ttk.Button(arow, text="Clear", command=self._ra_clear)
        _clear.pack(side="left")
        helptip.tip(_clear, "Clear the text box.")
        _phone = ttk.Button(arow, text="\U0001f4f1 Listen on my phone",
                            command=self._ra_listen_phone)
        _phone.pack(side="left", padx=(12, 0))
        helptip.tip(_phone, "Show a QR code to open your narrations on your "
                    "phone over WiFi - no accounts, no cloud.")
        self._ra_status = ttk.Label(arow, text="", style="Dim.TLabel")
        self._ra_status.pack(side="left", padx=12)

        if self.cfg.get("elevenlabs_api_key"):
            self._ra_load_voices()

    # ----- Read aloud handlers -----

    def _ra_set(self, msg):
        try:
            self.win.after(0, lambda: self._ra_status.configure(text=msg))
        except Exception:
            pass

    def _ra_error(self, where, e):
        from . import tts
        tts.log_error(where, e)
        msg = str(e)
        self._ra_set(msg)
        self.win.after(0, lambda: messagebox.showerror(
            "Read aloud", msg + "\n\n(Details saved to tts_error.log in your "
            "EchoQuill settings folder.)"))

    def _ra_open_folder(self):
        import os
        from .media_gui import narration_dir
        try:
            os.startfile(narration_dir(self.cfg))
        except Exception:
            self._ra_set("Could not open folder")

    def _ra_listen_phone(self):
        from . import phone_share
        phone_share.open_phone_window(self.win, self.cfg)

    def _ra_set_folder_entry(self):
        from .media_gui import narration_dir
        self._ra_folder_ent.configure(state="normal")
        self._ra_folder_ent.delete(0, "end")
        self._ra_folder_ent.insert(0, narration_dir(self.cfg))
        self._ra_folder_ent.configure(state="readonly")

    def _ra_choose_folder(self):
        from tkinter import filedialog
        d = filedialog.askdirectory(
            parent=self.win, title="Choose a folder to save narrations in "
            "(e.g. your OneDrive / Google Drive / Dropbox folder)")
        if not d:
            return
        self.cfg["narration_dir"] = d
        try:
            cfgmod.save(self.cfg)
        except Exception:
            pass
        self._ra_set_folder_entry()
        self._ra_set("Narrations now save to your chosen folder \u2713")

    def _ra_default_folder(self):
        self.cfg["narration_dir"] = ""
        try:
            cfgmod.save(self.cfg)
        except Exception:
            pass
        self._ra_set_folder_entry()
        self._ra_set("Back to the default Narration folder")

    def _ra_clear(self):
        self._ra_box.delete("1.0", "end")
        self._ra_status.configure(text="")
        self._ra_count()
        try:
            self._ra_player.invalidate()
        except Exception:
            pass

    def _ra_count(self):
        try:
            n = len(self._ra_box.get("1.0", "end").strip())
            self._ra_charlbl.configure(text=f"{n:,} characters")
        except Exception:
            pass

    def _ra_confirm_cost(self, n):
        if n <= 5000:
            return True
        return messagebox.askyesno(
            "Read aloud - heads up",
            f"This is {n:,} characters, which will use about {n:,} ElevenLabs "
            f"credits (ElevenLabs bills per character).\n\nGenerate anyway?",
            parent=self.win)

    def _ra_save_key(self):
        self.cfg["elevenlabs_api_key"] = self._ra_key.get().strip()
        try:
            cfgmod.save(self.cfg)
        except Exception:
            pass
        self._ra_set("Key saved \u2713")
        self._ra_load_voices()

    def _ra_open_doc(self):
        import threading
        from tkinter import filedialog
        from . import tts
        path = filedialog.askopenfilename(
            parent=self.win, title="Open a document to read",
            filetypes=[("Documents", "*.txt *.md *.docx *.pdf"),
                       ("All files", "*.*")])
        if not path:
            return
        self._ra_set("Reading document\u2026")

        def run():
            import os
            try:
                text = tts.read_document(path)
            except Exception as e:
                self._ra_set(str(e)); return

            def show():
                self._ra_box.delete("1.0", "end")
                self._ra_box.insert("1.0", text)
                self._ra_count()
                try:
                    self._ra_player.invalidate()
                except Exception:
                    pass
                self._ra_status.configure(text=f"Loaded {os.path.basename(path)} \u2713")
            self.win.after(0, show)
        threading.Thread(target=run, daemon=True).start()

    def _ra_load_voices(self):
        import threading
        from . import tts
        self.cfg["elevenlabs_api_key"] = self._ra_key.get().strip()
        if not self.cfg["elevenlabs_api_key"]:
            self._ra_set("Add your ElevenLabs API key first."); return
        self._ra_set("Loading voices\u2026")

        def run():
            try:
                voices = tts.list_voices(self.cfg)
            except Exception as e:
                self._ra_set(str(e)); return
            self.win.after(0, lambda: self._ra_fill_voices(voices))
        threading.Thread(target=run, daemon=True).start()

    def _ra_fill_voices(self, voices):
        self._ra_voices = voices
        menu = self._ra_menu["menu"]
        menu.delete(0, "end")
        if not voices:
            self._ra_voice.set("(no voices found)")
            self._ra_set("No voices on this account."); return
        for name, vid in voices:
            menu.add_command(label=name,
                             command=lambda n=name, i=vid: self._ra_pick(n, i))
        cur = next((n for n, i in voices if i == self._ra_voice_id), None)
        if cur:
            self._ra_voice.set(cur)
        else:
            self._ra_pick(voices[0][0], voices[0][1])
        self._ra_set(f"Loaded {len(voices)} voice"
                     f"{'s' if len(voices) != 1 else ''} \u2713")

    def _ra_pick(self, name, vid):
        self._ra_voice.set(name)
        self._ra_voice_id = vid
        self.cfg["tts_voice_id"] = vid

    def _ra_guard(self):
        if self._ra_busy:
            self._ra_set("Still working on the last one\u2026"); return False
        if not self._ra_key.get().strip():
            self._ra_set("Add your ElevenLabs API key first."); return False
        text = self._ra_box.get("1.0", "end").strip()
        if not text:
            self._ra_set("Nothing to read - paste or open some text."); return False
        if not self._ra_confirm_cost(len(text)):
            self._ra_set("Cancelled."); return False
        self.cfg["elevenlabs_api_key"] = self._ra_key.get().strip()
        return True

    def _ra_do_play(self):
        import threading, os, tempfile
        from . import tts
        if not self._ra_guard():
            return
        text = self._ra_box.get("1.0", "end").strip()
        self._ra_busy = True
        self._ra_set("Generating audio\u2026")

        def run():
            try:
                pcm = tts.synth_pcm(text, self.cfg, self._ra_voice_id,
                                    status_cb=self._ra_set)
                fd, wav = tempfile.mkstemp(prefix="eq_ras_", suffix=".wav")
                os.close(fd)
                tts.pcm_to_wav(pcm, wav)

                def go():
                    self._ra_player.load_and_play(wav)
                    self._ra_set("Playing \u25b6")
                self.win.after(0, go)
            except Exception as e:
                self._ra_error("play", e)
            finally:
                self._ra_busy = False
        threading.Thread(target=run, daemon=True).start()

    def _ra_do_save(self):
        import threading, os
        from tkinter import filedialog
        from . import tts
        from .media_gui import narration_dir
        if not self._ra_guard():
            return
        text = self._ra_box.get("1.0", "end").strip()
        path = filedialog.asksaveasfilename(
            parent=self.win, title="Save narration as MP3",
            initialdir=narration_dir(self.cfg), defaultextension=".mp3",
            filetypes=[("MP3 audio", "*.mp3")])
        if not path:
            return
        self._ra_busy = True
        self._ra_set("Generating audio\u2026")

        def run():
            try:
                tts.synthesize_to_mp3(text, self.cfg, self._ra_voice_id, path,
                                      status_cb=self._ra_set)
                self._ra_set(f"Saved \u2713  {os.path.basename(path)}")
            except Exception as e:
                self._ra_error("save", e)
            finally:
                self._ra_busy = False
        threading.Thread(target=run, daemon=True).start()

    def _build_whatsnew(self, f):
        from . import changelog
        hdr = ttk.Frame(f); hdr.pack(fill="x")
        ttk.Label(hdr, text="What\u2019s New", style="Title.TLabel").pack(side="left")
        ttk.Label(hdr, style="Dim.TLabel", text=(
            f"Free \u2014 {getattr(changelog, 'FREE_COUNT', 0)} updates   \u00b7   "
            f"Pro \u2014 {getattr(changelog, 'PRO_COUNT', 0)} updates")
            ).pack(side="right")
        ttk.Label(f, style="Dim.TLabel", wraplength=560, text=(
            "Every update to EchoQuill, newest first \u2014 Pro and Free."
            )).pack(anchor="w", pady=(2, 8))
        box = theme.dark_text(f, wrap="word")
        box.pack(fill="both", expand=True, pady=(2, 6))
        box.insert("1.0", changelog.TEXT)
        box.configure(state="disabled")

    def _build_clipboard(self, f):
        self._title(f, "Clipboard",
                    "Your recent transcriptions, always within reach.")
        ttk.Label(f, style="Dim.TLabel", wraplength=460, text=(
            "Every transcription is kept on the clipboard automatically, and "
            "the Clips tray shows your 10 most recent — drag it anywhere on "
            "screen, click a clip to copy it, drag a clip into another app, "
            "or delete one with its ✕.")).pack(anchor="w", pady=(0, 12))
        if self.on_clips:
            ttk.Button(f, text="Open the clips tray", style="Accent.TButton",
                       command=self.on_clips).pack(anchor="w")
        if self.on_history:
            ttk.Button(f, text="Browse all recent transcriptions…",
                       command=self.on_history).pack(anchor="w", pady=8)
        ttk.Label(f, style="Dim.TLabel", wraplength=460, text=(
            "Tip: both are also on the mic pill's right-click menu.")).pack(anchor="w")

    def _build_stats(self, f):
        self._title(f, "Stats", "How much talking has replaced typing.")
        stats = historymod.period_stats()
        grid = ttk.Frame(f)
        grid.pack(anchor="w", pady=6)
        headers = ["", "Words", "Dictations", "Time saved vs typing"]
        for c, htext in enumerate(headers):
            ttk.Label(grid, text=htext, style="Section.TLabel",
                      width=18 if c == 0 else 14).grid(row=0, column=c, sticky="w", pady=(0, 6))
        for r, (period, v) in enumerate(stats.items(), start=1):
            ttk.Label(grid, text=period, font=("Segoe UI Semibold", 10)
                      ).grid(row=r, column=0, sticky="w", pady=3)
            ttk.Label(grid, text=f"{v['words']:,}").grid(row=r, column=1, sticky="w")
            ttk.Label(grid, text=f"{v['dictations']:,}").grid(row=r, column=2, sticky="w")
            ttk.Label(grid, text=f"~{v['minutes_saved']} min").grid(row=r, column=3, sticky="w")
        ttk.Label(f, style="Dim.TLabel", wraplength=460, text=(
            "\nBased on ~40 words/min typing vs ~150 words/min speaking. "
            "All stats live only on this computer.")).pack(anchor="w")

    def _build_dictionary(self, f):
        self._title(f, "Dictionary",
                    "Words and phrases EchoQuill should always get right — "
                    "names, jargon, brands.")
        self.dict_enabled_var = tk.BooleanVar(value=self.cfg["dictionary_enabled"])
        ttk.Checkbutton(f, text="Enable dictionary replacements",
                        variable=self.dict_enabled_var).pack(anchor="w")
        self.learn_var = tk.BooleanVar(value=self.cfg["learn_corrections"])
        ttk.Checkbutton(f, text="Learn from my corrections automatically",
                        variable=self.learn_var).pack(anchor="w", pady=(2, 8))

        self.dict_list = theme.dark_listbox(f, height=11)
        self.dict_list.pack(fill="both", expand=True)
        self._refresh_dict()

        bar = ttk.Frame(f)
        bar.pack(pady=8)
        ttk.Button(bar, text="Add…", command=self._dict_add).pack(side="left", padx=4)
        ttk.Button(bar, text="Edit…", command=self._dict_edit).pack(side="left", padx=4)
        ttk.Button(bar, text="Remove selected",
                   command=self._dict_remove).pack(side="left", padx=4)

    def _build_ai(self, f):
        self._title(f, "AI Enhancement",
                    "Optional and off by default. Smarter cleanup and per-app tone "
                    "via any OpenAI-compatible service — or a free local LLM "
                    "(Ollama, LM Studio) so nothing leaves your PC.")
        self.ai_var = tk.BooleanVar(value=self.cfg["ai_enhancement"])
        ttk.Checkbutton(f, text="Enable AI enhancement (connect a provider below)",
                        variable=self.ai_var).pack(anchor="w", pady=(0, 2))
        self.ai_dictation_var = tk.BooleanVar(value=self.cfg.get("ai_on_dictation", False))
        ttk.Checkbutton(f, variable=self.ai_dictation_var,
                        text="Format dictation with AI (off = instant plain text)"
                        ).pack(anchor="w", pady=(0, 8))

        r = self._row(f, "Provider")
        providers = sorted(cfgmod.AI_PROVIDERS.keys())
        self.ai_provider_var = tk.StringVar(
            value=self.cfg.get("ai_provider", "OpenAI"))
        pv = ttk.Combobox(r, textvariable=self.ai_provider_var, width=42,
                          state="readonly", values=providers)
        pv.pack(side="left")
        self.ai_hint = ttk.Label(f, style="Dim.TLabel", wraplength=460)
        self.ai_hint.pack(anchor="w")

        r = self._row(f, "Model")
        self.ai_model_var = tk.StringVar(value=self.cfg["ai_model"])
        self.ai_model_box = ttk.Combobox(r, textvariable=self.ai_model_var,
                                         width=42)   # editable: type any model
        self.ai_model_box.pack(side="left")

        r = self._row(f, "Sign-in method")
        self.ai_auth_var = tk.StringVar(
            value=self.cfg.get("ai_auth_method", "api_key"))
        auth_box = ttk.Combobox(r, textvariable=self.ai_auth_var, width=42,
                                state="readonly",
                                values=["api_key", "oauth"])
        auth_box.pack(side="left")
        ttk.Label(f, style="Dim.TLabel", wraplength=460, text=(
            "api_key: paste a key from the provider · oauth: sign in with your "
            "account in the browser (needs a Client ID from the provider's "
            "developer program — apply once, then it's one click for everyone)."
            )).pack(anchor="w")

        r = self._row(f, "API key")
        self.ai_key_var = tk.StringVar(value=self.cfg["ai_api_key"])
        ttk.Entry(r, textvariable=self.ai_key_var, width=44, show="•").pack(side="left")

        self.ai_client_var = tk.StringVar(
            value=self.cfg.get("ai_oauth_client_id", ""))
        self._oauth_box = ttk.Frame(f)
        oc = self._row(self._oauth_box, "OAuth Client ID")
        ttk.Entry(oc, textvariable=self.ai_client_var, width=44).pack(side="left")
        ob = self._row(self._oauth_box, "")
        self.oauth_btn = ttk.Button(ob, text="Sign in with your account…",
                                    command=self._oauth_sign_in)
        self.oauth_btn.pack(side="left")
        self.oauth_status = ttk.Label(ob, text="", style="Dim.TLabel")
        self.oauth_status.pack(side="left", padx=10)
        if (self.cfg.get("ai_oauth_tokens") or {}).get("access_token"):
            self.oauth_status.configure(text="Signed in ✓")
        def _toggle_oauth(*_):
            if self.ai_auth_var.get() == "oauth":
                self._oauth_box.pack(fill="x", anchor="w")
            else:
                self._oauth_box.pack_forget()
        _toggle_oauth()
        auth_box.bind("<<ComboboxSelected>>", _toggle_oauth)

        r = self._row(f, "API base URL")
        self.ai_url_var = tk.StringVar(value=self.cfg["ai_base_url"])
        ttk.Entry(r, textvariable=self.ai_url_var, width=44).pack(side="left")

        def _provider_changed(_e=None, first=False):
            info = cfgmod.AI_PROVIDERS.get(self.ai_provider_var.get(), {})
            self.ai_model_box.configure(values=info.get("models", []))
            hint = info.get("key_hint", "")
            if info.get("oauth_auth_url"):
                hint += "  (supports OAuth sign-in)"
            self.ai_hint.configure(text=hint)
            if not first:   # user actively switched: fill in the defaults
                if info.get("base_url"):
                    self.ai_url_var.set(info["base_url"])
                if info.get("default_model"):
                    self.ai_model_var.set(info["default_model"])
                self.cfg["ai_oauth_auth_url"] = info.get("oauth_auth_url", "")
                self.cfg["ai_oauth_token_url"] = info.get("oauth_token_url", "")
        _provider_changed(first=True)
        pv.bind("<<ComboboxSelected>>", _provider_changed)

        ttk.Label(f, text="PER-APP TONE", style="Section.TLabel"
                  ).pack(anchor="w", pady=(12, 4))
        ttk.Label(f, style="Dim.TLabel", wraplength=460, text=(
            "Different apps, different voice: casual in Slack, formal in "
            "Outlook. Add the program name and the extra instruction."
            )).pack(anchor="w")
        self.tone_list = theme.dark_listbox(f, height=4)
        self.tone_list.pack(fill="x", pady=4)
        self._refresh_tones()
        tr = ttk.Frame(f); tr.pack(fill="x", pady=(2, 2))
        self.tone_app_var = tk.StringVar()
        self.tone_prompt_var = tk.StringVar()
        ttk.Entry(tr, textvariable=self.tone_app_var, width=16).pack(side="left")
        ttk.Entry(tr, textvariable=self.tone_prompt_var, width=34).pack(side="left", padx=6, fill="x", expand=True)
        ttk.Button(tr, text="Add", command=self._tone_add).pack(side="left")
        ttk.Label(f, style="Dim.TLabel",
                  text="app (slack.exe)          instruction (Casual tone, lowercase ok)"
                  ).pack(anchor="w")
        ttk.Button(f, text="Remove selected", command=self._tone_remove).pack(anchor="w", pady=(4, 6))

        ttk.Label(f, text="CLEANUP INSTRUCTIONS", style="Section.TLabel"
                  ).pack(anchor="w", pady=(12, 4))
        self.ai_prompt_text = theme.dark_text(f, height=5, wrap="word")
        self.ai_prompt_text.insert("1.0", self.cfg["ai_prompt"])
        self.ai_prompt_text.pack(fill="x")

    def _build_history(self, f):
        self._title(f, "History",
                    "Stored only on this computer. Free shows the last 10 — "
                    "Pro keeps an unlimited library with Favorites.")
        s = historymod.today_stats()
        ttk.Label(f, font=("Segoe UI Semibold", 12), text=(
            f"Today: {s['words']} words · {s['dictations']} dictations · "
            f"~{s['minutes_saved']} min saved vs typing")).pack(anchor="w", pady=(0, 8))
        self.hist_text = theme.dark_text(f, height=14, wrap="word")
        self.hist_text.pack(fill="both", expand=True)
        for e in historymod.entries(limit=10):
            self.hist_text.insert("end", f"[{e.get('date','')}]  {e.get('text','')}\n\n")
        self.hist_text.configure(state="disabled")
        hb = ttk.Frame(f); hb.pack(pady=8)
        ttk.Button(hb, text="Export everything (zip)…",
                   command=self._export_all).pack(side="left", padx=4)
        ttk.Button(hb, text="Clear history", command=self._clear_history).pack(side="left", padx=4)

        ttk.Label(f, text="AUDIO HISTORY", style="Section.TLabel").pack(anchor="w", pady=(14, 4))
        from . import audio_store
        self.keep_audio_var = tk.BooleanVar(value=self.cfg.get("keep_audio", False))
        ttk.Checkbutton(f, variable=self.keep_audio_var, text=(
            "Keep a recording of each dictation on this PC (off = save nothing)"
            )).pack(anchor="w")
        r = ttk.Frame(f); r.pack(anchor="w", pady=4)
        ttk.Label(r, text="Storage budget (MB):").pack(side="left")
        self.audio_mb_var = tk.IntVar(value=self.cfg.get("audio_max_mb", 500))
        ttk.Spinbox(r, from_=50, to=20000, increment=50, width=8,
                    textvariable=self.audio_mb_var).pack(side="left", padx=6)
        ttk.Label(f, style="Dim.TLabel",
                  text=f"Using {audio_store.usage_mb()} MB across {audio_store.count()} clips. "
                       "Oldest are removed first when over budget.").pack(anchor="w")
        ab = ttk.Frame(f); ab.pack(pady=6)
        ttk.Button(ab, text="Open audio folder",
                   command=lambda: __import__('os').startfile(str(audio_store.AUDIO_DIR))
                   ).pack(side="left", padx=4)
        ttk.Button(ab, text="Export audio (zip)…",
                   command=self._export_audio).pack(side="left", padx=4)
        ttk.Button(ab, text="Delete all audio",
                   command=self._clear_audio).pack(side="left", padx=4)

    HELP_TOPICS = {
        "Dictation": (
            "HOW TO DICTATE\n\n"
            "1. Click into any text field (email, Word, chat - anywhere).\n"
            "2. Press Ctrl+Alt+Space (or click the blue mic pill).\n"
            "3. Talk naturally. Your words appear live in the pill.\n"
            "4. Press Ctrl+Alt+Space again. The text lands at your cursor.\n\n"
            "TIPS\n"
            "• Say \"period\", \"comma\", \"new line\", \"new paragraph\" for punctuation.\n"
            "• Changed your mind mid-dictation? Press ESC to cancel - nothing is typed.\n"
            "• Prefer holding a key? Settings → General → Activation → hold, then hold Right Alt while talking.\n"
            "• Wrong word repeatedly? Add it in the Dictionary tab - EchoQuill also learns from repeated corrections.\n"
            "• Every transcription is kept on the clipboard too: Ctrl+V pastes it anywhere.\n\n"
            "AVOID\n"
            "• Talking before the ready-beep - wait for the cue.\n"
            "• The \"Maximum accuracy\" model for live dictation - it lags. Use Balanced."),
        "Voice commands": (
            "CONTROL YOUR PC BY VOICE\n\n"
            "1. Press Ctrl+Alt+C (or right-click the mic pill → Voice command).\n"
            "2. Say ONE command.\n"
            "3. Pause - it runs automatically. No second keypress needed.\n\n"
            "THE EASIEST WAY\n"
            "Just dictate normally (Ctrl+Alt+Space) and START with the word "
            "\"computer\":\n"
            "\"computer, open chrome\" · \"computer, volume up\"\n"
            "EchoQuill runs it as a command instead of typing it.\n\n"
            "THINGS YOU CAN SAY\n"
            "• \"open chrome\" / \"open word\" / \"open notepad\" / \"open calculator\"\n"
            "• \"search for houses in dallas\" - opens a web search\n"
            "• \"go to zillow.com\" - opens a website\n"
            "• \"press enter\" · \"select all\" · \"copy\" · \"paste\" · \"undo\" · \"save\"\n"
            "• \"new tab\" · \"close tab\" · \"refresh\" · \"switch window\"\n"
            "• \"volume up\" · \"volume down\" · \"mute\" · \"play\" · \"pause\"\n"
            "• \"minimize window\" · \"show desktop\" · \"take a screenshot\"\n"
            "• \"lock the computer\"\n\n"
            "SAFETY: only these known actions can run. Anything else is shown back to you, never executed."),
        "Transcribe videos": (
            "TURN ANY VIDEO OR AUDIO INTO TEXT\n\n"
            "1. Right-click the mic pill → Transcribe video / URL (or Settings → Transcription).\n"
            "2. Paste a video URL (YouTube and most sites) OR choose a file on your PC.\n"
            "3. The transcript appears in the window AND is saved automatically to\n"
            "   Documents\\EchoQuill Transcriptions, named after the video's title.\n\n"
            "BATCH MODE\n"
            "Click \"Batch: many URLs\", paste a list (one per line), press Start.\n"
            "Each video is transcribed in order and auto-saved. Walk away; it logs progress.\n\n"
            "FIND SOMETHING\n"
            "Type in \"Find in transcript\" to highlight every place a word appears.\n\n"
            "WHAT SOURCES WORK?\n"
            "About 1,800 sites are supported. The big ones:\n"
            "• YouTube (including Shorts and long videos)\n"
            "• TikTok\n"
            "• Instagram (Reels & posts)\n"
            "• Facebook\n"
            "• X / Twitter\n"
            "Also Vimeo, Twitch, Rumble, SoundCloud, most podcast and news sites.\n"
            "Full list: github.com/yt-dlp/yt-dlp/blob/master/supported_sites.md\n"
            "Plus ANY video/audio file already on your PC (mp4, mp3, mov, wav…).\n\n"
            "Every transcript starts with the video's title and URL, so you always "
            "know what it came from.\n\n"
            "Long videos take a while - a 1-hour video can take several minutes."),
        "Rewrite by voice": (
            "EDIT EXISTING TEXT WITH YOUR VOICE (WRITE MODE)\n\n"
            "1. Highlight text in any app - a sentence, a paragraph.\n"
            "2. Press Ctrl+Alt+W.\n"
            "3. Speak an instruction: \"make this more professional\",\n"
            "   \"shorten this\", \"fix the grammar\", \"turn this into bullet points\".\n"
            "4. Your selection is replaced with the rewritten version.\n\n"
            "It applies automatically when you pause - no second keypress.\n\n"
            "Works WITHOUT AI: whatever you say replaces the selected text.\n"
            "With AI Enhancement on (Settings → AI Enhancement), your instruction "
            "REWRITES the selection instead (\"make this more professional\")."),
        "Clips & clipboard": (
            "YOUR RECENT TRANSCRIPTIONS, ALWAYS HANDY\n\n"
            "• Right-click the mic pill → Clips tray: your 10 most recent dictations.\n"
            "• CLICK a clip - it pastes straight into wherever your cursor is.\n"
            "• Drag the tray by its header to park it anywhere.\n"
            "• Search box: type a word to highlight the clips containing it.\n"
            "• ✕ deletes a clip; Settings → History clears everything.\n"
            "• Every dictation is also on the Windows clipboard: Ctrl+V works immediately.\n"
            "• RECENT TRANSCRIPTIONS (Settings → History) works the same way: DRAG a "
            "line onto any text box to drop it, or CLICK to paste into your last app."),
        "Meeting / Record": (
            "RECORD & TRANSCRIBE WHAT YOU HEAR\n\n"
            "1. Settings → Meeting, or right-click the mic pill → Meeting / Record.\n"
            "2. (Optional) tick 'record my microphone' for two-way calls, and/or "
            "'capture the screen' to also save an MP4 video.\n"
            "3. Name it, click Start recording. Play your call / webinar / video.\n"
            "4. Click Stop & transcribe - it runs locally, no link or URL needed.\n\n"
            "Great for Skool, Zoom, Teams, webinars, or any playing video.\n"
            "Everything saves to Documents\\EchoQuill\\Meetings."),
        "Read aloud & phone": (
            "TURN TEXT INTO SPOKEN AUDIO (TEXT-TO-SPEECH)\n\n"
            "1. Settings → Read aloud, or right-click the mic pill → Read aloud.\n"
            "2. Paste text, or click 'Load a document' (.txt/.md/.docx/.pdf).\n"
            "3. Add your ElevenLabs API key once (Save key → Load voices) and pick "
            "a voice.\n"
            "4. Click 'Convert to audio'. Then Play/pause/scrub on the timeline, or "
            "'Save as MP3'. Audio is generated once - replays are free.\n\n"
            "SAVE ANYWHERE: 'Save narrations to...' can point at a OneDrive / Google "
            "Drive / Dropbox folder so files sync automatically.\n\n"
            "LISTEN ON YOUR PHONE: click 'Listen on my phone' for a QR code. On a "
            "phone on the SAME WiFi, scan it to open a page of your narrations - tap "
            "to play or download. No accounts, no cloud; it stays on your network."),
    }

    def _build_help(self, f):
        self._title(f, "Help", "Click a topic. Two minutes each, and you know the whole app.")
        btns = ttk.Frame(f)
        btns.pack(anchor="w", pady=(0, 10))
        self.help_text = theme.dark_text(f, wrap="word", height=18)
        self.help_text.pack(fill="both", expand=True)

        def show(topic):
            body = self.HELP_TOPICS[topic]
            if topic == "Voice commands":
                from . import commands as _c
                apps = ", ".join(sorted(set(_c.APP_ALIASES.keys())))
                acts = " · ".join(sorted(_c.KEY_COMMANDS.keys()))
                body += ("\n\nCOMPLETE LIST (generated from the app itself, always current)\n\n"
                         f"Apps you can open:\n{apps}\n\n"
                         f"Actions:\n{acts} · lock the computer")
            self.help_text.configure(state="normal")
            self.help_text.delete("1.0", "end")
            self.help_text.insert("1.0", body)
            self.help_text.configure(state="disabled")
        for i, topic in enumerate(self.HELP_TOPICS):
            ttk.Button(btns, text=topic,
                       command=lambda t=topic: show(t)).grid(
                row=i // 3, column=i % 3, padx=4, pady=4, sticky="w")
        show("Dictation")

    FEEDBACK_URL = "https://formspree.io/f/mrewjrjr"

    def _build_feedback(self, f):
        self._title(f, "Feedback",
                    "Idea? Problem? Tell us — this goes straight to the developer.")
        ttk.Label(f, text="Your message").pack(anchor="w")
        self.fb_text = theme.dark_text(f, height=8, wrap="word")
        self.fb_text.pack(fill="x", pady=(4, 10))
        r = ttk.Frame(f); r.pack(fill="x")
        ttk.Label(r, text="Your email (optional, for a reply):").pack(side="left")
        self.fb_email = tk.StringVar()
        ttk.Entry(r, textvariable=self.fb_email, width=32).pack(side="left", padx=8)
        r2 = ttk.Frame(f); r2.pack(anchor="w", pady=10)
        ttk.Button(r2, text="Send feedback", style="Accent.TButton",
                   command=self._send_feedback).pack(side="left")
        self.fb_status = ttk.Label(r2, text="", style="Dim.TLabel")
        self.fb_status.pack(side="left", padx=10)
        ttk.Label(f, style="Dim.TLabel", wraplength=460, text=(
            "Nothing else is sent — just what you type here. Developers can "
            "also open an issue on GitHub (Help → About → GitHub).")).pack(anchor="w")

    def _send_feedback(self):
        import threading
        msg = self.fb_text.get("1.0", "end").strip()
        if not msg:
            self.fb_status.configure(text="Write something first :)")
            return

        def run():
            def status(t):
                self.win.after(0, lambda: self.fb_status.configure(text=t))
            try:
                import requests
                from . import __version__
                status("Sending…")
                r = requests.post(self.FEEDBACK_URL, data={
                    "message": msg,
                    "email": self.fb_email.get().strip(),
                    "_subject": f"EchoQuill feedback (v{__version__})",
                }, headers={"Accept": "application/json"}, timeout=15)
                r.raise_for_status()
                status("Sent — thank you! 💙")
                self.win.after(0, lambda: self.fb_text.delete("1.0", "end"))
            except Exception:
                status("Couldn't send — check your internet and try again.")
        threading.Thread(target=run, daemon=True).start()

    def _build_about(self, f):
        from . import __version__
        self._title(f, "About")
        ttk.Label(f, text=f"EchoQuill v{__version__}",
                  font=("Segoe UI Semibold", 12)).pack(anchor="w")
        ub = ttk.Frame(f); ub.pack(anchor="w", pady=8)
        ttk.Button(ub, text="Check for updates", style="Accent.TButton",
                   command=self._check_updates).pack(side="left")
        self.update_status = ttk.Label(ub, text="", style="Dim.TLabel")
        self.update_status.pack(side="left", padx=10)
        ttk.Label(f, style="Dim.TLabel", wraplength=460, justify="left", text=(
            "\nFree, open-source, local-first dictation for Windows.\n\n"
            "Your voice never leaves this computer unless you enable a cloud "
            "AI provider yourself.\n\n"
            "Speech engine: OpenAI Whisper via faster-whisper.\n"
            "Inspired by FluidVoice for macOS (independent project, "
            "not affiliated).\n\nLicense: MIT — free forever."
        )).pack(anchor="w")

    # ---------- update banner ----------

    def _start_update_autocheck(self):
        """Check for a newer version in the background; show an in-app banner."""
        import threading

        def run():
            try:
                from . import update
                found = update.check()
            except Exception:
                found = None
            if found:
                ver, url = found
                try:
                    self.win.after(0, lambda: self._show_update_banner(ver, url))
                except Exception:
                    pass
        threading.Thread(target=run, daemon=True).start()

    def _show_update_banner(self, ver, url=None):
        if not (hasattr(self, "_update_banner") and self._update_banner.winfo_exists()):
            return
        for w in self._update_banner.winfo_children():
            w.destroy()
        self._banner_msg = tk.Label(
            self._update_banner, text=f"  \u2b06  Update available \u2014 v{ver}",
            bg="#30d158", fg="#00330f", font=("Segoe UI Semibold", 10), pady=8)
        self._banner_msg.pack(side="left", padx=(12, 0))
        tk.Button(self._update_banner, text="Install now",
                  bg="#00330f", fg="#eaffef", activebackground="#004d17",
                  activeforeground="#ffffff", relief="flat", cursor="hand2",
                  font=("Segoe UI Semibold", 9), padx=14, pady=3,
                  command=lambda: self._do_update(url)).pack(side="right", padx=12, pady=6)
        dismiss = tk.Label(self._update_banner, text="Later", bg="#30d158",
                           fg="#00330f", cursor="hand2", font=("Segoe UI", 9))
        dismiss.pack(side="right", padx=(0, 4))
        dismiss.bind("<Button-1>", lambda e: self._update_banner.pack_forget())
        try:
            self._update_banner.pack(side="top", fill="x", before=self.content)
        except Exception:
            self._update_banner.pack(side="top", fill="x")

    def _do_update(self, url):
        import threading

        def msg(text):
            try:
                self.win.after(0, lambda: self._banner_msg.configure(
                    text=f"  \u2b06  {text}"))
            except Exception:
                pass

        def run():
            try:
                from . import update
                u = url
                if not u:
                    found = update.check()
                    if not found:
                        msg("You're on the latest version")
                        return
                    _v, u = found
                msg("Downloading update\u2026")
                update.download_and_run(u, msg)
                msg("Installer launched \u2014 EchoQuill will close\u2026")
                if self.on_quit:
                    self.win.after(250, self.on_quit)
            except Exception as e:
                msg(f"Update failed: {e}")
        threading.Thread(target=run, daemon=True).start()

    def _build_meeting(self, f):
        from . import meeting, helptip
        _trow = ttk.Frame(f); _trow.pack(fill="x", anchor="w")
        ttk.Label(_trow, text="Meeting / Record", style="Title.TLabel").pack(side="left")
        helptip.attach(self.win, _trow, "Meeting / Record - help",
                       "Record what you HEAR on this PC - calls, webinars, any "
                       "playing video (incl. Skool) - plus your mic and/or the "
                       "full screen as MP4, then transcribe and Ask AI, all "
                       "locally.\n\n1) Tick mic/screen if you want them.\n"
                       "2) Name it.\n3) Start, then Stop & transcribe.").pack(side="left", padx=8)
        ttk.Label(f, style="Dim.TLabel", wraplength=640, text=(
            "Record what you HEAR on this PC (calls, webinars, any playing "
            "video - including Skool) and transcribe it locally. No link, no "
            "URL, no DevTools.")).pack(anchor="w")
        ttk.Frame(f, height=10).pack()

        _pro = True
        try:
            from . import license as _lic
            _pro = _lic.is_pro(self.cfg)
        except Exception:
            _pro = False
        if not _pro:
            ttk.Label(f, style="Dim.TLabel", wraplength=470, text=(
                "Meeting / Record is a Pro feature. Record calls, webinars and "
                "any playing video \u2014 audio only, or the full screen as "
                "video \u2014 then transcribe and summarize it, all locally.")
                ).pack(anchor="w", pady=(0, 12))
            ttk.Button(f, text="\u2b50 Upgrade to Pro", style="Accent.TButton",
                       command=self._meeting_upgrade).pack(anchor="w")
            return

        if not meeting.available():
            ttk.Label(f, style="Dim.TLabel", wraplength=470, text=(
                "System-audio capture isn't available in this build. "
                "Reinstall the latest EchoQuill to enable it.")).pack(anchor="w")
            return

        self._mt_mic = tk.BooleanVar(value=False)
        _cm = ttk.Checkbutton(f, text="Also record my microphone (for two-way calls)",
                              variable=self._mt_mic)
        _cm.pack(anchor="w", pady=(0, 4))
        helptip.tip(_cm, "Mix in your microphone so both sides of a call are captured.")
        self._mt_video = tk.BooleanVar(value=False)
        _cs = ttk.Checkbutton(
            f, text="Also capture the screen (save an MP4 video + transcribe)",
            variable=self._mt_video)
        _cs.pack(anchor="w", pady=(0, 6))
        helptip.tip(_cs, "Also record the whole screen to an MP4 next to the transcript.")

        nrow = ttk.Frame(f); nrow.pack(fill="x", pady=(0, 6))
        ttk.Label(nrow, text="Name this meeting / recording (required):").pack(side="left")
        self._mt_name = tk.StringVar()
        _ne = ttk.Entry(nrow, textvariable=self._mt_name)
        _ne.pack(side="left", fill="x", expand=True, padx=(8, 0), ipady=2)
        helptip.tip(_ne, "Everything saves under this name in your Meetings folder. "
                         "Required before you can start.")
        self._mt_nameentry = _ne

        crow = ttk.Frame(f); crow.pack(anchor="w", pady=(2, 6))
        self._mt_start = ttk.Button(crow, text="\u25cf  Start recording",
                                    style="Accent.TButton", command=self._meeting_start)
        self._mt_start.pack(side="left")
        helptip.tip(self._mt_start, "Start capturing system audio (plus mic/screen if ticked).")
        self._mt_stop = ttk.Button(crow, text="\u25a0  Stop & transcribe",
                                   command=self._meeting_stop, state="disabled")
        self._mt_stop.pack(side="left", padx=8)
        helptip.tip(self._mt_stop, "Stop and transcribe locally.")
        self._mt_status = ttk.Label(crow, text="", style="Dim.TLabel")
        self._mt_status.pack(side="left", padx=10)

        from . import prompts as _pr
        ttk.Label(f, text="Ask AI:").pack(anchor="w")
        prow = ttk.Frame(f); prow.pack(fill="x", pady=(2, 0))
        ttk.Label(prow, text="Presets:").pack(side="left")
        self._mt_preset = tk.StringVar(value="Presets \u25be")
        self._mt_presetmenu = ttk.OptionMenu(
            prow, self._mt_preset, "Presets \u25be", *_pr.menu_items(self.cfg),
            command=self._mt_preset_pick)
        self._mt_presetmenu.configure(width=18)
        self._mt_presetmenu.pack(side="left", padx=(6, 0))
        self._refresh_preset_menu()                      # truncate long items
        helptip.menu_hover(self._mt_presetmenu["menu"],
                           lambda: _pr.menu_items(self.cfg))
        helptip.tip(self._mt_presetmenu, "Pick a ready-made question, or the "
                    "bottom item to add / edit your own.")
        qrow = ttk.Frame(f); qrow.pack(fill="x", pady=(4, 4))
        _ab = ttk.Button(qrow, text="Ask", style="Accent.TButton",
                         command=self._meeting_ask)
        _ab.pack(side="right", padx=(8, 0))
        helptip.tip(_ab, "Ask anything about this recording - pick a preset or type your own question.")
        self._mt_qbox = tk.Text(qrow, height=2, wrap="word", bg=theme.FIELD,
                                fg=theme.FG, insertbackground=theme.FG,
                                borderwidth=1, relief="solid",
                                font=("Segoe UI", 10), padx=6, pady=4)
        self._mt_qbox.pack(side="left", fill="x", expand=True)
        self._mt_qbox.bind("<Return>", lambda e: (self._meeting_ask(), "break")[1])

        arow = ttk.Frame(f); arow.pack(anchor="w", pady=(0, 6))
        _b2 = ttk.Button(arow, text="Copy", command=self._meeting_copy)
        _b2.pack(side="left", padx=6)
        helptip.tip(_b2, "Copy the transcript to the clipboard.")
        _b3 = ttk.Button(arow, text="Save as .txt\u2026", command=self._meeting_save)
        _b3.pack(side="left", padx=6)
        helptip.tip(_b3, "Save the transcript (opens straight in your Meetings folder).")
        _b4 = ttk.Button(arow, text="Open folder",
                         command=self._meeting_open_folder)
        _b4.pack(side="left", padx=6)
        helptip.tip(_b4, "Open the folder where recordings and transcripts are saved.")
        _b5 = ttk.Button(arow, text="Clear", command=self._meeting_clear)
        _b5.pack(side="left", padx=6)
        helptip.tip(_b5, "Clear the text area.")

        ttk.Label(f, text="Transcript", style="Section.TLabel").pack(
            anchor="w", pady=(6, 0))
        self._mt_out = theme.dark_text(f, wrap="word", height=12)
        self._mt_out.pack(fill="both", expand=True, pady=(2, 6))
        self._mt_rec = None

    def _meeting_upgrade(self):
        if "License" in self.SECTIONS:
            self._show("License")
            return
        try:
            self._open_upgrade()
        except Exception:
            import webbrowser
            webbrowser.open("https://echo-quill.com")

    def _meeting_set(self, msg):
        try:
            self.win.after(0, lambda: self._mt_status.configure(text=msg))
        except Exception:
            pass

    def _meeting_copy(self):
        t = self._mt_out.get("1.0", "end").strip()
        if not t:
            self._meeting_set("Nothing to copy yet."); return
        try:
            import pyperclip
            pyperclip.copy(t)
            self._meeting_set("Copied \u2713")
        except Exception:
            self._meeting_set("Copy failed")

    def _meeting_clear(self):
        self._mt_out.delete("1.0", "end")
        self._meeting_set("")

    def _meeting_open_folder(self):
        import os
        from .media_gui import meetings_dir
        try:
            os.startfile(meetings_dir(self.cfg))
        except Exception as e:
            self._meeting_set(str(e))

    def _meeting_start(self):
        from . import meeting
        if not self._mt_name.get().strip():
            self._meeting_set("Please enter a name first \u2014 it's required.")
            try:
                self._mt_nameentry.focus_set()
            except Exception:
                pass
            return
        self._mt_video_path = None
        if getattr(self, "_mt_video", None) is not None and self._mt_video.get():
            if not hasattr(meeting, "ScreenRecorder"):
                self._meeting_set("Screen capture needs the latest build.")
                return
            import os
            from .media_gui import meetings_dir, safe_filename
            nm = self._mt_name.get().strip()
            self._mt_video_path = os.path.join(
                meetings_dir(self.cfg), safe_filename(nm)[:-4] + ".mp4")
            self._mt_rec = meeting.ScreenRecorder(
                self._mt_video_path, include_mic=self._mt_mic.get())
        else:
            self._mt_rec = meeting.MeetingRecorder(include_mic=self._mt_mic.get())
        try:
            self._mt_rec.start()
        except Exception as e:
            self._meeting_set(f"Could not start: {e}"); return
        self._mt_start.configure(state="disabled")
        self._mt_stop.configure(state="normal")
        self._meeting_tick()

    def _meeting_tick(self):
        if self._mt_rec is not None and self._mt_rec._running:
            s = int(self._mt_rec.elapsed())
            self._mt_status.configure(text=f"\u25cf Recording  {s // 60:02d}:{s % 60:02d}")
            self.win.after(500, self._meeting_tick)

    def _meeting_stop(self):
        import threading
        self._mt_stop.configure(state="disabled")
        self._meeting_set("Finishing\u2026")
        rec = self._mt_rec

        def run():
            try:
                audio = rec.stop()
            except Exception as e:
                self._meeting_set(f"Recording error: {e}")
                self.win.after(0, lambda: self._mt_start.configure(state="normal"))
                return
            import numpy as _np
            if audio is None or len(audio) < 1600:
                self._meeting_set("Nothing captured \u2014 no system audio came "
                                  "through. Is something actually playing?")
                self.win.after(0, lambda: self._mt_start.configure(state="normal"))
                return
            if float(_np.max(_np.abs(audio))) < 0.002:
                self._meeting_set("Captured only silence \u2014 your playback "
                                  "device may be muted or one we can't tap.")
                self.win.after(0, lambda: self._mt_start.configure(state="normal"))
                return
            self._meeting_set("Transcribing\u2026 (runs locally)")
            try:
                from .transcriber import Transcriber
                if not hasattr(self, "_mt_engine"):
                    self._mt_engine = Transcriber(self.cfg.get("model", "base"))
                model = self._mt_engine.load()
                lang = self.cfg.get("language", "auto")
                lang = None if lang in ("", "auto") else lang
                segs, _i = model.transcribe(_np.asarray(audio, dtype="float32"),
                                            language=lang, vad_filter=True)
                text = " ".join(s.text.strip() for s in segs).strip()
            except Exception as e:
                self._meeting_set(f"Transcription failed: {e}")
                self.win.after(0, lambda: self._mt_start.configure(state="normal"))
                return

            def show():
                self._mt_out.delete("1.0", "end")
                self._mt_out.insert("1.0", text)
                self._mt_start.configure(state="normal")
                if getattr(self, "_mt_video_path", None):
                    self._meeting_set("Done \u2713 (MP4 video + transcript saved to Meetings)")
                else:
                    self._meeting_set("Done \u2713 (saved to your Meetings folder)")
            self.win.after(0, show)
            try:
                from .media_gui import meetings_dir, safe_filename
                import os
                name = self._mt_name.get().strip() or __import__(
                    "datetime").datetime.now().strftime("Meeting %Y-%m-%d %H%M")
                folder = meetings_dir(self.cfg)
                out = os.path.join(folder, safe_filename(name))
                base, n = out, 2
                while os.path.exists(out):
                    out = base[:-4] + f" ({n}).txt"; n += 1
                with open(out, "w", encoding="utf-8") as fh:
                    fh.write(f"{name}\n\n{text}")
            except Exception:
                pass
        threading.Thread(target=run, daemon=True).start()

    def _meeting_ask(self):
        import threading
        text = self._mt_out.get("1.0", "end").strip()
        if not text:
            self._meeting_set("Transcribe something first."); return
        q = self._mt_qbox.get("1.0", "end").strip()
        if not q or q.startswith("Presets"):
            self._meeting_set("Pick a preset or type a question."); return
        self._meeting_set("Asking AI\u2026")

        def run():
            from . import ai_edit
            ok, res = ai_edit.transform(text, q, self.cfg)

            def show():
                if ok:
                    self._mt_out.insert("1.0", f"=== AI \u2014 {q} ===\n{res}"
                                        "\n\n=== TRANSCRIPT ===\n")
                    self._meeting_set("Answer added \u2713")
                else:
                    self._meeting_set(res)
            self.win.after(0, show)
        threading.Thread(target=run, daemon=True).start()

    def _mt_preset_pick(self, v):
        from . import prompts as _pr
        self._mt_preset.set("Presets \u25be")
        if v == _pr.MANAGE_LABEL:
            _pr.manage_dialog(self.win, self.cfg, self._refresh_preset_menu)
        else:
            self._mt_qbox.delete("1.0", "end")
            self._mt_qbox.insert("1.0", v)

    def _refresh_preset_menu(self):
        try:
            from . import prompts as _pr
            m = self._mt_presetmenu["menu"]
            m.delete(0, "end")
            for q in _pr.menu_items(self.cfg):
                lbl = q if len(q) <= 60 else q[:57] + "\u2026"
                m.add_command(label=lbl, command=lambda v=q: self._mt_preset_pick(v))
        except Exception:
            pass

    def _manage_presets(self):
        from . import prompts as _pr
        dlg = tk.Toplevel(self.win)
        dlg.title("Manage Ask-AI presets")
        dlg.geometry("480x380")
        dlg.attributes("-topmost", True)
        theme.apply(dlg)
        ttk.Label(dlg, text="Ask-AI preset questions", style="Title.TLabel"
                  ).pack(anchor="w", padx=14, pady=(12, 6))
        lb = theme.dark_listbox(dlg, height=10)
        lb.pack(fill="both", expand=True, padx=14)

        def reload():
            lb.delete(0, "end")
            for q in _pr.all_prompts(self.cfg):
                lb.insert("end", "  " + q)
        reload()
        row = ttk.Frame(dlg); row.pack(fill="x", padx=14, pady=8)
        var = tk.StringVar()
        ttk.Entry(row, textvariable=var).pack(side="left", fill="x", expand=True, ipady=2)

        def add():
            _pr.add_prompt(self.cfg, var.get()); var.set("")
            reload(); self._refresh_preset_menu()

        def rem():
            sel = lb.curselection()
            if sel:
                _pr.remove_prompt(self.cfg, lb.get(sel[0]).strip())
                reload(); self._refresh_preset_menu()
        ttk.Button(row, text="Add", command=add).pack(side="left", padx=(6, 0))
        brow = ttk.Frame(dlg); brow.pack(fill="x", padx=14, pady=(0, 10))
        ttk.Button(brow, text="Remove selected", command=rem).pack(side="left")
        ttk.Button(brow, text="Done", style="Accent.TButton",
                   command=dlg.destroy).pack(side="right")

    def _meeting_summarize(self):
        import threading
        text = self._mt_out.get("1.0", "end").strip()
        if not text:
            self._meeting_set("Nothing to summarize yet."); return
        self._meeting_set("Summarizing with AI\u2026")

        def run():
            from . import ai_edit
            ok, res = ai_edit.transform(
                text, "Summarize this meeting/recording into concise key "
                "points and a clear list of action items.", self.cfg)

            def show():
                if ok:
                    self._mt_out.insert("1.0", "=== AI SUMMARY ===\n" + res +
                                        "\n\n=== FULL TRANSCRIPT ===\n")
                    self._meeting_set("Summary added \u2713")
                else:
                    self._meeting_set(res)
            self.win.after(0, show)
        threading.Thread(target=run, daemon=True).start()

    def _meeting_save(self):
        from tkinter import filedialog
        from .media_gui import meetings_dir, safe_filename
        text = self._mt_out.get("1.0", "end").strip()
        if not text:
            self._meeting_set("Nothing to save yet."); return
        nm = self._mt_name.get().strip() or "meeting"
        p = filedialog.asksaveasfilename(
            parent=self.win, defaultextension=".txt",
            initialdir=meetings_dir(self.cfg), initialfile=safe_filename(nm),
            filetypes=[("Text", "*.txt")])
        if p:
            with open(p, "w", encoding="utf-8") as fh:
                fh.write(text)
            self._meeting_set("Saved \u2713")

    # ---------- actions ----------

    def _refresh_dict(self):
        self.dict_list.delete(0, "end")
        for wrong, right in sorted(self.dictionary.replacements.items()):
            self.dict_list.insert("end", f"  {wrong}   →   {right}")

    def _dict_add(self):
        wrong = simpledialog.askstring("Add replacement", "When it hears:", parent=self.win)
        if not wrong:
            return
        right = simpledialog.askstring("Add replacement", f'Replace "{wrong}" with:',
                                       parent=self.win)
        if right is None:
            return
        self.dictionary.add(wrong, right)
        self._refresh_dict()

    def _dict_edit(self):
        sel = self.dict_list.curselection()
        if not sel:
            return
        line = self.dict_list.get(sel[0])
        try:
            old_wrong, old_right = [p.strip() for p in line.split("   →   ", 1)]
        except ValueError:
            return
        new_wrong = simpledialog.askstring(
            "Edit replacement", "When it hears:",
            initialvalue=old_wrong, parent=self.win)
        if not new_wrong:
            return
        new_right = simpledialog.askstring(
            "Edit replacement", f'Replace "{new_wrong}" with:',
            initialvalue=old_right, parent=self.win)
        if new_right is None:
            return
        if new_wrong != old_wrong:
            self.dictionary.remove(old_wrong)   # key changed: drop the old one
        self.dictionary.add(new_wrong, new_right)
        self._refresh_dict()

    def _dict_remove(self):
        sel = self.dict_list.curselection()
        if not sel:
            return
        wrong = self.dict_list.get(sel[0]).split("   →   ")[0].strip()
        self.dictionary.remove(wrong)
        self._refresh_dict()

    def _check_updates(self):
        import threading

        def status(msg):
            self.win.after(0, lambda: self.update_status.configure(text=msg))

        def run():
            try:
                from . import update
                status("Checking…")
                found = update.check()
                if not found:
                    status("You're on the latest version ✓")
                    return
                ver, url = found
                status(f"v{ver} available — downloading…")
                update.download_and_run(url, status)
                status("Installer launched — EchoQuill will close.")
                if self.on_quit:
                    self.win.after(250, self.on_quit)
            except Exception as e:
                status(f"Update check failed: {e}")
        threading.Thread(target=run, daemon=True).start()

    def _open_upgrade(self):
        import webbrowser
        webbrowser.open(self.cfg.get("upgrade_url",
                        "https://github.com/CFRE-dotcom/echoquill#echoquill-pro"))

    def _oauth_sign_in(self):
        import threading

        def status(msg):
            self.win.after(0, lambda: self.oauth_status.configure(text=msg))

        def run():
            try:
                from . import oauth, config as cfgmod2
                self.cfg["ai_oauth_client_id"] = self.ai_client_var.get().strip()
                info = cfgmod.AI_PROVIDERS.get(self.ai_provider_var.get(), {})
                if info.get("oauth_auth_url"):
                    self.cfg["ai_oauth_auth_url"] = info["oauth_auth_url"]
                    self.cfg["ai_oauth_token_url"] = info["oauth_token_url"]
                tok = oauth.sign_in(self.cfg, status)
                self.cfg["ai_oauth_tokens"] = tok
                cfgmod2.save(self.cfg)
                status("Signed in ✓")
            except Exception as e:
                status(f"{e}")
        threading.Thread(target=run, daemon=True).start()

    def _refresh_tones(self):
        self.tone_list.delete(0, "end")
        for app, prompt in sorted(self.cfg.get("per_app_prompts", {}).items()):
            shown = prompt if len(prompt) <= 60 else prompt[:57] + "…"
            self.tone_list.insert("end", f"  {app}   →   {shown}")

    def _tone_add(self):
        app = self.tone_app_var.get().strip()
        prompt = self.tone_prompt_var.get().strip()
        if not app or not prompt:
            return
        tones = dict(self.cfg.get("per_app_prompts", {}))
        tones[app.strip().lower()] = prompt.strip()
        self.cfg["per_app_prompts"] = tones
        cfgmod.save(self.cfg)
        self.tone_app_var.set("")
        self.tone_prompt_var.set("")
        self._refresh_tones()

    def _tone_remove(self):
        sel = self.tone_list.curselection()
        if not sel:
            return
        app = self.tone_list.get(sel[0]).split("   →   ")[0].strip()
        tones = dict(self.cfg.get("per_app_prompts", {}))
        tones.pop(app, None)
        self.cfg["per_app_prompts"] = tones
        cfgmod.save(self.cfg)
        self._refresh_tones()

    def _export_all(self):
        from tkinter import filedialog
        import zipfile, os
        path = filedialog.asksaveasfilename(
            parent=self.win, defaultextension=".zip",
            initialfile="echoquill-export.zip", filetypes=[("Zip", "*.zip")])
        if not path:
            return
        from . import history as h
        from .media_gui import transcripts_dir
        with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zf:
            try:
                zf.write(h.HISTORY_PATH, "history.jsonl")
            except Exception:
                pass
            tdir = transcripts_dir(self.cfg)
            for name in os.listdir(tdir):
                fp = os.path.join(tdir, name)
                if os.path.isfile(fp):
                    zf.write(fp, os.path.join("transcripts", name))
        messagebox.showinfo("Export", "Everything exported ✓", parent=self.win)

    def _export_audio(self):
        from tkinter import filedialog
        from . import audio_store
        path = filedialog.asksaveasfilename(
            parent=self.win, defaultextension=".zip",
            initialfile="echoquill-audio.zip", filetypes=[("Zip", "*.zip")])
        if path and audio_store.export_zip(path):
            messagebox.showinfo("Audio", "Audio exported ✓", parent=self.win)

    def _clear_audio(self):
        from . import audio_store
        if messagebox.askyesno("Delete audio",
                               "Delete all saved dictation recordings?", parent=self.win):
            audio_store.clear()
            messagebox.showinfo("Audio", "Deleted ✓", parent=self.win)

    def _clear_history(self):
        if messagebox.askyesno("Clear history", "Delete all local dictation history?",
                               parent=self.win):
            historymod.clear()

    _STATE_VARS = ["hotkey_var","actmode_var","holdkey_var","insert_var",
        "always_copy_var","overlay_var","autostart_var","cmdmode_var",
        "cmdkey_var","writemode_var","writekey_var","model_var","preview_var",
        "lang_var","mic_var","livepreview_var","start_cue_var","end_cue_var",
        "duck_var","local_cleanup_var","spoken_punct_var","tail_var",
        "dict_enabled_var","learn_var","ai_var","ai_provider_var",
        "ai_auth_var","ai_client_var","ai_url_var","ai_key_var","ai_model_var"]

    def _collect_state(self):
        vals = []
        for name in self._STATE_VARS:
            v = getattr(self, name, None)
            try:
                vals.append(v.get() if v is not None else None)
            except Exception:
                vals.append(None)
        try:
            vals.append(self.ai_prompt_text.get("1.0", "end"))
        except Exception:
            vals.append("")
        return tuple(vals)

    def _on_close(self):
        try:
            dirty = self._collect_state() != self._snapshot
        except Exception:
            dirty = False
        if dirty:
            ans = messagebox.askyesnocancel(
                "EchoQuill", "You changed some settings.\nSave them?",
                parent=self.win)
            if ans is None:
                return          # cancel: stay open
            if ans:
                self._save()    # saves and closes
                return
        self.win.destroy()

    def _save(self):
        mic = self.mic_var.get()
        self.cfg.update({
            "activation_mode": self.actmode_var.get(),
            "hotkey": self.hotkey_var.get().strip() or "ctrl+alt+space",
            "hold_key": self.holdkey_var.get().strip() or "right alt",
            "insertion_mode": self.insert_var.get(),
            "always_copy": self.always_copy_var.get(),
            "overlay_enabled": self.overlay_var.get(),
            "theme": self.theme_var.get(),
            "keep_audio": self.keep_audio_var.get(),
            "audio_max_mb": int(self.audio_mb_var.get()),
            "autostart": self.autostart_var.get(),
            "admin_mode": self.adminmode_var.get(),
            "command_mode": self.cmdmode_var.get(),
            "command_hotkey": self.cmdkey_var.get().strip() or "ctrl+alt+c",
            "write_mode": self.writemode_var.get(),
            "write_hotkey": self.writekey_var.get().strip() or "ctrl+alt+w",
            "model": cfgmod.MODEL_IDS.get(self.model_var.get(), "base"),
            "preview_model": cfgmod.PREVIEW_IDS.get(self.preview_var.get(), "tiny"),
            "language": self.lang_var.get().strip() or "auto",
            "preferred_mic": "" if mic == "(system default)" else mic,
            "live_preview": self.livepreview_var.get(),
            "start_cue": self.start_cue_var.get(),
            "end_cue": self.end_cue_var.get(),
            "duck_media": self.duck_var.get(),
            "local_cleanup": self.local_cleanup_var.get(),
            "spoken_punctuation": self.spoken_punct_var.get(),
            "tail_ms": int(self.tail_var.get()),
            "dictionary_enabled": self.dict_enabled_var.get(),
            "learn_corrections": self.learn_var.get(),
            "ai_enhancement": self.ai_var.get(),
            "ai_on_dictation": self.ai_dictation_var.get(),
            "ai_provider": self.ai_provider_var.get(),
            "ai_auth_method": self.ai_auth_var.get(),
            "ai_oauth_client_id": self.ai_client_var.get().strip(),
            "ai_base_url": self.ai_url_var.get().strip(),
            "ai_api_key": self.ai_key_var.get().strip(),
            "ai_model": self.ai_model_var.get().strip(),
            "ai_prompt": self.ai_prompt_text.get("1.0", "end").strip(),
        })
        cfgmod.save(self.cfg)
        from . import autostart, elevation
        autostart.set_autostart(self.cfg["autostart"])
        if self.cfg.get("admin_mode"):
            elevation.enable()
        else:
            elevation.disable()
        self.on_save(self.cfg)
        self.win.destroy()
