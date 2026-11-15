"""Instagram highlight covers and profile picture in the light look (15 November 2026), Talha's ask: "follow the same
design principle and the icons of the story highlights make them more good and 3D type".

Each cover is a 1080 x 1920 story frame on the warm paper: a big disc with an ink outline and an offset shadow, and a
3D icon in the middle (soft clay shading, a darker back face for depth, a gloss highlight and a contact shadow), all
inside the circle Instagram crops a highlight cover to. The profile picture is Talha's real photo, cut out, on the
yellow disc, the same as on the covers and posts.

    python3 tools/studio/instagram_highlights.py OUTDIR
"""
import os, sys
import brand
import profiles as P
from capture import Browser

OUT = sys.argv[1] if len(sys.argv) > 1 else "/tmp/fd-highlights"
INK, YEL, YEL_D, EM, EM_D, PAPER = "#15191F", "#FFD84D", "#E8B92A", "#0B7955", "#075A3F", "#F6F1E7"


def defs(uid, top, mid, bot):
    return ('<defs><linearGradient id="f%s" x1="0" y1="0" x2="0.9" y2="1"><stop offset="0" stop-color="%s"/>'
            '<stop offset="0.55" stop-color="%s"/><stop offset="1" stop-color="%s"/></linearGradient>'
            '<radialGradient id="g%s" cx="0.32" cy="0.22" r="0.55"><stop offset="0" stop-color="#FFFFFF" stop-opacity="0.85"/>'
            '<stop offset="1" stop-color="#FFFFFF" stop-opacity="0"/></radialGradient>'
            '<filter id="s%s" x="-30%%" y="-30%%" width="160%%" height="160%%"><feGaussianBlur stdDeviation="14"/></filter></defs>'
            % (uid, top, mid, bot, uid, uid))


def solid(uid, path, back, depth=26, transform=""):
    """A shape with depth: a contact shadow, a darker back face pushed down and right, the shaded front, a gloss."""
    return ('<g %s><ellipse cx="300" cy="545" rx="190" ry="26" fill="%s" opacity="0.22" filter="url(#s%s)"/>'
            '<path d="%s" fill="%s" transform="translate(%d %d)"/>'
            '<path d="%s" fill="url(#f%s)" stroke="%s" stroke-width="6" stroke-linejoin="round"/>'
            '<path d="%s" fill="url(#g%s)"/></g>'
            % (transform, INK, uid, path, back, depth * 0.55, depth, path, uid, INK, path, uid))


def icon_flag():
    pole = "M160 110 h34 v400 h-34 z"
    cloth = "M194 120 C 260 95, 330 150, 400 125 C 440 112, 470 112, 490 120 L 490 330 C 470 322, 440 322, 400 335 C 330 360, 260 305, 194 330 Z"
    return (defs("a", "#FFF3B0", YEL, YEL_D) + defs("b", "#8A929E", "#4A515C", INK)
            + solid("b", pole, "#0B0E12", 10) + solid("a", cloth, "#B88E12")
            + '<circle cx="177" cy="104" r="26" fill="url(#fb)" stroke="%s" stroke-width="6"/>' % INK)


def icon_medal():
    ribbon_l = "M210 70 L290 70 L330 250 L250 250 Z"
    ribbon_r = "M310 70 L390 70 L350 250 L270 250 Z"
    disc = "M300 205 a150 150 0 1 0 0.1 0 Z"
    star = ("M300 270 L322 322 L378 326 L335 362 L349 417 L300 387 L251 417 L265 362 L222 326 L278 322 Z")
    return (defs("r", "#2BB37E", EM, EM_D) + defs("m", "#FFF3B0", YEL, YEL_D) + defs("t", "#FFFFFF", "#FFF7D6", "#F3E3A0")
            + solid("r", ribbon_l, "#04402C", 12) + solid("r", ribbon_r, "#04402C", 12)
            + solid("m", disc, "#B88E12", 20) + solid("t", star, "#D9C27A", 8))


def icon_folder():
    back = "M120 170 h130 l30 34 h200 a20 20 0 0 1 20 20 v260 a20 20 0 0 1 -20 20 h-360 a20 20 0 0 1 -20 -20 v-294 a20 20 0 0 1 20 -20 z"
    paper = "M170 150 h250 v250 h-250 z"
    front = "M100 250 h400 a20 20 0 0 1 20 22 l-26 210 a20 20 0 0 1 -20 18 h-350 a20 20 0 0 1 -20 -18 l-24 -210 a20 20 0 0 1 20 -22 z"
    return (defs("k", "#2BB37E", EM, EM_D) + defs("p", "#FFFFFF", "#FBF8F2", "#E9E2D2") + defs("y", "#FFF3B0", YEL, YEL_D)
            + solid("k", back, "#04402C", 14) + solid("p", paper, "#CFC6B2", 8)
            + '<path d="M200 205 h190 M200 245 h150 M200 285 h170" stroke="%s" stroke-width="12" stroke-linecap="round" opacity="0.55"/>' % INK
            + solid("y", front, "#B88E12", 16))


