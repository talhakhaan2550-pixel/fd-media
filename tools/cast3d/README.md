# The cast in 3D

Modelled on 16 November 2026 after Talha asked "Can we make these characters in 3d?"; he approved the 3D cast that
evening. Since then the studio's `cast` visual shows these sprites (tools/assets/cast) instead of the 2D drawings.

- `tex.py` renders the flat prints (mouths, blush, clothing prints, receipt and calendar pages, labels) from SVG with the brand fonts into `tex/`. Run it with the studio's Python (playwright).
- `b3d.py` is a small modelling kit for Blender 5 (`pip install bpy` in a Python 3.11 venv): materials, ellipsoids, rounded boxes, tubes, lathes, hair shells, eyes and brows, studio lights and a shadow catcher. Coordinates come from the 2D drawings: `P(x, y, d)` maps a point of the 320 x 440 SVG to 3D.
- `cast3d.py` builds each character (`sam`, `penny`, `rex`, `zara`, `grace`, `dev`, `maya`, `dot`) and renders it: `python cast3d.py sam - out/sam.png 900 1170 48` (transparent PNG with its shadow), or `python cast3d.py group` for the lineup.
- `sheet3d.py` makes the approval sheet from the renders.

Rendering is Cycles on the CPU: about 1.5 minutes a character at 900 x 1170 and 48 samples, denoised.

## Sprites for the studio

1. `./render_poses.sh` renders every pose the studio uses into `out/poses/<who>_<expr>.png` (it skips poses already
   there; about 2 minutes each on two CPUs). The poses are the six people happy, surprised and thinking; Rex sly,
   surprised, happy and wink; Dot happy, surprised and wink (tools/studio/cast.py POSES).
2. `python3 make_sprites.py --sheet out/sprites.png` trims the faint long shadow, crops every pose to one shared vertical
   frame (so characters keep their real sizes side by side) and one width per character, and writes
   `tools/assets/cast/<who>_<expr>.webp`, which is what the studio embeds.

To change a character, edit it here, delete its poses from `out/poses`, run both steps and commit the new sprites.
