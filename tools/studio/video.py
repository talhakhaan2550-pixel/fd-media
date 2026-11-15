"""Narrated story videos for explainers and ads (1080 x 1920): each line of approved words is spoken by the AI
narrator over a visual scene, with captions that light up word by word, original music and sound effects.

A piece's content may carry:
  say:    the spoken form of each beat, {"hook": ..., "lines": [...], "cta": ..., "offer": ...}; missing beats are
          spoken from the words themselves (numbers and initials written out by audio.speakable).
  scenes: one scene per beat, in the order hook, lines..., cta; null or missing means the default (the line as a
          large headline; the end card for the call to action). Scene types: headline, stat, doc, route, date,
          ladder, alert, compare, checklist, map, icons, steps, quote, gauge, end.
Scene labels restate the piece's own words; they never add a fact.
"""
import json, math, re
from brand import esc, ic, ARROW, WAVE, us_map, shell, SITE, DISCLAIMER, AI_NOTE

W, H, FPS = 1080, 1920, 30
GAP, GAP_SAME, START = 0.55, 0.25, 0.35
LATE = 1.4    # a scene's main picture is on screen by this many seconds into its beat; a later word gets a pulse
MONTHS = "January|February|March|April|May|June|July|August|September|October|November|December"
FIG = re.compile(r"^(\$[\d,.]+(?:M|K)?\+?|\d[\d,.]*%|\d[\d,]*\+?|" + MONTHS + r")[.,;:?!]?$")


def num_of(v):
    m = re.search(r"\d[\d,]*(?:\.\d+)?", str(v))
    return float(m.group(0).replace(",", "")) if m else None


def clean(w):
    return re.sub(r"[^\w$%+.-]", "", w.lower()).strip(".")


class Beat:
    def __init__(self, i, key, text, say, scene):
        self.i, self.key, self.text, self.say, self.scene = i, key, text, say, scene
        self.start = 0.0
        self.dur = 0.0
        self.words = []  # spoken words with times relative to start
        self.wav = None

    @property
    def end(self):
        return self.start + self.dur

    def at(self, word, default=None, nth=0):
        """Absolute time of a spoken word (first match of its start), or a default."""
        if word:
            target = clean(str(word))
            hits = [w for w in self.words if clean(w["w"]).startswith(target)]
            if len(hits) > nth:
                return self.start + hits[nth]["t0"]
        return default if default is not None else self.start + min(0.6, self.dur / 3)


def make_beats(piece):
    c = piece.get("content", {})
    say = c.get("say") or {}
    scenes = c.get("scenes") or []
    texts = [("hook", c["hook"])] + [("l%d" % (i + 1), l) for i, l in enumerate(c.get("lines", []))] + [("cta", c["cta"])]
    out = []
    for i, (k, t) in enumerate(texts):
        if k == "hook":
            s = say.get("hook")
        elif k == "cta":
            s = say.get("cta")
        else:
            s = (say.get("lines") or [None] * 99)[i - 1] if isinstance(say.get("lines"), list) and i - 1 < len(say.get("lines")) else None
        sc = scenes[i] if i < len(scenes) and scenes[i] else None
        if sc is None:
            sc = {"type": "end"} if k == "cta" else {"type": "headline"}
        out.append(Beat(i, k, t, s, sc))
    return out


def group_id(b):
    sc = b.scene
    if sc.get("id"):
        return sc["type"] + ":" + str(sc["id"])
    return "b%d" % b.i


def lay_out(beats, est_only=False):
    """Places the beats in time. Spoken beats use their narration's length; silent ones a reading time."""
    t = START
    for i, b in enumerate(beats):
        if not b.words:
            n = len(b.text.split())
            b.dur = max(2.2, 0.36 * n + 0.6)
            step = b.dur / max(1, n)
            b.words = [{"w": w, "t0": round(k * step, 3), "t1": round((k + 1) * step, 3)} for k, w in enumerate(b.text.split())]
        b.start = t
        nxt = beats[i + 1] if i + 1 < len(beats) else None
        t = b.end + (GAP_SAME if nxt and group_id(nxt) == group_id(b) else GAP)
    last = beats[-1]
    end_at = last.start - 0.1 if last.scene.get("type") == "end" else last.end + 0.3
    total = (last.end + 3.0) if last.scene.get("type") == "end" else end_at + 3.2
    return round(end_at, 3), round(total, 2)


# ---------------------------------------------------------------- captions
def caption_words(b):
    """Times for the words on screen, mapped from the spoken words: chunk by chunk when both split at the same
    punctuation, otherwise in proportion to their length across the whole beat."""
    shown = b.text.split()
    spoken = b.words
    def chunks(ws, key=lambda w: w):
        out, cur = [], []
        for w in ws:
            cur.append(w)
            if re.search(r"[,.;:?!]$", key(w)):
                out.append(cur); cur = []
        if cur:
            out.append(cur)
        return out
    cs, ss = chunks(shown), chunks(spoken, key=lambda w: w["w"])
    times = []
    if len(cs) == len(ss) and len(cs) > 1:
        pairs = zip(cs, ss)
    else:
        pairs = [(shown, spoken)]
    for cw, sw in pairs:
        a, z = sw[0]["t0"], sw[-1]["t1"]
        L = sum(len(w) + 1 for w in cw) or 1
        acc = 0
        for w in cw:
            times.append(b.start + a + (z - a) * acc / L)
            acc += len(w) + 1
    return list(zip(shown, times))


def caption_pages(b, max_chars=58):
    words = caption_words(b)
    pages, cur, n = [], [], 0
    for w, t in words:
        if cur and n + len(w) + 1 > max_chars:
            pages.append(cur); cur, n = [], 0
        cur.append((w, t)); n += len(w) + 1
        if re.search(r"[.;:?!]$", w) and n > max_chars * 0.55:
            pages.append(cur); cur, n = [], 0
    if cur:
        pages.append(cur)
    return pages


def word_cls(w, tone=None):
    if re.match(r"^\$?\d", w) or re.match(r"^(" + MONTHS + r")\b", w):
        return "n1"
    return ""


# ---------------------------------------------------------------- scenes
class Out:
    def __init__(self):
        self.html, self.js, self.cues, self.dips = [], [], [], []

    def j(self, s, *a):
        self.js.append(s % a if a else s)


TONES = {"green": "b1", "amber": "b2", "red": "b3"}


def pulse(o, sel, t, amount=1.1):
    """A short scale pulse, with a tick, on a word spoken after the picture is already up."""
    o.j("TL.to('%s',{keyframes:{scale:[1,%.2f,1]},duration:.44,ease:'power1.inOut'},%.3f);", sel, amount, t - 0.12)
    o.cues.append(("tick", t - 0.12, 0.26))


def sc_headline(o, g, beats, gi, hook_kicker):
    b = beats[0]
    n = len(b.text)
    if b.key == "hook":
        fs = 92 if n <= 40 else (80 if n <= 70 else 68)
    else:
        fs = 74 if n <= 60 else (64 if n <= 100 else 56)
    spans = "".join('<span class="%s">%s</span> ' % (word_cls(w), esc(w)) for w, _ in caption_words(b))
    o.html.append('<div class="hlw"><div class="hlt%s" style="font-size:%dpx">%s</div></div>' % (" serif" if b.key == "hook" else "", fs, spans))
    for k, (w, t) in enumerate(caption_words(b)):
        o.j("TL.to('#%s .hlt span:nth-child(%d)',{opacity:1,duration:.14},%.3f);", g, k + 1, t)
    o.j("TL.from('#%s .hlw',{y:40,opacity:0,duration:.6,ease:'power3.out'},%.3f);", g, b.start - 0.12)


