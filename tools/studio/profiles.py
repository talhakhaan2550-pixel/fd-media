"""Profile covers in the light look (15 November 2026), drawn with the studio's brand (fonts, paper, grain, marker):
the Facebook Page cover (1640 x 856), the YouTube channel banner (2560 x 1440) and the LinkedIn company page banner
(1128 x 191). Each carries FD-29's line with "written guarantee" on the marker and the three areas the home page opens
on; Facebook and YouTube add Talha's real photo, 300+ founders (FD-01) and the site's address. Every word stays inside
the part each platform shows on every device (noted beside each size).

    python3 tools/studio/profiles.py OUTDIR    # writes facebook-cover.png, youtube-banner.png, linkedin-company-banner.png

YouTube takes 6 MB at most and Claude in Chrome uploads 3.8 MB at most, so the YouTube banner went up as a JPEG
(quality 93, no chroma subsampling).
"""
import os, sys
import brand
from brand import esc
from capture import Browser

OUT = sys.argv[1] if len(sys.argv) > 1 else "/tmp/fd-profiles"
HEAD = 'Every service has a fixed price and a <span class="em">written guarantee</span>.'
DOORS = ["Books and tax", "Your US company from abroad", "Raising"]

def chips(scale=1.0):
    return "".join('<span class="chip" style="font-size:%dpx;padding:%dpx %dpx">%s%s</span>'
                   % (24 * scale, 13 * scale, 20 * scale, brand.ic("check", int(28 * scale), "#0B7955", 3.2), esc(d)) for d in DOORS)

def me(size):
    return ('<div class="me"><div class="ring" style="--rs:%dpx"><img src="%s"></div></div>'
            % (size, brand.photo_uri("talha_cut")))

def page(w, h, inner, css=""):
    return brand.shell(inner, w, h, extra_css=".slide{width:%dpx;height:%dpx}.lay{position:absolute;z-index:5}%s" % (w, h, css))

def facebook():
    w, h = 1640, 856  # phones show about the middle 1110 x 624; text stays inside it
    inner = ('<div class="lay" style="left:265px;top:150px;width:1110px;height:556px;display:flex;align-items:center;gap:52px">'
             '<div style="flex:1;display:flex;flex-direction:column;gap:26px">'
             '<span class="kicker">Finance Department</span>'
             '<h1 style="font-family:Fraunces;font-weight:700;font-size:64px;line-height:1.08;margin:0">%s</h1>'
             '<div style="display:flex;flex-wrap:wrap;gap:12px">%s</div>'
             '<div style="font-size:26px;font-weight:600">300+ founders · financedepartmentllc.com</div></div>'
             '%s</div>') % (HEAD, chips(0.95), me(250))
    return w, h, page(w, h, inner)

def youtube():
    w, h = 2560, 1440  # every device shows the middle 1546 x 423
    inner = ('<div class="lay" style="left:507px;top:508px;width:1546px;height:423px;display:flex;align-items:center;gap:56px">'
             '%s<div style="flex:1;display:flex;flex-direction:column;gap:22px">'
             '<h1 style="font-family:Fraunces;font-weight:700;font-size:68px;line-height:1.06;margin:0">%s</h1>'
             '<div style="display:flex;flex-wrap:wrap;gap:12px">%s</div>'
             '<div style="font-size:28px;font-weight:600">Finance Department · 300+ founders · financedepartmentllc.com</div></div></div>'
             ) % (me(300), HEAD, chips(1.05))
    return w, h, page(w, h, inner)

def linkedin():
    w, h = 1128, 191  # the logo sits over the lower left, so the words keep to the right
    inner = ('<div class="lay" style="left:300px;top:20px;width:800px;height:151px;display:flex;flex-direction:column;justify-content:center;gap:12px">'
             '<h1 style="font-family:Fraunces;font-weight:700;font-size:31px;line-height:1.1;margin:0">%s</h1>'
             '<div style="display:flex;gap:8px">%s</div></div>') % (HEAD, chips(0.62))
    return w, h, page(w, h, inner)

if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    b = Browser()
    try:
        for name, fn in [("facebook-cover", facebook), ("youtube-banner", youtube), ("linkedin-company-banner", linkedin)]:
            w, h, html = fn()
            out = os.path.join(OUT, name + ".png")
            problem = b.still(html, w, h, out, name=name, check=False)
            print(name, w, h, "->", out, "problem:", problem)
    finally:
        b.close()
