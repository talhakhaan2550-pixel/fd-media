"""Carousel slides (1080 x 1350, and 1080 x 1920 for the music reel) and story frames (1080 x 1920) in the new style.

The words come from the piece exactly as written. A slide may add a `visual`: a chart, card or map that shows the
slide's own figures again in a picture. Visuals restate the slide's words; they never add a fact.
"""
import re
from brand import esc, ic, ARROW, usmap, state_shape, photo_uri, shell, us_map, DISCLAIMER

MONTHS = "January|February|March|April|May|June|July|August|September|October|November|December"
FIG = re.compile(r"(\$[\d,.]+(?:\s?(?:million|billion|M|K)\b)?\+?|\d[\d,.]*%|\b\d{1,2} (?:" + MONTHS + r")(?: \d{4})?\b|\b\d{1,3}(?:,\d{3})+\b)")
COUNTABLE = re.compile(r"^(\$?)(\d{1,3}(?:,\d{3})*|\d+)$")


def emph_title(title, emph=None):
    """Colours one part of the title: emph when given (a substring, or "" for none), else the words after a colon,
    else the last two words of a title of three words or more."""
    t = str(title)
    if emph is None:
        m = FIG.search(t)
        if m and len(m.group(0)) >= 4:
            emph = m.group(0)
        elif ": " in t:
            emph = t.split(": ", 1)[1]
        else:
            words = t.split()
            emph = " ".join(words[-2:]) if len(words) >= 3 else ""
    if emph and emph in t:
        i = t.rindex(emph)
        return esc(t[:i]) + '<span class="em">' + esc(emph) + "</span>" + esc(t[i + len(emph):])
    return esc(t)


def bold_body(body, extra=()):
    """Bolds the figures and dates in a body, plus any phrases listed in bold."""
    s = esc(body)
    marks = []
    for m in FIG.finditer(str(body)):
        marks.append(m.group(0))
    for b in extra or ():
        if b and b in str(body):
            marks.append(b)
    for m in sorted(set(marks), key=len, reverse=True):
        e = esc(m)
        s = re.sub(r"(?<![\w>])" + re.escape(e) + r"(?![\w<])", "\u0000" + e + "\u0001", s, count=0)
    return s.replace("\u0000", "<b>").replace("\u0001", "</b>").replace("<b><b>", "<b>").replace("</b></b>", "</b>")


def value_html(v, cls="big", style="", d=1.0, extra_cls=""):
    """A big figure; plain numbers and dollar amounts count up when animated."""
    v = str(v)
    m = COUNTABLE.match(v)
    attrs = ' data-a="pop" data-d="%.2f"' % d
    if m:
        to = m.group(2).replace(",", "")
        attrs = ' data-a="count" data-to="%s" data-pre="%s" data-d="%.2f"' % (to, m.group(1), d)
    return '<div class="%s %s fit" style="%s"%s>%s</div>' % (cls, extra_cls, style, attrs, esc(v))


def tone_cls(t):
    return {"amber": "tone-amber", "red": "tone-red", "white": "tone-white"}.get(t or "", "")


# ---------------------------------------------------------------- visual blocks
def v_map(v, mode, d):
    w = 920 if mode == "post" else 700
    labels = v.get("labels")
    return '<div class="vis" style="display:flex;justify-content:center;margin-top:20px">%s</div>' % usmap(w, v.get("states", []), labels=labels, d=d, uid="c")


def v_stats(v, mode, d):
    items = v.get("items", [])[:3]
    n = len(items) or 1
    size = {1: 200, 2: 150, 3: 116}[n] if mode == "post" else {1: 160, 2: 120, 3: 92}[n]
    cards = ""
    for i, it in enumerate(items):
        hl = " hl" if it.get("highlight", i == 0) else ""
        cards += ('<div class="card%s statc" data-a="up" data-d="%.2f"><div class="label"%s>%s</div><div class="sp"></div>%s%s</div>'
                  % (hl, d + i * 0.12, "" if hl else ' style="color:#9AA6B6"', esc(it.get("label", "")),
                     value_html(it.get("value", ""), style="font-size:%dpx;margin-top:18px" % size, d=d + 0.25 + i * 0.12, extra_cls=tone_cls(it.get("tone"))),
                     ('<div class="small" style="margin-top:14px">%s</div>' % esc(it["note"])) if it.get("note") else ""))
    return '<div class="row vis" style="gap:20px;align-items:stretch">%s</div>' % cards


