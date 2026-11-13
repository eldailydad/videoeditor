#!/usr/bin/env python3
"""Build the rough cut from an edit list (edl.json).

  build_cut.py <edl.json> <out-dir>

edl.json:
  {"sources": {"A": "raw/IMG_0435.mov", "B": "raw/IMG_0436.MOV"},
   "segments": [{"src": "A", "in": 5.45, "out": 7.05, "role": "HOOK", "line": "Nadie me dijo esto."}, ...]}
Source paths are relative to the edl file.

Writes:
  roughcut_MASTER.mov    original colour (HDR stays HDR: 10-bit HEVC HLG), -16..-14 LUFS, for CapCut
  roughcut_preview.mp4   H.264 SDR for any screen; plain conversion (no added contrast/saturation)
  edl_out.json           the edl with output times filled in (for edit tables / overlays)
Segments are cut one at a time (cutting all at once from long 4K files runs out of memory).
"""
import json, os, subprocess, sys
sys.path.insert(0, os.path.dirname(__file__))
from common import FFMPEG, ff, probe

edl_path, out = sys.argv[1], sys.argv[2]
base = os.path.dirname(os.path.abspath(edl_path))
E = json.load(open(edl_path))
src = {k: (v if os.path.isabs(v) else os.path.join(base, v)) for k, v in E["sources"].items()}
info = {k: probe(v) for k, v in src.items()}
hlg = any(i["hlg"] for i in info.values())
fps = E.get("fps") or round(max(i["fps"] for i in info.values()))
os.makedirs(f"{out}/seg", exist_ok=True)

HLG_TAGS = ["-color_primaries", "bt2020", "-color_trc", "arib-std-b67", "-colorspace", "bt2020nc"]
if hlg:
    vcodec = ["-c:v", "libx265", "-crf", "12", "-preset", "fast", "-pix_fmt", "yuv420p10le", "-tag:v", "hvc1",
              "-x265-params", "log-level=error:keyint=30:colorprim=bt2020:transfer=arib-std-b67:colormatrix=bt2020nc", *HLG_TAGS]
else:
    vcodec = ["-c:v", "libx264", "-crf", "12", "-preset", "fast", "-pix_fmt", "yuv420p", "-g", str(fps)]

t = 0.0
with open(f"{out}/seg/list.txt", "w") as lst:
    for i, s in enumerate(E["segments"]):
        d = s["out"] - s["in"]
        o = f"{out}/seg/{i:03d}.mov"
        ff("-ss", f"{s['in']:.3f}", "-i", src[s["src"]], "-t", f"{d:.3f}", "-map", "0:v:0", "-map", "0:a:0",
           "-af", f"afade=t=in:d=0.008,afade=t=out:st={d - 0.008:.3f}:d=0.008",
           *vcodec, "-r", str(fps), "-c:a", "pcm_s16le", "-ar", "48000", o)
        lst.write(f"file '{os.path.abspath(o)}'\n")
        s["out_start"], s["out_end"] = round(t, 3), round(t + d, 3)
        t += d
        print(f"seg {i:03d} {s['out_start']:6.2f}-{s['out_end']:6.2f}  {s.get('role', '')}  {s.get('line', '')[:60]}", flush=True)

joined = f"{out}/seg/joined.mov"
ff("-f", "concat", "-safe", "0", "-i", f"{out}/seg/list.txt", "-c", "copy", joined)

# two-pass loudness normalisation (linear, so dynamics stay natural; true peak limits how loud it gets)
r = subprocess.run([FFMPEG, "-hide_banner", "-i", joined, "-af", "loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"],
                   capture_output=True, text=True).stderr
m = json.loads(r[r.rfind("{"):r.rfind("}") + 1])
ln = (f"loudnorm=I=-14:TP=-1.5:LRA=11:measured_I={m['input_i']}:measured_TP={m['input_tp']}:measured_LRA={m['input_lra']}:"
      f"measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true")
A = ["-af", ln, "-c:a", "aac", "-b:a", "192k", "-ar", "48000"]

ff("-i", joined, "-c:v", "copy", *A, "-movflags", "+faststart", f"{out}/roughcut_MASTER.mov")
# Plain conversion: HLG is designed to look right on SDR screens; tone-mapping filters made skin too red.
ff("-i", joined, "-vf", "format=yuv420p", "-c:v", "libx264", "-crf", "18", "-preset", "medium", "-g", str(fps),
   "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709", *A, "-movflags", "+faststart",
   f"{out}/roughcut_preview.mp4")

E["output_duration"] = round(probe(f"{out}/roughcut_MASTER.mov")["duration"], 3)  # real length (frame rounding)
E["hdr"] = hlg
json.dump(E, open(f"{out}/edl_out.json", "w"), ensure_ascii=False, indent=1)
print(f"\nrough cut {E['output_duration']:.1f}s  ({'HDR HLG' if hlg else 'SDR'})  -> {out}/roughcut_MASTER.mov, roughcut_preview.mp4")
