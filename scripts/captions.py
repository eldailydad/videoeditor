#!/usr/bin/env python3
"""Make phrase captions from the finished cut.

  captions.py <roughcut_preview.mp4> <out.srt> [--lang es] [--max-chars 38]

Transcribes the cut with word timestamps and groups words into short phrases
(1-2 lines, broken at punctuation), lowercase like the toys video. Whisper makes
mistakes on names and English words: ALWAYS read the SRT and fix the text by hand
(keep the timings). Also writes <out>.words.json for reference.
"""
import argparse, json, os, re, subprocess, sys
sys.path.insert(0, os.path.dirname(__file__))
from common import WHISPER_BIN, WHISPER_MODEL, ff, write_srt

ap = argparse.ArgumentParser()
ap.add_argument("video"); ap.add_argument("out")
ap.add_argument("--lang", default="es")
ap.add_argument("--max-chars", type=int, default=38)
ap.add_argument("--keep-case", action="store_true")
a = ap.parse_args()

stem = os.path.splitext(a.out)[0]
wav = stem + ".wav"
ff("-i", a.video, "-ar", "16000", "-ac", "1", wav)
subprocess.run([WHISPER_BIN, "-m", WHISPER_MODEL, "-f", wav, "-l", a.lang, "-t", "4", "-ml", "1", "-sow", "-ojf", "-of", stem + ".words"],
               check=True, capture_output=True)
j = json.load(open(stem + ".words.json"))
words = [(s["offsets"]["from"] / 1000, s["offsets"]["to"] / 1000, s["text"].strip())
         for s in j["transcription"] if s["text"].strip() and not s["text"].strip().startswith("[")]

caps, cur = [], []
def flush():
    if cur:
        txt = " ".join(w for _, _, w in cur)
        txt = re.sub(r"[.]+$", "", txt).strip()
        caps.append([cur[0][0], cur[-1][1], txt if a.keep_case else txt.lower()])
        cur.clear()
for w in words:
    if cur and len(" ".join(x for _, _, x in cur + [w])) > a.max_chars:
        flush()
    cur.append(w)
    if re.search(r"[.?!]$", w[2]) or (re.search(r",$", w[2]) and len(" ".join(x for _, _, x in cur)) > 18):
        flush()
flush()

# small lead-out so captions don't flash; never overlap the next one
for i in range(len(caps)):
    nxt = caps[i + 1][0] if i + 1 < len(caps) else caps[i][1] + 0.3
    caps[i][1] = min(caps[i][1] + 0.15, nxt)
write_srt(a.out, caps)
print(open(a.out).read())
print(f"{len(caps)} captions -> {a.out}   (proofread the text before using it)")
