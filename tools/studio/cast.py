"""The cartoon cast. Since 16 November 2026 the studio shows it in 3D (Talha approved the 3D cast that evening):

  Sam the founder, Penny the bookkeeper, Rex the runaway receipt, Zara the founder abroad, Grace the angel investor,
  Dev the co-founder, Maya the freelancer and Dot the deadline.

figure(who, expr) returns one character as an <img> of its 3D sprite (tools/assets/cast/<who>_<expr>.webp, made by
tools/cast3d: render_poses.sh, then make_sprites.py). All sprites share one vertical frame, so characters shown at one
height keep their real sizes. A slide shows them through the "cast" visual (slides.py v_cast). Expressions are in
POSES: the six people happy, surprised or thinking; Rex sly, surprised, happy or wink; Dot happy, surprised or wink.
They never play a real client, a reviewer or Talha, and say only the piece's own words.

The original 2D drawings of Sam, Penny and Rex (svg below, approved earlier on 16 November) stay for reference; the
studio no longer uses them.
"""

INK = '#15191F'
O = f'stroke="{INK}" stroke-width="6" stroke-linejoin="round" stroke-linecap="round"'

def limb(path, fill, w=24):
    return (f'<path d="{path}" fill="none" stroke="{INK}" stroke-width="{w+12}" stroke-linecap="round" stroke-linejoin="round"/>'
            f'<path d="{path}" fill="none" stroke="{fill}" stroke-width="{w}" stroke-linecap="round" stroke-linejoin="round"/>')

def eyes(cx1, cx2, cy, iris, expr, rx=15, ry=19):
    out = ''
    for cx in (cx1, cx2):
        if expr == 'wink' and cx == cx2:
            out += f'<path d="M{cx-14} {cy+2}q14 -12 28 0" fill="none" {O}/>'
            continue
        r_y = ry + (4 if expr == 'surprised' else 0)
        dx, dy = {'happy': (2, 3), 'surprised': (0, 0), 'thinking': (-4, -6), 'wink': (3, 2), 'sly': (4, 2)}.get(expr, (2, 3))
        ir = 7 if expr == 'surprised' else 10
        out += f'<ellipse cx="{cx}" cy="{cy}" rx="{rx}" ry="{r_y}" fill="#fff" {O} stroke-width="5"/>'
        out += f'<circle cx="{cx+dx}" cy="{cy+dy}" r="{ir}" fill="{iris}"/><circle cx="{cx+dx}" cy="{cy+dy}" r="{ir*0.5:.1f}" fill="{INK}"/>'
        out += f'<circle cx="{cx+dx-4}" cy="{cy+dy-5}" r="3.6" fill="#fff"/><circle cx="{cx+dx+3.5}" cy="{cy+dy+2.5}" r="1.8" fill="#fff"/>'
    return out

def mouth(expr, cx=160, y=180):
    if expr == 'surprised':
        return f'<ellipse cx="{cx}" cy="{y+6}" rx="10" ry="13" fill="#7A2318" {O} stroke-width="5"/><ellipse cx="{cx}" cy="{y+12}" rx="6" ry="4" fill="#E2786A"/>'
    if expr == 'thinking':
        return f'<path d="M{cx-12} {y+6}q12 -6 26 2" fill="none" {O} stroke-width="5"/>'
    if expr in ('sly', 'wink'):
        return (f'<path d="M{cx-26} {y-2}q30 26 54 -6q-22 8 -54 6z" fill="#7A2318" {O} stroke-width="5"/>'
                f'<path d="M{cx+2} {y+8}l5 9l6 -11z" fill="#fff" stroke="{INK}" stroke-width="3" stroke-linejoin="round"/>')
    return (f'<path d="M{cx-23} {y-4}q23 30 46 0z" fill="#7A2318" {O} stroke-width="5"/>'
            f'<path d="M{cx-17} {y-1}h34" stroke="#fff" stroke-width="5" stroke-linecap="round"/>'
            f'<ellipse cx="{cx}" cy="{y+11}" rx="9" ry="4.5" fill="#E2786A"/>')

