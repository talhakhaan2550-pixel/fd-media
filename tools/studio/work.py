"""Work scenes for motion v2 (17 November 2026): what an offer covers, shown being done.

Talha, 17 November 2026: whenever a piece introduces a service or quotes a price, it first shows in detail what
the service covers, practically showing the work, instead of just saying the name and the price.

So content.motion.shots may hold {"cover": "<offer id>"} where the offer is one of tools/coverage.json. At render
time it becomes one station per item on the offer page's What you get list (word for word, FD-31), each with a
scene of that work being done, numbered as steps, then a recap that names the offer. The price comes after.

Shot types added: "work" (kind: books, revenue, table, review, runway, findings, form, send, stack, calendar,
compare, setup) and "recap". Labels on screen come from the coverage list's own words; scenes show no figures.
"""
import json
import os

import motion as M
from brand import esc, ic

HERE = os.path.dirname(os.path.abspath(__file__))
COVERAGE = os.path.join(HERE, "..", "coverage.json")
_cov = None


def coverage():
    global _cov
    if _cov is None:
        with open(COVERAGE) as f:
            _cov = json.load(f)
    return _cov


def offer(oid):
    offers = coverage()["offers"]
    if oid not in offers:
        raise ValueError("cover: %s is not an offer in tools/coverage.json (%s)" % (oid, ", ".join(offers)))
    return offers[oid]


def expand(m):
    """content.motion with every {"cover": id} replaced by its stations. Returns (shots, pills by station index)."""
    shots, pills = [], {}
    old = m.get("pills", {}) or {}
    if "0" in old:
        pills["0"] = old["0"]
    numbered = not any(s.get("step") for s in m.get("shots", []) if "cover" not in s)
    for si, sh in enumerate(m.get("shots", [])):
        if str(si + 1) in old:
            pills[str(len(shots) + 1)] = old[str(si + 1)]
        if "cover" not in sh:
            shots.append(sh)
            continue
        o = offer(sh["cover"])
        items = o["items"]
        if sh.get("pill"):
            pills[str(len(shots) + 1)] = sh["pill"]
        for k, it in enumerate(items):
            scene = dict(it["scene"])
            scene.setdefault("type", "work")
            scene["title"] = it["title"]
            scene["cover"] = "%s.%s" % (sh["cover"], it["id"])
            shots.append({"shot": scene, "step": (k + 1) if numbered and sh.get("steps", True) else None,
                          "lines": [{"text": it["text"].rstrip(".") + ".", "say": it.get("say")}]})
        if sh.get("recap", True):
            rc = o["recap"]
            if sh.get("recap_pill"):
                pills[str(len(shots) + 1)] = sh["recap_pill"]
            shots.append({"shot": {"type": "recap", "title": rc["title"], "rows": [it["title"] for it in items]},
                          "lines": [{"text": rc["text"], "say": rc.get("say")}]})
    return shots, pills


# ---------------------------------------------------------------- timing
def span(bs, arrive, tail=0.0):
    """Start and end of a scene's main action: from the camera landing to just before its last word ends."""
    t0 = arrive + 0.1
    t1 = max(t0 + 0.9, bs[-1].end - 0.3 - tail)
    return t0, t1


def spread(t0, t1, n, k):
    return t0 + (t1 - t0) * (k + 0.5) / max(1, n)


def nb(text):
    """Escaped, with any word that has a hyphen in it (1099-NEC, W-9) kept on one line."""
    return " ".join('<span style="white-space:nowrap">%s</span>' % esc(w) if "-" in w else esc(w) for w in str(text).split(" "))


def pills_html(labels, cls="wchips"):
    return '<div class="%s">%s</div>' % (cls, "".join('<div class="wchip c%d">%s<span>%s</span></div>' % (k, M.check(34), esc(x)) for k, x in enumerate(labels)))


def pop_all(o, sid, n, t, cls="wchip", step=0.16, cue="tick"):
    for k in range(n):
        M.pop(o, "#%s .%s.c%d" % (sid, cls, k), t + k * step, cue, 0.18, 24)


W1 = [62, 48, 70, 55, 66, 44, 58]
W2 = [24, 30, 20, 28, 22, 26, 18]


# ---------------------------------------------------------------- kinds
def k_books(o, sid, bs, sp, arrive):
    """Two papers side by side; each line on one is matched to the other, a line drawn between, a tick."""
    n = sp.get("rows", 5)
    chips, stamp_t = sp.get("chips") or [], sp.get("stamp")
    t0, t1 = span(bs, arrive, 0.75 if (chips or stamp_t) else 0)
    top, rowh, gap = 590, 66, 14
    first = top + 34 + 108

    def doc(cls, name, left, tick):
        rows = "".join('<div class="wr r%d"><i style="width:%d%%"></i><b style="width:%d%%"></b>%s</div>'
                       % (k, W1[k % len(W1)], W2[k % len(W2)], '<span class="wt">%s</span>' % M.check(36) if tick else "") for k in range(n))
        return ('<div class="paper wdoc %s" style="left:%dpx;top:%dpx;width:440px;height:%dpx"><div class="wdn">%s</div>%s</div>'
                % (cls, left, top, 160 + n * (rowh + gap), esc(name), rows))
    o.h(doc("wa", sp["left"], 60, False))
    o.h(doc("wb", sp["right"], 580, True))
    paths = "".join('<path class="wl%d" d="M%d %d C%d %d %d %d %d %d" fill="none" stroke="#0B7955" stroke-width="7" stroke-linecap="round"/>'
                    % (k, 455, first + k * (rowh + gap), 520, first + k * (rowh + gap) - 26, 530, first + k * (rowh + gap) + 26, 610, first + k * (rowh + gap))
                    for k in range(n))
    o.h('<svg class="wlinks" style="position:absolute;left:0;top:0;overflow:visible" width="1080" height="1300" viewBox="0 0 1080 1300">%s</svg>' % paths)
    o.j("gsap.set('#%s .wa',{rotation:-1.2}); gsap.set('#%s .wb',{rotation:1}); gsap.set('#%s .wt',{scale:0,opacity:0});", sid, sid, sid)
    for k in range(n):
        t = spread(t0, t1, n, k)
        o.j("TL.to('#%s .wa .r%d, #%s .wb .r%d',{backgroundColor:'rgba(11,121,85,.13)',duration:.25},%.3f);", sid, k, sid, k, t - 0.15)
        M.draw(o, "#%s .wl%d" % (sid, k), t - 0.12, 0.35)
        o.j("TL.to('#%s .wb .r%d .wt',{scale:1,opacity:1,duration:.3,ease:'back.out(2.2)'},%.3f);", sid, k, t + 0.15)
        o.cue("tick", t + 0.15, 0.2)
    if chips:
        o.h(pills_html(chips).replace('class="wchips"', 'class="wchips" style="left:60px;top:%dpx"' % (top + 190 + n * (rowh + gap))))
        pop_all(o, sid, len(chips), t1 + 0.1)
    if stamp_t:
        M.stamp(o, sid, "wst", stamp_t, 620, top + 110 + n * (rowh + gap) - 120, t1 + 0.35, -8, 58)


