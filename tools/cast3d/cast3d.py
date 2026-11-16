"""The 3D cast: Sam, Penny, Rex, Zara, Grace, Dev, Maya and Dot, modelled from the 2D drawings' coordinates.
Run with Blender's Python:  bpyenv/bin/python cast3d.py <who|all|group> [expr] [out.png] [w h samples]"""
import sys, math, random
import os
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from b3d import *

INK = '#15191F'
TORSO = [(0.60, 0.0, 0.0), (0.63, 0.42, 0.30), (0.70, 0.66, 0.46), (0.95, 0.72, 0.49), (1.35, 0.69, 0.47),
         (1.70, 0.63, 0.43), (1.92, 0.52, 0.37), (2.06, 0.32, 0.27), (2.12, 0.0, 0.0)]
TORSO_UV = (-0.8, 0.8, 0.59, 2.19)


def fabric(name, col, **kw):
    return mat(name, col, rough=0.82, sheen=0.5, **kw)


class Person:
    def __init__(self, key, root, skin, head=(160, 144, 78), eye_y=152, eye_r=(14, 18), iris='#3A2416', hair=INK, expr='happy'):
        self.key, self.root, self.expr = key, root, expr
        self.H = Head(*head)
        self.skin_col = skin
        self.skin = mat('skin_' + key, skin, rough=0.5, sss=0.2, spec=0.35)
        self.eye_y, self.eye_r, self.iris, self.hair = eye_y, eye_r, iris, hair

    def head(self):
        H = self.H
        m = mat(f'face_{self.key}_{self.expr}', self.skin_col, rough=0.5, sss=0.2, spec=0.35, decal=f'face_{self.key}_{self.expr}')
        ellipsoid(self.key + '_head', H.c, (H.R, H.R * 0.97, H.R * 0.99), m, self.root, segs=72, rings=36, uv=(-H.R, H.R, -H.R, H.R))
        # nose and ears
        s, n = H.surf(160, self.eye_y + 19)
        ellipsoid(self.key + '_nose', s - n * 0.025, (0.075, 0.06, 0.062), self.skin, self.root, align(n), segs=24, rings=12)
        ez = P(0, self.eye_y + 2).z
        for sx in (-1, 1):
            ellipsoid(f'{self.key}_ear{sx}', (H.c.x + sx * H.R * 0.97, H.c.y + 0.05, ez), (0.08, 0.11, 0.14), self.skin, self.root, segs=24, rings=12)
        # eyes and brows
        rx, ry = self.eye_r[0] / 100 * 0.95, self.eye_r[1] / 100 * 0.95
        for side, x in ((-1, 132), (1, 188)):
            s, n = H.surf(x, self.eye_y)
            eye(f'{self.key}_eye{side}', s, n, rx, ry, self.iris, self.expr, self.root, side)
        brows_on(self.key, lambda x, y: H.surf(x, y, 0.02), 132, 188, self.eye_y - 25, self.hair, self.expr, self.root)

    def lashes(self, col=INK):
        H, m = self.H, mat('ink', INK, rough=0.4)
        rx, ry = self.eye_r
        for k, (x, dx) in enumerate(((132 - rx * 0.85, -1), (188 + rx * 0.85, 1))):
            for j, (oy, lx, ly) in enumerate(((-ry * 0.45, 8, -5), (-ry * 0.75, 6, -8))):
                a = H.surf(x, self.eye_y + oy, 0.045)[0]
                b = H.surf(x + dx * lx, self.eye_y + oy + ly, 0.03)[0]
                sweep(f'{self.key}_lash{k}{j}', [a, b], 0.014, m, self.root, segs=10, rf=lambda t: 1 - 0.6 * t)

    def torso(self, m, prof=TORSO):
        lathe(self.key + '_torso', prof, m, self.root, uv=TORSO_UV)
        return prof

    def legs(self, pants, shoe, sole='#EDE8DF', stripe=None, cuff=None):
        for sx in (-1, 1):
            sweep(f'{self.key}_leg{sx}', [(sx * 0.17, 0.0, 0.98), (sx * 0.185, -0.01, 0.55), (sx * 0.19, -0.02, 0.2)], 0.16, pants, self.root, segs=24)
            ellipsoid(f'{self.key}_shoe{sx}', (sx * 0.19, -0.09, 0.135), (0.17, 0.27, 0.125), shoe, self.root, segs=32, rings=16)
            ellipsoid(f'{self.key}_sole{sx}', (sx * 0.19, -0.09, 0.05), (0.185, 0.29, 0.052), mat('sole_' + sole, sole, rough=0.6), self.root, segs=32, rings=12)
            if stripe:
                ellipsoid(f'{self.key}_stripe{sx}', (sx * 0.345, -0.06, 0.13), (0.02, 0.15, 0.032), stripe, self.root, segs=20, rings=10)
            if cuff:
                sweep(f'{self.key}_cuff{sx}', [(sx * 0.19 + 0.17 * math.cos(a), -0.02 + 0.17 * math.sin(a), 0.33) for a in
                                               [2 * math.pi * i / 12 for i in range(12)]], 0.06, cuff, self.root, cyclic=True, segs=14)

    def arm(self, name, pts, sleeve, hand, hr=(0.125, 0.11, 0.135), r=0.125):
        sweep(f'{self.key}_{name}', pts, r, sleeve, self.root, segs=24)
        return ellipsoid(f'{self.key}_{name}_hand', hand, hr, self.skin, self.root, segs=28, rings=14)


