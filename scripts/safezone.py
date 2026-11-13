#!/usr/bin/env python3
"""Check the overlay layer against Instagram's Reels safe area.

  safezone.py <overlay.mov> [--step 0.25]

Reads the overlay's alpha channel every --step seconds and counts drawn pixels in the
no-text zones of a 1080x1920 Reel:
  top 240 px, bottom 240 px, left 48 px, right 44 px, and the button column
  (x > 909 below y 1173: like / comment / share / audio).
Exit code 1 if anything is drawn there.
"""
import argparse, os, subprocess, sys
import numpy as np
sys.path.insert(0, os.path.dirname(__file__))
from common import FFMPEG, probe

ap = argparse.ArgumentParser(); ap.add_argument("overlay"); ap.add_argument("--step", type=float, default=0.25)
a = ap.parse_args()
p = probe(a.overlay); W, H = 1080, 1920
raw = subprocess.run([FFMPEG, "-v", "error", "-i", a.overlay, "-vf", f"fps=1/{a.step},alphaextract,format=gray", "-f", "rawvideo", "-"],
                     capture_output=True, check=True).stdout
frames = np.frombuffer(raw, np.uint8).reshape(-1, H, W) > 24
zones = {"top": (slice(0, 240), slice(0, W)), "bottom": (slice(1680, H), slice(0, W)),
         "left": (slice(0, H), slice(0, 48)), "right": (slice(0, H), slice(1036, W)),
         "buttons": (slice(1173, H), slice(909, W))}
bad = 0
ys, xs = np.where(frames.any(axis=0))
for i, f in enumerate(frames):
    hits = {k: int(f[z].sum()) for k, z in zones.items()}
    if sum(hits.values()):
        bad += 1
        print(f"  t={i * a.step:6.2f}s  " + "  ".join(f"{k}={v}" for k, v in hits.items() if v))
print(f"checked {len(frames)} frames every {a.step}s; text extent x {xs.min() if len(xs) else '-'}-{xs.max() if len(xs) else '-'}, "
      f"y {ys.min() if len(ys) else '-'}-{ys.max() if len(ys) else '-'}")
print("SAFE: nothing in Instagram's no-text zones" if not bad else f"NOT SAFE: {bad} frames draw in a no-text zone")
sys.exit(1 if bad else 0)