def brows(expr, x1, x2, y, col):
    if expr == 'surprised':
        return f'<path d="M{x1-14} {y-12}q14 -10 28 -2M{x2-14} {y-14}q14 -8 28 2" fill="none" stroke="{col}" stroke-width="6.5" stroke-linecap="round"/>'
    if expr == 'thinking':
        return f'<path d="M{x1-14} {y-2}q14 -6 28 0M{x2-14} {y-14}q14 -10 28 0" fill="none" stroke="{col}" stroke-width="6.5" stroke-linecap="round"/>'
    if expr in ('sly', 'wink'):
        return f'<path d="M{x1-15} {y-10}l28 8M{x2+15} {y-10}l-28 8" fill="none" stroke="{col}" stroke-width="7" stroke-linecap="round"/>'
    return f'<path d="M{x1-14} {y-4}q14 -9 28 -2M{x2-14} {y-6}q14 -7 28 2" fill="none" stroke="{col}" stroke-width="6.5" stroke-linecap="round"/>'

def sam(expr='happy', vb='0 0 320 440'):
    SK, SKD, HD, H2, HO, HO2 = '#C98B5E', '#AE7149', '#2E1F14', '#5B3B26', '#0E8A60', '#0A6E4C'
    s = f'<svg viewBox="{vb}" xmlns="http://www.w3.org/2000/svg">'
    s += '<ellipse cx="160" cy="428" rx="82" ry="10" fill="rgba(21,25,31,.14)"/>'
    s += f'<g {O}><rect x="126" y="336" width="32" height="76" rx="13" fill="#3A3F47"/><rect x="162" y="336" width="32" height="76" rx="13" fill="#3A3F47"/>'
    s += '<path d="M108 404h52v20h-58v-5a15 15 0 0 1 6-15z" fill="#fff"/><path d="M160 404h52a15 15 0 0 1 6 15v5h-58z" fill="#fff"/></g>'
    s += '<path d="M116 412h36M168 412h36" stroke="#FFD84D" stroke-width="5" stroke-linecap="round"/>'
    s += limb('M104 252C82 238 72 214 72 190', HO) + limb('M216 252C232 266 238 284 236 300', HO)
    s += f'<path d="M96 254C96 230 120 216 160 216C200 216 224 230 224 254L232 342C232 350 226 356 218 356H102C94 356 88 350 88 342Z" fill="{HO}" {O}/>'
    s += f'<path d="M196 222C214 228 222 240 224 254L232 342C232 350 226 356 218 356H198C210 320 214 270 196 222Z" fill="{HO2}"/>'
    s += f'<path d="M96 254C96 230 120 216 160 216C200 216 224 230 224 254L232 342C232 350 226 356 218 356H102C94 356 88 350 88 342Z" fill="none" {O}/>'
    s += f'<path d="M120 220q40 30 80 0" fill="{HO2}" {O} stroke-width="5"/>'
    s += f'<rect x="120" y="300" width="80" height="36" rx="12" fill="{HO2}" {O} stroke-width="5"/>'
    s += '<path d="M146 236v30M174 236v30" stroke="#fff" stroke-width="5" stroke-linecap="round"/><circle cx="146" cy="270" r="4.5" fill="#FFD84D"/><circle cx="174" cy="270" r="4.5" fill="#FFD84D"/>'
    s += f'<circle cx="198" cy="270" r="12" fill="#FFD84D" {O} stroke-width="4"/><path d="M200 261l-6 10h6l-3 9l8 -12h-6l3 -7z" fill="{INK}"/>'
    s += f'<circle cx="72" cy="182" r="16" fill="{SK}" {O} stroke-width="5"/><path d="M64 172v-8M72 168v-9M80 172v-7" stroke="{INK}" stroke-width="4" stroke-linecap="round"/>'
    s += f'<g {O} stroke-width="5"><path d="M224 262h34v40a6 6 0 0 1 -6 6h-22a6 6 0 0 1 -6 -6z" fill="#fff"/><rect x="222" y="256" width="38" height="9" rx="3" fill="#E8E2D4"/><path d="M226 280h30v14h-30z" fill="#FFD84D"/></g>'
    s += '<path d="M234 248q-6 -8 0 -16M248 248q-6 -8 0 -16" fill="none" stroke="#8A8F98" stroke-width="3.5" stroke-linecap="round"/>'
    s += f'<circle cx="236" cy="302" r="15" fill="{SK}" {O} stroke-width="5"/>'
    s += f'<circle cx="82" cy="150" r="15" fill="{SK}" {O} stroke-width="5"/><circle cx="238" cy="150" r="15" fill="{SK}" {O} stroke-width="5"/>'
    s += f'<circle cx="160" cy="142" r="80" fill="{SK}" {O}/>'
    s += f'<path d="M212 92C236 110 244 150 230 182C216 210 190 222 170 222C200 206 222 170 212 92Z" fill="{SKD}" opacity=".55"/>'
    s += f'<g fill="{HD}" {O}>' + ''.join(f'<circle cx="{x}" cy="{y}" r="{r}"/>' for x, y, r in
          [(98, 120, 20), (102, 92, 28), (130, 70, 31), (164, 62, 32), (198, 72, 30), (224, 98, 26), (232, 126, 17)]) + '</g>'
    s += f'<path d="M118 66q10 -8 22 -6M156 50q12 -6 24 0M196 60q10 0 18 8" fill="none" stroke="{H2}" stroke-width="5" stroke-linecap="round"/>'
    s += brows(expr, 132, 188, 124, HD) + eyes(132, 188, 148, '#4A2C1A', expr)
    s += f'<path d="M154 164q6 7 12 0" fill="none" stroke="{SKD}" stroke-width="4" stroke-linecap="round"/>'
    s += '<ellipse cx="112" cy="174" rx="12" ry="8" fill="#F08A7A" opacity=".5"/><ellipse cx="208" cy="174" rx="12" ry="8" fill="#F08A7A" opacity=".5"/>'
    s += mouth(expr, 160, 184) + '</svg>'
    return s

