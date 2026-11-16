"""Flat print textures for the 3D cast: faces (mouth, blush, freckles), clothing prints and prop labels.
Each SVG uses the 2D cast's own coordinates (viewBox 320x440 space), so a texture lands where the 2D drawing had it.
Rendered with Chromium (brand fonts embedded) to transparent PNGs in tex/."""
import sys
sys.path.insert(0, __import__('os').path.join(__import__('os').path.dirname(__import__('os').path.abspath(__file__)), '..', 'studio'))
import brand
from playwright.sync_api import sync_playwright

INK = '#15191F'
import os
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tex')

def blush(x, y, rx=15, ry=10, op=.55):
    return f'<ellipse cx="{x}" cy="{y}" rx="{rx}" ry="{ry}" fill="url(#bl)" opacity="{op}"/>'

DEFS = ('<defs><radialGradient id="bl"><stop offset="0" stop-color="#F08A7A" stop-opacity="1"/>'
        '<stop offset=".55" stop-color="#F08A7A" stop-opacity=".55"/><stop offset="1" stop-color="#F08A7A" stop-opacity="0"/></radialGradient></defs>')

def mouth(expr, cx, y):
    dark, lip = '#6E1F16', '#4A130D'
    if expr == 'surprised':
        return (f'<ellipse cx="{cx}" cy="{y+6}" rx="9" ry="12" fill="{dark}" stroke="{lip}" stroke-width="1.6"/>'
                f'<ellipse cx="{cx}" cy="{y+12}" rx="5.5" ry="3.6" fill="#E2786A"/>')
    if expr == 'thinking':
        return f'<path d="M{cx-12} {y+6}q12 -6 26 2" fill="none" stroke="#5A2116" stroke-width="4.5" stroke-linecap="round"/>'
    if expr in ('sly', 'wink'):
        return (f'<clipPath id="mc"><path d="M{cx-26} {y-2}q30 26 54 -6q-22 8 -54 6z"/></clipPath>'
                f'<path d="M{cx-26} {y-2}q30 26 54 -6q-22 8 -54 6z" fill="{dark}" stroke="{lip}" stroke-width="1.6"/>'
                f'<g clip-path="url(#mc)"><ellipse cx="{cx+6}" cy="{y+16}" rx="12" ry="5" fill="#E2786A"/></g>'
                f'<path d="M{cx+2} {y+7}l5 8l6 -10z" fill="#fff"/>')
    return (f'<clipPath id="mc"><path d="M{cx-22} {y-4}q22 30 44 0z"/></clipPath>'
            f'<path d="M{cx-22} {y-4}q22 30 44 0z" fill="{dark}" stroke="{lip}" stroke-width="1.6"/>'
            f'<g clip-path="url(#mc)"><rect x="{cx-20}" y="{y-6}" width="40" height="8" rx="3" fill="#fff"/>'
            f'<ellipse cx="{cx}" cy="{y+12}" rx="10" ry="5.5" fill="#E2786A"/></g>')

# who: (head cx, cy, R, eye_y, mouth_y, freckles)
HEADS = {'sam': (160, 142, 80, 148, 184, False), 'penny': (160, 144, 78, 152, 190, False), 'zara': (160, 144, 78, 152, 192, False),
         'grace': (160, 144, 78, 152, 190, False), 'dev': (160, 144, 78, 162, 202, False), 'maya': (160, 144, 78, 154, 192, True)}

def face_svg(who, expr):
    cx, cy, R, ey, my, fr = HEADS[who]
    s = f'<svg viewBox="{cx-R} {cy-R} {2*R} {2*R}" xmlns="http://www.w3.org/2000/svg">' + DEFS
    s += blush(110, ey + 27) + blush(210, ey + 27)
    if fr:
        s += '<g fill="#B9784F">' + ''.join(f'<circle cx="{x}" cy="{y}" r="2.3"/>' for x, y in
              [(104, 178), (113, 185), (100, 188), (216, 178), (207, 185), (220, 188), (108, 194), (212, 194)]) + '</g>'
    return s + mouth(expr, 160, my) + '</svg>'