def doc_html(spec, mini=False):
    fields = spec.get("fields") or ["Payer", "Recipient", "Amount"]
    rows = ""
    for k, f in enumerate(fields[:3]):
        last = k == len(fields[:3]) - 1
        rows += '<div class="fld"%s><span>%s</span>%s<i style="width:%d%%"></i></div>' % (' id="amt"' if last else "", esc(f).upper(), "<b>$</b>" if last and spec.get("money", True) else "", [58, 46, 34][k])
    tag = '<div class="dtag">%s</div>' % esc(spec["tag"]) if spec.get("tag") else ""
    lab = '<div class="dlab">%s</div>' % esc(spec["label"]).upper() if spec.get("label") else ""
    return ('<div class="form%s"><div style="display:flex;align-items:flex-end;justify-content:space-between"><div>%s<div class="dtitle">%s</div></div>%s</div>%s</div>'
            % (" mini" if mini else "", lab, esc(spec.get("title", "")), tag, rows))


def sc_doc(o, g, beats, gi, nxt_type):
    b = beats[0]; sp = b.scene
    o.html.append('<div class="docw">%s%s</div>' % (doc_html(sp), "".join(
        '<div class="stamp st%d">%s</div>' % (k, esc(s.get("text", ""))) for k, s in enumerate(sp.get("stamps", [])[:3]))))
    o.j("TL.fromTo('#%s .form',{y:120,opacity:.2,rotation:-8,scale:.92},{y:0,opacity:1,rotation:-3,scale:1,duration:.7,ease:'power3.out'},%.3f);", g, max(0, b.start - 0.35))
    o.cues.append(("whoosh", max(0, b.start - 0.4), 0.2))
    rot = [-12, 7, -4]
    for k, s in enumerate(sp.get("stamps", [])[:3]):
        t = b.at(s.get("at"), b.start + 0.5 + k * 0.45)
        o.j("gsap.set('#%s .st%d',{rotation:%d});", g, k, rot[k])
        o.j("TL.fromTo('#%s .st%d',{opacity:0,scale:2.5},{opacity:1,scale:1,duration:.19,ease:'power4.in'},%.3f);", g, k, t - 0.19)
        o.j("TL.to('#%s .form',{keyframes:{x:[0,-12,9,-5,2,0]},duration:.32,ease:'none'},%.3f);", g, t)
        o.cues.append(("impact", t - 0.01, 0.5))
    if nxt_type == "route":
        o.exit_style = "shrink"


def sc_route(o, g, beats, gi, prev):
    b = beats[0]; sp = b.scene
    docspec = dict(sp)
    if prev is not None and prev.scene.get("type") == "doc":
        for k in ("title", "tag", "label", "fields"):
            docspec.setdefault(k, prev.scene.get(k))
    to = sp.get("to", [])[:3]
    xs = {1: [335], 2: [80, 590], 3: [10, 335, 660]}[max(1, len(to))]
    nodes, paths = "", ""
    for k, nd in enumerate(to):
        x = xs[k]
        nodes += ('<div class="node n%d" style="left:%dpx"><div class="nc">%s</div><div class="nl">%s</div></div>'
                  % (k, x, ic(nd.get("icon", "person"), 70, "#C9FBE7", 2.2), esc(nd.get("label", ""))))
        cx = x + 85
        paths += '<path class="p%d" d="M420 236 C 420 290, %d 250, %d 296" fill="none" stroke="#6AF3C0" stroke-width="3" stroke-dasharray="8 10" opacity="0"/>' % (k, cx, cx)
    minis = "".join('<div class="minic m%d"><div></div><div></div><div style="width:70%%"></div></div>' % k for k in range(len(to)))
    date = ""
    if sp.get("date") and len(to) <= 2:
        d = sp["date"]
        date = ('<div class="calB"><div class="m">%s</div><div class="d">%s</div><div class="s">%s</div></div>'
                % (esc(d.get("top", "")), esc(d.get("day", "")), esc(d.get("bottom", ""))))
    o.html.append('<div class="rdoc">%s</div><svg width="840" height="600" style="position:absolute;inset:0;overflow:visible">%s</svg>%s%s%s'
                  % (doc_html(docspec, mini=True), paths, minis, nodes, date))
    came_from_doc = prev is not None and prev.scene.get("type") == "doc"
    o.j("TL.fromTo('#%s .rdoc',{opacity:0},{opacity:1,duration:%s},%.3f);", g, ".01" if came_from_doc else ".5", b.start - (0.05 if came_from_doc else 0.2))
    o.j("TL.fromTo('#%s .node',{autoAlpha:0,scale:.6},{autoAlpha:1,scale:1,duration:.55,stagger:.12,ease:'back.out(1.8)'},%.3f);", g, b.start + 0.25)
    for k, nd in enumerate(to):
        t = b.at(nd.get("at"), b.start + 0.8 + k * 0.7)
        dx = xs[k] + 85 - 420
        o.j("TL.to('#%s .p%d',{opacity:1,duration:.3},%.3f);", g, k, t - 0.35)
        o.j("TL.fromTo('#%s .p%d',{strokeDashoffset:0},{strokeDashoffset:-180,duration:4,ease:'none'},%.3f);", g, k, t - 0.35)
        o.j("gsap.set('#%s .m%d',{left:345,top:180});", g, k)
        o.j("TL.fromTo('#%s .m%d',{autoAlpha:0,scale:.5,x:0,y:0},{autoAlpha:1,scale:.75,x:%d,y:150,duration:.75,ease:'power2.inOut'},%.3f);", g, k, dx, t - 0.35)
        o.j("TL.to('#%s .m%d',{autoAlpha:0,scale:.4,duration:.25},%.3f);", g, k, t + 0.42)
        o.j("TL.fromTo('#%s .n%d .nc',{boxShadow:'0 0 50px rgba(21,183,129,.3)'},{boxShadow:'0 0 90px rgba(21,183,129,.85)',duration:.3,yoyo:true,repeat:1},%.3f);", g, k, t + 0.35)
        o.cues.append(("whoosh", t - 0.35, 0.2))
    if date:
        t = b.at(sp["date"].get("at"), b.end - 1.6)
        o.j("TL.fromTo('#%s .calB',{autoAlpha:0,y:80,scale:.7},{autoAlpha:1,y:0,scale:1,duration:.55,ease:'back.out(1.7)'},%.3f);", g, t - 0.3)
        o.cues.append(("impact", t + 0.1, 0.28))


def sc_date(o, g, beats, gi):
    b = beats[0]; sp = b.scene
    lab = '<div class="label" style="font-size:24px;margin-bottom:26px">%s</div>' % esc(sp["label"]) if sp.get("label") else ""
    o.html.append('<div class="center">%s<div class="calB big"><div class="m">%s</div><div class="d">%s</div><div class="s">%s</div></div>%s</div>'
                  % (lab, esc(sp.get("top", "")), esc(sp.get("day", "")), esc(sp.get("bottom", "")),
                     ('<div class="dtext">%s</div>' % esc(sp["text"])) if sp.get("text") else ""))
    said = b.at(sp.get("at"), b.start + 0.4)
    t = min(said, b.start + LATE)
    o.j("TL.fromTo('#%s .calB',{autoAlpha:0,y:80,scale:.7},{autoAlpha:1,y:0,scale:1,duration:.55,ease:'back.out(1.7)'},%.3f);", g, t - 0.3)
    o.j("TL.from('#%s .label,#%s .dtext',{opacity:0,y:20,duration:.5},%.3f);", g, g, b.start - 0.1)
    o.cues += [("tick", t - 0.3, 0.3), ("impact", t + 0.1, 0.25)]
    if said > t + 0.6:
        pulse(o, "#%s .calB" % g, said, 1.08)


