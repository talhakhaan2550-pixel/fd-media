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


def _b64(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()


# The light look (15 November 2026): Fraunces for display, Plus Jakarta Sans for text, Caveat for handwriting
FONTS_LIGHT = [("Fraunces", "fraunces-latin-600-normal.woff2", 600, "normal"), ("Fraunces", "fraunces-latin-700-normal.woff2", 700, "normal"),
               ("Fraunces", "fraunces-latin-600-italic.woff2", 600, "italic"), ("Fraunces", "fraunces-latin-700-italic.woff2", 700, "italic"),
               ("Jakarta", "plus-jakarta-sans-latin-500-normal.woff2", 500, "normal"), ("Jakarta", "plus-jakarta-sans-latin-600-normal.woff2", 600, "normal"),
               ("Jakarta", "plus-jakarta-sans-latin-700-normal.woff2", 700, "normal"), ("Jakarta", "plus-jakarta-sans-latin-800-normal.woff2", 800, "normal"),
               ("Caveat", "caveat-latin-600-normal.woff2", 600, "normal"), ("Caveat", "caveat-latin-700-normal.woff2", 700, "normal"),
               ("PlexMono", "ibm-plex-mono-latin-400-normal.woff2", 400, "normal")]
FONT_CHECKS = ["400 40px SS4", "600 40px SS4", "700 40px SS4", "400 40px Plex", "500 40px Plex", "600 40px Plex",
               "600 40px Fraunces", "700 40px Fraunces", "italic 700 40px Fraunces", "500 40px Jakarta", "600 40px Jakarta",
               "700 40px Jakarta", "800 40px Jakarta", "700 40px Caveat", "400 40px PlexMono"]
INK, PAPER, EM, YEL, RED = "#15191F", "#F6F1E7", "#0B7955", "#FFD84D", "#C23A2B"


@functools.lru_cache(None)
def fonts_css():
    out = []
    for fam, file, w in [("SS4", "source-serif-4-latin-400-normal.woff2", 400), ("SS4", "source-serif-4-latin-600-normal.woff2", 600),
                         ("SS4", "source-serif-4-latin-700-normal.woff2", 700), ("Plex", "ibm-plex-sans-latin-400-normal.woff2", 400),
                         ("Plex", "ibm-plex-sans-latin-500-normal.woff2", 500), ("Plex", "ibm-plex-sans-latin-600-normal.woff2", 600)]:
        out.append("@font-face{font-family:'%s';src:url(data:font/woff2;base64,%s) format('woff2');font-weight:%d;font-display:block}"
                   % (fam, _b64(os.path.join(ASSETS, "fonts", file)), w))
    for fam, file, w, st in FONTS_LIGHT:
        out.append("@font-face{font-family:'%s';src:url(data:font/woff2;base64,%s) format('woff2');font-weight:%d;font-style:%s;font-display:block}"
                   % (fam, _b64(os.path.join(ASSETS, "fonts", file)), w, st))
    return "".join(out)


@functools.lru_cache(None)
def gsap_js():
    with open(os.path.join(ASSETS, "gsap.min.js")) as f:
        return f.read()


@functools.lru_cache(None)
def us_map():
    with open(os.path.join(ASSETS, "us-map.json")) as f:
        return json.load(f)


PHOTOS = {"talha": "talha.jpg", "award": "award.jpg", "talha_cut": "talha_cut.png", "talha_sticker": "talha_sticker.png"}


@functools.lru_cache(None)
def photo_uri(name):
    f = PHOTOS[name]
    return "data:image/%s;base64,%s" % ("png" if f.endswith(".png") else "jpeg", _b64(os.path.join(ASSETS, "photos", f)))


@functools.lru_cache(None)
def texture_uri(name):
    return "data:image/png;base64," + _b64(os.path.join(ASSETS, "textures", name + ".png"))


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
    """Base layer (warm paper, a little lighter at the top left) and a top layer (a very soft warm edge)."""
    y, x = np.mgrid[0:h, 0:w].astype(np.float32)
    t = np.clip(0.78 * (y / h) + 0.22 * (x / w), 0, 1)[..., None]
    c0, c1 = _hex("#F9F5EE"), _hex("#F1EADC")
    base_img = np.clip(c0 + (c1 - c0) * t, 0, 255).astype(np.uint8)
    vx, vy = (x - 0.5 * w) / (1.30 * w / 2), (y - 0.45 * h) / (1.0 * h / 2)
    vig = np.clip((np.sqrt(vx ** 2 + vy ** 2) - 0.62) / 0.5, 0, 1) * 0.10
    top = np.zeros((h, w, 4), np.uint8)
    top[..., 0], top[..., 1], top[..., 2] = 118, 96, 58
    top[..., 3] = np.clip(vig * 255, 0, 255).astype(np.uint8)
    return _png_uri(base_img), _png_uri(top)


def grain_tile():
    """Paper grain: dark specks at low opacity on a 256 pixel tile (held still in videos so they stay small)."""
    return texture_uri("paper_grain")


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


def ic(name, size=48, color="#0B7955", sw=2.4):
    body = ICONS.get(name, ICONS["doc"])
    return ('<svg width="%d" height="%d" viewBox="0 0 48 48" fill="none" stroke="%s" stroke-width="%s" stroke-linecap="round" '
            'stroke-linejoin="round" style="flex:none">%s</svg>' % (size, size, color, sw, body))


ARROW = ('<svg width="32" height="18" viewBox="0 0 34 20" style="flex:none"><path d="M2 10h28M22 2l8 8-8 8" fill="none" stroke="currentColor" '
         'stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"/></svg>')
WAVE = ('<svg width="22" height="18" viewBox="0 0 22 18"><path d="M2 7v4M6 4v10M10 1v16M14 5v8M18 7v4" stroke="#15191F" '
        'stroke-width="2.2" stroke-linecap="round"/></svg>')


# ---------------------------------------------------------------- the US map
def state_shape(code, size, d=0.3, anim=True):
    s = us_map()["states"][code]["shape"]
    a = ' data-a="draw" data-d="%s" data-dur="0.9"' % d if anim else ""
    return ('<svg width="%d" height="%d" viewBox="0 0 400 400" style="overflow:visible"><path%s d="%s" fill="rgba(11,121,85,.12)" '
            'stroke="#0B7955" stroke-width="2.5" vector-effect="non-scaling-stroke" stroke-linejoin="round" '
            'style="filter:drop-shadow(0 8px 14px rgba(70,55,30,.18))"/></svg>' % (size, size, a, s))


def usmap(width, states=(), labels=None, d=0.3, pins=True, faint=False, uid="m", anim=True):
    m = us_map()
    s = width / m["w"]
    h = m["h"] * s
    small = width < 400
    A = (lambda k, dd: ' data-a="%s" data-d="%.2f"' % (k, dd)) if anim else (lambda k, dd: "")
    hl = ""
    for code in states:
        hl += ('<path d="%s" fill="rgba(11,121,85,.34)" stroke="#0B7955" stroke-width="%.2f" stroke-linejoin="round" data-gl="%s"%s/>'
               % (m["states"][code]["albers"], 2.2 / s if small else 2.2, uid, A("fade", d + 0.35)))
    pin, lab = "", ""
    if pins:
        for i, code in enumerate(states):
            cx, cy = m["states"][code]["c"]
            pin += ('<g%s style="transform-origin:%spx %spx"><circle cx="%s" cy="%s" r="17" fill="none" stroke="rgba(21,25,31,.45)" stroke-width="2"/>'
                    '<circle cx="%s" cy="%s" r="8" fill="#FFD84D" stroke="#15191F" stroke-width="2.5"/></g>' % (A("pop", d + 0.6 + i * 0.15), cx, cy, cx, cy, cx, cy))
            if labels is not False:
                name = (labels or {}).get(code, m["states"][code]["name"])
                lab += ('<div%s style="position:absolute;left:%.0fpx;top:%.0fpx;transform:translateX(-50%%);display:flex;flex-direction:column;align-items:center">'
                        '<div class="maplabel">%s</div><div style="width:2px;height:40px;background:linear-gradient(#15191F,rgba(21,25,31,0))"></div></div>'
                        % (A("up", d + 0.75 + i * 0.15), cx * s, cy * s - 96, esc(name)))
    return ('<div style="position:relative;width:%dpx;height:%.0fpx;opacity:%s"><svg viewBox="0 0 %d %d" width="%d" height="%.0f" '
            'style="overflow:visible;position:absolute;inset:0"><defs><filter id="gl%s" x="-50%%" y="-50%%" width="200%%" height="200%%">'
            '<feGaussianBlur stdDeviation="7" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter></defs>'
            '<path d="%s" fill="rgba(255,255,255,.55)" stroke="rgba(21,25,31,.42)" stroke-width="%.2f"%s/>'
            '<path d="%s" fill="none" stroke="rgba(21,25,31,.16)" stroke-width="%.2f"%s/>%s%s</svg>%s</div>'
            % (width, h, ".55" if faint else "1", m["w"], m["h"], width, h, uid, m["nation"], 1.2 / s if small else 1.3, A("fade", d),
               m["mesh"], 0.8 / s if small else 0.9, A("fade", d + 0.1), hl, pin, lab))


# ---------------------------------------------------------------- shared CSS
CSS = """
:root{--ink:#15191F;--paper:#F6F1E7;--em:#0B7955;--em2:#14A374;--yel:#FFD84D;--red:#C23A2B;--mute:#59606C;--grey:#4D5562}
*{box-sizing:border-box;margin:0;padding:0}
html,body{background:#F6F1E7}
.slide{position:relative;width:1080px;height:1350px;overflow:hidden;color:#15191F;font-family:'Jakarta';background:#F6F1E7}
.tall .slide{height:1920px}
.bg,.ov{position:absolute;inset:0;width:100%;height:100%;display:block;pointer-events:none}
.bg{z-index:0}.ov{z-index:20}
.grain{position:absolute;inset:0;z-index:21;pointer-events:none;background-repeat:repeat}
.bgl{position:absolute;border-radius:50%;pointer-events:none;z-index:1;will-change:transform}
.g1{width:1100px;height:1000px;left:-320px;top:-380px;background:radial-gradient(closest-side,rgba(255,255,255,.92),rgba(255,255,255,0))}
.g2{width:1000px;height:1000px;right:-440px;bottom:-440px;background:radial-gradient(closest-side,rgba(255,216,77,.28),rgba(255,216,77,0))}
.tall .g1{top:-120px}.tall .g2{bottom:-160px}
.top{position:absolute;left:72px;right:72px;top:62px;display:flex;align-items:center;justify-content:space-between;z-index:5}
.brand{display:flex;align-items:center;gap:16px;font-family:'SS4';font-weight:600;font-size:29px;color:#15191F;white-space:nowrap}
.mark{width:54px;height:54px;border-radius:8px;background:#0B7955;display:grid;place-items:center;font-family:'SS4';font-weight:600;font-size:30px;line-height:1;color:#fff;flex:none}
.count{font-weight:600;font-size:22px;letter-spacing:.16em;color:#59606C}
.count b{color:#15191F;font-weight:800}
.content{position:absolute;left:72px;right:72px;top:168px;bottom:118px;display:flex;flex-direction:column;z-index:4}
.kicker{align-self:flex-start;display:inline-flex;align-items:center;gap:12px;padding:10px 20px 10px 16px;border-radius:999px;border:2.5px solid #15191F;
 background:rgba(255,255,255,.6);color:#15191F;font-weight:700;font-size:20px;letter-spacing:.15em;text-transform:uppercase;white-space:nowrap}
.kicker i{width:13px;height:13px;border-radius:50%;background:#FFD84D;border:2px solid #15191F}
h1,h2{font-family:'Fraunces';font-weight:700;letter-spacing:-.02em;color:#15191F;text-wrap:balance}
h1{font-size:84px;line-height:1.04}
h2{font-size:70px;line-height:1.06}
.em{font-style:italic;background:linear-gradient(transparent 12%,#FFD84D 12%,#FFD84D 92%,transparent 92%);padding:0 .12em;margin:0 -.06em;
 -webkit-box-decoration-break:clone;box-decoration-break:clone;border-radius:6px}
.body{font-size:30px;line-height:1.45;color:#3F4652;font-weight:500}
.body b{color:#15191F;font-weight:800}
.card{position:relative;border-radius:30px;background:#FFFDF8;border:2px solid rgba(21,25,31,.11);box-shadow:0 30px 60px rgba(70,55,30,.12)}
.card.hl{border:3px solid #15191F;box-shadow:8px 8px 0 #15191F}
.big{font-family:'Fraunces';font-weight:700;letter-spacing:-.035em;line-height:.95;color:#15191F;white-space:nowrap}
.label{font-weight:700;font-size:19px;letter-spacing:.16em;text-transform:uppercase;color:#0B7955}
.small{font-size:23px;line-height:1.38;color:#4D5562;font-weight:500}
.cal{width:176px;border-radius:24px;overflow:hidden;background:#FFFFFF;color:#15191F;box-shadow:0 22px 44px rgba(70,55,30,.18);border:2px solid rgba(21,25,31,.12);text-align:center;flex:none}
.cal .m{background:#0B7955;color:#fff;font-weight:700;font-size:22px;letter-spacing:.2em;padding:11px 6px 10px;white-space:nowrap}
.cal .d{font-family:'Fraunces';font-weight:700;font-size:96px;line-height:1.02;padding:8px 0 0;letter-spacing:-.02em}
.cal .s{font-weight:700;font-size:16px;letter-spacing:.08em;color:#59606C;padding:0 10px 16px}
.dots{position:absolute;left:0;right:0;bottom:56px;display:flex;justify-content:center;gap:12px;z-index:5}
.dots span{width:12px;height:12px;border-radius:99px;background:rgba(21,25,31,.18)}
.dots span.on{width:44px;background:#15191F}
.cta{display:inline-flex;align-items:center;gap:16px;padding:22px 40px;border-radius:999px;font-weight:800;font-size:30px;color:#15191F;
 background:#FFD84D;border:3px solid #15191F;box-shadow:6px 6px 0 #15191F;white-space:nowrap}
.fine{font-size:18px;color:#7A808A;letter-spacing:.01em}
.row{display:flex;gap:20px}
.sp{flex:1}
.chip{display:inline-flex;align-items:center;gap:12px;padding:13px 20px;border-radius:14px;background:#FFFFFF;border:2px solid rgba(21,25,31,.14);
 color:#15191F;font-weight:600;font-size:24px;line-height:1.25}
.maplabel{padding:9px 16px;border-radius:12px;background:#FFFFFF;border:2.5px solid #15191F;font-weight:700;font-size:21px;letter-spacing:.12em;
 text-transform:uppercase;color:#15191F;white-space:nowrap;box-shadow:4px 4px 0 #15191F}
.quote{font-family:'Fraunces';font-weight:600;font-size:46px;line-height:1.18;color:#15191F}
.qm{font-family:'Fraunces';font-weight:700;font-size:120px;line-height:.6;color:#0B7955}
.seal{width:96px;height:96px;border-radius:50%;display:grid;place-items:center;background:#0B7955;box-shadow:0 0 0 8px rgba(11,121,85,.14),0 14px 30px rgba(11,121,85,.3);flex:none}
.ico{width:66px;height:66px;border-radius:18px;display:grid;place-items:center;background:rgba(11,121,85,.10);border:2px solid rgba(11,121,85,.3);flex:none}
.tone-amber{color:#B26B00!important}
.tone-red{color:#C23A2B!important}
.tone-white{color:#15191F!important}
.me{position:relative;display:flex;align-items:center;gap:22px}
.me .ring{position:relative;width:var(--rs,190px);height:var(--rs,190px);border-radius:50%;background:#FFD84D;overflow:hidden;flex:none;border:3px solid #15191F}
.me .ring img{position:absolute;left:4%;top:8%;width:92%}
.me .who b{display:block;font-family:'Fraunces';font-weight:700;font-size:36px;line-height:1.1}
.me .who span{display:block;font-weight:600;font-size:22px;color:#59606C;margin-top:4px}
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
// in reels the cast sways gently once everything has come in, so the built slide (window.final) shows it standing still
if(document.documentElement.classList.contains('reel')) document.querySelectorAll('.castc').forEach((el,i)=>{
  TL.fromTo(el,{rotation:0,y:0},{rotation:i%2?-2:2,y:-6,duration:1.4,ease:'sine.inOut',yoyo:true,repeat:9,immediateRender:false},window.ENTRANCE+0.05+i*0.2);});
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
