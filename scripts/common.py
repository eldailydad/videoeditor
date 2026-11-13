"""Shared helpers: tool paths, ffprobe, timestamps."""
import json, os, shutil, subprocess

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# System ffmpeg has libx264/libx265/zscale; a self-built one earlier on PATH may not.
FFMPEG = os.environ.get("EDD_FFMPEG", "/usr/bin/ffmpeg" if os.path.exists("/usr/bin/ffmpeg") else shutil.which("ffmpeg"))
FFPROBE = os.environ.get("EDD_FFPROBE", "/usr/bin/ffprobe" if os.path.exists("/usr/bin/ffprobe") else shutil.which("ffprobe"))
WHISPER_DIR = os.environ.get("EDD_WHISPER_DIR", next((p for p in ["/opt/whisper.cpp", os.path.expanduser("~/tools/whisper.cpp")]
                                                      if os.path.exists(p)), "/opt/whisper.cpp"))
WHISPER_BIN = os.path.join(WHISPER_DIR, "build/bin/whisper-cli")
WHISPER_MODEL = os.environ.get("EDD_WHISPER_MODEL", os.path.join(WHISPER_DIR, "models/ggml-small.bin"))


def run(cmd, **kw):
    return subprocess.run(cmd, check=True, **kw)


def ff(*args):
    run([FFMPEG, "-v", "error", "-y", *args])


def probe(path):
    out = subprocess.run([FFPROBE, "-v", "error", "-show_entries",
                          "format=duration,bit_rate:stream=index,codec_type,codec_name,width,height,r_frame_rate,pix_fmt,color_transfer,color_primaries:stream_side_data=rotation",
                          "-of", "json", path], capture_output=True, text=True, check=True).stdout
    d = json.loads(out)
    v = next((s for s in d["streams"] if s["codec_type"] == "video"), {})
    rot = 0
    for sd in v.get("side_data_list", []) or []:
        rot = int(sd.get("rotation", 0) or 0)
    w, h = v.get("width"), v.get("height")
    if rot in (90, -90, 270, -270):
        w, h = h, w
    num, den = (v.get("r_frame_rate", "30/1").split("/") + ["1"])[:2]
    return {
        "duration": float(d["format"]["duration"]),
        "width": w, "height": h, "fps": round(float(num) / float(den or 1), 3),
        "pix_fmt": v.get("pix_fmt"), "transfer": v.get("color_transfer"),
        "hdr": v.get("color_transfer") in ("arib-std-b67", "smpte2084"),
        "hlg": v.get("color_transfer") == "arib-std-b67",
        "bit_rate": int(d["format"].get("bit_rate", 0) or 0),
    }


def ts(t):
    t = max(0.0, t)
    h, m = int(t // 3600), int(t % 3600 // 60)
    s = t % 60
    ms = int(round((s - int(s)) * 1000))
    if ms == 1000:
        ms = 999
    return f"{h:02d}:{m:02d}:{int(s):02d},{ms:03d}"


def parse_ts(s):
    h, m, rest = s.strip().split(":")
    sec, ms = rest.split(",")
    return int(h) * 3600 + int(m) * 60 + int(sec) + int(ms) / 1000


def read_srt(path):
    caps = []
    for block in open(path, encoding="utf-8").read().strip().split("\n\n"):
        lines = block.strip().split("\n")
        if len(lines) >= 3 and "-->" in lines[1]:
            a, b = lines[1].split("-->")
            caps.append((parse_ts(a), parse_ts(b), " ".join(lines[2:]).strip()))
    return caps


def write_srt(path, caps):
    with open(path, "w", encoding="utf-8") as f:
        for i, (a, b, txt) in enumerate(caps, 1):
            f.write(f"{i}\n{ts(a)} --> {ts(b)}\n{txt}\n\n")
