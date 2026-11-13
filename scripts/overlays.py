#!/usr/bin/env python3
"""Generate and render the overlay layer (captions, stickers, optional titles) with Hyperframes.

  overlays.py <overlays.json> <out-dir> [--render] [--preview-on <video>]

Renders a TRANSPARENT ProRes 4444 layer (overlay.mov) that composite.py puts on the
original footage. Rendering the overlay alone avoids Hyperframes' HDR mode, which left
old captions stacked on screen.

overlays.json (times are seconds in the cut; see templates/overlays.example.json):
  duration          cut length (from edl_out.json output_duration)
  captions          path to SRT (relative to the json)
  highlight         words/phrases shown in neon yellow, e.g. ["uno,", "diez segundos"]
  skip_captions     caption texts to leave out, e.g. ["nadie me dijo esto"]
  stickers          [{"type": "share"|"comment"|"clock", "start": s, "end": s, "text": "¡SE ACABÓ<br>EL TIMER!"}]
  titles            optional; omit when titles are added in CapCut:
      series: {"start":0,"end":3.45,"line":"Cosas importantes de bebés","age":"2-4 años","click_at":1.02}
      topic:  {"start":1.6,"end":54.8,"word1":"EL TIMER","word2":"CON TODDLERS"}
      subs:   [{"start":9.57,"end":16.66,"text":"1. DALE OPCIONES"}, ...]
All positions are inside Instagram's Reels safe area (see STYLE_GUIDE.md / safezone.py).
"""
import argparse, html, json, os, re, shutil, subprocess, sys
sys.path.insert(0, os.path.dirname(__file__))
from common import REPO, FFMPEG, FFPROBE, read_srt

PALE_BLUE, BUTTER, CREAM, SKY, NEON = "#BCE3FB", "#FBFFB8", "#FCFEC0", "#63BFFA", "#ECFF0E"
GSAP = '<script src="assets/vendor/gsap.min.js"></script>'
FONTS = """@font-face { font-family:"Modern Match"; src:url("assets/fonts/baloo-2-latin-800-normal.woff2") format("woff2"); font-weight:800; }
    @font-face { font-family:"Lilita One"; src:url("assets/fonts/lilita-one-latin-400-normal.woff2") format("woff2"); }
    @font-face { font-family:"Poppins Local"; src:url("assets/fonts/poppins-latin-600-normal.woff2") format("woff2"); font-weight:600; }
    @font-face { font-family:"Poppins Local"; src:url("assets/fonts/poppins-latin-800-normal.woff2") format("woff2"); font-weight:800; }"""

ap = argparse.ArgumentParser()
ap.add_argument("config"); ap.add_argument("out")
ap.add_argument("--render", action="store_true")
a = ap.parse_args()
C = json.load(open(a.config)); base = os.path.dirname(os.path.abspath(a.config))
DUR = float(C["duration"])
P = os.path.join(a.out, "overlay_project")
shutil.rmtree(P, ignore_errors=True)
os.makedirs(f"{P}/compositions"); shutil.copytree(f"{REPO}/assets", f"{P}/assets")

# ---------------- captions ----------------
caps = read_srt(os.path.join(base, C["captions"]))
skip = [s.lower() for s in C.get("skip_captions", [])]
caps = [c for c in caps if c[2].lower() not in skip]
HL = C.get("highlight", [])
def mark(txt):
    out = html.escape(txt)
    for w in HL:
        out = re.sub(rf"(?<![\w>]){re.escape(html.escape(w))}", f'<span class="hl">{html.escape(w)}</span>', out, count=1)
    return out
cd, ct = [], []
for i, (s, e, txt) in enumerate(caps):
    cd.append(f'    <div id="cap{i}" class="clip cap" data-start="{s:.3f}" data-duration="{e - s:.3f}"><span class="ci">{mark(txt)}</span></div>')
    ct.append(f'  tl.fromTo("#cap{i} .ci",{{scale:0.92,opacity:0}},{{scale:1,opacity:1,duration:0.12,ease:"power2.out"}},{s:.3f});')
