"""Talha's personal LinkedIn background photo (1584 x 396) in the light look, two directions, and previews of each on
his profile with the new profile picture (Talha's cut-out photo on the yellow circle, the same picture as Instagram's).

    python3 tools/studio/linkedin_profile.py OUTDIR

Where LinkedIn covers the banner (measured on his profile, 15 November 2026): on a computer the banner shows at
792 x 198 and the photo (152 px) covers x 48 to 368 and y 204 down of the 1584 x 396 file; on phones the photo is
larger (about 524 px of the file, lower left), so every word sits right of x 610 or above y 110.
Every claim is the Claim Library's: FD-30 (the line), FD-01 (300+ founders), FD-12 (a 30 minute call), FD-03
(trained at BDO Ebrahim & Co.), FD-26 (Wyoming LLC or Delaware corporation), and the three areas the home page opens on.
"""
import base64, os, sys
import brand
from brand import esc
from capture import Browser

OUT = sys.argv[1] if len(sys.argv) > 1 else "/tmp/fd-linkedin"
SITE = "/home/claude/financedepartment"
W, H = 1584, 396

CSS = """
.slide{width:1584px;height:396px}.lay{position:absolute;z-index:5}
.lead{font-family:Fraunces;font-weight:600;font-size:31px;line-height:1.14;letter-spacing:-.012em;color:#15191F;text-wrap:balance}
.punch{font-family:Fraunces;font-weight:700;font-size:66px;line-height:1.02;letter-spacing:-.025em;color:#15191F;white-space:nowrap}
.punch .em{padding:0 .1em}
.cta2{display:inline-flex;align-items:center;gap:10px;padding:9px 18px 9px 20px;border-radius:999px;background:#FFD84D;border:2.5px solid #15191F;
 box-shadow:4px 4px 0 #15191F;font-family:Jakarta;font-weight:800;font-size:19px;color:#15191F;white-space:nowrap}
.url{font-family:Jakarta;font-weight:700;font-size:18px;color:#15191F;white-space:nowrap;padding-left:4px;border-bottom:2px solid #FFD84D}
.k2{align-self:flex-start;display:inline-flex;align-items:center;gap:9px;padding:6px 14px 6px 11px;border-radius:999px;border:2px solid #15191F;
 background:rgba(255,255,255,.65);font-family:Jakarta;font-weight:700;font-size:14px;letter-spacing:.15em;text-transform:uppercase;color:#15191F;white-space:nowrap}
.k2 i{width:10px;height:10px;border-radius:50%;background:#FFD84D;border:2px solid #15191F}
.lock{display:flex;align-items:center;gap:12px;font-family:SS4;font-weight:600;font-size:25px;color:#15191F;white-space:nowrap}
.lock .mark{width:40px;height:40px;border-radius:7px;font-size:22px}
/* the three service cards */
.svc{position:absolute;width:180px;height:236px;background:#FFFFFF;border:3px solid #15191F;border-radius:16px;box-shadow:6px 6px 0 #15191F;overflow:hidden;font-family:Jakarta;color:#15191F}
.svc .hd{display:flex;align-items:center;gap:8px;height:46px;padding:0 11px;border-bottom:3px solid #15191F;font-weight:800;font-size:12px;letter-spacing:.07em;white-space:nowrap;text-transform:uppercase;line-height:1.1}
.svc .bd{padding:12px 14px 0}
.svc .ln{display:flex;align-items:center;gap:8px;font-weight:700;font-size:14.5px;margin-top:9px;white-space:nowrap}
.svc .tk{width:20px;height:20px;border-radius:6px;background:#0B7955;display:grid;place-items:center;flex:none}
.bars{display:flex;align-items:flex-end;gap:9px;height:74px;padding:0 4px;margin-right:22px;border-bottom:2.5px solid #15191F}
.bars i{display:block;flex:1;border:2.5px solid #15191F;border-bottom:none;border-radius:6px 6px 0 0;background:#E3F1EA}
.bars i.y{background:#FFD84D}
.seal{position:absolute;width:132px;height:132px;border-radius:50%;background:#0B7955;border:3px solid #15191F;box-shadow:5px 5px 0 #15191F;
 display:flex;flex-direction:column;align-items:center;justify-content:center;color:#FFFFFF;z-index:9}
.seal b{font-family:Fraunces;font-weight:700;font-size:44px;line-height:.95;letter-spacing:-.02em}
.seal span{font-family:Jakarta;font-weight:800;font-size:12.5px;letter-spacing:.16em;text-transform:uppercase;color:#E3F1EA;margin-top:4px}
.seal:after{content:"";position:absolute;inset:7px;border-radius:50%;border:1.5px dashed rgba(255,255,255,.55)}
/* the record */
.stat{position:absolute;background:#FFFFFF;border:3px solid #15191F;border-radius:18px;box-shadow:6px 6px 0 #15191F;font-family:Jakarta;color:#15191F}
.logo{position:absolute;background:#FFFFFF;border:2.5px solid #15191F;border-radius:14px;display:flex;align-items:center;justify-content:center;padding:8px 14px;
 box-shadow:4px 4px 0 rgba(21,25,31,.9)}
.logo img{max-width:100%;max-height:44px;object-fit:contain}
"""