def cal_html(month, day, sub="", d=0.9, width=176):
    ml = len(str(month))
    mstyle = "" if ml <= 9 else "font-size:15px;letter-spacing:.12em;padding:14px 4px 13px"
    return ('<div class="cal" style="width:%dpx" data-a="pop" data-d="%.2f"><div class="m" style="%s">%s</div><div class="d">%s</div>%s</div>'
            % (width, d, mstyle, esc(month), esc(day), ('<div class="s">%s</div>' % esc(sub)) if sub else '<div class="s"></div>'))


def v_date(v, mode, d):
    right = ""
    if v.get("label"):
        right += '<div class="label">%s</div>' % esc(v["label"])
    if v.get("text"):
        right += '<div style="font-family:SS4;font-weight:600;font-size:40px;line-height:1.12;color:#F4F8F6">%s</div>' % esc(v["text"])
    for i, c in enumerate(v.get("chips", [])):
        c = c if isinstance(c, dict) else {"text": c}
        right += '<span class="chip" data-a="left" data-d="%.2f">%s%s</span>' % (d + 0.35 + i * 0.12, ic(c.get("icon", "check"), 30), esc(c["text"]))
    return ('<div class="card vis" style="padding:26px 30px;display:flex;align-items:center;gap:34px" data-a="up" data-d="%.2f">%s'
            '<div style="display:flex;flex-direction:column;gap:14px;align-items:flex-start">%s</div></div>'
            % (d, cal_html(v.get("month", ""), v.get("day", ""), v.get("sub", ""), d + 0.25), right))


def v_bars(v, mode, d):
    bars = v.get("bars", [])
    add = v.get("add")
    amounts = [float(b.get("amount", 1)) for b in bars]
    top = max(amounts + ([amounts[-1] + float(add.get("amount", 0))] if add and amounts else [])) or 1
    cols, labels = "", ""
    H = "var(--ch,330px)"
    for i, b in enumerate(bars):
        frac = float(b.get("amount", 1)) / top
        tag = '<div class="label" style="margin-bottom:8px">%s</div>' % esc(b["tag"]) if b.get("tag") else ""
        cols += ('<div class="col">%s%s<div class="barv" style="height:calc(%s*%.3f)" data-a="bar" data-d="%.2f"></div></div>'
                 % (tag, value_html(b.get("value", ""), cls="val", d=d + 0.35 + i * 0.15), H, frac, d + 0.25 + i * 0.15))
        labels += '<div class="col xl">%s</div>' % esc(b.get("label", ""))
    if add and bars:
        base = float(bars[-1].get("amount", 1)) / top
        inc = float(add.get("amount", 0)) / top
        i = len(bars)
        cols += ('<div class="col"><div class="val" data-a="fade" data-d="%.2f">%s</div>'
                 '<div class="barv" style="height:calc(%s*%.3f - 6px);border-radius:16px 16px 4px 4px;background:linear-gradient(180deg,#B5F9DE,#2BC48D)" data-a="bar" data-d="%.2f"></div>'
                 '<div class="barg" style="height:calc(%s*%.3f);margin-top:6px" data-a="bar" data-d="%.2f"></div></div>'
                 % (d + 0.85, esc(add.get("value", "")), H, inc, d + 0.75, H, base, d + 0.55))
        labels += '<div class="col xl">%s</div>' % esc(add.get("label", ""))
    return ('<div class="card vis" style="padding:30px 34px 28px" data-a="up" data-d="%.2f"><div class="chart">%s</div>'
            '<div class="row" style="gap:26px;border-top:1px solid rgba(255,255,255,.16)">%s</div></div>' % (d, cols, labels))