def sc_ladder(o, g, beats, gi):
    sp = beats[0].scene
    bars = sp.get("bars", [])[:4]
    n = max(1, len(bars))
    gap = 66 if n == 3 else (90 if n == 2 else 40)
    cw = (840 - gap * (n - 1)) / n
    vals = [num_of(x.get("value")) or 1 for x in bars]
    top = max(vals) or 1
    cols = ""
    for k, x in enumerate(bars):
        h = max(46, 352 * vals[k] / top)
        left = k * (cw + gap)
        cls = TONES.get(x.get("tone"), ["b1", "b2", "b3", "b1"][k])
        cols += ('<div class="lg" id="%s_lg%d" style="left:%.0fpx;width:%.0fpx;height:%.0fpx"></div><div class="lc" style="left:%.0fpx;width:%.0fpx">'
                 '<div class="lv" id="%s_lv%d">%s</div><div class="lb %s" id="%s_lb%d" style="height:%.0fpx"></div></div>'
                 '<div class="lx" id="%s_lx%d" style="left:%.0fpx;width:%.0fpx">%s</div>'
                 % (g, k, left, cw, h, left, cw, g, k, esc(x.get("value", "")), cls, g, k, h, g, k, left, cw, esc(x.get("label", ""))))
    title = '<div class="label" style="font-size:22px">%s</div>' % esc(sp["title"]) if sp.get("title") else ""
    o.html.append('%s<div class="lad"><div class="base"></div>%s</div>' % (title, cols))
    b0 = beats[0]
    o.j("TL.from('#%s .base',{scaleX:0,duration:.8,ease:'power3.inOut',transformOrigin:'0 50%%'},%.3f);", g, b0.start + 0.1)
    o.j("TL.from('#%s .lg',{opacity:0,y:30,duration:.5,stagger:.12},%.3f);", g, b0.start + 0.35)
    o.j("TL.from('#%s .lx',{opacity:0,y:16,duration:.5,stagger:.12},%.3f);", g, b0.start + 0.5)
    o.j("gsap.set('#%s .lb',{scaleY:0,transformOrigin:'50%% 100%%'}); gsap.set('#%s .lv',{opacity:0});", g, g)
    shown = set()
    for b in beats:
        sp_b = b.scene
        show = sp_b.get("show")
        if show is None:
            show = [k for k in range(len(bars)) if k not in shown][:1]
        ats = sp_b.get("at") or []
        if isinstance(ats, str):
            ats = [ats]
        for j, k in enumerate(show):
            if k in shown or k >= len(bars):
                continue
            shown.add(k)
            t = b.at(ats[j] if j < len(ats) else None, b.start + 0.4 + j * 0.9)
            v = num_of(bars[k].get("value"))
            pre = "$" if str(bars[k].get("value", "")).startswith("$") else ""
            o.j("TL.to('#%s_lb%d',{scaleY:1,duration:.75,ease:'power3.out'},%.3f);", g, k, t - 0.3)
            o.j("TL.fromTo('#%s_lv%d',{opacity:0,y:20},{opacity:1,y:0,duration:.4},%.3f);", g, k, t - 0.3)
            if v is not None and float(v).is_integer():
                o.j("(()=>{const o={v:0},el=document.getElementById('%s_lv%d'),fin=el.textContent;TL.to(o,{v:%d,duration:.75,ease:'power2.out',onUpdate:()=>{el.textContent=o.v>=%d-1e-6?fin:'%s'+Math.round(o.v).toLocaleString('en-US')}},%.3f)})();",
                    g, k, int(v), int(v), pre, t - 0.3)
            for q in range(4):
                o.cues.append(("tick", t - 0.3 + q * 0.12, 0.2))
            if bars[k].get("tone") == "red" or (k == len(bars) - 1 and len(bars) >= 3 and not bars[k].get("tone")):
                o.j("TL.to('#stage',{keyframes:{x:[0,-10,8,-4,0]},duration:.3},%.3f);", t + 0.4)
                o.cues.append(("impact", t + 0.4, 0.38))
        marks = sp_b.get("mark") or []
        mats = sp_b.get("mark_at") or []
        for j, k in enumerate(marks):
            if k >= len(bars):
                continue
            t = b.at(mats[j] if j < len(mats) else None, b.start + 0.3)
            col = {"b1": ("#B9FBE2", "rgba(21,183,129,.16)"), "b2": ("#FFE2A6", "rgba(242,181,68,.14)"), "b3": ("#FFC2C4", "rgba(255,90,95,.14)")}[TONES.get(bars[k].get("tone"), ["b1", "b2", "b3", "b1"][k])]
            o.j("TL.to('#%s_lx%d',{color:'%s',backgroundColor:'%s',duration:.35},%.3f);", g, k, col[0], col[1], t)


def sc_alert(o, g, beats, gi):
    b = beats[0]; sp = b.scene
    o.html.append('<div class="warn"><div class="wi">%s</div><div class="rlabel wl">%s</div>%s<div style="margin-top:26px;display:flex;flex-direction:column;align-items:center">'
                  '%s<div class="bigred" id="%s_v">%s</div>%s</div></div>'
                  % (ic("warning", 96, "#FF8A8E", 2.4), esc(sp.get("title", "")), ('<div class="wsub">%s</div>' % esc(sp["sub"])) if sp.get("sub") else "",
                     ('<div class="rlabel atl" style="color:#FFC2C4">%s</div>' % esc(sp["prefix"])) if sp.get("prefix") else "", g, esc(sp.get("value", "")),
                     ('<div class="per">%s</div>' % esc(sp["suffix"])) if sp.get("suffix") else ""))
    s = b.start
    o.j("TL.to('#redv',{opacity:1,duration:.7},%.3f);", s - 0.45)
    o.j("gsap.set(['#%s .wi','#%s .wl','#%s .wsub','#%s .atl','#%s_v','#%s .per'],{opacity:0});", g, g, g, g, g, g)
    o.j("TL.fromTo('#%s .wi',{opacity:0,scale:.4},{opacity:1,scale:1,duration:.5,ease:'back.out(2)'},%.3f);", g, s - 0.05)
    o.j("TL.fromTo('#%s .wl',{opacity:0,y:20},{opacity:1,y:0,duration:.45},%.3f);", g, s + 0.15)
    o.j("TL.fromTo('#%s .wsub',{opacity:0,y:16},{opacity:1,y:0,duration:.45},%.3f);", g, b.at(sp.get("sub_at"), s + 1.4))
    land = b.at(sp.get("at"), s + 2.4)
    o.j("TL.fromTo('#%s .atl',{opacity:0},{opacity:1,duration:.35},%.3f);", g, land - 0.8)
    o.j("TL.fromTo('#%s_v',{opacity:0,scale:.7},{opacity:1,scale:1,duration:.55,ease:'back.out(1.6)'},%.3f);", g, land - 0.45)
    v = num_of(sp.get("value"))
    if v is not None and float(v).is_integer():
        frm = int(sp.get("from", 0) or 0)
        pre = "$" if str(sp.get("value", "")).startswith("$") else ""
        o.j("(()=>{const o={v:%d},el=document.getElementById('%s_v'),fin=el.textContent;TL.fromTo(o,{v:%d},{v:%d,duration:.75,ease:'power2.out',onUpdate:()=>{el.textContent=o.v>=%d-1e-6?fin:'%s'+Math.round(o.v).toLocaleString('en-US')}},%.3f)})();",
            frm, g, frm, int(v), int(v), pre, land - 0.45)
    o.j("TL.fromTo('#%s .per',{opacity:0},{opacity:1,duration:.35},%.3f);", g, land + 0.35)
    o.j("TL.to('#redv',{opacity:.55,duration:.25,yoyo:true,repeat:1},%.3f);", land + 0.3)
    o.cues += [("boom", s - 0.42, 0.5), ("riser", land - 1.7, 0.3), ("impact", land + 0.25, 0.55)]
    o.dips.append((s - 0.55, s + 0.35, 0.75))
    o.red = True


