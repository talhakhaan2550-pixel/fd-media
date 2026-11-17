"""Motion v2 for reels (17 November 2026): motion graphics instead of narrated slides.

What changes from video.py (which stays as it is for every piece without content.motion):
- One camera over a paper desk. Every shot sits at its own place on a large world, and the camera pushes and
  pans (with a slight roll) from one shot to the next. No colour wipes.
- Frame one is the hook: the hook's title and its object are fully on screen at 0 seconds, already moving.
- One big object per shot that does what the narrator is saying, timed to the spoken word (a form fills in,
  a stamp lands, a calendar flips, a fax takes the pages, a figure counts up).
- Big captions, two to four words at a time, figures on the marker, for people watching with the sound off.
- Middle of funnel pieces carry a STEP n OF N pill and a progress bar; each step is a verb-first title.
- Every piece ends with its stage's call to action (top: follow; middle: comment a keyword for a free tool;
  bottom: DM a keyword for the offer's page), then the end card with Talha's real photo.

A piece's content.motion:
  stage:   "top" | "middle" | "bottom"
  pills:   labels for the top pill, by shot index (0 is the hook); a missing index keeps the last label
  hook:    {"text", "say", "shot": {...}}                      the hook's words are its title, so no captions
  shots:   [{"shot": {...}, "step": n, "lines": [{"text", "say"}, ...]}]   several lines keep the camera still
  cta:     {"text", "say", "kind": "follow" | "comment" | "dm", "keyword", "pill", "shot": {...}}
  offer:   optional words under Talha's name on the end card
  shots may also hold {"cover": "<offer id>", "pill": "What you get"}: it becomes one numbered station per item
  the offer covers (tools/coverage.json, word for word from its page) and a recap naming it (work.py). Talha,
  17 November 2026: a piece that introduces a service or quotes a price shows what it covers first.
Shot types: versus, form, castpay, bars, calendar, follow, person, checklist, docpair, fax, deadline, penalty,
comment, report, days, price, proof, nofee, phone, and from work.py work and recap. Every word on screen restates
the piece's own approved words: a shot never adds a fact.
"""
import math
from brand import esc, ic, shell, SITE, DISCLAIMER, photo_uri, texture_uri
import cast
import video

W, H, FPS = 1080, 1920, 30
START, GAP, GAP_SAME, MOVE, LAND = 0.12, 0.34, 0.18, 0.8, 0.18
END_HOLD = 2.8
ROLL = [0, -2.5, 2.0, -1.6, 2.4, -2.0, 1.6, -2.4, 2.2, -1.8]