def penny(expr='happy', vb='0 0 320 440'):
    SK, SKD, HD, H2, CY, CY2 = '#8A5A3C', '#6E4630', '#1E1714', '#3E2E26', '#FFD84D', '#EDB92A'
    s = f'<svg viewBox="{vb}" xmlns="http://www.w3.org/2000/svg">'
    s += '<ellipse cx="160" cy="428" rx="80" ry="10" fill="rgba(21,25,31,.14)"/>'
    s += f'<g {O}><rect x="128" y="336" width="30" height="76" rx="13" fill="#4A4F58"/><rect x="162" y="336" width="30" height="76" rx="13" fill="#4A4F58"/>'
    s += '<path d="M110 404h48v20h-54v-5a15 15 0 0 1 6-15z" fill="#C23A2B"/><path d="M162 404h48a15 15 0 0 1 6 15v5h-54z" fill="#C23A2B"/></g>'
    s += limb('M104 254C88 272 84 296 92 318', CY) + limb('M216 252C238 236 248 214 250 190', CY)
    s += f'<path d="M98 254C98 230 122 216 160 216C198 216 222 230 222 254L230 344C230 350 226 356 220 356H100C94 356 90 350 90 344Z" fill="{CY}"/>'
    s += f'<path d="M196 222C212 228 220 240 222 254L230 344C230 350 226 356 220 356H200C210 320 214 270 196 222Z" fill="{CY2}"/>'
    s += f'<path d="M136 220L160 300L184 220Z" fill="#fff"/>'
    s += f'<path d="M98 254C98 230 122 216 160 216C198 216 222 230 222 254L230 344C230 350 226 356 220 356H100C94 356 90 350 90 344Z" fill="none" {O}/>'
    s += f'<path d="M136 220L160 300L184 220" fill="none" {O} stroke-width="5"/>'
    s += f'<g {O} stroke-width="4"><path d="M160 232l-20 -10v22z" fill="#0B7955"/><path d="M160 232l20 -10v22z" fill="#0B7955"/><circle cx="160" cy="232" r="6" fill="#0A6A4B"/></g>'
    s += f'<g fill="{INK}"><circle cx="150" cy="316" r="4"/><circle cx="150" cy="336" r="4"/><circle cx="170" cy="316" r="4"/><circle cx="170" cy="336" r="4"/></g>'
    s += f'<g transform="rotate(-12 96 320)" {O} stroke-width="5"><rect x="60" y="282" width="70" height="88" rx="6" fill="#C23A2B"/><path d="M72 282v88" /><rect x="82" y="300" width="38" height="26" rx="4" fill="#F6F1E7" stroke-width="3.5"/></g>'
    s += f'<text x="96" y="318" text-anchor="middle" transform="rotate(-12 96 320)" font-family="Fraunces" font-weight="700" font-size="19" fill="{INK}">$</text>'
    s += f'<circle cx="94" cy="320" r="15" fill="{SK}" {O} stroke-width="5"/>'
    s += f'<circle cx="160" cy="54" r="30" fill="{HD}" {O}/><path d="M146 40q12 -10 26 -4" fill="none" stroke="{H2}" stroke-width="5" stroke-linecap="round"/>'
    s += f'<g transform="rotate(35 172 48)" {O} stroke-width="4"><rect x="140" y="42" width="66" height="12" rx="3" fill="#FFD84D"/><rect x="200" y="42" width="11" height="12" rx="3" fill="#F2A6A0"/></g>'
    s += f'<circle cx="84" cy="152" r="14" fill="{SK}" {O} stroke-width="5"/><circle cx="236" cy="152" r="14" fill="{SK}" {O} stroke-width="5"/>'
    s += f'<circle cx="84" cy="170" r="6" fill="#FFD84D" {O} stroke-width="3"/><circle cx="236" cy="170" r="6" fill="#FFD84D" {O} stroke-width="3"/>'
    s += f'<circle cx="160" cy="144" r="78" fill="{SK}" {O}/>'
    s += f'<path d="M210 96C234 114 240 152 228 182C214 210 190 222 170 222C198 206 220 170 210 96Z" fill="{SKD}" opacity=".5"/>'
    s += f'<path d="M84 146C80 96 116 66 160 66C204 66 240 96 236 146C222 122 204 108 176 102C150 112 120 112 96 128C92 134 88 140 84 146Z" fill="{HD}" {O}/>'
    s += f'<path d="M118 84q22 -12 46 -10" fill="none" stroke="{H2}" stroke-width="5" stroke-linecap="round"/>'
    s += brows(expr, 132, 188, 124, HD) + eyes(132, 188, 152, '#3A2416', expr, 13, 16)
    s += f'<path d="M146 134l-8 -6M202 134l8 -6" stroke="{INK}" stroke-width="4" stroke-linecap="round"/>' if expr != 'thinking' else ''
    s += f'<g fill="rgba(255,255,255,.18)" stroke="#C23A2B" stroke-width="6"><circle cx="132" cy="152" r="24"/><circle cx="188" cy="152" r="24"/></g><path d="M156 150q4 -5 8 0" fill="none" stroke="#C23A2B" stroke-width="6" stroke-linecap="round"/>'
    s += '<path d="M118 140l10 -8M174 140l10 -8" stroke="#fff" stroke-width="3.5" stroke-linecap="round" opacity=".8"/>'
    s += f'<path d="M155 172q5 6 10 0" fill="none" stroke="{SKD}" stroke-width="4" stroke-linecap="round"/>'
    s += '<ellipse cx="110" cy="180" rx="11" ry="7" fill="#F08A7A" opacity=".45"/><ellipse cx="210" cy="180" rx="11" ry="7" fill="#F08A7A" opacity=".45"/>'
    s += f'<g transform="rotate(28 258 170)" {O} stroke-width="4"><rect x="251" y="112" width="14" height="62" rx="3" fill="#FFD84D"/><rect x="251" y="104" width="14" height="11" rx="3" fill="#F2A6A0"/><path d="M251 174l7 15l7 -15z" fill="#E7C49A"/></g>'
    s += f'<circle cx="250" cy="186" r="15" fill="{SK}" {O} stroke-width="5"/>'
    s += mouth(expr, 160, 190) + '</svg>'
    return s