def sc_compare(o, g, beats, gi):
    b = beats[0]; sp = b.scene
    L, R = sp.get("left", {}), sp.get("right", {})

    def card(side, s, x):
        vals = s.get("values") or []
        mb = ""
        nv = [num_of(v) or 1 for v in vals]
        top = max(nv) if nv else 1
        for k, v in enumerate(vals[:4]):
            h = max(30, 220 * nv[k] / top)
            bx = 30 + k * 108
            mb += ('<div class="mb %s" id="%s_%sb%d" style="left:%dpx;height:%.0fpx"></div><div class="mv" id="%s_%sv%d" style="left:%dpx;bottom:%.0fpx">%s</div>'
                   % (["b1", "b2", "b3", "b1"][k], g, side, k, bx, h, g, side, k, bx - 10, 82 + h, esc(v)))
        if not vals:
            return ('<div class="pc" id="%s_%s" style="left:%dpx"><div class="h">%s</div>%s<div class="pcicon">%s</div></div>'
                    % (g, side, x, esc(s.get("title", "")), ('<div class="pcnote">%s</div>' % esc(s["note"])) if s.get("note") else "", ic(s.get("icon", "doc"), 150, "#6AF3C0", 1.6)))
        return ('<div class="pc" id="%s_%s" style="left:%dpx"><div class="h">%s%s</div>%s<div class="pcbase"></div>%s</div>'
                % (g, side, x, ic(s.get("icon", "doc"), 44, "#6AF3C0"), esc(s.get("title", "")),
                   ('<div class="pcnote">%s</div>' % esc(s["note"])) if s.get("note") else "", mb))
    o.html.append('%s%s<div class="eq">%s</div>%s' % (card("l", L, 0), card("r", R, 460), esc(sp.get("join", "=")),
                                                       ('<div class="same">%s</div>' % esc(sp["chip"])) if sp.get("chip") else ""))
    s = b.start
    o.j("TL.from('#%s_l',{x:-70,opacity:0,duration:.6,ease:'power3.out'},%.3f);", g, s - 0.15)
    o.j("TL.from('#%s_r',{x:70,opacity:0,duration:.6,ease:'power3.out'},%.3f);", g, s - 0.05)
    o.j("gsap.set(['#%s .eq','#%s .same'],{opacity:0});", g, g)
    o.j("TL.from('#%s_l .mb',{scaleY:0,transformOrigin:'50%% 100%%',duration:.5,stagger:.1,ease:'power3.out'},%.3f);", g, s + 0.25)
    o.j("TL.from('#%s_l .mv',{opacity:0,duration:.3,stagger:.1},%.3f);", g, s + 0.45)
    t = b.at(sp.get("at"), s + 1.6)
    o.j("TL.to('#%s_r',{borderColor:'rgba(255,122,127,.85)',boxShadow:'0 40px 90px rgba(0,0,0,.45),0 0 60px rgba(255,90,95,.35)',duration:.4},%.3f);", g, s + 0.6)
    o.j("gsap.set('#%s_r .mb',{scaleY:0,transformOrigin:'50%% 100%%'}); gsap.set('#%s_r .mv',{opacity:0});", g, g)
    o.j("TL.fromTo('#%s .eq',{opacity:0,scale:.5},{opacity:1,scale:1,duration:.45,ease:'back.out(2)'},%.3f);", g, t - 0.25)
    o.j("TL.to('#%s_r .mb',{scaleY:1,duration:.5,stagger:.12,ease:'power3.out'},%.3f);", g, t)
    o.j("TL.to('#%s_r .mv',{opacity:1,duration:.3,stagger:.12},%.3f);", g, t + 0.2)
    if sp.get("chip"):
        tc = b.at(sp.get("chip_at"), t + 0.7)
        o.j("TL.fromTo('#%s .same',{opacity:0,y:16},{opacity:1,y:0,duration:.45},%.3f);", g, tc - 0.15)
        o.cues.append(("chime", tc - 0.15, 0.26))


def sc_checklist(o, g, beats, gi):
    b = beats[0]; sp = b.scene
    items = sp.get("items") or [None] * int(sp.get("rows", 4))
    rows = ""
    for k, it in enumerate(items[:6]):
        txt = ('<span class="ckt">%s</span>' % esc(it)) if it else '<i style="width:%d%%"></i>' % [78, 62, 84, 55, 70, 66][k % 6]
        rows += '<div class="ckr"><div class="box" id="%s_bx%d">%s</div>%s</div>' % (g, k, ic("check", 30, "#04150E", 4), txt)
    tag = ('<div class="kicker" style="font-size:18px;padding:8px 14px"><i></i>%s</div>' % esc(sp["tag"])) if sp.get("tag") else ""
    btn = ('<div class="btn">%s %s</div>' % (esc(sp["button"]), ARROW)) if sp.get("button") else ""
    o.html.append('<div class="ck"><div style="display:flex;align-items:center;justify-content:space-between;gap:20px"><div class="ckh">%s</div>%s</div>%s</div>%s'
                  % (esc(sp.get("title", "")), tag, rows, btn))
    s = b.start
    o.j("TL.from('#%s .ck',{y:70,opacity:0,duration:.6,ease:'power3.out'},%.3f);", g, s - 0.1)
    for k in range(len(items[:6])):
        t = s + 0.45 + k * 0.28
        o.j("TL.to('#%s_bx%d',{backgroundColor:'#5CF0B6',borderColor:'#5CF0B6',duration:.15},%.3f);", g, k, t)
        o.j("TL.fromTo('#%s_bx%d svg',{opacity:0,scale:.4},{opacity:1,scale:1,duration:.25,ease:'back.out(2.5)'},%.3f);", g, k, t)
        o.cues.append(("tick", t, 0.28))
    if btn:
        tb = b.at(sp.get("button_at"), s + 0.45 + len(items[:6]) * 0.28 + 0.5)
        o.j("TL.fromTo('#%s .btn',{opacity:0,y:30,scale:.9},{opacity:1,y:0,scale:1,duration:.5,ease:'back.out(1.7)'},%.3f);", g, tb)


def sc_stat(o, g, beats, gi):
    b = beats[0]; sp = b.scene
    tone = {"amber": "tone-amber", "red": "tone-red"}.get(sp.get("tone"), "")
    chips = "".join('<span class="chip sch" id="%s_c%d">%s%s</span>' % (g, k, ic((c.get("icon") if isinstance(c, dict) else None) or "check", 30),
                                                                        esc(c.get("text") if isinstance(c, dict) else c)) for k, c in enumerate(sp.get("chips", [])[:4]))
    o.html.append('<div class="center">%s<div class="big sbig %s fit" id="%s_v">%s</div>%s%s</div>'
                  % (('<div class="label slab">%s</div>' % esc(sp["prefix"])) if sp.get("prefix") else "", tone, g, esc(sp.get("value", "")),
                     ('<div class="ssuf">%s</div>' % esc(sp["label"])) if sp.get("label") else "", ('<div class="chips">%s</div>' % chips) if chips else ""))
    s = b.start
    said = b.at(sp.get("at"), s + 0.5)
    land = min(said, s + LATE)
    o.j("TL.from('#%s .slab,#%s .ssuf',{opacity:0,y:20,duration:.5},%.3f);", g, g, s - 0.1)
    if said > land + 0.6:
        pulse(o, "#%s_v" % g, said, 1.1)
    o.j("TL.fromTo('#%s_v',{opacity:0,scale:.7},{opacity:1,scale:1,duration:.55,ease:'back.out(1.6)'},%.3f);", g, land - 0.4)
    v = num_of(sp.get("value"))
    raw = str(sp.get("value", ""))
    if v is not None and float(v).is_integer() and re.match(r"^\$?\d[\d,]*$", raw):
        pre = "$" if raw.startswith("$") else ""
        o.j("(()=>{const o={v:0},el=document.getElementById('%s_v'),fin=el.textContent;TL.fromTo(o,{v:%d},{v:%d,duration:.8,ease:'power2.out',onUpdate:()=>{el.textContent=o.v>=%d-1e-6?fin:'%s'+Math.round(o.v).toLocaleString('en-US')}},%.3f)})();",
            g, int(sp.get("from", 0) or 0), int(v), int(v), pre, land - 0.4)
        for q in range(4):
            o.cues.append(("tick", land - 0.4 + q * 0.12, 0.2))
    if sp.get("tone") == "red":
        o.cues.append(("impact", land + 0.2, 0.4))
    cats = sp.get("chips_at") or []
    for k in range(len(sp.get("chips", [])[:4])):
        t = b.at(cats[k] if k < len(cats) else None, land + 0.6 + k * 0.45)
        o.j("TL.fromTo('#%s_c%d',{opacity:0,y:20},{opacity:1,y:0,duration:.4},%.3f);", g, k, t - 0.1)
        o.cues.append(("tick", t - 0.1, 0.22))