def curly(key, H, col, root, shell=1.0, ball=(0.11, 0.15), n=320, front_z=0.55, side_z=0.2, back_z=-0.4, face_w=0.62, extra=(), seed=3,
          top=1.0, jit=0.05, base_t=None, avoid=(), avoid_r=0.2):
    """Curly hair: a base shell plus many overlapping curls (spheres), like the 2D drawing's circles."""
    rnd = random.Random(seed)
    m = mat('hair_' + key, col, rough=0.5, sheen=0.25, coat=0.25, coat_rough=0.3)
    if base_t:
        cap(key + '_hairbase', H.c, H.R * 1.0, base_t, m, root, thick=0.06, sub=1)
    k = 0
    for d in fib(n):
        f, b = max(0.0, -d.y), max(0.0, d.y)
        lim = front_z * f + back_z * b + side_z * max(0.0, 1 - f - b)
        if d.z < lim:
            continue
        if d.y < -0.3 and abs(d.x) < face_w and d.z < front_z + 0.05:
            continue
        rr = H.R * (shell + rnd.uniform(-jit, jit)) * (1 + 0.08 * max(0, d.z) * top)
        r = rnd.uniform(*ball)
        pc = H.c + d * rr
        if any((pc - a).length < avoid_r for a in avoid):
            continue
        ellipsoid(f'{key}_curl{k}', pc, (r, r, r), m, root, segs=14, rings=8)
        k += 1
    for (cc, r) in extra:
        ellipsoid(f'{key}_curl{k}', cc, (r, r, r), m, root, segs=14, rings=8)
        k += 1


def glasses(key, H, ey, col, root, w=0.235, h=0.235, shape=2.0, r=0.027, up=0.0):
    m = mat('frame_' + col, col, rough=0.25, coat=0.6)
    yf = min(H.surf(132, ey)[0].y, H.surf(188, ey)[0].y) - 0.11
    cs = []
    for x in (132, 188):
        c = P(x, ey)
        c = Vector((c.x, yf, c.z + up))
        cs.append(c)
        pts = []
        for i in range(32):
            a = 2 * math.pi * i / 32
            ca, sa = math.cos(a), math.sin(a)
            px = w * math.copysign(abs(ca) ** (2 / shape), ca)
            pz = h * math.copysign(abs(sa) ** (2 / shape), sa)
            pts.append(c + Vector((px, 0, pz)))
        sweep(f'{key}_lens{x}', pts, r, m, root, cyclic=True, segs=14)
    a, b = cs[0] + Vector((w, 0, 0.02)), cs[1] - Vector((w, 0, -0.02))
    sweep(key + '_bridge', [a, (a + b) / 2 + Vector((0, -0.01, 0.06)), b], r * 0.85, m, root, segs=12)
    for k, c in enumerate(cs):
        sx = -1 if k == 0 else 1
        o = c + Vector((sx * w, 0, 0.03))
        ear = Vector((sx * (H.R * 0.97), H.c.y + 0.05, c.z + 0.06))
        sweep(f'{key}_temple{k}', [o, o + Vector((sx * 0.08, 0.12, 0.0)), ear], r * 0.8, m, root, segs=10)


def sheet_frame(center, deg):
    return Matrix.Translation(Vector(center)) @ Ry(deg).to_4x4()


def paper_eyes(key, M, cx, cy, xs, y, r, iris, expr, root, depth):
    """Googly eyes and brows on a flat sheet whose drawing is centred at SVG (cx, cy)."""
    R3 = M.to_3x3()
    n = (R3 @ Vector((0, -1, 0))).normalized()

    def surf(x, yy, off=0.0):
        return M @ Vector(((x - cx) / 100, -depth - off, (cy - yy) / 100)), n
    for side, x in zip((-1, 1), xs):
        s, _ = surf(x, y)
        eye(f'{key}_eye{side}', s, n, r[0], r[1], iris, expr, root, side)
    brows_on(key, lambda x, yy: surf(x, yy, 0.02), xs[0], xs[1], y - 22, INK, expr, root, r=0.036)


def limbs_ink(key, paths, root, r=0.042):
    m = mat('ink', INK, rough=0.4)
    for i, pts in enumerate(paths):
        sweep(f'{key}_limb{i}', pts, r, m, root, segs=12)


def glove(name, c, root):
    ellipsoid(name, c, (0.14, 0.12, 0.14), mat('glove', '#FAFAF7', rough=0.6, sheen=0.3), root, segs=28, rings=14)


def kick_shoe(name, c, deg, root, col='#C23A2B'):
    rot = Ry(deg)
    ellipsoid(name, c, (0.24, 0.15, 0.11), mat('shoe_' + col, col, rough=0.35, coat=0.3), root, rot, segs=32, rings=16)
    ellipsoid(name + '_sole', Vector(c) + rot @ Vector((0, 0, -0.08)), (0.25, 0.16, 0.04), mat('sole_#F4F1EA', '#F4F1EA', rough=0.6), root, rot, segs=28, rings=10)


