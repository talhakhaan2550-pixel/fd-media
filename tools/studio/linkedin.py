"""LinkedIn post images in the light look Talha chose on 15 November 2026 (a mix of options A and B):
warm paper, a Fraunces headline with one part on a yellow marker, one drawn object (a cheque, a bill, a
timeline, or any carousel visual), up to three points, and Talha's real photo, cut out on a yellow circle.

One 1080 by 1350 image per post (4:5, the tallest LinkedIn shows in the feed). Every word and figure on the
image comes from the post itself; the image never adds a fact.

Spec (a piece of format linkedin_image, content):
  kicker  the tag at the top right, up to 32 characters
  lead    optional line above the headline, up to 120 characters
  title   the headline, up to 60 characters, with \n where a line must break; emph is the part on the
          marker (default: as for slides)
  object  one drawn object: {"type": "cheque" | "bill" | "spread" | any carousel visual type, ...}
  points  optional title (up to 50 characters) and items (up to 3): mark (box, tick, cross, num),
          title (up to 40 characters), text (up to 150 characters)
"""
from brand import esc, shell, photo_uri, texture_uri, DISCLAIMER
import slides

W, H = 1080, 1350
LIMITS = {"kicker": 32, "lead": 120, "title": 60}

CSS = """
.li-tag{font-family:Jakarta;font-weight:700;font-size:17px;letter-spacing:.16em;text-transform:uppercase;padding:10px 18px;border:2.5px solid #15191F;border-radius:999px;color:#15191F;white-space:nowrap}
.content.li-col{top:148px;right:56px;bottom:112px;display:block;z-index:4}
.li-lead{font-family:Jakarta;font-weight:500;font-size:30px;line-height:1.36;color:#4D5562;max-width:900px;margin:0}
.li-h1{font-family:Fraunces;font-weight:700;line-height:1.04;letter-spacing:-.02em;color:#15191F;margin:12px 0 0;max-width:952px}
.li-h1 .em{font-style:italic;color:#15191F;background:linear-gradient(transparent 14%,#FFD84D 14%,#FFD84D 92%,transparent 92%);padding:0 12px;margin:0 -6px;-webkit-box-decoration-break:clone;box-decoration-break:clone;border-radius:6px}
.li-obj{position:relative;margin-top:30px}
.li-pts{position:relative;width:560px;margin-top:26px}
.li-pt-title{font-family:Jakarta;font-weight:700;font-size:24px;margin:0 0 16px;width:640px;color:#15191F}
.li-it{display:flex;gap:18px;margin-bottom:14px}
.li-mk{width:40px;height:40px;border:3.5px solid #15191F;border-radius:9px;flex:none;margin-top:2px;background:rgba(255,255,255,.6);display:grid;place-items:center;
 font-family:Fraunces;font-weight:700;font-size:22px;line-height:1;color:#15191F}
.li-mk.tick{background:#0B7955;border-color:#0B7955}
.li-mk.cross{background:#FFFFFF;border-color:#C23A2B}
.li-mk.num{border-radius:50%;background:#FFD84D}
.li-im{font-family:Fraunces;font-weight:700;font-size:30px;line-height:1.12;color:#15191F;margin:0}
.li-im s{text-decoration-color:#C23A2B;text-decoration-thickness:4px}
.li-id{font-family:Jakarta;font-weight:500;font-size:20px;line-height:1.4;color:#4D5562;margin:4px 0 0}
.li-circle{position:absolute;right:-130px;bottom:-150px;width:600px;height:600px;border-radius:50%;background:#FFD84D;z-index:2}
.li-photo{position:absolute;right:18px;bottom:0;width:470px;z-index:3;filter:drop-shadow(0 18px 30px rgba(60,45,20,.20))}
.li-name{position:absolute;right:52px;bottom:48px;background:#15191F;color:#fff;border-radius:18px;padding:13px 22px 12px;box-shadow:0 14px 30px rgba(14,17,22,.25);z-index:6;font-family:Jakarta}
.li-name b{display:block;font-weight:700;font-size:22px}
.li-name span{display:block;font-weight:500;font-size:16px;color:#C9CED6;margin-top:2px}
.li-disc{position:absolute;left:72px;bottom:46px;font-family:Jakarta;font-size:16px;line-height:1.38;color:#7A808A;width:420px;z-index:4}
.hand{font-family:Caveat;font-weight:700;color:#24418F;line-height:1}
.stampx{position:absolute;transform:rotate(-10deg);border:7px solid #C23A2B;border-radius:16px;padding:6px 24px 4px;font-family:Jakarta;font-weight:800;font-size:56px;
 letter-spacing:.03em;color:#C23A2B;opacity:.9;mix-blend-mode:multiply;white-space:nowrap;-webkit-mask-image:url(STAMP);mask-image:url(STAMP);-webkit-mask-size:100% 100%;mask-size:100% 100%;z-index:3}
/* cheque */
.ck{position:absolute;left:24px;top:12px;width:860px;height:268px;border-radius:14px;transform:rotate(-2.4deg);
 background:repeating-linear-gradient(115deg,rgba(11,121,85,.07) 0 2px,transparent 2px 10px),repeating-linear-gradient(25deg,rgba(11,121,85,.05) 0 1px,transparent 1px 13px),linear-gradient(180deg,#EFF7F2,#E2EEE6);
 border:1px solid rgba(11,121,85,.28);box-shadow:0 34px 60px rgba(70,55,30,.20),0 6px 14px rgba(70,55,30,.10);padding:20px 34px 16px;color:#2C3B34;font-family:Plex}
.ck-top{display:flex;justify-content:space-between;align-items:flex-start}
.ck .payer{font-weight:600;font-size:20px;letter-spacing:.16em}
.ck .payer i{display:block;width:180px;height:2px;background:rgba(44,59,52,.18);margin-top:12px}
.ck .no{font-family:PlexMono;font-size:18px;text-align:right;line-height:1.7}
.ck .no span{display:inline-block;width:150px;border-bottom:2px solid rgba(44,59,52,.45);margin-left:10px}
.ck-row{display:flex;align-items:flex-end;gap:16px;margin-top:12px}
.ck .lbl{font-weight:500;font-size:14px;letter-spacing:.08em;line-height:1.25}
.ck .line{flex:1;border-bottom:2px solid rgba(44,59,52,.5);height:30px}
.ck .amt{display:flex;align-items:center;gap:8px;font-size:26px;font-weight:600}
.ck .amt b{display:block;width:170px;height:48px;border:2px solid rgba(44,59,52,.45);border-radius:6px;background:rgba(255,255,255,.55)}
.ck-row2{display:flex;align-items:flex-end;gap:14px;margin-top:14px}
.ck-bottom{display:flex;justify-content:space-between;align-items:flex-end;margin-top:14px}
.ck .memo{display:flex;align-items:flex-end;gap:14px}
.ck .memo .hand{font-size:42px;border-bottom:2px solid rgba(44,59,52,.5);padding:0 40px 2px 6px}
.ck .sig{width:300px;border-bottom:2px solid rgba(44,59,52,.5);text-align:center}
.ck .sig .hand{font-size:54px;display:block;transform:rotate(-4deg)}
/* bill */
.bill{position:absolute;left:10px;top:8px;width:600px;background:#FFFFFF;border-radius:6px;transform:rotate(-1.8deg);padding:26px 32px 22px;
 box-shadow:0 30px 56px rgba(70,55,30,.20),0 5px 12px rgba(70,55,30,.10);font-family:Jakarta;color:#15191F}
.bill:before{content:"";position:absolute;left:0;right:0;top:0;height:10px;border-radius:6px 6px 0 0;background:#0B7955}
.bill-h{display:flex;justify-content:space-between;align-items:baseline;border-bottom:2px solid #15191F;padding-bottom:10px;margin-bottom:8px}
.bill-h b{font-family:Fraunces;font-weight:700;font-size:30px}
.bill-h span{font-weight:600;font-size:15px;letter-spacing:.12em;text-transform:uppercase;color:#59606C}
.bill-r{display:flex;justify-content:space-between;align-items:baseline;gap:20px;padding:7px 0;border-bottom:1.5px dashed rgba(21,25,31,.22);font-size:19px;font-weight:500;color:#3F4652}
.bill-r b{font-family:PlexMono;font-weight:400;font-size:21px;color:#15191F;white-space:nowrap}
.bill-t{display:flex;justify-content:space-between;align-items:baseline;padding-top:10px}
.bill-t span{font-weight:800;font-size:18px;letter-spacing:.12em;text-transform:uppercase}
.bill-t b{font-family:Fraunces;font-weight:700;font-size:56px;line-height:1}
.sticky{position:absolute;right:30px;top:40px;width:270px;min-height:210px;background:#FFE680;transform:rotate(4deg);padding:26px 22px 22px;display:flex;flex-direction:column;justify-content:center;align-items:flex-start;gap:10px;
 box-shadow:0 22px 34px rgba(70,55,30,.18),0 3px 8px rgba(70,55,30,.10);z-index:4}
.sticky:before{content:"";position:absolute;left:50%;top:-14px;width:110px;height:30px;transform:translateX(-50%) rotate(-3deg);background:rgba(255,255,255,.55);box-shadow:0 1px 3px rgba(0,0,0,.08)}
.sticky .sl{display:block;font-family:Jakarta;font-weight:800;font-size:15px;letter-spacing:.14em;text-transform:uppercase;color:#59606C}
.sticky .hand{display:inline;font-size:58px;color:#15191F;position:relative}
.sticky .strike{position:relative;display:inline-block;margin-top:8px}
.sticky .strike:after{content:"";position:absolute;left:-6px;right:-6px;top:56%;height:4px;border-radius:2px;background:#C23A2B;transform:rotate(-4deg);opacity:.92}
/* spread (a timeline of years) */
.tl{position:relative;background:#FFFFFF;border:3px solid #15191F;border-radius:20px;box-shadow:8px 8px 0 #15191F;padding:24px 30px 18px;width:936px;font-family:Jakarta;color:#15191F}
.tl-row{margin-bottom:18px}
.tl-lab{display:flex;align-items:baseline;gap:14px;margin-bottom:8px}
.tl-lab b{font-family:Fraunces;font-weight:700;font-size:28px}
.tl-lab span{font-weight:600;font-size:19px;color:#59606C}
.tl-track{position:relative;display:grid;grid-template-columns:repeat(var(--n),1fr);gap:6px;height:46px}
.tl-track i{display:block;border-radius:8px;background:rgba(21,25,31,.06);border:1.5px dashed rgba(21,25,31,.18)}
.tl-bar{position:absolute;top:0;bottom:0;left:0;border-radius:9px;border:3px solid #15191F;display:flex;align-items:center;padding:0 14px;font-weight:800;font-size:17px;white-space:nowrap}
.tl-bar.em{background:#0B7955;color:#fff;border-color:#0B7955}
.tl-bar.red{background:repeating-linear-gradient(135deg,#FFE6D3 0 12px,#FFD3B8 12px 24px);color:#15191F}
.tl-bar.yel{background:#FFD84D;color:#15191F}
.tl-axis{display:flex;justify-content:space-between;font-family:PlexMono;font-size:16px;color:#59606C;margin-top:-4px}
.ovis{width:936px}
""".replace("STAMP", texture_uri("stamp_mask"))


