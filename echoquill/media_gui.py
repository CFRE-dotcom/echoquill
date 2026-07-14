"""Transcribe any video or audio - from a URL (YouTube etc. via yt-dlp) or a
local file (mp4, mp3, mov, m4a, wav, ...). Free replacement for paid
transcription services: the same local Whisper engine does the work.
"""

import os
import tempfile
import threading

from . import config as cfgmod
from . import helptip

MEDIA_HELP = 'How to transcribe video and audio\n\n- Paste a URL from YouTube (incl. Shorts), TikTok, and ~1,800 sites, then click Transcribe URL.\n- Choose a file on this PC to transcribe any audio or video file.\n- Batch: many URLs - paste a whole list; each is transcribed one at a time and auto-saved (named after the video) in your Transcriptions folder.\n- Stop cancels a transcription in progress.\n- Find in transcript: type a word to highlight it, with timestamps.\n- Skool / members-only: paste the embedded video link in the lesson (YouTube, Vimeo, Loom or Wistia). For the Skool native player, open the video, press F12 - Network tab - filter m3u8, and paste that .m3u8 link. For login-gated videos turn on Settings - Transcription - Sign in via browser.\n\nEverything runs on your PC - nothing is uploaded.'



def _allowance(cfg) -> int:
    """Transcriptions left in the free version (Pro removes this limit)."""
    return max(0, cfg.get("transcription_limit", 5) - cfg.get("transcriptions_used", 0))


def _use_one(cfg):
    cfg["transcriptions_used"] = cfg.get("transcriptions_used", 0) + 1
    cfgmod.save(cfg)


def normalize_url(u: str) -> str:
    """Fix what paste drags in: whitespace, quotes, angle brackets, and a
    missing https:// (why Shorts links sometimes needed several tries)."""
    u = (u or "").strip().strip('\'"<>').strip()
    u = u.replace(" ", "")
    if u and "://" not in u and "." in u:
        u = "https://" + u
    return u


def _keep_awake(on: bool):
    """Stop Windows sleeping mid-transcription (long videos, batches)."""
    try:
        import ctypes
        ES_CONTINUOUS, ES_SYSTEM_REQUIRED = 0x80000000, 0x00000001
        ctypes.windll.kernel32.SetThreadExecutionState(
            ES_CONTINUOUS | ES_SYSTEM_REQUIRED if on else ES_CONTINUOUS)
    except Exception:
        pass


def fmt_time(sec: float) -> str:
    sec = int(sec or 0)
    h, m, s2 = sec // 3600, (sec % 3600) // 60, sec % 60
    return f"{h}:{m:02d}:{s2:02d}" if h else f"{m:02d}:{s2:02d}"


LIMIT_MSG = ("Free limit reached (5 video transcriptions). Upgrade to Pro for "
             "unlimited — only $5/month or $39/year. Dictation stays free forever.")


def friendly_dl_error(e) -> str:
    """Turn common yt-dlp errors into plain-language guidance."""
    msg = str(e)
    low = msg.lower()
    if "not a bot" in low or "sign in to confirm" in low or \
       ("cookies" in low and "youtube" in low):
        return ("YouTube asked to verify you're not a bot. Turn on Settings > "
                "Transcription > \"Sign in via browser\" and pick the browser "
                "you're logged into YouTube with, then try again.")
    if "cookie" in low and ("copy" in low or "database" in low or "chrome" in low):
        return ("Can't read Chrome's cookies (Chrome locks/encrypts them). "
                "Either switch Settings > Transcription > Sign in via browser to "
                "FIREFOX, or export a cookies.txt and set it in Settings > "
                "Transcription > Cookies file.")
    if "403" in low or "forbidden" in low:
        return ("Access denied - the signed link may have expired or needs your "
                "login. Grab a fresh link, and/or turn on Settings > "
                "Transcription > Sign in via browser.")
    return f"Error: {msg}"


