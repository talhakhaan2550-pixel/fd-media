"""Finance Department's visual system for the studio tools: fonts, colours, icons, the US map and the page shell.

Everything a frame needs is embedded in the page (fonts and backgrounds as data URIs), so pages render the same
in any headless Chromium with no network.
"""
import base64, io, json, os, functools
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(os.path.dirname(HERE), "assets")
SITE = "financedepartmentllc.com"
DISCLAIMER = "General information, not tax or legal advice for your situation."
AI_NOTE = "Narration is an AI voice."


def _b64(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()


@functools.lru_cache(None)
def fonts_css():
    out = []
    for fam, file, w in [("SS4", "source-serif-4-latin-400-normal.woff2", 400), ("SS4", "source-serif-4-latin-600-normal.woff2", 600),
                         ("SS4", "source-serif-4-latin-700-normal.woff2", 700), ("Plex", "ibm-plex-sans-latin-400-normal.woff2", 400),
                         ("Plex", "ibm-plex-sans-latin-500-normal.woff2", 500), ("Plex", "ibm-plex-sans-latin-600-normal.woff2", 600)]:
        out.append("@font-face{font-family:'%s';src:url(data:font/woff2;base64,%s) format('woff2');font-weight:%d;font-display:block}"
                   % (fam, _b64(os.path.join(ASSETS, "fonts", file)), w))
    return "".join(out)


@functools.lru_cache(None)
def gsap_js():
    with open(os.path.join(ASSETS, "gsap.min.js")) as f:
        return f.read()


@functools.lru_cache(None)
def us_map():
    with open(os.path.join(ASSETS, "us-map.json")) as f:
        return json.load(f)


def photo_uri(name):
    return "data:image/jpeg;base64," + _b64(os.path.join(ASSETS, "photos", {"talha": "talha.jpg", "award": "award.jpg"}[name]))


def esc(s):
    return str(s if s is not None else "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


# ---------------------------------------------------------------- backgrounds, drawn once per size with numpy
def _png_uri(arr):
    buf = io.BytesIO()
    Image.fromarray(arr).save(buf, format="PNG", optimize=False, compress_level=3)
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


def _hex(h):
    h = h.lstrip("#")
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], np.float32)