MONTHS = "JFMAMJJASOND"


def k_revenue(o, sid, bs, sp, arrive):
    """One block of revenue split into the months it is earned in."""
    chip = sp.get("chip")
    t0, t1 = span(bs, arrive, 0.6 if chip else 0)
    o.h('<div class="card wrev" style="left:60px;top:600px;width:390px;height:430px">%s<div class="wblk%s"><div class="wfill"></div><b>%s</b></div></div>'
        % ('<div class="wrl">%s</div>' % esc(sp["doc"]) if sp.get("doc") else "", "" if sp.get("doc") else " tall", esc(sp.get("block", ""))))
    tiles = "".join('<div class="wmo m%d"><span>%s</span></div>' % (k, MONTHS[k]) for k in range(12))
    o.h('<div class="wmonths" style="left:486px;top:600px">%s</div>' % tiles)
    bits = "".join('<i class="wbit b%d"></i>' % k for k in range(12))
    o.h('<div class="wbits" style="left:0;top:0">%s</div>' % bits)
    cx, cy = 60 + 195, 600 + 270
    o.j("gsap.set('#%s .wbit',{x:%d,y:%d,opacity:0,scale:.6});", sid, cx - 30, cy - 30)
    o.j("TL.to('#%s .wblk',{keyframes:{scale:[1,1.06,1]},duration:.4},%.3f);", sid, t0)
    for k in range(12):
        col, row = k % 4, k // 4
        tx, ty = 486 + col * 132 + 59 - 30, 600 + row * 134 + 66 - 30
        t = t0 + 0.35 + (t1 - t0 - 0.35) * k / 12
        o.j("TL.set('#%s .b%d',{opacity:1},%.3f); TL.to('#%s .b%d',{x:%d,y:%d,scale:1,duration:.42,ease:'power2.inOut'},%.3f);", sid, k, t, sid, k, tx, ty, t)
        o.j("TL.to('#%s .m%d',{backgroundColor:'#DDF1E7',borderColor:'#0B7955',duration:.2},%.3f);", sid, k, t + 0.38)
        if k % 3 == 0:
            o.cue("tick", t + 0.38, 0.12)
    o.j("TL.to('#%s .wfill',{scaleY:.08,transformOrigin:'50%% 100%%',duration:%.2f,ease:'none'},%.3f);", sid, max(0.5, t1 - t0 - 0.35), t0 + 0.35)
    if chip:
        o.h('<div class="ytag wtag" style="left:60px;top:1100px">%s %s</div>' % (M.check(40, "#15191F"), esc(chip)))
        M.pop(o, "#%s .wtag" % sid, t1 + 0.1, "chime", 0.16)


def k_table(o, sid, bs, sp, arrive):
    """Rows checked one by one with a magnifier, against source papers, or each making a form."""
    rows = sp.get("rows", 4)
    labels = rows if isinstance(rows, list) else [None] * rows
    n = len(labels)
    pick, make, sources = sp.get("pick") or [], sp.get("make"), sp.get("sources") or []
    t0, t1 = span(bs, arrive, 0.6 if pick else 0)
    mark = '<b>%s</b>' % esc(sp["pick_mark"]) if sp.get("pick_mark") else ic("arrow", 40, "#15191F", 3.4)
    rowh = 92 if n <= 4 else 80
    body = "".join('<div class="wtr r%d" style="height:%dpx">%s<i style="width:%d%%"></i><span class="wbx">%s</span></div>'
                   % (k, rowh, '<em>%s</em>' % esc(l) if l else '<i class="wph" style="width:%d%%"></i>' % (W1[k % len(W1)] - 20), W2[k % len(W2)] + 6,
                      M.check(40) if k not in pick else mark) for k, l in enumerate(labels))
    o.h('<div class="card wtab" style="left:60px;top:590px;width:620px"><div class="wth">%s</div>%s</div>' % (esc(sp.get("head", "")), body))
    if sources:
        for j, s in enumerate(sources[:3]):
            o.h('<div class="paper wsrc s%d" style="left:%dpx;top:%dpx;width:300px;height:380px"><div class="wsn">%s</div><div class="dl"><i></i><i></i><i style="width:60%%"></i><i></i></div></div>'
                % (j, 720 + j * 14, 620 + j * 120, esc(s)))
            o.j("gsap.set('#%s .s%d',{rotation:%d});", sid, j, [4, -3, 5][j])
    if make:
        o.h('<div class="wpile" style="left:730px;top:640px">%s</div>' % "".join(
            '<div class="paper wmk k%d"><b>%s</b><div class="dl"><i></i><i style="width:60%%"></i></div></div>' % (k, nb(make)) for k in range(n)))
    if pick:
        o.h('<div class="ytag wpick" style="left:60px;top:%dpx">%s</div>' % (590 + 100 + n * rowh + 30, esc(sp.get("pick_tag", ""))))
    o.h('<div class="wmag">%s</div>' % ic("search", 150, "#15191F", 3.2))
    y0 = 590 + 100
    o.j("gsap.set('#%s .wbx > *',{scale:0,opacity:0}); gsap.set('#%s .wmag',{x:470,y:%d,opacity:0});", sid, sid, y0 - 40)
    o.j("TL.to('#%s .wmag',{opacity:1,duration:.2},%.3f);", sid, t0 - 0.2)
    for k in range(n):
        t = spread(t0, t1, n, k)
        o.j("TL.to('#%s .wmag',{y:%d,duration:.32,ease:'power2.inOut'},%.3f);", sid, y0 + k * rowh - 40, t - 0.34)
        o.j("TL.to('#%s .r%d .wbx > *',{scale:1,opacity:1,duration:.3,ease:'back.out(2.2)'},%.3f);", sid, k, t)
        o.j("TL.to('#%s .r%d',{backgroundColor:'%s',duration:.25},%.3f);", sid, k, "rgba(255,216,77,.45)" if k in pick else "rgba(11,121,85,.1)", t)
        o.cue("tick", t, 0.2)
        if make:
            o.j("gsap.set('#%s .k%d',{x:-420,y:%d,opacity:0,rotation:-8});", sid, k, y0 + k * rowh - 700)
            o.j("TL.to('#%s .k%d',{x:%d,y:%d,opacity:1,rotation:%d,duration:.45,ease:'power3.out'},%.3f);", sid, k, k * 10, k * 26, [-4, 3, -2, 4, -3, 2, -1][k % 7], t + 0.05)
    o.j("TL.to('#%s .wmag',{opacity:0,duration:.25},%.3f);", sid, t1 + 0.2)
    if pick:
        M.pop(o, "#%s .wpick" % sid, t1 + 0.1, "chime", 0.14)


