EchoQuill - Complete Change History
Every tagged release, newest first. Pro (2.x) and Free (1.x).
For anything not listed, see the Releases page on GitHub.

============================================================
ECHOQUILL PRO
============================================================

v2.15.0  (2026-07-16)
    Settings cleanup + What's New. Scroll panes auto-hide when content fits (no more pointless bars on Stats/License/About); the text-box sections (Transcription, History, Help, Feedback, Dictionary) drop the outer pane so only the box's own scrollbar shows - no more double bars. Help updated with Meeting, Read aloud & phone. New 'What's New' section shows the full changelog (Pro + Free) in a scrollable box; CHANGELOG.md added.

v2.14.2  (2026-07-16)
    FIX - the standalone Read-aloud window was missing the '🎙 Convert to audio' button (its layout had reverted in an earlier reset while the instructions still referenced it). Restored: 'Load a document' + 'Convert to audio' sit together above the text box, matching the Settings section.

v2.14.1  (2026-07-16)
    (1) Read-aloud clarity - plain 1-2-3 instructions, 'Open a document' -> 'Load a document', 'Text to convert to audio' label, clearer tooltips. (2) Recent transcriptions now work like the Clips tray: drag a line onto any text box to drop it, or click to paste into your last app.

v2.14.0  (2026-07-15)
    'Listen on my phone' - a button in Read-aloud shows a QR code; scan it on a phone on the same WiFi to open a little page listing your narrations (stream or download). Local-network only, random-token URL, Range/seek streaming, no accounts, no cloud, no matching logins needed.

v2.13.5  (2026-07-15)
    fix double scrollbar in Meeting and Read-aloud - those sections no longer sit inside an outer scroll pane, so the transcript box's own internal scrollbar is the only one (matches the standalone windows).

v2.13.4  (2026-07-15)
    Read-aloud layout - 'Open a document' and 'Convert to audio' now sit together right above the text (natural open->convert flow); Voice + Load voices on their own row. Window width unchanged.

v2.13.3  (2026-07-15)
    'Save narrations to...' - point Read-aloud at any folder (e.g. a OneDrive/Drive/Dropbox synced folder) so MP3s appear on your phone automatically. Becomes the default; 'Use default' disconnects back to Documents/EchoQuill/Narration. In both the window and Settings.

v2.13.2  (2026-07-15)
    Read-aloud gets a clear '🎙 Convert to audio' button (Play no longer secretly generates) + the 2.13.1 fixes (unique temp file per render; right-click menu parented to the clicked field).

v2.13.1  (2026-07-15)
    fix two Read-aloud bugs - (1) 'Permission denied ...readaloud.wav' on a 2nd transcript: each render now writes a unique temp file and the player deletes the previous one (the open file was locked). (2) crash-log 'bad window path name' on right-click: the Cut/Copy/Paste menu is now parented to the field you clicked instead of a possibly-closed window.

v2.13.0  (2026-07-15)
    Read-aloud audio player - Play/Pause, Stop, and a seekable timeline you can drag to scrub/relisten. Built on Windows MCI (ctypes/winmm) - no new deps, no ffmpeg. Audio is generated once (one charge); pause/seek/replay are free. In both the window and the Settings section.

v2.12.6  (2026-07-15)
    scrollbars app-wide - one clean piece (no arrow buttons), medium-gray auto-sizing thumb that's visible on light AND dark (was white/invisible in light mode), accent colour while dragging.

v2.12.5  (2026-07-15)
    Read-aloud cost guard - live character counter + a 'this is N characters (~N ElevenLabs credits), generate anyway?' confirmation before any generation over 5k chars, in both the window and the Settings section. Stops surprise credit burns.

v2.12.4  (2026-07-15)
    CRITICAL - make the event loop unkillable. _poll only caught queue.Empty, so ANY exception in a window/handler killed the whole loop (dictation + every menu action dead, pill still visible). Now each event is isolated; crashes are logged to crash.log and the app keeps running. Adds tk report_callback_exception logging.

v2.12.3  (2026-07-15)
    FIX blank Settings panel - _build_read_aloud used helptip without importing it (NameError aborted the whole section build). Add scripts/check_undefined.py (pyflakes) + CI guard so a missing import can never blank a panel again.

v2.12.2  (2026-07-15)
    fix Read-aloud playback/save - drop ffmpeg entirely (raw PCM -> winsound for Play, direct MP3 concat for Save); every failure now pops a dialog and writes tts_error.log. This fixes 'made N chunks then nothing happened'.

