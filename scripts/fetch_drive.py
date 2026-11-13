#!/usr/bin/env python3
"""Download videos from a public ("anyone with the link") Google Drive folder.

  fetch_drive.py <folder-url> <out-dir> [--sub Raw/timer-toddlers] [--list]

Drive redirects normal downloads to randomly named googleusercontent hosts that a
restricted network blocks, so each file is fetched from drive.usercontent.google.com.
Files already downloaded with the same size are skipped.
"""
import argparse, os, subprocess, sys
import gdown

VIDEO = (".mov", ".mp4", ".m4v", ".mkv", ".webm")

ap = argparse.ArgumentParser()
ap.add_argument("url")
ap.add_argument("out")
ap.add_argument("--sub", default="", help="only files under this subfolder path, e.g. Raw/timer")
ap.add_argument("--list", action="store_true", help="only list files")
ap.add_argument("--all", action="store_true", help="include non-video files")
a = ap.parse_args()

files = gdown.download_folder(url=a.url, skip_download=True, quiet=True, output=a.out) or []
picked = []
for f in files:
    rel = os.path.relpath(f.local_path, a.out)
    if a.sub and not rel.replace("\\", "/").startswith(a.sub.strip("/") + "/"):
        continue
    if not a.all and not rel.lower().endswith(VIDEO):
        continue
    picked.append((f.id, rel))

for fid, rel in picked:
    print(f"{fid}  {rel}")
if a.list:
    sys.exit(0)
if not picked:
    sys.exit("no matching files (is the folder shared as 'anyone with the link'? is --sub right?)")

for fid, rel in picked:
    dst = os.path.join(a.out, rel)
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    if os.path.exists(dst) and os.path.getsize(dst) > 0:
        print(f"skip (exists) {rel}")
        continue
    url = f"https://drive.usercontent.google.com/download?id={fid}&export=download&confirm=t"
    r = subprocess.run(["curl", "-sSL", "--retry", "4", "-m", "1800", "-o", dst, "-w", "%{http_code} %{size_download}", url],
                       capture_output=True, text=True)
    code = r.stdout.split()[0] if r.stdout else "?"
    if r.returncode or code != "200":
        print(f"FAILED {rel}: http {code} {r.stderr.strip()}", file=sys.stderr)
        if os.path.exists(dst):
            os.remove(dst)
        continue
    print(f"ok {rel} ({int(r.stdout.split()[1]) / 1e6:.1f} MB)")