def k_review(o, sid, bs, sp, arrive):
    """A paper read through: lines highlighted, a note written in the margin for each."""
    notes = sp.get("notes") or []
    t0, t1 = span(bs, arrive)
    lines = [2, 5, 8][:max(1, len(notes))] if len(notes) <= 3 else [1, 3, 6, 8]
    widths = [92, 80, 96, 70, 88, 94, 64, 90, 84, 76, 58]
    ls = "".join('<i class="ln%d" style="width:%d%%"></i>' % (k, widths[k]) for k in range(11))
    hl = "".join('<span class="whl h%d" style="top:%dpx;width:%d%%"></span>' % (j, 128 + ln * 42 - 10, widths[ln] - 4) for j, ln in enumerate(lines))
    o.h('<div class="paper wrd" style="left:70px;top:570px;width:600px;height:640px"><div class="wdn">%s</div><div class="wls">%s</div>%s</div>' % (esc(sp["doc"]), ls, hl))
    for j, (ln, note) in enumerate(zip(lines, notes)):
        y = 570 + 128 + ln * 42 - 40
        o.h('<div class="wnote n%d" style="left:700px;top:%dpx">%s</div>' % (j, y, esc(note)))
        o.h('<svg class="wna a%d" style="position:absolute;left:640px;top:%dpx" width="80" height="60" viewBox="0 0 80 60"><path d="M74 30 C50 30 30 30 8 34 M20 24 L6 34 L20 44" fill="none" stroke="#0B7955" stroke-width="5" stroke-linecap="round" stroke-linejoin="round"/></svg>' % (j, y + 6))
    o.j("gsap.set('#%s .wrd',{rotation:-1.4}); gsap.set('#%s .whl',{scaleX:0,transformOrigin:'0 50%%'});", sid, sid)
    for j in range(len(lines)):
        t = spread(t0, t1, len(lines), j)
        o.j("TL.to('#%s .h%d',{scaleX:1,duration:.45,ease:'power2.inOut'},%.3f);", sid, j, t - 0.3)
        o.cue("tick", t - 0.3, 0.12)
        if j < len(notes):
            o.j("gsap.set('#%s .n%d',{opacity:0,x:-14});TL.to('#%s .n%d',{opacity:1,x:0,duration:.35},%.3f);", sid, j, sid, j, t + 0.1)
            M.draw(o, "#%s .a%d path" % (sid, j), t, 0.35)


def k_runway(o, sid, bs, sp, arrive):
    """Cash month by month at the current rate of spending, down to the month it runs out."""
    t0, t1 = span(bs, arrive, 0.5)
    n, pitch = 10, 70
    cols = "".join('<i class="wc c%d" style="left:%dpx;height:%dpx"></i>' % (k, 30 + k * pitch, max(12, round(300 * (1 - k / n) ** 0.85))) for k in range(n))
    ticks = "".join('<span style="left:%dpx"></span>' % (56 + k * pitch) for k in range(n + 1))
    o.h('<div class="card wrun" style="left:60px;top:580px;width:960px;height:600px"><div class="wrh">%s<b>%s</b></div>'
        '<div class="wchart">%s<div class="wbase"></div><div class="wticks">%s</div>'
        '<div class="wflag" style="left:%dpx"><svg width="190" height="190" viewBox="0 0 190 190"><path d="M10 186 V12" stroke="#15191F" stroke-width="7" stroke-linecap="round"/>'
        '<path d="M12 14 H178 L154 46 L178 78 H12z" fill="#C23A2B" stroke="#15191F" stroke-width="5" stroke-linejoin="round"/></svg><em>%s</em></div></div>'
        '<div class="wsub">%s</div></div>' % (ic("dollar", 52, "#0B7955", 3), esc(sp.get("label", "")), cols, ticks, 30 + n * pitch - 6, esc(sp.get("flag", "")), esc(sp.get("sub", ""))))
    o.j("gsap.set('#%s .wc',{scaleY:0,transformOrigin:'50%% 100%%'}); gsap.set('#%s .wflag',{y:-120,opacity:0,rotation:-10}); gsap.set('#%s .wsub',{opacity:0,y:16});", sid, sid, sid)
    for k in range(n):
        t = t0 + (t1 - t0) * k / n
        o.j("TL.to('#%s .c%d',{scaleY:1,duration:.32,ease:'power2.out'},%.3f);", sid, k, t)
        if k % 2 == 0:
            o.cue("tick", t, 0.1)
    o.j("TL.to('#%s .wsub',{opacity:1,y:0,duration:.35},%.3f);", sid, t0 + (t1 - t0) * 0.45)
    o.j("TL.to('#%s .wflag',{y:0,opacity:1,rotation:0,duration:.45,ease:'bounce.out'},%.3f);", sid, t1)
    o.cue("impact", t1 + 0.12, 0.24)