def v_quote(v, mode, d):
    return ('<div class="card vis" style="padding:34px 36px 38px;display:flex;gap:26px;align-items:flex-start;'
            'background:linear-gradient(180deg,rgba(21,183,129,.17),rgba(21,183,129,.04));border-color:rgba(60,220,160,.38)" data-a="up" data-d="%.2f">'
            '<div class="qm">“</div><div>%s<div class="quote">%s”</div></div></div>'
            % (d, ('<div class="label" style="margin-bottom:14px">%s</div>' % esc(v["source"])) if v.get("source") else "", esc(v.get("text", ""))))


def v_hero(v, mode, d):
    size = 300 if mode == "post" else 230
    shape = ""
    if v.get("state") in us_map()["states"]:
        shape = '<div class="heroshape">%s</div>' % state_shape(v["state"], 380 if mode == "post" else 290, d=d - 0.2)
    return ('<div class="vis" style="position:relative">%s<div class="label" data-a="fade" data-d="%.2f">%s</div>%s%s</div>'
            % (shape, d, esc(v.get("label", "")), value_html(v.get("value", ""), style="font-size:%dpx;margin-top:4px" % size, d=d, extra_cls=tone_cls(v.get("tone"))),
               ('<div class="small" style="margin-top:12px">%s</div>' % esc(v["note"])) if v.get("note") else ""))


def v_chips(v, mode, d):
    out = ""
    for i, c in enumerate(v.get("items", [])):
        c = c if isinstance(c, dict) else {"text": c}
        out += '<span class="chip" data-a="left" data-d="%.2f">%s%s</span>' % (d + 0.3 + i * 0.12, ic(c.get("icon", "check"), 32), esc(c["text"]))
    return ('<div class="card vis" style="padding:26px 30px;display:flex;flex-direction:column;gap:14px;align-items:flex-start" data-a="up" data-d="%.2f">%s%s</div>'
            % (d, ('<div class="label" style="color:#9AA6B6;margin-bottom:6px">%s</div>' % esc(v["label"])) if v.get("label") else "", out))


def v_threshold(v, mode, d):
    lines = v.get("lines", [])[:2]
    pos = [84, 56][:len(lines)]
    out = ""
    for i, (ln, p) in enumerate(zip(lines, pos)):
        out += ('<div class="thr" style="bottom:%d%%" data-a="barx" data-d="%.2f"><span><b>%s</b><i>%s</i></span></div>'
                % (p, d + 0.5 + i * 0.15, esc(ln.get("value", "")), esc(ln.get("note", ""))))
    bars = v.get("bars", [{}, {}, {"dashed": True}])[:4]
    low = pos[-1] if pos else 50
    for i, b in enumerate(bars):
        hgt = low + 11 + (i % 3) * 2
        out += ('<div class="ibar%s" style="left:%.1f%%;width:17%%;height:%d%%" data-a="bar" data-d="%.2f"></div>'
                % (" exp" if b.get("dashed") else "", 2 + i * 21, hgt, d + 0.25 + i * 0.12))
    groups, x = "", 2
    for g in v.get("groups", []):
        span = int(g.get("span", 1))
        groups += ('<div class="xl" style="position:absolute;left:%.1f%%;width:%.1f%%;text-align:center;line-height:1.25">%s</div>'
                   % (x, 21 * span - 4, esc(g.get("label", ""))))
        x += 21 * span
    return ('<div class="card vis" style="padding:56px 34px 22px" data-a="up" data-d="%.2f"><div class="inc">%s</div>'
            '<div style="position:relative;height:64px;border-top:1px solid rgba(255,255,255,.18)">%s</div></div>' % (d, out, groups))


def v_split(v, mode, d):
    L, R = v.get("left", {}), v.get("right", {})
    items = ""
    for i, it in enumerate(L.get("items", [])):
        if i:
            items += '<span style="color:#8C99AB;font-size:24px;padding-left:6px">%s</span>' % esc(L.get("joiner", "or"))
        items += '<span class="chip" data-a="left" data-d="%.2f">%s%s</span>' % (d + 0.3 + i * 0.15, ic(L.get("icon", "person"), 30), esc(it))
    left = ('<div class="card feeW" style="flex:1;gap:16px" data-a="up" data-d="%.2f"><div class="label" style="color:#9AA6B6;margin-bottom:8px">%s</div>%s</div>'
            % (d, esc(L.get("label", "")), items))
    crossed = " crossed" if R.get("crossed", True) else ""
    right = ('<div class="card feeW" style="flex:.85;align-items:center;text-align:center" data-a="up" data-d="%.2f">'
             '<div class="label" style="color:%s;align-self:flex-start">%s</div><div class="sp"></div><div class="house%s" data-a="pop" data-d="%.2f">%s</div>'
             '<div style="font-family:SS4;font-weight:600;font-size:32px;margin-top:16px;color:#fff">%s</div></div>'
             % (d + 0.12, "#FF9EA2" if crossed else "#86E9C2", esc(R.get("label", "")), crossed, d + 0.4, ic(R.get("icon", "house"), 80, "#E9F2EE", 2.2), esc(R.get("title", ""))))
    return '<div class="row vis" style="gap:20px;align-items:stretch">%s%s</div>' % (left, right)


