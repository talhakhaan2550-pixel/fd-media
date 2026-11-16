"""Turns the pose renders (out/poses/<who>_<expr>.png) into the studio's cast sprites (tools/assets/cast/<who>_<expr>.webp).

Every sprite shares one vertical frame (the same top and bottom for the whole cast), so characters keep their real
sizes next to each other when the studio shows them at one height. Each character keeps one width across its
expressions, so switching expression between slides does not shift it. The faint long shadow is trimmed to its
core so no sprite ends in a hard edge.

Run with any Python that has Pillow and numpy:  python3 make_sprites.py [--sheet out/sprites.png]
"""
import glob, os, sys
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
POSES = os.path.join(HERE, 'out', 'poses')
DEST = os.path.join(os.path.dirname(HERE), 'assets', 'cast')
LO, MARGIN = 55, 14


def load(path):
    im = np.array(Image.open(path).convert('RGBA')).astype(np.float32)
    # alpha below LO (the faint long shadow) goes; the rest is stretched back to the full range, so it stays smooth
    im[:, :, 3] = np.clip((im[:, :, 3] - LO) * 255.0 / (255 - LO), 0, 255)
    return np.round(im).astype(np.uint8)


def bbox(alpha):
    ys, xs = np.where(alpha > 0)
    return xs.min(), ys.min(), xs.max(), ys.max()


def main():
    files = sorted(glob.glob(os.path.join(POSES, '*.png')))
    if not files:
        sys.exit('no renders in %s' % POSES)
    ims = {os.path.basename(f)[:-4]: load(f) for f in files}
    boxes = {k: bbox(v[:, :, 3]) for k, v in ims.items()}
    H, W = next(iter(ims.values())).shape[:2]
    top = max(0, min(b[1] for b in boxes.values()) - MARGIN)
    bottom = min(H, max(b[3] for b in boxes.values()) + MARGIN + 1)
    who_x = {}
    for k, b in boxes.items():
        who = k.split('_')[0]
        lo, hi = who_x.get(who, (W, 0))
        who_x[who] = (min(lo, b[0]), max(hi, b[2]))
    os.makedirs(DEST, exist_ok=True)
    out = []
    for k, im in sorted(ims.items()):
        x0, x1 = who_x[k.split('_')[0]]
        crop = Image.fromarray(im[top:bottom, max(0, x0 - MARGIN):min(W, x1 + MARGIN + 1)])
        path = os.path.join(DEST, k + '.webp')
        crop.save(path, 'WEBP', quality=90, method=6)
        out.append((k, crop.size, os.path.getsize(path)))
        print('%-18s %4d x %4d  %6.1f KB' % (k, crop.size[0], crop.size[1], os.path.getsize(path) / 1024))
    print('frame: rows %d to %d of the %d x %d renders' % (top, bottom, W, H))
    if '--sheet' in sys.argv:
        sheet = sys.argv[sys.argv.index('--sheet') + 1]
        tiles = [Image.open(os.path.join(DEST, k + '.webp')) for k, _, _ in out]
        th = 300
        tiles = [t.resize((max(1, round(t.width * th / t.height)), th), Image.LANCZOS) for t in tiles]
        cols = 7
        rows = (len(tiles) + cols - 1) // cols
        cw = max(t.width for t in tiles) + 16
        bg = Image.new('RGBA', (cols * cw, rows * (th + 16)), (246, 241, 231, 255))
        for i, t in enumerate(tiles):
            bg.alpha_composite(t, (i % cols * cw + (cw - t.width) // 2, i // cols * (th + 16) + 8))
        bg.convert('RGB').save(sheet)
        print('sheet', sheet)


if __name__ == '__main__':
    main()