captions = f"""<template>
  <style>
    {FONTS}
    #root {{ position:absolute; inset:0; width:1080px; height:1920px; pointer-events:none; }}
    /* x 100-890 keeps clear of the Reels button column (x>909 below y 1173) */
    .cap {{ position:absolute; left:100px; right:190px; top:1360px; text-align:center; }}
    .ci {{ display:inline-block; font-family:"Poppins Local"; font-weight:600; font-size:50px; line-height:1.18; color:#fff;
           -webkit-text-stroke:5px rgba(0,0,0,.85); paint-order:stroke fill; text-shadow:0 3px 8px rgba(0,0,0,.5); }}
    .hl {{ color:{NEON}; font-weight:800; }}
  </style>
  <div id="root" data-composition-id="captions" data-width="1080" data-height="1920" data-start="0" data-duration="{DUR}" data-layout-allow-overlap>
{chr(10).join(cd)}
  </div>
  {GSAP}
  <script>
  const tl = gsap.timeline({{paused:true}});
{chr(10).join(ct)}
  window.__timelines["captions"] = tl;
  </script>
</template>
"""

# ---------------- stickers ----------------
PLANE = '<svg viewBox="0 0 24 24" width="120" height="120"><path d="M2 11.5L22 3l-6.5 18-3.6-7.2z" fill="#fff" stroke="#111" stroke-width="1.2" stroke-linejoin="round"/><path d="M11.9 13.8L22 3" stroke="#111" stroke-width="1.2"/></svg>'
BUBBLE = f'<svg viewBox="0 0 24 24" width="120" height="120"><path d="M4 4h16a2 2 0 012 2v9a2 2 0 01-2 2H10l-5 4v-4H4a2 2 0 01-2-2V6a2 2 0 012-2z" fill="{SKY}" stroke="#111" stroke-width="1.2"/><circle cx="8" cy="10.5" r="1.3" fill="#fff"/><circle cx="12" cy="10.5" r="1.3" fill="#fff"/><circle cx="16" cy="10.5" r="1.3" fill="#fff"/></svg>'
CLOCK = '<svg viewBox="0 0 24 24" width="130" height="130"><circle cx="12" cy="13" r="8.5" fill="#fff" stroke="#111" stroke-width="1.4"/><path d="M12 8v5l3 2" stroke="#E5443B" stroke-width="1.6" fill="none" stroke-linecap="round"/><path d="M5 4.5l-2.5 2.2M19 4.5l2.5 2.2" stroke="#111" stroke-width="1.6" stroke-linecap="round"/></svg>'
sd, st = [], []
for i, s in enumerate(C.get("stickers", [])):
    a0, d = s["start"], s["end"] - s["start"]
    if s["type"] in ("share", "comment"):
        svg = PLANE if s["type"] == "share" else BUBBLE
        sd.append(f'    <div id="st{i}" class="clip ico" data-start="{a0:.2f}" data-duration="{d:.2f}">{svg}</div>')
        st.append(f'  tl.fromTo("#st{i} svg",{{scale:0,rotation:-30}},{{scale:1,rotation:0,duration:0.3,ease:"back.out(2.5)"}},{a0:.2f});')
        if s["type"] == "share":
            st.append(f'  tl.to("#st{i} svg",{{x:160,y:-160,opacity:0,duration:0.4,ease:"power2.in"}},{a0 + d - 0.45:.2f});')
        else:
            st.append(f'  tl.to("#st{i} svg",{{scale:1.12,duration:0.25,yoyo:true,repeat:3,ease:"sine.inOut"}},{a0 + 0.45:.2f});')
    elif s["type"] == "clock":
        txt = f'<br><span class="gagtxt">{s["text"]}</span>' if s.get("text") else ""
        sd.append(f'    <div id="st{i}" class="clip gag" data-start="{a0:.2f}" data-duration="{d:.2f}"><div class="clock">{CLOCK}</div>{txt}</div>')
        st.append(f'  tl.fromTo("#st{i} .clock",{{scale:0}},{{scale:1,duration:0.25,ease:"back.out(3)"}},{a0:.2f});')
        st.append(f'  tl.to("#st{i} .clock",{{rotation:14,duration:0.06,yoyo:true,repeat:9,ease:"none"}},{a0 + 0.1:.2f});')
        if txt:
            st.append(f'  tl.fromTo("#st{i} .gagtxt",{{scale:0.4,opacity:0}},{{scale:1,opacity:1,duration:0.3,ease:"back.out(2.2)"}},{a0 + 0.15:.2f});')
        st.append(f'  tl.to("#st{i}",{{opacity:0,duration:0.3}},{a0 + d - 0.35:.2f});')