def v_tiles(v, mode, d):
    cards = ""
    for i, n in enumerate(v.get("items", [])[:4]):
        cards += ('<div class="lic" data-a="up" data-d="%.2f"><div style="display:flex;align-items:center;justify-content:space-between">'
                  '<div class="label">%s</div>%s</div><div class="n big">%s</div></div>' % (d + i * 0.13, esc(v.get("label", "")), ic(v.get("icon", "badge"), 40), esc(n)))
    status = ""
    st = v.get("status")
    if st:
        status = ('<div class="card hl" style="margin-top:20px;padding:26px 30px;display:flex;align-items:center;gap:22px" data-a="up" data-d="%.2f">'
                  '<div class="seal" style="width:84px;height:84px" data-a="pop" data-d="%.2f">%s</div><div><div class="label">%s</div>'
                  '<div style="font-family:SS4;font-weight:600;font-size:44px;color:#fff;margin-top:4px">%s</div></div></div>'
                  % (d + 0.45, d + 0.65, ic("check", 42, "#04150E", 4), esc(st.get("label", "")), esc(st.get("text", ""))))
    return '<div class="vis"><div class="row" style="gap:20px">%s</div>%s</div>' % (cards, status)


def v_list(v, mode, d):
    rows = ""
    for i, it in enumerate(v.get("items", [])):
        it = it if isinstance(it, dict) else {"text": it}
        rows += ('<div class="crow" data-a="left" data-d="%.2f"><div class="ico">%s</div><div class="t">%s</div><div class="sp"></div><div style="color:#6AF3C0">%s</div></div>'
                 % (d + 0.35 + i * 0.14, ic(it.get("icon", "check"), 36), esc(it["text"]), ARROW))
    head = ""
    if v.get("title"):
        head = ('<div style="display:flex;align-items:center;gap:24px;margin-bottom:22px"><div class="seal" data-a="pop" data-d="%.2f">%s</div>'
                '<div style="font-family:SS4;font-weight:600;font-size:46px;color:#fff">%s</div></div>' % (d + 0.25, ic("check", 50, "#04150E", 4), esc(v["title"])))
    return '<div class="cred vis" data-a="up" data-d="%.2f">%s%s</div>' % (d, head, rows)


def v_steps(v, mode, d):
    rows = ""
    for i, it in enumerate(v.get("items", [])[:5]):
        rows += ('<div class="step" data-a="left" data-d="%.2f"><div class="stepn">%d</div><div class="stept">%s</div></div>'
                 % (d + 0.25 + i * 0.15, i + 1, esc(it)))
    return '<div class="card vis" style="padding:28px 32px" data-a="up" data-d="%.2f">%s</div>' % (d, rows)


def v_compare(v, mode, d):
    def side(s, dd, hl):
        items = "".join('<div class="cmpi">%s<span>%s</span></div>' % (ic("check", 26), esc(x)) for x in s.get("items", []))
        val = value_html(s["value"], style="font-size:%dpx;margin:16px 0 6px" % (110 if mode == "post" else 84), d=dd + 0.3, extra_cls=tone_cls(s.get("tone"))) if s.get("value") else ""
        return ('<div class="card%s feeW" style="flex:1" data-a="up" data-d="%.2f"><div style="display:flex;align-items:center;gap:14px">%s'
                '<div style="font-family:SS4;font-weight:600;font-size:36px;color:#fff">%s</div></div>%s%s%s</div>'
                % (" hl" if hl else "", dd, ic(s.get("icon", "doc"), 40), esc(s.get("title", "")), val,
                   ('<div class="small">%s</div>' % esc(s["note"])) if s.get("note") else "", items))
    j = esc(v.get("join", "vs"))
    return ('<div class="row vis" style="gap:20px;align-items:stretch;position:relative">%s<div class="vsj" data-a="pop" data-d="%.2f">%s</div>%s</div>'
            % (side(v.get("left", {}), d, True), d + 0.4, j, side(v.get("right", {}), d + 0.15, False)))


