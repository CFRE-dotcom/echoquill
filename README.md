<div align="center">

# 🎙 EchoQuill

### Speak anywhere you can type. Free. Offline. Private.

**Voice dictation for Windows that keeps your voice on your computer** — powered by local Whisper AI.
No subscription. No account. No audio ever uploaded.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
![Platform](https://img.shields.io/badge/Windows-10%20%7C%2011-0a84ff)
![Engine](https://img.shields.io/badge/engine-Whisper%20(local)-brightgreen)
![Price](https://img.shields.io/badge/price-free%20forever-success)

**[⬇ Download for Windows](../../releases/latest)** · **[Website](https://echo-quill.com)** · **[Report an issue](../../issues)**

*If EchoQuill saves you time, a ⭐ star helps more people find it.*

</div>

---

## Why EchoQuill?

Speaking is ~3x faster than typing. The paid dictation apps know it — and charge monthly for it, while routing your voice through their servers. EchoQuill does what they do, free and offline:

| | EchoQuill | Wispr Flow | Dragon |
|---|---|---|---|
| Price | **Free forever** | $12+/mo | $200–700 |
| Works offline | **Yes** | No | Partly |
| Voice leaves your PC | **Never** | Yes | Configurable |
| Open source | **Yes (MIT)** | No | No |
| Live words while you speak | **Yes** | Yes | Yes |
| Voice-control your PC ("open chrome", "volume up") | **Yes** | No | Yes |
| Rewrite selected text by voice | **Yes** | Yes | Limited |
| Video/YouTube transcription | **Yes** | No | No |
| Batch: transcribe a whole list of URLs | **Yes** | No | No |
| Timestamped transcript search | **Yes** | No | No |
| Clipboard manager with drag & drop | **Yes** | No | No |
| Dictionary that learns your corrections | **Yes** | Yes | Yes |
| Per-app tone (casual in Slack, formal in Outlook) | **Yes** | Yes | No |
| Choose your AI (Claude, OpenAI, Groq, free local Ollama) | **Yes** | No | No |
| One-click self-update | **Yes** | Yes | Yes |

## What it does

**🎙 Live dictation, anywhere** — press `Ctrl+Alt+Space`, talk, and your words appear live in a floating pill, then land wherever your cursor is: email, Word, browsers, chat, code editors. Prefer push-to-talk? Hold Right Alt instead.

**🎧 Voice-control your PC** — say *"computer, open chrome"*, *"search for foreclosure listings"*, *"press enter"*, *"volume up"*, *"lock the computer"*. Recognition is primed with the command vocabulary, and only a fixed, safe list of actions can ever run.

**✍ Rewrite anything by voice** — highlight text in any app, press `Ctrl+Alt+W`, and say *"make this more professional."* The selection is rewritten in place.

**🎬 Turn videos into text** — paste a link from YouTube (including Shorts) or ~1,800 other sites, or pick any media file. Transcripts auto-save, named after the video, with title + URL on top. Batch mode chews through a whole list of URLs unattended. Search a transcript and matches report *when* they were said: `4 matches — at 02:14, 05:37, 11:02`.

**📋 Clips tray** — your recent dictations in a draggable floating tray. Click a clip to paste it at your cursor, drag one into any window to drop it there, search to find old ones.

**📖 A dictionary that learns** — names, jargon, and brands always come out right, and repeated corrections become dictionary entries automatically.

**🤖 Optional AI polish** — plug in Anthropic Claude, OpenAI, Groq, Ollama (free, local), or Ollama Cloud for smarter cleanup — with different tone per app: casual in Slack, formal in Outlook. Off by default; your keys are stored in Windows Credential Manager.

**⬆ Updates itself** — one click in Settings → About when a new version ships.

Plus: spoken punctuation, mic lock, media ducking, never-miss-the-first-word cueing, adjustable tail capture, daily/weekly/monthly stats, full data export, and a first-run tour so you're dictating in under a minute.

## Install (30 seconds)

1. Download **EchoQuill-Setup.exe** from the [latest release](../../releases/latest)
2. Run it (Windows may show "unrecognized app" — click *More info → Run anyway*; the entire source code is right here for inspection)
3. Press `Ctrl+Alt+Space` and start talking

Requirements: Windows 10/11 + a microphone. First dictation downloads a speech model (~140 MB) once; after that it's fully offline. NVIDIA GPU = faster, but optional.

## Privacy, verifiable

- Voice, transcripts, history, dictionary: **processed and stored only on your computer**
- **Zero** analytics, telemetry, or tracking — read the code, it's all here
- Network is used only for: one-time model downloads, video URLs *you* paste, update checks, and AI providers *you* enable with your own key (stored in Windows Credential Manager)

Details: [SECURITY.md](SECURITY.md)

## EchoQuill Pro

Free covers unlimited dictation forever, 5 video transcriptions, and your last 10 clips. **Pro** — unlimited video transcription, an unlimited clip library with a Favorites tab, and priority support — is coming soon at **$5/month or $39/year** at [echo-quill.com](https://echo-quill.com/#pricing). Star + Watch this repo to catch the launch.

## Building from source

```bash
git clone https://github.com/CFRE-dotcom/echoquill.git
cd echoquill
install.bat        # one-time dependency setup (Python 3.10+)
EchoQuill.bat      # run from source
build_exe.bat      # or build your own EchoQuill.exe
```

Releases are compiled automatically by GitHub Actions from the tagged source — what you download is what you see here.

## Contributing

Issues and PRs welcome. One focused change per PR; open an issue first for anything non-trivial.

## License & credits

[MIT](LICENSE) — free for everyone, forever.
Speech recognition: [OpenAI Whisper](https://github.com/openai/whisper) via [faster-whisper](https://github.com/SYSTRAN/faster-whisper) · Video downloads: [yt-dlp](https://github.com/yt-dlp/yt-dlp) · Inspired by [FluidVoice for macOS](https://github.com/altic-dev/FluidVoice) (independent project, not affiliated)
