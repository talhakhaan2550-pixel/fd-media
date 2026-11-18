"""Pictures for the Featured section of Talha's personal LinkedIn profile (1200 x 627, LinkedIn's link picture size),
in the light look of the two Featured items put up on 15 November 2026.

    python3 tools/studio/linkedin_featured.py OUTDIR

checklist: the free US filing checklist on the US Entry page (FD-11), added to Featured on 18 November 2026 for
founders running a US company from abroad. Every claim is the Claim Library's: FD-11 (the checklist, free and
printable, on the US Entry page) and FD-01 (300+ founders).
"""
import os, sys
import brand
from brand import esc
from capture import Browser

OUT = sys.argv[1] if len(sys.argv) > 1 else "/tmp/fd-featured"
W, H = 1200, 627

CSS = """
.slide{width:1200px;height:627px}.lay{position:absolute;z-index:5}
.k2{align-self:flex-start;display:inline-flex;align-items:center;gap:10px;padding:8px 18px 8px 14px;border-radius:999px;border:2.5px solid #15191F;
 background:rgba(255,255,255,.7);font-family:Jakarta;font-weight:700;font-size:17px;letter-spacing:.15em;text-transform:uppercase;color:#15191F;white-space:nowrap}
.k2 i{width:12px;height:12px;border-radius:50%;background:#FFD84D;border:2px solid #15191F}
.lead{font-family:Fraunces;font-weight:600;font-size:44px;line-height:1.12;letter-spacing:-.015em;color:#15191F;text-wrap:balance}
.punch{font-family:Fraunces;font-weight:700;font-size:62px;line-height:1.08;letter-spacing:-.025em;color:#15191F}
.punch .em{padding:0 .1em}
.chips{display:flex;gap:12px;flex-wrap:nowrap}
.chip2{display:inline-flex;align-items:center;gap:9px;padding:8px 16px 8px 9px;border-radius:12px;border:2px solid #15191F;background:#FFFFFF;
 font-family:Jakarta;font-weight:700;font-size:19px;color:#15191F;white-space:nowrap;box-shadow:3px 3px 0 #15191F}
.tk{width:24px;height:24px;border-radius:7px;background:#0B7955;display:grid;place-items:center;flex:none}
.foot{font-family:Jakarta;font-weight:700;font-size:20px;color:#15191F;white-space:nowrap}
.foot b{border-bottom:3px solid #FFD84D}
"""

TICK = ('<span class="tk"><svg width="15" height="15" viewBox="0 0 24 24"><path d="M5 12.5l4.5 4.5L19 7.5" fill="none" stroke="#fff" '
        'stroke-width="3.6" stroke-linecap="round" stroke-linejoin="round"/></svg></span>')


def chips(items):
    return '<div class="chips">%s</div>' % "".join('<span class="chip2">%s%s</span>' % (TICK, esc(t)) for t in items)


def photo(size, left, top):
    return ('<div class="lay me" style="left:%dpx;top:%dpx"><div class="ring" style="--rs:%dpx"><img src="%s"></div></div>'
            % (left, top, size, brand.photo_uri("talha_cut")))


def checklist():
    text = ('<div class="lay" style="left:72px;top:0;width:740px;height:627px;display:flex;flex-direction:column;justify-content:center;gap:20px">'
            '<span class="k2"><i></i>For founders abroad</span>'
            '<div class="lead">Running a US company from abroad?</div>'
            '<div class="punch"><span class="em">The free US filing checklist.</span></div>'
            + chips(["Free", "Printable", "On the US Entry page"]) +
            '<div class="foot" style="margin-top:6px">300+ founders · <b>financedepartmentllc.com</b></div></div>')
    return brand.shell(text + photo(300, 852, 163), W, H, extra_css=CSS)


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    b = Browser()
    try:
        for name, fn in [("linkedin-featured-checklist", checklist)]:
            out = os.path.join(OUT, name + ".png")
            print(name, b.still(fn(), W, H, out, name=name, check=False))
    finally:
        b.close()