def v_checklist(v, mode, d):
    rows = ""
    items = v.get("items") or [None] * int(v.get("rows", 4))
    widths = [78, 62, 84, 55, 70, 66]
    for i, it in enumerate(items[:6]):
        txt = ('<span style="font-size:26px;color:#E5ECE9">%s</span>' % esc(it)) if it else '<i style="width:%d%%"></i>' % widths[i % 6]
        rows += '<div class="ckr"><div class="box on" data-a="pop" data-d="%.2f">%s</div>%s</div>' % (d + 0.4 + i * 0.15, ic("check", 30, "#04150E", 4), txt)
    tag = ('<div class="kicker" style="font-size:18px;padding:8px 14px"><i></i>%s</div>' % esc(v["tag"])) if v.get("tag") else ""
    return ('<div class="card hl vis" style="padding:30px 34px" data-a="up" data-d="%.2f"><div style="display:flex;align-items:center;justify-content:space-between;gap:20px">'
            '<div style="font-family:SS4;font-weight:600;font-size:40px;color:#fff">%s</div>%s</div>%s</div>' % (d, esc(v.get("title", "")), tag, rows))


VISUALS = {"map": v_map, "stats": v_stats, "date": v_date, "bars": v_bars, "quote": v_quote, "hero": v_hero, "chips": v_chips,
           "threshold": v_threshold, "split": v_split, "tiles": v_tiles, "list": v_list, "steps": v_steps, "compare": v_compare,
           "checklist": v_checklist}


def visual(v, mode, d=0.6):
    if not v:
        return ""
    fn = VISUALS.get(v.get("type"))
    if not fn:
        raise ValueError("unknown visual type %s" % v.get("type"))
    return fn(v, mode, d)


def visuals(s, mode, d=0.6):
    """A slide may carry one visual, or two stacked (visual and visual2)."""
    out = visual(s.get("visual"), mode, d)
    if s.get("visual2"):
        out += '<div style="height:20px"></div>' + visual(s.get("visual2"), mode, d + 0.35)
    return out