v2.12.1  (2026-07-15)
    add 'Read aloud' as its own section in the Settings sidebar (next to Meeting), in addition to the existing tray + overlay shortcuts

v2.12.0  (2026-07-15)
    Read aloud (Text-to-speech) - paste text or open a .txt/.md/.docx/.pdf, pick an ElevenLabs voice, Play or Save as MP3 into Documents/EchoQuill/Narration. Pro, bring-your-own ElevenLabs key (kept in Credential Manager). Menu entries in tray + overlay.

v2.11.0  (2026-07-15)
    delete folders + folder controls in the edit dialog (add/remove/delete, migrates on save); preset dropdowns show full text on hover + Meeting menu truncated to compact width; copy/paste + right-click fixed in all fields (direct clipboard handlers, selection captured before menu opens)

v2.10.0  (2026-07-14)
    Ask AI re-binds to current video (fix cross-video mix-up); folders in Clips + Recent (custom 30-char dialog); Clips folder + Save/Open; standardized button bars; Meeting preset word-wrap + pinned Ask

v2.9.3  (2026-07-14)
    Ask AI about this video now reads the video's title + URL + full transcript (not the description). Answers plainly with only what's present - no 'not found'/negative filler, no invented links. Plus: saved Q&A blocks are separated by two rows of 50 asterisks.

v2.9.2  (2026-07-14)
    Approved batch: fix Ollama Cloud model list (kimi-k2.7 -> kimi-k2.7-code, verified against ollama.com; default -> qwen3.5), raise AI timeout 45->180s (gpt-oss:120b/thinking models were timing out). Ask AI presets: manager moved to the BOTTOM of the dropdown (add/edit/delete your own; defaults locked). Add Clear + Open-folder to 'Ask AI about this video'. Real always-visible right-side scrollbar on every text box (safe wrapper, no freeze).

v2.9.1  (2026-07-14)
    Revert the self-updating yt-dlp engine (2.8.0). Evidence: the YouTube download code is byte-identical to the last known-good version, so the only thing that changed was the engine version. The auto-updater force-swapped the bundled yt-dlp for the newest (most locked-down) copy on every launch. Back to the bundled engine; removed the Update-engine/Restart UI. Cookies paste box kept.

