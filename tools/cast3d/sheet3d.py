import sys, base64
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'studio'))
import brand
from playwright.sync_api import sync_playwright
D = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'out')
def b64(p): return 'data:image/png;base64,' + base64.b64encode(open(p, 'rb').read()).decode()
CAST = [('sam', 'Sam', 'the founder', '#DCEFE6', 'Runs a young US startup and asks what every founder asks about money, filings and raising.'),
        ('penny', 'Penny', 'the bookkeeper', '#FFF1BF', 'Keeps the books straight and answers with the rule, the date and the form.'),
        ('rex', 'Rex', 'the runaway receipt', '#F3EEE4', 'The receipt that always gets away, until the books catch him.'),
        ('zara', 'Zara', 'the founder abroad', '#FBE1DA', 'Runs her US company from Dubai and asks what the US expects from a founder who lives abroad.'),
        ('grace', 'Grace', 'the angel investor', '#E4E8EF', 'Asks for the cap table, the burn and the runway before she asks your name.'),
        ('dev', 'Dev', 'the co-founder', '#F9DED8', 'Ships code at 2 a.m. and swears the spreadsheet is the books.'),
        ('maya', 'Maya', 'the freelancer', '#DCEFE6', 'Designs brands for startups and knows exactly why a client asks for her W-9.'),
        ('dot', 'Dot', 'the deadline', '#FFF1BF', 'A calendar page that never forgets a filing day and never says a date it was not given.')]
cards = ''.join(f'''<div class="card"><div class="art" style="--bg:{bg}"><img src="{b64(f"{D}/{k}_trim.png")}"></div>
<h3>{n} <span>{role}</span></h3><p>{line}</p></div>''' for k, n, role, bg, line in CAST)
html = f'''<html><head><style>{brand.fonts_css()}
*{{box-sizing:border-box}} body{{margin:0;background:#F6F1E7;font-family:Jakarta;color:#15191F}}
.page{{width:1600px;padding:64px 64px 56px}}
.top{{display:flex;justify-content:space-between;align-items:flex-start}}
h1{{font-family:Fraunces;font-weight:700;font-size:64px;margin:0;line-height:1.05}}
h1 em{{font-style:normal;background:linear-gradient(transparent 58%,#FFD84D 58%,#FFD84D 92%,transparent 92%)}}
.sub{{font-size:22px;color:#3E4652;margin:14px 0 0;max-width:1080px;line-height:1.45}}
.tag{{border:2.5px solid #15191F;border-radius:999px;padding:12px 22px;font-weight:700;letter-spacing:.14em;font-size:16px;white-space:nowrap}}
.banner{{margin:36px 0 34px;border-radius:28px;overflow:hidden;border:3px solid #15191F;box-shadow:8px 8px 0 #15191F;background:#F1EADF}}
.banner img{{display:block;width:100%}}
.grid{{display:grid;grid-template-columns:repeat(4,1fr);gap:28px}}
.card{{background:#fff;border:3px solid #15191F;border-radius:26px;box-shadow:7px 7px 0 #15191F;padding:18px 20px 22px}}
.art{{background:radial-gradient(circle at 50% 55%, var(--bg) 0 58%, transparent 59%);height:380px;display:flex;align-items:flex-end;justify-content:center}}
.art img{{max-height:370px;max-width:100%}}
h3{{font-family:Fraunces;font-weight:700;font-size:34px;margin:12px 0 4px}}
h3 span{{font-family:Jakarta;font-weight:600;font-size:19px;color:#0B7955}}
.card p{{margin:0;font-size:18px;line-height:1.45;color:#2B313A}}
.foot{{margin-top:30px;font-size:17px;color:#4A5260;line-height:1.5;max-width:1400px}}
</style></head><body><div class="page">
<div class="top"><div><h1>The cast, <em>now in 3D</em></h1>
<p class="sub">The same eight characters, same faces, colours and props, made as 3D figures. Built in Blender, which is free, so every pose and expression can be rendered again whenever a reel needs it, and they look the same every time.</p></div>
<div class="tag">FOR TALHA'S APPROVAL</div></div>
<div class="banner"><img src="{b64(f"{D}/group_banner.png")}"></div>
<div class="grid">{cards}</div>
<p class="foot">All eight are our own designs, not based on any existing character or real person. Sam, Penny and Rex were approved in 2D on 16 November; Zara, Grace, Dev, Maya and Dot wait for your yes. In reels they move like the 2D cast (bounce, lean, change expression), using rendered poses rather than full 3D animation, which would take hours of rendering per video on free tools.</p>
</div></body></html>'''
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page(viewport={'width': 1600, 'height': 1200})
    pg.set_content(html); pg.evaluate('document.fonts.ready.then(()=>1)'); pg.wait_for_timeout(300)
    h = pg.evaluate('document.querySelector(".page").getBoundingClientRect().height')
    pg.set_viewport_size({'width': 1600, 'height': int(h)})
    pg.screenshot(path=f'{D}/cast-3d-sheet.png', full_page=True); b.close()
print('ok', h)
