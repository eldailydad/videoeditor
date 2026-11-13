#!/usr/bin/env python3
"""Analyze raw clips: probe, contact sheets, spoken sections, per-take transcripts.

  analyze.py <work-dir> <clip1> [<clip2> ...] [--lang es]

Writes into <work-dir>:
  clips.json                 probe info per clip (duration, HDR, fps...)
  <clip>.sheet.jpg           contact sheet (one frame every N s)
  <clip>.takes.json / .txt   every spoken section with start/end and its own transcript
                             -> this is what take selection is based on
Sections closer than 0.5 s are merged into one take.
"""
import argparse, json, os, subprocess, sys
sys.path.insert(0, os.path.dirname(__file__))
from common import FFMPEG, WHISPER_BIN, WHISPER_MODEL, ff, probe

ap = argparse.ArgumentParser()
ap.add_argument("work")
ap.add_argument("clips", nargs="+")
ap.add_argument("--lang", default="es")
ap.add_argument("--silence-db", default="-36")
ap.add_argument("--silence-min", default="0.35")
a = ap.parse_args()
os.makedirs(a.work, exist_ok=True)

info = {}
for clip in a.clips:
    name = os.path.splitext(os.path.basename(clip))[0]
    p = probe(clip); p["path"] = os.path.abspath(clip); info[name] = p
    print(f"== {name}: {p['duration']:.1f}s {p['width']}x{p['height']} {p['fps']}fps {'HDR/HLG' if p['hlg'] else ('HDR' if p['hdr'] else 'SDR')}")

    # contact sheet: ~40 tiles max
    step = max(1.0, p["duration"] / 40)
    ff("-i", clip, "-vf", f"fps=1/{step:.2f},scale=180:320,tile=10x4", "-frames:v", "1", f"{a.work}/{name}.sheet.jpg")

    wav = f"{a.work}/{name}.wav"
    ff("-i", clip, "-ar", "16000", "-ac", "1", wav)
    r = subprocess.run([FFMPEG, "-i", wav, "-af", f"silencedetect=n={a.silence_db}dB:d={a.silence_min}", "-f", "null", "-"],
                       capture_output=True, text=True).stderr
    st = [float(l.split("silence_start:")[1]) for l in r.splitlines() if "silence_start:" in l]
    en = [float(l.split("silence_end:")[1].split()[0]) for l in r.splitlines() if "silence_end:" in l]
    sp, t = [], 0.0
    for s, e in zip(st, en + [p["duration"]]):
        if s - t > 0.15:
            sp.append([t, s])
        t = e
    if p["duration"] - t > 0.15:
        sp.append([t, p["duration"]])
    takes = []
    for s, e in sp:
        if takes and s - takes[-1][1] < 0.5:
            takes[-1][1] = e
        else:
            takes.append([s, e])

    os.makedirs(f"{a.work}/sec_{name}", exist_ok=True)
    out = []
    for i, (s, e) in enumerate(takes):
        f = f"{a.work}/sec_{name}/{i:03d}.wav"
        ff("-ss", f"{max(0, s - 0.2):.3f}", "-to", f"{min(p['duration'], e + 0.2):.3f}", "-i", wav, f)
        res = subprocess.run([WHISPER_BIN, "-m", WHISPER_MODEL, "-f", f, "-l", a.lang, "-t", "4", "-nt", "-np"],
                             capture_output=True, text=True)
        txt = " ".join(res.stdout.split())
        out.append({"i": i, "start": round(s, 2), "end": round(e, 2), "dur": round(e - s, 2), "text": txt})
        print(f"  {i:03d} {s:7.2f}-{e:7.2f} ({e - s:4.1f}s) {txt}", flush=True)
    json.dump(out, open(f"{a.work}/{name}.takes.json", "w"), ensure_ascii=False, indent=1)
    with open(f"{a.work}/{name}.takes.txt", "w") as fh:
        for o in out:
            fh.write(f"{o['i']:03d} {o['start']:7.2f}-{o['end']:7.2f} ({o['dur']:4.1f}s) {o['text']}\n")

json.dump(info, open(f"{a.work}/clips.json", "w"), indent=1)
print("\nnext: write edl.json (see templates/edl.example.json), then build_cut.py")