def sc_map(o, g, beats, gi):
    b = beats[0]; sp = b.scene
    m = us_map(); width = 840; s = width / m["w"]; h = m["h"] * s
    states = [x for x in sp.get("states", []) if x in m["states"]][:4]
    hl, pins, labs = "", "", ""
    for k, code in enumerate(states):
        st = m["states"][code]; cx, cy = st["c"]
        hl += '<path id="%s_s%d" d="%s" fill="rgba(21,183,129,.42)" stroke="#6AF3C0" stroke-width="2.2" stroke-linejoin="round" opacity="0"/>' % (g, k, st["albers"])
        pins += ('<g id="%s_p%d" opacity="0" style="transform-origin:%spx %spx"><circle cx="%s" cy="%s" r="17" fill="none" stroke="rgba(106,243,192,.55)" stroke-width="2"/>'
                 '<circle cx="%s" cy="%s" r="7" fill="#B9FBE2"/></g>' % (g, k, cx, cy, cx, cy, cx, cy))
        name = (sp.get("labels") or {}).get(code, st["name"])
        labs += ('<div id="%s_l%d" style="position:absolute;left:%.0fpx;top:%.0fpx;transform:translateX(-50%%);display:flex;flex-direction:column;align-items:center;opacity:0">'
                 '<div class="maplabel">%s</div><div style="width:2px;height:40px;background:linear-gradient(#6AF3C0,rgba(106,243,192,0))"></div></div>' % (g, k, cx * s, cy * s - 96, esc(name)))
    o.html.append('<div style="position:absolute;left:0;top:70px;width:%dpx;height:%.0fpx"><svg viewBox="0 0 %d %d" width="%d" height="%.0f" style="overflow:visible;position:absolute;inset:0">'
                  '<path d="%s" fill="rgba(255,255,255,.04)" stroke="rgba(255,255,255,.30)" stroke-width="1.3"/><path d="%s" fill="none" stroke="rgba(255,255,255,.13)" stroke-width=".9"/>%s%s</svg>%s</div>'
                  % (width, h, m["w"], m["h"], width, h, m["nation"], m["mesh"], hl, pins, labs))
    ats = sp.get("at") or []
    o.j("TL.from('#%s svg',{opacity:0,duration:.6},%.3f);", g, b.start - 0.1)
    for k in range(len(states)):
        t = b.at(ats[k] if k < len(ats) else None, b.start + 0.6 + k * 0.7)
        o.j("TL.to('#%s_s%d',{opacity:1,duration:.4},%.3f); TL.fromTo('#%s_p%d',{opacity:0,scale:.3},{opacity:1,scale:1,duration:.5,ease:'back.out(2)'},%.3f); TL.fromTo('#%s_l%d',{opacity:0,y:20},{opacity:1,y:0,duration:.4},%.3f);",
            g, k, t - 0.3, g, k, t - 0.2, g, k, t - 0.05)
        o.cues.append(("tick", t - 0.2, 0.3))


def sc_icons(o, g, beats, gi):
    b = beats[0]; sp = b.scene
    items = sp.get("items", [])[:4]
    tiles = "".join('<div class="itile" id="%s_i%d"><div class="ico big2">%s</div><div class="itl">%s</div></div>' % (g, k, ic(it.get("icon", "check"), 64), esc(it.get("label", "")))
                    for k, it in enumerate(items))
    o.html.append('<div class="center"><div class="igrid n%d">%s</div></div>' % (len(items), tiles))
    # every tile is on stage, dimmed, from the start of the beat; each one lights up on its word
    o.j("TL.fromTo('#%s .itile',{opacity:0,y:40,scale:.9},{opacity:.3,y:0,scale:.95,duration:.5,stagger:.08,ease:'power3.out'},%.3f);", g, b.start - 0.1)
    for k, it in enumerate(items):
        t = max(b.start + 0.6, b.at(it.get("at"), b.start + 0.3 + k * 0.55) - 0.15)
        o.j("TL.to('#%s_i%d',{opacity:1,scale:1.06,duration:.22,ease:'power2.out'},%.3f); TL.to('#%s_i%d',{scale:1,duration:.3,ease:'power2.inOut'},%.3f);",
            g, k, t, g, k, t + 0.22)
        o.cues.append(("tick", t, 0.25))


def sc_steps(o, g, beats, gi):
    b = beats[0]; sp = b.scene
    items = sp.get("items", [])[:5]
    rows = "".join('<div class="step" id="%s_s%d"><div class="stepn">%d</div><div class="stept">%s</div></div>' % (g, k, k + 1, esc(x)) for k, x in enumerate(items))
    o.html.append('<div class="center"><div class="card" style="padding:30px 34px;width:840px">%s</div></div>' % rows)
    ats = sp.get("at") or []
    o.j("TL.from('#%s .card',{opacity:0,y:40,duration:.5},%.3f);", g, b.start - 0.15)
    for k in range(len(items)):
        t = b.at(ats[k] if k < len(ats) else None, b.start + 0.3 + k * 0.6)
        o.j("TL.fromTo('#%s_s%d',{opacity:0,x:-40},{opacity:1,x:0,duration:.45},%.3f);", g, k, t - 0.15)
        o.cues.append(("tick", t - 0.15, 0.22))


def sc_quote(o, g, beats, gi):
    b = beats[0]; sp = b.scene
    o.html.append('<div class="center"><div class="card qcard"><div class="qm">“</div><div>%s<div class="quote">%s”</div></div></div></div>'
                  % (('<div class="label" style="margin-bottom:14px">%s</div>' % esc(sp["source"])) if sp.get("source") else "", esc(sp.get("text", ""))))
    o.j("TL.from('#%s .qcard',{opacity:0,y:50,duration:.6,ease:'power3.out'},%.3f);", g, b.start - 0.1)


def sc_gauge(o, g, beats, gi):
    b = beats[0]; sp = b.scene
    n = int(sp.get("gaps", 3))
    bars = "".join('<div class="gapr"><span>%s %d</span><i id="%s_g%d" style="width:%d%%"></i></div>' % (esc(sp.get("gap_label", "Gap")), k + 1, g, k, [86, 64, 48, 36][k % 4]) for k in range(n))
    o.html.append('<div class="center"><svg width="420" height="230" viewBox="0 0 420 230"><path d="M30 210 A180 180 0 0 1 390 210" fill="none" stroke="rgba(255,255,255,.14)" stroke-width="26" stroke-linecap="round"/>'
                  '<path id="%s_arc" d="M30 210 A180 180 0 0 1 390 210" fill="none" stroke="url(#%s_gr)" stroke-width="26" stroke-linecap="round"/><defs><linearGradient id="%s_gr"><stop offset="0" stop-color="#FF8A8E"/><stop offset=".5" stop-color="#FFD57A"/><stop offset="1" stop-color="#5CF0B6"/></linearGradient></defs></svg>'
                  '<div class="label" style="margin-top:6px;font-size:24px">%s</div><div class="gaps">%s</div></div>' % (g, g, g, esc(sp.get("label", "")), bars))
    o.j("(()=>{const p=document.getElementById('%s_arc'),L=p.getTotalLength();p.style.strokeDasharray=L;TL.fromTo(p,{strokeDashoffset:L},{strokeDashoffset:L*0.28,duration:1.2,ease:'power2.out'},%.3f)})();", g, b.start + 0.1)
    for k in range(n):
        t = b.at((sp.get("at") or [None] * 9)[k] if k < len(sp.get("at") or []) else None, b.start + 1.0 + k * 0.4)
        o.j("TL.from('#%s_g%d',{scaleX:0,transformOrigin:'0 50%%',duration:.5,ease:'power3.out'},%.3f);", g, k, t)
        o.cues.append(("tick", t, 0.22))