def open_upgrade(cfg):
    import webbrowser
    webbrowser.open(cfg.get("upgrade_url",
                    "https://github.com/CFRE-dotcom/echoquill#echoquill-pro"))
import tkinter as tk
from tkinter import ttk, filedialog

from . import theme


def fetch_audio_info(url: str, status_cb, cfg=None):
    """Download best-audio for a URL. Returns (path, video_title).

    Handles Skool: its native player streams signed HLS (.m3u8) from a CDN that
    demands a Referer header, and member-only videos need your browser login.
    """
    import yt_dlp
    tmpdir = tempfile.mkdtemp(prefix="echoquill_")
    status_cb("Downloading audio…")
    opts = {
        "format": "bestaudio/best",
        "outtmpl": os.path.join(tmpdir, "audio.%(ext)s"),
        "quiet": True, "no_warnings": True, "noplaylist": True,
    }
    low = (url or "").lower()
    if "skool.com" in low or ".m3u8" in low:
        opts["http_headers"] = {"Referer": "https://www.skool.com/",
                                "Origin": "https://www.skool.com"}
    # Optional: pull videos that require you to be logged in, using the cookies
    # from your browser (Settings > Transcription > "Sign in via browser").
    cf = ((cfg or {}).get("yt_cookies_file", "") or "").strip()
    br = ((cfg or {}).get("yt_cookies_browser", "") or "").strip().lower()
    if cf and os.path.exists(cf):
        opts["cookiefile"] = cf          # exported cookies.txt (most reliable)
    elif br:
        try:
            opts["cookiesfrombrowser"] = (br,)
        except Exception:
            pass
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=True)
    title = (info or {}).get("title") or "transcript"
    for name in os.listdir(tmpdir):
        return os.path.join(tmpdir, name), title
    raise RuntimeError("Download produced no audio file")


def fetch_audio(url: str, status_cb) -> str:
    return fetch_audio_info(url, status_cb)[0]


def safe_filename(title: str) -> str:
    import re
    name = re.sub(r'[\\/:*?"<>|]+', "", title).strip()
    name = re.sub(r"\s+", " ", name)
    return (name[:120] or "transcript") + ".txt"


def _safe_stem(title: str) -> str:
    return safe_filename(title)[:-4]  # strip the .txt


def _unique_path(p: str) -> str:
    base, ext = os.path.splitext(p)
    q, n = p, 2
    while os.path.exists(q):
        q = f"{base} ({n}){ext}"
        n += 1
    return q


def _media_opts(url, cfg, tmpl, fmt):
    opts = {"format": fmt, "outtmpl": tmpl,
            "quiet": True, "no_warnings": True, "noplaylist": True}
    low = (url or "").lower()
    if "skool.com" in low or ".m3u8" in low:
        opts["http_headers"] = {"Referer": "https://www.skool.com/",
                                "Origin": "https://www.skool.com"}
    cf = ((cfg or {}).get("yt_cookies_file", "") or "").strip()
    br = ((cfg or {}).get("yt_cookies_browser", "") or "").strip().lower()
    if cf and os.path.exists(cf):
        opts["cookiefile"] = cf          # exported cookies.txt (most reliable)
    elif br:
        try:
            opts["cookiesfrombrowser"] = (br,)
        except Exception:
            pass
    return opts


def download_video(url, cfg, dest_dir, status_cb=lambda s: None, name=None) -> str:
    """Download the FULL video (not just audio) into dest_dir. Returns title.

    If name is given, the file is saved under that name (used for Skool videos
    and the optional 'Name this transcript' box)."""
    import yt_dlp
    status_cb("Downloading video…")
    if name:
        tmpl = os.path.join(dest_dir, _safe_stem(name) + ".%(ext)s")
    else:
        tmpl = os.path.join(dest_dir, "%(title).120B.%(ext)s")
    opts = _media_opts(url, cfg, tmpl, "best/bv*+ba/b")
    opts["merge_output_format"] = "mp4"
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=True)
    return (info or {}).get("title") or "video"