# ======================================================================== the cast
def sam(root, expr='happy'):
    p = Person('sam', root, '#C98B5E', (160, 142, 80), 148, (15, 19), '#4A2C1A', '#2E1F14', expr)
    p.head()
    H = p.H
    curly('sam', H, '#2E1F14', root, shell=1.06, ball=(0.12, 0.16), n=300, front_z=0.5, side_z=0.18, back_z=-0.35, face_w=0.7, jit=0.05,
          base_t=lambda ph: 62 if math.sin(math.radians(ph)) < 0 else 112)
    hood = fabric('hoodie', '#0E8A60', decal='torso_sam')
    prof = p.torso(hood)
    hm = fabric('hoodie2', '#0E8A60')
    sweep('sam_hoodring', [(0.38 * math.cos(a), 0.06 + 0.32 * math.sin(a), 2.05 - 0.05 * math.sin(a)) for a in [2 * math.pi * i / 16 for i in range(16)]],
          0.11, hm, root, cyclic=True, segs=18)
    ellipsoid('sam_hoodback', (0, 0.38, 2.0), (0.40, 0.22, 0.30), hm, root)
    white = mat('string', '#F4F1EA', rough=0.6)
    gold = mat('yellow', '#FFD84D', rough=0.35, coat=0.4)
    for sx in (-1, 1):
        sweep(f'sam_string{sx}', [(sx * 0.13, -0.30, 2.04), (sx * 0.135, -0.44, 1.84), (sx * 0.125, -0.48, 1.62)], 0.022, white, root, segs=10)
        ellipsoid(f'sam_aglet{sx}', (sx * 0.125, -0.49, 1.58), (0.032, 0.032, 0.055), gold, root, segs=16, rings=8)
    s, n = lathe_front(prof, 0.38, 1.54)
    ellipsoid('sam_badge', s + n * 0.012, (0.115, 0.03, 0.115), mat('badge', '#FFD84D', rough=0.35, coat=0.5, decal='bolt'), root, align(n),
              uv=(-0.115, 0.115, -0.115, 0.115))
    # arms: waving (viewer's left) and the coffee (viewer's right)
    p.arm('armL', [(-0.48, 0.0, 1.80), (-0.70, -0.10, 1.92), (-0.84, -0.18, 2.14), (-0.88, -0.22, 2.30)], hm, (-0.88, -0.24, 2.44))
    ellipsoid('sam_thumb', (-0.76, -0.30, 2.42), (0.045, 0.04, 0.07), p.skin, root, Rz(20), segs=16, rings=8)
    p.arm('armR', [(0.48, 0.0, 1.80), (0.70, -0.10, 1.60), (0.78, -0.24, 1.40), (0.76, -0.33, 1.30)], hm, (0.74, -0.42, 1.27))
    cup = (0.88, -0.52)
    lathe('sam_cup', [(1.06, 0.0, 0.0), (1.065, 0.12, 0.12), (1.25, 0.138, 0.138), (1.42, 0.155, 0.155), (1.425, 0.0, 0.0)],
          mat('cup', '#FBFAF6', rough=0.3, coat=0.3), root, c=cup)
    lathe('sam_sleeve', [(1.17, 0.0, 0.0), (1.172, 0.136, 0.136), (1.30, 0.150, 0.150), (1.302, 0.0, 0.0)], gold, root, c=cup)
    lathe('sam_lid', [(1.40, 0.0, 0.0), (1.405, 0.168, 0.168), (1.45, 0.165, 0.165), (1.48, 0.11, 0.11), (1.50, 0.0, 0.0)],
          mat('lid', '#E8E2D4', rough=0.4), root, c=cup)
    p.legs(fabric('pants_sam', '#3A3F47'), mat('shoe_white', '#F7F5F0', rough=0.4, coat=0.2), '#E3DDD2', gold)


def penny(root, expr='happy'):
    p = Person('penny', root, '#8A5A3C', (160, 144, 78), 152, (13, 16), '#3A2416', '#1E1714', expr)
    p.head()
    H = p.H
    hair = mat('hair_penny', '#1E1714', rough=0.45, sheen=0.3, coat=0.3, coat_rough=0.25, bump='hair')

    def tmax(ph):
        s, c = math.sin(math.radians(ph)), math.cos(math.radians(ph))
        f, b = max(0.0, -s), max(0.0, s)
        return (56 - 9 * c) * f + 124 * b + 100 * max(0.0, 1 - f - b)
    cap('penny_hair', H.c, H.R * 1.02, tmax, hair, root, thick=0.075)
    ellipsoid('penny_bun', (0, 0.16, 3.60), (0.30, 0.28, 0.28), hair, root)
    pen_y, pen_p, pen_w = mat('pencil', '#FFD84D', rough=0.35, coat=0.4), mat('eraser', '#F2A6A0', rough=0.6), mat('wood', '#E7C49A', rough=0.7)
    a0, a1 = Vector((-0.26, 0.10, 3.40)), Vector((0.30, 0.18, 3.82))
    sweep('penny_bunpencil', [a0, a1], 0.05, pen_y, root, sides=6, caps=False)
    sweep('penny_bunpencil_e', [a1, a1 + (a1 - a0).normalized() * 0.09], 0.05, pen_p, root)
    sweep('penny_bunpencil_t', [a0, a0 - (a1 - a0).normalized() * 0.12], 0.05, pen_w, root, rf=lambda t: 1 - 0.95 * t, caps=False)
    glasses('penny', H, 152, '#C23A2B', root, w=0.235, h=0.235)
    gold = mat('yellow', '#FFD84D', rough=0.35, coat=0.4)
    for sx in (-1, 1):
        ellipsoid(f'penny_earring{sx}', (sx * 0.77, -0.06, 2.53), (0.055,) * 3, gold, root, segs=16, rings=8)
    card = fabric('cardigan', '#FFD84D', decal='torso_penny')
    p.torso(card)
    green = mat('bow', '#0B7955', rough=0.5, sheen=0.3)
    for sx in (-1, 1):
        ellipsoid(f'penny_bow{sx}', (sx * 0.10, -0.33, 2.02), (0.12, 0.05, 0.085), green, root, Ry(-sx * 12), segs=24, rings=12)
    ellipsoid('penny_knot', (0, -0.36, 2.02), (0.05, 0.04, 0.05), mat('bow2', '#0A6A4B', rough=0.5), root, segs=16, rings=8)
    c2 = fabric('cardigan2', '#FFD84D')
    p.arm('armL', [(-0.48, 0.0, 1.80), (-0.70, -0.12, 1.55), (-0.70, -0.30, 1.22), (-0.62, -0.40, 1.08)], c2, (-0.60, -0.48, 1.06))
    rbox('penny_ledger', (-0.70, -0.58, 1.02), (0.35, 0.065, 0.44), mat('ledger', '#C23A2B', rough=0.55, sheen=0.2, decal='ledger'), root, Ry(-12),
         p=8, uv=(-0.35, 0.35, -0.44, 0.44))
    p.arm('armR', [(0.48, 0.0, 1.80), (0.72, -0.10, 1.95), (0.86, -0.18, 2.18), (0.90, -0.22, 2.30)], c2, (0.90, -0.26, 2.42))
    b0, b1 = Vector((0.80, -0.34, 2.20)), Vector((1.10, -0.34, 2.86))
    sweep('penny_pencil', [b0, b1], 0.055, pen_y, root, sides=6, caps=False)
    sweep('penny_pencil_e', [b1, b1 + (b1 - b0).normalized() * 0.10], 0.055, pen_p, root)
    sweep('penny_pencil_t', [b0, b0 - (b1 - b0).normalized() * 0.14], 0.055, pen_w, root, rf=lambda t: 1 - 0.95 * t, caps=False)
    p.legs(fabric('pants_penny', '#4A4F58'), mat('shoe_red', '#C23A2B', rough=0.35, coat=0.3), '#F4F1EA')