stickers = f"""<template>
  <style>
    {FONTS}
    #root {{ position:absolute; inset:0; width:1080px; height:1920px; pointer-events:none; }}
    .ico {{ position:absolute; left:680px; top:1180px; }}
    .gag {{ position:absolute; left:0; right:0; top:760px; text-align:center; }}
    .gagtxt {{ display:inline-block; font-family:"Lilita One"; font-size:96px; color:{NEON}; line-height:1.0; text-shadow:0 4px 10px rgba(0,0,0,.45); -webkit-text-stroke:2px #111; }}
    .clock {{ display:inline-block; margin-bottom:10px; }}
  </style>
  <div id="root" data-composition-id="stickers" data-width="1080" data-height="1920" data-start="0" data-duration="{DUR}" data-layout-allow-overlap>
{chr(10).join(sd)}
  </div>
  {GSAP}
  <script>
  const tl = gsap.timeline({{paused:true}});
{chr(10).join(st)}
  window.__timelines["stickers"] = tl;
  </script>
</template>
"""

# ---------------- optional titles ----------------
T = C.get("titles") or {}
title_html = ""
if T.get("series"):
    S = T["series"]; ck = S.get("click_at", S["start"] + 1.0) - S["start"]
    title_html += f"""
    <div id="series" class="clip" data-start="{S['start']:.2f}" data-duration="{S['end'] - S['start']:.2f}">
      <div class="swrap"><div><span id="p1" class="pill">{html.escape(S['line'])}</span></div>
      <div id="p2wrap"><div id="frame"></div><span id="p2" class="pill">{html.escape(S.get('age', ''))}</span>
      <div id="cursor"><svg viewBox="0 0 24 24" width="84" height="84"><path d="M4 2l15 11-6.6 1.2 3.9 7.4-2.8 1.4-3.9-7.5L4 20z" fill="#fff" stroke="#111" stroke-width="1.4" stroke-linejoin="round"/></svg></div></div></div>
    </div>"""
    series_tw = f"""
  tl.fromTo("#p1",{{scale:0.6,opacity:0}},{{scale:1,opacity:1,duration:0.28,ease:"back.out(2)"}},{S['start'] + 0.05:.2f});
  tl.fromTo("#p2",{{opacity:0,y:20}},{{opacity:1,y:0,duration:0.22}},{S['start'] + 0.45:.2f});
  tl.fromTo("#frame",{{opacity:0}},{{opacity:1,duration:0.1}},{S['start'] + 0.55:.2f});
  tl.fromTo("#cursor",{{x:220,y:160,opacity:0}},{{x:0,y:0,opacity:1,duration:0.45,ease:"power2.out"}},{S['start'] + 0.55:.2f});
  tl.to("#cursor",{{scale:0.82,duration:0.08,yoyo:true,repeat:1}},{S['start'] + ck:.2f});
  tl.to("#p2",{{scale:1.08,duration:0.1,yoyo:true,repeat:1}},{S['start'] + ck + 0.02:.2f});
  tl.to(["#frame","#cursor"],{{opacity:0,duration:0.2}},{S['start'] + ck + 0.5:.2f});
  tl.to(".swrap",{{opacity:0,y:-20,duration:0.3}},{S['end'] - 0.35:.2f});"""
else:
    series_tw = ""
topic_tw = ""
if T.get("topic"):
    tp = T["topic"]
    title_html += f"""
    <div id="topic" class="clip" data-start="{tp['start']:.2f}" data-duration="{tp['end'] - tp['start']:.2f}"><div class="sq"><span id="w1">{html.escape(tp['word1'])} </span><span id="w2">{html.escape(tp.get('word2', ''))}</span></div></div>"""
    topic_tw += f"""
  tl.fromTo("#w1",{{y:-40,opacity:0}},{{y:0,opacity:1,duration:0.3,ease:"back.out(2)"}},{tp['start']:.2f});
  tl.fromTo("#w2",{{y:-40,opacity:0}},{{y:0,opacity:1,duration:0.3,ease:"back.out(2)"}},{tp['start'] + 0.12:.2f});
  tl.to("#topic .sq",{{opacity:0,duration:0.3}},{tp['end'] - 0.35:.2f});"""
for i, sb in enumerate(T.get("subs", [])):
    title_html += f"""
    <div id="sub{i}" class="clip sub" data-start="{sb['start']:.2f}" data-duration="{sb['end'] - sb['start']:.2f}"><div class="sq"><span class="st">{html.escape(sb['text'])}</span></div></div>"""
    topic_tw += f"""
  tl.fromTo("#sub{i} .st",{{clipPath:"inset(0 100% 0 0)"}},{{clipPath:"inset(0 0% 0 0)",duration:0.45,ease:"steps({len(sb['text'])})"}},{sb['start']:.2f});"""