EXTRA = """
.vis{flex:none;min-width:0}
.statc,.feeW,.col,.lic,.card{min-width:0}
.loc{position:absolute;right:0;top:-8px}
.hw{max-width:760px}
.statc{flex:1;padding:28px 30px 30px;display:flex;flex-direction:column;min-height:250px}
.reel .statc{min-height:230px;padding:22px 24px!important}
.feeW{flex:1;padding:28px 30px 30px;display:flex;flex-direction:column}
.chart{display:flex;gap:26px;align-items:flex-end;height:calc(var(--ch,330px) + 92px)}
.reel .chart{--ch:200px}
.col{flex:1;display:flex;flex-direction:column;align-items:stretch;min-width:0}
.barv{border-radius:16px 16px 6px 6px;background:linear-gradient(180deg,#3FE0A6 0%,#0F8C61 100%);box-shadow:0 0 40px rgba(21,183,129,.32),inset 0 1px 0 rgba(255,255,255,.4)}
.barg{border-radius:6px;background:rgba(255,255,255,.06);border:1px dashed rgba(255,255,255,.25)}
.val{font-family:'SS4';font-weight:700;font-size:60px;letter-spacing:-.02em;color:#fff;margin-bottom:12px;line-height:1;white-space:nowrap}
.reel .val{font-size:46px}
.xl{font-size:22px;line-height:1.3;color:#B4BFCC;margin-top:16px}
.reel .xl{font-size:19px}
.heroshape{position:absolute;right:-10px;top:-40px;z-index:-1;opacity:.95}
.cred{position:relative;border-radius:34px;padding:34px 36px 30px;background:linear-gradient(145deg,rgba(255,255,255,.12),rgba(255,255,255,.03) 55%,rgba(21,183,129,.10));
 border:1px solid rgba(255,255,255,.18);box-shadow:0 50px 100px rgba(0,0,0,.5),0 0 0 1px rgba(21,183,129,.15),inset 0 1px 0 rgba(255,255,255,.2);overflow:hidden}
.crow{display:flex;align-items:center;gap:20px;padding:20px 0;border-top:1px solid rgba(255,255,255,.12)}
.crow .t{font-family:'SS4';font-weight:600;font-size:36px;color:#F4F8F6}
.reel .crow{padding:14px 0}.reel .crow .t{font-size:30px}.reel .ico{width:54px;height:54px}
.inc{position:relative;height:var(--ih,400px)}
.reel .inc{--ih:230px}
.ibar{position:absolute;bottom:0;border-radius:14px 14px 4px 4px;background:linear-gradient(180deg,#3FE0A6,#0F8C61);box-shadow:0 0 36px rgba(21,183,129,.3),inset 0 1px 0 rgba(255,255,255,.4)}
.ibar.exp{background:repeating-linear-gradient(135deg,rgba(63,224,166,.22) 0 10px,rgba(63,224,166,.08) 10px 20px);border:2px dashed rgba(106,243,192,.7);box-shadow:none}
.thr{position:absolute;left:0;right:0;border-top:2px dashed rgba(255,255,255,.55)}
.thr span{position:absolute;right:0;bottom:8px;width:34%;display:flex;flex-direction:column;gap:2px;text-align:right}
.thr span b{font-family:'SS4';font-weight:700;font-size:34px;color:#fff;letter-spacing:-.01em}
.thr span i{font-style:normal;font-size:20px;line-height:1.25;color:#B4BFCC}
.reel .thr span b{font-size:28px}.reel .thr span i{font-size:18px}
.house{width:170px;height:170px;border-radius:50%;border:2px dashed rgba(255,255,255,.35);display:grid;place-items:center;position:relative;flex:none}
.reel .house{width:130px;height:130px}
.house.crossed:after{content:"";position:absolute;width:150%;height:3px;background:#FF7A7F;transform:rotate(-38deg);box-shadow:0 0 16px rgba(255,90,95,.6);border-radius:3px}
.lic{flex:1;border-radius:26px;padding:24px 24px 26px;background:linear-gradient(160deg,rgba(255,255,255,.11),rgba(255,255,255,.025));border:1px solid rgba(106,243,192,.35);
 box-shadow:0 30px 70px rgba(0,0,0,.45),inset 0 1px 0 rgba(255,255,255,.16);display:flex;flex-direction:column}
.lic .n{font-family:'SS4';font-weight:700;font-size:190px;line-height:.9;letter-spacing:-.04em;margin-top:50px;margin-bottom:10px}
.reel .lic .n{font-size:110px;margin-top:20px}
.step{display:flex;align-items:center;gap:22px;padding:14px 0}
.stepn{width:58px;height:58px;border-radius:50%;display:grid;place-items:center;background:#0B7955;color:#fff;font-family:SS4;font-weight:700;font-size:30px;flex:none;
 box-shadow:0 0 0 6px rgba(21,183,129,.15)}
.stept{font-size:28px;line-height:1.3;color:#E9F0EC}
.cmpi{display:flex;align-items:flex-start;gap:12px;margin-top:14px;font-size:24px;line-height:1.3;color:#DCE4EA}
.vsj{position:absolute;left:50%;top:50%;transform:translate(-50%,-50%);width:76px;height:76px;border-radius:50%;display:grid;place-items:center;background:#0B7955;
 font-family:SS4;font-weight:700;font-size:30px;color:#fff;box-shadow:0 0 0 8px rgba(21,183,129,.18),0 20px 50px rgba(21,183,129,.4);z-index:3}
.ckr{display:flex;align-items:center;gap:20px;margin-top:22px}
.box{width:46px;height:46px;border-radius:12px;border:2px solid rgba(255,255,255,.35);display:grid;place-items:center;flex:none}
.box.on{background:#5CF0B6;border-color:#5CF0B6}
.ckr i{display:block;height:16px;border-radius:8px;background:rgba(255,255,255,.18)}
.reel .card{padding:22px 24px!important}
.reel .chip{font-size:22px;padding:10px 16px}
.reel .quote{font-size:40px!important}
.reel .cal{transform:scale(.86);transform-origin:0 50%;margin-right:-24px}
.reel .content{top:500px;bottom:520px;left:80px;right:160px}
.reel .top{top:400px;left:80px;right:160px}
.reel .dots{bottom:450px}
.reel h1{font-size:72px}.reel h2{font-size:62px}.reel .body{font-size:28px}
.reel .vis{margin-top:22px}
"""