def icon_gear():
    import math
    pts = []
    for i in range(16):
        a = math.pi * 2 * i / 16 - math.pi / 2
        r = 215 if i % 2 == 0 else 168
        for da in (-0.13, 0.13):
            pts.append((300 + r * math.cos(a + da), 300 + r * math.sin(a + da)))
    gear = "M" + " L".join("%.1f %.1f" % p for p in pts) + " Z M300 230 a70 70 0 1 0 0.1 0 Z"
    return (defs("e", "#2BB37E", EM, EM_D)
            + '<g fill-rule="evenodd">' + solid("e", gear, "#04402C", 22) + '</g>'
            + '<circle cx="300" cy="300" r="70" fill="%s" opacity="0.0"/>' % PAPER)


def icon_bubble():
    bubble = ("M140 120 h320 a70 70 0 0 1 70 70 v170 a70 70 0 0 1 -70 70 h-150 l-90 80 l10 -80 h-90 a70 70 0 0 1 -70 -70 v-170 "
              "a70 70 0 0 1 70 -70 z")
    return (defs("q", "#FFF3B0", YEL, YEL_D) + solid("q", bubble, "#B88E12", 20)
            + '<text x="300" y="365" text-anchor="middle" font-family="Fraunces" font-weight="700" font-size="230" fill="%s">?</text>' % INK)


def icon_star():
    import math
    pts = []
    for i in range(10):
        a = -math.pi / 2 + i * math.pi / 5
        r = 240 if i % 2 == 0 else 110
        pts.append((300 + r * math.cos(a), 315 + r * math.sin(a)))
    star = "M" + " L".join("%.1f %.1f" % p for p in pts) + " Z"
    return defs("s", "#FFF3B0", YEL, YEL_D) + solid("s", star, "#B88E12", 22)


HIGHLIGHTS = [  # (file name, label for reference, disc colour, icon)
    ("01-start-here", "Start here", "emerald", icon_flag),
    ("02-credentials", "Credentials", "yellow", icon_medal),
    ("03-services", "Services", "paper", icon_folder),
    ("04-how-we-work", "How we work", "yellow", icon_gear),
    ("05-faqs", "FAQs", "emerald", icon_bubble),
    ("06-client-reviews", "Client reviews", "paper", icon_star),
]
DISCS = {"emerald": ("#E3F1EA", "#CFE6DA"), "yellow": ("#FFE998", "#FFD84D"), "paper": ("#FFFFFF", "#EFE6D3")}


def cover(disc, icon):
    a, b = DISCS[disc]
    inner = ('<div class="lay" style="left:40px;top:460px;width:1000px;height:1000px;border-radius:50%%;border:8px solid %s;'
             'background:radial-gradient(circle at 35%% 30%%, %s 0%%, %s 70%%);box-shadow:14px 14px 0 %s;display:flex;align-items:center;justify-content:center">'
             '<svg width="780" height="780" viewBox="0 0 600 600" style="overflow:visible">%s</svg></div>'
             % (INK, a, b, INK, icon()))
    return P.page(1080, 1920, inner)


def profile_picture():
    inner = ('<div class="lay" style="left:0;top:0;width:1080px;height:1080px;display:flex;align-items:center;justify-content:center">%s</div>'
             % P.me(1060))
    return P.page(1080, 1080, inner)


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    b = Browser()
    try:
        for name, label, disc, icon in HIGHLIGHTS:
            out = os.path.join(OUT, "highlight-%s.png" % name)
            print(name, b.still(cover(disc, icon), 1080, 1920, out, name=name, check=False))
        out = os.path.join(OUT, "profile-picture.png")
        print("profile", b.still(profile_picture(), 1080, 1080, out, name="profile", check=False))
    finally:
        b.close()


# The story frames behind each cover, in the words of the website, the offers and the Claim Library.
import slides

CALL = {"photo": "talha", "kicker": "Your next step", "title": "Book a 30 minute call", "emph": "30 minute call",
        "body": "Every offer and its price are on our website.", "cta": "Link in bio"}