def base_dir(cfg) -> str:
    """The one EchoQuill folder that holds all the organized subfolders."""
    d = (cfg or {}).get("output_dir") or os.path.join(
        os.path.expanduser("~"), "Documents", "EchoQuill")
    os.makedirs(d, exist_ok=True)
    return d


def _subfolder(cfg, name) -> str:
    d = os.path.join(base_dir(cfg), name)
    os.makedirs(d, exist_ok=True)
    return d


def transcripts_dir(cfg) -> str:
    # honor a legacy explicit override if the user set one
    if (cfg or {}).get("transcripts_dir"):
        d = cfg["transcripts_dir"]
        os.makedirs(d, exist_ok=True)
        return d
    return _subfolder(cfg, "Transcriptions")


def meetings_dir(cfg) -> str:
    return _subfolder(cfg, "Meetings")


def clips_dir(cfg) -> str:
    return _subfolder(cfg, "Clips")


class MediaWindow:
    def __init__(self, root: tk.Tk, transcriber, cfg: dict):
        self.transcriber = transcriber
        self.cfg = cfg
        self.win = tk.Toplevel(root)
        self.win.title("EchoQuill — Transcribe video or audio")
        self.win.geometry("660x560")
        self.win.minsize(560, 480)
        self.win.attributes("-topmost", True)
        theme.apply(self.win)

        # bottom action bar FIRST so it can never be pushed off-screen
        bar = ttk.Frame(self.win)
        bar.pack(side="bottom", fill="x", padx=18, pady=(2, 12))
        _b_copy = ttk.Button(bar, text="Copy", style="Accent.TButton",
                   command=self._copy); _b_copy.pack(side="left")
        helptip.tip(_b_copy, "Copy the whole transcript to the clipboard.")
        _b_save = ttk.Button(bar, text="Save as .txt…", command=self._save)
        _b_save.pack(side="left", padx=8)
        helptip.tip(_b_save, "Save the transcript as a text file.")
        _b_open = ttk.Button(bar, text="Open folder",
                   command=lambda: os.startfile(transcripts_dir(self.cfg)))
        _b_open.pack(side="left")
        helptip.tip(_b_open, "Open the folder where transcripts are saved.")
        _b_clear = ttk.Button(bar, text="Clear", command=self._clear)
        _b_clear.pack(side="left", padx=8)
        helptip.tip(_b_clear, "Clear the URL box and the transcript.")
        ttk.Button(bar, text="⭐ Upgrade",
                   command=lambda: open_upgrade(self.cfg)).pack(side="right")

        _title_row = ttk.Frame(self.win)
        _title_row.pack(anchor="w", padx=18, pady=(14, 2))
        ttk.Label(_title_row, text="Transcribe video / audio",
                  style="Title.TLabel").pack(side="left")
        helptip.attach(self.win, _title_row, "Transcriber - help", MEDIA_HELP).pack(side="left", padx=8)
        ttk.Label(self.win, style="Dim.TLabel", wraplength=580, text=(
            "Paste a video URL (YouTube and most sites), or pick a file from "
            "your computer. Runs on your PC with the same free engine — "
            "nothing is uploaded anywhere.")).pack(anchor="w", padx=18)

        row = ttk.Frame(self.win)
        row.pack(fill="x", padx=18, pady=(12, 4))
        self.url_var = tk.StringVar()
        ttk.Entry(row, textvariable=self.url_var).pack(
            side="left", fill="x", expand=True)
        _b_url = ttk.Button(row, text="Transcribe URL", style="Accent.TButton",
                   command=self._go_url); _b_url.pack(side="left", padx=(8, 0))
        helptip.tip(_b_url, "Download and transcribe the video/audio at this URL.")

        row2 = ttk.Frame(self.win)
        row2.pack(fill="x", padx=18, pady=4)
        _b_file = ttk.Button(row2, text="Choose a file on this PC…",
                   command=self._go_file); _b_file.pack(side="left")
        helptip.tip(_b_file, "Pick an audio or video file on your computer to transcribe.")
        _b_batch = ttk.Button(row2, text="Batch: many URLs…",
                   command=self._open_batch); _b_batch.pack(side="left", padx=8)
        helptip.tip(_b_batch, "Transcribe a whole list of URLs, one after another.")
        self.stop_btn = ttk.Button(row2, text="Stop", command=self._stop, state="disabled")
        self.stop_btn.pack(side="left", padx=(8, 0))
        helptip.tip(self.stop_btn, "Stop the transcription in progress.")
        self.status = ttk.Label(row2, text="", style="Dim.TLabel")
        self.status.pack(side="left", padx=12)

        namerow = ttk.Frame(self.win)
        namerow.pack(fill="x", padx=18, pady=(6, 0))
        ttk.Label(namerow, text="Name this transcript (optional):").pack(side="left")
        self.name_var = tk.StringVar()
        _nm = ttk.Entry(namerow, textvariable=self.name_var)
        _nm.pack(side="left", fill="x", expand=True, padx=(8, 0), ipady=2)
        helptip.tip(_nm, "Type a name and the transcript (plus any kept "
                         "audio/video) saves under it - no re-saving. Leave "
                         "blank to use the video's own title. Handy for Skool "
                         "videos, which have no title.")
        keeprow = ttk.Frame(self.win)
        keeprow.pack(fill="x", padx=18, pady=(4, 0))
        self.keep_audio_var = tk.BooleanVar(value=False)
        self.keep_video_var = tk.BooleanVar(value=False)
        _ka = ttk.Checkbutton(keeprow, text="Keep audio file",
                              variable=self.keep_audio_var)
        _ka.pack(side="left")
        _kv = ttk.Checkbutton(keeprow, text="Keep video file",
                              variable=self.keep_video_var)
        _kv.pack(side="left", padx=(16, 0))
        helptip.tip(_ka, "Also save the downloaded audio next to the transcript "
                         "(off by default).")
        helptip.tip(_kv, "Also download and save the full video file "
                         "(off by default).")
        # Find-in-transcript shares this row, filling the empty space on the right
        self.search_count = ttk.Label(keeprow, text="", style="Dim.TLabel")
        self.search_count.pack(side="right", padx=(6, 0))
        self.search_var = tk.StringVar()
        se = ttk.Entry(keeprow, textvariable=self.search_var, width=28)
        se.pack(side="right", padx=6)
        se.bind("<KeyRelease>", lambda e: self._search())
        ttk.Label(keeprow, text="Find in transcript:").pack(side="right")

        self.out = theme.dark_text(self.win, wrap="word")
        self.out.pack(fill="both", expand=True, padx=18, pady=(8, 4))

    # ---------- actions ----------

    def _set_status(self, text):
        self.win.after(0, lambda: self.status.configure(text=text))

    def _append(self, text):
        def _do():
            self.out.insert("end", text)
            self.out.see("end")
        self.win.after(0, _do)

    def _open_batch(self):
        BatchWindow(self.win, self.transcriber, self.cfg)

    def _go_url(self):
        url = normalize_url(self.url_var.get())
        self.url_var.set(url)
        if url:
            threading.Thread(target=self._run, args=(url, True), daemon=True).start()

    def _go_file(self):
        path = filedialog.askopenfilename(parent=self.win, title="Pick video or audio",
            filetypes=[("Video/Audio", "*.mp4 *.mkv *.mov *.avi *.webm *.mp3 *.m4a *.wav *.flac *.ogg"),
                       ("All files", "*.*")])
        if path:
            threading.Thread(target=self._run, args=(path, False), daemon=True).start()

    def _engine(self):
        """Own transcription engine per window so it never blocks dictation."""
        if not hasattr(self, "_own_engine"):
            from .transcriber import Transcriber
            self._own_engine = Transcriber(self.cfg.get("model", "base"))
        return self._own_engine

    def _stop(self):
        """Cancel an in-progress transcription."""
        self._cancel = True
        self._set_status("Stopping…")

    def _run(self, source, is_url):
        self._cancel = False
        self.win.after(0, lambda: self.stop_btn.configure(state="normal"))
        if _allowance(self.cfg) <= 0:
            self._set_status(LIMIT_MSG)
            return
        path = None
        try:
            self.win.after(0, lambda: self.out.delete("1.0", "end"))
            if is_url:
                path, title = fetch_audio_info(source, self._set_status, self.cfg)
            else:
                path = source
                title = os.path.splitext(os.path.basename(source))[0]
            custom = (self.name_var.get().strip()
                      if hasattr(self, "name_var") else "")
            if custom:
                title = custom
            header = f"{title}\n{source}\n\n"
            self._append(header)
            # Keep audio/video BEFORE transcribing, while the signed link is
            # still fresh (a long transcription can outlive a Skool token).
            if is_url:
                keep_folder = transcripts_dir(self.cfg)
                if self.keep_video_var.get():
                    try:
                        self._set_status("Downloading video…")
                        download_video(source, self.cfg, keep_folder,
                                       self._set_status, name=title)
                        self._append("[Saved the video file ✓]\n\n")
                    except Exception as _ve:
                        self._append(f"[Could not save video: {_ve}]\n\n")
                if self.keep_audio_var.get() and path and os.path.exists(path):
                    try:
                        ext = os.path.splitext(path)[1] or ".m4a"
                        adst = _unique_path(os.path.join(
                            keep_folder, _safe_stem(title) + ext))
                        import shutil as _sh
                        _sh.copy2(path, adst)
                        self._append(f"[Saved the audio file: "
                                     f"{os.path.basename(adst)} ✓]\n\n")
                    except Exception as _ae:
                        self._append(f"[Could not save audio: {_ae}]\n\n")

            self._set_status("Transcribing… (long videos take a while)")
            eng = self._engine()
            model = eng.load()
            lang = self.cfg.get("language", "auto")
            lang = None if lang in ("", "auto") else lang
            parts = []
            self._seg_map = []          # (char_start, char_end, seconds)
            pos = len(header)
            _keep_awake(True)
            with eng._lock:
                segments, _info = model.transcribe(path, language=lang, vad_filter=True)
                for seg in segments:
                    if self._cancel:
                        break
                    t = seg.text.strip()
                    parts.append(t)
                    self._seg_map.append((pos, pos + len(t) + 1, seg.start))
                    pos += len(t) + 1
                    self._append(t + " ")
            # auto-save, named after the (cleaned) video title
            folder = transcripts_dir(self.cfg)
            out = os.path.join(folder, safe_filename(title))
            base, n = out, 2
            while os.path.exists(out):
                out = base[:-4] + f" ({n}).txt"; n += 1
            with open(out, "w", encoding="utf-8") as f:
                f.write(header + " ".join(parts).strip())
            _use_one(self.cfg)
            left = _allowance(self.cfg)
            self._set_status(f"Done ✓ — saved automatically: {os.path.basename(out)}"
                             f"  ({left} free transcription{'s' if left != 1 else ''} left)")
        except Exception as e:
            self._set_status(friendly_dl_error(e))
        finally:
            _keep_awake(False)
            self.win.after(0, lambda: self.stop_btn.configure(state="disabled"))
            if getattr(self, "_cancel", False):
                self._set_status("Stopped.")
            if is_url and path:
                import shutil
                shutil.rmtree(os.path.dirname(path), ignore_errors=True)

    def _time_at(self, char_offset: int):
        for start, end, sec in getattr(self, "_seg_map", []):
            if start <= char_offset < end:
                return sec
        return None

    def _clear(self):
        self.out.delete("1.0", "end")
        self.url_var.set("")
        self.search_var.set("")
        self.search_count.configure(text="")
        self.status.configure(text="")

    def _search(self):
        term = self.search_var.get().strip()
        self.out.tag_remove("hit", "1.0", "end")
        if not term:
            self.search_count.configure(text="")
            return
        self.out.tag_configure("hit", background="#0a84ff", foreground="#ffffff")
        count = 0
        idx = "1.0"
        while True:
            idx = self.out.search(term, idx, nocase=True, stopindex="end")
            if not idx:
                break
            end = f"{idx}+{len(term)}c"
            self.out.tag_add("hit", idx, end)
            if count == 0:
                self.out.see(idx)
            idx = end
            count += 1
        times = []
        if count and getattr(self, "_seg_map", None):
            i2 = "1.0"
            while len(times) < 5:
                i2 = self.out.search(term, i2, nocase=True, stopindex="end")
                if not i2:
                    break
                off = int(self.out.count("1.0", i2, "chars")[0])
                t = self._time_at(off)
                if t is not None:
                    ts = fmt_time(t)
                    if ts not in times:
                        times.append(ts)
                i2 = f"{i2}+{len(term)}c"
        label = f"{count} match{'es' if count != 1 else ''}"
        if times:
            label += " — at " + ", ".join(times)
        self.search_count.configure(text=label)

    def _copy(self):
        try:
            import pyperclip
            pyperclip.copy(self.out.get("1.0", "end").strip())
            self._set_status("Copied ✓")
        except Exception:
            self._set_status("Copy failed")

    def _save(self):
        path = filedialog.asksaveasfilename(parent=self.win, defaultextension=".txt",
                                            filetypes=[("Text", "*.txt")])
        if path:
            with open(path, "w", encoding="utf-8") as f:
                f.write(self.out.get("1.0", "end").strip())
            self._set_status("Saved ✓")