def page_top(idx, total, count=None):
    c = count if count is not None else "<b>%02d</b> / %02d" % (idx + 1, total)
    return '<div class="top"><div class="brand"><div class="mark">FD</div>Finance Department</div><div class="count">%s</div></div>' % c


SWIPE = '<span style="display:inline-flex;align-items:center;gap:12px;color:#E8F0EC;font-weight:600">SWIPE ' + ARROW + "</span>"


def tag_html(text, n=None):
    num = ""
    if n:
        num = ('<span style="font-family:SS4;font-weight:700;font-size:26px;color:#fff;letter-spacing:0">%s</span>'
               '<span style="width:26px;height:1px;background:rgba(255,255,255,.35)"></span>' % esc(n))
    return '<div style="display:flex;align-items:center;gap:14px" data-a="fade" data-d="0.12">%s<span class="label">%s</span></div>' % (num, esc(text or ""))


def carousel_slide(s, idx, total, mode="post", disclaimer=False):
    lay = s.get("layout")
    if lay == "COVER":
        inner = ('<div class="kicker" data-a="down" data-d="0.1"><i></i>%s</div>' % esc(s["kicker"])) if s.get("kicker") else ""
        size = 82 if len(s.get("title", "")) > 60 else 96
        if mode == "reel":
            size = int(size * 0.84)
        inner += '<h1 style="margin-top:34px;font-size:%dpx" class="cvh" data-a="up" data-d="0.25">%s</h1>' % (size, emph_title(s["title"], s.get("emph")))
        if s.get("body"):
            inner += '<p class="body" style="margin-top:22px;font-size:34px" data-a="up" data-d="0.4">%s</p>' % bold_body(s["body"], s.get("bold"))
        inner += '<div class="sp"></div>' + visuals(s, mode, 0.55) + '<div class="sp" style="flex:.35"></div>'
        top = page_top(idx, total, SWIPE if mode == "post" else None)
    elif lay == "POINT":
        loc = ""
        st = s.get("state")
        if st in us_map()["states"]:
            loc = '<div class="loc" data-a="fade" data-d="0.2">%s</div>' % usmap(200, [st], pins=False, d=0.2, uid="l" + st)
        inner = loc + tag_html(s.get("tag", ""), s.get("num"))
        inner += '<h2 class="%s" style="margin-top:22px" data-a="up" data-d="0.25">%s</h2>' % ("hw" if loc else "", emph_title(s["title"], s.get("emph")))
        if s.get("body"):
            long = len(s["body"]) > 120
            inner += ('<p class="body" style="margin-top:24px;%s" data-a="up" data-d="0.4">%s</p>'
                      % ("" if long else "font-size:34px;line-height:1.42", bold_body(s["body"], s.get("bold"))))
        inner += '<div class="sp"></div>' + visuals(s, mode, 0.6)
        top = page_top(idx, total)
    elif lay == "CLOSE":
        inner = ('<div class="sp" style="flex:.18"></div><div class="mark" style="width:116px;height:116px;border-radius:16px;font-size:64px" data-a="pop" data-d="0.15">FD</div>'
                 '<h1 style="margin-top:44px;font-size:%dpx" data-a="up" data-d="0.35">%s</h1>' % (96 if mode == "post" else 80, emph_title(s["title"], s.get("emph"))))
        if s.get("body"):
            inner += '<p class="body" style="font-size:38px;line-height:1.35;margin-top:26px;color:#DCE4EA" data-a="up" data-d="0.55">%s</p>' % esc(s["body"])
        if s.get("cta"):
            inner += '<div style="margin-top:50px" data-a="pop" data-d="0.85"><span class="cta">%s %s</span></div>' % (esc(s["cta"]), ARROW)
        inner += '<div class="sp"></div>'
        if s.get("visual"):
            inner += visuals(s, mode, 0.9)
        else:
            inner += '<div class="zmap" style="display:flex;justify-content:center;margin:30px 0 22px;opacity:.7">%s</div>' % usmap(640 if mode == "post" else 470, [], pins=False, d=0.9, faint=True, uid="z")
        if disclaimer:
            inner += '<div class="fine" style="margin-top:14px" data-a="fade" data-d="1.1">%s</div>' % DISCLAIMER
        top = page_top(idx, total)
    else:
        raise ValueError("unknown carousel layout %s" % lay)
    dots = "".join('<span class="%s"></span>' % ("on" if i == idx else "") for i in range(total))
    body = '%s<div class="content">%s</div><div class="dots">%s</div>' % (top, inner, dots)
    w, h = (1080, 1350) if mode == "post" else (1080, 1920)
    return shell(body, w, h, EXTRA, "reel" if mode == "reel" else "")