FRAMES = {
    "01-start-here": [
        {"kicker": "Start here", "title": "Every startup or company needs a Finance Department. Here's yours.", "emph": "Here's yours.",
         "body": "An accounting, tax and advisory firm for US startups, and for founders running a US company from abroad. Done for you, start to finish."},
        {"kicker": "Books and tax", "title": "Books and tax", "emph": "tax",
         "body": "Monthly books for funded startups, books that are behind brought up to date, business tax returns, 1099s, payroll and the R&D tax credit.",
         "visual": {"type": "stats", "items": [{"label": "1099s", "value": "$100", "note": "Up to five forms"},
                                               {"label": "Tax returns", "value": "$600", "note": "From"}]}},
        {"kicker": "Your US company from abroad", "title": "Your US company, set up and kept compliant", "emph": "kept compliant",
         "body": "Set up in 10 working days, then kept compliant, including Delaware franchise tax and Form 5472 for foreign owned LLCs.",
         "visual": {"type": "stats", "items": [{"label": "Set up", "value": "$425", "note": "From, state fee included"},
                                               {"label": "Kept compliant", "value": "$175", "note": "A month"}]}},
        {"kicker": "Raising", "title": "Investor ready before you raise", "emph": "before you raise",
         "body": "The 5 Day Investor Ready Scan finds your gaps before an investor does. The Investor Ready Sprint builds the model, the cap table and the data room. We do not introduce investors or take a success fee."},
        CALL,
    ],
    "02-credentials": [
        {"photo": "talha", "kicker": "Credentials", "title": "Muhammad Talha, trained at BDO Ebrahim & Co.", "emph": "BDO Ebrahim & Co."},
        {"kicker": "Qualifications", "title": "Qualifications",
         "visual": {"type": "list", "items": ["QuickBooks ProAdvisor (Silver)", "ICAP's Certificate in Accounting and Finance",
                                              "Completing the ACCA qualification",
                                              "Working towards qualifying as a Chartered Accountant with ICAP"]}},
        {"kicker": "Fiverr Pro", "title": "Vetted by Fiverr Pro", "emph": "Fiverr Pro",
         "body": "Selected by the Fiverr Pro team for his expertise."},
        {"photo": "award", "kicker": "Award", "title": "Best Freelancer of Swabi", "emph": "Best Freelancer"},
        {"kicker": "The record", "title": "We have worked with 300+ founders", "emph": "300+ founders",
         "body": "Materials we prepared have helped founders raise more than $100M across SBA loans, angel rounds and early venture rounds, and clients have left more than 150 reviews on Fiverr.",
         "cta": "Link in bio"},
    ],
    "03-services": [
        {"kicker": "Services", "title": "Books and tax",
         "visual": {"type": "list", "items": ["Monthly books for funded startups: $625 a month", "Books Catch Up: from $1,000",
                                              "Business tax returns: from $600", "1099s: $100 for up to five forms",
                                              "Payroll: $200 to set up, $75 a month", "R&D credit: $1,000"]}},
        {"kicker": "Services", "title": "Your US company",
         "visual": {"type": "list", "items": ["Set up in 10 working days: from $425, state fee included",
                                              "The International Founder Plan: $175 a month",
                                              "Delaware franchise tax: $125 a year", "Form 5472 for foreign owned LLCs: $300 a year"]}},
        {"kicker": "Services", "title": "Raising",
         "body": "We do not introduce investors or take a success fee.",
         "visual": {"type": "list", "items": ["5 Day Investor Ready Scan: $750 for the first five, then $1,250",
                                              "Investor Ready Sprint: $4,250"]}},
        CALL,
    ],
    "04-how-we-work": [
        {"kicker": "How we work", "title": "1. Pick a service or book a call", "emph": "Pick a service",
         "body": "Every offer and its price are on our website. Not sure which fits? Book a 30 minute call."},
        {"kicker": "How we work", "title": "2. Send your documents", "emph": "Send your documents",
         "body": "We tell you exactly what we need."},
        {"kicker": "How we work", "title": "3. We do the work, on time", "emph": "on time",
         "body": "Each service's guarantee says exactly what we pay or refund, and it is written into your terms before you pay."},
        {"photo": "talha", "kicker": "Your next step", "title": "Book a 30 minute call", "emph": "30 minute call",
         "body": "Thirty minutes on what you need and what it costs. If we are a fit, you get a written proposal with fixed fees.",
         "cta": "Link in bio"},
    ],
}


def faq_frames(site):
    import re
    src = open(os.path.join(site, "src/pages/Index.tsx"), encoding="utf-8").read()
    block = src[src.index("const FAQS"):src.index("];", src.index("const FAQS"))]
    pairs = re.findall(r'q: "([^"]+)",\s*a: "([^"]+)"', block)
    return [{"kicker": "FAQs", "title": q, "body": a} for q, a in pairs]


def review_frames(site):
    import re
    src = open(os.path.join(site, "src/lib/site.ts"), encoding="utf-8").read()
    intro = re.search(r'REVIEWS_INTRO = "([^"]+)"', src).group(1)
    reviews = re.findall(r'quote:\s*"([^"]+)",\s*client: "([^"]+)"', src)
    out = [{"kicker": "Client reviews", "title": intro, "emph": "150 reviews"}]
    # A client's words are shown as they wrote them, with no marker on any part of them.
    out += [{"kicker": client, "title": "“%s”" % quote, "emph": ""} for quote, client in reviews]
    out.append({"kicker": "Client reviews", "title": "Read all of Talha's reviews on Fiverr", "emph": "on Fiverr",
                "body": "fiverr.com/talha2550", "cta": "Link in bio"})
    return out


def render_frames(out_dir, site="/home/claude/financedepartment"):
    frames = dict(FRAMES)
    frames["05-faqs"] = faq_frames(site)
    frames["06-client-reviews"] = review_frames(site)
    b = Browser()
    try:
        for name, fr in frames.items():
            for i, s in enumerate(fr):
                out = os.path.join(out_dir, "story-%s-%02d.png" % (name, i + 2))
                problem = b.still(slides.story_frame(s), 1080, 1920, out, name="%s-%d" % (name, i))
                if problem:
                    print(name, i + 2, problem)
    finally:
        b.close()
    return frames
