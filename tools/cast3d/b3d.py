"""Small modelling kit for the 3D cast (Blender 5, Cycles). Shapes are built in code from the 2D cast's coordinates:
P(x, y, d) maps a point of the 320x440 SVG drawing to 3D (1 unit = 100 px, ground at y=424, the character faces -Y)."""
import bpy, bmesh, math, os
from mathutils import Vector, Matrix

TEX = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tex')


def P(x, y, d=0.0):
    return Vector(((x - 160) / 100.0, d, (424 - y) / 100.0))


def srgb(h, a=1.0):
    h = h.lstrip('#')
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple([x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c] + [a])


def Ry(deg):
    return Matrix.Rotation(math.radians(deg), 3, 'Y')


def Rx(deg):
    return Matrix.Rotation(math.radians(deg), 3, 'X')


def Rz(deg):
    return Matrix.Rotation(math.radians(deg), 3, 'Z')


# ---------------------------------------------------------------- materials
_mats = {}


def mat(name, color, rough=0.5, sss=0.0, sheen=0.0, coat=0.0, metal=0.0, spec=0.5, trans=0.0, emit=0.0, ior=1.45,
        decal=None, stripes=None, bump=None, coat_rough=0.05):
    """decal = image name in tex/ (sampled through the object's 'decal' UV map, front faces only);
    stripes = (color2, frequency per unit, share of color2) along Z; bump = 'hair' | 'rib' | 'fuzz' | 'knit'."""
    if name in _mats:
        return _mats[name]
    m = bpy.data.materials.new(name)
    try:
        m.use_nodes = True
    except Exception:
        pass
    N, L = m.node_tree.nodes, m.node_tree.links
    b = N.get('Principled BSDF')
    out = N.get('Material Output')
    b.inputs['Base Color'].default_value = srgb(color)
    b.inputs['Roughness'].default_value = rough
    b.inputs['Metallic'].default_value = metal
    b.inputs['Specular IOR Level'].default_value = spec
    b.inputs['IOR'].default_value = ior
    if sss:
        b.inputs['Subsurface Weight'].default_value = sss
        b.inputs['Subsurface Radius'].default_value = (1.0, 0.42, 0.25)
        b.inputs['Subsurface Scale'].default_value = 0.05
        try:
            b.subsurface_method = 'BURLEY'
        except Exception:
            pass
    if sheen:
        b.inputs['Sheen Weight'].default_value = sheen
        b.inputs['Sheen Roughness'].default_value = 0.45
    if coat:
        b.inputs['Coat Weight'].default_value = coat
        b.inputs['Coat Roughness'].default_value = coat_rough
    if trans:
        b.inputs['Transmission Weight'].default_value = trans
    if emit:
        b.inputs['Emission Color'].default_value = srgb(color)
        b.inputs['Emission Strength'].default_value = emit
    cur = None
    tc = N.new('ShaderNodeTexCoord')
    if stripes:
        c2, freq, share = stripes
        sep = N.new('ShaderNodeSeparateXYZ'); L.new(tc.outputs['Object'], sep.inputs[0])
        m1 = N.new('ShaderNodeMath'); m1.operation = 'MULTIPLY'; m1.inputs[1].default_value = freq
        L.new(sep.outputs['Z'], m1.inputs[0])
        fr = N.new('ShaderNodeMath'); fr.operation = 'FRACT'; L.new(m1.outputs[0], fr.inputs[0])
        gt = N.new('ShaderNodeMath'); gt.operation = 'LESS_THAN'; gt.inputs[1].default_value = share
        L.new(fr.outputs[0], gt.inputs[0])
        mix = N.new('ShaderNodeMixRGB'); mix.inputs['Color1'].default_value = srgb(color); mix.inputs['Color2'].default_value = srgb(c2)
        L.new(gt.outputs[0], mix.inputs['Fac'])
        cur = mix.outputs['Color']
    if decal:
        uv = N.new('ShaderNodeUVMap'); uv.uv_map = 'decal'
        img = N.new('ShaderNodeTexImage')
        im = bpy.data.images.load(os.path.join(TEX, decal + '.png'), check_existing=True)
        im.alpha_mode = 'STRAIGHT'
        img.image = im; img.extension = 'CLIP'; img.interpolation = 'Cubic'
        L.new(uv.outputs['UV'], img.inputs['Vector'])
        sep = N.new('ShaderNodeSeparateXYZ'); L.new(tc.outputs['Normal'], sep.inputs[0])
        mk = N.new('ShaderNodeMath'); mk.operation = 'MULTIPLY_ADD'; mk.use_clamp = True
        mk.inputs[1].default_value = -6.0; mk.inputs[2].default_value = -0.4
        L.new(sep.outputs['Y'], mk.inputs[0])
        fac = N.new('ShaderNodeMath'); fac.operation = 'MULTIPLY'
        L.new(img.outputs['Alpha'], fac.inputs[0]); L.new(mk.outputs[0], fac.inputs[1])
        mix = N.new('ShaderNodeMixRGB')
        if cur is not None:
            L.new(cur, mix.inputs['Color1'])
        else:
            mix.inputs['Color1'].default_value = srgb(color)
        L.new(img.outputs['Color'], mix.inputs['Color2'])
        L.new(fac.outputs[0], mix.inputs['Fac'])
        cur = mix.outputs['Color']
    if cur is not None:
        L.new(cur, b.inputs['Base Color'])
    if bump:
        bp = N.new('ShaderNodeBump')
        if bump == 'hair':
            w = N.new('ShaderNodeTexWave'); w.wave_type = 'BANDS'; w.bands_direction = 'X'
            w.inputs['Scale'].default_value = 9.0; w.inputs['Distortion'].default_value = 6.0; w.inputs['Detail'].default_value = 2.0
            L.new(tc.outputs['Object'], w.inputs['Vector']); L.new(w.outputs['Fac'], bp.inputs['Height'])
            bp.inputs['Strength'].default_value = 0.12
        elif bump in ('rib', 'knit'):
            w = N.new('ShaderNodeTexWave'); w.wave_type = 'RINGS'; w.rings_direction = 'Z'
            w.inputs['Scale'].default_value = 26.0 if bump == 'rib' else 40.0
            L.new(tc.outputs['Object'], w.inputs['Vector']); L.new(w.outputs['Fac'], bp.inputs['Height'])
            bp.inputs['Strength'].default_value = 0.35 if bump == 'rib' else 0.15
        else:
            nz = N.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 60.0; nz.inputs['Detail'].default_value = 4.0
            L.new(tc.outputs['Object'], nz.inputs['Vector']); L.new(nz.outputs['Fac'], bp.inputs['Height'])
            bp.inputs['Strength'].default_value = 0.4
        L.new(bp.outputs['Normal'], b.inputs['Normal'])
    _mats[name] = m
    return m