def zara(root, expr='happy'):
    p = Person('zara', root, '#D9A07A', (160, 144, 78), 152, (14, 18), '#4A2C1A', '#1F1612', expr)
    p.head()
    p.lashes()
    H = p.H
    hair = mat('hair_zara', '#1F1612', rough=0.42, sheen=0.3, coat=0.35, coat_rough=0.2, bump='hair')

    def tmax(ph):
        s = math.sin(math.radians(ph))
        f, b = max(0.0, -s), max(0.0, s)
        return 54 * f + 116 * b + 104 * max(0.0, 1 - f - b)

    def rfn(th, ph):
        s = math.sin(math.radians(ph))
        part = math.exp(-((ph + 90) / 9) ** 2) * max(0.0, 1 - th / 60) * 0.035 if s < 0 else 0
        return H.R * 1.03 - part
    cap('zara_hair', H.c, H.R * 1.03, tmax, hair, root, thick=0.08, rfn=rfn)
    ellipsoid('zara_back', (0, 0.30, 2.30), (0.66, 0.34, 0.66), hair, root)
    for sx in (-1, 1):
        ellipsoid(f'zara_curtain{sx}', (sx * 0.70, 0.05, 2.40), (0.17, 0.26, 0.52), hair, root, Ry(sx * 8), segs=28, rings=16)
    gold = mat('gold', '#E8B83A', rough=0.25, metal=1.0)
    for sx in (-1, 1):
        c = Vector((sx * 0.80, -0.10, 2.20))
        sweep(f'zara_hoop{sx}', [c + Vector((0.075 * math.cos(a), 0, 0.075 * math.sin(a))) for a in [2 * math.pi * i / 16 for i in range(16)]],
              0.014, gold, root, cyclic=True, segs=10)
    blazer = fabric('blazer', '#E0664F', decal='torso_zara')
    p.torso(blazer)
    b2 = fabric('blazer2', '#E0664F')
    p.arm('armL', [(-0.48, 0.0, 1.80), (-0.66, 0.0, 1.70), (-0.84, 0.0, 1.60)], b2, (-0.94, 0.0, 1.55))
    case = mat('case', '#0B7955', rough=0.3, coat=0.5)
    rbox('zara_case', (-1.00, 0.08, 0.58), (0.40, 0.21, 0.41), case, root, p=7)
    rbox('zara_band', (-1.00, 0.08, 0.62), (0.405, 0.215, 0.055), mat('yellow', '#FFD84D', rough=0.35, coat=0.4), root, p=10)
    for x in (-1.24, -0.76):
        sweep(f'zara_rib{x}', [(x, -0.14, 0.30), (x, -0.14, 0.88)], 0.03, mat('case2', '#0A6A4B', rough=0.3, coat=0.5), root, segs=12)
    metal = mat('steel', '#9AA0A8', rough=0.3, metal=0.9)
    sweep('zara_pole', [(-0.96, 0.08, 0.95), (-0.96, 0.08, 1.48)], 0.035, metal, root, segs=12)
    rbox('zara_grip', (-0.96, 0.08, 1.52), (0.11, 0.05, 0.045), mat('grip', '#3A3F47', rough=0.5), root, p=6)
    for x in (-1.22, -0.78):
        ellipsoid(f'zara_wheel{x}', (x, 0.08, 0.09), (0.05, 0.09, 0.09), mat('wheel', '#2A2E35', rough=0.5), root, segs=20, rings=10)
    p.arm('armR', [(0.48, 0.0, 1.80), (0.72, -0.08, 1.98), (0.86, -0.16, 2.20), (0.90, -0.20, 2.30)], b2, (0.90, -0.24, 2.42))
    rbox('zara_passport', (0.96, -0.32, 2.80), (0.24, 0.022, 0.31), mat('passport', '#22324A', rough=0.5, sheen=0.2, decal='passport'), root, Ry(14),
         p=10, uv=(-0.24, 0.24, -0.31, 0.31))
    p.legs(fabric('pants_zara', '#2E3A4F'), mat('shoe_green', '#0B7955', rough=0.35, coat=0.3), '#F4F1EA')