TICK = ('<span class="tk"><svg width="13" height="13" viewBox="0 0 24 24"><path d="M5 12.5l4.5 4.5L19 7.5" fill="none" stroke="#fff" '
        'stroke-width="3.6" stroke-linecap="round" stroke-linejoin="round"/></svg></span>')


def page(inner):
    return brand.shell(inner, W, H, extra_css=CSS)


def rings():
    """Thin rings around where LinkedIn puts the photo on a computer (centre 208, 364), with a soft yellow light."""
    circles = "".join('<circle cx="208" cy="364" r="%d" fill="none" stroke="rgba(21,25,31,%.2f)" stroke-width="2"%s/>'
                      % (r, a, ' stroke-dasharray="3 9" stroke-linecap="round"' if dash else "")
                      for r, a, dash in [(196, .16, False), (252, .13, True), (312, .10, False), (376, .08, True)])
    return ('<div class="lay" style="left:0;top:0;width:640px;height:396px;z-index:2;pointer-events:none">'
            '<div style="position:absolute;left:-112px;top:44px;width:640px;height:640px;border-radius:50%%;'
            'background:radial-gradient(closest-side,rgba(255,216,77,.42),rgba(255,216,77,0))"></div>'
            '<svg width="640" height="396" viewBox="0 0 640 396" style="position:absolute;inset:0">%s</svg></div>' % circles)


def lockup():
    return ('<div class="lay lock" style="left:56px;top:40px"><span class="mark">FD</span>Finance Department</div>')


def sparkle(x, y, size, rot=0):
    return ('<svg class="lay" width="%d" height="%d" viewBox="0 0 40 40" style="left:%dpx;top:%dpx;transform:rotate(%ddeg);z-index:6;overflow:visible">'
            '<path d="M20 2 C21.6 13 27 18.4 38 20 C27 21.6 21.6 27 20 38 C18.4 27 13 21.6 2 20 C13 18.4 18.4 13 20 2Z" fill="#FFD84D" '
            'stroke="#15191F" stroke-width="2.6" stroke-linejoin="round"/></svg>' % (size, size, x, y, rot))


def text_block(left=614, width=440):
    return ('<div class="lay" style="left:%dpx;top:0;width:%dpx;height:396px;display:flex;flex-direction:column;justify-content:center;gap:12px">'
            '<span class="k2"><i></i>For US founders</span>'
            '<div class="lead">Every startup or company needs a Finance Department.</div>'
            '<div class="punch"><span class="em">Here’s yours.</span></div>'
            '<div style="display:flex;flex-direction:column;align-items:flex-start;gap:10px;margin-top:6px"><span class="cta2">Book a 30 minute call %s</span>'
            '<span class="url">financedepartmentllc.com</span></div></div>') % (left, width, brand.ARROW.replace('width="32"', 'width="24"').replace('height="18"', 'height="14"'))