def station_xy(i):
    return (i % 2) * 1500 + (i // 2) * 160, i * 1300


def at(b, word=None, frac=0.3, nth=0):
    """Absolute time of a spoken word in beat b (start of its first match), or a share of the beat."""
    if word:
        t = b.at(word, default=-1, nth=nth)
        if t >= 0:
            return t
    return b.start + frac * b.dur


class Out:
    def __init__(self):
        self.html, self.js, self.cues = [], [], []

    def h(self, s):
        self.html.append(s)

    def j(self, s, *a):
        self.js.append(s % a if a else s)

    def cue(self, name, t, g=0.3):
        self.cues.append((name, max(0.0, t), g))


def sprite(who, expr, height):
    who, expr = cast.pose(who, expr)
    uri, w, h = cast.sprite(who, expr)
    return '<img class="spr" alt="" src="%s" style="height:%dpx;width:%dpx">' % (uri, height, round(w * height / h))


CHECK = '<svg viewBox="0 0 48 48" width="%d" height="%d"><path d="M10 25l9 9 19-20" fill="none" stroke="%s" stroke-width="6" stroke-linecap="round" stroke-linejoin="round"/></svg>'
CROSS = '<svg viewBox="0 0 48 48" width="%d" height="%d"><path d="M12 12l24 24M36 12L12 36" fill="none" stroke="%s" stroke-width="6" stroke-linecap="round"/></svg>'


def check(size=44, color="#0B7955"):
    return CHECK % (size, size, color)


def cross(size=44, color="#C23A2B"):
    return CROSS % (size, size, color)


# ---------------------------------------------------------------- beats and timing
def make_beats(piece):
    """Beats in speaking order, each tied to a station (the hook's, each shot's, the call to action's)."""
    m = piece["content"]["motion"]
    shots, pills = work.expand(m)
    beats, stations = [], []
    i = 0
    hook = m["hook"]
    b = video.Beat(i, "hook", hook["text"], hook.get("say"), hook["shot"])
    b.station, b.caption = 0, False
    beats.append(b); stations.append({"shot": hook["shot"], "beats": [b], "kind": "hook", "pill": pills.get("0")})
    for si, sh in enumerate(shots):
        st = {"shot": sh["shot"], "beats": [], "kind": "shot", "step": sh.get("step"), "pill": pills.get(str(si + 1))}
        for li, ln in enumerate(sh["lines"]):
            i += 1
            b = video.Beat(i, "s%d_%d" % (si + 1, li + 1), ln["text"], ln.get("say"), sh["shot"])
            b.station, b.caption = len(stations), True
            st["beats"].append(b); beats.append(b)
        stations.append(st)
    cta = m["cta"]
    i += 1
    b = video.Beat(i, "cta", cta["text"], cta.get("say"), cta["shot"])
    b.station, b.caption = len(stations), True
    beats.append(b); stations.append({"shot": cta["shot"], "beats": [b], "kind": "cta"})
    return beats, stations


def lay_out(beats):
    t = START
    for k, b in enumerate(beats):
        if not b.words:
            n = len(b.text.split())
            b.dur = max(2.0, 0.34 * n + 0.5)
            step = b.dur / max(1, n)
            b.words = [{"w": w, "t0": round(q * step, 3), "t1": round((q + 1) * step, 3)} for q, w in enumerate(b.text.split())]
        b.start = t
        nxt = beats[k + 1] if k + 1 < len(beats) else None
        t = b.end + (GAP_SAME if nxt is not None and nxt.station == b.station else GAP)
    end_at = beats[-1].end + 0.35
    return round(end_at, 3), round(end_at + END_HOLD, 2)


# ---------------------------------------------------------------- captions (two to four words a page)
def caption_pages(b, max_chars=19, max_words=4):
    words = video.caption_words(b)
    pages, cur, n = [], [], 0
    for w, t in words:
        if cur and (n + len(w) + 1 > max_chars or len(cur) >= max_words):
            pages.append(cur); cur, n = [], 0
        cur.append((w, t)); n += len(w) + 1
        if w[-1] in ",.;:?!" and len(cur) >= 2:
            pages.append(cur); cur, n = [], 0
    if cur:
        pages.append(cur)
    if len(pages) > 1 and len(pages[-1]) == 1 and len(pages[-1][0][0]) <= 6 and sum(len(w) + 1 for w, _ in pages[-2]) + len(pages[-1][0][0]) <= max_chars + 2:
        last = pages.pop(); pages[-1] = pages[-1] + last
    return pages


def captions(beats, total):
    html, js, shows = [], [], []
    for b in beats:
        if not b.caption:
            continue
        pages = caption_pages(b)
        for pi, page in enumerate(pages):
            cid = "c%d_%d" % (b.i, pi)
            spans = "".join('<span class="%s">%s</span> ' % (video.word_cls(w), esc(w)) for w, _ in page)
            html.append('<div class="cap" id="%s">%s</div>' % (cid, spans))
            show = page[0][1] - 0.08
            hide = (pages[pi + 1][0][1] - 0.1) if pi + 1 < len(pages) else b.end + 0.25
            shows.append([cid, show, hide])
            js.append("TL.fromTo('#%s',{opacity:0,y:26,scale:.94},{opacity:1,y:0,scale:1,duration:.18,ease:'back.out(2)'},%.3f);" % (cid, show))
            for k, (w, t) in enumerate(page):
                js.append("TL.to('#%s span:nth-child(%d)',{opacity:1,duration:.1},%.3f);" % (cid, k + 1, max(show, t - 0.02)))
    shows.sort(key=lambda x: x[1])
    for k, (cid, show, hide) in enumerate(shows):
        if k + 1 < len(shows):
            hide = min(hide, shows[k + 1][1] - 0.1)
        js.append("TL.to('#%s',{opacity:0,duration:.07},%.3f);" % (cid, max(show + 0.25, hide)))
    return "".join(html), js


# ---------------------------------------------------------------- shared parts
def title(o, text, step=None, top=392, size=80):
    disc = '<div class="sdisc">%d</div>' % step if step else ""
    o.h('<div class="stitle" style="top:%dpx">%s<h2 style="font-size:%dpx">%s</h2></div>' % (top, disc, size, text))


def stamp(o, sid, cls, text, left, top, t, rot=-8, size=60):
    o.h('<div class="stamp %s" style="left:%dpx;top:%dpx;font-size:%dpx;transform:rotate(%ddeg)">%s</div>' % (cls, left, top, size, rot, esc(text)))
    o.j("gsap.set('#%s .%s',{opacity:0,scale:2.4});", sid, cls)
    o.j("TL.to('#%s .%s',{opacity:1,scale:1,duration:.2,ease:'power4.in'},%.3f);", sid, cls, t - 0.2)
    o.j("TL.to('#%s .%s',{keyframes:{x:[0,-6,5,-3,0]},duration:.25},%.3f);", sid, cls, t)
    o.cue("impact", t - 0.02, 0.32)


def pop(o, sel, t, cue="tick", g=0.22, y=30):
    o.j("gsap.set('%s',{opacity:0,y:%d,scale:.86});", sel, y)
    o.j("TL.to('%s',{opacity:1,y:0,scale:1,duration:.42,ease:'back.out(1.8)'},%.3f);", sel, t)
    if cue:
        o.cue(cue, t, g)


def draw(o, sel, t, dur=0.7):
    """Draws an SVG path from nothing (stroke-dashoffset)."""
    o.j("(()=>{const p=document.querySelector('%s'); const L=p.getTotalLength(); gsap.set(p,{strokeDasharray:L,strokeDashoffset:L,opacity:0});"
        "TL.set(p,{opacity:1},%.3f); TL.to(p,{strokeDashoffset:0,duration:%.2f,ease:'power2.inOut'},%.3f);})();", sel, t, dur, t)


def bob(o, sel, t0, dur):
    n = max(1, int(dur / 1.5))
    o.j("TL.fromTo('%s',{y:0,rotation:0},{y:-12,rotation:1.2,duration:.75,ease:'sine.inOut',yoyo:true,repeat:%d,immediateRender:false},%.3f);", sel, n * 2 - 1, t0)


def count(o, sel, t, to, pre="", suf="", dur=1.0, dec=0):
    o.j("(()=>{const el=document.querySelector('%s'); const fin=el.textContent; const v={n:0}; el.textContent='%s0%s';"
        "TL.to(v,{n:%s,duration:%.2f,ease:'power2.out',onUpdate:()=>{el.textContent=(v.n>=%s-1e-9)?fin:'%s'+Math.round(v.n).toLocaleString('en-US')+'%s'}},%.3f);"
        "TL.set(el,{},%.3f);})();", sel, pre, suf, to, dur, to, pre, suf, t, t)


def typewrite(o, sel, text, t, cps=16):
    """Types text into an element letter by letter from time t."""
    spans = "".join('<span class="tw">%s</span>' % esc(ch) for ch in text)
    o.j("(()=>{const el=document.querySelector('%s'); el.innerHTML=%r; el.querySelectorAll('.tw').forEach((s,k)=>{gsap.set(s,{opacity:0});"
        "TL.to(s,{opacity:1,duration:.01},%.3f+k/%d);});})();", sel, spans, t, cps)


# ---------------------------------------------------------------- shots
def sh_versus(o, sid, bs, sp, arrive, step):
    """Hook for a changed figure: the new figure huge, the old one struck through."""
    b = bs[0]
    o.h('<div class="stitle" style="top:400px"><h1>%s</h1></div>' % sp["title"])
    o.h('<div class="card vs" style="left:90px;top:860px;width:900px;height:430px"><div class="vslab">%s</div>'
        '<div class="vsnew"><i class="mk"></i><b>%s</b></div><div class="vsold">not <span class="old">%s'
        '<svg viewBox="0 0 300 90" preserveAspectRatio="none"><path class="strk" d="M6 62 C80 40 200 30 294 22" stroke="#C23A2B" stroke-width="12" fill="none" stroke-linecap="round"/></svg></span></div></div>'
        % (esc(sp["label"]), esc(sp["new"]), esc(sp["old"])))
    o.j("gsap.set('#%s .mk',{scaleX:0,transformOrigin:'0%% 50%%'}); TL.to('#%s .mk',{scaleX:1,duration:.45,ease:'power3.out'},.08);", sid, sid)
    o.j("TL.fromTo('#%s .vs',{rotation:-1.5},{rotation:-.5,duration:%.2f,ease:'sine.inOut'},0);", sid, b.dur + 0.4)
    t_new, t_old = at(b, sp.get("say_new"), 0.45), min(at(b, sp.get("say_old"), 0.8), 0.55)
    if sp.get("who"):
        o.h('<div class="chr vwho" style="left:%dpx;top:%dpx">%s</div>' % (sp.get("who_left", 600), sp.get("who_top", 1260), sprite(sp["who"], sp.get("expr", "thinking"), sp.get("who_h", 560))))
        bob(o, "#%s .vwho" % sid, 0.05, b.dur + 1)
    o.j("TL.to('#%s .vsnew b',{keyframes:{scale:[1,1.08,1]},duration:.5,ease:'power1.inOut'},%.3f);", sid, t_new - 0.1)
    o.cue("tick", t_new - 0.1, 0.2)
    draw(o, "#%s .strk" % sid, t_old - 0.05, 0.4)
    o.cue("impact", t_old + 0.2, 0.28)
    o.cue("impact", 0.05, 0.22)


def sh_form(o, sid, bs, sp, arrive, step):
    """A drawn form: a field fills in, a ring is drawn around it, a stamp lands."""
    b = bs[0]
    rows = "".join('<div class="frow"><span>%s</span><i></i></div>' % esc(r) for r in sp.get("rows", []))
    o.h('<div class="paper form" style="left:110px;top:430px;width:860px;height:840px">'
        '<div class="fhead"><div class="ftitle">%s</div><div class="ftag">%s</div></div><div class="fsub">%s</div>%s'
        '<div class="fbox"><span class="fn">1</span><span class="fl">%s</span><b class="fv"></b>'
        '<svg class="ring" viewBox="0 0 800 140" preserveAspectRatio="none"><path d="M30 70 C30 20 160 8 400 10 C640 12 780 22 780 70 C780 120 640 132 400 130 C150 128 20 118 34 62" fill="none" stroke="#FFD84D" stroke-width="10" stroke-linecap="round"/></svg></div>'
        '<div class="flines"><i></i><i></i><i style="width:60%%"></i></div></div>'
        % (esc(sp["form"]), esc(sp.get("tag", "")), esc(sp.get("sub", "")), rows, esc(sp["field"])))
    o.j("gsap.set('#%s .form',{rotation:-2.5,y:40}); TL.to('#%s .form',{y:0,rotation:-1.5,duration:.9,ease:'power3.out'},%.3f);", sid, sid, arrive - 0.5)
    t_fill = at(b, sp.get("at_fill"), 0.45)
    typewrite(o, "#%s .fv" % sid, sp["value"], t_fill - 0.15, 18)
    draw(o, "#%s .ring path" % sid, t_fill + 0.25, 0.55)
    o.cue("tick", t_fill - 0.1, 0.2)
    if sp.get("stamp"):
        stamp(o, sid, "st1", sp["stamp"], 470, 1100, at(b, sp.get("at_stamp"), 0.8), -9, 54)


def sh_castpay(o, sid, bs, sp, arrive, step):
    """Two characters, pay moving from one to the other; who counts and who does not."""
    b = bs[0]
    o.h('<div class="chr c1" style="left:40px;top:470px">%s</div><div class="chr c2" style="left:590px;top:450px">%s</div>'
        % (sprite(sp["left"], sp.get("left_expr", "happy"), 600), sprite(sp["right"], sp.get("right_expr", "happy"), 620)))
    o.h('<svg class="payline" style="position:absolute;left:300px;top:620px" width="360" height="160" viewBox="0 0 360 160"><path d="M10 120 C120 10 240 10 350 110" fill="none" stroke="#15191F" stroke-width="5" stroke-dasharray="14 14" stroke-linecap="round"/></svg>')
    o.h('<div class="cheque"><span class="mark">FD</span><b>%s</b></div>' % esc(sp["pay"]))
    o.h('<div class="chips2"><div class="chip2 no">%s<span>%s</span></div><div class="chip2 yes">%s<span>%s</span></div></div>'
        % (cross(40), esc(sp["no"]), check(40), esc(sp["yes"])))
    t_pay = at(b, sp.get("at_pay"), 0.2)
    o.j("gsap.set('#%s .cheque',{x:0,y:0,rotation:-8,opacity:0});", sid)
    o.j("TL.to('#%s .cheque',{opacity:1,duration:.2},%.3f);", sid, t_pay - 0.2)
    o.j("TL.to('#%s .cheque',{keyframes:{x:[0,170,330],y:[0,-90,250],rotation:[-8,4,12]},duration:1.1,ease:'power1.inOut'},%.3f);", sid, t_pay - 0.1)
    o.cue("whoosh", t_pay - 0.1, 0.15)
    pop(o, "#%s .chip2.no" % sid, at(b, sp.get("at_no"), 0.55))
    o.j("gsap.set('#%s .chip2.no span',{'--s':0}); TL.to('#%s .chip2.no span',{'--s':1,duration:.35,ease:'power2.out'},%.3f);", sid, sid, at(b, sp.get("at_no"), 0.55) + 0.35)
    pop(o, "#%s .chip2.yes" % sid, at(b, sp.get("at_yes"), 0.85), "chime", 0.18)
    bob(o, "#%s .c2" % sid, arrive, b.dur)


def sh_bars(o, sid, bs, sp, arrive, step):
    """Two bars side by side: the old figure small, the new one tall."""
    b = bs[0]
    a, z = sp["items"]
    o.h('<div class="card bars" style="left:90px;top:440px;width:900px;height:820px"><div class="bbase"></div>'
        '<div class="bcol c1" style="left:110px"><div class="bval">%s</div><div class="bar b3" style="height:170px"></div><div class="blab">%s</div></div>'
        '<div class="bcol c2" style="left:500px"><div class="bval">%s</div><div class="bar b1" style="height:470px"></div><div class="blab">%s</div></div></div>'
        % (esc(a["value"]), esc(a["label"]), esc(z["value"]), esc(z["label"])))
    o.j("gsap.set('#%s .bar',{scaleY:0,transformOrigin:'50%% 100%%'}); gsap.set('#%s .bval',{opacity:0,y:20});", sid, sid)
    o.j("TL.to('#%s .c2 .bar',{scaleY:1,duration:.7,ease:'power3.out'},%.3f); TL.to('#%s .c2 .bval',{opacity:1,y:0,duration:.4},%.3f);", sid, arrive - 0.3, sid, arrive + 0.2)
    t = at(b, sp.get("at_old"), 0.4)
    o.j("TL.to('#%s .c1 .bar',{scaleY:1,duration:.6,ease:'back.out(1.6)'},%.3f); TL.to('#%s .c1 .bval',{opacity:1,y:0,duration:.4},%.3f);", sid, t - 0.2, sid, t)
    o.cue("tick", t, 0.24)


def calendar_html(cls, month, day, weekday, label=None, big=False):
    lab = '<div class="clab">%s</div>' % esc(label) if label else ""
    return ('<div class="calw %s">%s<div class="cal2%s"><div class="m">%s</div><div class="d">%s</div><div class="s">%s</div></div></div>'
            % (cls, lab, " big" if big else "", esc(month), esc(day), esc(weekday)))


def sh_calendar(o, sid, bs, sp, arrive, step):
    """Pages flip to the date, a ring is drawn round the day, and who it goes to comes in."""
    b = bs[0]
    flips = "".join('<div class="flip f%d"><div class="m">%s</div><div class="d">%s</div><div class="s">&nbsp;</div></div>' % (k, esc(m), esc(d) or "&nbsp;") for k, (m, d) in enumerate(sp.get("flips", [])))
    o.h('<div class="chr dotc" style="left:20px;top:640px">%s</div>' % sprite(sp.get("who", "dot"), sp.get("expr", "surprised"), 560))
    o.h('<div class="calbigw" style="left:500px;top:470px">%s%s'
        '<svg class="cring" viewBox="0 0 300 220"><path d="M60 120 C50 50 140 22 210 40 C280 60 270 170 190 190 C110 210 50 170 70 100" fill="none" stroke="#C23A2B" stroke-width="9" stroke-linecap="round"/></svg></div>'
        % (calendar_html("main", sp["month"], sp["day"], sp["weekday"], big=True), flips))
    chips = "".join('<div class="tochip t%d">%s<span>%s</span></div>' % (k, ic("arrow", 40, "#0B7955", 3), esc(c)) for k, c in enumerate(sp.get("to", [])))
    o.h('<div class="tochips" style="left:500px;top:1050px">%s</div>' % chips)
    t_date = at(b, sp.get("at_date"), 0.65)
    n = len(sp.get("flips", []))
    o.j("gsap.set('#%s .flip',{transformOrigin:'50%% 0%%'});", sid)
    for k in range(n):
        o.j("TL.to('#%s .f%d',{rotationX:-100,y:40,opacity:0,duration:.32,ease:'power2.in'},%.3f);", sid, n - 1 - k, t_date - 0.75 + k * 0.22)
        o.cue("tick", t_date - 0.75 + k * 0.22, 0.14)
    draw(o, "#%s .cring path" % sid, t_date + 0.1, 0.6)
    for k, w in enumerate(sp.get("at_to", [])):
        pop(o, "#%s .t%d" % (sid, k), at(b, w, 0.7 + 0.1 * k), "tick", 0.2, 0)
    bob(o, "#%s .dotc" % sid, arrive, b.dur)


def end_card_html(kind, keyword, cta_pill, offer, disclaimer):
    off = '<div class="eoffer">%s</div>' % esc(offer) if offer else ""
    fine = '<div class="efine">%s</div>' % DISCLAIMER if disclaimer else ""
    return ('<div class="endc" id="endc"><div class="ering"><img src="%s"></div><div class="ename">Muhammad Talha</div>'
            '<div class="ebrand"><span class="mark">FD</span>Finance Department</div>%s<div class="ecta">%s</div><div class="esite">%s</div>%s</div>'
            % (photo_uri("talha_cut"), off, cta_pill, SITE, fine))


def sh_follow(o, sid, bs, sp, arrive, step):
    """Top of funnel call to action: the follow button is pressed."""
    b = bs[0]
    o.h('<div class="stitle" style="top:430px"><h2 style="font-size:84px">%s</h2></div>' % sp["title"])
    o.h('<div class="card prof" style="left:90px;top:900px;width:900px;height:250px"><div class="pava"><img src="%s"></div>'
        '<div class="pwho"><b>%s</b><span>Finance Department</span></div><div class="fbtn"><span class="f1">Follow</span><span class="f2">Following %s</span></div>'
        '<div class="tap"></div></div>' % (photo_uri("talha_cut"), esc(sp["handle"]), check(30, "#15191F")))
    t = at(b, None, 0.55)
    o.j("gsap.set('#%s .f2',{opacity:0}); gsap.set('#%s .tap',{scale:0,opacity:.6});", sid, sid)
    o.j("TL.to('#%s .tap',{scale:1.6,opacity:0,duration:.5,ease:'power2.out'},%.3f);", sid, t)
    o.j("TL.to('#%s .fbtn',{keyframes:{scale:[1,.9,1.06,1]},duration:.45},%.3f);", sid, t - 0.05)
    o.j("TL.to('#%s .f1',{opacity:0,duration:.1},%.3f); TL.to('#%s .f2',{opacity:1,duration:.1},%.3f); TL.to('#%s .fbtn',{backgroundColor:'#FFFFFF',duration:.2},%.3f);",
        sid, t + 0.12, sid, t + 0.12, sid, t + 0.12)
    o.cue("tick", t, 0.3)
    o.cue("chime", t + 0.15, 0.18)


def sh_person(o, sid, bs, sp, arrive, step):
    """Hook with a person: the question as the title, the character and what the question is about."""
    b = bs[0]
    o.h('<div class="stitle" style="top:400px"><h1 style="font-size:%dpx">%s</h1></div>' % (sp.get("size", 90), sp["title"]))
    o.h('<div class="card llc" style="left:90px;top:%dpx;width:430px;height:360px"><div class="ico big2">%s</div><div class="llct">%s</div><div class="llcs">%s</div></div>'
        % (sp.get("card_top", 930), ic(sp.get("icon", "building"), 76), esc(sp["card"]), esc(sp.get("card_sub", ""))))
    o.h('<div class="chr hc" style="left:560px;top:%dpx">%s</div>' % (sp.get("who_top", 800), sprite(sp["who"], sp.get("expr", "thinking"), 600)))
    if sp.get("tag"):
        o.h('<div class="ytag" style="left:90px;top:%dpx">%s</div>' % (sp.get("card_top", 930) + 400, esc(sp["tag"])))
        o.j("gsap.set('#%s .ytag',{rotation:-3});", sid)
    bob(o, "#%s .hc" % sid, 0.05, b.dur + 1)
    o.j("TL.fromTo('#%s .llc',{rotation:-2},{rotation:1,duration:%.2f,ease:'sine.inOut'},0);", sid, b.dur + 0.6)
    o.cue("impact", 0.05, 0.2)


def sh_checklist(o, sid, bs, sp, arrive, step):
    b = bs[0]
    title(o, sp["title"], step)
    rows = "".join('<div class="ckr r%d"><div class="box">%s</div><div class="ckt">%s</div></div>' % (k, check(48), esc(r)) for k, r in enumerate(sp["rows"]))
    o.h('<div class="card ck" style="left:70px;top:560px;width:940px">%s</div>' % rows)
    if sp.get("result"):
        o.h('<div class="ytag res" style="left:80px;top:%dpx">%s %s</div>' % (sp.get("result_top", 1180), ic("arrow", 40, "#15191F", 3.2), esc(sp["result"])))
    o.j("gsap.set('#%s .box svg',{scale:0,opacity:0});", sid)
    for k, w in enumerate(sp["at"]):
        t = at(b, w, 0.25 + 0.25 * k) if w != "start" else arrive
        o.j("TL.to('#%s .r%d .box svg',{scale:1,opacity:1,duration:.3,ease:'back.out(2.2)'},%.3f);", sid, k, t)
        o.j("TL.to('#%s .r%d',{backgroundColor:'rgba(11,121,85,.09)',duration:.3},%.3f);", sid, k, t)
        o.cue("tick", t, 0.26)
    if sp.get("result"):
        pop(o, "#%s .res" % sid, at(b, sp.get("at_result"), 0.92), "chime", 0.16)


def doc_html(cls, name, sub, left, top, rot, w=440, h=580):
    return ('<div class="paper doc %s" style="left:%dpx;top:%dpx;width:%dpx;height:%dpx;transform:rotate(%sdeg)"><div class="dname">%s</div><div class="dsub">%s</div>'
            '<div class="dl"><i></i><i></i><i style="width:70%%"></i><i></i><i style="width:55%%"></i></div></div>' % (cls, left, top, w, h, rot, esc(name), esc(sub)))


def sh_docpair(o, sid, bs, sp, arrive, step):
    b = bs[0]
    title(o, sp["title"], step)
    o.h(doc_html("da", sp["left"], sp.get("left_sub", ""), 60, 560, -3))
    o.h(doc_html("db", sp["right"], sp.get("right_sub", ""), 580, 580, 2.5))
    o.h('<div class="plus">+</div>')
    o.h('<div class="note" style="left:470px;top:1180px">%s</div>'
        '<svg class="narrow" style="position:absolute;left:770px;top:1100px" width="140" height="110" viewBox="0 0 140 110"><path d="M10 100 C70 95 110 70 120 12 M104 28 L120 10 L132 32" fill="none" stroke="#0B7955" stroke-width="5" stroke-linecap="round" stroke-linejoin="round"/></svg>'
        % esc(sp["note"]))
    o.j("gsap.set('#%s .da',{x:-60,opacity:0}); gsap.set('#%s .db',{x:60,opacity:0}); gsap.set('#%s .plus',{scale:0});", sid, sid, sid)
    t1, t2 = at(b, sp.get("at_left"), 0.15), at(b, sp.get("at_right"), 0.45)
    o.j("TL.to('#%s .da',{x:0,opacity:1,duration:.5,ease:'power3.out'},%.3f);", sid, t1 - 0.2)
    o.j("TL.to('#%s .plus',{scale:1,duration:.35,ease:'back.out(2)'},%.3f);", sid, t2 - 0.3)
    o.j("TL.to('#%s .db',{x:0,opacity:1,duration:.5,ease:'power3.out'},%.3f);", sid, t2 - 0.2)
    o.cue("tick", t1 - 0.2, 0.2); o.cue("tick", t2 - 0.2, 0.2)
    t3 = at(b, sp.get("at_note"), 0.8)
    o.j("gsap.set('#%s .note',{opacity:0,y:16});TL.to('#%s .note',{opacity:1,y:0,duration:.4},%.3f);", sid, sid, t3 - 0.1)
    draw(o, "#%s .narrow path" % sid, t3, 0.5)
    t4 = b.end + 0.05
    o.j("TL.to('#%s .da',{x:250,y:30,rotation:1,duration:.55,ease:'power3.inOut'},%.3f); TL.to('#%s .plus',{scale:0,duration:.25},%.3f);", sid, t4, sid, t4)


def sh_fax(o, sid, bs, sp, arrive, step):
    b = bs[0]
    title(o, sp["title"], step)
    o.h('<div class="rtag" style="left:80px;top:560px">%s<span>%s</span></div>' % (cross(38), esc(sp["no"])))
    o.h('<div class="fax" style="left:40px;top:690px"><div class="fslot"></div><div class="fpaper"><i></i><i></i><i></i></div><div class="fbody"><div class="flcd"></div>'
        '<div class="fkeys">%s</div></div><div class="flab">%s</div></div>' % ("<i></i>" * 12, esc(sp["fax_label"])))
    o.h('<div class="ordisc" style="left:572px;top:930px">or</div>')
    o.h('<div class="env" style="left:640px;top:800px"><div class="eflap"></div><div class="eaddr"><b>%s</b><span>%s</span></div><div class="emark">%s</div></div>'
        % (esc(sp["mail_to"]), esc(sp["mail_where"]), ic("mail", 46, "#C23A2B", 3)))
    t_no = at(b, sp.get("at_no"), 0.25)
    pop(o, "#%s .rtag" % sid, t_no - 0.1, "impact", 0.24)
    t_fax = at(b, sp.get("at_fax"), 0.45)
    typewrite(o, "#%s .flcd" % sid, sp["number"], t_fax + 0.15, 9)
    o.j("gsap.set('#%s .fpaper',{y:-170,opacity:0}); TL.to('#%s .fpaper',{opacity:1,duration:.2},%.3f); TL.to('#%s .fpaper',{y:40,duration:1.4,ease:'power1.inOut'},%.3f);",
        sid, sid, t_fax - 0.2, sid, t_fax)
    o.cue("riser", t_fax, 0.12)
    t_mail = at(b, sp.get("at_mail"), 0.75)
    pop(o, "#%s .ordisc" % sid, t_mail - 0.4, None)
    o.j("gsap.set('#%s .env',{opacity:0,x:80,rotation:8}); TL.to('#%s .env',{opacity:1,x:0,rotation:-3,duration:.55,ease:'back.out(1.6)'},%.3f);", sid, sid, t_mail - 0.1)
    o.cue("whoosh", t_mail - 0.1, 0.14)


def sh_deadline(o, sid, bs, sp, arrive, step):
    title(o, sp["title"], step)
    a, z = sp["due"], sp["ext"]
    o.h('<div class="calhold" style="left:70px;top:610px">%s</div>' % calendar_html("ca", a["month"], a["day"], a["weekday"], a.get("label")))
    o.h('<div class="calhold cb" style="left:600px;top:610px">%s</div>' % calendar_html("cb", z["month"], z["day"], z["weekday"], z.get("label")))
    o.h('<svg class="darrow" style="position:absolute;left:390px;top:760px" width="230" height="120" viewBox="0 0 230 120"><path d="M10 90 C70 10 160 10 215 70 M196 52 L216 72 L192 84" fill="none" stroke="#15191F" stroke-width="6" stroke-linecap="round" stroke-linejoin="round"/></svg>')
    o.h('<div class="ytag ext" style="left:330px;top:1130px">%s</div>' % esc(sp["ext_tag"]))
    o.h('<div class="chr dotc" style="left:40px;top:1080px">%s</div>' % sprite("dot", "surprised", 300))
    b1 = bs[0]; b2 = bs[1] if len(bs) > 1 else bs[0]
    o.j("gsap.set('#%s .cb',{opacity:0,x:60,rotation:6});", sid)
    t_due = at(b1, sp.get("at_due"), 0.6)
    o.j("TL.to('#%s .ca .cal2',{keyframes:{scale:[1,1.08,1]},duration:.45},%.3f);", sid, t_due - 0.1)
    o.cue("impact", t_due - 0.05, 0.2)
    t_ext = at(b2, sp.get("at_ext"), 0.4)
    draw(o, "#%s .darrow path" % sid, t_ext - 0.2, 0.5)
    o.j("TL.to('#%s .cb',{opacity:1,x:0,rotation:2,duration:.55,ease:'back.out(1.6)'},%.3f);", sid, at(b2, sp.get("at_ext_date"), 0.75) - 0.15)
    o.cue("whoosh", t_ext - 0.2, 0.14)
    pop(o, "#%s .ext" % sid, t_ext, "tick", 0.2)
    bob(o, "#%s .dotc" % sid, b1.start, b1.dur + b2.dur)


def sh_penalty(o, sid, bs, sp, arrive, step):
    b = bs[0]
    o.h('<div class="redv"></div>')
    o.h('<div class="pen" style="top:470px"><div class="plab">%s %s</div><div class="pbig">%s</div><div class="psub">%s</div></div>'
        % (ic("warning", 48, "#C23A2B", 3), esc(sp["label"]), esc(sp["value"]), esc(sp["sub"])))
    o.h('<div class="chr pchr" style="left:%dpx;top:900px">%s</div>' % (sp.get("who_left", 600), sprite(sp.get("who", "dot"), sp.get("expr", "surprised"), sp.get("who_h", 470))))
    if sp.get("doc"):
        o.h(doc_html("pdoc", sp["doc"], "", 90, 960, -4, 420, 360))
        stamp(o, sid, "pst", sp["stamp"], 110, 1150, at(b, sp.get("at_stamp"), 0.3), -10, 44)
    t = at(b, sp.get("at_value"), 0.6)
    o.j("gsap.set('#%s .redv',{opacity:0}); TL.to('#%s .redv',{opacity:1,duration:.5},%.3f);", sid, sid, t - 0.3)
    count(o, "#%s .pbig" % sid, t - 0.25, sp["to"], "$", "", 0.9)
    o.cue("boom", t + 0.55, 0.3)
    o.j("TL.to('#%s .pbig',{keyframes:{scale:[1,1.07,1]},duration:.4},%.3f);", sid, t + 0.6)
    bob(o, "#%s .pchr" % sid, arrive, b.dur)


def sh_comment(o, sid, bs, sp, arrive, step):
    """Middle of funnel call to action: the keyword is typed as a comment and the free tool arrives by DM."""
    b = bs[0]
    o.h('<div class="stitle" style="top:420px"><h2 style="font-size:80px">%s</h2></div>' % sp["title"])
    o.h('<div class="card cbox" style="left:90px;top:760px;width:900px;height:150px"><div class="cava">%s</div><div class="cin"><span class="ctyped"></span><i class="caret"></i></div>'
        '<div class="csend">%s</div></div>' % (ic("person", 44, "#59606C", 2.6), ic("send", 44, "#0B7955", 3)))
    o.h('<div class="dm" style="left:90px;top:960px;width:900px"><div class="dmh"><span class="mark">FD</span><b>Finance Department</b><span>sent you a message</span></div>'
        '<div class="dmb">%s</div><div class="dml">%s %s</div></div>' % (esc(sp["dm"]), ic("arrow", 34, "#0B7955", 3), esc(sp["link"])))
    t_type = at(b, sp.get("at_type"), 0.15)
    typewrite(o, "#%s .ctyped" % sid, sp["keyword"], t_type, 12)
    o.j("TL.to('#%s .csend',{keyframes:{scale:[1,.85,1.1,1]},duration:.4},%.3f);", sid, t_type + len(sp["keyword"]) / 12 + 0.1)
    o.cue("tick", t_type + len(sp["keyword"]) / 12 + 0.1, 0.24)
    t_dm = at(b, sp.get("at_dm"), 0.6)
    o.j("gsap.set('#%s .dm',{opacity:0,y:80}); TL.to('#%s .dm',{opacity:1,y:0,duration:.55,ease:'back.out(1.5)'},%.3f);", sid, sid, t_dm)
    o.cue("chime", t_dm + 0.1, 0.2)


def sh_report(o, sid, bs, sp, arrive, step):
    """Hook for an offer: its name as the title and what it delivers as an object."""
    b = bs[0]
    o.h('<div class="stitle" style="top:400px"><h1 style="font-size:%dpx">%s</h1></div>' % (sp.get("size", 104), sp["title"]))
    o.h('<div class="paper rep" style="left:170px;top:820px;width:700px;height:500px"><div class="rhead"><span class="mark">FD</span>Finance Department</div>'
        '<div class="rname">%s</div><div class="dl"><i></i><i></i><i style="width:70%%"></i><i></i></div><div class="rtab">%s</div></div>' % (esc(sp["doc"]), esc(sp["tab"])))
    o.j("TL.fromTo('#%s .rep',{rotation:-3,y:0},{rotation:-1,y:-14,duration:%.2f,ease:'sine.inOut'},0);", sid, b.dur + 0.8)
    if sp.get("who"):
        o.h('<div class="chr rwho" style="left:%dpx;top:%dpx">%s</div>' % (sp.get("who_left", 40), sp.get("who_top", 1240), sprite(sp["who"], sp.get("expr", "thinking"), sp.get("who_h", 540))))
        bob(o, "#%s .rwho" % sid, 0.05, b.dur + 1)
    o.j("TL.to('#%s .rtab',{keyframes:{x:[0,16,0]},duration:.6,ease:'power1.inOut'},.35);", sid)
    o.cue("impact", 0.05, 0.2)


def sh_days(o, sid, bs, sp, arrive, step):
    b = bs[0]
    tiles = "".join('<div class="day d%d"><span>Day</span><b>%d</b></div>' % (k, k + 1) for k in range(sp.get("days", 5)))
    o.h('<div class="days" style="left:80px;top:470px">%s</div>' % tiles)
    o.h('<div class="paper rep2" style="left:150px;top:700px;width:780px;height:540px"><div class="pg p0"><div class="rname">%s</div><div class="dl"><i></i><i></i><i style="width:70%%"></i><i></i></div></div>'
        '<div class="pg p1"><div class="mas">%s<b>%s</b></div><div class="dl"><i></i><i style="width:80%%"></i><i></i></div></div></div>' % (esc(sp["doc"]), ic("dollar", 64, "#C23A2B", 3), esc(sp["page"])))
    n = sp.get("days", 5)
    t0, t1 = arrive, b.end - 0.2
    for k in range(n):
        t = t0 + (t1 - t0) * (k + 0.5) / n
        o.j("TL.to('#%s .d%d',{backgroundColor:'#0B7955',color:'#FFFFFF',duration:.2},%.3f); TL.to('#%s .d%d',{keyframes:{scale:[1,1.12,1]},duration:.3},%.3f);", sid, k, t, sid, k, t)
        o.cue("tick", t, 0.16)
    t_page = at(b, sp.get("at_page"), 0.45)
    o.j("gsap.set('#%s .p1',{opacity:0,rotationY:-70,transformOrigin:'0%% 50%%'}); TL.to('#%s .p1',{opacity:1,rotationY:0,duration:.6,ease:'power3.out'},%.3f);", sid, sid, t_page - 0.2)
    o.cue("whoosh", t_page - 0.2, 0.12)


def sh_price(o, sid, bs, sp, arrive, step):
    b = bs[0]
    seats = "".join('<i class="seat s%d">%s</i>' % (k, ic("person", 44, "#15191F", 2.8)) for k in range(sp.get("seats", 5)))
    o.h('<div class="card ptag pa" style="left:80px;top:470px;width:600px;height:500px"><div class="pval">%s</div><div class="plab2">%s</div><div class="seats">%s</div></div>'
        % (esc(sp["first"]), esc(sp["first_label"]), seats))
    o.h('<div class="card ptag pb" style="left:500px;top:900px;width:500px;height:330px"><div class="pthen">%s</div><div class="pval2">%s</div></div>' % (esc(sp["then_label"]), esc(sp["then"])))
    o.j("gsap.set('#%s .pa',{rotation:-3}); gsap.set('#%s .pb',{opacity:0,rotation:14,x:80});", sid, sid)
    t_first = at(b, sp.get("at_first"), 0.15)
    o.j("TL.to('#%s .pval',{keyframes:{scale:[1,1.08,1]},duration:.45},%.3f);", sid, t_first)
    t_seats = at(b, sp.get("at_seats"), 0.4)
    for k in range(sp.get("seats", 5)):
        o.j("TL.to('#%s .s%d',{backgroundColor:'#FFD84D',duration:.15},%.3f);", sid, k, t_seats + k * 0.12)
        o.cue("tick", t_seats + k * 0.12, 0.12)
    t_then = at(b, sp.get("at_then"), 0.75)
    o.j("TL.to('#%s .pb',{opacity:1,rotation:3,x:0,duration:.6,ease:'back.out(1.7)'},%.3f);", sid, t_then - 0.15)
    o.cue("whoosh", t_then - 0.15, 0.14)


def sh_proof(o, sid, bs, sp, arrive, step):
    a, z = sp["items"]
    o.h('<div class="card prf pa" style="left:80px;top:470px;width:920px;height:360px"><div class="pnum">%s</div><div class="ptx">%s</div></div>' % (esc(a["value"]), esc(a["label"])))
    o.h('<div class="card prf pb" style="left:80px;top:880px;width:920px;height:360px"><div class="pnum2"><small>%s</small>%s</div><div class="ptx">%s</div></div>'
        % (esc(z.get("pre", "")), esc(z["value"]), esc(z["label"])))
    b1 = bs[0]; b2 = bs[1] if len(bs) > 1 else bs[0]
    t1 = at(b1, a.get("at"), 0.35)
    count(o, "#%s .pnum" % sid, t1 - 0.3, a["to"], "", a.get("suf", ""), 0.9)
    o.cue("tick", t1 + 0.6, 0.2)
    o.j("gsap.set('#%s .pb',{opacity:0,y:60});", sid)
    t2 = at(b2, z.get("at"), 0.25)
    o.j("TL.to('#%s .pb',{opacity:1,y:0,duration:.5,ease:'back.out(1.5)'},%.3f);", sid, b2.start - 0.15)
    o.cue("whoosh", b2.start - 0.15, 0.12)
    o.j("TL.to('#%s .pnum2',{keyframes:{scale:[1,1.08,1]},duration:.4},%.3f);", sid, t2)


def sh_nofee(o, sid, bs, sp, arrive, step):
    b = bs[0]
    nos = "".join('<div class="nochip n%d">%s<span>%s</span></div>' % (k, cross(40), esc(x)) for k, x in enumerate(sp["no"]))
    o.h('<div class="nos" style="left:80px;top:470px">%s</div>' % nos)
    o.h('<div class="card yes2" style="left:80px;top:830px;width:560px;height:400px"><div class="seal">%s</div><div class="yt">%s</div></div>' % (check(56, "#FFFFFF"), esc(sp["yes"])))
    o.h('<div class="chr samc" style="left:650px;top:700px">%s</div>' % sprite(sp.get("who", "sam"), "happy", 560))
    for k, w in enumerate(sp["at_no"]):
        t = at(b, w, 0.2 + 0.2 * k)
        pop(o, "#%s .n%d" % (sid, k), t - 0.15, None)
        o.j("gsap.set('#%s .n%d span',{'--s':0}); TL.to('#%s .n%d span',{'--s':1,duration:.3},%.3f);", sid, k, sid, k, t + 0.2)
        o.cue("impact", t + 0.2, 0.16)
    t_yes = at(b, sp.get("at_yes"), 0.75)
    o.j("gsap.set('#%s .yes2',{opacity:0,y:50}); TL.to('#%s .yes2',{opacity:1,y:0,duration:.5,ease:'back.out(1.6)'},%.3f);", sid, sid, t_yes - 0.2)
    o.cue("chime", t_yes, 0.16)
    bob(o, "#%s .samc" % sid, arrive, b.dur)


def sh_phone(o, sid, bs, sp, arrive, step):
    """Bottom of funnel call to action: the keyword goes out by DM and the offer's page comes back."""
    b = bs[0]
    o.h('<div class="phone" style="left:200px;top:400px"><div class="ph-top"><span class="mark">FD</span><b>Finance Department</b></div>'
        '<div class="bub out"><span class="kw"></span></div><div class="bub in"><div>%s</div><div class="plink">%s<span>%s</span></div></div>'
        '<div class="ph-in"><span>Message</span>%s</div></div>' % (esc(sp["reply"]), ic("arrow", 32, "#0B7955", 3), esc(sp["link"]).replace("/", "/<wbr>"), ic("send", 36, "#0B7955", 3)))
    t_type = at(b, sp.get("at_type"), 0.12)
    o.j("gsap.set('#%s .bub.out',{opacity:0,y:30,scale:.9}); TL.to('#%s .bub.out',{opacity:1,y:0,scale:1,duration:.35,ease:'back.out(2)'},%.3f);", sid, sid, t_type - 0.1)
    typewrite(o, "#%s .kw" % sid, sp["keyword"], t_type, 12)
    o.cue("tick", t_type + 0.2, 0.22)
    t_in = at(b, sp.get("at_reply"), 0.62)
    o.j("gsap.set('#%s .bub.in',{opacity:0,y:40}); TL.to('#%s .bub.in',{opacity:1,y:0,duration:.5,ease:'back.out(1.6)'},%.3f);", sid, sid, t_in)
    o.cue("chime", t_in + 0.1, 0.2)


SHOTS = {"versus": sh_versus, "form": sh_form, "castpay": sh_castpay, "bars": sh_bars, "calendar": sh_calendar, "follow": sh_follow,
         "person": sh_person, "checklist": sh_checklist, "docpair": sh_docpair, "fax": sh_fax, "deadline": sh_deadline, "penalty": sh_penalty,
         "comment": sh_comment, "report": sh_report, "days": sh_days, "price": sh_price, "proof": sh_proof, "nofee": sh_nofee, "phone": sh_phone}


# ---------------------------------------------------------------- desk props that pass by between shots
PROPS = [
    '<svg width="420" height="60" viewBox="0 0 420 60"><rect x="40" y="12" width="300" height="36" rx="6" fill="#FFD84D" stroke="#15191F" stroke-width="3"/>'
    '<rect x="340" y="12" width="44" height="36" rx="6" fill="#F4A8A0" stroke="#15191F" stroke-width="3"/><path d="M40 12 L4 30 L40 48z" fill="#F3E3C3" stroke="#15191F" stroke-width="3" stroke-linejoin="round"/>'
    '<path d="M4 30 L16 24 L16 36z" fill="#15191F"/></svg>',
    '<svg width="240" height="240" viewBox="0 0 240 240"><circle cx="120" cy="120" r="96" fill="none" stroke="rgba(120,80,40,.16)" stroke-width="16"/>'
    '<path d="M40 150 C60 200 170 214 206 140" fill="none" stroke="rgba(120,80,40,.12)" stroke-width="9"/></svg>',
    '<div class="sticky"></div>',
    '<svg width="200" height="80" viewBox="0 0 200 80"><path d="M30 20 h120 a20 20 0 0 1 0 40 h-110 a12 12 0 0 1 0 -24 h100" fill="none" stroke="#59606C" stroke-width="7" stroke-linecap="round"/></svg>',
    '<div class="tape"></div>',
]


def props(n_stations):
    """Two desk things in the gap between each pair of shots: never inside a shot, seen only while the camera moves."""
    out = []
    for i in range(n_stations - 1):
        x0, y0 = station_xy(i); x1, y1 = station_xy(i + 1)
        gl, gr = (x0 + 1080, x1) if x1 > x0 else (x1 + 1080, x0)
        cx = (gl + gr) / 2
        for k, (dy, rot) in enumerate([(y1 + 120, 74), (y0 + 1700, -12)]):
            p = PROPS[(i * 2 + k) % len(PROPS)]
            out.append('<div class="prop" style="left:%dpx;top:%dpx;transform:translateX(-50%%) rotate(%ddeg) scale(.8)">%s</div>' % (cx, dy, rot, p))
    return "".join(out)


# ---------------------------------------------------------------- the page
CSS = """
.slide{width:1080px;height:1920px;--mk:#FFD84D}
.bgl{display:none}
#push{position:absolute;left:540px;top:960px;width:0;height:0;z-index:3}
#cam{position:absolute;left:0;top:0;width:0;height:0}
#world{position:absolute;left:-540px;top:-960px;width:0;height:0}
.grid{position:absolute;left:-2600px;top:-2600px;background-image:radial-gradient(rgba(21,25,31,.075) 2.4px,transparent 2.6px);background-size:64px 64px}
.station{position:absolute;width:1080px;height:1920px}
.sin{position:absolute;inset:0}
.prop{position:absolute;opacity:.9}
.sticky{width:230px;height:230px;background:#FFE680;box-shadow:0 18px 30px rgba(70,55,30,.18);border-radius:4px}
.tape{width:280px;height:64px;background:rgba(160,220,195,.75);clip-path:polygon(0 0,100% 0,96% 50%,100% 100%,0 100%,4% 50%)}
.hud{position:absolute;left:0;top:0;width:1080px;height:1920px;z-index:25;pointer-events:none}
.hbrand{position:absolute;left:80px;top:226px;display:flex;align-items:center;gap:14px;font-family:'SS4';font-weight:600;font-size:27px;color:#15191F}
.hbrand .mark{width:46px;height:46px;font-size:25px;border-radius:8px}
.hpill{position:absolute;left:80px;top:292px;display:inline-flex;align-items:center;gap:12px;padding:12px 22px 11px 18px;border-radius:999px;border:3px solid #15191F;
 background:#FFFFFF;color:#15191F;font-weight:800;font-size:24px;letter-spacing:.14em;text-transform:uppercase;white-space:nowrap;opacity:0;box-shadow:4px 4px 0 #15191F}
.hpill i{width:14px;height:14px;border-radius:50%;background:#FFD84D;border:2.5px solid #15191F}
.hprog{position:absolute;left:470px;top:313px;display:flex;gap:10px}
.hprog span{position:relative;width:118px;height:16px;border-radius:9px;background:rgba(21,25,31,.12);overflow:hidden;border:2px solid rgba(21,25,31,.25)}
.hprog span b{position:absolute;left:0;top:0;bottom:0;width:100%;background:#0B7955;transform:scaleX(0);transform-origin:0 50%}
.stitle{position:absolute;left:70px;width:950px;display:flex;align-items:flex-start;gap:24px}
.stitle h1{font-family:'Fraunces';font-weight:700;font-size:100px;line-height:1.02;letter-spacing:-.03em;color:#15191F;text-wrap:balance}
.stitle h2{font-family:'Fraunces';font-weight:700;line-height:1.02;letter-spacing:-.025em;color:#15191F;text-wrap:balance}
.stitle mark,.mk2{background:linear-gradient(transparent 14%,#FFD84D 14%,#FFD84D 90%,transparent 90%);color:inherit;padding:0 .1em;border-radius:6px;-webkit-box-decoration-break:clone;box-decoration-break:clone}
.sdisc{width:104px;height:104px;border-radius:50%;flex:none;display:grid;place-items:center;background:#FFD84D;border:4px solid #15191F;box-shadow:5px 5px 0 #15191F;
 font-family:'Fraunces';font-weight:700;font-size:62px;color:#15191F;margin-top:2px}
.card{position:absolute;border-radius:34px;background:#FFFDF8;border:4px solid #15191F;box-shadow:12px 12px 0 #15191F}
.paper{position:absolute;border-radius:16px;background:linear-gradient(180deg,#FFFFFF,#F8F5EE);border:3px solid #15191F;box-shadow:12px 14px 0 rgba(21,25,31,.9)}
.chr{position:absolute}
.spr{display:block;filter:drop-shadow(0 26px 22px rgba(70,55,30,.22))}
.ytag{position:absolute;display:inline-flex;align-items:center;gap:14px;padding:18px 30px;border-radius:999px;background:#FFD84D;border:4px solid #15191F;box-shadow:6px 6px 0 #15191F;
 font-weight:800;font-size:38px;color:#15191F;white-space:nowrap}
.stamp{position:absolute;padding:10px 26px 8px;border:9px solid #C23A2B;border-radius:18px;color:#C23A2B;font-family:'Jakarta';font-weight:800;letter-spacing:.05em;
 white-space:nowrap;mix-blend-mode:multiply;background:rgba(255,255,255,.35);-webkit-mask-image:url(STAMP);mask-image:url(STAMP);-webkit-mask-size:100% 100%;mask-size:100% 100%}
/* versus */
.vs{display:flex;flex-direction:column;justify-content:center;padding:0 60px}
.vslab{font-weight:800;font-size:28px;letter-spacing:.16em;color:#0B7955;text-transform:uppercase}
.vsnew{position:relative;align-self:flex-start;margin-top:6px}
.vsnew b{position:relative;display:block;font-family:'Fraunces';font-weight:700;font-size:216px;line-height:1;letter-spacing:-.045em;color:#15191F}
.vsnew .mk{position:absolute;left:-10px;right:-14px;bottom:22px;height:80px;background:#FFD84D;border-radius:12px}
.vsold{font-family:'Jakarta';font-weight:800;font-size:66px;color:#59606C;margin-top:4px}
.vsold .old{position:relative;display:inline-block;color:#15191F}
.vsold svg{position:absolute;left:-14px;top:-6px;width:calc(100% + 28px);height:100%}
/* form */
.form{padding:44px 48px}
.fhead{display:flex;align-items:center;justify-content:space-between}
.ftitle{font-family:'Fraunces';font-weight:700;font-size:70px;color:#15191F;letter-spacing:-.02em}
.ftag{padding:10px 20px;border-radius:12px;background:#0B7955;color:#fff;font-weight:800;font-size:32px}
.fsub{font-weight:800;font-size:26px;letter-spacing:.14em;color:#59606C;text-transform:uppercase;margin-top:8px}
.frow{display:flex;align-items:center;gap:20px;height:78px;margin-top:22px;padding:0 24px;border:3px solid #D8D2C4;border-radius:14px;background:#fff}
.frow span{font-weight:800;font-size:24px;letter-spacing:.12em;color:#59606C;text-transform:uppercase}
.frow i{flex:1;height:16px;border-radius:8px;background:#E6E0D3}
.fbox{position:relative;display:flex;align-items:center;gap:18px;height:150px;margin-top:26px;padding:0 26px;border:4px solid #15191F;border-radius:16px;background:#FFFDF2}
.fn{width:58px;height:58px;border-radius:12px;background:#15191F;color:#fff;display:grid;place-items:center;font-weight:800;font-size:30px;flex:none}
.fl{font-weight:700;font-size:30px;color:#3F4652;line-height:1.15;width:270px}
.fv{margin-left:auto;font-family:'PlexMono';font-weight:400;font-size:64px;color:#15191F;white-space:nowrap}
.ring{position:absolute;left:-30px;top:-22px;width:calc(100% + 60px);height:calc(100% + 44px);overflow:visible}
.flines{margin-top:34px}.flines i,.dl i{display:block;height:16px;border-radius:8px;background:#E9E3D6;margin-top:18px}
/* characters, pay */
.cheque{position:absolute;left:250px;top:560px;display:flex;align-items:center;gap:14px;padding:22px 28px;border-radius:14px;background:#E8F6EE;border:4px solid #15191F;
 box-shadow:6px 6px 0 #15191F;font-weight:800;font-size:34px;color:#15191F;white-space:nowrap;z-index:2}
.cheque .mark{width:44px;height:44px;font-size:24px;border-radius:8px}
.chips2{position:absolute;left:80px;top:1130px;display:flex;gap:22px}
.chip2{display:inline-flex;align-items:center;gap:14px;padding:18px 26px;border-radius:999px;border:4px solid #15191F;background:#fff;font-weight:800;font-size:38px;color:#15191F;box-shadow:6px 6px 0 #15191F;white-space:nowrap}
.chip2.yes{background:#DDF1E7}
.chip2.no span{position:relative}
.chip2.no span::after{content:'';position:absolute;left:-6px;right:-6px;top:52%;height:7px;border-radius:4px;background:#C23A2B;transform:scaleX(var(--s,0));transform-origin:0 50%}
/* bars */
.bbase{position:absolute;left:60px;right:60px;bottom:170px;height:5px;background:#15191F;border-radius:3px}
.bcol{position:absolute;bottom:175px;width:300px;display:flex;flex-direction:column;align-items:center}
.bval{font-family:'Fraunces';font-weight:700;font-size:96px;line-height:1;letter-spacing:-.03em;color:#15191F;margin-bottom:18px}
.bar{width:220px;border-radius:22px 22px 6px 6px;border:4px solid #15191F}
.b1{background:linear-gradient(180deg,#14A374,#0B7955)}.b3{background:linear-gradient(180deg,#F0A79F,#C23A2B)}
.blab{position:absolute;top:100%;margin-top:26px;font-weight:800;font-size:34px;color:#3F4652;white-space:nowrap}
/* calendars */
.calhold{position:absolute}
.calw{position:relative}
.clab{font-weight:800;font-size:28px;letter-spacing:.14em;color:#0B7955;text-transform:uppercase;margin-bottom:14px}
.cal2,.flip{width:380px;border-radius:30px;overflow:hidden;background:#FFFFFF;color:#15191F;text-align:center;border:4px solid #15191F;box-shadow:10px 10px 0 #15191F}
.cal2 .m,.flip .m{background:#0B7955;color:#fff;font-weight:800;font-size:34px;letter-spacing:.16em;padding:16px 4px 14px;white-space:nowrap}
.cal2 .d,.flip .d{font-family:'Fraunces';font-weight:700;font-size:190px;line-height:1.02;padding:10px 0 0}
.cal2 .s{font-weight:800;font-size:28px;letter-spacing:.16em;color:#59606C;padding:0 0 26px}
.cal2.big{width:440px}.cal2.big .d{font-size:230px}
.flip{position:absolute;left:0;top:0;width:440px;background:#FFFFFF}
.flip .d{font-size:230px}.flip .s{font-weight:800;font-size:28px;padding:0 0 26px}
.flip .m{background:#59606C}
.cring{position:absolute;left:60px;top:80px;width:320px;height:230px;overflow:visible}
.calbigw{position:absolute}
.tochips{position:absolute;display:flex;flex-direction:column;gap:18px}
.tochip{display:inline-flex;align-items:center;gap:14px;padding:16px 26px;border-radius:999px;background:#fff;border:4px solid #15191F;box-shadow:6px 6px 0 #15191F;font-weight:800;font-size:36px;color:#15191F;white-space:nowrap}
/* follow */
.prof{display:flex;align-items:center;gap:26px;padding:0 36px}
.pava{width:150px;height:150px;border-radius:50%;background:#FFD84D;border:4px solid #15191F;overflow:hidden;position:relative;flex:none}
.pava img{position:absolute;left:4%;top:8%;width:92%}
.pwho b{display:block;font-weight:800;font-size:34px;color:#15191F}
.pwho span{display:block;font-weight:600;font-size:26px;color:#59606C;margin-top:6px}
.fbtn{position:relative;margin-left:auto;display:grid;place-items:center;width:250px;height:92px;border-radius:20px;background:#FFD84D;border:4px solid #15191F;box-shadow:5px 5px 0 #15191F;font-weight:800;font-size:34px}
.fbtn span{grid-area:1/1;display:inline-flex;align-items:center;gap:8px;white-space:nowrap}
.tap{position:absolute;right:120px;top:80px;width:110px;height:110px;border-radius:50%;background:rgba(21,25,31,.35)}
/* person hook */
.llc{display:flex;flex-direction:column;align-items:flex-start;padding:40px 40px}
.ico.big2{width:120px;height:120px;border-radius:30px}
.llct{font-family:'Fraunces';font-weight:700;font-size:68px;color:#15191F;margin-top:22px;line-height:1}
.llcs{font-weight:700;font-size:30px;color:#59606C;margin-top:12px;line-height:1.25}
/* checklist */
.ck{padding:30px 34px}
.ckr{display:flex;align-items:center;gap:26px;padding:24px 20px;border-radius:20px}
.ckr+.ckr{margin-top:8px}
.box{width:80px;height:80px;border-radius:18px;border:5px solid #15191F;background:#fff;display:grid;place-items:center;flex:none}
.ckt{font-weight:700;font-size:46px;line-height:1.18;color:#15191F}
/* documents */
.doc{padding:34px 34px}
.dname{font-family:'Fraunces';font-weight:700;font-size:60px;line-height:1.05;color:#15191F}
.dsub{font-weight:800;font-size:22px;letter-spacing:.12em;color:#59606C;text-transform:uppercase;margin-top:12px;line-height:1.3}
.plus{position:absolute;left:478px;top:800px;width:110px;height:110px;border-radius:50%;background:#FFD84D;border:4px solid #15191F;box-shadow:5px 5px 0 #15191F;
 display:grid;place-items:center;font-family:'Fraunces';font-weight:700;font-size:80px;color:#15191F;z-index:3;line-height:1}
.note{position:absolute;font-family:'Caveat';font-weight:700;font-size:62px;line-height:1;color:#0B7955;width:480px;text-align:right}
/* fax and mail */
.rtag{position:absolute;display:inline-flex;align-items:center;gap:12px;padding:14px 26px;border-radius:999px;background:#FDE8E5;border:4px solid #C23A2B;font-weight:800;font-size:36px;color:#C23A2B;white-space:nowrap}
.fax{position:absolute;width:470px;height:520px;transform:scale(1.14);transform-origin:0 0}
.fslot{position:absolute;left:70px;top:150px;width:330px;height:22px;border-radius:11px;background:#15191F;z-index:3}
.fpaper{position:absolute;left:105px;top:10px;width:260px;height:250px;border-radius:8px;background:#fff;border:3px solid #15191F;padding:30px 26px;z-index:2}
.fpaper i{display:block;height:13px;border-radius:7px;background:#E6E0D3;margin-top:16px}
.fbody{position:absolute;left:0;top:160px;width:470px;height:300px;border-radius:34px;background:#F3EFE6;border:4px solid #15191F;box-shadow:10px 10px 0 #15191F;z-index:4;padding:34px 36px}
.flcd{height:84px;border-radius:14px;background:#163B2E;color:#9CF2C5;font-family:'PlexMono';font-size:46px;line-height:84px;padding:0 20px;white-space:nowrap;overflow:hidden}
.fkeys{display:grid;grid-template-columns:repeat(6,1fr);gap:12px;margin-top:28px}
.fkeys i{height:38px;border-radius:10px;background:#FFFFFF;border:3px solid #15191F}
.flab{position:absolute;left:0;top:478px;width:470px;text-align:center;font-weight:800;font-size:34px;color:#15191F;z-index:5}
.ordisc{position:absolute;width:96px;height:96px;border-radius:50%;background:#FFFFFF;border:4px solid #15191F;display:grid;place-items:center;font-family:'Fraunces';font-weight:700;font-size:44px;font-style:italic;color:#15191F}
.env{position:absolute;width:390px;height:290px;border-radius:16px;background:#FFF7E8;border:4px solid #15191F;box-shadow:8px 8px 0 #15191F;overflow:hidden}
.eflap{position:absolute;left:0;top:0;width:100%;height:110px;background:linear-gradient(160deg,transparent 49%,#15191F 49.5%,#15191F 51%,transparent 51.5%),linear-gradient(20deg,transparent 49%,#15191F 49.5%,#15191F 51%,transparent 51.5%)}
.eaddr{position:absolute;left:40px;bottom:36px}
.eaddr b{display:block;font-family:'Fraunces';font-weight:700;font-size:46px;color:#15191F}
.eaddr span{display:block;font-weight:700;font-size:28px;color:#3F4652}
.emark{position:absolute;right:26px;top:26px;width:66px;height:66px;border:3px dashed #C23A2B;border-radius:8px;display:grid;place-items:center}
/* deadline */
.calhold .cal2{width:360px}
.calhold .cal2 .d{font-size:170px}
.ext{white-space:nowrap}
/* penalty */
.redv{position:absolute;left:-40px;top:-40px;width:1160px;height:2000px;background:radial-gradient(60% 50% at 50% 45%,transparent 45%,rgba(194,58,43,.28) 100%)}
.pen{position:absolute;left:80px;width:920px;text-align:center;display:flex;flex-direction:column;align-items:center}
.plab{display:inline-flex;align-items:center;gap:14px;font-weight:800;font-size:34px;letter-spacing:.14em;color:#C23A2B;text-transform:uppercase}
.pbig{font-family:'Fraunces';font-weight:700;font-size:250px;line-height:1;letter-spacing:-.045em;color:#C23A2B;margin-top:26px;white-space:nowrap}
.psub{font-weight:800;font-size:58px;color:#15191F;margin-top:6px}
/* comment */
.cbox{display:flex;align-items:center;gap:22px;padding:0 30px;border-radius:999px}
.cava{width:84px;height:84px;border-radius:50%;background:#EDE7DA;display:grid;place-items:center;flex:none}
.cin{flex:1;display:flex;align-items:center;font-family:'Jakarta';font-weight:800;font-size:52px;color:#15191F;letter-spacing:.04em}
.caret{display:inline-block;width:5px;height:56px;background:#15191F;margin-left:6px}
.csend{width:84px;height:84px;border-radius:50%;background:#DDF1E7;border:3px solid #0B7955;display:grid;place-items:center}
.dm{position:absolute;padding:30px 34px;border-radius:30px;background:#FFFFFF;border:4px solid #15191F;box-shadow:10px 10px 0 #0B7955}
.dmh{display:flex;align-items:center;gap:14px;font-size:26px;color:#59606C;font-weight:600}
.dmh b{color:#15191F;font-weight:800;font-size:30px}
.dmh .mark{width:46px;height:46px;font-size:24px;border-radius:8px}
.dmb{font-weight:800;font-size:44px;line-height:1.2;color:#15191F;margin-top:18px}
.dml{display:inline-flex;align-items:center;gap:12px;margin-top:20px;padding:14px 22px;border-radius:16px;background:#DDF1E7;border:3px solid #0B7955;font-weight:700;font-size:32px;color:#0B5E43;white-space:nowrap}
/* report */
.rep,.rep2{padding:40px 46px}
.rhead{display:flex;align-items:center;gap:14px;font-family:'SS4';font-weight:600;font-size:28px;color:#3F4652}
.rhead .mark{width:44px;height:44px;font-size:24px;border-radius:8px}
.rname{font-family:'Fraunces';font-weight:700;font-size:72px;line-height:1.02;color:#15191F;margin-top:26px}
.rtab{position:absolute;right:-150px;top:290px;padding:16px 26px;border-radius:0 16px 16px 0;background:#FFD84D;border:4px solid #15191F;font-weight:800;font-size:32px;color:#15191F;white-space:nowrap;box-shadow:6px 6px 0 #15191F}
.days{position:absolute;display:flex;gap:16px}
.day{width:168px;height:150px;border-radius:24px;background:#FFFFFF;border:4px solid #15191F;box-shadow:5px 5px 0 #15191F;display:flex;flex-direction:column;align-items:center;justify-content:center;color:#15191F}
.day span{font-weight:800;font-size:24px;letter-spacing:.14em;text-transform:uppercase}
.day b{font-family:'Fraunces';font-weight:700;font-size:72px;line-height:1}
.pg{position:absolute;inset:0;padding:40px 46px;border-radius:14px;background:linear-gradient(180deg,#FFFFFF,#F8F5EE)}
.mas{display:flex;align-items:center;gap:20px}
.mas b{font-family:'Fraunces';font-weight:700;font-size:76px;line-height:1;color:#C23A2B}
/* price */
.ptag{padding:46px 50px}
.pval{font-family:'Fraunces';font-weight:700;font-size:200px;line-height:1;letter-spacing:-.04em;color:#15191F}
.plab2{font-weight:800;font-size:38px;color:#3F4652;margin-top:10px}
.seats{display:flex;gap:14px;margin-top:30px}
.seat{width:72px;height:72px;border-radius:50%;border:4px solid #15191F;background:#FFFFFF;display:grid;place-items:center}
.pthen{font-weight:800;font-size:36px;letter-spacing:.14em;color:#59606C;text-transform:uppercase}
.pval2{font-family:'Fraunces';font-weight:700;font-size:128px;line-height:1.05;letter-spacing:-.04em;color:#0B7955}
.pb{padding:40px 46px}
/* proof */
.prf{display:flex;align-items:center;gap:40px;padding:0 54px}
.pnum,.pnum2{font-family:'Fraunces';font-weight:700;font-size:190px;line-height:1;letter-spacing:-.045em;color:#15191F;white-space:nowrap}
.pnum2{display:flex;flex-direction:column;font-size:170px}
.pnum2 small{font-family:'Jakarta';font-weight:800;font-size:30px;letter-spacing:.12em;color:#0B7955;text-transform:uppercase;margin-bottom:8px}
.ptx{font-weight:800;font-size:44px;line-height:1.18;color:#15191F}
/* no fee */
.nos{position:absolute;display:flex;flex-direction:column;gap:22px;align-items:flex-start}
.nochip{display:inline-flex;align-items:center;gap:16px;padding:20px 30px;border-radius:999px;background:#FFFFFF;border:4px solid #15191F;box-shadow:6px 6px 0 #15191F;font-weight:800;font-size:44px;color:#15191F;white-space:nowrap}
.nochip span{position:relative}
.nochip span::after{content:'';position:absolute;left:-6px;right:-6px;top:52%;height:7px;border-radius:4px;background:#C23A2B;transform:scaleX(var(--s,0));transform-origin:0 50%}
.yes2{display:flex;flex-direction:column;justify-content:center;padding:0 48px}
.seal{width:110px;height:110px;border-radius:50%;background:#0B7955;display:grid;place-items:center;border:4px solid #15191F}
.yt{font-family:'Fraunces';font-weight:700;font-size:62px;line-height:1.05;color:#15191F;margin-top:24px}
/* phone */
.phone{position:absolute;width:680px;height:900px;border-radius:70px;background:#FFFDF8;border:6px solid #15191F;box-shadow:14px 14px 0 #15191F;padding:40px 36px}
.ph-top{display:flex;align-items:center;gap:16px;padding-bottom:26px;border-bottom:3px solid #E6E0D3}
.ph-top b{font-weight:800;font-size:34px;color:#15191F}
.ph-top .mark{width:56px;height:56px;font-size:30px;border-radius:10px}
.bub{max-width:560px;padding:26px 32px;border-radius:30px;font-weight:700;font-size:44px;line-height:1.25;margin-top:40px}
.bub.out{margin-left:auto;width:max-content;background:#FFD84D;border:4px solid #15191F;border-bottom-right-radius:8px;font-weight:800;font-size:56px;letter-spacing:.06em;min-width:120px;min-height:60px}
.bub.in{background:#FFFFFF;border:4px solid #15191F;border-bottom-left-radius:8px;color:#15191F}
.plink{display:flex;align-items:center;gap:10px;margin-top:18px;padding:14px 18px;border-radius:16px;background:#DDF1E7;border:3px solid #0B7955;font-size:30px;color:#0B5E43;overflow-wrap:anywhere}
.ph-in{position:absolute;left:36px;right:36px;bottom:40px;height:90px;border-radius:999px;border:3px solid #D8D2C4;display:flex;align-items:center;justify-content:space-between;padding:0 30px;font-weight:600;font-size:30px;color:#9AA0A8}
/* captions */
.capband{position:absolute;left:0;right:0;top:1290px;height:330px;z-index:24;background:linear-gradient(180deg,rgba(246,241,231,0),rgba(246,241,231,.86) 28%,rgba(246,241,231,.86) 72%,rgba(246,241,231,0))}
.caps{position:absolute;left:50px;width:900px;top:1370px;height:240px;z-index:26}
.cap{position:absolute;left:0;right:0;top:0;text-align:center;font-family:'Jakarta';font-weight:800;font-size:80px;line-height:1.08;color:#15191F;opacity:0;letter-spacing:-.02em}
.cap span{opacity:.28;display:inline-block}
.cap span.n1{background:#FFD84D;border-radius:10px;padding:0 10px}
/* end card */
.endc{position:absolute;inset:0;z-index:40;display:flex;flex-direction:column;align-items:center;justify-content:center;opacity:0;padding:0 150px 0 90px;text-align:center;background:#F6F1E7}
.ering{position:relative;width:420px;height:420px;border-radius:50%;background:#FFD84D;overflow:hidden;border:5px solid #15191F;flex:none;box-shadow:10px 10px 0 #15191F}
.ering img{position:absolute;left:4%;top:8%;width:92%}
.ename{font-family:'Fraunces';font-weight:700;font-size:80px;letter-spacing:-.02em;color:#15191F;margin-top:40px}
.ebrand{display:flex;align-items:center;gap:14px;font-family:'SS4';font-weight:600;font-size:38px;color:#3F4652;margin-top:10px}
.ebrand .mark{width:50px;height:50px;font-size:27px;border-radius:8px}
.eoffer{font-size:38px;line-height:1.25;color:#0B7955;margin-top:30px;font-weight:800;max-width:840px}
.ecta{display:inline-flex;align-items:center;gap:16px;margin-top:44px;padding:26px 44px;border-radius:999px;font-weight:800;font-size:40px;color:#15191F;
 background:#FFD84D;border:4px solid #15191F;box-shadow:7px 7px 0 #15191F;line-height:1.2;white-space:nowrap}
.ecta b{background:#15191F;color:#FFD84D;border-radius:12px;padding:2px 14px;letter-spacing:.06em}
.esite{font-size:32px;font-weight:600;color:#3F4652;margin-top:34px;letter-spacing:.02em}
.efine{margin-top:26px;text-align:center;font-size:24px;line-height:1.45;color:#7A808A;max-width:760px}
""".replace("STAMP", texture_uri("stamp_mask"))

TIMELINE = r"""
<script>
gsap.ticker.lagSmoothing(0);
const T=%(T)s; const TL=gsap.timeline({paused:true}); window.TLREF=TL;
gsap.set('#push',{transformOrigin:'0 0'}); gsap.set('#cam',{transformOrigin:'0 0'});
%(JS)s
TL.set({},{},T);
window.fitNow=()=>{};
window.seek=(t)=>{TL.seek(t,false);return true};
window.final=()=>{TL.seek(T-0.5,false);return T};
</script>"""


def build(piece, beats, stations, disclaimer=False):
    """The whole reel as one page with a GSAP timeline. Returns (html, total, cues, looks)."""
    m = piece["content"]["motion"]
    end_at, total = lay_out(beats)
    o = Out()
    world = []
    n = len(stations)
    # camera: where each station starts and lands
    st_times = []
    for si, st in enumerate(stations):
        b0 = st["beats"][0]
        move = 0.0 if si == 0 else b0.start - MOVE + LAND
        st_times.append((move, move + MOVE if si else 0.0))
    for si, st in enumerate(stations):
        sid = "s%d" % si
        x, y = station_xy(si)
        rot = ROLL[si % len(ROLL)]
        sub = Out()
        sh = st["shot"]
        fn = SHOTS.get(sh["type"])
        if not fn:
            raise ValueError("unknown shot type %s" % sh["type"])
        fn(sub, sid, st["beats"], sh, st_times[si][1], st.get("step"))
        world.append('<div class="station" id="%s" style="left:%dpx;top:%dpx;transform:rotate(%sdeg)"><div class="sin">%s</div></div>' % (sid, x, y, rot, "".join(sub.html)))
        if si:
            o.j("gsap.set('#%s .sin',{y:70,scale:.97,transformOrigin:'50%% 40%%'}); TL.to('#%s .sin',{y:0,scale:1,duration:.9,ease:'power3.out'},%.3f);", sid, sid, st_times[si][0] + 0.25)
        if si + 1 < n and "redv" in "".join(sub.html):
            o.j("TL.to('#%s .redv',{opacity:0,duration:.35},%.3f);", sid, stations[si + 1]["beats"][0].start - MOVE + LAND)
        o.js += sub.js
        o.cues += sub.cues
        if si:
            t0 = st_times[si][0]
            o.j("TL.to('#world',{x:%d,y:%d,duration:%.2f,ease:'power3.inOut'},%.3f);", -x, -y, MOVE, t0)
            o.j("TL.to('#cam',{rotation:%s,duration:%.2f,ease:'power2.inOut'},%.3f);", -rot, MOVE, t0)
            o.j("TL.to('#cam',{scale:.82,duration:%.2f,ease:'power2.in'},%.3f); TL.to('#cam',{scale:1,duration:%.2f,ease:'power2.out'},%.3f);", MOVE / 2, t0, MOVE / 2, t0 + MOVE / 2)
            o.cue("whoosh", t0 - 0.05, 0.2)
        # a slow push in while a station is on screen
        t_end = st_times[si + 1][0] if si + 1 < n else total
        a = st_times[si][1]
        o.j("TL.fromTo('#push',{scale:1},{scale:1.045,duration:%.2f,ease:'none',immediateRender:false},%.3f);", max(0.5, t_end - a), a)
    # the top pill (and the step bar for middle of funnel pieces)
    labels, cur = [], None
    for si in range(n):
        lab = stations[si].get("pill") or cur
        labels.append(lab); cur = lab
    hud = ['<div class="hbrand"><span class="mark">FD</span>Finance Department</div>']
    seen = {}
    for si, lab in enumerate(labels):
        if lab is None:
            continue
        if lab not in seen:
            seen[lab] = len(seen)
            hud.append('<div class="hpill" id="hp%d"><i></i>%s</div>' % (seen[lab], esc(lab)))
    shown = None
    for si, lab in enumerate(labels):
        if lab == shown:
            continue
        t = 0.0 if si == 0 else st_times[si][0] + MOVE * 0.5
        if shown is not None:
            o.j("TL.to('#hp%d',{opacity:0,y:-10,duration:.15},%.3f);", seen[shown], t - 0.05)
        if lab is not None:
            if si == 0:
                o.j("gsap.set('#hp%d',{opacity:1});", seen[lab])
            else:
                o.j("TL.fromTo('#hp%d',{opacity:0,y:12},{opacity:1,y:0,duration:.25,ease:'back.out(2)'},%.3f);", seen[lab], t)
        shown = lab
    steps = [st.get("step") for st in stations if st.get("step")]
    if steps:
        nsteps = max(steps)
        hud.append('<div class="hprog" id="hprog">%s</div>' % "".join('<span><b id="pb%d"></b></span>' % k for k in range(nsteps)))
        first = min(si for si, st in enumerate(stations) if st.get("step"))
        last = max(si for si, st in enumerate(stations) if st.get("step"))
        o.j("gsap.set('#hprog',{opacity:0}); TL.to('#hprog',{opacity:1,duration:.3},%.3f);", st_times[first][0] + MOVE * 0.5)
        for si, st in enumerate(stations):
            if st.get("step"):
                o.j("TL.to('#pb%d',{scaleX:1,duration:.5,ease:'power2.out'},%.3f);", st["step"] - 1, st_times[si][1])
        if last + 1 < n:
            o.j("TL.to('#hprog',{opacity:0,duration:.3},%.3f);", st_times[last + 1][0] + MOVE * 0.5)
    # captions
    cap_html, cap_js = captions(beats, total)
    o.js += cap_js
    o.j("gsap.set('.capband',{opacity:0}); TL.to('.capband',{opacity:1,duration:.3},%.3f);", beats[1].start - 0.3 if len(beats) > 1 else 0)
    o.j("TL.to('.capband',{opacity:0,duration:.25},%.3f);", end_at - 0.1)
    # end card
    cta = m["cta"]
    pill = cta.get("pill") or esc(cta["text"])
    o.j("TL.to('#endc',{opacity:1,duration:.5,ease:'power1.inOut'},%.3f);", end_at)
    o.j("TL.from('#endc .ering',{scale:.6,opacity:0,duration:.6,ease:'back.out(1.8)'},%.3f);", end_at + 0.1)
    o.j("TL.from('#endc .ename,#endc .ebrand',{y:30,opacity:0,duration:.5,ease:'power3.out',stagger:.08},%.3f);", end_at + 0.25)
    o.j("TL.from('#endc .ecta',{y:30,opacity:0,duration:.5,ease:'back.out(1.6)'},%.3f);", end_at + 0.45)
    o.cue("chime", end_at + 0.2, 0.26)
    x_max = max(station_xy(i)[0] for i in range(n)) + 1080
    y_max = station_xy(n - 1)[1] + 1920
    grid = '<div class="grid" style="width:%dpx;height:%dpx"></div>' % (x_max + 5200, y_max + 5200)
    body = ('<div id="push"><div id="cam"><div id="world">%s%s%s</div></div></div>'
            '<div class="hud">%s</div><div class="capband"></div><div class="caps">%s</div>%s'
            % (grid, props(n), "".join(world), "".join(hud), cap_html, end_card_html(cta.get("kind"), cta.get("keyword"), pill, m.get("offer"), disclaimer)))
    script = TIMELINE % {"T": total, "JS": "\n".join(o.js)}
    html = shell(body, W, H, CSS, "video", script=script)
    looks = [0.0] + [round(max(0.2, (st["beats"][0].start + st["beats"][-1].end) / 2 + 0.4), 2) for st in stations[1:]] + [round(min(total - 0.3, end_at + 1.6), 2)]
    return html, total, o.cues, looks


import work  # noqa: E402  (adds the work and recap shots and the cover expansion)