def eye_mats(iris):
    return (mat('eye_white', '#FBFAF6', rough=0.12, coat=1.0, sss=0.04),
            mat('iris_' + iris, iris, rough=0.3, coat=1.0, coat_rough=0.02),
            mat('pupil', '#0B0A09', rough=0.2, coat=1.0, coat_rough=0.02),
            mat('catch', '#FFFFFF', rough=0.5, emit=6.0))


# ---------------------------------------------------------------- objects
def link(ob, parent=None):
    bpy.context.scene.collection.objects.link(ob)
    if parent is not None:
        ob.parent = parent
    return ob


def empty(name, loc=(0, 0, 0), rot_z=0.0, parent=None):
    ob = bpy.data.objects.new(name, None)
    ob.location = loc
    ob.rotation_euler = (0, 0, math.radians(rot_z))
    return link(ob, parent)


def _finish(bm, name, m, parent, M=None, uv=None, smooth=True):
    if uv:
        x0, x1, z0, z1 = uv
        lay = bm.loops.layers.uv.new('decal')
        for f in bm.faces:
            for lp in f.loops:
                co = lp.vert.co
                lp[lay].uv = ((co.x - x0) / (x1 - x0), (co.z - z0) / (z1 - z0))
    if M is not None:
        bmesh.ops.transform(bm, matrix=M, verts=bm.verts)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    if smooth:
        for p in me.polygons:
            p.use_smooth = True
    if m is not None:
        me.materials.append(m)
    ob = bpy.data.objects.new(name, me)
    return link(ob, parent)