def rex(expr='sly', vb='0 0 320 440'):
    s = f'<svg viewBox="{vb}" xmlns="http://www.w3.org/2000/svg">'
    s += '<ellipse cx="170" cy="428" rx="70" ry="9" fill="rgba(21,25,31,.14)"/>'
    s += '<path d="M28 250h40M16 282h46M34 314h30" stroke="#9AA0A8" stroke-width="6" stroke-linecap="round"/>'
    s += f'<path d="M140 350C132 372 116 388 98 400M196 352C212 366 224 384 248 386" fill="none" stroke="{INK}" stroke-width="7" stroke-linecap="round"/>'
    s += f'<g {O} stroke-width="5"><path d="M74 398h34a10 10 0 0 1 10 10v6H70v-6a10 10 0 0 1 4-10z" fill="#C23A2B"/><path d="M70 414h48" stroke="#fff" stroke-width="5"/>'
    s += '<path d="M240 372l30 -4a10 10 0 0 1 11 9l1 6l-40 5z" fill="#C23A2B"/></g>'
    s += f'<path d="M98 218C70 206 54 182 52 156M226 226C252 232 272 216 280 190" fill="none" stroke="{INK}" stroke-width="7" stroke-linecap="round"/>'
    s += f'<circle cx="52" cy="148" r="14" fill="#fff" {O} stroke-width="5"/><circle cx="282" cy="182" r="14" fill="#fff" {O} stroke-width="5"/>'
    s += f'<g {O} stroke-width="4" fill="#FFD84D"><circle cx="40" cy="104" r="13"/><circle cx="292" cy="132" r="11"/><circle cx="270" cy="96" r="9"/></g>'
    s += f'<g font-family="Fraunces" font-weight="700" fill="{INK}" text-anchor="middle"><text x="40" y="111" font-size="17">$</text><text x="292" y="138" font-size="14">$</text><text x="270" y="101" font-size="11">$</text></g>'
    s += '<g transform="rotate(9 160 220)">'
    zz = 'M92 64' + ''.join(f'l11 {-11 if i % 2 == 0 else 11}' for i in range(12)) + 'V362' + ''.join(f'l-11 {11 if i % 2 == 0 else -11}' for i in range(12)) + 'Z'
    s += f'<path d="{zz}" fill="#fff" {O}/>'
    s += '<path d="M206 64V362l-11 11l-11 -11V96C192 84 200 74 206 64Z" fill="#ECE6D9"/>'
    s += f'<path d="{zz}" fill="none" {O}/>'
    s += f'<path d="M184 64h22v22z" fill="#E3DCCD" {O} stroke-width="4"/>'
    s += '<g stroke="#B9B2A4" stroke-width="5" stroke-linecap="round"><path d="M110 222h56M180 222h12M110 244h44M180 244h12M110 266h60M180 266h12M110 288h36M180 288h12"/></g>'
    s += f'<path d="M108 306h86" stroke="{INK}" stroke-width="3" stroke-dasharray="6 6"/>'
    s += f'<text x="150" y="336" text-anchor="middle" font-family="Fraunces" font-weight="700" font-size="18" fill="{INK}">TOTAL $$$</text>'
    s += brows(expr if expr != 'happy' else 'happy', 126, 172, 116, INK) + eyes(126, 172, 138, '#3A2416', expr, 15, 18)
    s += '<ellipse cx="104" cy="168" rx="11" ry="7" fill="#F08A7A" opacity=".5"/><ellipse cx="196" cy="168" rx="11" ry="7" fill="#F08A7A" opacity=".5"/>'
    s += mouth(expr, 150, 178) + '</g></svg>'
    return s

