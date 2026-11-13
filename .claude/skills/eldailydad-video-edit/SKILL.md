---
name: eldailydad-video-edit
description: Use when editing an @eldailydad Instagram Reel from raw footage: transcribe and choose takes, build the rough cut, make Spanish captions and stickers on the original HDR footage, and plan titles and sounds for finishing in CapCut.
---

# El Daily Dad video edit

Edit raw vertical iPhone footage into a Reel in his style. Claude cuts the video, writes the
captions and adds stickers on the original-quality footage. He adds titles (CapCut "Modern"
font) and sounds in CapCut.

## If the eldailydad-editor repo is in the session
Follow its `CLAUDE.md` exactly. It has the scripts (fetch_drive, analyze, build_cut, captions,
overlays, safezone, composite) and `STYLE_GUIDE.md`. Everything below is the short version.

## Inputs
- Raw clips in his Google Drive folder (a subfolder he names, e.g. `Raw/<video>`)
- Format (home list, home talk "Part N", car POV, day in the life, family Q&A, split-screen vlog)
- Topic, part number, age line, any product mentioned

## Steps
1. Download the clips (Drive files via `drive.usercontent.google.com`; normal links redirect to blocked hosts).
2. Transcribe every spoken section separately with whisper.cpp, **multilingual model, `-l es`**
   (he speaks Spanish with English words). Find sections with silencedetect (-36 dB, 0.35 s).
3. Choose takes from the transcripts and contact sheets. He records lines 2-4 times: pick the
   most complete, fluent take, never "last take wins". List uncertain choices for him to check.
4. Cut: hook lean-in (~1.5 s) → title line → body in script order → CTA → silent ending gag (1.5-4 s).
   40-60 s total, segments 2-6 s, pauses ≤ 0.6 s, 0.15 s pad before / 0.12 s after speech.
   No speed-up, no punch-ins, no colour grade. Cut one segment at a time (memory).
5. Keep iPhone HDR (HLG) as HDR. Never tone-map (it turned skin red). SDR previews: plain conversion.
6. Captions: phrase captions from the cut's word timings, proofread by hand, lowercase, white,
   lower centre (x 100-890, y ~1360), number words and key numbers in neon yellow `#ECFF0E`.
   No caption on the hook line "nadie me dijo esto".
7. Stickers: share icon on "mándaselo", comment bubble on "dime", alarm clock + short yellow gag
   text on the ending exit when it fits.
8. Render captions and stickers as a transparent layer (Hyperframes, no footage) and composite it
   onto the HDR footage with FFmpeg, SDR white at HLG 75% (zscale npl=203). Do not let
   Hyperframes render HDR footage directly (captions stacked up).
9. Check Instagram Reels safe zones: nothing in the top/bottom 240 px, the side margins, or the
   button column (x > 909, y > 1173).
10. Deliver: final video (captions + stickers, original quality), clean rough cut for CapCut,
    captions SRT, and edit notes with the edit table, CapCut title plan (series card, topic
    title, numbered sub-lines; cursor click and typing sounds) and the please-check list.

Say plainly that audio was checked by transcript and loudness, not by listening, and that
captions are machine-transcribed then proofread.

## Style constants
Pale-blue title pill `#BCE3FB`, butter-yellow age pill `#FBFFB8`, topic title cream `#FCFEC0` +
sky blue `#63BFFA` with a dark outline on light walls, neon yellow emphasis `#ECFF0E`.
Loudness about -16 to -14 LUFS.