@functools.lru_cache(None)
def backgrounds(w, h):
    """Base layer (gradient and a faint grid fading out from the upper right) and a top layer (vignette and grain)."""
    y, x = np.mgrid[0:h, 0:w].astype(np.float32)
    t = np.clip(0.82 * (y / h) + 0.18 * (x / w), 0, 1)[..., None]
    c0, c1, c2 = _hex("#0B2343"), _hex("#06162D"), _hex("#030B19")
    base = np.where(t < 0.5, c0 + (c1 - c0) * (t / 0.5), c1 + (c2 - c1) * ((t - 0.5) / 0.5))
    tall = h > 1500
    cx, cy, rx, ry = 0.80 * w, (0.30 if tall else 0.18) * h, (760 if tall else 720), (700 if tall else 620)
    d = np.sqrt(((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2)
    mask = np.clip(1 - d / 0.72, 0, 1)
    grid = (((x.astype(int) % 60) == 59) | ((y.astype(int) % 60) == 59)).astype(np.float32)
    base = base + (255 - base) * (0.055 * grid * mask)[..., None]
    base_img = np.clip(base, 0, 255).astype(np.uint8)
    # top layer: a vignette; the film grain is a small tile repeated over the frame
    vx, vy = (x - 0.5 * w) / (1.30 * w / 2), (y - 0.42 * h) / (0.95 * h / 2)
    vd = np.sqrt(vx ** 2 + vy ** 2)
    vig = np.clip((vd - 0.58) / 0.42, 0, 1) * 0.5
    top = np.zeros((h, w, 4), np.uint8)
    top[..., 3] = np.clip(vig * 255, 0, 255).astype(np.uint8)
    return _png_uri(base_img), _png_uri(top)


@functools.lru_cache(None)
def grain_tile():
    rng = np.random.default_rng(3)
    g = rng.normal(0, 1, (256, 256)).astype(np.float32)
    tile = np.zeros((256, 256, 4), np.uint8)
    tile[..., :3] = np.where(g[..., None] > 0, 255, 0).astype(np.uint8)
    tile[..., 3] = np.clip(np.abs(g) * 0.035 * 255, 0, 0.09 * 255).astype(np.uint8)
    return _png_uri(tile)


# ---------------------------------------------------------------- icons (stroke style, 48 unit box)
ICONS = {
    "bars": '<path d="M8 40h32"/><rect x="11" y="24" width="6" height="12" rx="1.5"/><rect x="21" y="16" width="6" height="20" rx="1.5"/><rect x="31" y="8" width="6" height="28" rx="1.5"/>',
    "stack": '<ellipse cx="24" cy="12" rx="13" ry="5"/><path d="M11 12v8c0 2.8 5.8 5 13 5s13-2.2 13-5v-8"/><path d="M11 20v8c0 2.8 5.8 5 13 5s13-2.2 13-5v-8"/><path d="M11 28v8c0 2.8 5.8 5 13 5s13-2.2 13-5v-8"/>',
    "badge": '<rect x="7" y="10" width="34" height="26" rx="4"/><circle cx="18" cy="21" r="4.5"/><path d="M11.5 31c1.4-3 3.8-4.5 6.5-4.5s5.1 1.5 6.5 4.5"/><path d="M28 19h8M28 25h6"/>',
    "house": '<path d="M7 22 24 8l17 14"/><path d="M11 19v19h26V19"/><path d="M20 38V27h8v11"/>',
    "check": '<path d="M10 25l9 9 19-20"/>',
    "person": '<circle cx="24" cy="16" r="7.5"/><path d="M9 41c1.8-8 7.6-12.5 15-12.5S37.2 33 39 41"/>',
    "people": '<circle cx="17" cy="17" r="6"/><circle cx="32" cy="15" r="5"/><path d="M5 39c1.4-6.4 6-10 12-10s10.6 3.6 12 10"/><path d="M29 26c5.5 0 9.4 3.2 11 9"/>',
    "bank": '<path d="M6 18 24 8l18 10z"/><path d="M10 22v13M18 22v13M30 22v13M38 22v13"/><path d="M6 39h36"/>',
    "doc": '<path d="M13 6h15l9 9v27H13z"/><path d="M28 6v9h9"/><path d="M18 24h14M18 30h14M18 36h9"/>',
    "calendar": '<rect x="8" y="11" width="32" height="29" rx="4"/><path d="M8 19h32M16 7v8M32 7v8"/>',
    "warning": '<path d="M24 7 43 40H5z"/><path d="M24 19v10M24 34.5v.5"/>',
    "clock": '<circle cx="24" cy="24" r="16"/><path d="M24 15v10l7 4"/>',
    "dollar": '<circle cx="24" cy="24" r="17"/><path d="M29 17.5c-1.2-1.7-3.2-2.5-5.2-2.5-3 0-5.3 1.6-5.3 4.2 0 6 10.9 3 10.9 9.2 0 2.7-2.4 4.6-5.6 4.6-2.4 0-4.6-1-5.8-2.8M24 11.5v3.5M24 33.5v3"/>',
    "chart": '<path d="M7 40h34"/><path d="M9 33l9-9 7 6 13-14"/><path d="M31 16h7v7"/>',
    "shield": '<path d="M24 6l15 6v10c0 9.5-6.4 16.6-15 20-8.6-3.4-15-10.5-15-20V12z"/><path d="M17 24l5 5 9-10"/>',
    "globe": '<circle cx="24" cy="24" r="17"/><path d="M7 24h34M24 7c4.6 4.7 7 10.3 7 17s-2.4 12.3-7 17c-4.6-4.7-7-10.3-7-17s2.4-12.3 7-17z"/>',
    "send": '<path d="M41 7 21 27"/><path d="M41 7 28 41l-7-14-14-7z"/>',
    "mail": '<rect x="6" y="11" width="36" height="26" rx="3"/><path d="M7 13l17 13 17-13"/>',
    "search": '<circle cx="21" cy="21" r="12"/><path d="M30 30l10 10"/>',
    "lock": '<rect x="10" y="21" width="28" height="20" rx="3"/><path d="M16 21v-6a8 8 0 0 1 16 0v6"/>',
    "building": '<path d="M9 41V9h20v32M29 19h10v22"/><path d="M15 15h3M21 15h3M15 22h3M21 22h3M15 29h3M21 29h3M33 26h2M33 32h2M6 41h36"/>',
    "rocket": '<path d="M24 6c6 4 9 11 9 19l-4 8H19l-4-8c0-8 3-15 9-19z"/><circle cx="24" cy="20" r="3.5"/><path d="M19 33l-5 6 6-1M29 33l5 6-6-1"/>',
    "scale": '<path d="M24 8v32M14 40h20M10 14h28"/><path d="M10 14l-5 12h10zM38 14l-5 12h10z"/>',
    "list": '<path d="M18 13h22M18 24h22M18 35h22"/><circle cx="9" cy="13" r="2"/><circle cx="9" cy="24" r="2"/><circle cx="9" cy="35" r="2"/>',
    "reply": '<path d="M19 13 8 24l11 11"/><path d="M8 24h20c7 0 12 5 12 12"/>',
    "arrow": '<path d="M6 24h34M30 14l10 10-10 10"/>',
}


def ic(name, size=48, color="#4BE3AA", sw=2.4):
    body = ICONS.get(name, ICONS["doc"])
    return ('<svg width="%d" height="%d" viewBox="0 0 48 48" fill="none" stroke="%s" stroke-width="%s" stroke-linecap="round" '
            'stroke-linejoin="round" style="flex:none">%s</svg>' % (size, size, color, sw, body))


ARROW = ('<svg width="32" height="18" viewBox="0 0 34 20" style="flex:none"><path d="M2 10h28M22 2l8 8-8 8" fill="none" stroke="currentColor" '
         'stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"/></svg>')
WAVE = ('<svg width="22" height="18" viewBox="0 0 22 18"><path d="M2 7v4M6 4v10M10 1v16M14 5v8M18 7v4" stroke="#6AF3C0" '
        'stroke-width="2.2" stroke-linecap="round"/></svg>')


# ---------------------------------------------------------------- the US map
def state_shape(code, size, d=0.3, anim=True):
    s = us_map()["states"][code]["shape"]
    a = ' data-a="draw" data-d="%s" data-dur="0.9"' % d if anim else ""
    return ('<svg width="%d" height="%d" viewBox="0 0 400 400" style="overflow:visible"><path%s d="%s" fill="rgba(21,183,129,.10)" '
            'stroke="#4BE3AA" stroke-width="2.5" vector-effect="non-scaling-stroke" stroke-linejoin="round" '
            'style="filter:drop-shadow(0 0 16px rgba(21,183,129,.55))"/></svg>' % (size, size, a, s))


def usmap(width, states=(), labels=None, d=0.3, pins=True, faint=False, uid="m", anim=True):
    m = us_map()
    s = width / m["w"]
    h = m["h"] * s
    small = width < 400
    A = (lambda k, dd: ' data-a="%s" data-d="%.2f"' % (k, dd)) if anim else (lambda k, dd: "")
    hl = ""
    for code in states:
        hl += ('<path d="%s" fill="rgba(21,183,129,.42)" stroke="#6AF3C0" stroke-width="%.2f" stroke-linejoin="round" filter="url(#gl%s)"%s/>'
               % (m["states"][code]["albers"], 2.2 / s if small else 2.2, uid, A("fade", d + 0.35)))
    pin, lab = "", ""
    if pins:
        for i, code in enumerate(states):
            cx, cy = m["states"][code]["c"]
            pin += ('<g%s style="transform-origin:%spx %spx"><circle cx="%s" cy="%s" r="17" fill="none" stroke="rgba(106,243,192,.55)" stroke-width="2"/>'
                    '<circle cx="%s" cy="%s" r="7" fill="#B9FBE2"/></g>' % (A("pop", d + 0.6 + i * 0.15), cx, cy, cx, cy, cx, cy))
            if labels is not False:
                name = (labels or {}).get(code, m["states"][code]["name"])
                lab += ('<div%s style="position:absolute;left:%.0fpx;top:%.0fpx;transform:translateX(-50%%);display:flex;flex-direction:column;align-items:center">'
                        '<div class="maplabel">%s</div><div style="width:2px;height:40px;background:linear-gradient(#6AF3C0,rgba(106,243,192,0))"></div></div>'
                        % (A("up", d + 0.75 + i * 0.15), cx * s, cy * s - 96, esc(name)))
    return ('<div style="position:relative;width:%dpx;height:%.0fpx;opacity:%s"><svg viewBox="0 0 %d %d" width="%d" height="%.0f" '
            'style="overflow:visible;position:absolute;inset:0"><defs><filter id="gl%s" x="-50%%" y="-50%%" width="200%%" height="200%%">'
            '<feGaussianBlur stdDeviation="7" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter></defs>'
            '<path d="%s" fill="rgba(255,255,255,.04)" stroke="rgba(255,255,255,.30)" stroke-width="%.2f"%s/>'
            '<path d="%s" fill="none" stroke="rgba(255,255,255,.13)" stroke-width="%.2f"%s/>%s%s</svg>%s</div>'
            % (width, h, ".55" if faint else "1", m["w"], m["h"], width, h, uid, m["nation"], 1.2 / s if small else 1.3, A("fade", d),
               m["mesh"], 0.8 / s if small else 0.9, A("fade", d + 0.1), hl, pin, lab))


# ---------------------------------------------------------------- shared CSS
CSS = """
:root{--navy:#06162D;--em:#0B7955;--em2:#15B781;--off:#F9FBFA;--grey:#C9D1DB;--mute:#8C99AB;--amber:#F2B544;--red:#FF5A5F}
*{box-sizing:border-box;margin:0;padding:0}
html,body{background:#06162D}
.slide{position:relative;width:1080px;height:1350px;overflow:hidden;color:var(--off);font-family:'Plex';background:#06162D}
.tall .slide{height:1920px}
.bg,.ov{position:absolute;inset:0;width:100%;height:100%;display:block;pointer-events:none}
.bg{z-index:0}.ov{z-index:20}
.grain{position:absolute;inset:0;z-index:21;pointer-events:none;background-repeat:repeat}
.bgl{position:absolute;border-radius:50%;pointer-events:none;z-index:1;will-change:transform}
.g1{width:1100px;height:900px;right:-330px;top:-300px;background:radial-gradient(closest-side,rgba(21,183,129,.32),rgba(21,183,129,.10) 55%,transparent)}
.g2{width:1000px;height:1000px;left:-420px;bottom:-420px;background:radial-gradient(closest-side,rgba(52,110,220,.28),rgba(52,110,220,.08) 55%,transparent)}
.tall .g1{top:-60px}.tall .g2{bottom:-120px}
.top{position:absolute;left:72px;right:72px;top:62px;display:flex;align-items:center;justify-content:space-between;z-index:5}
.brand{display:flex;align-items:center;gap:16px;font-family:'SS4';font-weight:600;font-size:29px;color:#EEF3F1;white-space:nowrap}
.mark{width:54px;height:54px;border-radius:7.5px;background:#0B7955;display:grid;place-items:center;font-family:'SS4';font-weight:600;font-size:30px;line-height:1;color:#fff;
 box-shadow:0 10px 30px rgba(11,121,85,.55),inset 0 1px 0 rgba(255,255,255,.22);flex:none}
.count{font-weight:500;font-size:22px;letter-spacing:.16em;color:var(--mute)}
.count b{color:#fff;font-weight:600}
.content{position:absolute;left:72px;right:72px;top:168px;bottom:118px;display:flex;flex-direction:column;z-index:4}
.kicker{align-self:flex-start;display:inline-flex;align-items:center;gap:14px;padding:11px 22px 11px 18px;border-radius:999px;border:1px solid rgba(21,183,129,.5);
 background:rgba(21,183,129,.11);color:#8BF0CA;font-weight:600;font-size:21px;letter-spacing:.15em;text-transform:uppercase;white-space:nowrap}
.kicker i{width:10px;height:10px;border-radius:50%;background:var(--em2);box-shadow:0 0 14px 2px rgba(21,183,129,.9)}
h1,h2{font-family:'SS4';font-weight:600;letter-spacing:-.02em;color:#F7FAF9;text-wrap:balance}
h1{font-size:84px;line-height:1.04}
h2{font-size:70px;line-height:1.05}
.em{background:linear-gradient(100deg,#8CF7CF 0%,#2AD196 45%,#14A374 100%);-webkit-background-clip:text;background-clip:text;color:transparent}
.body{font-size:30px;line-height:1.45;color:var(--grey)}
.body b{color:#fff;font-weight:600}
.card{position:relative;border-radius:30px;background:linear-gradient(180deg,rgba(255,255,255,.085),rgba(255,255,255,.02));border:1px solid rgba(255,255,255,.13);
 box-shadow:0 36px 80px rgba(0,0,0,.42),inset 0 1px 0 rgba(255,255,255,.13)}
.card.hl{border-color:rgba(60,220,160,.45);box-shadow:0 36px 80px rgba(0,0,0,.42),0 0 50px rgba(21,183,129,.20),inset 0 1px 0 rgba(255,255,255,.16)}
.big{font-family:'SS4';font-weight:700;letter-spacing:-.035em;line-height:.92;background:linear-gradient(180deg,#C2FCE5 0%,#41DDA5 45%,#0F8C61 100%);
 -webkit-background-clip:text;background-clip:text;color:transparent;filter:drop-shadow(0 12px 34px rgba(21,183,129,.35));white-space:nowrap}
.label{font-weight:600;font-size:19px;letter-spacing:.16em;text-transform:uppercase;color:#86E9C2}
.small{font-size:23px;line-height:1.35;color:var(--grey)}
.cal{width:176px;border-radius:24px;overflow:hidden;background:#F4F7F6;color:#06162D;box-shadow:0 26px 60px rgba(0,0,0,.5);text-align:center;flex:none}
.cal .m{background:#0B7955;color:#fff;font-weight:600;font-size:22px;letter-spacing:.2em;padding:11px 6px 10px;white-space:nowrap}
.cal .d{font-family:'SS4';font-weight:700;font-size:96px;line-height:1.02;padding:8px 0 0;letter-spacing:-.02em}
.cal .s{font-weight:600;font-size:16px;letter-spacing:.08em;color:#4E596A;padding:0 10px 16px}
.dots{position:absolute;left:0;right:0;bottom:56px;display:flex;justify-content:center;gap:12px;z-index:5}
.dots span{width:12px;height:12px;border-radius:99px;background:rgba(255,255,255,.22)}
.dots span.on{width:44px;background:linear-gradient(90deg,#41DDA5,#15B781);box-shadow:0 0 14px rgba(21,183,129,.7)}
.cta{display:inline-flex;align-items:center;gap:16px;padding:24px 42px;border-radius:999px;font-weight:600;font-size:30px;color:#04150E;
 background:linear-gradient(180deg,#5CF0B6,#16B07B);box-shadow:0 18px 54px rgba(21,183,129,.5),inset 0 1px 0 rgba(255,255,255,.5);white-space:nowrap}
.fine{font-size:18px;color:#7D8A9C;letter-spacing:.01em}
.row{display:flex;gap:20px}
.sp{flex:1}
.chip{display:inline-flex;align-items:center;gap:12px;padding:13px 20px;border-radius:14px;background:rgba(21,183,129,.10);border:1px solid rgba(21,183,129,.35);
 color:#D6FBEB;font-weight:500;font-size:24px;line-height:1.25}
.maplabel{padding:9px 16px;border-radius:12px;background:rgba(6,22,45,.82);border:1px solid rgba(106,243,192,.5);font-weight:600;font-size:21px;letter-spacing:.12em;
 text-transform:uppercase;color:#C9FBE7;white-space:nowrap;box-shadow:0 10px 30px rgba(0,0,0,.4)}
.quote{font-family:'SS4';font-weight:600;font-size:46px;line-height:1.18;color:#F3F8F6}
.qm{font-family:'SS4';font-weight:700;font-size:120px;line-height:.6;color:#2AD196;opacity:.9}
.seal{width:96px;height:96px;border-radius:50%;display:grid;place-items:center;background:radial-gradient(circle at 35% 30%,#7CF5C6,#12996B 70%);
 box-shadow:0 0 0 8px rgba(21,183,129,.15),0 18px 50px rgba(21,183,129,.45);flex:none}
.ico{width:66px;height:66px;border-radius:18px;display:grid;place-items:center;background:rgba(21,183,129,.13);border:1px solid rgba(21,183,129,.35);flex:none}
.tone-amber{background:linear-gradient(180deg,#FFE7B0 0%,#FFC85C 45%,#B97A0E 100%)!important;-webkit-background-clip:text!important;background-clip:text!important;filter:drop-shadow(0 12px 34px rgba(242,181,68,.35))!important}
.tone-red{background:linear-gradient(180deg,#FFD0D2 0%,#FF6B70 45%,#B4242B 100%)!important;-webkit-background-clip:text!important;background-clip:text!important;filter:drop-shadow(0 12px 34px rgba(255,90,95,.4))!important}
.tone-white{background:linear-gradient(180deg,#FFFFFF 0%,#DCE6EE 100%)!important;-webkit-background-clip:text!important;background-clip:text!important;filter:none!important}
"""

# Entrance animations: every element with data-a gets a tween; window.seek(t) draws time t; window.final() the built slide.
RUNTIME = r"""
<script>
gsap.ticker.lagSmoothing(0);
const TL = gsap.timeline({paused:true}); window.TLREF=TL;
const ease='power3.out'; let auto=0.15;
const fmt=(v,dec)=>v.toLocaleString('en-US',{minimumFractionDigits:dec,maximumFractionDigits:dec});
// big figures shrink until they fit their box (run once the fonts are in: window.fitNow)
window.fitNow=()=>{const tl=window.TLREF; if(tl) tl.seek(tl.duration(),false);
document.querySelectorAll('.fit').forEach((el)=>{
  let fs=parseFloat(el.dataset.fs0||getComputedStyle(el).fontSize); el.dataset.fs0=fs; el.style.fontSize=fs+'px';
  const box=el.parentElement, cs=getComputedStyle(box);
  const room=()=>box.clientWidth-parseFloat(cs.paddingLeft)-parseFloat(cs.paddingRight)-6;
  const textW=()=>{const r=document.createRange(); r.selectNodeContents(el); const sc=(el.getBoundingClientRect().width/(el.offsetWidth||1))||1; return r.getBoundingClientRect().width/sc;};
  let guard=0; while(textW()>room()&&fs>28&&guard++<80){fs-=3;el.style.fontSize=fs+'px';}
}); if(tl) tl.seek(0,false);};
document.querySelectorAll('[data-a]').forEach((el)=>{
  const a=el.dataset.a, d=el.dataset.d!==undefined?parseFloat(el.dataset.d):(auto+=0.09);
  const dur=parseFloat(el.dataset.dur||(a==='bar'?0.9:a==='count'?1.1:0.75));
  if(a==='up') TL.from(el,{y:46,opacity:0,duration:dur,ease},d);
  else if(a==='down') TL.from(el,{y:-40,opacity:0,duration:dur,ease},d);
  else if(a==='left') TL.from(el,{x:-60,opacity:0,duration:dur,ease},d);
  else if(a==='right') TL.from(el,{x:60,opacity:0,duration:dur,ease},d);
  else if(a==='fade') TL.from(el,{opacity:0,duration:dur,ease:'power1.out'},d);
  else if(a==='pop') TL.from(el,{scale:.82,opacity:0,duration:dur,ease:'back.out(1.7)'},d);
  else if(a==='bar') TL.from(el,{scaleY:0,transformOrigin:'50% 100%',duration:dur,ease:'power3.out'},d);
  else if(a==='barx') TL.from(el,{scaleX:0,transformOrigin:'0% 50%',duration:dur,ease:'power3.inOut'},d);
  else if(a==='draw'){const L=el.getTotalLength();el.style.strokeDasharray=L;TL.fromTo(el,{strokeDashoffset:L},{strokeDashoffset:0,duration:dur*1.8,ease:'power2.inOut'},d);
     TL.from(el,{fillOpacity:0,duration:.6},d+dur*1.2);}
  else if(a==='count'){const to=parseFloat(el.dataset.to),dec=parseInt(el.dataset.dec||0),pre=el.dataset.pre||'',suf=el.dataset.suf||'';
     const final=el.textContent; const o={v:0};
     TL.fromTo(o,{v:0},{v:to,duration:dur,ease:'power2.out',onUpdate:()=>{el.textContent=(o.v>=to-1e-9)?final:pre+fmt(o.v,dec)+suf}},d);
     TL.from(el,{opacity:0,duration:.3},d);}
});
const g1=document.querySelector('.g1'),g2=document.querySelector('.g2');
if(g1) TL.fromTo(g1,{x:0,y:0},{x:-70,y:40,duration:12,ease:'sine.inOut'},0);
if(g2) TL.fromTo(g2,{x:0,y:0},{x:60,y:-50,duration:12,ease:'sine.inOut'},0);
if(document.documentElement.classList.contains('reel')) TL.fromTo('.content',{scale:1},{scale:1.022,duration:8,ease:'none',transformOrigin:'40% 40%'},0);
window.ENTRANCE=Math.max(0.01,...TL.getChildren(false,true,true).filter(c=>c.duration()<6).map(c=>c.endTime()));
window.seek=(t)=>{TL.seek(Math.min(t,TL.duration()),false);return true};
window.final=()=>{TL.seek(window.ENTRANCE+0.01,false);return window.ENTRANCE};
</script>"""


def shell(inner_body, w, h, extra_css="", html_class="", script=None):
    base, top = backgrounds(w, h)
    cls = (html_class + (" tall" if h > 1500 else "")).strip()
    return ('<!doctype html><html class="%s"><head><meta charset="utf-8"><style>%s%s%s</style></head><body>'
            '<div class="slide" id="slide"><img class="bg" src="%s"><div class="bgl g1"></div><div class="bgl g2"></div>%s<img class="ov" src="%s">'
            '<div class="grain" style="background-image:url(%s)"></div></div>'
            '<script>%s</script>%s</body></html>'
            % (cls, fonts_css(), CSS, extra_css, base, inner_body, top, grain_tile(), gsap_js(), RUNTIME if script is None else script))