def card(x, y, rot, z, head_bg, head_fg, icon, label, body):
    return ('<div class="svc" style="left:%dpx;top:%dpx;transform:rotate(%sdeg);z-index:%d">'
            '<div class="hd" style="background:%s;color:%s">%s<span>%s</span></div><div class="bd">%s</div></div>'
            % (x, y, rot, z, head_bg, head_fg, brand.ic(icon, 22, head_fg, 3), esc(label), body))


def lines(items):
    return "".join('<div class="ln">%s%s</div>' % (TICK, esc(t)) for t in items)


def option_a():
    """The department: three service cards fanned out, and 300+ founders on a seal."""
    books = ('<div class="bars"><i style="height:38%"></i><i style="height:58%"></i><i style="height:47%"></i><i class="y" style="height:86%"></i></div>'
             + lines(["Books closed", "Tax return", "Payroll"]))
    usco = ('<div style="margin:-2px -4px 0;height:96px;display:flex;align-items:center;justify-content:center">%s</div>'
            % brand.usmap(150, states=("WY", "DE"), labels=False, anim=False, uid="a")) + lines(["Wyoming LLC", "Delaware corp"])
    raise_ = lines(["Model", "Cap table", "Data room"]) + (
        '<div style="margin-top:14px;height:8px;border-radius:99px;background:rgba(21,25,31,.08);overflow:hidden">'
        '<div style="width:100%;height:100%;background:#0B7955"></div></div>'
        '<div style="font-weight:800;font-size:12px;letter-spacing:.14em;margin-top:7px;color:#0B7955">INVESTOR READY</div>')
    cards = (card(1062, 100, -6, 6, "#0B7955", "#FFFFFF", "bars", "Books and tax", books)
             + card(1220, 66, 0, 7, "#FFD84D", "#15191F", "globe", "Your US company", usco)
             + card(1386, 102, 6, 8, "#E3F1EA", "#15191F", "chart", "Raising", raise_))
    seal = '<div class="seal" style="left:416px;top:34px;transform:rotate(-9deg)"><b>300+</b><span>founders</span></div>'
    return page(rings() + lockup() + text_block() + cards + seal + sparkle(540, 26, 30, 8) + sparkle(568, 82, 16, -12))


LOGOS = ["hoolii", "mcorp", "verifynova", "yild", "four-paws", "house-of-hasko"]


def logo_uri(name):
    return "data:image/webp;base64," + base64.b64encode(open(os.path.join(SITE, "src/assets/clients", name + ".webp"), "rb").read()).decode()