def xform(c, rot=None):
    M = Matrix.Translation(Vector(c))
    if rot is not None:
        M = M @ rot.to_4x4()
    return M


def ellipsoid(name, c, r, m, parent=None, rot=None, segs=40, rings=20, uv=None, sup=None):
    """Ellipsoid of radii r centred at c. sup = superellipsoid exponent (rounded box when 4..10). uv bounds are local."""
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=segs, v_segments=rings, radius=1.0)
    for v in bm.verts:
        p = v.co.copy()
        if sup:
            s = (abs(p.x) ** sup + abs(p.y) ** sup + abs(p.z) ** sup) ** (-1.0 / sup)
            p = p * s
        v.co = Vector((p.x * r[0], p.y * r[1], p.z * r[2]))
    return _finish(bm, name, m, parent, xform(c, rot), uv)


def rbox(name, c, half, m, parent=None, rot=None, p=8, uv=None, segs=48, rings=32):
    return ellipsoid(name, c, half, m, parent, rot, segs, rings, uv, sup=p)


def _cr(p0, p1, p2, p3, t):
    t2, t3 = t * t, t * t * t
    return 0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 + (-p0 + 3 * p1 - 3 * p2 + p3) * t3)


def spline(pts, n, cyclic=False):
    pts = [Vector(p) for p in pts]
    if len(pts) == 2 and not cyclic:
        return [pts[0].lerp(pts[1], i / (n - 1)) for i in range(n)]
    if cyclic:
        ext = [pts[-1]] + pts + [pts[0], pts[1]]
        segs = len(pts)
    else:
        ext = [pts[0] * 2 - pts[1]] + pts + [pts[-1] * 2 - pts[-2]]
        segs = len(pts) - 1
    out = []
    per = max(2, n // segs)
    for s in range(segs):
        p0, p1, p2, p3 = ext[s], ext[s + 1], ext[s + 2], ext[s + 3]
        for i in range(per):
            out.append(_cr(p0, p1, p2, p3, i / per))
    if not cyclic:
        out.append(pts[-1])
    return out


def sweep(name, pts, r, m, parent=None, segs=18, n=None, caps=True, cyclic=False, rf=None, flat=1.0, side=None, sides=None):
    """Tube through pts (Catmull-Rom) with round end caps. rf(t) scales the radius along the tube; flat squashes it
    across 'side' (a vector, default Y), giving ribbons for brows and bands. sides=6 makes a hexagonal pencil."""
    segs = sides or segs
    path = spline(pts, n or max(16, 10 * (len(pts) - 1)), cyclic)
    k = len(path)
    T = []
    for i in range(k):
        if cyclic:
            d = path[(i + 1) % k] - path[i - 1]
        else:
            d = path[min(i + 1, k - 1)] - path[max(i - 1, 0)]
        T.append(d.normalized())
    hint = Vector(side) if side is not None else Vector((0, 1, 0))
    B = (hint - T[0] * hint.dot(T[0]))
    if B.length < 1e-4:
        B = T[0].orthogonal()
    B.normalize()
    Nn = B.cross(T[0]).normalized()
    frames = []
    for i in range(k):
        if i > 0:
            Nn = (Nn - T[i] * Nn.dot(T[i]))
            if Nn.length < 1e-6:
                Nn = T[i].orthogonal()
            Nn.normalize()
        Bi = T[i].cross(Nn).normalized()
        frames.append((Nn.copy(), Bi))
    bm = bmesh.new()
    rings = []

    def ring(center, Nv, Bv, rad):
        vs = []
        for j in range(segs):
            a = 2 * math.pi * j / segs + (math.pi / segs if sides else 0)
            vs.append(bm.verts.new(center + Nv * (math.cos(a) * rad) + Bv * (math.sin(a) * rad * flat)))
        return vs

    def rad_at(i):
        t = i / (k - 1) if k > 1 else 0
        return r * (rf(t) if rf else 1.0)

    capk = 6
    if caps and not cyclic:
        r0 = rad_at(0)
        if r0 > 1e-5:
            pole = bm.verts.new(path[0] - T[0] * r0)
            for c in range(1, capk):
                a = (math.pi / 2) * (c / capk)
                rings.append(ring(path[0] - T[0] * (r0 * math.cos(a)), frames[0][0], frames[0][1], r0 * math.sin(a)))
            first = rings[0]
            for j in range(segs):
                bm.faces.new((pole, first[(j + 1) % segs], first[j]))
    for i in range(k):
        rings.append(ring(path[i], frames[i][0], frames[i][1], max(rad_at(i), 1e-5)))
    if caps and not cyclic:
        r1 = rad_at(k - 1)
        if r1 > 1e-5:
            for c in range(capk - 1, 0, -1):
                a = (math.pi / 2) * (c / capk)
                rings.append(ring(path[-1] + T[-1] * (r1 * math.cos(a)), frames[-1][0], frames[-1][1], r1 * math.sin(a)))
            pole2 = bm.verts.new(path[-1] + T[-1] * r1)
    for a_, b_ in zip(rings[:-1], rings[1:]):
        for j in range(segs):
            bm.faces.new((a_[j], a_[(j + 1) % segs], b_[(j + 1) % segs], b_[j]))
    if cyclic:
        a_, b_ = rings[-1], rings[0]
        for j in range(segs):
            bm.faces.new((a_[j], a_[(j + 1) % segs], b_[(j + 1) % segs], b_[j]))
    elif caps and rad_at(k - 1) > 1e-5:
        last = rings[-1]
        for j in range(segs):
            bm.faces.new((pole2, last[j], last[(j + 1) % segs]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return _finish(bm, name, m, parent, None, None, smooth=not sides)


def lathe(name, prof, m, parent=None, segs=56, n=48, c=(0.0, 0.0), uv=None):
    """Surface of revolution with elliptical rings. prof = [(z, rx, ry), ...] bottom to top, smoothed; closed at both ends."""
    pts = spline([Vector(p) for p in prof], n)
    bm = bmesh.new()
    rings = []
    for (z, rx, ry) in pts:
        rings.append([bm.verts.new((c[0] + max(rx, 0) * math.cos(2 * math.pi * j / segs), c[1] + max(ry, 0) * math.sin(2 * math.pi * j / segs), z))
                      for j in range(segs)])
    for a_, b_ in zip(rings[:-1], rings[1:]):
        for j in range(segs):
            bm.faces.new((a_[j], a_[(j + 1) % segs], b_[(j + 1) % segs], b_[j]))
    bot = bm.verts.new((c[0], c[1], pts[0][0]))
    top = bm.verts.new((c[0], c[1], pts[-1][0]))
    for j in range(segs):
        bm.faces.new((bot, rings[0][(j + 1) % segs], rings[0][j]))
        bm.faces.new((top, rings[-1][j], rings[-1][(j + 1) % segs]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return _finish(bm, name, m, parent, None, uv)


def lathe_front(prof, x, z):
    """Front surface point (most negative y) of a lathe profile at height z and offset x."""
    pts = spline([Vector(p) for p in prof], 200)
    best = min(pts, key=lambda p: abs(p[0] - z))
    rx, ry = max(best[1], 1e-3), max(best[2], 1e-3)
    u = min(abs(x) / rx, 0.999)
    y = -ry * math.sqrt(1 - u * u)
    n = Vector((x / (rx * rx), y / (ry * ry), 0)).normalized()
    return Vector((x, y, z)), n


def cap(name, center, R, tmax, m, parent=None, thick=0.07, nphi=128, nth=36, rfn=None, sub=2, tmin=None):
    """Hair or hat shell over a head: polar angle from the top (degrees) up to tmax(phi_deg); phi = -90 is the front.
    rfn(theta, phi) gives the radius (default R). Solidified outward and subdivided so the edge is a soft rim."""
    bm = bmesh.new()
    c = Vector(center)
    grid = []
    for i in range(nth + 1):
        row = []
        for j in range(nphi):
            ph = 360.0 * j / nphi
            lo = tmin(ph) if tmin else 0.0
            th = lo + (tmax(ph) - lo) * i / nth
            rr = rfn(th, ph) if rfn else R
            t, p = math.radians(th), math.radians(ph)
            row.append(c + Vector((math.sin(t) * math.cos(p), math.sin(t) * math.sin(p), math.cos(t))) * rr)
        grid.append(row)
    if tmin is None:
        pole = bm.verts.new(c + Vector((0, 0, rfn(0, 0) if rfn else R)))
        vrows = [[bm.verts.new(v) for v in row] for row in grid[1:]]
        for j in range(nphi):
            bm.faces.new((pole, vrows[0][j], vrows[0][(j + 1) % nphi]))
    else:
        vrows = [[bm.verts.new(v) for v in row] for row in grid]
    for a_, b_ in zip(vrows[:-1], vrows[1:]):
        for j in range(nphi):
            bm.faces.new((a_[j], b_[j], b_[(j + 1) % nphi], a_[(j + 1) % nphi]))
    ob = _finish(bm, name, m, parent)
    for f in ob.data.polygons:
        pass
    sol = ob.modifiers.new('solid', 'SOLIDIFY')
    sol.thickness = thick
    sol.offset = 1.0
    sol.use_even_offset = True
    if sub:
        sd = ob.modifiers.new('sub', 'SUBSURF')
        sd.levels = 1
        sd.render_levels = sub
    return ob


def cloud(name, balls, m, parent=None, res=0.03, thresh=0.6):
    mb = bpy.data.metaballs.new(name)
    mb.resolution = 0.08
    mb.render_resolution = res
    mb.threshold = thresh
    mb.materials.append(m)
    ob = bpy.data.objects.new(name, mb)
    link(ob, parent)
    for (cc, r) in balls:
        e = mb.elements.new()
        e.co = Vector(cc)
        e.radius = r
    return ob


def fib(n):
    g = math.pi * (3 - math.sqrt(5))
    out = []
    for i in range(n):
        z = 1 - 2 * (i + 0.5) / n
        rr = math.sqrt(1 - z * z)
        out.append(Vector((math.cos(g * i) * rr, math.sin(g * i) * rr, z)))
    return out


# ---------------------------------------------------------------- face parts
class Head:
    """A head sphere from the 2D drawing's circle (cx, cy, R in px)."""

    def __init__(self, cx, cy, R):
        self.c = P(cx, cy)
        self.R = R / 100.0
        self.svg = (cx, cy, R)

    def surf(self, x, y, off=0.0):
        p = P(x, y)
        dx, dz = p.x - self.c.x, p.z - self.c.z
        dy = -math.sqrt(max(self.R ** 2 - dx * dx - dz * dz, 0.0))
        s = Vector((p.x, self.c.y + dy, p.z))
        n = (s - self.c).normalized()
        return s + n * off, n

    def uv(self):
        cx, cy, R = self.svg
        a, b = P(cx - R, cy + R), P(cx + R, cy - R)
        return (a.x, b.x, a.z, b.z)


def align(n):
    """Rotation taking local -Y (the front) to direction n."""
    return Vector((0, -1, 0)).rotation_difference(n).to_matrix()


def eye(name, s, n, rx, ry, iris, expr, parent, side=1, scale=1.0):
    """One cartoon eye sitting on a surface point s with normal n. rx, ry in units. side=-1 for the viewer's left eye."""
    white, irm, pup, cat = eye_mats(iris)
    R = align(n)
    d = rx * 0.62
    if expr == 'surprised':
        ry *= 1.14
        rx *= 1.06
    if expr == 'wink' and side == 1:
        lid = [(-rx * 0.95, 0, -ry * 0.05), (0, 0, ry * 0.35), (rx * 0.95, 0, -ry * 0.05)]
        pts = [s + R @ Vector(p) - n * 0.0 + n * 0.02 for p in lid]
        return [sweep(name + '_wink', pts, 0.028, mat('ink', '#15191F', rough=0.4), parent, flat=0.6, side=n)]
    c = s + n * (0.05 - d)
    out = [ellipsoid(name + '_white', c, (rx, d, ry), white, parent, R, segs=32, rings=16)]
    ox, oz = {'happy': (0.14, -0.16), 'surprised': (0.0, 0.0), 'thinking': (-0.26, 0.30), 'sly': (0.28, -0.12), 'wink': (0.2, -0.1)}.get(expr, (0.1, -0.1))
    ir = (0.50 if expr == 'surprised' else 0.62) * rx
    lx, lz = ox * rx, oz * ry
    u = (lx / rx) ** 2 + (lz / ry) ** 2
    ly = -d * math.sqrt(max(1 - u, 0.05))
    ic = c + R @ Vector((lx, ly * 0.93, lz))
    out.append(ellipsoid(name + '_iris', ic, (ir, ir * 0.42, ir * 1.08), irm, parent, R, segs=28, rings=14))
    out.append(ellipsoid(name + '_pupil', ic + R @ Vector((0, -ir * 0.30, 0)), (ir * 0.5, ir * 0.2, ir * 0.55), pup, parent, R, segs=24, rings=12))
    out.append(ellipsoid(name + '_c1', ic + R @ Vector((-ir * 0.38, -ir * 0.48, ir * 0.42)), (ir * 0.24,) * 3, cat, parent, segs=12, rings=8))
    out.append(ellipsoid(name + '_c2', ic + R @ Vector((ir * 0.34, -ir * 0.45, -ir * 0.30)), (ir * 0.11,) * 3, cat, parent, segs=10, rings=6))
    return out


BROWS = {
    'happy': (((-14, -4), (0, -9), (14, -6)), ((-14, -6), (0, -9.5), (14, -4))),
    'surprised': (((-14, -12), (0, -18), (14, -14)), ((-14, -14), (0, -18), (14, -12))),
    'thinking': (((-14, -2), (0, -5), (14, -2)), ((-14, -14), (0, -19), (14, -14))),
    'sly': (((-15, -10), (0, -6), (13, -2)), ((-13, -2), (0, -6), (15, -10))),
    'wink': (((-15, -9), (0, -12), (13, -8)), ((-13, -2), (0, -6), (15, -10))),
}


def brows_on(name, surf_fn, x1, x2, y, col, expr, parent, r=0.034):
    m = mat('brow_' + col, col, rough=0.55, sheen=0.2)
    out = []
    for k, (x, pts) in enumerate(zip((x1, x2), BROWS.get(expr, BROWS['happy']))):
        ps = [surf_fn(x + dx, y + dy)[0] for dx, dy in pts]
        n = surf_fn(x, y)[1]
        out.append(sweep(f'{name}_brow{k}', ps, r, m, parent, flat=0.55, side=n, rf=lambda t: 0.75 + 0.5 * math.sin(math.pi * t)))
    return out


# ---------------------------------------------------------------- scene
def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    _mats.clear()
    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'
    sc.cycles.device = 'CPU'
    sc.cycles.use_adaptive_sampling = True
    sc.cycles.adaptive_threshold = 0.02
    sc.cycles.use_denoising = True
    sc.cycles.denoiser = 'OPENIMAGEDENOISE'
    sc.cycles.max_bounces = 6
    sc.cycles.diffuse_bounces = 3
    sc.cycles.glossy_bounces = 3
    sc.cycles.transmission_bounces = 6
    sc.cycles.transparent_max_bounces = 6
    sc.view_settings.view_transform = os.environ.get('CAST_VIEW', 'Standard')
    sc.view_settings.exposure = float(os.environ.get('CAST_EXPOSURE', '-0.35'))
    w = bpy.data.worlds.new('W')
    sc.world = w
    try:
        w.use_nodes = True
    except Exception:
        pass
    bg = w.node_tree.nodes.get('Background')
    bg.inputs['Color'].default_value = srgb('#EFE8DC')
    bg.inputs['Strength'].default_value = 0.42
    return sc


def area(name, loc, target, size, energy, color=(1, 1, 1), shape='DISK', shadow=True):
    li = bpy.data.lights.new(name, 'AREA')
    li.use_shadow = shadow
    li.energy = energy
    li.size = size
    li.shape = shape
    li.color = color
    ob = bpy.data.objects.new(name, li)
    ob.location = loc
    d = Vector(target) - Vector(loc)
    ob.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    return link(ob)


def camera(loc, target, lens=105):
    cd = bpy.data.cameras.new('Cam')
    cd.lens = lens
    ob = bpy.data.objects.new('Cam', cd)
    ob.location = loc
    ob.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    link(ob)
    bpy.context.scene.camera = ob
    return ob


def studio(scale=1.0, cx=0.0):
    area('Key', (cx - 5.5 * scale, -7.5 * scale, 8.5 * scale), (cx, 0, 2.2), 5 * scale, 1250 * scale * scale, (1.0, 0.95, 0.88))
    area('Fill', (cx + 7 * scale, -6 * scale, 3.6 * scale), (cx, 0, 2.0), 7 * scale, 380 * scale * scale, (0.88, 0.94, 1.0), shadow=False)
    area('Rim', (cx + 1.5 * scale, 7.0 * scale, 7.0 * scale), (cx, 0, 2.6), 3.5 * scale, 950 * scale * scale, (1.0, 0.97, 0.92), shadow=False)


def floor(catcher=True, color='#F3EDE2', size=80):
    bm = bmesh.new()
    if catcher:
        bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=size / 2)
        ob = _finish(bm, 'Floor', mat('floor', color, rough=0.9), None, smooth=False)
        ob.is_shadow_catcher = True
        return ob
    # a sweep backdrop: floor curving up behind the characters
    prof = []
    for i in range(40):
        a = i / 39 * (math.pi / 2)
        prof.append((0, 4 + 6 * math.sin(a), 6 - 6 * math.cos(a)))
    verts = []
    for x in (-size / 2, size / 2):
        row = [bm.verts.new((x, -size / 2, 0))] + [bm.verts.new((x, y, z)) for _, y, z in prof] + [bm.verts.new((x, 10, 30))]
        verts.append(row)
    for j in range(len(verts[0]) - 1):
        bm.faces.new((verts[0][j], verts[1][j], verts[1][j + 1], verts[0][j + 1]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return _finish(bm, 'Backdrop', mat('backdrop', color, rough=0.95), None)


def render(path, w, h, samples=64, transparent=True):
    sc = bpy.context.scene
    sc.render.resolution_x, sc.render.resolution_y = w, h
    sc.render.resolution_percentage = 100
    sc.render.film_transparent = transparent
    sc.cycles.samples = samples
    sc.render.image_settings.file_format = 'PNG'
    sc.render.image_settings.color_mode = 'RGBA' if transparent else 'RGB'
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)