EXPRESSIONS = {"sam": ("happy", "surprised", "thinking"), "penny": ("happy", "surprised", "thinking"), "rex": ("sly", "surprised", "happy", "wink")}
DEFAULT = {"sam": "happy", "penny": "happy", "rex": "sly"}


def svg(who, expr=None):
    who = (who or "").lower()
    if who not in EXPRESSIONS:
        raise ValueError("unknown cast member %s" % who)
    expr = expr if expr in EXPRESSIONS[who] else DEFAULT[who]
    return {"sam": sam, "penny": penny, "rex": rex}[who](expr)


# ---------------------------------------------------------------- the cast in 3D
import base64, functools, os

SPRITES = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "cast")
PEOPLE = ("happy", "surprised", "thinking")
POSES = {"sam": PEOPLE, "penny": PEOPLE, "zara": PEOPLE, "grace": PEOPLE, "dev": PEOPLE, "maya": PEOPLE,
         "rex": ("sly", "surprised", "happy", "wink"), "dot": ("happy", "surprised", "wink")}
POSE_DEFAULT = {"rex": "sly"}
ROLES = {"sam": "the founder", "penny": "the bookkeeper", "rex": "the runaway receipt", "zara": "the founder abroad",
         "grace": "the angel investor", "dev": "the co-founder", "maya": "the freelancer", "dot": "the deadline"}


def pose(who, expr=None):
    """The character's key and the expression it will wear (an unknown expression falls back to its default)."""
    who = (who or "").lower()
    if who not in POSES:
        raise ValueError("unknown cast member %s" % who)
    return who, expr if expr in POSES[who] else POSE_DEFAULT.get(who, "happy")


@functools.lru_cache(None)
def sprite(who, expr):
    """(data URI, width, height) of a sprite."""
    from PIL import Image
    path = os.path.join(SPRITES, "%s_%s.webp" % (who, expr))
    with Image.open(path) as im:
        w, h = im.size
    with open(path, "rb") as f:
        return "data:image/webp;base64," + base64.b64encode(f.read()).decode(), w, h


def figure(who, expr=None):
    who, expr = pose(who, expr)
    uri, w, h = sprite(who, expr)
    return '<img class="cast3d" alt="" src="%s" width="%d" height="%d">' % (uri, w, h)


def row_height(whos, exprs, h, room, gap=6):
    """The height at which the characters fit side by side in room pixels: h, or less when they would not fit."""
    widths = []
    for i, w in enumerate(whos):
        who, expr = pose(w, exprs[i] if i < len(exprs) else None)
        _, sw, sh = sprite(who, expr)
        widths.append(sw / sh)
    need = sum(widths) * h + gap * (len(widths) - 1)
    return h if need <= room else int((room - gap * (len(widths) - 1)) / sum(widths))