def k_findings(o, sid, bs, sp, arrive):
    """The findings report: each gap gets what it costs and how long it takes to fix; then the call."""
    n, chips, call = sp.get("rows", 3), sp.get("chips") or [], sp.get("call")
    t0, t1 = span(bs, arrive, 0.6 if call else 0)
    rows = "".join('<div class="wfr r%d"><span class="wfl">%s %d</span>%s</div>' % (k, esc(sp.get("row_label", "Gap")), k + 1,
                   "".join('<span class="wfc c%d">%s</span>' % (j, esc(c)) for j, c in enumerate(chips))) for k in range(n))
    o.h('<div class="paper wfind" style="left:80px;top:560px;width:920px"><div class="wfh">%s<b>%s</b></div>%s</div>' % (ic("dollar", 64, "#C23A2B", 3), esc(sp.get("page", "")), rows))
    if call:
        o.h('<div class="card wcall" style="left:500px;top:%dpx">%s<span>%s</span></div>' % (560 + 150 + n * 118 + 30, ic("person", 50, "#0B7955", 3), esc(call)))
    o.j("gsap.set('#%s .wfind',{rotation:-1});", sid)
    for k in range(n):
        t = spread(t0, t1, n, k)
        M.pop(o, "#%s .wfr.r%d" % (sid, k), t - 0.3, "tick", 0.16, 20)
        for j in range(len(chips)):
            M.pop(o, "#%s .r%d .wfc.c%d" % (sid, k, j), t + 0.05 + j * 0.15, None, 0, 12)
    if call:
        M.pop(o, "#%s .wcall" % sid, t1 + 0.1, "chime", 0.18)


