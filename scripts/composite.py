#!/usr/bin/env python3
"""Put the transparent overlay layer on the footage, keeping the footage's original colour.

  composite.py <roughcut_MASTER.mov> <overlay.mov> <out.mp4>

HDR (HLG) footage stays 10-bit HEVC HLG BT.2020: the overlay is converted into HLG with
SDR white at the BT.2408 graphics level (npl=203 -> 75% signal), so white text matches the
footage instead of glaring. SDR footage gets a plain H.264 composite.
"""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from common import ff, probe

src, ovl, out = sys.argv[1:4]
p = probe(src)
if p["hlg"]:
    fc = ("[1:v]split[c][a];[a]alphaextract,format=gray10le[al];"
          "[c]format=gbrpf32le,zscale=tin=iec61966-2-1:pin=bt709:t=arib-std-b67:p=bt2020:npl=203:m=bt2020nc:r=tv,format=yuv444p10le[cc];"
          "[cc][al]alphamerge[o];[0:v]format=yuv444p10le[b];[b][o]overlay=format=yuv444p10:eof_action=pass,format=yuv420p10le[v]")
    venc = ["-c:v", "libx265", "-crf", "14", "-preset", "medium", "-tag:v", "hvc1",
            "-x265-params", "log-level=error:colorprim=bt2020:transfer=arib-std-b67:colormatrix=bt2020nc",
            "-color_primaries", "bt2020", "-color_trc", "arib-std-b67", "-colorspace", "bt2020nc"]
else:
    fc = "[0:v][1:v]overlay=eof_action=pass,format=yuv420p[v]"
    venc = ["-c:v", "libx264", "-crf", "17", "-preset", "slow"]
ff("-i", src, "-i", ovl, "-filter_complex", fc, "-map", "[v]", "-map", "0:a", *venc, "-c:a", "aac", "-b:a", "192k",
   "-movflags", "+faststart", out)
q = probe(out)
print(f"{out}: {q['duration']:.1f}s {q['width']}x{q['height']} {'HDR HLG' if q['hlg'] else 'SDR'} {q['bit_rate'] / 1e6:.1f} Mbps")