v2.9.0  (2026-07-14)
    Quality pass (2.9.0): verified every UI button/handler is wired (whole-app static scan, now enforced in CI so a broken build can't publish). Confirmed Ollama Cloud (ollama.com/api, gpt-oss:20b), Meeting Ask-AI presets, and Clips folders are all correctly hooked up. Restart button + simplified single sign-in retained. No new features - correctness + coherence.

v2.8.3  (2026-07-14)
    Clarify cookies: use the extension's 'Export All Cookies' so ONE file covers every logged-in site (YouTube AND Skool), since they use different cookies. v2.8.3

v2.8.2  (2026-07-14)
    Add a real Restart button after engine updates (shows only when a restart is needed; app relaunches itself). Simplify Transcription: one sign-in method (paste cookies, covers YouTube+Skool+member-only) instead of two overlapping ones. Clarify that the 'do not edit' header in cookies is normal. v2.8.2

v2.8.1  (2026-07-14)
    Fix right-click Cut/Copy/Paste: menu now calls grab_release (it was flashing shut on Windows) and focuses the field so Paste lands there. Also bind middle-click. Right-click paste works in all text fields now. v2.8.1

v2.8.0  (2026-07-14)
    Self-updating video engine: EchoQuill now pulls the latest yt-dlp (pure-python wheel) into AppData and uses it, auto-refreshing on launch + an 'Update engine now' button — so YouTube changes stop breaking downloads. Redo YouTube cookies as a paste box with Save/Clear (paste exported cookies straight in). v2.8.0

v2.7.7  (2026-07-14)
    YouTube auth: Chrome locks/encrypts its cookie DB (yt-dlp #7271). Add a Cookies file (cookies.txt) option in Settings > Transcription (most reliable, works around Chrome), prefer it over browser cookies, and give a plain-language error pointing to Firefox or a cookies.txt. v2.7.7

v2.7.6  (2026-07-14)
    YouTube 'confirm you're not a bot' errors now show plain guidance in the transcriber + batch: turn on Settings > Transcription > Sign in via browser. (This is YouTube's anti-bot escalation; cookies-from-browser is the fix and is already supported.) v2.7.6

v2.7.5  (2026-07-14)
    CRITICAL: define _preset_add_current/_preset_remove_current (the +/trash buttons referenced them but they were never added). Their absence threw AttributeError while building the Meeting panel, blanking the entire Settings window from Meeting onward (incl. AI Enhancement). Settings renders fully again. v2.7.5

v2.7.4  (2026-07-14)
    Fix Ollama Cloud default model (was a non-Ollama 'gemini-3' id -> real gpt-oss:20b + catalog ids). Add +/trash inline preset save/remove to the video 'Ask AI about this video' (parity with Meeting). v2.7.4

v2.7.3  (2026-07-14)
    HOTFIX: revert the auto-scrollbar in dark_text — packing a scrollbar inside the yscrollcommand callback caused an infinite Tk geometry loop that froze the whole app (windows wouldn't open, menu/quit dead). Text boxes scroll via wheel again; will re-add visible scrollbars the safe wrapped way later. v2.7.3

v2.7.2  (2026-07-14)
    Clips vault (Pro): folders in the Favorites tab — a Folder filter + per-clip move-to-folder (type a name to create). Meeting: inline + save / trash-remove preset buttons instead of a separate manage dialog. v2.7.2

v2.7.1  (2026-07-14)
    Fix AI 404 with Ollama Cloud: ollama.com only serves the native /api/chat (not OpenAI /v1). New ai_call routes native for ollama.com and any /api base; OpenAI-compat otherwise. Ollama Cloud default + saved URLs migrated to https://ollama.com/api. Applies to dictation cleanup, Ask-AI and the editor. v2.7.1

v2.7.0  (2026-07-14)
    Tooltips: only one open at a time, always closes on leave (poll catches missed leaves). Real visible auto-scrollbars on every text box. Meeting: '?' help by the title, clearer 'Name this meeting/recording' label. Ask AI replaces Summarize in Meeting + preset-question dropdown (with add/remove your own) in both Meeting and the video transcriber. v2.7.0

v2.6.6  (2026-07-14)
    Perf + UX: Recent transcriptions now lazy/paged (only the visible page is parsed — snappy with thousands). Every text box scrolls internally (wheel scrolls the text, not the page) app-wide. v2.6.6

v2.6.5  (2026-07-14)
    Meeting tab overhaul: tooltips everywhere, Name required before Start, Save opens in Meetings folder, added Copy/Open-folder/Clear (parity with transcriber), fixed-height text box so action buttons are always visible + internal scrolling, temp-file cleanup after screen recording, add Clips subfolder. v2.6.5

v2.6.4  (2026-07-13)
    Meeting capture fix: init COM multithreaded (MTA) on the WASAPI thread and pick the loopback device robustly - fixes 'Nothing captured'. Clearer diagnostics (no-audio vs silence). v2.6.4

v2.6.3  (2026-07-13)
    Installer: per-user install (PrivilegesRequired=lowest) so silent auto-updates need no admin - fixes 'DeleteFile failed code 5 Access denied' in Program Files. Add Meeting/Record to the pill + tray menus. Make Meeting a Pro feature (free shows it locked with Upgrade to Pro). v2.6.3

v2.6.2  (2026-07-13)
    Fix Meeting recording error 0x800401F0 (CoInitialize the WASAPI capture thread). Organize output into one Documents/EchoQuill folder with subfolders (Transcriptions, Meetings); meeting transcripts + recordings save to Meetings. v2.6.2

v2.6.1  (2026-07-13)
    Meeting/Record: add 'Also capture the screen' — records desktop video (ffmpeg gdigrab) + system audio, muxes to MP4, and transcribes. Turns it into a full Zoom/Meet/webinar recorder, not just audio. Bundles ffmpeg via imageio-ffmpeg. v2.6.1

v2.6.0  (2026-07-13)
    New Meeting/Record tab: capture system audio (+ optional mic) and transcribe locally - works for calls, webinars, and any playing video incl. Skool (no URL). Adds AI 'Summarize' + save. Sidebar reordered: General, then services A-Z (incl. Meeting), then History/Stats, then License/Help/Feedback/About. v2.6.0

v2.5.8  (2026-07-13)
    Transcriber layout: put Keep audio / Keep video checkboxes and Find in transcript on one row (fills the empty right side). v2.5.8

v2.5.7  (2026-07-13)
    Keep video file: now downloads the video FIRST (before the long transcription) so the signed Skool link is still valid, with visible status and a saved-file note. Uses a mergeless 'best' format so it works without extra ffmpeg steps. v2.5.7

v2.5.6  (2026-07-13)
    Transcriber: optional 'Name this transcript' box. Leave blank for the video's own title; type a name and the transcript (and any kept audio/video) saves under it automatically - ideal for Skool videos that have no title. v2.5.6

v2.5.5  (2026-07-13)
    Transcriber: add 'Keep audio file' and 'Keep video file' checkboxes (default OFF). Keeps the downloaded audio and/or downloads the full video into the transcripts folder, with Skool Referer + browser-cookies support. v2.5.5

v2.5.4  (2026-07-13)
    Skool support: auto-add Referer/Origin for skool.com and .m3u8 (signed HLS), plus optional 'Sign in via browser' (yt-dlp cookies-from-browser) for member-only videos. Settings > Transcription dropdown + help text. v2.5.4

v2.5.3  (2026-07-13)
    Update install now runs the installer via a hidden waiter that starts only AFTER EchoQuill has fully exited - fixes the green banner 'close all instances' / app-not-closing race. Fixes both the banner and the About button routes. v2.5.3

v2.5.2  (2026-07-13)
    Recent transcriptions: drop the static caption line, add a hover '?' help next to the title (consistent with the other windows). Real per-icon tooltips remain. v2.5.2

v2.5.1  (2026-07-13)
    Fix tooltips not showing inside scrolling lists (ignore the spurious mouse-leave when the tip window maps; delayed cursor-anchored tooltip). Add tooltips across all windows: transcriber, batch, Ask AI, recent-transcriptions paging/tabs/delete, clips tabs/close. v2.5.1

v2.5.0  (2026-07-13)
    Recent transcriptions now works like the Clips tray: per-row star/edit/delete icons, a Recent/Favorites tab (Favorite pulls up only favorites), real search box with placeholder, tooltips. Clips search bar redone the same way (placeholder, no bare emoji) + row tooltips. v2.5.0

v2.4.9  (2026-07-12)
    Editor: clean layout (Save/Cancel + Ask AI never overlap), the AI instruction is now an obvious bordered field with placeholder, visible status feedback, and a tooltip. Tooltips + clear hints on all Ask AI buttons. v2.4.9

v2.4.8  (2026-07-12)
    Fix update install loop: hard-exit on update (frees single-instance mutex + file locks instantly), relaunched copy waits out the stale lock, exit immediately when installer launches. v2.4.8

v2.4.7  (2026-07-12)
    Favorite is now a real toggle (click again to un-favorite). Help '?' is a hover tooltip next to the title (no click, no 'New here?'). v2.4.7

v2.4.6  (2026-07-12)
    Edit dialog: Save always visible, opens beside the tray, + Ask AI (rewrite/reformat/answer in place). Remove ping watchdog window; installer relaunches silently. v2.4.6

v2.4.5  (2026-07-12)
    In-app update banner + Install button in Settings; auto-check on every open; drop floating desktop badge. v2.4.5

v2.4.4  (2026-07-12)
    Recent transcriptions: fit buttons, double/right-click edit, right-click menu, ★ favorites. v2.4.4

v2.4.3  (2026-07-12)
    Fix update checker: point Pro at echoquill-pro repo (was reading free repo, so Pro never saw updates). v2.4.3

v2.4.2  (2026-07-12)
    Edit on the visible top toolbar (Newer/Older/page line); edit clips in the tray (✎)

v2.4.1  (2026-07-12)
    Edit button visible (moved left, wider window)

v2.4.0  (2026-07-12)
    '?' help icons on Clips, Transcriber, and Ask AI windows (how-to incl. drag/click paste + admin note)

v2.3.3  (2026-07-12)
    trigger public build (auto-update now fully one-click from GitHub)

v2.3.2  (2026-07-12)
    Pro auto-update identical to free (GitHub download+install) — one-click the moment the repo is public

v2.3.1  (2026-07-12)
    Pro updates point to GitHub (not Lemon Squeezy) — opens the Pro releases page to grab the installer

v2.3.0  (2026-07-12)
    auto update-check twice daily + green corner badge

v2.2.3  (2026-07-12)
    edit transcription text and save it (Recent transcriptions → Edit)

v2.2.2  (2026-07-09)
    v2.2.2 CRITICAL: API/license keys persist across updates — load() resolves the vault; bundle keyring Windows backend

v2.2.1  (2026-07-09)
    drag-and-drop audio/video upload → auto-transcribe (Pro)

v2.2.0  (2026-07-09)
    light/dark/system theme + optional audio recording history (budget + zip export)

v2.1.7  (2026-07-09)
    Edit button for dictionary entries

v2.1.6  (2026-07-09)
    manage transcriptions — multi-select, Select all, Delete selected, Delete all (paged)

v2.1.5  (2026-07-09)
    FIX Recent transcriptions freeze (self._pro used before assignment); safe close + empty state

v2.1.4  (2026-07-09)
    Stop button on batch transcription too

v2.1.3  (2026-07-09)
    Stop button on the transcriber

v2.1.2  (2026-07-06)
    keys stored in Windows Credential Manager (survive updates); docs updated

v2.1.1  (2026-07-06)
    remove pointless 'Search the web instead' button from Ask AI

v2.1.0  (2026-07-06)
    Pro build unlocks all features unconditionally (no license limit until a store exists)

v2.0.9  (2026-07-06)
    separate engine per window (no freeze); Ask AI save-answer (title - question, appends, stays open); key strip; batch own engine one-at-a-time

v2.0.8  (2026-07-06)
    clearer checkbox label 'Format dictation with AI'

v2.0.7  (2026-07-06)
    Pro update check reads public version manifest (works for private builds, no embedded token)

v2.0.6  (2026-07-06)
    current model lineup with thinking labels + fast defaults; timeout 20

v2.0.5  (2026-07-06)
    AI enhancement fails fast (6s)

v2.0.4  (2026-07-06)
    AI opt-in for dictation; keep_alive latency fix; GLM; slimmer AI panel; ask_ai keep_alive

v2.0.3  (2026-07-06)
    Ask AI copy button always visible + confirmation; AI settings note about local-model speed

v2.0.2  (2026-07-06)
    optional Administrator mode + elevated-app warning

v2.0.1  (2026-07-06)
    installer refreshes the Windows icon cache

v2.0.0  (2026-07-06)
    EchoQuill Pro v2.0.0 — license activation, unlimited transcriptions, Favorites, unlimited clips, Ask AI with timestamps

============================================================
ECHOQUILL FREE
============================================================

v1.23.0  (2026-07-16)
    PARITY with Pro - brings Free up to date. NEW: Read aloud (Text-to-speech) with the audio player, Save-to-folder, and 'Listen on my phone' (QR over local WiFi). Reliability: crash-proof event loop + crash.log; copy/paste + right-click menu fix. UX: app-wide clean auto-hiding scrollbars (no more double/pointless bars); Recent transcriptions drag/click like the Clips tray. Help updated (Meeting, Read aloud & phone); new 'What's New' changelog section + CHANGELOG.md.

v1.22.0  (2026-07-15)
    delete folders + folder controls in the edit dialog; Meeting preset dropdown hover + truncate; copy/paste + right-click fixed in all fields

v1.21.0  (2026-07-14)
    folders in Clips + Recent (custom 30-char dialog); Clips folder + Save/Open; standardized button bars; Meeting preset word-wrap + pinned Ask

v1.20.2  (2026-07-14)
    Approved batch: fix Ollama Cloud model list (kimi-k2.7 -> kimi-k2.7-code, verified against ollama.com; default -> qwen3.5), raise AI timeout 45->180s (gpt-oss:120b/thinking models were timing out). Ask AI presets: manager moved to the BOTTOM of the dropdown (add/edit/delete your own; defaults locked). Add Clear + Open-folder to 'Ask AI about this video'. Real always-visible right-side scrollbar on every text box (safe wrapper, no freeze).

v1.20.1  (2026-07-14)
    Revert the self-updating yt-dlp engine (2.8.0). Evidence: the YouTube download code is byte-identical to the last known-good version, so the only thing that changed was the engine version. The auto-updater force-swapped the bundled yt-dlp for the newest (most locked-down) copy on every launch. Back to the bundled engine; removed the Update-engine/Restart UI. Cookies paste box kept.

v1.20.0  (2026-07-14)
    Quality pass (2.9.0): verified every UI button/handler is wired (whole-app static scan, now enforced in CI so a broken build can't publish). Confirmed Ollama Cloud (ollama.com/api, gpt-oss:20b), Meeting Ask-AI presets, and Clips folders are all correctly hooked up. Restart button + simplified single sign-in retained. No new features - correctness + coherence.

v1.19.3  (2026-07-14)
    Clarify cookies: use the extension's 'Export All Cookies' so ONE file covers every logged-in site (YouTube AND Skool), since they use different cookies. v1.19.3

v1.19.2  (2026-07-14)
    Add a real Restart button after engine updates (shows only when a restart is needed; app relaunches itself). Simplify Transcription: one sign-in method (paste cookies, covers YouTube+Skool+member-only) instead of two overlapping ones. Clarify that the 'do not edit' header in cookies is normal. v1.19.2

v1.19.1  (2026-07-14)
    Fix right-click Cut/Copy/Paste: menu now calls grab_release (it was flashing shut on Windows) and focuses the field so Paste lands there. Also bind middle-click. Right-click paste works in all text fields now. v1.19.1

v1.19.0  (2026-07-14)
    Self-updating video engine: EchoQuill now pulls the latest yt-dlp (pure-python wheel) into AppData and uses it, auto-refreshing on launch + an 'Update engine now' button — so YouTube changes stop breaking downloads. Redo YouTube cookies as a paste box with Save/Clear (paste exported cookies straight in). v1.19.0

v1.18.7  (2026-07-14)
    YouTube auth: Chrome locks/encrypts its cookie DB (yt-dlp #7271). Add a Cookies file (cookies.txt) option in Settings > Transcription (most reliable, works around Chrome), prefer it over browser cookies, and give a plain-language error pointing to Firefox or a cookies.txt. v1.18.7

v1.18.6  (2026-07-14)
    YouTube 'confirm you're not a bot' errors now show plain guidance in the transcriber + batch: turn on Settings > Transcription > Sign in via browser. (This is YouTube's anti-bot escalation; cookies-from-browser is the fix and is already supported.) v1.18.6

v1.18.5  (2026-07-14)
    CRITICAL: define _preset_add_current/_preset_remove_current (the +/trash buttons referenced them but they were never added). Their absence threw AttributeError while building the Meeting panel, blanking the entire Settings window from Meeting onward (incl. AI Enhancement). Settings renders fully again. v1.18.5

v1.18.4  (2026-07-14)
    Fix Ollama Cloud default model (was a non-Ollama 'gemini-3' id -> real gpt-oss:20b + catalog ids). Add +/trash inline preset save/remove to the video 'Ask AI about this video' (parity with Meeting). v1.18.4

v1.18.3  (2026-07-14)
    HOTFIX: revert the auto-scrollbar in dark_text — packing a scrollbar inside the yscrollcommand callback caused an infinite Tk geometry loop that froze the whole app (windows wouldn't open, menu/quit dead). Text boxes scroll via wheel again; will re-add visible scrollbars the safe wrapped way later. v1.18.3

v1.18.2  (2026-07-14)
    Clips vault (Pro): folders in the Favorites tab — a Folder filter + per-clip move-to-folder (type a name to create). Meeting: inline + save / trash-remove preset buttons instead of a separate manage dialog. v1.18.2

v1.18.1  (2026-07-14)
    Fix AI 404 with Ollama Cloud: ollama.com only serves the native /api/chat (not OpenAI /v1). New ai_call routes native for ollama.com and any /api base; OpenAI-compat otherwise. Ollama Cloud default + saved URLs migrated to https://ollama.com/api. Applies to dictation cleanup, Ask-AI and the editor. v1.18.1

v1.18.0  (2026-07-14)
    Tooltips: only one open at a time, always closes on leave (poll catches missed leaves). Real visible auto-scrollbars on every text box. Meeting: '?' help by the title, clearer 'Name this meeting/recording' label. Ask AI replaces Summarize in Meeting + preset-question dropdown (with add/remove your own) in both Meeting and the video transcriber. v1.18.0

v1.17.6  (2026-07-14)
    Perf + UX: Recent transcriptions now lazy/paged (only the visible page is parsed — snappy with thousands). Every text box scrolls internally (wheel scrolls the text, not the page) app-wide. v1.17.6

v1.17.5  (2026-07-14)
    Meeting tab overhaul: tooltips everywhere, Name required before Start, Save opens in Meetings folder, added Copy/Open-folder/Clear (parity with transcriber), fixed-height text box so action buttons are always visible + internal scrolling, temp-file cleanup after screen recording, add Clips subfolder. v1.17.5

v1.17.4  (2026-07-13)
    Meeting capture fix: init COM multithreaded (MTA) on the WASAPI thread and pick the loopback device robustly - fixes 'Nothing captured'. Clearer diagnostics (no-audio vs silence). v1.17.4

v1.17.3  (2026-07-13)
    Installer: per-user install (PrivilegesRequired=lowest) so silent auto-updates need no admin - fixes 'DeleteFile failed code 5 Access denied' in Program Files. Add Meeting/Record to the pill + tray menus. Make Meeting a Pro feature (free shows it locked with Upgrade to Pro). v1.17.3

v1.17.2  (2026-07-13)
    Fix Meeting recording error 0x800401F0 (CoInitialize the WASAPI capture thread). Organize output into one Documents/EchoQuill folder with subfolders (Transcriptions, Meetings); meeting transcripts + recordings save to Meetings. v1.17.2

v1.17.1  (2026-07-13)
    Meeting/Record: add 'Also capture the screen' — records desktop video (ffmpeg gdigrab) + system audio, muxes to MP4, and transcribes. Turns it into a full Zoom/Meet/webinar recorder, not just audio. Bundles ffmpeg via imageio-ffmpeg. v1.17.1

v1.17.0  (2026-07-13)
    New Meeting/Record tab: capture system audio (+ optional mic) and transcribe locally - works for calls, webinars, and any playing video incl. Skool (no URL). Adds AI 'Summarize' + save. Sidebar reordered: General, then services A-Z (incl. Meeting), then History/Stats, then License/Help/Feedback/About. v1.17.0

v1.16.17  (2026-07-13)
    Transcriber layout: put Keep audio / Keep video checkboxes and Find in transcript on one row (fills the empty right side). v1.16.17

v1.16.16  (2026-07-13)
    Keep video file: now downloads the video FIRST (before the long transcription) so the signed Skool link is still valid, with visible status and a saved-file note. Uses a mergeless 'best' format so it works without extra ffmpeg steps. v1.16.16

v1.16.15  (2026-07-13)
    Transcriber: optional 'Name this transcript' box. Leave blank for the video's own title; type a name and the transcript (and any kept audio/video) saves under it automatically - ideal for Skool videos that have no title. v1.16.15

v1.16.14  (2026-07-13)
    Transcriber: add 'Keep audio file' and 'Keep video file' checkboxes (default OFF). Keeps the downloaded audio and/or downloads the full video into the transcripts folder, with Skool Referer + browser-cookies support. v1.16.14

v1.16.13  (2026-07-13)
    Skool support: auto-add Referer/Origin for skool.com and .m3u8 (signed HLS), plus optional 'Sign in via browser' (yt-dlp cookies-from-browser) for member-only videos. Settings > Transcription dropdown + help text. v1.16.13

v1.16.12  (2026-07-13)
    Update install now runs the installer via a hidden waiter that starts only AFTER EchoQuill has fully exited - fixes the green banner 'close all instances' / app-not-closing race. Fixes both the banner and the About button routes. v1.16.12

v1.16.11  (2026-07-13)
    Recent transcriptions: drop the static caption line, add a hover '?' help next to the title (consistent with the other windows). Real per-icon tooltips remain. v1.16.11

v1.16.10  (2026-07-13)
    Fix tooltips not showing inside scrolling lists (ignore the spurious mouse-leave when the tip window maps; delayed cursor-anchored tooltip). Add tooltips across all windows: transcriber, batch, Ask AI, recent-transcriptions paging/tabs/delete, clips tabs/close. v1.16.10

v1.16.9  (2026-07-13)
    Recent transcriptions now works like the Clips tray: per-row star/edit/delete icons, a Recent/Favorites tab (Favorite pulls up only favorites), real search box with placeholder, tooltips. Clips search bar redone the same way (placeholder, no bare emoji) + row tooltips. v1.16.9

v1.16.8  (2026-07-12)
    Editor: clean layout (Save/Cancel + Ask AI never overlap), the AI instruction is now an obvious bordered field with placeholder, visible status feedback, and a tooltip. Tooltips + clear hints on all Ask AI buttons. v1.16.8

v1.16.7  (2026-07-12)
    Fix update install loop: hard-exit on update (frees single-instance mutex + file locks instantly), relaunched copy waits out the stale lock, exit immediately when installer launches. v1.16.7

v1.16.6  (2026-07-12)
    Favorite is now a real toggle (click again to un-favorite). Help '?' is a hover tooltip next to the title (no click, no 'New here?'). v1.16.6

v1.16.5  (2026-07-12)
    Edit dialog: Save always visible, opens beside the tray, + Ask AI (rewrite/reformat/answer in place). Remove ping watchdog window; installer relaunches silently. v1.16.5

v1.16.4  (2026-07-12)
    In-app update banner + Install button in Settings; auto-check on every open; drop floating desktop badge. v1.16.4

v1.16.3  (2026-07-12)
    Recent transcriptions: fit buttons, double/right-click edit, right-click menu, ★ favorites. v1.16.3

v1.16.2  (2026-07-12)
    Edit on the visible top toolbar (with page count); edit clips directly in the tray (✎)

v1.16.1  (2026-07-12)
    Edit button moved to left of the transcriptions bar so it's never clipped off-screen; wider window

v1.16.0  (2026-07-12)
    '?' help icon on the Clips tray and Transcriber windows with how-to (click/drag to paste, admin-rights note)

v1.15.0  (2026-07-12)
    auto update-check twice daily + green corner badge (hover to see version, click to update)

v1.14.2  (2026-07-12)
    edit transcription text and save it (Recent transcriptions → Edit)

v1.14.1  (2026-07-09)
    v1.14.1 CRITICAL: API key now persists across updates — load() resolves the Credential Manager vault (was returning a marker string, causing 401); bundle keyring Windows backend

v1.14.0  (2026-07-09)
    light/dark/system theme + optional audio recording history (budget + zip export)

v1.13.23  (2026-07-09)
    Edit button for dictionary entries

v1.13.22  (2026-07-09)
    manage transcriptions — multi-select, Select all, Delete selected, Delete all

v1.13.21  (2026-07-09)
    harden Recent transcriptions window (safe close, empty state, no crash)

v1.13.20  (2026-07-09)
    Stop button on batch transcription too

v1.13.19  (2026-07-09)
    Stop button on the transcriber to cancel an in-progress transcription

v1.13.18  (2026-07-06)
    store API/license keys in Windows Credential Manager so they survive updates; docs updated

v1.13.17  (2026-07-06)
    transcription windows use their own engine (never block dictation); AI key whitespace-stripped

v1.13.16  (2026-07-06)
    clearer checkbox label 'Format dictation with AI'

v1.13.15  (2026-07-06)
    current model lineup (GLM-5.2, DeepSeek-V4, Qwen3.5, GPT-5.4, Claude, Gemini-3-flash) with thinking labels, fast defaults, timeout back to 20; AI stays optional for dictation

v1.13.14  (2026-07-06)
    AI enhancement fails fast (6s) so a misconfigured provider can't stall dictation

v1.13.13  (2026-07-06)
    AI only formats dictation when opted in; keep_alive fixes Ollama cold-start latency; GLM provider; slimmer AI panel

v1.13.12  (2026-07-06)
    optional Administrator mode + auto-warning when dictating into elevated apps

v1.13.11  (2026-07-06)
    installer refreshes the Windows icon cache so version badges update

v1.13.10  (2026-07-06)
    press ESC to cancel an in-progress dictation

v1.13.9  (2026-07-06)
    reopening Settings now reliably brings the existing window to the front

v1.13.8  (2026-07-06)
    update relaunch hardened — watchdog restart + /CURRENTUSER for silent per-user installs

v1.13.7  (2026-07-06)
    AI defaults now STRUCTURE output — email layout, bullet-pointed notes, document paragraphs (formatting, not tone)

v1.13.6  (2026-07-05)
    installer also sweeps leftover echoquill_ temp audio from any prior version

v1.13.5  (2026-07-05)
    unsaved-changes prompt, auto context tones, temp cleanup, restore missing _time_at

v1.13.4  (2026-07-05)
    v1.13.4 CRITICAL: fix dictation crash (raw before assignment); silent auto-relaunching updates; inline per-app tone fields; settings layout fix

v1.13.3  (2026-07-05)
    self-cleaning installer — auto-closes app, sweeps old temp unpacks and stale autostart, upgrades in place

v1.13.2  (2026-07-05)
    folder-format build to reduce antivirus false positives; portable download becomes a zip

v1.13.1  (2026-07-05)
    in-app Feedback page; expanded README comparison table

v1.13.0  (2026-07-05)
    v1.13: one-click updates, URL normalizing (Shorts fix), timestamps on search, per-app tone editor, keep-awake, export-all, first-run welcome

v1.12.0  (2026-07-05)
    v1.12: voice-command recognition overhaul — vocabulary-primed decoding, beam search for commands, web shortcuts (youtube, gmail, zillow...)

v1.11.6  (2026-07-05)
    Settings: Save button only on tabs with settings; README install section; upgrade links to echo-quill.com

v1.11.5  (2026-07-05)
    Upgrade links point to echo-quill.com

v1.11.4  (2026-07-05)
    Clips tray rebuilt: working search, paste-to-last-app on click, true carry-and-drop drag

v1.11.3  (2026-07-05)
    Free tier: clip history capped at 10 (Pro: unlimited + Favorites)

v1.11.2  (2026-07-05)
    Upgrade path: Pro link in settings sidebar, transcriber windows, and limit message ($5/mo, $39/yr)

v1.11.1  (2026-07-05)
    Free tier: 5 lifetime video transcriptions; dictation unlimited forever
