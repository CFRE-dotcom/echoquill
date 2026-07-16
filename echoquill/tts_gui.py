"""Read aloud - paste text or open a document and hear it spoken, or save it
as an MP3. Pro feature, powered by your own ElevenLabs account.
"""

import os
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from . import theme, helptip, tts, player
from .media_gui import narration_dir

READ_HELP = (
    "Read aloud (Text-to-speech)\n\n"
    "• Paste text, or click 'Open a document…' (.txt, .md, .docx, .pdf).\n"
    "• Pick a voice, then Play to hear it, or Save as MP3 to keep the audio.\n"
    "• Audio is saved in your EchoQuill\\Narration folder.\n\n"
    "This uses YOUR ElevenLabs account. Paste your API key once and it's kept "
    "safely in Windows Credential Manager. Get a key at elevenlabs.io → Profile."
)


class ReadAloudWindow:
    def __init__(self, root, cfg):
        self.cfg = cfg
        self._voice_id = cfg.get("tts_voice_id", "") or tts.DEFAULT_VOICE
        self._voices = []            # [(name, id)]
        self._busy = False
        self._play_wav = None

        self.win = tk.Toplevel(root)
        self.win.title("EchoQuill — Read aloud")
        self.win.geometry("640x560")
        self.win.minsize(540, 480)
        self.win.attributes("-topmost", True)
        theme.apply(self.win)
        self.win.protocol("WM_DELETE_WINDOW", self._close)

        # ---- bottom action bar first (never pushed off-screen) ----
        # file-actions row (packed first so it sits at the very bottom)
        bar = ttk.Frame(self.win)
        bar.pack(side="bottom", fill="x", padx=18, pady=(0, 10))
        _save = ttk.Button(bar, text="Save as MP3…", command=self._save)
        _save.pack(side="left")
        helptip.tip(_save, "Generate the audio and save it as an MP3 file.")
        _open = ttk.Button(bar, text="Open folder",
                           command=lambda: self._open_folder())
        _open.pack(side="left", padx=8)
        helptip.tip(_open, "Open your EchoQuill\\Narration folder.")
        _clear = ttk.Button(bar, text="Clear", command=self._clear)
        _clear.pack(side="left")
        helptip.tip(_clear, "Clear the text box.")
        _phone = ttk.Button(bar, text="📱 Listen on my phone",
                            command=self._listen_phone)
        _phone.pack(side="left", padx=(12, 0))
        helptip.tip(_phone, "Show a QR code to open your narrations on your "
                    "phone over WiFi - no accounts, no cloud.")
        self.status = ttk.Label(bar, text="", style="Dim.TLabel")
        self.status.pack(side="left", padx=12)
        # player transport (Play/Pause, Stop, seekable timeline) above it
        prow = ttk.Frame(self.win)
        prow.pack(side="bottom", fill="x", padx=18, pady=(4, 2))
        self.player = player.AudioPlayer(prow, self.win)
        self.player.pack(fill="x")
        helptip.tip(self.player.play_btn, "Play/pause the converted audio. Drag "
                    "the bar to scrub; replays are free.")

        # ---- title ----
        trow = ttk.Frame(self.win)
        trow.pack(anchor="w", padx=18, pady=(14, 2))
        ttk.Label(trow, text="Read aloud", style="Title.TLabel").pack(side="left")
        helptip.attach(self.win, trow, "Read aloud — help", READ_HELP).pack(
            side="left", padx=8)
        ttk.Label(self.win, style="Dim.TLabel", wraplength=590, text=(
            "Turn text into spoken audio.  1) Paste text below, or load a "
            "document.  2) Pick a voice.  3) Click \u201cConvert to audio.\u201d  "
            "Then play it, save an MP3, or send it to your phone \u2014 no cloud."
            )).pack(anchor="w", padx=18)

        # ---- API key row ----
        krow = ttk.Frame(self.win)
        krow.pack(fill="x", padx=18, pady=(10, 2))
        ttk.Label(krow, text="ElevenLabs API key:").pack(side="left")
        self.key_var = tk.StringVar(value=cfg.get("elevenlabs_api_key", ""))
        self.key_entry = ttk.Entry(krow, textvariable=self.key_var, show="•")
        self.key_entry.pack(side="left", fill="x", expand=True, padx=(8, 8), ipady=2)
        _ks = ttk.Button(krow, text="Save key", command=self._save_key)
        _ks.pack(side="left")
        helptip.tip(_ks, "Store your ElevenLabs API key (kept in Windows "
                    "Credential Manager) and load your voices.")

        frow = ttk.Frame(self.win); frow.pack(fill="x", padx=18, pady=(6, 2))
        ttk.Label(frow, text="Save narrations to:").pack(side="left")
        _fch = ttk.Button(frow, text="Change\u2026", command=self._choose_folder)
        _fch.pack(side="right")
        helptip.tip(_fch, "Choose where narrations save - e.g. a OneDrive / "
                    "Google Drive / Dropbox folder so they sync to your phone.")
        self.folder_ent = ttk.Entry(frow)
        self.folder_ent.pack(side="left", fill="x", expand=True, padx=(8, 8), ipady=2)
        self._set_folder_entry()

        # ---- voice + open-document row ----
        vrow = ttk.Frame(self.win)
        vrow.pack(fill="x", padx=18, pady=(6, 2))
        ttk.Label(vrow, text="Voice:").pack(side="left")
        self.voice_var = tk.StringVar(value="(add key, then Load voices)")
        _lv = ttk.Button(vrow, text="Load voices", command=self._load_voices)
        _lv.pack(side="right")
        helptip.tip(_lv, "Fetch the voices on your ElevenLabs account.")
        self.voice_menu = ttk.OptionMenu(vrow, self.voice_var,
                                         "(add key, then Load voices)")
        self.voice_menu.pack(side="left", fill="x", expand=True, padx=(6, 8))

        # Load-document + Convert sit together, right above the text box
        drow = ttk.Frame(self.win); drow.pack(fill="x", padx=18, pady=(8, 0))
        _od = ttk.Button(drow, text="📄 Load a document…", command=self._open_doc)
        _od.pack(side="left")
        helptip.tip(_od, "Pull the text out of a .txt, .md, .docx or .pdf into "
                    "the box, so you can convert it to audio.")
        self.convert_btn = ttk.Button(drow, text="🎙 Convert to audio",
                                      style="Accent.TButton", command=self._play)
        self.convert_btn.pack(side="left", fill="x", expand=True, padx=(8, 0))
        helptip.tip(self.convert_btn, "Turn the text into audio. Then use the "
                    "player to listen, or Save as MP3.")

        _trow = ttk.Frame(self.win); _trow.pack(fill="x", padx=18, pady=(8, 0))
        ttk.Label(_trow, style="Dim.TLabel", text="Text to convert to audio:").pack(side="left")
        self.char_lbl = ttk.Label(_trow, style="Dim.TLabel", text="0 characters")
        self.char_lbl.pack(side="right")
        self.box = theme.dark_text(self.win, wrap="word")
        self.box.pack(fill="both", expand=True, padx=18, pady=(2, 6))
        self.box.bind("<KeyRelease>", lambda e: (self._update_count(), self.player.invalidate()))

        if self.cfg.get("elevenlabs_api_key"):
            self._load_voices()

    # ---------- helpers ----------

    def _set_status(self, text):
        self.win.after(0, lambda: self.status.configure(text=text))

    def _error(self, where, e):
        tts.log_error(where, e)
        msg = str(e)
        self._set_status(msg)
        self.win.after(0, lambda: messagebox.showerror(
            "Read aloud", msg + "\n\n(Details saved to tts_error.log in your "
            "EchoQuill settings folder.)"))

    def _open_folder(self):
        try:
            os.startfile(narration_dir(self.cfg))
        except Exception:
            self._set_status("Could not open folder")

    def _listen_phone(self):
        from . import phone_share
        phone_share.open_phone_window(self.win, self.cfg)

    def _set_folder_entry(self):
        self.folder_ent.configure(state="normal")
        self.folder_ent.delete(0, "end")
        self.folder_ent.insert(0, narration_dir(self.cfg))
        self.folder_ent.configure(state="readonly")

    def _choose_folder(self):
        d = filedialog.askdirectory(
            parent=self.win, title="Choose a folder to save narrations in "
            "(e.g. your OneDrive / Google Drive / Dropbox folder)")
        if not d:
            return
        self.cfg["narration_dir"] = d
        try:
            from . import config as _cfg
            _cfg.save(self.cfg)
        except Exception:
            pass
        self._set_folder_entry()
        self._set_status("Narrations now save to your chosen folder ✓")

    def _default_folder(self):
        self.cfg["narration_dir"] = ""
        try:
            from . import config as _cfg
            _cfg.save(self.cfg)
        except Exception:
            pass
        self._set_folder_entry()
        self._set_status("Back to the default Narration folder")

    def _clear(self):
        self.box.delete("1.0", "end")
        self.status.configure(text="")
        self._update_count()
        try:
            self.player.invalidate()
        except Exception:
            pass

    def _update_count(self):
        try:
            n = len(self.box.get("1.0", "end").strip())
            self.char_lbl.configure(text=f"{n:,} characters")
        except Exception:
            pass

    def _confirm_cost(self, n):
        if n <= 5000:
            return True
        return messagebox.askyesno(
            "Read aloud - heads up",
            f"This is {n:,} characters, which will use about {n:,} ElevenLabs "
            f"credits (ElevenLabs bills per character).\n\nGenerate anyway?",
            parent=self.win)

    def _save_key(self):
        from . import config as _cfg
        self.cfg["elevenlabs_api_key"] = self.key_var.get().strip()
        try:
            _cfg.save(self.cfg)
        except Exception:
            pass
        self._set_status("Key saved ✓")
        self._load_voices()

    def _open_doc(self):
        path = filedialog.askopenfilename(
            parent=self.win, title="Open a document to read",
            filetypes=[("Documents", "*.txt *.md *.docx *.pdf"),
                       ("All files", "*.*")])
        if not path:
            return
        self._set_status("Reading document…")

        def run():
            try:
                text = tts.read_document(path)
            except Exception as e:
                self._set_status(str(e)); return

            def show():
                self.box.delete("1.0", "end")
                self.box.insert("1.0", text)
                self.status.configure(
                    text=f"Loaded {os.path.basename(path)} ✓")
                self._update_count()
                try:
                    self.player.invalidate()
                except Exception:
                    pass
            self.win.after(0, show)
        threading.Thread(target=run, daemon=True).start()

    def _load_voices(self):
        self.cfg["elevenlabs_api_key"] = self.key_var.get().strip()
        if not self.cfg["elevenlabs_api_key"]:
            self._set_status("Add your ElevenLabs API key first.")
            return
        self._set_status("Loading voices…")

        def run():
            try:
                voices = tts.list_voices(self.cfg)
            except Exception as e:
                self._set_status(str(e)); return
            self.win.after(0, lambda: self._fill_voices(voices))
        threading.Thread(target=run, daemon=True).start()

    def _fill_voices(self, voices):
        self._voices = voices
        menu = self.voice_menu["menu"]
        menu.delete(0, "end")
        if not voices:
            self.voice_var.set("(no voices found)")
            self._set_status("No voices on this account.")
            return
        for name, vid in voices:
            menu.add_command(label=name,
                             command=lambda n=name, i=vid: self._pick_voice(n, i))
        # keep the previously chosen voice if it's still there
        cur = next((n for n, i in voices if i == self._voice_id), None)
        if cur:
            self.voice_var.set(cur)
        else:
            self._pick_voice(voices[0][0], voices[0][1])
        self._set_status(f"Loaded {len(voices)} voice"
                         f"{'s' if len(voices) != 1 else ''} ✓")

    def _pick_voice(self, name, vid):
        self.voice_var.set(name)
        self._voice_id = vid
        self.cfg["tts_voice_id"] = vid

    # ---------- play / save ----------

    def _guard(self):
        if self._busy:
            self._set_status("Still working on the last one…")
            return False
        if not self.key_var.get().strip():
            self._set_status("Add your ElevenLabs API key first.")
            return False
        text = self.box.get("1.0", "end").strip()
        if not text:
            self._set_status("Nothing to read - paste or open some text.")
            return False
        if not self._confirm_cost(len(text)):
            self._set_status("Cancelled.")
            return False
        self.cfg["elevenlabs_api_key"] = self.key_var.get().strip()
        return True

    def _play(self):
        if not self._guard():
            return
        text = self.box.get("1.0", "end").strip()
        self._busy = True
        self._set_status("Generating audio…")

        def run():
            import tempfile
            try:
                pcm = tts.synth_pcm(text, self.cfg, self._voice_id,
                                    status_cb=self._set_status)
                fd, wav = tempfile.mkstemp(prefix="eq_ra_", suffix=".wav")
                os.close(fd)
                tts.pcm_to_wav(pcm, wav)

                def go():
                    self.player.load_and_play(wav)
                    self._set_status("Playing ▶")
                self.win.after(0, go)
            except Exception as e:
                self._error("play", e)
            finally:
                self._busy = False
        threading.Thread(target=run, daemon=True).start()

    def _close(self):
        try:
            self.player.shutdown()
        except Exception:
            pass
        self.win.destroy()

    def _save(self):
        if not self._guard():
            return
        text = self.box.get("1.0", "end").strip()
        folder = narration_dir(self.cfg)
        path = filedialog.asksaveasfilename(
            parent=self.win, title="Save narration as MP3",
            initialdir=folder, defaultextension=".mp3",
            filetypes=[("MP3 audio", "*.mp3")])
        if not path:
            return
        self._busy = True
        self._set_status("Generating audio…")

        def run():
            try:
                tts.synthesize_to_mp3(text, self.cfg, self._voice_id, path,
                                      status_cb=self._set_status)
                self._set_status(f"Saved ✓  {os.path.basename(path)}")
            except Exception as e:
                self._error("save", e)
            finally:
                self._busy = False
        threading.Thread(target=run, daemon=True).start()
