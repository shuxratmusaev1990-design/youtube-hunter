---
name: youtube-hunter
description: YouTube Hunter — record YouTube live streams, download videos, cut them into 9:16 Shorts with karaoke subtitles, write trend-based titles/descriptions/tags in any language, and auto-upload to YouTube. Use for "youtube hunter", "record the stream", "make shorts from this video", "trend tags", "upload to youtube", "auto mode".
---

# YouTube Hunter

Reply in the user's language. Everything lives in `~/youtube-hunter/` (Windows: `%USERPROFILE%\youtube-hunter`).
This skill's folder (the folder containing this SKILL.md, below called `SKILL_DIR`) holds the installers and scripts.

## 0. Where it runs
Run on the user's own computer or server (Claude Code, a desktop shell, or a VPS).
Sandboxed cloud environments usually block YouTube, so recording, downloading and uploading will not work there:
in that case give the user this skill folder (or the GitHub repo) and walk them through running it locally.

## 1. Install (once) — do this first
Check whether it is installed: `~/youtube-hunter/hunter` (Mac/Linux) or `%USERPROFILE%\youtube-hunter\hunter.bat` (Windows).
If missing, run the installer from `SKILL_DIR`:

| OS | Command |
|---|---|
| Windows | `"SKILL_DIR\install.bat"` (or the user double-clicks it) |
| Mac / Linux | `bash "SKILL_DIR/install.sh"` |

The installer installs/checks everything and prints a check at the end:

| What | Why | How it is installed |
|---|---|---|
| Python 3.10+ | runs the scripts | winget (Windows), brew (Mac), apt/dnf/pacman (Linux) |
| FFmpeg | cut, 9:16, subtitles, audio | winget / brew / apt |
| Python venv `~/youtube-hunter/.venv` | isolated libraries | `python -m venv` |
| yt-dlp | record live streams, download videos, trend search | pip |
| faster-whisper | speech-to-text with word timings (auto language detection) | pip |
| requests | YouTube Data API trend queries | pip |
| google-api-python-client, google-auth-oauthlib, google-auth-httplib2 | upload to YouTube | pip |
| anthropic | optional: Claude picks clips in auto mode | pip |

It also copies the scripts to `~/youtube-hunter/scripts/`, creates `config.json` (from `config.example.json`),
`.env` (from `.env.example`, empty keys) and the `hunter` / `hunter.bat` command.
First transcription downloads the Whisper model (~3 GB for `large-v3`; use `medium`/`small` in config on weak PCs).
If the installer fails, read its output, fix the one missing piece, and re-run it (it is safe to re-run).

## 2. Connect YouTube (once, only needed for uploading)
Walk the user through this; never ask them to paste secrets into the chat.
1. https://console.cloud.google.com → create a project → APIs & Services → Library → enable **YouTube Data API v3**.
2. Google Auth Platform / OAuth consent screen → External → app name, support email → **Test users**: add the
   Google account that owns the channel.
3. Clients / Credentials → Create OAuth client ID → **Desktop app** → **Download JSON**.
4. Save it as `~/youtube-hunter/client_secret.json`. First upload opens the browser for consent; `token.json` is saved.
Notes: while the app is in "Testing", Google may expire the consent after about a week (re-consent, or publish the app).
Videos uploaded from an unverified API project may stay private until Google's audit. The daily API quota is limited;
`max_uploads_per_day` (default 6) respects it.

Optional keys go in `~/youtube-hunter/.env` (the user fills them in themselves):
- `YT_API_KEY` — faster, more accurate trend data (without it, yt-dlp search is used).
- `ANTHROPIC_API_KEY` — in unattended auto mode, Claude picks the clips and writes metadata (without it, a heuristic is used).

## 3. Commands
Mac/Linux: `~/youtube-hunter/hunter <cmd> ...` · Windows: `%USERPROFILE%\youtube-hunter\hunter.bat <cmd> ...`