STORY_CSS = """
.st .content{top:370px;bottom:330px;left:84px;right:84px}
.st .top{top:270px;left:84px;right:84px}
.st h1{font-size:88px;line-height:1.05}
.st .body{font-size:38px;line-height:1.38}
.photo{width:300px;height:300px;border-radius:50%;object-fit:cover;border:6px solid #15B781;box-shadow:0 0 0 12px rgba(21,183,129,.16),0 30px 80px rgba(0,0,0,.55);display:block}
.award{width:100%;height:auto;border-radius:28px;display:block;border:1px solid rgba(255,255,255,.2);box-shadow:0 40px 90px rgba(0,0,0,.55)}
.reply{display:flex;align-items:center;gap:18px;align-self:stretch;justify-content:center;padding:28px 36px;border-radius:999px;font-weight:600;font-size:36px;color:#04150E;
 background:linear-gradient(180deg,#5CF0B6,#16B07B);box-shadow:0 18px 54px rgba(21,183,129,.5),inset 0 1px 0 rgba(255,255,255,.5)}
"""


def story_frame(s, disclaimer=False):
    inner = '<div class="sp" style="flex:.3"></div>' if not s.get("visual") else ""
    photo = s.get("photo")
    if photo == "talha":
        inner += '<img class="photo" src="%s" data-a="pop" data-d="0.15">' % photo_uri("talha")
        inner += '<div style="height:44px"></div>'
    elif photo == "award":
        inner += '<img class="award" src="%s" data-a="up" data-d="0.15">' % photo_uri("award")
        inner += '<div style="height:44px"></div>'
    if s.get("kicker"):
        inner += '<div class="kicker" data-a="down" data-d="0.2"><i></i>%s</div>' % esc(s["kicker"])
    t = s.get("title", "")
    size = 88 if len(t) <= 60 else (74 if len(t) <= 95 else 64)
    if photo:
        size = min(size, 76)
    inner += '<h1 style="margin-top:30px;font-size:%dpx" data-a="up" data-d="0.3">%s</h1>' % (size, emph_title(t, s.get("emph")))
    if s.get("body"):
        inner += '<p class="body" style="margin-top:26px" data-a="up" data-d="0.45">%s</p>' % bold_body(s["body"], s.get("bold"))
    inner += '<div class="sp"></div>'
    if s.get("visual"):
        inner += visuals(s, "post", 0.6) + '<div class="sp" style="flex:.4"></div>'
    if s.get("cta"):
        inner += '<div class="reply" data-a="pop" data-d="0.8">%s<span>%s</span></div>' % (ic("reply", 40, "#04150E", 3.2), esc(s["cta"]))
    if disclaimer:
        inner += '<div class="fine" style="margin-top:18px;text-align:center" data-a="fade" data-d="1">%s</div>' % DISCLAIMER
    body = '<div class="top"><div class="brand"><div class="mark">FD</div>Finance Department</div></div><div class="content">%s</div>' % inner
    return shell(body, 1080, 1920, EXTRA + STORY_CSS, "st")
