"""Instagram profile posts in the light look (15 November 2026): the two pinned carousels, Start here and The record,
remade for the twelve offers and Talha's line (FD-30). Every sentence comes from the Claim Library, the offer prices
or the website's own words; the client logos are the ones Talha supplied on 21 October 2026 (website src/assets/clients).

    python3 tools/studio/instagram_profile.py OUTDIR [WEBSITE_DIR]
"""
import base64, os, sys
import slides
from brand import esc
from capture import Browser

OUT = sys.argv[1] if len(sys.argv) > 1 else "/tmp/fd-instagram"
SITE = sys.argv[2] if len(sys.argv) > 2 else "/home/claude/financedepartment"
LOGOS = ["central-square-sandton", "verifynova", "mcorp", "house-of-hasko", "yild", "hoolii", "house-of-victory",
         "mirth-and-mischief", "the-glass-garden", "four-paws"]


def v_logos(v, mode, d):
    """The client logos on white tiles, five rows of two."""
    tiles = ""
    for i, name in enumerate(LOGOS):
        path = os.path.join(SITE, "src/assets/clients", name + ".webp")
        uri = "data:image/webp;base64," + base64.b64encode(open(path, "rb").read()).decode()
        tiles += ('<div data-a="up" data-d="%.2f" style="background:#FFFFFF;border:2.5px solid #15191F;border-radius:18px;height:118px;'
                  'display:flex;align-items:center;justify-content:center;padding:14px 22px"><img src="%s" style="max-width:100%%;'
                  'max-height:84px;object-fit:contain"></div>' % (d + 0.06 * i, uri))
    return '<div class="vis" style="display:grid;grid-template-columns:1fr 1fr;gap:16px">%s</div>' % tiles


slides.VISUALS["logos"] = v_logos

AREAS = {"type": "chips", "items": [{"text": "Books and tax"}, {"text": "Your US company from abroad"}, {"text": "Raising"}]}
CLOSE = {"layout": "CLOSE", "title": "Book a 30 minute call", "emph": "30 minute call",
         "body": "Every offer and its price are on our website, where you can book a call with Muhammad Talha.",
         "cta": "Link in bio"}

START_HERE = [
    {"layout": "COVER", "kicker": "Start here", "title": "Every startup or company needs a Finance Department. Here's yours.",
     "emph": "Here's yours.", "visual": AREAS},
    {"layout": "POINT", "num": "1", "tag": "Who we help", "title": "For US startups, and founders running a US company from abroad",
     "body": "Finance Department is an accounting, tax and advisory firm led by Muhammad Talha. Done for you, start to finish.",
     "visual": {"type": "chips", "items": [{"text": "US startups"}, {"text": "Founders running a US company from abroad"}]}},
    {"layout": "POINT", "num": "2", "tag": "Books and tax", "title": "Books and tax",
     "body": "Monthly books for funded startups, books that are behind brought up to date, business tax returns, 1099s, payroll and the R&D tax credit.",
     "visual": {"type": "stats", "items": [{"label": "1099s", "value": "$100", "note": "Up to five forms"},
                                           {"label": "Tax returns", "value": "$600", "note": "From"},
                                           {"label": "Monthly books", "value": "$625", "note": "A month"}]}},
    {"layout": "POINT", "num": "3", "tag": "Your US company from abroad", "title": "Your US company, set up and kept compliant",
     "body": "A US company set up in 10 working days, then kept compliant, including Delaware franchise tax and Form 5472 for foreign owned LLCs.",
     "visual": {"type": "stats", "items": [{"label": "Set up", "value": "$425", "note": "From, state fee included"},
                                           {"label": "Kept compliant", "value": "$175", "note": "A month"}]}},
    {"layout": "POINT", "num": "4", "tag": "Raising", "title": "Investor ready before you raise",
     "body": "The 5 Day Investor Ready Scan finds your gaps before an investor does. The Investor Ready Sprint builds the model, the cap table and the data room. We do not introduce investors or take a success fee.",
     "visual": {"type": "chips", "items": [{"text": "Model"}, {"text": "Cap table"}, {"text": "Data room"}]}},
    {"layout": "POINT", "num": "5", "tag": "How it works", "title": "Three steps",
     "visual": {"type": "steps", "items": ["Pick a service or book a call", "Send your documents", "We do the work, on time"]}},
    CLOSE,
]

THE_RECORD = [
    {"layout": "COVER", "kicker": "The record", "title": "We have worked with 300+ founders", "emph": "300+ founders",
     "visual": {"type": "hero", "label": "Founders", "value": "300+"}},
    {"layout": "POINT", "num": "1", "tag": "Raised", "title": "More than $100M raised",
     "body": "Materials we prepared have helped founders raise more than $100M across SBA loans, angel rounds and early venture rounds.",
     "visual": {"type": "stats", "items": [{"label": "Raised with materials we prepared", "value": "$100M+", "note": "SBA loans, angel and early venture rounds"}]}},
    {"layout": "POINT", "num": "2", "tag": "Clients", "title": "Some of the companies we have worked with",
     "visual": {"type": "logos"}},
    {"layout": "POINT", "num": "3", "tag": "Credentials", "title": "Trained at BDO Ebrahim & Co.", "emph": "BDO Ebrahim & Co.",
     "visual": {"type": "list", "items": ["QuickBooks ProAdvisor (Silver)", "ICAP's Certificate in Accounting and Finance",
                                          "Completing the ACCA qualification", "Vetted by Fiverr Pro", "Best Freelancer of Swabi",
                                          "More than 150 reviews from clients on Fiverr"]}},
    CLOSE,
]


if __name__ == "__main__":
    from PIL import Image
    os.makedirs(OUT, exist_ok=True)
    b = Browser()
    try:
        for name, sl in [("IG-START-HERE", START_HERE), ("IG-THE-RECORD", THE_RECORD)]:
            for i, s in enumerate(sl):
                s = dict(s)
                if s.get("num") and len(s["num"]) == 1:
                    s["num"] = "0" + s["num"]
                html = slides.carousel_slide(s, i, len(sl), "post")
                png = os.path.join(OUT, "%s_%02d.png" % (name, i + 1))
                problem = b.still(html, 1080, 1350, png, name="%s_%02d" % (name, i + 1))
                jpg = png[:-4] + ".jpg"
                Image.open(png).convert("RGB").save(jpg, "JPEG", quality=93, subsampling=0, optimize=True)
                os.remove(png)
                print(os.path.basename(jpg), "problem:", problem)
    finally:
        b.close()
