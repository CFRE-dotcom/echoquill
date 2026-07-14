"""EchoQuill — free, open-source, local-first dictation.

Press the global hotkey once to start dictating, again to stop.
Text is transcribed on-device and inserted into whatever app is focused.
Lives in the system tray. Everything optional is off unless you turn it on.
"""

import queue
import threading
import time
import tkinter as tk

from . import config as cfgmod
from . import cleanup, history, injector
from .audio import Recorder
from .dictionary import Dictionary
from .overlay import Overlay
from .transcriber import Transcriber

APP_TITLE = "EchoQuill"


class App:
    def __init__(self):
        self.cfg = cfgmod.load()
        from . import theme as _theme0
        _theme0.set_mode(self.cfg.get("theme", "dark"))
        self.dictionary = Dictionary()
        self.transcriber = Transcriber(self.cfg["model"])
        # Separate ultra-fast model so live words keep up with your voice
        self.preview_transcriber = Transcriber(self.cfg.get("preview_model", "tiny"))
        self.events = queue.Queue()
        self.recorder = None
        self._record_started_at = 0.0
        self._busy = False
        self._last_text = ""
        self._mode = "dictate"          # dictate | command | write
        self._write_selection = ""

        # tkinter root (hidden) drives the overlay + settings windows.
        # TkinterDnD root enables dragging clips out into other apps.
        try:
            from tkinterdnd2 import TkinterDnD
            self.root = TkinterDnD.Tk()
        except Exception:
            self.root = tk.Tk()
        self.root.withdraw()
        self.root.title(APP_TITLE)
        self.overlay = Overlay(
            self.root,
            on_toggle=lambda: self.events.put("toggle"),
            on_settings=lambda: self.events.put("settings"),
            on_stats=lambda: self.events.put("stats"),
            on_quit=lambda: self.events.put("quit"),
            on_history=lambda: self.events.put("history"),
            on_clips=lambda: self.events.put("clips"),
            on_media=lambda: self.events.put("media"),
            on_command=lambda: self.events.put("toggle_command"),
            on_help=lambda: self.events.put("help"),
            on_meeting=lambda: self.events.put("meeting"),
            level_provider=lambda: (self.recorder.level if self.recorder else 0.0),
        )

        from .update_badge import UpdateBadge
        self._update_badge = UpdateBadge(self.root, lambda: self.events.put("open_update"))

        self._register_activation()
        self._refresh_idle_hint()
        self.overlay.show_idle()
        self._start_tray()

        # Warm the model in the background so the first dictation is fast
        threading.Thread(target=self._warm_model, daemon=True).start()

        # Heal the auto-start entry (points at wherever THIS copy lives)
        if self.cfg.get("autostart"):
            try:
                from . import autostart
                autostart.set_autostart(True)
            except Exception:
                pass

        # First run: friendly welcome instead of silence
        from . import onboarding
        self.root.after(800, lambda: onboarding.maybe_show(self.root, self.cfg))

        # Quiet update check shortly after startup
        if self.cfg.get("auto_check_updates", True):
            threading.Thread(target=self._startup_update_check, daemon=True).start()

    # ---------- setup ----------

    def _startup_update_check(self):
        first = True
        while True:
            try:
                time.sleep(6 if first else 12 * 3600)
                first = False
                from . import update
                found = update.check()
                if found:
                    ver, _url = found
                    self.events.put(("update_available", ver))
            except Exception:
                time.sleep(3600)

    def _warm_model(self):
        try:
            self.transcriber.load()
        except Exception:
            pass  # will retry (with a visible error) on first use
        try:
            if self.cfg.get("live_preview", True):
                self.preview_transcriber.load()
        except Exception:
            pass

    def _refresh_idle_hint(self):
        if self.cfg.get("activation_mode", "toggle") == "hold":
            self._hint = f"🎙  Hold {self.cfg.get('hold_key', 'right alt')} and talk — or click the mic"
        else:
            self._hint = f"🎙  {self.cfg.get('hotkey', 'ctrl+alt+space')} — or click the mic"
        self.overlay.idle_text = "🎙"

    def _register_activation(self):
        import keyboard
        try:
            keyboard.unhook_all()
        except Exception:
            pass
        if self.cfg.get("activation_mode", "toggle") == "hold":
            # Hold-to-talk, like holding Option on the Mac app
            key = self.cfg.get("hold_key", "right alt")
            keyboard.on_press_key(key, lambda e: self.events.put("hold_press"), suppress=False)
            keyboard.on_release_key(key, lambda e: self.events.put("hold_release"), suppress=False)
        else:
            keyboard.add_hotkey(self.cfg["hotkey"], lambda: self.events.put("toggle"))
        if self.cfg.get("command_mode", True):
            keyboard.add_hotkey(self.cfg.get("command_hotkey", "ctrl+alt+c"),
                                lambda: self.events.put("toggle_command"))
        if self.cfg.get("write_mode", True):
            keyboard.add_hotkey(self.cfg.get("write_hotkey", "ctrl+alt+w"),
                                lambda: self.events.put("toggle_write"))
        # ESC cancels an in-progress dictation (only acts while recording)
        keyboard.on_press_key("esc", self._esc_pressed, suppress=False)

    def _start_tray(self):
        threading.Thread(target=self._tray_thread, daemon=True).start()

    def _tray_thread(self):
        try:
            import pystray
            from PIL import Image, ImageDraw

            img = Image.new("RGB", (64, 64), "#1c1c1e")
            d = ImageDraw.Draw(img)
            d.rounded_rectangle([24, 10, 40, 40], radius=8, fill="#0a84ff")  # mic body
            d.rectangle([30, 40, 34, 50], fill="#0a84ff")                    # mic stem
            d.rectangle([22, 50, 42, 54], fill="#0a84ff")                    # mic base

            menu = pystray.Menu(
                pystray.MenuItem(
                    lambda item: "Stop dictation" if self.recorder and self.recorder.recording
                    else "Start dictation",
                    lambda: self.events.put("toggle"), default=True),
                pystray.MenuItem("Voice command", lambda: self.events.put("toggle_command")),
                pystray.MenuItem("Settings…", lambda: self.events.put("settings")),
                pystray.MenuItem("Meeting / Record", lambda: self.events.put("meeting")),
                pystray.MenuItem("Today's stats", lambda: self.events.put("stats")),
                pystray.MenuItem("Help", lambda: self.events.put("help")),
                pystray.MenuItem("Quit", lambda: self.events.put("quit")),
            )
            self.tray = pystray.Icon("echoquill", img, APP_TITLE, menu)
            self.tray.run()
        except Exception:
            self.tray = None  # app still works via hotkey without a tray icon

    # ---------- event loop ----------

    def run(self):
        self.root.after(50, self._poll)
        self.root.mainloop()

    def _poll(self):
        try:
            while True:
                ev = self.events.get_nowait()
                if ev == "toggle":
                    self._toggle()
                elif ev == "cancel":
                    self._cancel_dictation()
                elif ev == "toggle_command":
                    self._toggle(mode="command")
                elif ev == "toggle_write":
                    self._toggle(mode="write")
                elif ev == "hold_press":
                    if not (self.recorder and self.recorder.recording) and not self._busy:
                        self._begin()
                elif ev == "hold_release":
                    if self.recorder and self.recorder.recording and not self._busy:
                        self._busy = True
                        self._overlay_update("busy")
                        threading.Thread(target=self._finish, daemon=True).start()
                elif ev == "settings":
                    self._open_settings()
                elif ev == "stats":
                    self._open_settings(section="Stats")
                elif ev == "help":
                    self._open_settings(section="Help")
                elif ev == "meeting":
                    self._open_settings(section="Meeting")
                elif ev == "open_update":
                    self._update_badge.hide()
                    self._open_settings(section="About")
                elif isinstance(ev, tuple) and ev[0] == "update_available":
                    # show it INSIDE the app (Settings window), not a floating badge
                    self._pending_update = ev[1]
                    win = getattr(self, "_settings_win", None)
                    try:
                        if win is not None and win.win.winfo_exists():
                            win._show_update_banner(ev[1])
                    except Exception:
                        pass
                elif ev == "history":
                    self._open_history()
                elif ev == "clips":
                    from .clips_gui import ClipsTray
                    ClipsTray.toggle(self.root)
                elif ev == "media":
                    from .media_gui import MediaWindow
                    MediaWindow(self.root, self.transcriber, self.cfg)
                elif ev == "quit":
                    self._quit()
                    return
                elif isinstance(ev, tuple) and ev[0] == "overlay":
                    self._overlay_update(ev[1], ev[2] if len(ev) > 2 else "")
        except queue.Empty:
            pass
        self.root.after(50, self._poll)

    def _overlay_update(self, state: str, text: str = ""):
        if not self.cfg.get("overlay_enabled", True):
            return
        if state == "recording":
            self.overlay.show_recording()
        elif state == "busy":
            self.overlay.show_busy()
        elif state == "live":
            self.overlay.show_live(text)
        elif state == "result":
            self.overlay.show_result(text)
        elif state == "hide":
            self.overlay.hide()

    # ---------- dictation ----------

    def _esc_pressed(self, _e=None):
        if self.recorder and self.recorder.recording and not self._busy:
            self.events.put("cancel")

    def _cancel_dictation(self):
        if not (self.recorder and self.recorder.recording) or self._busy:
            return
        self._busy = True

        def run():
            try:
                self.recorder.stop()      # discard the audio entirely
            except Exception:
                pass
            finally:
                self._busy = False
                self._mode = "dictate"
                self._write_selection = ""
            self.events.put(("overlay", "result", "✖ Cancelled"))
        threading.Thread(target=run, daemon=True).start()

    def _toggle(self, mode="dictate"):
        if self._busy:
            return
        if self.recorder and self.recorder.recording:
            self._busy = True
            self._overlay_update("busy")
            threading.Thread(target=self._finish, daemon=True).start()
        else:
            if mode == "write":
                self._capture_selection()
            self._mode = mode
            self._begin()
            if mode == "command":
                self.events.put(("overlay", "live",
                                 "🎧 Say a command — e.g. \"open chrome\" — I'll run it when you pause"))
                threading.Thread(target=self._autostop,
                                 args=("toggle_command",), daemon=True).start()
            elif mode == "write":
                if self.cfg.get("ai_enhancement", False):
                    hint = "✍ Speak your instruction (e.g. \"make this formal\") — applies when you pause"
                else:
                    hint = "✍ AI is off: what you say will REPLACE the selection — applies when you pause"
                self.events.put(("overlay", "live", hint))
                threading.Thread(target=self._autostop,
                                 args=("toggle_write",), daemon=True).start()

    def _autostop(self, fire_event):
        """Auto-finish ~1.3s after the user stops talking (command/write modes)."""
        rec = self.recorder
        spoke = False
        last_loud = time.time()
        start = time.time()
        while rec and rec.recording and not self._busy:
            time.sleep(0.1)
            lvl = getattr(rec, "level", 0.0)
            if lvl > 0.10:
                spoke = True
                last_loud = time.time()
            if spoke and time.time() - last_loud > 1.3:
                self.events.put(fire_event)
                return
            if not spoke and time.time() - start > 15:
                self.events.put(fire_event)   # gave up waiting
                return

    def _capture_selection(self):
        """Copy whatever text is selected in the focused app (for Write Mode)."""
        self._write_selection = ""
        try:
            import keyboard, pyperclip
            time.sleep(0.35)   # let the hotkey keys come up first
            old = pyperclip.paste()
            keyboard.send("ctrl+c")
            time.sleep(0.25)
            sel = pyperclip.paste()
            if sel != old:
                self._write_selection = sel
        except Exception:
            pass

    def _maybe_warn_elevated(self):
        if self.cfg.get("admin_mode"):
            return
        try:
            from . import elevation
            if not elevation.is_self_elevated() and elevation.foreground_is_elevated():
                self.events.put(("overlay", "result",
                    "\u26a0 That app runs as administrator \u2014 turn on "
                    "Admin mode in Settings \u2192 General"))
        except Exception:
            pass

    def _begin(self):
        self._maybe_warn_elevated()
        self.recorder = Recorder(
            preferred_mic=self.cfg["preferred_mic"],
            tail_ms=self.cfg["tail_ms"],
            start_cue=self.cfg["start_cue"],
            end_cue=self.cfg["end_cue"],
            duck_media=self.cfg["duck_media"],
        )
        try:
            self.recorder.start()
            self._record_started_at = time.time()
            self._overlay_update("recording")
            if self.cfg.get("live_preview", True):
                threading.Thread(target=self._live_preview_loop, daemon=True).start()
        except Exception as e:
            self._overlay_update("result", f"Mic error: {e}")

    def _live_preview_loop(self):
        """Show words live while speaking, using the fast preview model.

        Only the most recent ~12 s is re-transcribed each pass, so the
        preview stays quick no matter how long you talk. The final text
        still comes from the full recording with your accurate model.
        """
        from .audio import SAMPLE_RATE
        rec = self.recorder
        window = 12 * SAMPLE_RATE
        while rec.recording:
            time.sleep(0.35)
            if not rec.recording or self._busy:
                break
            snap = rec.snapshot()
            if len(snap) < 8000:  # wait for ~0.5 s of audio
                continue
            try:
                partial = self.preview_transcriber.transcribe(
                    snap[-window:], self.cfg["language"])
            except Exception:
                break
            if rec.recording and partial:
                self.events.put(("overlay", "live", partial))

    def _finish(self):
        """Runs in a worker thread: stop -> transcribe -> clean -> insert."""
        try:
            audio = self.recorder.stop()
            duration = time.time() - self._record_started_at
            try:
                from . import audio_store
                audio_store.save(audio, self.cfg)
            except Exception:
                pass
            if self._mode == "command":
                from . import commands
                raw = self.transcriber.transcribe_command(
                    audio, commands.vocab_hint())
                feedback = commands.execute(raw)
                self.events.put(("overlay", "result", "🎧  " + feedback))
                return
            raw = self.transcriber.transcribe(audio, self.cfg["language"])
            prefix = self.cfg.get("command_prefix", "computer")
            if (self.cfg.get("prefix_commands", True) and prefix
                    and raw.strip().lower().startswith(prefix.lower())):
                from . import commands
                rest = raw.strip()[len(prefix):].lstrip(" ,.:;!")
                feedback = commands.execute(rest)
                self.events.put(("overlay", "result", "🎧  " + feedback))
                return
            if self._mode == "write":
                self._finish_write(raw)
                return
            text = cleanup.process(raw, self.cfg, self.dictionary)
            if text:
                injector.insert(text, self.cfg["insertion_mode"])
                if (self.cfg.get("always_copy", True)
                        and self.cfg["insertion_mode"] != "clipboard"):
                    try:
                        import pyperclip
                        pyperclip.copy(text)  # safety net: always re-pasteable
                    except Exception:
                        pass
                history.add(text, duration, self.cfg)
                self._last_text = text
                shown = ("Copied to clipboard: " + text
                         if self.cfg["insertion_mode"] == "clipboard" else text)
                self.events.put(("overlay", "result", shown))
            else:
                self.events.put(("overlay", "result", "(heard nothing)"))
        except Exception as e:
            self.events.put(("overlay", "result", f"Error: {e}"))
        finally:
            self._busy = False
            self._mode = "dictate"

    def _finish_write(self, instruction: str):
        """Write Mode: rewrite the captured selection (AI) or replace it."""
        sel = self._write_selection
        result = ""
        if sel and self.cfg.get("ai_enhancement", False):
            base = dict(self.cfg)
            base["ai_prompt"] = (
                "You rewrite text. Apply the user's spoken instruction to the "
                "text between <text> tags. Return ONLY the rewritten text.")
            result = cleanup.ai_enhance(
                f"Instruction: {instruction}\n<text>{sel}</text>", base)
            if result.strip() == f"Instruction: {instruction}\n<text>{sel}</text>".strip():
                result = ""  # AI unavailable - fall through
        if not result:
            # no AI (or no selection): treat speech as replacement text
            result = cleanup.process(instruction, self.cfg, self.dictionary)
        if result:
            injector.insert(result, "paste")
            history.add(result, 0.0, self.cfg)
            self.events.put(("overlay", "result", "✍  " + result))
        else:
            self.events.put(("overlay", "result", "(heard nothing)"))

    # ---------- windows ----------

    def _open_settings(self, section=None):
        from .settings_gui import SettingsWindow
        win = getattr(self, "_settings_win", None)
        if win is not None:
            try:
                if win.win.winfo_exists():
                    win.show_section(section)   # None = just bring to front
                    return
            except Exception:
                pass
        self._settings_win = SettingsWindow(
            self.root, self.cfg, self.dictionary,
            self._on_settings_saved,
            on_media=lambda: self.events.put("media"),
            on_clips=lambda: self.events.put("clips"),
            on_history=lambda: self.events.put("history"),
            on_quit=lambda: self.events.put("quit"),
            initial_section=section)

    def _on_settings_saved(self, cfg):
        self.cfg = cfg
        from . import theme as _theme1
        _theme1.set_mode(cfg.get("theme", "dark"))
        self.transcriber.set_model(cfg["model"])
        self.preview_transcriber.set_model(cfg.get("preview_model", "tiny"))
        from .update_badge import UpdateBadge
        self._update_badge = UpdateBadge(self.root, lambda: self.events.put("open_update"))

        self._register_activation()
        self._refresh_idle_hint()
        self.overlay.show_idle()
        threading.Thread(target=self._warm_model, daemon=True).start()

    def _open_history(self):
        from .history_gui import ClipboardWindow
        ClipboardWindow(self.root)



    def _quit(self):
        try:
            if getattr(self, "tray", None):
                self.tray.stop()
        except Exception:
            pass
        try:
            import keyboard
            keyboard.unhook_all()
        except Exception:
            pass
        try:
            self.root.quit()
        except Exception:
            pass
        # Hard-exit: releases the single-instance mutex and unlocks app files
        # right away, so an update installer can replace + relaunch cleanly.
        import os
        os._exit(0)