def title_size(t):
    if "\n" in t:
        n = max(len(x) for x in t.split("\n"))
        return 92 if n <= 14 else 86 if n <= 20 else 76 if n <= 26 else 66
    n = len(t)
    return 92 if n <= 26 else 84 if n <= 40 else 74 if n <= 52 else 66


def o_cheque(o):
    stamp = ('<div class="stampx" style="left:368px;top:106px">%s</div>' % esc(o["stamp"])) if o.get("stamp") else ""
    return ('<div class="li-obj" style="height:%dpx"><div class="ck">'
            '<div class="ck-top"><div class="payer">%s<i></i></div><div class="no">%s<br>DATE<span></span></div></div>'
            '<div class="ck-row"><span class="lbl">PAY TO THE<br>ORDER OF</span><span class="line"></span><span class="amt">$<b></b></span></div>'
            '<div class="ck-row2"><span class="line"></span><span class="lbl">DOLLARS</span></div>'
            '<div class="ck-bottom"><div class="memo"><span class="lbl">MEMO</span><span class="hand">%s</span></div>'
            '<div class="sig"><span class="hand">%s</span></div></div></div>%s</div>'
            % (o.get("height", 290), esc(o.get("payer", "")).upper(), esc(o.get("number", "No. 0001")), esc(o.get("memo", "")),
               esc(o.get("signature", "")), stamp))


