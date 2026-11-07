"""Re-fit the HD wolf sheets (270/271/272 + species variants) to the engine's
original frame silhouettes.

integrate_hd_wolf.py pasted ONE painted pose into every frame with an
aspect-preserving fit, so (a) every walk/attack frame looked identical (no
animation) and (b) the wolf ended up ~15-20% smaller than the original
because the painting's aspect ratio did not match the frame box.

For each frame rect this script takes the current HD content and, stretches
it to the bounding box of the ORIGINAL pixel-art frame (root NNN.png, 2x), so the HD
wolf is exactly as large as the original. NOTE: this fixes size only; real per-frame
poses (legs) must come from newly painted frames (see wolf spec). Run from the repo root; idempotent only on a
pristine copy of the Gemini sheets (it re-fits, so do not run twice on
already-fitted output unless you want a second smoothing pass).
"""
import os
import numpy as np
from PIL import Image

R = 'app/src/midlet/resources/'
HD = R + 'hd/'
THR = 20

RECTS = {
    '270': {
        0: (0, 0, 74, 42), 8: (76, 56, 70, 42), 10: (0, 102, 74, 40), 11: (76, 102, 72, 42),
        1: (76, 2, 26, 52), 2: (104, 0, 22, 54), 3: (128, 0, 22, 56), 4: (152, 0, 22, 56),
        5: (0, 46, 24, 46), 6: (26, 44, 24, 56), 7: (52, 44, 22, 52), 9: (152, 58, 22, 54),
    },
    '271': {
        0: (0, 0, 72, 36), 7: (54, 58, 72, 36), 8: (0, 94, 74, 44), 9: (76, 94, 72, 44),
        1: (74, 0, 26, 56), 2: (102, 2, 24, 56), 3: (128, 2, 26, 56), 4: (156, 0, 22, 58),
        10: (152, 80, 22, 56), 5: (0, 38, 26, 50), 6: (28, 38, 26, 50),
    },
    '272': {0: (0, 0, 64, 28)},
}
SUFFIXES = ['', '_t0', '_t8', '_t9', '_t10']


def col_extent(alpha):
    """Per-column (top, bottom+1) of opaque pixels; None for empty columns."""
    m = alpha > THR
    out = []
    for x in range(m.shape[1]):
        ys = np.nonzero(m[:, x])[0]
        out.append((ys[0], ys[-1] + 1) if len(ys) else None)
    return out


def smooth(ext, k=1):
    res = []
    for i, e in enumerate(ext):
        if e is None:
            res.append(None)
            continue
        nb = [ext[j] for j in range(max(0, i - k), min(len(ext), i + k + 1)) if ext[j]]
        res.append((np.mean([n[0] for n in nb]), np.mean([n[1] for n in nb])))
    return res


def refit(src, tgt_alpha):
    """Stretch src content to the bounding box of the original frame's silhouette."""
    H, W = tgt_alpha.shape
    ys, xs = np.nonzero(tgt_alpha > THR)
    out = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    if not len(xs):
        return out
    x0, x1, y0, y1 = xs.min(), xs.max() + 1, ys.min(), ys.max() + 1
    out.paste(src.resize((x1 - x0, y1 - y0), Image.Resampling.LANCZOS), (x0, y0))
    return out


def main():
    for n, rects in RECTS.items():
        orig = Image.open(R + n + '.png').convert('RGBA')
        orig = orig.resize((orig.width * 2, orig.height * 2), Image.NEAREST)
        oa = np.asarray(orig)[:, :, 3]
        for suf in SUFFIXES:
            path = f'{HD}{n}{suf}.png'
            if not os.path.exists(path):
                continue
            sheet = Image.open(path).convert('RGBA')
            res = Image.new('RGBA', sheet.size, (0, 0, 0, 0))
            for k, (x, y, w, h) in rects.items():
                crop = sheet.crop((x, y, x + w, y + h))
                bb = crop.getchannel('A').point(lambda v: 255 if v > THR else 0).getbbox()
                if not bb:
                    continue
                fit = refit(crop.crop(bb), oa[y:y + h, x:x + w])
                res.paste(fit, (x, y))
            res.save(path)
            print('refit', path)


if __name__ == '__main__':
    main()