def grace(root, expr='happy'):
    p = Person('grace', root, '#F2C9A8', (160, 144, 78), 152, (13, 16), '#3E5A73', '#8E949C', expr)
    p.head()
    H = p.H
    hair = mat('hair_grace', '#C3C8D0', rough=0.38, sheen=0.6, coat=0.3, coat_rough=0.2, bump='hair')

    def tmax(ph):
        s, c = math.sin(math.radians(ph)), math.cos(math.radians(ph))
        f, b = max(0.0, -s), max(0.0, s)
        return (58 + 10 * c) * f + 120 * b + 118 * max(0.0, 1 - f - b)

    def rfn(th, ph):
        t = min(max((th - 78) / 40, 0.0), 1.0)
        return H.R * 1.04 + 0.17 * t * t * (3 - 2 * t)
    cap('grace_hair', H.c, H.R * 1.0, lambda ph: tmax(ph) - 6, hair, root, thick=0.06, rfn=lambda th, ph: rfn(th, ph) - 0.04, sub=1)
    for i in range(22):
        ph0 = -90 + 360 * i / 22
        front = math.sin(math.radians(ph0)) < -0.55
        sweep_deg = 30 if front else 0
        t_end = tmax(ph0) + (4 if not front else 2)
        pts = []
        for k in range(9):
            t = k / 8
            th = 6 + (t_end - 6) * t
            ph = math.radians(ph0 + sweep_deg * t)
            rr = rfn(th, ph0) + 0.03 - (0.05 * max(0.0, t - 0.8) / 0.2 if not front else 0)
            pts.append(H.c + Vector((math.sin(math.radians(th)) * math.cos(ph), math.sin(math.radians(th)) * math.sin(ph), math.cos(math.radians(th)))) * rr)
        side = (pts[0] - H.c).normalized()
        sweep(f'grace_lock{i}', pts, 0.19, hair, root, flat=0.32, side=side, segs=16, rf=lambda t: 0.75 + 0.35 * math.sin(math.pi * min(t, 0.85) / 0.85) - 0.22 * max(0, t - 0.85) / 0.15)
    # emerald glasses pushed up on the hair
    gm = mat('frame_#0B7955', '#0B7955', rough=0.25, coat=0.6)
    rot = Rx(-42)
    for x in (-0.25, 0.25):
        c = Vector((x, -0.60, 3.40))
        pts = []
        for i in range(32):
            a = 2 * math.pi * i / 32
            ca, sa = math.cos(a), math.sin(a)
            pts.append(c + rot @ Vector((0.17 * math.copysign(abs(ca) ** 0.5, ca), 0, 0.11 * math.copysign(abs(sa) ** 0.5, sa))))
        sweep(f'grace_lens{x}', pts, 0.024, gm, root, cyclic=True, segs=12)
    sweep('grace_bridge', [(-0.08, -0.62, 3.42), (0, -0.64, 3.45), (0.08, -0.62, 3.42)], 0.022, gm, root, segs=10)
    suit = fabric('suit', '#2B3445', decal='torso_grace')
    prof = [(0.56, 0.0, 0.0), (0.60, 0.46, 0.33), (0.66, 0.70, 0.48)] + TORSO[3:]
    p.torso(suit, prof)
    pearl = mat('pearl', '#F7F4EE', rough=0.15, coat=1.0, sss=0.1)
    for x, y in ((146, 236), (152, 247), (160, 252), (168, 247), (174, 236)):
        s, n = lathe_front(prof, P(x, y).x, P(x, y).z)
        ellipsoid(f'grace_pearl{x}{y}', s + n * 0.035, (0.042,) * 3, pearl, root, segs=16, rings=8)
    s, n = lathe_front(prof, 0.40, 1.66)
    rbox('grace_square', s + n * 0.02, (0.07, 0.02, 0.05), mat('yellow', '#FFD84D', rough=0.35, coat=0.4), root, align(n) @ Ry(25), p=4)
    s2 = fabric('suit2', '#2B3445')
    p.arm('armL', [(-0.48, 0.0, 1.80), (-0.78, 0.04, 1.60), (-0.90, 0.04, 1.40), (-0.74, -0.06, 1.24)], s2, (-0.64, -0.12, 1.21))
    p.arm('armR', [(0.48, 0.0, 1.80), (0.70, -0.10, 1.96), (0.82, -0.20, 2.12), (0.86, -0.24, 2.20)], s2, (0.87, -0.28, 2.27))
    sweep('grace_handle', [(0.88, -0.32, 2.16), (1.02, -0.32, 2.52)], 0.045, mat('handle', '#8A5A3C', rough=0.4, coat=0.5), root, segs=14)
    lc = Vector((1.09, -0.32, 2.80))
    sweep('grace_ring', [lc + Vector((0.25 * math.cos(a), 0, 0.25 * math.sin(a))) for a in [2 * math.pi * i / 24 for i in range(24)]],
          0.035, mat('ring', '#2B2F36', rough=0.3, metal=0.6), root, cyclic=True, segs=14)
    ellipsoid('grace_lens', lc, (0.235, 0.018, 0.235), mat('glass', '#EAF4EF', rough=0.03, trans=1.0, ior=1.5), root, segs=40, rings=12)
    p.legs(fabric('pants_grace', '#2B3445'), mat('shoe_green', '#0B7955', rough=0.35, coat=0.3), '#F4F1EA')


