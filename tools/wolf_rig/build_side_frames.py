"""Render rigged side-view poses and write them into the HD wolf sheets (run from repo root)."""
import sys, os
sys.path.insert(0, 'tools/wolf_rig')
import numpy as np
from PIL import Image
import rig

R = 'app/src/midlet/resources/'
HD = R + 'hd/'
THR = 20
# sheet -> {frame: (rect, pose, bob, tail, tilt)}
POSES = {
 '270': {
  0:  ((0, 0, 74, 42),    dict(fn=28, ff=20, bn=-28, bf=-20), -8, 6, 0),
  8:  ((76, 56, 70, 42),  dict(fn=-10, ff=-5, bn=15, bf=22), 14, -6, 0),
  10: ((0, 102, 74, 40),  dict(fn=22, ff=30, bn=5, bf=-10), 0, 8, 0),
  11: ((76, 102, 72, 42), dict(fn=-20, ff=-28, bn=-22, bf=8), 6, -4, 0),
 },
 '271': {
  0: ((0, 0, 72, 36),    dict(fn=-8, ff=-12, bn=10, bf=16), 22, -10, 3),
  7: ((54, 58, 72, 36),  dict(fn=30, ff=22, bn=-32, bf=-24), -6, 10, 4),
  8: ((0, 94, 74, 44),   dict(fn=36, ff=28, bn=-18, bf=-10), 8, 14, 9),
  9: ((76, 94, 72, 44),  dict(fn=6, ff=0, bn=-10, bf=-2), 4, 0, 2),
 },
}
SUFFIXES = ['', '_t0', '_t8', '_t9', '_t10']
# per-species tint (kept equal to integrate_hd_wolf.py)
TONE = {'': (None, 0.0),
        '_t0': (((0.35, 1.15), (0.35, 1.05), (0.35, 0.90)), -0.05),
        '_t8': (((0.40, 0.85), (0.40, 0.85), (0.40, 0.90)), 0.18),
        '_t9': (((0.50, 0.60), (0.50, 0.55), (0.50, 0.65)), 0.42),
        '_t10': (((0.50, 0.60), (0.50, 0.55), (0.50, 0.65)), 0.42)}


def tone(im, tint, darken):
    a = np.asarray(im).astype(np.float64)
    r, g, b, al = a[..., 0], a[..., 1], a[..., 2], a[..., 3]
    if tint:
        lum = r * .299 + g * .587 + b * .114
        (tr, tg, tb) = tint
        r = r * (1 - tr[0]) + lum * tr[1] * tr[0]
        g = g * (1 - tg[0]) + lum * tg[1] * tg[0]
        b = b * (1 - tb[0]) + lum * tb[1] * tb[0]
    k = 1 - darken
    out = np.stack([r * k, g * k, b * k, al], -1)
    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8), 'RGBA')


def frame(pose, bob, tail, tilt, rect, orig2x):
    return fit_img(rig.render(pose, bob, tail, tilt), rect, orig2x)


def fit_img(img, rect, orig2x):
    x, y, w, h = rect
    bb = img.getchannel('A').point(lambda v: 255 if v > THR else 0).getbbox()
    img = img.crop(bb)
    oa = np.asarray(orig2x)[y:y + h, x:x + w, 3]
    ys, xs = np.nonzero(oa > THR)
    x0, x1, y0, y1 = xs.min(), xs.max() + 1, ys.min(), ys.max() + 1
    # downscale in two steps for clean antialiasing
    big = img.resize((max((x1 - x0) * 4, 1), max((y1 - y0) * 4, 1)), Image.LANCZOS)
    small = big.resize((x1 - x0, y1 - y0), Image.LANCZOS)
    out = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    out.paste(small, (x0, y0))
    return out


def main():
    cache = {}
    for n, frames in POSES.items():
        o = Image.open(R + n + '.png').convert('RGBA')
        orig2x = o.resize((o.width * 2, o.height * 2), Image.NEAREST)
        for k, (rect, pose, bob, tail, tilt) in frames.items():
            cache[(n, k)] = (rect, frame(pose, bob, tail, tilt, rect, orig2x))
    for n in POSES:
        for suf in SUFFIXES:
            path = f'{HD}{n}{suf}.png'
            sheet = Image.open(path).convert('RGBA')
            for (nn, k), (rect, fr) in cache.items():
                if nn != n:
                    continue
                x, y, w, h = rect
                t = tone(fr, *TONE[suf]) if suf else fr
                blank = Image.new('RGBA', (w, h), (0, 0, 0, 0))
                sheet.paste(blank, (x, y))
                sheet.alpha_composite(t, (x, y))
            sheet.save(path)
            print('wrote', path)


if __name__ == '__main__':
    main()