def end_card(piece, voiced, disclaimer):
    c = piece["content"]
    offer = ('<div class="eoffer">%s</div>' % esc(c["offer"])) if c.get("offer") else ""
    fine = []
    if disclaimer:
        fine.append(DISCLAIMER)
    if voiced:
        fine.append(AI_NOTE)
    return ('<div class="endc" id="endc"><div class="mark" style="width:150px;height:150px;border-radius:21px;font-size:82px">FD</div>'
            '<div class="ebrand">Finance Department</div>%s<div class="ecta">%s %s</div><div class="esite">%s</div>'
            '<div class="efine">%s</div></div>' % (offer, esc(c["cta"]), ARROW, SITE, "<br>".join(fine)))


CSS = """
.slide{width:1080px;height:1920px}
.top{top:400px;left:80px;right:160px}
.ai{display:inline-flex;align-items:center;gap:10px;padding:9px 16px;border-radius:999px;border:1px solid rgba(255,255,255,.25);background:rgba(255,255,255,.06);
 font-weight:600;font-size:19px;letter-spacing:.14em;color:#C9D1DB}
.kick{position:absolute;left:80px;top:480px;z-index:5}
.stage{position:absolute;left:80px;top:570px;width:840px;height:600px;z-index:4}
.scene{position:absolute;inset:0}
.hlw{position:absolute;left:0;right:0;top:-10px;height:830px;display:flex;align-items:center}
.hlt{font-family:'Plex';font-weight:600;line-height:1.16;color:#fff;letter-spacing:-.01em;text-wrap:balance}
.hlt.serif{font-family:'SS4';font-weight:600;letter-spacing:-.02em;line-height:1.06}
.hlt span{opacity:.18}.hlt span.n1{color:#6AF3C0}
.form{position:absolute;left:120px;top:90px;width:600px;padding:30px 32px 30px;border-radius:24px;background:linear-gradient(180deg,#FAFCFB,#E9EFEC);color:#06162D;
 box-shadow:0 50px 100px rgba(0,0,0,.55),0 0 0 1px rgba(255,255,255,.6) inset}
.form.mini{left:420px;top:10px;transform:translateX(-50%) scale(.62);transform-origin:50% 0}
.dlab{font-size:20px;font-weight:600;letter-spacing:.14em;color:#4E596A}
.dtitle{font-family:SS4;font-weight:700;font-size:62px;line-height:1;color:#06162D;letter-spacing:-.02em}
.dtag{padding:10px 18px;border-radius:12px;background:#0B7955;color:#fff;font-weight:600;font-size:26px}
.fld{position:relative;display:flex;align-items:center;gap:14px;height:62px;margin-top:12px;padding:0 18px;border:1.5px solid #C5D0CB;border-radius:12px;background:#fff}
.fld:first-of-type{margin-top:22px}
.fld span{font-size:17px;font-weight:600;letter-spacing:.1em;color:#6B7686;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.fld i{display:block;height:14px;border-radius:7px;background:#DCE3E0;margin-left:auto}
.fld b{font-family:SS4;font-size:30px;color:#06162D;margin-left:auto}
.fld b+i{margin-left:0}
.docw{position:absolute;inset:0}
.stamp{position:absolute;padding:8px 22px;border:6px solid #E5484D;border-radius:14px;color:#E5484D;font-weight:600;font-size:64px;letter-spacing:.12em;background:rgba(229,72,77,.07);opacity:0;white-space:nowrap}
.stamp.st0{right:94px;top:208px}.stamp.st1{left:180px;top:380px}.stamp.st2{left:300px;top:260px}
.node{position:absolute;top:300px;width:170px;display:flex;flex-direction:column;align-items:center;gap:14px}
.nc{width:150px;height:150px;border-radius:50%;display:grid;place-items:center;background:radial-gradient(circle at 35% 30%,rgba(21,183,129,.35),rgba(6,22,45,.9) 70%);
 border:2px solid rgba(106,243,192,.6);box-shadow:0 0 50px rgba(21,183,129,.3)}
.nl{font-weight:600;font-size:26px;letter-spacing:.14em;color:#E8F4EF;text-transform:uppercase;white-space:nowrap}
.minic{position:absolute;width:150px;padding:14px 16px;border-radius:14px;background:#F3F6F5;box-shadow:0 20px 40px rgba(0,0,0,.45);opacity:0}
.minic div{height:10px;border-radius:5px;background:#CBD5D1;margin-top:8px}
.minic div:first-child{margin-top:0;height:14px;width:60%;background:#0B7955}
.calB{position:absolute;left:310px;top:300px;width:220px;border-radius:26px;overflow:hidden;background:#F4F7F6;color:#06162D;text-align:center;box-shadow:0 30px 70px rgba(0,0,0,.55)}
.calB .m{background:#0B7955;color:#fff;font-weight:600;font-size:24px;letter-spacing:.18em;padding:12px 4px 11px;white-space:nowrap}
.calB .d{font-family:SS4;font-weight:700;font-size:118px;line-height:1.02;padding:6px 0 0}
.calB .s{font-weight:600;font-size:21px;letter-spacing:.16em;color:#4E596A;padding:0 0 18px;min-height:20px}
.center{position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center}
.center .calB{position:relative;left:auto;top:auto}
.center .calB.big{width:300px}.center .calB.big .d{font-size:160px}.center .calB.big .m{font-size:30px}
.dtext{font-family:SS4;font-weight:600;font-size:46px;color:#fff;margin-top:34px}
.lad{position:absolute;left:0;right:0;top:60px;height:470px}
.base{position:absolute;left:0;right:0;bottom:90px;height:2px;background:rgba(255,255,255,.35)}
.lc{position:absolute;bottom:92px;display:flex;flex-direction:column;align-items:center}
.lv{font-family:SS4;font-weight:700;font-size:70px;line-height:1;letter-spacing:-.02em;margin-bottom:14px;color:#fff;white-space:nowrap}
.lb{width:100%;border-radius:18px 18px 6px 6px}
.lg{position:absolute;bottom:92px;border-radius:18px 18px 6px 6px;border:2px dashed rgba(255,255,255,.18)}
.lx{position:absolute;bottom:0;height:84px;text-align:center;font-weight:600;font-size:25px;line-height:1.25;color:#8C99AB;padding-top:14px;border-radius:14px}
.b1{background:linear-gradient(180deg,#5CF0B6,#0F8C61);box-shadow:0 0 50px rgba(21,183,129,.45)}
.b2{background:linear-gradient(180deg,#FFD57A,#C98A12);box-shadow:0 0 50px rgba(242,181,68,.45)}
.b3{background:linear-gradient(180deg,#FF9A9D,#C9363C);box-shadow:0 0 60px rgba(255,90,95,.5)}
.redv{position:absolute;inset:0;background:radial-gradient(120% 80% at 50% 45%,transparent 35%,rgba(200,30,40,.55) 100%);opacity:0;z-index:3;pointer-events:none}
.warn{position:absolute;left:0;right:0;top:10px;display:flex;flex-direction:column;align-items:center;gap:16px}
.rlabel{font-weight:600;font-size:30px;letter-spacing:.16em;color:#FF9EA2;text-transform:uppercase;text-align:center}
.wsub{font-size:30px;color:#E7C9CB;text-align:center}
.per{font-size:30px;color:#E7C9CB;margin-top:10px}
.bigred{font-family:SS4;font-weight:700;font-size:250px;line-height:.9;letter-spacing:-.04em;background:linear-gradient(180deg,#FFD0D2 0%,#FF6B70 45%,#B4242B 100%);
 -webkit-background-clip:text;background-clip:text;color:transparent;filter:drop-shadow(0 18px 50px rgba(255,90,95,.45));white-space:nowrap}
.pc{position:absolute;top:30px;width:380px;height:470px;border-radius:30px;padding:28px 28px;background:linear-gradient(180deg,rgba(255,255,255,.09),rgba(255,255,255,.02));
 border:1px solid rgba(255,255,255,.15);box-shadow:0 40px 90px rgba(0,0,0,.45)}
.pc .h{display:flex;align-items:center;gap:16px;font-family:SS4;font-weight:600;font-size:38px;color:#fff}
.pcnote{font-size:26px;color:#C9D1DB;margin-top:16px;line-height:1.3}
.pcicon{position:absolute;left:0;right:0;bottom:60px;display:flex;justify-content:center;opacity:.95;filter:drop-shadow(0 0 30px rgba(21,183,129,.45))}
.mb{position:absolute;bottom:80px;width:76px;border-radius:10px 10px 4px 4px}
.mv{position:absolute;width:96px;text-align:center;font-family:SS4;font-weight:700;font-size:30px;color:#fff}
.pcbase{position:absolute;left:28px;right:28px;bottom:78px;height:2px;background:rgba(255,255,255,.3)}
.eq{position:absolute;left:50%;top:205px;transform:translateX(-50%);width:84px;height:84px;border-radius:50%;display:grid;place-items:center;background:#0B7955;
 font-family:SS4;font-weight:700;font-size:44px;color:#fff;box-shadow:0 0 0 8px rgba(21,183,129,.18),0 20px 50px rgba(21,183,129,.4);z-index:2}
.same{position:absolute;left:50%;bottom:0;transform:translateX(-50%);padding:14px 26px;border-radius:999px;background:rgba(21,183,129,.14);border:1px solid rgba(106,243,192,.55);
 color:#D6FBEB;font-weight:600;font-size:26px;letter-spacing:.04em;white-space:nowrap}
.ck{position:absolute;left:110px;top:10px;width:620px;border-radius:30px;padding:32px 34px;background:linear-gradient(180deg,rgba(255,255,255,.10),rgba(255,255,255,.025));
 border:1px solid rgba(106,243,192,.35);box-shadow:0 40px 90px rgba(0,0,0,.45),0 0 60px rgba(21,183,129,.15)}
.ckh{font-family:SS4;font-weight:600;font-size:40px;color:#fff;text-align:left}
.ckr{display:flex;align-items:center;gap:20px;margin-top:22px}
.ckt{font-size:28px;color:#E5ECE9;text-align:left}
.box{width:46px;height:46px;border-radius:12px;border:2px solid rgba(255,255,255,.35);display:grid;place-items:center;flex:none}
.box svg{opacity:0}
.ckr i{display:block;height:16px;border-radius:8px;background:rgba(255,255,255,.18)}
.btn{position:absolute;left:50%;transform:translateX(-50%);top:480px;display:inline-flex;align-items:center;gap:14px;white-space:nowrap;padding:24px 36px;border-radius:999px;
 font-weight:600;font-size:31px;color:#04150E;background:linear-gradient(180deg,#5CF0B6,#16B07B);box-shadow:0 18px 54px rgba(21,183,129,.5),inset 0 1px 0 rgba(255,255,255,.5)}
.sbig{font-size:230px;max-width:840px}
.slab{font-size:26px;margin-bottom:10px}
.ssuf{font-size:34px;color:#DCE4EA;margin-top:22px;max-width:760px;line-height:1.3}
.chips{display:flex;flex-wrap:wrap;gap:14px;justify-content:center;margin-top:34px;max-width:840px}
.sch{font-size:26px}
.igrid{display:grid;gap:22px;width:840px}
.igrid.n1{grid-template-columns:1fr}.igrid.n2{grid-template-columns:1fr 1fr}.igrid.n3{grid-template-columns:1fr 1fr 1fr}.igrid.n4{grid-template-columns:1fr 1fr}
.igrid.n3 .itl{font-size:27px}.igrid.n3 .itile{padding:26px 14px}
.itile{border-radius:28px;padding:30px 20px;background:linear-gradient(180deg,rgba(255,255,255,.09),rgba(255,255,255,.02));border:1px solid rgba(255,255,255,.14);
 display:flex;flex-direction:column;align-items:center;gap:20px;box-shadow:0 30px 70px rgba(0,0,0,.4)}
.ico.big2{width:110px;height:110px;border-radius:28px}
.itl{font-family:SS4;font-weight:600;font-size:34px;color:#fff;line-height:1.15}
.step{display:flex;align-items:center;gap:22px;padding:16px 0;text-align:left}
.stepn{width:62px;height:62px;border-radius:50%;display:grid;place-items:center;background:#0B7955;color:#fff;font-family:SS4;font-weight:700;font-size:32px;flex:none;box-shadow:0 0 0 6px rgba(21,183,129,.15)}
.stept{font-size:32px;line-height:1.28;color:#E9F0EC}
.qcard{padding:40px 40px 44px;display:flex;gap:26px;align-items:flex-start;text-align:left;width:840px;background:linear-gradient(180deg,rgba(21,183,129,.17),rgba(21,183,129,.04));border-color:rgba(60,220,160,.38)}
.gaps{width:640px;margin-top:30px;display:flex;flex-direction:column;gap:16px}
.gapr{display:flex;align-items:center;gap:18px}.gapr span{width:110px;text-align:left;font-weight:600;font-size:22px;letter-spacing:.1em;color:#FFC2C4;text-transform:uppercase}
.gapr i{display:block;height:22px;border-radius:11px;background:linear-gradient(90deg,#FF8A8E,#FFD57A)}
.caps{position:absolute;left:80px;top:1205px;width:840px;height:200px;z-index:6}
.cap{position:absolute;left:0;top:0;width:100%;font-weight:600;font-size:54px;line-height:1.2;color:#fff;opacity:0;text-shadow:0 4px 24px rgba(0,0,0,.6)}
.cap span{opacity:.28}.cap span.n1{color:#6AF3C0}
.capband{position:absolute;left:0;right:0;top:1150px;height:300px;background:linear-gradient(180deg,transparent,rgba(3,11,25,.55) 40%,rgba(3,11,25,.55) 70%,transparent);z-index:5;opacity:0}
.endc{position:absolute;inset:0;z-index:8;display:flex;flex-direction:column;align-items:center;justify-content:center;opacity:0;padding:0 160px 0 80px;text-align:center;
 background:radial-gradient(900px 700px at 50% 45%,rgba(11,121,85,.25),transparent 70%),linear-gradient(160deg,#0B2343,#06162D 55%,#030B19)}
.ebrand{font-family:SS4;font-weight:600;font-size:60px;color:#F7FAF9;margin-top:34px}
.eoffer{font-size:32px;color:#8BF0CA;margin-top:30px;font-weight:600}
.ecta{display:inline-flex;align-items:center;gap:16px;margin-top:40px;padding:26px 40px;border-radius:999px;font-weight:600;font-size:34px;color:#04150E;
 background:linear-gradient(180deg,#5CF0B6,#16B07B);box-shadow:0 18px 54px rgba(21,183,129,.5),inset 0 1px 0 rgba(255,255,255,.5);max-width:840px;line-height:1.2}
.esite{font-size:30px;color:#C9D1DB;margin-top:30px;letter-spacing:.02em}
.efine{position:absolute;left:80px;right:160px;top:1250px;text-align:center;font-size:24px;line-height:1.5;color:#8C99AB}
.dot{position:absolute;width:6px;height:6px;border-radius:50%;background:#6AF3C0;box-shadow:0 0 12px rgba(106,243,192,.9);opacity:0}
"""