def dev(root, expr='happy'):
    p = Person('dev', root, '#B07A52', (160, 144, 78), 162, (14, 18), '#2B1A10', '#141414', expr)
    p.head()
    H = p.H
    knit = mat('beanie', '#C23A2B', rough=0.8, sheen=0.6, bump='knit')
    cap('dev_beanie', H.c, H.R * 1.04, lambda ph: 68 if math.sin(math.radians(ph)) < 0 else 74, knit, root, thick=0.09)
    cap('dev_cuff', H.c, H.R * 1.12, lambda ph: 76 if math.sin(math.radians(ph)) < 0 else 82, mat('beanie2', '#A12E22', rough=0.8, sheen=0.6, bump='rib'),
        root, thick=0.07, tmin=lambda ph: 52 if math.sin(math.radians(ph)) < 0 else 58)
    ellipsoid('dev_pom', (0, 0.04, 3.80), (0.17, 0.17, 0.16), mat('pom', '#FFD84D', rough=0.9, sheen=1.0, bump='fuzz'), root)
    hairm = mat('hair_dev', '#141414', rough=0.6, sheen=0.3)
    for sx in (-1, 1):
        ellipsoid(f'dev_side{sx}', (sx * 0.74, -0.02, 2.86), (0.08, 0.18, 0.13), hairm, root, segs=20, rings=10)
    glasses('dev', H, 162, INK, root, w=0.20, h=0.165, shape=6.0, r=0.03)
    tee = fabric('tee', '#3A3F47', decal='torso_dev')
    p.torso(tee)
    phones = mat('phones', '#0B7955', rough=0.35, coat=0.4)
    sweep('dev_band', [(-0.44, -0.18, 2.04), (-0.36, -0.40, 1.82), (0.0, -0.49, 1.72), (0.36, -0.40, 1.82), (0.44, -0.18, 2.04)], 0.038, phones, root, segs=14)
    for sx in (-1, 1):
        rbox(f'dev_cup{sx}', (sx * 0.47, -0.22, 2.04), (0.10, 0.08, 0.15), phones, root, Rz(sx * 25), p=4)
    t2 = fabric('tee2', '#3A3F47')
    p.arm('armL', [(-0.48, 0.0, 1.80), (-0.72, -0.10, 1.92), (-0.84, -0.18, 2.08), (-0.86, -0.22, 2.14)], t2, (-0.86, -0.25, 2.22))
    sweep('dev_finger', [(-0.88, -0.29, 2.30), (-0.90, -0.29, 2.50)], 0.045, p.skin, root, segs=14)
    p.arm('armR', [(0.48, 0.0, 1.80), (0.70, -0.10, 1.55), (0.82, -0.25, 1.36), (0.84, -0.32, 1.30)], t2, (0.84, -0.40, 1.28))
    alu = mat('alu', '#C9CDD3', rough=0.3, metal=0.7)
    rbox('dev_base', (1.06, -0.76, 1.37), (0.46, 0.30, 0.026), alu, root, p=8)
    rbox('dev_screen', (1.06, -0.47, 1.68), (0.42, 0.024, 0.30), mat('screen', '#C9CDD3', rough=0.3, metal=0.5, decal='screen'), root, Rx(-8),
         p=8, uv=(-0.37, 0.37, -0.25, 0.27))
    p.legs(fabric('denim', '#3D5A80'), mat('shoe_white', '#F7F5F0', rough=0.4, coat=0.2), '#E3DDD2', mat('stripe_red', '#C23A2B', rough=0.4))


def maya(root, expr='happy'):
    p = Person('maya', root, '#F0BE96', (160, 144, 78), 154, (14, 18), '#3B6B4F', '#9A4A2A', expr)
    p.head()
    p.lashes()
    H = p.H
    extra = []
    for sx in (-1, 1):
        for i, z in enumerate((2.40, 2.20, 2.02)):
            for y in (-0.12, 0.12, 0.36):
                extra.append(((sx * (0.84 - 0.05 * i), y, z), 0.17))
    for y, z in ((0.50, 2.45), (0.55, 2.22), (0.45, 2.04)):
        for x in (-0.45, -0.15, 0.15, 0.45):
            extra.append(((x, y, z), 0.18))
    band = mat('yellow', '#FFD84D', rough=0.35, coat=0.4)
    pts = []
    for i in range(17):
        a = math.radians(8 + 164 * i / 16)
        v = Rx(14) @ Vector((math.cos(a), 0, math.sin(a)))
        pts.append(H.c + v * H.R * 1.24)
    sweep('maya_band', pts, 0.08, band, root, flat=0.5, side=(0, -1, 0.4))
    curly('maya', H, '#9A4A2A', root, shell=1.10, ball=(0.14, 0.19), n=300, front_z=0.52, side_z=-0.5, back_z=-0.7, face_w=0.74, extra=extra, seed=7,
          top=1.3, base_t=lambda ph: 60 if math.sin(math.radians(ph)) < 0 else 120, avoid=spline(pts, 60), avoid_r=0.2)
    red = mat('stud', '#C23A2B', rough=0.3, coat=0.6)
    for sx in (-1, 1):
        ellipsoid(f'maya_stud{sx}', (sx * 0.79, -0.12, 2.42), (0.045,) * 3, red, root, segs=14, rings=8)
    shirt = mat('stripes', '#FBF8F0', rough=0.8, sheen=0.4, stripes=('#C23A2B', 9.0, 0.42))
    p.torso(shirt)
    ov = fabric('overall', '#0B7955')
    lathe('maya_overall', [(0.58, 0.0, 0.0), (0.62, 0.44, 0.32), (0.69, 0.69, 0.48), (0.95, 0.745, 0.51), (1.25, 0.72, 0.495), (1.33, 0.715, 0.49), (1.335, 0.0, 0.0)], ov, root)
    s, n = lathe_front(TORSO, 0.0, 1.62)
    rbox('maya_bib', s + n * 0.01 + Vector((0, 0, 0)), (0.34, 0.035, 0.30), ov, root, Rx(-10), p=6)
    for sx in (-1, 1):
        sweep(f'maya_strap{sx}', [(sx * 0.27, -0.46, 1.86), (sx * 0.31, -0.32, 2.04), (sx * 0.32, 0.0, 2.10), (sx * 0.30, 0.30, 1.92)], 0.05, ov, root,
              flat=0.45, side=(0, 0, 1), segs=14)
        ellipsoid(f'maya_button{sx}', (sx * 0.26, -0.52, 1.84), (0.05, 0.03, 0.05), mat('gold', '#E8B83A', rough=0.25, metal=1.0), root, segs=16, rings=8)
    rbox('maya_pocket', (0, -0.53, 1.52), (0.14, 0.02, 0.11), fabric('overall2', '#0A6A4B'), root, Rx(-10), p=6)
    sweep('maya_pocketline', [(-0.07, -0.555, 1.57), (0.07, -0.555, 1.57)], 0.014, band, root, segs=8)
    p.arm('armL', [(-0.48, 0.0, 1.80), (-0.70, -0.10, 1.92), (-0.84, -0.18, 2.14), (-0.88, -0.22, 2.30)], shirt, (-0.88, -0.24, 2.44))
    p.arm('armR', [(0.48, 0.0, 1.80), (0.70, -0.10, 1.62), (0.80, -0.24, 1.36), (0.80, -0.32, 1.24)], shirt, (0.80, -0.40, 1.20))
    rbox('maya_invoice', (1.00, -0.48, 1.36), (0.35, 0.012, 0.45), mat('paper', '#FFFFFF', rough=0.85, sss=0.05, decal='invoice'), root, Ry(8),
         p=10, uv=(-0.35, 0.35, -0.45, 0.45))
    p.legs(ov, mat('shoe_white', '#F7F5F0', rough=0.4, coat=0.2), '#E3DDD2', band, cuff=band)