def _already_running() -> bool:
    """Windows named mutex - prevents two EchoQuills fighting over the CPU.

    During an update the outgoing instance is exiting, so if an update marker
    is fresh we wait up to ~15s for the lock to clear instead of refusing."""
    try:
        import ctypes, os, time
        k = ctypes.windll.kernel32
        NAME = "EchoQuill_SingleInstance"
        # is an update in progress? (marker written by update.download_and_run)
        deadline = time.time()
        try:
            from .config import app_data_dir
            marker = app_data_dir() / "update_in_progress"
            if marker.exists() and (time.time() - marker.stat().st_mtime) < 300:
                deadline = time.time() + 15
        except Exception:
            marker = None
        while True:
            h = k.CreateMutexW(None, False, NAME)
            if k.GetLastError() != 183:      # 183 = ERROR_ALREADY_EXISTS
                # fresh lock acquired -> we are the only instance. Keep the
                # handle open for the life of the process (intentional leak).
                try:
                    if marker is not None and marker.exists():
                        marker.unlink()
                except Exception:
                    pass
                return False
            k.CloseHandle(h)                 # don't keep the stale lock alive
            if time.time() >= deadline:
                return True
            time.sleep(0.4)
    except Exception:
        return False


def main():
    if _already_running():
        try:
            import ctypes
            ctypes.windll.user32.MessageBoxW(
                None, "EchoQuill is already running - look for the blue mic "
                "pill at the bottom of your screen.", "EchoQuill", 0x40)
        except Exception:
            pass
        return
    # keep the video engine (yt-dlp) current: use the newest downloaded copy,
    # and refresh it in the background so YouTube changes don't break us.
    try:
        from . import ytdlp_updater
        ytdlp_updater.activate()
        import threading
        threading.Thread(target=lambda: ytdlp_updater.ensure(), daemon=True).start()
    except Exception:
        pass
    App().run()


if __name__ == "__main__":
    main()