def o_bill(o):
    rows = "".join('<div class="bill-r"><span>%s</span><b>%s</b></div>' % (esc(a), esc(b)) for a, b in o.get("rows", []))
    tot = o.get("total")
    tot = ('<div class="bill-t"><span>%s</span><b>%s</b></div>' % (esc(tot[0]), esc(tot[1]))) if tot else ""
    stamp = ('<div class="stampx" style="left:%dpx;top:%dpx;font-size:%dpx;border-width:%dpx">%s</div>'
             % (o.get("stamp_x", 96), o.get("stamp_y", 238), o.get("stamp_size", 40), 6 if o.get("stamp_size", 40) < 50 else 7, esc(o["stamp"]))) if o.get("stamp") else ""
    note = o.get("note")
    if note:
        words = esc(note["text"])
        if note.get("strike"):
            words = '<span class="strike"><span class="hand">%s</span></span>' % words
        else:
            words = '<span class="hand">%s</span>' % words
        note = '<div class="sticky"><span class="sl">%s</span>%s</div>' % (esc(note.get("label", "")), words)
    return ('<div class="li-obj" style="height:%dpx"><div class="bill"><div class="bill-h"><b>%s</b><span>%s</span></div>%s%s</div>%s%s</div>'
            % (o.get("height", 330), esc(o.get("title", "")), esc(o.get("sub", "")), rows, tot, stamp, note or ""))