def k_form(o, sid, bs, sp, arrive):
    """One or two forms filled in field by field, then stamped."""
    forms, stamp_t = sp["forms"], sp.get("stamp")
    t0, t1 = span(bs, arrive, 0.8 if stamp_t else 0)
    nf = 5
    spots = [(170, 570, 740, -1.5)] if len(forms) == 1 else [(60, 580, 470, -2.5), (560, 610, 470, 2)]
    for j, (f, (x, y, w, r)) in enumerate(zip(forms, spots)):
        tag = '<span class="wftag">%s</span>' % esc(f["tag"]) if f.get("tag") else ""
        fields = "".join('<div class="wff"><i style="width:%dpx"></i><div class="wfb"><b class="fb%d" style="width:%d%%"></b></div></div>' % (90 + (k * 37) % 60, k, 60 + (k * 23) % 35) for k in range(nf))
        o.h('<div class="paper wform f%d" style="left:%dpx;top:%dpx;width:%dpx"><div class="wfn">%s</div>%s%s</div>' % (j, x, y, w, nb(f["name"]), tag, fields))
        o.j("gsap.set('#%s .f%d',{rotation:%s}); gsap.set('#%s .f%d .wfb b',{scaleX:0,transformOrigin:'0 50%%'});", sid, j, r, sid, j)
    total = nf * len(forms)
    for j in range(len(forms)):
        for k in range(nf):
            t = t0 + (t1 - t0) * (j * nf + k) / total
            o.j("TL.to('#%s .f%d .fb%d',{scaleX:1,duration:.3,ease:'steps(6)'},%.3f);", sid, j, k, t)
            if k % 2 == 0:
                o.cue("tick", t, 0.1)
    if stamp_t:
        x, y, w, r = spots[-1]
        M.stamp(o, sid, "wst", stamp_t, x + w // 2 - 180, y + 420, t1 + 0.3, -9, 56)


ICON_FOR = {"irs": "building", "state": "building", "delaware": "building", "wyoming": "building", "you": "person", "contractor": "people",
            "each contractor": "people", "fax": "send", "mail": "mail", "your payroll provider": "building"}


def k_send(o, sid, bs, sp, arrive):
    """Papers go where they need to go (or come in from people), and a receipt or note says it is done."""
    items, dests = sp.get("items") or [], sp.get("to") or []
    people, receipt, note = sp.get("from_people", 0), sp.get("receipt"), sp.get("note")
    t0, t1 = span(bs, arrive, 0.6 if (receipt or note) else 0)
    if people:
        o.h('<div class="wppl" style="left:70px;top:620px">%s</div>' % "".join('<div class="wpp p%d">%s</div>' % (k, ic("person", 70, "#15191F", 2.6)) for k in range(people)))
    else:
        o.h("".join('<div class="paper wit i%d" style="left:%dpx;top:%dpx"><b>%s</b><div class="dl"><i></i><i></i><i style="width:60%%"></i></div></div>'
                    % (k, 80 + k * 22, 640 + k * 30, nb(x)) for k, x in enumerate(items)))
        for k in range(len(items)):
            o.j("gsap.set('#%s .i%d',{rotation:%d});", sid, k, [-4, 3, -2][k % 3])
    nd = max(1, len(dests))
    for j, d in enumerate(dests):
        lab = d if isinstance(d, str) else d["label"]
        icon = (d.get("icon") if isinstance(d, dict) else None) or ICON_FOR.get(lab.lower(), "doc")
        y = 600 + (j * 300 if nd > 1 else 150)
        o.h('<div class="card wdst d%d" style="left:620px;top:%dpx">%s<b>%s</b><span class="wok">%s</span></div>' % (j, y, ic(icon, 74, "#0B7955", 2.8), esc(lab), M.check(40)))
    o.j("gsap.set('#%s .wok',{scale:0,opacity:0});", sid)
    flights = []
    if people:
        for k in range(people):
            flights.append((150, 680 + k * 160, 0))
    else:
        for k in range(len(items)):
            for j in range(nd):
                flights.append((200 + k * 22, 760 + k * 30, j))
    o.h("".join('<div class="paper wfly y%d"><b>%s</b></div>' % (q, nb(items[0] if people else items[(q // nd) % len(items)])) for q in range(len(flights))))
    for q, (x, y, j) in enumerate(flights):
        dj = j if not people else 0
        tx, ty = 700, (600 + (dj * 300 if nd > 1 else 150)) + 40
        t = spread(t0, t1, len(flights), q) - 0.3
        o.j("gsap.set('#%s .y%d',{x:%d,y:%d,opacity:0,scale:.8});", sid, q, x, y)
        o.j("TL.to('#%s .y%d',{opacity:1,duration:.12},%.3f); TL.to('#%s .y%d',{keyframes:{x:[%d,%d,%d],y:[%d,%d,%d],scale:[.8,.7,.35],opacity:[1,1,0]},duration:.6,ease:'power1.inOut'},%.3f);",
            sid, q, t, sid, q, x, (x + tx) // 2, tx, y, min(y, ty) - 160, ty, t + 0.05)
        o.j("TL.to('#%s .d%d',{keyframes:{scale:[1,1.06,1]},duration:.3},%.3f); TL.to('#%s .d%d .wok',{scale:1,opacity:1,duration:.3,ease:'back.out(2)'},%.3f);",
            sid, dj, t + 0.6, sid, dj, t + 0.6)
        o.cue("whoosh", t, 0.1)
    if receipt:
        o.h('<div class="wrcpt" style="left:300px;top:1150px">%s<span>%s</span></div>' % (M.check(44), esc(receipt)))
        o.j("gsap.set('#%s .wrcpt',{opacity:0,y:40,clipPath:'inset(0 0 100%% 0)'}); TL.to('#%s .wrcpt',{opacity:1,y:0,clipPath:'inset(0 0 0%% 0)',duration:.5,ease:'power2.out'},%.3f);", sid, sid, t1 + 0.1)
        o.cue("chime", t1 + 0.2, 0.16)
    if note:
        o.h('<div class="rtag wnt" style="left:70px;top:1150px">%s<span>%s</span></div>' % (ic("mail", 40, "#C23A2B", 3), esc(note)))
        M.pop(o, "#%s .wnt" % sid, t1 + (0.35 if receipt else 0.1), "impact", 0.14)


def k_stack(o, sid, bs, sp, arrive):
    """What you receive, dealt onto the desk one paper at a time."""
    docs = sp["docs"]
    n = len(docs)
    extra = sp.get("call") or sp.get("folder") or sp.get("stamp")
    t0, t1 = span(bs, arrive, 0.6 if extra else 0)
    w = 400 if n <= 2 else 340
    lefts = {1: [340], 2: [110, 560], 3: [60, 370, 680], 4: [50, 290, 530, 770]}[min(4, n)]
    tops = [610, 580, 620, 590]
    rots = [-5, 2, 6, -3]
    for k, d in enumerate(docs[:4]):
        name, sub = (d, "") if isinstance(d, str) else (d["name"], d.get("sub", ""))
        o.h('<div class="paper wsk k%d" style="left:%dpx;top:%dpx;width:%dpx"><span class="mark">FD</span><div class="wskn">%s</div>%s<div class="dl"><i></i><i></i><i style="width:70%%"></i><i></i><i style="width:50%%"></i></div></div>'
            % (k, lefts[k] if n <= 4 else 0, tops[k], w if n > 1 else 440, nb(name), '<div class="wsks">%s</div>' % esc(sub) if sub else ""))
        t = t0 + (t1 - t0) * k / n
        o.j("gsap.set('#%s .k%d',{x:360,y:-520,rotation:24,opacity:0}); TL.to('#%s .k%d',{x:0,y:0,rotation:%d,opacity:1,duration:.55,ease:'power3.out'},%.3f);", sid, k, sid, k, rots[k], t)
        o.cue("whoosh", t, 0.1)
    te = t1 + 0.1
    if sp.get("stamp"):
        M.stamp(o, sid, "wst", sp["stamp"], 560, 1000, te + 0.2, -8, 56)
    if sp.get("folder"):
        o.h('<div class="ytag wfold" style="left:70px;top:1180px">%s %s</div>' % (ic("lock", 40, "#15191F", 3), esc(sp["folder"])))
        M.pop(o, "#%s .wfold" % sid, te, "chime", 0.14)
    if sp.get("call"):
        o.h('<div class="card wcall" style="left:500px;top:1150px">%s<span>%s</span></div>' % (ic("person", 50, "#0B7955", 3), esc(sp["call"])))
        M.pop(o, "#%s .wcall" % sid, te, "chime", 0.16)


def k_calendar(o, sid, bs, sp, arrive):
    """A date ringed on the calendar, or every deadline ringed on a calendar of its own."""
    t0, t1 = span(bs, arrive, 0.4)
    if sp.get("month"):
        o.h('<div class="calbigw" style="left:300px;top:560px">%s<svg class="cring" viewBox="0 0 300 220"><path d="M60 120 C50 50 140 22 210 40 C280 60 270 170 190 190 C110 210 50 170 70 100" fill="none" stroke="#C23A2B" stroke-width="9" stroke-linecap="round"/></svg></div>'
            % M.calendar_html("main", sp["month"], sp["day"], sp.get("weekday", "&nbsp;"), big=True).replace("&amp;nbsp;", "&nbsp;"))
        M.draw(o, "#%s .cring path" % sid, t0 + (t1 - t0) * 0.45, 0.6)
        o.cue("tick", t0 + (t1 - t0) * 0.45, 0.2)
        if sp.get("label"):
            o.h('<div class="ytag wtag" style="left:300px;top:1150px">%s %s</div>' % (ic("calendar", 40, "#15191F", 3), esc(sp["label"])))
            M.pop(o, "#%s .wtag" % sid, t1, "chime", 0.16)
        return
    rings = sp.get("rings", [4, 9, 16, 24, 30])
    cells = "".join('<div class="wcell q%d">%s</div>' % (k, '<svg viewBox="0 0 100 100"><circle cx="50" cy="50" r="38" fill="none" stroke="#C23A2B" stroke-width="9"/></svg>' if k in rings else "") for k in range(35))
    o.h('<div class="card wcal" style="left:80px;top:570px;width:920px"><div class="wch">%s<b>%s</b></div><div class="wdays">%s</div><div class="wgrid">%s</div></div>'
        % (ic("calendar", 52, "#0B7955", 3), esc(sp.get("label", "")), "".join("<span>%s</span>" % d for d in "MTWTFSS"), cells))
    for j, k in enumerate(rings):
        t = spread(t0, t1, len(rings), j)
        M.draw(o, "#%s .q%d circle" % (sid, k), t, 0.35)
        o.j("TL.to('#%s .q%d',{backgroundColor:'#FDE8E5',duration:.2},%.3f);", sid, k, t)
        o.cue("tick", t, 0.14)


def k_compare(o, sid, bs, sp, arrive):
    """Worked out both ways from the same papers; the lower figure circled."""
    t0, t1 = span(bs, arrive, 0.5)
    src = sp.get("from") or []
    o.h('<div class="wfrom" style="top:560px">%s</div>' % "".join('<div class="wsrcc s%d">%s<span>%s</span></div>' % (k, ic("doc", 40, "#15191F", 2.6), esc(s)) for k, s in enumerate(src)))
    pick = 1 if sp.get("pick", "right") == "right" else 0
    for j, (side, x) in enumerate(((sp["left"], 70), (sp["right"], 560))):
        h = 150 if j == pick else 330
        o.h('<div class="card wcmp m%d%s" style="left:%dpx;top:720px;width:450px;height:460px"><div class="wcn">%s</div><div class="wbar" style="height:%dpx"></div></div>' % (j, " lo" if j == pick else "", x, esc(side), h))
    px = 70 if pick == 0 else 560
    o.h('<svg class="wring" style="position:absolute;left:%dpx;top:690px;overflow:visible" width="510" height="530" viewBox="0 0 510 530"><path d="M60 40 C200 -10 420 0 480 90 C530 200 520 420 430 490 C300 560 90 530 30 420 C-20 300 0 120 90 40" fill="none" stroke="#0B7955" stroke-width="10" stroke-linecap="round"/></svg>' % (px - 30))
    if sp.get("tag"):
        o.h('<div class="ytag wtag" style="left:%dpx;top:1200px">%s %s</div>' % (px, M.check(40, "#15191F"), esc(sp["tag"])))
    o.j("gsap.set('#%s .wbar',{scaleY:0,transformOrigin:'50%% 100%%'}); gsap.set('#%s .wsrcc',{opacity:0,y:-20});", sid, sid)
    for k in range(len(src)):
        o.j("TL.to('#%s .wsrcc.s%d',{opacity:1,y:0,duration:.3},%.3f);", sid, k, t0 + 0.15 * k)
    ta, tb = t0 + (t1 - t0) * 0.3, t0 + (t1 - t0) * 0.6
    o.j("TL.to('#%s .m0 .wbar',{scaleY:1,duration:.5,ease:'power3.out'},%.3f); TL.to('#%s .m1 .wbar',{scaleY:1,duration:.5,ease:'power3.out'},%.3f);", sid, ta, sid, tb)
    o.cue("tick", ta, 0.16); o.cue("tick", tb, 0.16)
    M.draw(o, "#%s .wring path" % sid, t1 - 0.1, 0.5)
    if sp.get("tag"):
        M.pop(o, "#%s .wtag" % sid, t1 + 0.3, "chime", 0.16)


def k_setup(o, sid, bs, sp, arrive):
    """An app window: each part switched on in turn."""
    rows, done = sp["rows"], sp.get("done")
    t0, t1 = span(bs, arrive, 0.5 if done else 0)
    body = "".join('<div class="wsr r%d"><span>%s</span><div class="wsw"><i></i></div></div>' % (k, esc(r)) for k, r in enumerate(rows))
    o.h('<div class="card wapp" style="left:80px;top:580px;width:920px"><div class="wab"><i></i><i></i><i></i><b>%s</b></div>%s</div>' % (esc(sp.get("app", "")), body))
    for k in range(len(rows)):
        t = spread(t0, t1, len(rows), k)
        o.j("TL.to('#%s .r%d .wsw',{backgroundColor:'#0B7955',duration:.2},%.3f); TL.to('#%s .r%d .wsw i',{x:56,duration:.25,ease:'back.out(2)'},%.3f); TL.to('#%s .r%d',{backgroundColor:'rgba(11,121,85,.08)',duration:.2},%.3f);",
            sid, k, t, sid, k, t, sid, k, t)
        o.cue("tick", t, 0.2)
    if done:
        o.h('<div class="ytag wtag" style="left:80px;top:%dpx">%s %s</div>' % (580 + 110 + len(rows) * 116 + 40, M.check(40, "#15191F"), esc(done)))
        M.pop(o, "#%s .wtag" % sid, t1 + 0.1, "chime", 0.16)


KINDS = {"books": k_books, "revenue": k_revenue, "table": k_table, "review": k_review, "runway": k_runway, "findings": k_findings,
         "form": k_form, "send": k_send, "stack": k_stack, "calendar": k_calendar, "compare": k_compare, "setup": k_setup}


def sh_work(o, sid, bs, sp, arrive, step):
    """One thing the offer covers, shown being done. sp["kind"] picks the scene."""
    M.title(o, esc(sp["title"]), step)
    if sp["kind"] not in KINDS:
        raise ValueError("unknown work kind %s (%s)" % (sp["kind"], ", ".join(KINDS)))
    KINDS[sp["kind"]](o, sid, bs, sp, arrive)


def sh_recap(o, sid, bs, sp, arrive, step):
    """Everything the offer covers, ticked off at once, and the offer's name: the price comes next."""
    b = bs[0]
    M.title(o, sp["title"], None, 392, sp.get("size", 72))
    rows = "".join('<div class="wrcr r%d"><div class="box">%s</div><span>%s</span></div>' % (k, M.check(40), esc(r)) for k, r in enumerate(sp["rows"]))
    o.h('<div class="card wrecap" style="left:70px;top:%dpx;width:940px">%s</div>' % (sp.get("top", 600), rows))
    o.j("gsap.set('#%s .wrecap .box svg',{scale:0,opacity:0});", sid)
    n = len(sp["rows"])
    t0, t1 = arrive, max(arrive + 0.6, b.end - 0.6)
    for k in range(n):
        t = t0 + (t1 - t0) * k / max(1, n)
        o.j("TL.to('#%s .r%d .box svg',{scale:1,opacity:1,duration:.25,ease:'back.out(2.2)'},%.3f); TL.to('#%s .r%d',{backgroundColor:'rgba(11,121,85,.09)',duration:.2},%.3f);", sid, k, t, sid, k, t)
        o.cue("tick", t, 0.18)


CSS = """
/* work scenes */
.wdoc{padding:34px 30px}
.wdn{font-family:'Fraunces';font-weight:700;font-size:44px;line-height:1.05;color:#15191F;height:84px;display:flex;align-items:flex-end}
.wr{display:flex;align-items:center;gap:14px;height:66px;margin-top:14px;padding:0 14px;border-radius:12px}
.wr i{display:block;height:16px;border-radius:8px;background:#E2DBCC}
.wr b{display:block;height:22px;border-radius:8px;background:#B9B2A2;margin-left:auto}
.wt{width:40px;display:grid;place-items:center}
.wchips{position:absolute;display:flex;flex-wrap:wrap;gap:16px;width:960px}
.wchip{display:inline-flex;align-items:center;gap:12px;padding:16px 26px;border-radius:999px;background:#FFFFFF;border:4px solid #15191F;box-shadow:6px 6px 0 #15191F;font-weight:800;font-size:36px;color:#15191F;white-space:nowrap}
.wrev{padding:34px 34px}
.wrl{font-family:'Fraunces';font-weight:700;font-size:48px;color:#15191F;height:60px}
.wblk{position:absolute;left:44px;right:44px;bottom:44px;height:250px;border-radius:24px;background:#FFFDF2;border:4px dashed #15191F;display:grid;place-items:center;overflow:hidden}
.wblk.tall{height:330px}
.wfill{position:absolute;left:0;right:0;bottom:0;top:0;background:#FFD84D}
.wblk b{position:relative;font-family:'Fraunces';font-weight:700;font-size:56px;color:#15191F}
.wmonths{position:absolute;display:grid;grid-template-columns:repeat(4,118px);gap:14px}
.wmo{height:120px;border-radius:18px;background:#FFFFFF;border:4px solid #D8D2C4;position:relative}
.wmo span{position:absolute;left:14px;top:8px;font-weight:800;font-size:28px;color:#59606C}
.wbits{position:absolute;width:0;height:0}
.wbit{position:absolute;left:0;top:0;width:60px;height:60px;border-radius:14px;background:#FFD84D;border:4px solid #15191F}
.wtag{white-space:nowrap}
.wtab{padding:26px 30px 30px}
.wth{font-family:'Fraunces';font-weight:700;font-size:46px;color:#15191F;height:74px}
.wtr{display:flex;align-items:center;gap:18px;padding:0 16px;border-radius:14px;border-top:3px solid #E6E0D3}
.wtr em{font-style:normal;font-weight:800;font-size:36px;color:#15191F;white-space:nowrap}
.wtr i{display:block;height:16px;border-radius:8px;background:#E2DBCC;margin-left:auto}
.wtr i.wph{margin-left:0;flex:none}
.wbx{width:58px;height:58px;border-radius:14px;border:4px solid #15191F;background:#fff;display:grid;place-items:center;flex:none}
.wbx b{font-family:'Fraunces';font-weight:700;font-size:44px;color:#15191F;line-height:1}
.wsrc{padding:30px 28px}
.wsn{font-family:'Fraunces';font-weight:700;font-size:38px;line-height:1.08;color:#15191F}
.wpile{position:absolute;width:300px;height:400px}
.wmk{position:absolute;left:0;top:0;width:280px;height:340px;padding:26px 24px}
.wmk b{font-family:'Fraunces';font-weight:700;font-size:38px;color:#15191F}
.wmag{position:absolute;left:0;top:0;z-index:5;filter:drop-shadow(6px 8px 0 rgba(21,25,31,.25))}
.wpick{white-space:nowrap}
.wrd{padding:34px 40px}
.wls i{display:block;height:16px;border-radius:8px;background:#E2DBCC;margin-top:26px}
.whl{position:absolute;left:34px;height:36px;border-radius:6px;background:rgba(255,216,77,.75);mix-blend-mode:multiply}
.wnote{position:absolute;width:330px;font-family:'Caveat';font-weight:700;font-size:58px;line-height:.95;color:#0B7955}
.wrun{padding:34px 40px}
.wrh{display:flex;align-items:center;gap:16px}
.wrh b{font-family:'Fraunces';font-weight:700;font-size:52px;color:#15191F}
.wchart{position:absolute;left:40px;top:130px;width:880px;height:330px}
.wc{position:absolute;bottom:0;width:58px;border-radius:12px 12px 4px 4px;background:linear-gradient(180deg,#14A374,#0B7955);border:3px solid #15191F}
.wbase{position:absolute;left:0;right:0;bottom:-6px;height:5px;border-radius:3px;background:#15191F}
.wticks span{position:absolute;bottom:-26px;width:4px;height:16px;border-radius:2px;background:#59606C}
.wflag{position:absolute;bottom:-4px;width:190px;height:190px}
.wflag svg{position:absolute;left:0;bottom:0}
.wflag em{position:absolute;left:20px;top:22px;font-style:normal;font-weight:800;font-size:28px;color:#FFFFFF;white-space:nowrap}
.wsub{position:absolute;left:40px;bottom:34px;display:inline-flex;align-items:center;padding:12px 22px;border-radius:999px;background:#FDE8E5;border:3px solid #C23A2B;font-weight:800;font-size:34px;color:#C23A2B;white-space:nowrap}
.wfind{padding:36px 40px 30px}
.wfh{display:flex;align-items:center;gap:18px;height:100px}
.wfh b{font-family:'Fraunces';font-weight:700;font-size:66px;color:#C23A2B;line-height:1}
.wfr{display:flex;align-items:center;gap:14px;height:104px;margin-top:14px;padding:0 18px;border-radius:16px;border:3px solid #E6E0D3;background:#FFFFFF}
.wfl{font-weight:800;font-size:38px;color:#15191F;width:150px;white-space:nowrap}
.wfc{display:inline-flex;align-items:center;padding:10px 18px;border-radius:12px;background:#FFF3C2;border:3px solid #15191F;font-weight:800;font-size:30px;color:#15191F;white-space:nowrap}
.wcall{display:inline-flex;align-items:center;gap:16px;padding:22px 30px;border-radius:999px;box-shadow:8px 8px 0 #0B7955}
.wcall span{font-weight:800;font-size:38px;color:#15191F;white-space:nowrap}
.wform{padding:34px 34px;min-height:560px}
.wfn{font-family:'Fraunces';font-weight:700;font-size:52px;line-height:1.02;color:#15191F}
.wftag{display:inline-block;margin-top:12px;padding:8px 18px;border-radius:10px;background:#0B7955;color:#fff;font-weight:800;font-size:28px}
.wff{display:flex;align-items:center;gap:16px;margin-top:26px}
.wff i{display:block;height:14px;border-radius:7px;background:#E2DBCC;flex:none}
.wfb{flex:1;height:62px;border-radius:12px;border:3px solid #D8D2C4;background:#FFFDF2;padding:0 14px;display:flex;align-items:center}
.wfb b{display:block;height:20px;border-radius:6px;background:#3F4652}
.wppl{position:absolute;display:flex;flex-direction:column;gap:30px}
.wpp{width:130px;height:130px;border-radius:50%;background:#FFFFFF;border:4px solid #15191F;box-shadow:5px 5px 0 #15191F;display:grid;place-items:center}
.wit{width:250px;height:310px;padding:28px 24px}
.wit b,.wfly b{font-family:'Fraunces';font-weight:700;font-size:36px;line-height:1.05;color:#15191F}
.wfly{position:absolute;left:0;top:0;width:220px;height:270px;padding:24px 22px;z-index:6}
.wdst{width:380px;height:250px;display:flex;flex-direction:column;justify-content:center;padding:0 36px}
.wdst b{font-family:'Fraunces';font-weight:700;font-size:48px;line-height:1.05;color:#15191F;margin-top:14px}
.wok{position:absolute;right:24px;top:24px;width:64px;height:64px;border-radius:50%;background:#DDF1E7;border:3px solid #0B7955;display:grid;place-items:center}
.wrcpt{position:absolute;display:inline-flex;align-items:center;gap:16px;padding:22px 30px;border-radius:18px;background:#FFFFFF;border:4px solid #15191F;box-shadow:8px 8px 0 #15191F;font-weight:800;font-size:38px;color:#15191F;white-space:nowrap}
.wsk{height:520px;padding:30px 30px}
.wsk .mark{width:44px;height:44px;font-size:24px;border-radius:8px}
.wskn{font-family:'Fraunces';font-weight:700;font-size:46px;line-height:1.04;color:#15191F;margin-top:18px}
.wsks{font-weight:800;font-size:24px;letter-spacing:.12em;color:#59606C;text-transform:uppercase;margin-top:10px}
.wfold{white-space:nowrap}
.wcal{padding:30px 34px 34px}
.wch{display:flex;align-items:center;gap:16px;height:80px}
.wch b{font-family:'Fraunces';font-weight:700;font-size:50px;color:#15191F}
.wdays{display:grid;grid-template-columns:repeat(7,1fr);gap:12px;margin-top:10px}
.wdays span{text-align:center;font-weight:800;font-size:26px;color:#59606C}
.wgrid{display:grid;grid-template-columns:repeat(7,1fr);gap:12px;margin-top:12px}
.wcell{height:84px;border-radius:14px;background:#FFFFFF;border:3px solid #E2DBCC;position:relative}
.wcell svg{position:absolute;left:-6px;top:-6px;width:calc(100% + 12px);height:calc(100% + 12px);overflow:visible}
.wfrom{position:absolute;left:0;width:1080px;display:flex;justify-content:center;gap:20px}
.wsrcc{display:inline-flex;align-items:center;gap:12px;padding:14px 22px;border-radius:16px;background:#FFFFFF;border:3px solid #15191F;font-weight:800;font-size:32px;color:#15191F;white-space:nowrap}
.wcmp{padding:30px 34px}
.wcn{font-family:'Fraunces';font-weight:700;font-size:46px;color:#15191F}
.wbar{position:absolute;left:120px;right:120px;bottom:40px;border-radius:18px 18px 6px 6px;border:4px solid #15191F;background:linear-gradient(180deg,#F0A79F,#C23A2B)}
.wcmp.lo .wbar{background:linear-gradient(180deg,#14A374,#0B7955)}
.wapp{padding:0 0 26px;overflow:hidden}
.wab{display:flex;align-items:center;gap:12px;height:84px;padding:0 30px;background:#F3EFE6;border-bottom:4px solid #15191F}
.wab i{width:20px;height:20px;border-radius:50%;background:#FFFFFF;border:3px solid #15191F}
.wab b{margin-left:18px;font-weight:800;font-size:34px;color:#15191F}
.wsr{display:flex;align-items:center;justify-content:space-between;height:100px;margin:16px 26px 0;padding:0 24px;border-radius:16px;border:3px solid #E6E0D3}
.wsr span{font-weight:800;font-size:38px;color:#15191F}
.wsw{position:relative;width:116px;height:60px;border-radius:999px;background:#D8D2C4;border:3px solid #15191F;flex:none}
.wsw i{position:absolute;left:4px;top:4px;width:46px;height:46px;border-radius:50%;background:#FFFFFF;border:3px solid #15191F}
.wrecap{padding:26px 30px}
.wrcr{display:flex;align-items:center;gap:22px;padding:14px 18px;border-radius:16px}
.wrcr .box{width:62px;height:62px;border-radius:14px;border-width:4px}
.wrcr span{font-weight:800;font-size:40px;line-height:1.12;color:#15191F}
"""


M.SHOTS["work"] = sh_work
M.SHOTS["recap"] = sh_recap
M.CSS = M.CSS + CSS
