# eldailydad-editor

Toolkit and instructions for editing El Daily Dad Instagram Reels with Claude Code.

## How to use it (for you)

1. Put the raw clips for a new video in your Drive folder, in a new subfolder, e.g. `Raw/timer-toddlers/`.
2. Start a new Claude Code session with this repository and the **eldailydad-editor** environment selected.
3. Say what you want, for example:
   > Edit Raw/timer-toddlers. Home list format, topic: el timer con toddlers, age 2-4 años.
4. You get back: the final video with captions and stickers (original HDR quality), the clean
   rough cut for CapCut, the captions file, and edit notes with timestamps for titles and sounds.
5. Add titles (Modern font) and sounds in CapCut.

Claude follows `CLAUDE.md`, and your style is in `STYLE_GUIDE.md`.

## What's inside

| Path | What it does |
|---|---|
| `CLAUDE.md` | Step-by-step workflow Claude follows every time |
| `STYLE_GUIDE.md` | Your six formats, pacing, colours, fonts and captions |
| `setup.sh` | Installs whisper.cpp, Hyperframes and the Drive downloader |
| `scripts/fetch_drive.py` | Downloads clips from your Drive folder |
| `scripts/analyze.py` | Finds every take and transcribes it, makes contact sheets |
| `scripts/build_cut.py` | Builds the rough cut from an edit list (keeps HDR) |
| `scripts/captions.py` | Draft captions from the cut (then proofread) |
| `scripts/overlays.py` | Renders captions, stickers (and optional titles) as a transparent layer |
| `scripts/safezone.py` | Checks nothing sits in Instagram's no-text zones |
| `scripts/composite.py` | Puts the layer on the original-quality footage |
| `.claude/skills/eldailydad-video-edit/` | The editing skill (loads automatically in sessions with this repo; also upload it to claude.ai) |
| `templates/` | Example edit list and overlay settings (from the timer video) |
| `assets/` | Fonts and animation library used by the overlays |