def o_spread(o):
    n = int(o.get("years", 15))
    out = []
    for r in o.get("rows", []):
        span = max(1, min(n, int(r.get("span", 1))))
        width = "calc(%d * (100%% - %d * 6px) / %d + %d * 6px)" % (span, n - 1, n, span - 1)
        out.append('<div class="tl-row"><div class="tl-lab"><b>%s</b><span>%s</span></div><div class="tl-track" style="--n:%d">%s'
                   '<div class="tl-bar %s" style="width:%s">%s</div></div></div>'
                   % (esc(r.get("label", "")), esc(r.get("note", "")), n, "<i></i>" * n, esc(r.get("tone", "em")), width, esc(r.get("bar", ""))))
    axis = o.get("axis") or ["Year 1", "Year %d" % n]
    return ('<div class="li-obj"><div class="tl">%s<div class="tl-axis"><span>%s</span><span>%s</span></div></div></div>'
            % ("".join(out), esc(axis[0]), esc(axis[1])))


OBJECTS = {"cheque": o_cheque, "bill": o_bill, "spread": o_spread}

TICK = '<svg width="24" height="24" viewBox="0 0 24 24"><path d="M5 12.5l4.5 4.5L19 7.5" fill="none" stroke="#fff" stroke-width="3.4" stroke-linecap="round" stroke-linejoin="round"/></svg>'
CROSS = '<svg width="22" height="22" viewBox="0 0 24 24"><path d="M6 6l12 12M18 6L6 18" fill="none" stroke="#C23A2B" stroke-width="3.6" stroke-linecap="round"/></svg>'


def obj_html(o):
    if not o:
        return ""
    fn = OBJECTS.get(o.get("type"))
    if fn:
        return fn(o)
    return '<div class="li-obj"><div class="ovis">%s</div></div>' % slides.visual(o, "post", 0.0)


def points_html(p):
    if not p or not p.get("items"):
        return ""
    items = []
    for i, it in enumerate(p["items"][:3]):
        kind = it.get("mark", "box")
        inner = TICK if kind == "tick" else CROSS if kind == "cross" else str(i + 1) if kind == "num" else ""
        title = esc(it.get("title", ""))
        if it.get("strike"):
            title = "<s>%s</s>" % title
        text = ('<p class="li-id">%s</p>' % esc(it["text"])) if it.get("text") else ""
        items.append('<div class="li-it"><div class="li-mk %s">%s</div><div><p class="li-im">%s</p>%s</div></div>' % (esc(kind), inner, title, text))
    head = ('<p class="li-pt-title">%s</p>' % esc(p["title"])) if p.get("title") else ""
    return '<div class="li-pts">%s%s</div>' % (head, "".join(items))


def problems_in(spec):
    """Words over their limits, so a long line is cut in the spec, never squeezed on the image."""
    out = []
    for k, n in LIMITS.items():
        if len(spec.get(k) or "") > n:
            out.append("%s is %d characters, over %d" % (k, len(spec[k]), n))
    for i, it in enumerate((spec.get("points") or {}).get("items", [])):
        if len(it.get("title", "")) > 40:
            out.append("point %d title is over 40 characters" % (i + 1))
        if len(it.get("text", "")) > 150:
            out.append("point %d text is over 150 characters" % (i + 1))
    return out


def image(spec, disclaimer=True):
    title = spec["title"]
    lead = ('<p class="li-lead">%s</p>' % esc(spec["lead"])) if spec.get("lead") else ""
    h1 = '<h1 class="li-h1" style="font-size:%dpx">%s</h1>' % (title_size(title), slides.emph_title(title, spec.get("emph")).replace("\n", "<br>"))
    body = ('<div class="top"><div class="brand"><div class="mark">FD</div>Finance Department</div><div class="li-tag">%s</div></div>'
            '<div class="content li-col">%s%s%s%s</div>'
            '<div class="li-circle"></div><img class="li-photo" src="%s">'
            '<div class="li-name"><b>Muhammad Talha</b><span>Finance Department</span></div>%s'
            % (esc(spec.get("kicker", "")), lead, h1, obj_html(spec.get("object")), points_html(spec.get("points")),
               photo_uri("talha_sticker"), ('<div class="li-disc">%s</div>' % DISCLAIMER) if disclaimer else ""))
    return shell(body, W, H, CSS)