class BatchWindow:
    """Paste many URLs (one per line). Transcribes them one at a time and
    auto-saves each as <video title>.txt in your EchoQuill Transcriptions
    folder (Documents\EchoQuill Transcriptions)."""

    def __init__(self, parent, transcriber, cfg):
        self.transcriber = transcriber
        self.cfg = cfg
        self.win = tk.Toplevel(parent)
        self.win.title("EchoQuill — Batch transcription")
        self.win.geometry("660x560")
        self.win.minsize(560, 480)
        self.win.attributes("-topmost", True)
        theme.apply(self.win)

        ttk.Label(self.win, text="Batch transcription",
                  style="Title.TLabel").pack(anchor="w", padx=18, pady=(14, 2))
        self.folder = transcripts_dir(cfg)
        ttk.Label(self.win, style="Dim.TLabel", wraplength=580, text=(
            "Paste video URLs below, one per line. Each is transcribed in "
            f"order and saved automatically as its video title in:\n{self.folder}"
            )).pack(anchor="w", padx=18)

        self.urls = theme.dark_text(self.win, height=8, wrap="none")
        self.urls.pack(fill="x", padx=18, pady=(10, 6))

        bar = ttk.Frame(self.win)
        bar.pack(fill="x", padx=18)
        self.start_btn = ttk.Button(bar, text="Start batch",
                                    style="Accent.TButton", command=self._start)
        self.start_btn.pack(side="left")
        helptip.tip(self.start_btn, "Transcribe every URL in the list, one at a time.")
        self.stop_btn = ttk.Button(bar, text="Stop", command=self._stop, state="disabled")
        self.stop_btn.pack(side="left", padx=(8, 0))
        helptip.tip(self.stop_btn, "Stop the batch after the current item.")
        _bb_copy = ttk.Button(bar, text="Copy",
                   command=self._copy_last); _bb_copy.pack(side="left", padx=(16, 0))
        helptip.tip(_bb_copy, "Copy the most recently finished transcript.")
        _bb_open = ttk.Button(bar, text="Open folder",
                   command=self._open_folder); _bb_open.pack(side="left", padx=8)
        helptip.tip(_bb_open, "Open the folder where transcripts are saved.")
        _bb_clear = ttk.Button(bar, text="Clear", command=self._clear)
        _bb_clear.pack(side="left", padx=8)
        helptip.tip(_bb_clear, "Clear the list and log.")
        _bb_up = ttk.Button(bar, text="⭐ Upgrade",
                   command=lambda: open_upgrade(self.cfg)); _bb_up.pack(side="right")
        helptip.tip(_bb_up, "See what EchoQuill Pro unlocks.")
        self._last_text = ""

        ttk.Label(self.win, text="PROGRESS", style="Section.TLabel"
                  ).pack(anchor="w", padx=18, pady=(12, 2))
        self.log = theme.dark_text(self.win, wrap="word", state="disabled")
        self.log.pack(fill="both", expand=True, padx=18, pady=(0, 14))

    def _open_folder(self):
        try:
            os.startfile(self.folder)
        except Exception:
            pass

    def _log(self, line):
        def _do():
            self.log.configure(state="normal")
            self.log.insert("end", line + "\n")
            self.log.see("end")
            self.log.configure(state="disabled")
        self.win.after(0, _do)

    def _clear(self):
        self.urls.delete("1.0", "end")
        self.log.configure(state="normal")
        self.log.delete("1.0", "end")
        self.log.configure(state="disabled")

    def _copy_last(self):
        try:
            import pyperclip
            pyperclip.copy(self._last_text)
        except Exception:
            pass

    def _stop(self):
        self._bcancel = True
        self._log("Stopping after the current step…")

    def _start(self):
        urls = [normalize_url(u) for u in self.urls.get("1.0", "end").splitlines()
                if u.strip()]
        if not urls:
            return
        self._bcancel = False
        self.start_btn.configure(state="disabled")
        self.stop_btn.configure(state="normal")
        threading.Thread(target=self._run, args=(urls,), daemon=True).start()

    def _run(self, urls):
        _keep_awake(True)
        lang = self.cfg.get("language", "auto")
        lang = None if lang in ("", "auto") else lang
        done = 0
        for i, url in enumerate(urls, 1):
            if getattr(self, "_bcancel", False):
                self._log("Stopped.")
                break
            if _allowance(self.cfg) <= 0:
                self._log(LIMIT_MSG)
                break
            try:
                self._log(f"[{i}/{len(urls)}] Downloading: {url}")
                path, title = fetch_audio_info(url, lambda s: None, self.cfg)
                self._log(f"[{i}/{len(urls)}] Transcribing: {title}")
                model = self.transcriber.load()
                with self.transcriber._lock:
                    segments, _info = model.transcribe(path, language=lang,
                                                       vad_filter=True)
                    text = " ".join(seg.text.strip() for seg in segments).strip()
                out = os.path.join(self.folder, safe_filename(title))
                base, n = out, 2
                while os.path.exists(out):
                    out = base[:-4] + f" ({n}).txt"; n += 1
                full = f"{title}\n{url}\n\n{text}"
                with open(out, "w", encoding="utf-8") as f:
                    f.write(full)
                done += 1
                _use_one(self.cfg)
                import shutil
                shutil.rmtree(os.path.dirname(path), ignore_errors=True)
                self._last_text = full
                self._log(f"[{i}/{len(urls)}] Saved ✓  {os.path.basename(out)}")
                preview = text if len(text) <= 600 else text[:600] + " […full text saved to file]"
                self._log("    " + preview + "\n")
            except Exception as e:
                self._log(f"[{i}/{len(urls)}] FAILED: " + friendly_dl_error(e))
        _keep_awake(False)
        if not getattr(self, "_bcancel", False):
            self._log(f"Batch finished — {done}/{len(urls)} saved to {self.folder}")
        else:
            self._log(f"Batch stopped — {done} saved to {self.folder}")
        self.win.after(0, lambda: self.start_btn.configure(state="normal"))
        self.win.after(0, lambda: self.stop_btn.configure(state="disabled"))