titles = f"""<template>
  <style>
    {FONTS}
    #root {{ position:absolute; inset:0; width:1080px; height:1920px; pointer-events:none; }}
    .swrap {{ position:absolute; left:0; right:0; top:930px; text-align:center; }}
    .pill {{ display:inline-block; font-family:"Poppins Local"; font-weight:800; letter-spacing:-0.045em; color:#000; padding:2px 18px 6px; line-height:1.1; }}
    #p1 {{ background:{PALE_BLUE}; font-size:64px; }}
    #p2wrap {{ margin-top:18px; position:relative; display:inline-block; }}
    #p2 {{ background:{BUTTER}; font-size:68px; }}
    #frame {{ position:absolute; left:-26px; right:-26px; top:-20px; bottom:-20px; border:2px dashed {SKY}; }}
    #cursor {{ position:absolute; left:58%; top:60%; }}
    .sq {{ display:inline-block; transform:scaleX(0.88); transform-origin:center; }}
    #topic {{ position:absolute; left:0; right:0; top:262px; line-height:1; text-align:center; font-family:"Modern Match"; font-weight:800; font-size:88px;
             -webkit-text-stroke:3px #1a1a1a; paint-order:stroke fill; text-shadow:0 4px 0 #1a1a1a, 0 6px 14px rgba(0,0,0,.35); }}
    #w1 {{ color:{CREAM}; }} #w2 {{ color:{SKY}; }}
    .sub {{ position:absolute; left:0; right:0; top:362px; line-height:1; text-align:center; }}
    .st {{ display:inline-block; font-family:"Modern Match"; font-weight:800; font-size:64px; color:{CREAM}; letter-spacing:0.02em;
           -webkit-text-stroke:2px #1a1a1a; paint-order:stroke fill; text-shadow:0 3px 0 #1a1a1a; }}
  </style>
  <div id="root" data-composition-id="titles" data-width="1080" data-height="1920" data-start="0" data-duration="{DUR}" data-layout-allow-overlap>{title_html}
  </div>
  {GSAP}
  <script>
  const tl = gsap.timeline({{paused:true}});{series_tw}{topic_tw}
  window.__timelines["titles"] = tl;
  </script>
</template>
"""

hosts = []
for name, z, kind in [("titles", 2, "graphics"), ("stickers", 3, "graphics"), ("captions", 4, "captions")]:
    hosts.append(f'      <div id="{name}" class="clip layer" style="z-index:{z}" data-composition-id="{name}" data-composition-src="compositions/{name}.html" data-start="0" data-duration="{DUR}" data-track-index="{z}" data-track-kind="{kind}"></div>')
root = f"""<!doctype html>
<html lang="en" data-resolution="portrait">
  <head>
    <meta charset="UTF-8" /><meta name="viewport" content="width=1080, height=1920" />
    <title>Overlay layer</title>
    {GSAP}
    <style>
      * {{ margin:0; padding:0; box-sizing:border-box; }}
      html, body {{ width:1080px; height:1920px; overflow:hidden; background:transparent; }}
      #root {{ position:relative; width:1080px; height:1920px; overflow:hidden; }}
      .layer {{ position:absolute; inset:0; }}
    </style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-duration="{DUR}" data-width="1080" data-height="1920">
{chr(10).join(hosts)}
    </div>
    <script>
      const tl = gsap.timeline({{ paused: true }});
      window.__timelines["main"] = tl;
    </script>
  </body>
</html>
"""
for n, b in [("captions", captions), ("stickers", stickers), ("titles", titles)]:
    open(f"{P}/compositions/{n}.html", "w").write(b)
open(f"{P}/index.html", "w").write(root)
json.dump({"$schema": "https://hyperframes.heygen.com/schema/hyperframes.json", "paths": {"assets": "assets"}}, open(f"{P}/hyperframes.json", "w"))
print(f"overlay project -> {P}  ({len(caps)} captions, {len(C.get('stickers', []))} stickers, titles: {'yes' if T else 'no'})")

if a.render:
    env = dict(os.environ, HYPERFRAMES_FFMPEG_PATH=FFMPEG, HYPERFRAMES_FFPROBE_PATH=FFPROBE, HYPERFRAMES_SKIP_SKILLS="1")
    out_mov = os.path.abspath(f"{a.out}/overlay.mov")
    r = subprocess.run(["hyperframes", "render", "--format", "mov", "-o", out_mov], cwd=P, env=env, capture_output=True, text=True)
    tail = "\n".join(l for l in (r.stdout + r.stderr).splitlines() if "█" not in l and "░" not in l)[-1500:]
    if r.returncode or not os.path.exists(out_mov):
        sys.exit("render failed:\n" + tail)
    print(f"overlay layer -> {out_mov}")
