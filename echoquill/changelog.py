"""In-app changelog shown in Settings -> What's New."""

TEXT = """EchoQuill - What's New
Newest first. Pro = 2.x, Free = 1.x. (F x.y.z) marks the matching Free release.

============================================================
READ ALOUD, PHONE & POLISH  -  July 15-16, 2026
============================================================

v2.14.2  (Jul 16)
 - Fixed: the Read-aloud window was missing its "Convert to audio"
   button (its layout had reverted); restored to match Settings.

v2.14.1  (Jul 16)
 - Read aloud: plain 1-2-3 instructions; "Open a document" renamed
   "Load a document"; box labelled "Text to convert to audio".
 - Recent transcriptions now work like the Clips tray: drag a line
   onto any text box to drop it, or click to paste into your last app.

v2.14.0  (Jul 15)
 - "Listen on my phone": a QR code serves your narrations over your
   local WiFi. Scan it, tap to stream or download - no accounts, no
   cloud, private (random-token link), with seek/scrub support.

v2.13.0 - v2.13.5  (Jul 15)
 - Read-aloud audio player: Play/Pause, Stop, and a draggable timeline
   to scrub and relisten. Audio is generated once (one charge) - pause,
   seek and replay are free.
 - "Save narrations to..." - point Read aloud at any folder (e.g. a
   OneDrive / Google Drive / Dropbox folder). "Use default" to reset.
 - A clear "Convert to audio" button (Play no longer secretly generates).
 - Fixes: "Permission denied" on a 2nd render (unique temp file each
   time); right-click menu crash; double scrollbar in Meeting/Read aloud.

v2.12.0 - v2.12.6  (Jul 15)
 - NEW: Read aloud (Text-to-speech). Paste text or load a .txt/.md/
   .docx/.pdf, pick an ElevenLabs voice, then Play or Save as MP3 into
   Documents/EchoQuill/Narration. Its own Settings section + tray/overlay
   shortcuts. Uses your own ElevenLabs key (kept in Credential Manager).
 - Cost guard: live character counter + a "this will use ~N credits,
   continue?" confirmation before generating.
 - Scrollbars app-wide: one clean piece, a medium-gray auto-sizing thumb
   visible on light AND dark (the old one was white/invisible in light).
 - Reliability: the event loop is now unkillable - one bad window can no
   longer freeze the whole app; every crash is written to crash.log.
 - Playback reworked to need no ffmpeg; failures now show a dialog.

============================================================
FOLDERS, ASK AI & CLEANUP  -  July 14-15, 2026
============================================================

v2.11.0  (F 1.22.0)  (Jul 15)
 - Delete folders, plus folder controls (add / remove / delete) right
   in the edit dialog; assignment follows the text when you edit it.
 - Preset dropdowns show the full question text on hover; Meeting preset
   menu trimmed to a compact width.

v2.10.0  (F 1.21.0)  (Jul 14-15)
 - Ask AI now re-binds to the CURRENT video (fixes answering about an
   older transcript).
 - Folders in the Clips tray AND Recent transcriptions, with a custom
   new-folder dialog; the Clipboard gets its own Clips folder.
 - Standardized button bars across Transcriber, Batch, Meeting, Ask AI.

v2.6 - v2.9  (F 1.17 - 1.20)  (Jul 13-14)
 - Meeting / Record: capture what you HEAR on the PC (calls, webinars,
   any playing video incl. Skool) + optional mic and screen video, then
   transcribe locally. Ask AI presets you can add/edit/delete.
 - Recent transcriptions made lazy/paged (snappy with thousands).
 - Every text box scrolls internally; real visible scrollbars.
 - Sign-in helper for YouTube bot-checks, Skool & member-only videos.
 - Ollama Cloud model list fixed; AI timeouts raised for slow models.
 - Auto-updater fixes; per-user install that survives upgrades.

============================================================
EDITING, THEMES & AI  -  July 13-14, 2026
============================================================

v2.4  (F 1.16)
 - "?" help icons on the Clips, Transcriber and Ask AI windows.
 - Edit clips right in the tray; edit button kept fully on-screen.

v2.3  (F 1.15)
 - Auto update-check twice daily + a green corner badge; one-click
   update straight from GitHub.

v2.2  (F 1.14)
 - Edit and save transcription text.
 - Drag-and-drop an audio/video file onto the window to auto-transcribe.
 - Light / dark / system theme; optional saved recording history.

v2.1  (F 1.13.19-23)
 - Manage transcriptions: multi-select, Select all, Delete selected/all.
 - Stop button on the transcriber and on batch.
 - Editable dictionary entries.
 - API/license keys stored in Windows Credential Manager (survive updates).

v2.0  (F 1.13.11-18)
 - Optional Administrator mode + a warning when dictating into elevated
   apps.
 - AI enhancement is opt-in and fails fast so it can't stall dictation;
   current model line-up with "thinking" labels and fast defaults.
 - Each transcription window uses its own engine so it never blocks
   dictation.
 - Press ESC to cancel an in-progress dictation.
 - Self-cleaning installer; icon-cache refresh; in-app Feedback page.

For the full commit-by-commit history, see the Releases page on GitHub.
"""