def rex(root, expr='sly'):
    cx, cy, deg = 149, 213, 9
    M = sheet_frame(P(cx, cy), deg)
    w, h, teeth = 1.14, 2.98, 10
    bm = bmesh.new()
    nx, nz = teeth * 2, 30
    grid = []
    for i in range(nz + 1):
        row = []
        for j in range(nx + 1):
            x = -w / 2 + w * j / nx
            z = -h / 2 + h * i / nz
            if i == nz and j % 2 == 1:
                z += 0.10
            if i == 0 and j % 2 == 1:
                z -= 0.10
            row.append(bm.verts.new((x, 0.0, z)))
        grid.append(row)
    for i in range(nz):
        for j in range(nx):
            bm.faces.new((grid[i][j], grid[i][j + 1], grid[i + 1][j + 1], grid[i + 1][j]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    paper = mat('receipt', '#FBFAF7', rough=0.85, sss=0.06, decal='rex_front')
    ob = None
    lay = bm.loops.layers.uv.new('decal')
    for f in bm.faces:
        for lp in f.loops:
            co = lp.vert.co
            lp[lay].uv = ((co.x + w / 2) / w, (co.z + h / 2) / h)
    me = bpy.data.meshes.new('rex_body')
    bm.to_mesh(me)
    bm.free()
    for pl in me.polygons:
        pl.use_smooth = True
    me.materials.append(paper)
    ob = bpy.data.objects.new('rex_body', me)
    link(ob, root)
    ob.matrix_basis = M
    sol = ob.modifiers.new('solid', 'SOLIDIFY')
    sol.thickness = 0.045
    sol.offset = 0.0
    bend = ob.modifiers.new('bend', 'SIMPLE_DEFORM')
    bend.deform_method = 'BEND'
    bend.deform_axis = 'Z'
    bend.angle = math.radians(-22)
    paper_eyes('rex', M, cx, cy, (126, 172), 138, (0.15, 0.18), '#3A2416', expr, root, 0.03)
    limbs_ink('rex', [[P(98, 218, -0.05), P(72, 206, -0.08), P(57, 184, -0.1), P(53, 160, -0.1)],
                      [P(204, 226, -0.05), P(240, 232, -0.08), P(266, 218, -0.1), P(278, 196, -0.1)],
                      [P(140, 345, 0.0), P(130, 372, -0.02), P(114, 390, -0.04), P(100, 398, -0.05)],
                      [P(190, 348, 0.0), P(212, 366, -0.02), P(226, 382, -0.04), P(244, 384, -0.05)]], root)
    glove('rex_gloveL', P(52, 148, -0.12), root)
    glove('rex_gloveR', P(282, 184, -0.12), root)
    kick_shoe('rex_shoeL', P(90, 404, -0.05), 8, root)
    kick_shoe('rex_shoeR', P(262, 378, -0.05), -12, root)
    coin = mat('coin', '#E8B83A', rough=0.28, metal=1.0, decal='coin')
    for i, (x, y, r, a) in enumerate(((40, 104, 0.13, 18), (292, 132, 0.11, -14), (270, 94, 0.09, 26))):
        rb = 0.0 if i else 0
        ellipsoid(f'rex_coin{i}', P(x, y, -0.2), (r, 0.03, r), coin, root, Ry(a) @ Rz(-12 + 10 * i), segs=32, rings=12, uv=(-r, r, -r, r))
    grey = mat('speed', '#9AA0A8', rough=0.5)
    for i, (x0, x1, y) in enumerate(((28, 68, 250), (16, 62, 282), (34, 64, 314))):
        sweep(f'rex_speed{i}', [P(x0, y, 0.1), P(x1, y, 0.1)], 0.03, grey, root, segs=10)


def dot(root, expr='happy'):
    cx, cy, deg = 168, 223, -6
    M = sheet_frame(P(cx, cy), deg)
    R3 = M.to_3x3()
    page = rbox('dot_page', (0, 0, 0), (0.82, 0.045, 1.31), mat(f'dotpage_{expr}', '#FFFFFF', rough=0.8, sss=0.05, decal=f'dot_front_{expr}'), root,
                p=10, uv=(-0.82, 0.82, -1.31, 1.31), segs=64, rings=48)
    page.matrix_basis = M
    steel = mat('steel', '#9AA0A8', rough=0.3, metal=0.9)
    for x in (-0.45, 0.45):
        pts = [M @ Vector((x, -0.09, 1.16)), M @ Vector((x, -0.08, 1.40)), M @ Vector((x, 0.0, 1.50)), M @ Vector((x, 0.08, 1.40)), M @ Vector((x, 0.09, 1.16))]
        sweep(f'dot_ring{x}', pts, 0.05, steel, root, segs=14)
    paper_eyes('dot', M, cx, cy, (140, 196), 208, (0.15, 0.18), '#3A2416', expr, root, 0.045)
    limbs_ink('dot', [[P(96, 226, -0.02), P(68, 218, -0.06), P(54, 196, -0.08), P(51, 176, -0.1)],
                      [P(236, 238, -0.02), P(256, 244, -0.06), P(270, 230, -0.08), P(278, 214, -0.1)],
                      [P(142, 345, 0.0), P(134, 374, -0.02), P(124, 390, -0.04), P(110, 398, -0.05)],
                      [P(192, 348, 0.0), P(204, 372, -0.02), P(214, 386, -0.04), P(230, 390, -0.05)]], root)
    glove('dot_gloveL', P(50, 164, -0.12), root)
    gold = mat('clockgold', '#FFD84D', rough=0.3, metal=0.6, coat=0.4)
    ellipsoid('dot_clock', P(284, 184, -0.16), (0.22, 0.13, 0.22), gold, root, segs=40, rings=20)
    ellipsoid('dot_face', P(284, 184, -0.30), (0.165, 0.02, 0.165), mat('clockface', '#FFFFFF', rough=0.4, coat=0.5, decal='clock'), root,
              segs=40, rings=10, uv=(-0.165, 0.165, -0.165, 0.165))
    for x in (266, 302):
        ellipsoid(f'dot_bell{x}', P(x, 158, -0.12), (0.085,) * 3, gold, root, segs=20, rings=10)
    glove('dot_gloveR', P(280, 208, -0.22), root)
    grey = mat('speed', '#9AA0A8', rough=0.5)
    sweep('dot_ring1', [P(306, 150, -0.1), P(316, 166, -0.1), P(306, 182, -0.1)], 0.026, grey, root, segs=10)
    sweep('dot_ring2', [P(318, 140, -0.1), P(334, 166, -0.1), P(318, 194, -0.1)], 0.026, grey, root, segs=10)
    kick_shoe('dot_shoeL', P(100, 404, -0.05), 6, root)
    kick_shoe('dot_shoeR', P(242, 390, -0.05), -10, root)


CAST = {'sam': sam, 'penny': penny, 'rex': rex, 'zara': zara, 'grace': grace, 'dev': dev, 'maya': maya, 'dot': dot}
DEFAULT = {'rex': 'sly'}


def solo(who, expr=None, out=None, w=1000, h=1300, samples=64, turn=14):
    reset()
    root = empty('root_' + who, rot_z=turn)
    CAST[who](root, expr or DEFAULT.get(who, 'happy'))
    floor(catcher=True)
    studio()
    camera((0, -16, 2.8), (0, 0, 2.15), 112)
    render(out or os.path.join(HERE, 'out', who + '.png'), w, h, samples)


def group(out=os.path.join(HERE, 'out', 'group.png'), w=2400, h=1080, samples=64):
    reset()
    order = ['maya', 'zara', 'penny', 'sam', 'rex', 'dev', 'grace', 'dot']
    xs = [-8.6, -6.2, -3.7, -1.25, 1.25, 3.7, 6.2, 8.6]
    for i, (who, x) in enumerate(zip(order, xs)):
        turn = 16 if x < 0 else -16
        root = empty('root_' + who, (x, 0.6 if i % 2 else 0.0, 0), turn)
        CAST[who](root, DEFAULT.get(who, 'happy'))
    floor(catcher=False, color='#F1EADF')
    area('Key', (-9, -16, 14), (0, 0, 2.0), 12, 5200, (1.0, 0.95, 0.88))
    area('Fill', (12, -14, 5), (0, 0, 2.0), 14, 1500, (0.88, 0.94, 1.0), shadow=False)
    area('Rim', (2, 10, 11), (0, 0, 2.6), 10, 2600, (1.0, 0.97, 0.92), shadow=False)
    camera((0, -33, 3.6), (0, 0, 2.15), 52)
    render(out, w, h, samples, transparent=False)


if __name__ == '__main__':
    a = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:]
    who = a[0] if a else 'sam'
    if who == 'group':
        group(*([a[1]] if len(a) > 1 else []), *[int(v) for v in a[2:5]])
    else:
        expr = a[1] if len(a) > 1 and a[1] != '-' else None
        out = a[2] if len(a) > 2 else None
        nums = [int(v) for v in a[3:6]]
        solo(who, expr, out, *nums)