| Task | Command |
|---|---|
| Record a live stream in chunks | `hunter record URL [--segment 600] [--wait]` (URL = stream or `https://www.youtube.com/@channel/live`) |
| Record a live stream from its start | `hunter record URL --from-start` (needs DVR on the stream) |
| Download a video / playlist / channel | `hunter download URL [--max 5] [--after 20261101]` |
| Transcribe | `hunter transcribe VIDEO [--lang auto]` → `.words.json`, `.transcript.txt` |
| Make one Short | `hunter short VIDEO --start S --end E --out x.mp4 --words VIDEO.words.json --hook "text" [--layout blur\|crop\|fit]` |
| Trend research | `hunter trends "topic" [--days 30] [--region US] [--lang en]` (no region = worldwide) |
| Upload | `hunter upload x.mp4 --meta x.json --shorts [--publish-at 2026-12-01T15:00:00Z]` |
| Full auto, one file | `hunter auto process VIDEO [--topic "..."] [--region US] [--no-upload]` |
| Full auto, watch channels | `hunter auto watch [--interval 300] [--no-upload]` |

Downloads go to `~/youtube-hunter/downloads/`, live chunks to `live/`, finished Shorts to `shorts/` (or `queue/` with `--no-upload`).

## 4. Best-quality workflow (Claude drives it)
1. **Source:** live stream → `hunter record`; normal video → `hunter download`.
2. **Transcribe:** `hunter transcribe`, then read the `.transcript.txt` yourself.
3. **Pick moments yourself:** 3–7 clips, `short_min_sec`–`short_max_sec` (default 20–59 s); strong hook in the
   first 2 seconds, one complete idea, no cut mid-sentence, no overlap. Show the list (times, hook, why).
4. **Edit:** `hunter short` for each (`--hook` = 3–6 on-screen words). Extract one frame with ffmpeg and look at it.
5. **Trends:** `hunter trends "<topic>" --lang <lang> [--region <country>]`.
6. **Metadata:** write a `meta.json` per Short: `title` ≤70 chars (keyword + curiosity), `description` 2–3 sentences
   + 3–5 hashtags incl. `#Shorts`, `tags` 10–15 (trend + specific). No clickbait the clip does not deliver.
   Language = `output_language` (auto = the video's language).
7. **Confirm:** show the Shorts, texts and schedule to the user. Do not upload until they say so.
8. **Upload:** `hunter upload ... --shorts`; several Shorts → spread them with `--publish-at` 3–4 hours apart.

## 5. Auto mode
`hunter auto watch` checks `channels_to_watch` every 5 minutes: records live streams, processes finished chunks
and new uploads → Shorts → trend metadata → scheduled upload (`privacy`, `schedule_every_hours`,
`max_uploads_per_day` from config). Recommend `--no-upload` for the first week so the user reviews `queue/`.
Keep it running: Windows Task Scheduler, Mac/Linux `tmux`/`nohup`/`systemd`, or a VPS.
State is in `state.json`; upload log in `uploads.jsonl`.

## 6. Any audience
Nothing is tied to one language or country. `language: auto` lets Whisper detect the video language;
`output_language` sets the metadata language (e.g. Russian video, English titles: `en`);
`trend_region` empty = worldwide, or a country code (`US`, `IN`, `BR`, `UZ`...). If the user names an audience,
set `--lang` / `--region` / `output_language` for that run. For several languages, write one `meta.json` per language.

## 7. Rules
- Only use the user's own content or content they have permission to reuse. Re-uploading other people's videos
  without permission leads to copyright strikes — say so plainly when relevant.
- Default `privacy: private`; switch to `public` only when the user explicitly asks.
- Never print, copy into chat, or commit `client_secret.json`, `token.json`, `.env` or cookies.
- Troubleshooting order: `hunter` venv `python -m pip install -U yt-dlp` → cookies (`config.json` → `cookies`,
  a `cookies.txt` exported from the browser) → FFmpeg/Python versions → re-run the installer.