SCENES = {"headline", "stat", "doc", "route", "date", "ladder", "alert", "compare", "checklist", "map", "icons", "steps", "quote", "gauge", "end"}


def build(piece, beats, voiced=True, disclaimer=False):
    """The whole video as one page with a GSAP timeline. Returns (html, total, cues, dips, looks)."""
    end_at, total = lay_out(beats)
    c = piece["content"]
    # group consecutive beats that share a scene id
    groups = []
    for b in beats:
        if b.scene.get("type") == "end":
            continue
        if groups and group_id(groups[-1][-1]) == group_id(b):
            groups[-1].append(b)
        else:
            groups.append([b])
    o = Out()
    scene_html = []
    caption_html, cap_js, cap_pages = [], [], []
    red_any = False
    for gi, gb in enumerate(groups):
        typ = gb[0].scene.get("type", "headline")
        if typ not in SCENES:
            raise ValueError("unknown scene type %s" % typ)
        g = "g%d" % gi
        prev = groups[gi - 1][-1] if gi else None
        nxt = groups[gi + 1][0] if gi + 1 < len(groups) else None
        sub = Out(); sub.exit_style = None; sub.red = False
        if typ == "headline":
            sc_headline(sub, g, gb, gi, c.get("kicker"))
        elif typ == "doc":
            sc_doc(sub, g, gb, gi, nxt.scene.get("type") if nxt else None)
        elif typ == "route":
            sc_route(sub, g, gb, gi, prev)
        else:
            {"stat": sc_stat, "date": sc_date, "ladder": sc_ladder, "alert": sc_alert, "compare": sc_compare, "checklist": sc_checklist,
             "map": sc_map, "icons": sc_icons, "steps": sc_steps, "quote": sc_quote, "gauge": sc_gauge}[typ](sub, g, gb, gi)
        red_any = red_any or sub.red
        scene_html.append('<div class="scene" id="%s">%s</div>' % (g, "".join(sub.html)))
        start = gb[0].start - 0.45
        o.j("gsap.set('#%s',{autoAlpha:0}); TL.to('#%s',{autoAlpha:1,duration:.01},%.3f);", g, g, max(0, start))
        o.js += sub.js
        o.cues += sub.cues
        o.dips += sub.dips
        if gi:
            o.cues.append(("whoosh", max(0, gb[0].start - 0.55), 0.22))
        out_t = (nxt.start - 0.5) if nxt else end_at - 0.05
        if sub.exit_style == "shrink" and nxt is not None:
            o.j("TL.to('#%s .stamp',{opacity:0,duration:.3},%.3f);", g, out_t - 0.3)
            o.j("TL.to('#%s .form',{scale:.62,y:-80,x:0,rotation:0,duration:.6,ease:'power3.inOut',transformOrigin:'50%% 0%%'},%.3f);", g, out_t - 0.35)
            o.j("TL.to('#%s',{autoAlpha:0,duration:.01},%.3f);", g, out_t + 0.3)
        else:
            o.j("TL.to('#%s',{autoAlpha:0,y:-40,duration:.4,ease:'power2.in'},%.3f);", g, out_t)
        if sub.red:
            o.j("TL.to('#redv',{opacity:0,duration:.6},%.3f);", out_t)
        # captions for every beat whose scene does not show the words itself
        if typ != "headline":
            for b in gb:
                for pi, page in enumerate(caption_pages(b)):
                    cid = "cap%d_%d" % (b.i, pi)
                    spans = "".join('<span class="%s">%s</span> ' % (word_cls(w), esc(w)) for w, _ in page)
                    caption_html.append('<div class="cap" id="%s">%s</div>' % (cid, spans))
                    show = page[0][1] - 0.06
                    pages = caption_pages(b)
                    nxt_show = pages[pi + 1][0][1] - 0.06 if pi + 1 < len(pages) else None
                    hide = min(nxt_show - 0.22, page[-1][1] + 1.0) if nxt_show else b.end + 0.45
                    cap_pages.append([cid, show, hide])
                    cap_js.append("TL.fromTo('#%s',{opacity:0,y:18},{opacity:1,y:0,duration:.16,ease:'power2.out'},%.3f);" % (cid, show))
                    for k, (w, t) in enumerate(page):
                        cap_js.append("TL.to('#%s span:nth-child(%d)',{opacity:1,duration:.12},%.3f);" % (cid, k + 1, t))
                cap_js.append("TL.to('#capband',{opacity:1,duration:.3},%.3f); TL.to('#capband',{opacity:0,duration:.3},%.3f);" % (b.start - 0.2, b.end + 0.3))
    cap_pages.sort(key=lambda x: x[1])
    for k, (cid, show, hide) in enumerate(cap_pages):
        if k + 1 < len(cap_pages):
            hide = min(hide, cap_pages[k + 1][1] - 0.2)
        cap_js.append("TL.to('#%s',{opacity:0,duration:.14},%.3f);" % (cid, max(show + 0.3, hide)))
    # end card, spoken over when the call to action has no scene of its own
    last = beats[-1]
    endc = end_card(piece, voiced, disclaimer)
    o.j("TL.to('#endc',{opacity:1,duration:.6,ease:'power1.inOut'},%.3f);", end_at)
    o.j("TL.from('#endc .mark',{scale:.6,opacity:0,duration:.6,ease:'back.out(1.8)'},%.3f);", end_at + 0.15)
    o.j("TL.from('#endc .ecta',{y:30,opacity:0,duration:.5,ease:'back.out(1.6)'},%.3f);", end_at + 0.45)
    o.cues.append(("chime", end_at + 0.2, 0.3))
    if last.scene.get("type") != "end":
        o.cues.append(("whoosh", end_at - 0.2, 0.2))
    kick = ('<div class="kick"><div class="kicker" id="kick"><i></i>%s</div></div>' % esc(c["kicker"])) if c.get("kicker") else ""
    ai = '<div class="ai">%sAI VOICE</div>' % WAVE if voiced else ""
    body = ('<div id="dots"></div><div class="top"><div class="brand"><div class="mark">FD</div>Finance Department</div>%s</div>%s'
            '<div class="redv" id="redv"></div><div class="stage" id="stage">%s</div><div class="capband" id="capband"></div><div class="caps">%s</div>%s'
            % (ai, kick, "".join(scene_html), "".join(caption_html), endc))
    script = TIMELINE % {"T": total, "JS": "\n".join(o.js + cap_js)}
    html = shell(body, W, H, CSS, "video", script=script)
    looks = [round(max(0.2, (gb[0].start + gb[-1].end) / 2), 2) for gb in groups] + [round(min(total - 0.3, end_at + 1.6), 2)]
    return html, total, o.cues, o.dips, looks


