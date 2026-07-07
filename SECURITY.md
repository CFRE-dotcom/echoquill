# Security notes

EchoQuill is local-first by design. This page states exactly what it does and
does not do, so users and reviewers can verify the claims against the source.

## What never leaves your computer
- Your voice and microphone audio (processed locally by faster-whisper)
- Transcribed text, history, stats, and dictionary (stored under %APPDATA%\EchoQuill and Documents\EchoQuill Transcriptions)
- No analytics, no telemetry, no crash reporting, no auto-update phone-home

## Network access happens only when YOU trigger it
- One-time speech-model downloads (from Hugging Face, by faster-whisper)
- Optional AI enhancement: requests go only to the API base URL you configured
- Video transcription: yt-dlp downloads audio from the URL you pasted

## Credentials
- Your optional AI API key and Pro license key are stored in the Windows
  Credential Manager (the OS per-user secure vault) - never written to disk in plain text.

## Command Mode safety
- Only a fixed allow-list of applications and key presses can be executed.
- Arbitrary shell commands from speech are never run; unrecognized phrases
  are displayed back, not executed.

## Known considerations
- The global-hotkey library uses a low-level keyboard hook (that is how every
  dictation hotkey works). It does not log or store keystrokes.
- The packaged .exe is unsigned; Windows SmartScreen may warn until the
  project accumulates reputation or a code-signing certificate is added.

## Reporting
Found something? Please open a GitHub issue (or a private security advisory).
