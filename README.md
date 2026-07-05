# EchoQuill

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
![Platform](https://img.shields.io/badge/Windows-10%20%7C%2011-0a84ff)
![Engine](https://img.shields.io/badge/engine-Whisper%20(local)-brightgreen)
![Price](https://img.shields.io/badge/price-free%20forever-success)

Free, open-source, local-first voice-to-text dictation for Windows. Your voice is the echo; the quill does the writing.

Press one hotkey, speak, and your words appear in whatever app you're using — email, Word, chat, browser, anywhere you can type. Everything runs on your own computer: no subscription, no account, no audio ever leaves your machine.

## Features

- **One hotkey, any app** — default `Ctrl+Alt+Space`. Press to start, press to stop; text lands in the focused text field.
- **Hold-to-talk mode** — or switch Activation to *hold* in Settings and just hold a key (default: Right Alt) while you speak, release to finish — like holding Option on the Mac app.
- **Live preview** — words appear in the on-screen overlay *while you speak*, then the final cleaned text drops into your app.
- **100% local speech recognition** — powered by [faster-whisper](https://github.com/SYSTRAN/faster-whisper), the free open-source Whisper engine. Works offline after the one-time model download.
- **Speed settings** — pick a model size from *tiny* (near-instant) to *large-v3* (best accuracy, 99 languages).
- **Custom dictionary** — add names, jargon, and phrases it should always get right.
- **Learns from your corrections** — repeated fixes become dictionary entries automatically (optional).
- **Local text cleanup** — capitalization, spacing, and sentence punctuation, fully offline.
- **Spoken punctuation** — say "period", "comma", "new line", "new paragraph".
- **Optional AI enhancement** — off by default. Bring your own OpenAI/Groq key, or point it at a free local LLM (Ollama, LM Studio) for smarter cleanup with zero cloud.
- **Per-app tone** — different AI cleanup instructions per application (casual in Slack, formal in Outlook).
- **On-screen overlay** — a small pill shows listening / transcribing status and a preview of the result.
- **History and daily stats** — local-only log of dictations, words per day, and estimated time saved vs typing.
- **System tray app** — start/stop, settings, and stats from the tray icon.
- **Clips tray** — a draggable pop-up panel with your 10 most recent transcriptions; click any clip to copy it again (right-click the mic pill → Clips tray).
- **Clipboard safety net** — every transcription is also left on the clipboard, so if text landed in the wrong place, just Ctrl+V where you meant.
- **Command Mode** — control your PC by voice (Ctrl+Alt+C): "open chrome", "search for …", "press enter", "volume up", "lock the computer". Safe by design: only known actions run; anything else is shown back to you.
- **Write Mode** — select text in any app, press Ctrl+Alt+W, and speak: with AI enhancement on, your instruction rewrites the selection ("make this more formal"); without AI, your words replace it.
- **Batch video transcription** — paste many URLs, and each is transcribed one at a time and auto-saved as *video title*.txt in Documents\EchoQuill Transcriptions.
- **Start with Windows** — one checkbox in Settings (or via the installer).
- **Video & URL transcription** *(free version includes 5 video transcriptions; dictation and everything else is unlimited and free forever)* — right-click the pill → *Transcribe video / URL*: paste a YouTube (or most sites) link or pick a video/audio file on your PC and get the full transcript to copy or save. Same free local engine, nothing uploaded.

### Fine-tuning details

- **Never miss the first word** — the ready-cue plays only after the microphone is actually live.
- **Never lose the last word** — an adjustable "tail" keeps recording briefly after you stop.
- **Microphone lock** — always use your chosen mic even if Windows switches the default.
- **Media ducking** — other apps' audio is lowered (not paused) while you dictate, then restored.
- **Clipboard-only mode** — if you prefer, nothing is typed for you; the text is just copied, ready to paste.
- **Everything is optional** — all cleanup, AI, history, and cues can be switched off.

## Easiest install: download the .exe

If a release is available on the [Releases page](../../releases), just download **EchoQuill-Setup.exe** and run it — it installs to Program Files with a Start Menu shortcut, optional desktop icon, optional start-with-Windows, and a normal uninstaller. Or grab the portable **EchoQuill.exe** and run it from anywhere, no install needed.

> **Maintainers:** releases build themselves. Publishing a GitHub release triggers `.github/workflows/build.yml`, which compiles `EchoQuill.exe` and `EchoQuill-Setup.exe` on GitHub's free Windows servers and attaches both to the release. To build locally instead, run `build_exe.bat` (and optionally compile `installer.iss` with [Inno Setup](https://jrsoftware.org/isinfo.php)).

## Install from source (about 2 minutes)

1. Install **Python 3.10 or newer** from [python.org/downloads](https://www.python.org/downloads/). During install, check **"Add python.exe to PATH."**
2. Download this project (green **Code** button → **Download ZIP**) and unzip it anywhere.
3. Double-click **`install.bat`** and wait for it to finish (one time only).
4. Double-click **`EchoQuill.bat`** — the mic icon appears in your system tray.
5. Click into any text field, press **Ctrl+Alt+Space**, talk (watch your words appear live in the overlay), press it again. Done. Prefer holding a key while you talk? Settings → General → Activation → hold.

The first dictation downloads the speech model (~140 MB for the default "base" model); after that it's fully offline.

> **Tip:** to have it start with Windows, press `Win+R`, type `shell:startup`, and put a shortcut to `EchoQuill.bat` in that folder.

## Speed / accuracy settings

Open **Settings → General → Speed / accuracy** from the tray icon:

| Model | Best for | Download |
|---|---|---|
| tiny | Fastest, quick notes | ~75 MB |
| base | Everyday balance (default) | ~140 MB |
| small | More accurate | ~460 MB |
| medium | Very accurate, decent PC needed | ~1.5 GB |
| large-v3 | Best accuracy, 99 languages | ~3 GB |

If your PC has an NVIDIA GPU, transcription automatically uses it and is much faster.

## Privacy

- Your voice and text are processed **on your computer** and never uploaded.
- No analytics, no telemetry, no accounts.
- The only network use is the one-time model download — unless *you* enable cloud AI enhancement with your own API key.

## Contributing

Issues and pull requests are welcome. Please open an issue first for non-trivial changes. Keep PRs focused: one feature or fix per PR.

## License

[MIT](LICENSE) — free for everyone, forever.

## Credits

- Speech recognition: [OpenAI Whisper](https://github.com/openai/whisper) via [faster-whisper](https://github.com/SYSTRAN/faster-whisper)
- Inspired by [FluidVoice for macOS](https://github.com/altic-dev/FluidVoice) by the Altic team (independent project, not affiliated)