TIMELINE = r"""
<script>
gsap.ticker.lagSmoothing(0);
const T=%(T)s; const TL=gsap.timeline({paused:true}); window.TLREF=TL;
TL.fromTo('.g1',{x:0,y:0},{x:-120,y:90,duration:T,ease:'sine.inOut'},0);
TL.fromTo('.g2',{x:0,y:0},{x:110,y:-120,duration:T,ease:'sine.inOut'},0);
TL.fromTo('#stage',{scale:1},{scale:1.035,duration:T,ease:'none',transformOrigin:'50%% 50%%'},0);
TL.from('#kick',{opacity:0,y:-16,duration:.5,ease:'power3.out'},0.05);
TL.to('#kick',{opacity:0,duration:.4},Math.max(0.1,T-3.4));
let seed=7; const rnd=()=>(seed=(seed*16807)%%2147483647)/2147483647;
const DOTS=[]; const dots=document.getElementById('dots');
for(let i=0;i<24;i++){const d=document.createElement('div');d.className='dot';d.style.left=(60+rnd()*900)+'px';d.style.top=(560+rnd()*1100)+'px';dots.appendChild(d);
  DOTS.push({el:d,s:0.5+rnd()*1.1,dur:7+rnd()*6,ph:rnd()});}
function drawDots(t){for(const p of DOTS){const u=((t/p.dur)+p.ph)%%1;const o=u<.5?u*2:(1-u)*2;p.el.style.transform=`translateY(${-520*u}px) scale(${p.s})`;p.el.style.opacity=(o*.55).toFixed(3);}}
window.fitNow=()=>{document.querySelectorAll('.fit').forEach((el)=>{
  let fs=parseFloat(getComputedStyle(el).fontSize); const room=840-8;
  const textW=()=>{const r=document.createRange(); r.selectNodeContents(el); const sc=(el.getBoundingClientRect().width/(el.offsetWidth||1))||1; return r.getBoundingClientRect().width/sc;};
  let guard=0; while(textW()>room&&fs>40&&guard++<80){fs-=4;el.style.fontSize=fs+'px';}
});};
%(JS)s
TL.set({},{},T);
window.seek=(t)=>{TL.seek(t,false);drawDots(t);return true};
window.final=()=>{TL.seek(T-0.5,false);return T};
</script>"""