def torso_svg(who):
    s = '<svg viewBox="80 205 160 160" xmlns="http://www.w3.org/2000/svg">'
    if who == 'sam':
        s += '<rect x="114" y="296" width="92" height="44" rx="16" fill="#0A6E4C"/><path d="M122 300h76" stroke="#12A06F" stroke-width="2.5" stroke-linecap="round"/>'
    elif who == 'penny':
        s += '<path d="M134 212L160 300L186 212Z" fill="#FBF8F0"/><path d="M134 212L160 300L186 212" fill="none" stroke="#E3AE1E" stroke-width="5" stroke-linejoin="round"/>'
        s += '<path d="M160 300V365" stroke="#E3AE1E" stroke-width="3"/>'
        s += f'<g fill="{INK}"><circle cx="151" cy="318" r="4"/><circle cx="151" cy="338" r="4"/><circle cx="169" cy="318" r="4"/><circle cx="169" cy="338" r="4"/></g>'
    elif who == 'zara':
        s += '<path d="M140 212L160 270L180 212Z" fill="#FBF8F0"/>'
        s += '<path d="M136 212L160 276L146 290L120 228Z" fill="#C24E39"/><path d="M184 212L160 276L174 290L200 228Z" fill="#C24E39"/>'
        s += f'<circle cx="160" cy="318" r="6" fill="#FFD84D" stroke="{INK}" stroke-width="2"/>'
        s += f'<circle cx="134" cy="252" r="8" fill="#FFD84D" stroke="#B8901A" stroke-width="1.5"/><path d="M126 252h16M134 244v16" stroke="{INK}" stroke-width="1.6"/><ellipse cx="134" cy="252" rx="3.6" ry="8" fill="none" stroke="{INK}" stroke-width="1.6"/>'
    elif who == 'grace':
        s += '<path d="M146 212L160 264L174 212Z" fill="#FBF8F0"/>'
        s += '<path d="M142 212L160 268L148 282L126 228Z" fill="#1F2633"/><path d="M178 212L160 268L172 282L194 228Z" fill="#1F2633"/>'
        s += '<g fill="#3A4458"><circle cx="160" cy="300" r="4.5"/><circle cx="160" cy="326" r="4.5"/></g>'
        s += f'<path d="M136 250l2.4 5.6 6 .4-4.6 3.8 1.6 5.8-5.4-3.2-5.4 3.2 1.6-5.8-4.6-3.8 6-.4z" fill="#FFD84D" stroke="#B8901A" stroke-width="1"/>'
    elif who == 'dev':
        s += '<text x="160" y="314" text-anchor="middle" font-family="PlexMono" font-size="44" fill="#FFD84D" stroke="#FFD84D" stroke-width="2.2">{ }</text>'
    return s + '</svg>'

def rex_svg():
    s = '<svg viewBox="92 64 114 298" xmlns="http://www.w3.org/2000/svg">' + DEFS
    s += '<path d="M184 64h22v22z" fill="#E3DCCD"/>'
    s += '<g stroke="#B9B2A4" stroke-width="5" stroke-linecap="round"><path d="M110 222h56M180 222h12M110 244h44M180 244h12M110 266h60M180 266h12M110 288h36M180 288h12"/></g>'
    s += f'<path d="M108 306h86" stroke="{INK}" stroke-width="3" stroke-dasharray="6 6"/>'
    s += f'<text x="150" y="336" text-anchor="middle" font-family="Fraunces" font-weight="700" font-size="18" fill="{INK}">TOTAL $$$</text>'
    s += blush(104, 168) + blush(196, 168) + mouth('sly', 150, 178)
    return s + '</svg>'

def dot_svg(expr='happy'):
    s = '<svg viewBox="86 92 164 262" xmlns="http://www.w3.org/2000/svg">' + DEFS
    s += '<path d="M86 106a14 14 0 0 1 14 -14h136a14 14 0 0 1 14 14v44H86Z" fill="#C23A2B"/>'
    s += '<text x="168" y="134" text-anchor="middle" font-family="Fraunces" font-weight="700" font-size="30" letter-spacing="3" fill="#fff">DUE</text>'
    cells = ''.join(f'<rect x="{104 + c * 27}" y="{278 + r * 22}" width="20" height="15" rx="3"/>' for r in range(3) for c in range(5))
    s += f'<g fill="none" stroke="#D6D0C2" stroke-width="3">{cells}</g>'
    s += '<circle cx="168" cy="307" r="17" fill="none" stroke="#C23A2B" stroke-width="4"/>'
    s += '<path d="M226 326v14a14 14 0 0 1 -14 14h-16z" fill="#E6DFD0"/>'
    s += blush(116, 236) + blush(220, 236) + mouth(expr, 168, 244)
    return s + '</svg>'

def invoice_svg():
    s = '<svg viewBox="222 244 70 90" xmlns="http://www.w3.org/2000/svg">'
    s += f'<text x="257" y="268" text-anchor="middle" font-family="Fraunces" font-weight="700" font-size="13" fill="{INK}">INVOICE</text>'
    s += '<path d="M232 282h44M232 294h50M232 306h34" stroke="#B9B2A4" stroke-width="4" stroke-linecap="round"/><path d="M232 320h50" stroke="#C23A2B" stroke-width="4" stroke-linecap="round"/>'
    return s + '</svg>'