def option_b():
    """The record: 300+ founders, trained at BDO, and client logos."""
    stat = ('<div class="stat" style="left:1066px;top:40px;width:282px;height:132px;padding:12px 18px;display:flex;flex-direction:column;justify-content:center;gap:6px">'
            '<div style="font-weight:800;font-size:12.5px;letter-spacing:.14em;text-transform:uppercase;color:#0B7955">We have worked with</div>'
            '<div style="display:flex;align-items:baseline;gap:10px"><span style="font-family:Fraunces;font-weight:700;font-size:52px;line-height:1;letter-spacing:-.03em">'
            '<span class="em" style="padding:0 .08em">300+</span></span><span style="font-family:Fraunces;font-weight:700;font-size:22px">founders</span></div></div>')
    bdo = ('<div class="stat" style="left:1366px;top:40px;width:198px;height:132px;padding:14px 16px;display:flex;flex-direction:column;justify-content:center;gap:8px">'
           '<div style="display:flex;align-items:center;gap:10px">%s<span style="font-weight:800;font-size:13px;letter-spacing:.14em;text-transform:uppercase;color:#0B7955">Trained at</span></div>'
           '<div style="font-family:Fraunces;font-weight:700;font-size:24px;line-height:1.08;white-space:nowrap">BDO Ebrahim<br>&amp; Co.</div></div>') % brand.ic("badge", 28, "#0B7955", 2.6)
    tiles = ""
    for i, name in enumerate(LOGOS):
        cx, cy = 1066 + (i % 3) * 170, 196 + (i // 3) * 82
        tiles += '<div class="logo" style="left:%dpx;top:%dpx;width:158px;height:68px"><img src="%s"></div>' % (cx, cy, logo_uri(name))
    return page(rings() + lockup() + text_block() + stat + bdo + tiles + sparkle(1330, 22, 26, 8))


def profile_picture():
    inner = ('<div class="lay" style="left:0;top:0;width:1080px;height:1080px;display:flex;align-items:center;justify-content:center">%s</div>'
             % '<div class="me"><div class="ring" style="--rs:1060px"><img src="%s"></div></div>' % brand.photo_uri("talha_cut"))
    return brand.shell(inner, 1080, 1080, extra_css=".slide{width:1080px;height:1080px}.lay{position:absolute;z-index:5}")


HEADLINE = ("Every startup or company needs a Finance Department. Here\u2019s yours. | Books, tax, US companies and investor "
            "readiness for US founders | Trained at BDO Ebrahim & Co. | 300+ founders")


def uri(path):
    ext = "png" if path.endswith(".png") else "jpeg"
    return "data:image/%s;base64,%s" % (ext, base64.b64encode(open(path, "rb").read()).decode())


def preview(sets, avatar, out_html_w=900):
    """sets: [(title, banner path)]. A computer view to LinkedIn's measured proportions, and a phone view (approximate)."""
    av = uri(avatar)
    blocks = ""
    for title, path in sets:
        bn = uri(path)
        blocks += ('<div style="font:700 26px Jakarta;color:#15191F;margin:34px 0 14px">%s</div>'
                   '<div style="font:600 15px Jakarta;color:#59606C;margin:0 0 8px;letter-spacing:.1em">ON A COMPUTER</div>'
                   '<div style="width:860px;background:#fff;border-radius:12px;overflow:hidden;border:1px solid #D9D6CF">'
                   '<img src="%s" style="width:860px;height:215px;display:block">'
                   '<div style="position:relative;padding:0 26px 22px">'
                   '<img src="%s" style="position:absolute;left:30px;top:-100px;width:165px;height:165px;border-radius:50%%;border:4px solid #fff">'
                   '<div style="padding-top:82px;font:600 25px Arial,Helvetica,sans-serif;color:#191919">Muhammad Talha</div>'
                   '<div style="font:400 16px/1.38 Arial,Helvetica,sans-serif;color:#191919;margin-top:6px;width:600px">%s</div></div></div>'
                   '<div style="font:600 15px Jakarta;color:#59606C;margin:22px 0 8px;letter-spacing:.1em">ON A PHONE (APPROXIMATE: THE APP TRIMS THE SIDES)</div>'
                   '<div style="width:390px;background:#fff;border-radius:12px;overflow:hidden;border:1px solid #D9D6CF">'
                   '<div style="width:390px;height:130px;overflow:hidden;position:relative"><img src="%s" style="position:absolute;left:-65px;top:0;width:520px;height:130px"></div>'
                   '<div style="position:relative;padding:0 16px 16px"><img src="%s" style="position:absolute;left:16px;top:-62px;width:118px;height:118px;border-radius:50%%;border:3px solid #fff">'
                   '<div style="padding-top:64px;font:600 20px Arial,Helvetica,sans-serif;color:#191919">Muhammad Talha</div></div></div>'
                   % (esc(title), bn, av, esc(HEADLINE), bn, av))
    html = ('<!doctype html><html><head><meta charset="utf-8"><style>%s body{margin:0;background:#F6F1E7}</style></head><body>'
            '<div style="padding:10px 20px 40px">%s</div></body></html>' % (brand.fonts_css(), blocks))
    return html


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    b = Browser()
    try:
        for name, fn in [("linkedin-banner-a", option_a), ("linkedin-banner-b", option_b)]:
            out = os.path.join(OUT, name + ".png")
            print(name, b.still(fn(), W, H, out, name=name, check=False))
        avatar = os.path.join(OUT, "linkedin-profile-picture.jpg")
        if os.path.exists(avatar):
            sets = [("A \u00b7 The department", os.path.join(OUT, "linkedin-banner-a.png")),
                    ("B \u00b7 The record", os.path.join(OUT, "linkedin-banner-b.png"))]
            print("preview", b.still(preview(sets, avatar), 900, 1560, os.path.join(OUT, "linkedin-preview.png"), name="preview", check=False))
    finally:
        b.close()