def screen_svg():
    s = '<svg viewBox="232 232 68 46" xmlns="http://www.w3.org/2000/svg"><rect x="232" y="232" width="68" height="46" fill="#fff"/>'
    s += '<rect x="232" y="232" width="68" height="11" fill="#DCEFE6"/><rect x="249" y="257" width="17" height="13" fill="#F2A6A0"/>'
    s += '<path d="M249 232v46M266 232v46M283 232v46M232 244h68M232 257h68M232 270h68" stroke="#B9B2A4" stroke-width="1.6"/>'
    return s + '</svg>'

def passport_svg():
    s = '<svg viewBox="229 116 48 62" xmlns="http://www.w3.org/2000/svg"><rect x="229" y="116" width="48" height="62" fill="#22324A"/>'
    s += '<g fill="none" stroke="#E8C24A" stroke-width="2"><circle cx="253" cy="140" r="11"/><ellipse cx="253" cy="140" rx="5" ry="11"/><path d="M242 140h22M244 134h18M244 146h18"/></g>'
    s += '<text x="253" y="166" text-anchor="middle" font-family="Jakarta" font-weight="800" font-size="5.6" letter-spacing=".8" fill="#E8C24A">PASSPORT</text>'
    return s + '</svg>'

def ledger_svg():
    s = '<svg viewBox="60 282 70 88" xmlns="http://www.w3.org/2000/svg">'
    s += '<path d="M72 282v88" stroke="#9E2C20" stroke-width="3"/>'
    s += f'<rect x="82" y="300" width="38" height="26" rx="4" fill="#F6F1E7"/><text x="101" y="320" text-anchor="middle" font-family="Fraunces" font-weight="700" font-size="19" fill="{INK}">$</text>'
    return s + '</svg>'

def coin_svg():
    return f'<svg viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg"><text x="50" y="74" text-anchor="middle" font-family="Fraunces" font-weight="700" font-size="68" fill="#9A7410">$</text></svg>'

def bolt_svg():
    return f'<svg viewBox="186 258 24 24" xmlns="http://www.w3.org/2000/svg"><path d="M200 261l-6 10h6l-3 9l8 -12h-6l3 -7z" fill="{INK}"/></svg>'

def clock_svg():
    ticks = ''.join(f'<circle cx="{284 + 11.5 * __import__("math").sin(a * 0.5236):.2f}" cy="{184 - 11.5 * __import__("math").cos(a * 0.5236):.2f}" r=".9" fill="{INK}"/>' for a in range(12))
    return (f'<svg viewBox="269 169 30 30" xmlns="http://www.w3.org/2000/svg"><circle cx="284" cy="184" r="15" fill="#fff"/>{ticks}'
            f'<path d="M284 176v9l6 4" fill="none" stroke="{INK}" stroke-width="2.2" stroke-linecap="round"/><circle cx="284" cy="184" r="1.6" fill="{INK}"/></svg>')

def items():
    out = []
    for who in HEADS:
        for expr in ('happy', 'surprised', 'thinking'):
            out.append((f'face_{who}_{expr}', face_svg(who, expr), 1024, 1024))
        out.append((f'torso_{who}', torso_svg(who), 1024, 1024))
    out += [('rex_front', rex_svg(), 456, 1192), ('dot_front_happy', dot_svg('happy'), 656, 1048), ('dot_front_surprised', dot_svg('surprised'), 656, 1048),
            ('dot_front_wink', dot_svg('wink'), 656, 1048), ('invoice', invoice_svg(), 560, 720), ('screen', screen_svg(), 680, 460),
            ('passport', passport_svg(), 480, 620), ('ledger', ledger_svg(), 560, 704), ('coin', coin_svg(), 400, 400),
            ('bolt', bolt_svg(), 240, 240), ('clock', clock_svg(), 300, 300)]
    return out

if __name__ == '__main__':
    css = brand.fonts_css()
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page()
        for name, svg, w, h in items():
            pg.set_viewport_size({'width': w, 'height': h})
            pg.set_content(f'<html><head><style>{css} html,body{{margin:0;background:transparent}} svg{{display:block;width:{w}px;height:{h}px}}</style></head><body>{svg}</body></html>')
            pg.evaluate('document.fonts.ready.then(()=>1)')
            pg.wait_for_timeout(60)
            pg.screenshot(path=f'{OUT}/{name}.png', omit_background=True)
        b.close()
    print('ok', len(items()))
