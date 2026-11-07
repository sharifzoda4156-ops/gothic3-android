"""Front/rear wolf frames: animate legs (vertical swing + perspective scale), body bob and sway."""
import sys
sys.path.insert(0, 'tools/wolf_rig')
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
import build_side_frames as B

SRC = 'tools/wolf_rig/src/'
R, HD = B.R, B.HD
fullF = Image.open(SRC + 'front_full.png').convert('RGBA')
fullR = Image.open(SRC + 'rear_full.png').convert('RGBA')
SZ = fullF.size


def mask(poly, blur=4):
    m = Image.new('L', SZ, 0)
    ImageDraw.Draw(m).polygon(poly, fill=255)
    return m.filter(ImageFilter.GaussianBlur(blur))


def cutlayer(full, m):
    a = np.minimum(np.asarray(full)[:, :, 3], np.asarray(m))
    out = full.copy(); out.putalpha(Image.fromarray(a.astype(np.uint8))); return out


def rest(full, ms):
    inv = np.ones(SZ[::-1])
    for m in ms:
        inv = np.minimum(inv, 1 - np.asarray(m) / 255.0)
    a = (np.asarray(full)[:, :, 3] * inv).astype(np.uint8)
    out = full.copy(); out.putalpha(Image.fromarray(a)); return out

TOP = 700
FRONT = {
 'L': [(0, TOP), (385, TOP), (385, 1010), (415, 1120), (415, 1300), (0, 1300)],
 'R': [(462, TOP), (900, TOP), (900, 1300), (415, 1300), (415, 1120), (462, 1010)],
}
REAR = {
 'L': [(0, 740), (385, 740), (385, 1300), (0, 1300)],
 'R': [(495, 740), (900, 740), (900, 1300), (495, 1300)],
}
PARTS = {}
for name, full, polys in (('front', fullF, FRONT), ('rear', fullR, REAR)):
    ms = {k: mask(p) for k, p in polys.items()}
    PARTS[name] = (rest(full, ms.values()), {k: cutlayer(full, m) for k, m in ms.items()}, polys)


def leg(layer, top, dy, sc):
    bb = layer.getchannel('A').getbbox()
    crop = layer.crop(bb)
    h = max(int(crop.height * sc), 1)
    crop = crop.resize((crop.width, h), Image.LANCZOS)
    # soften the cut edge at the top where the leg blends into the body
    a = np.asarray(crop.getchannel('A')).astype(np.float64)
    f = np.clip(np.arange(h)[:, None] / 40.0, 0, 1)
    crop.putalpha(Image.fromarray((a * f).astype(np.uint8)))
    out = Image.new('RGBA', layer.size, (0, 0, 0, 0))
    out.alpha_composite(crop, (bb[0], bb[1] + dy))
    return out


def render(view, dyL=0, scL=1.0, dyR=0, scR=1.0, bob=0, rot=0, grow=1.0):
    base, legs, _ = PARTS[view]
    c = Image.new('RGBA', (SZ[0] + 200, SZ[1] + 300), (0, 0, 0, 0))
    ox, oy = 100, 150
    c.alpha_composite(base, (ox, oy + bob))
    for k, (dy, sc) in (('L', (dyL, scL)), ('R', (dyR, scR))):
        c.alpha_composite(leg(legs[k], TOP, dy, sc), (ox, oy + bob))
    if rot:
        c = c.rotate(rot, resample=Image.BICUBIC, center=(ox + 450, oy + 900))
    if grow != 1.0:
        c = c.resize((int(c.width * grow), int(c.height * grow)), Image.LANCZOS)
    return c

# sheet -> frame -> (rect, view, kwargs)
RECTS = {
 '270': {1: (76, 2, 26, 52), 2: (104, 0, 22, 54), 3: (128, 0, 22, 56), 4: (152, 0, 22, 56),
         5: (0, 46, 24, 46), 6: (26, 44, 24, 56), 7: (52, 44, 22, 52), 9: (152, 58, 22, 54)},
 '271': {1: (74, 0, 26, 56), 2: (102, 2, 24, 56), 3: (128, 2, 26, 56), 4: (156, 0, 22, 58),
         10: (152, 80, 22, 56), 5: (0, 38, 26, 50), 6: (28, 38, 26, 50)},
}
WALK_F = [dict(dyL=60, scL=1.10, dyR=-50, scR=0.88, bob=-10, rot=2),
          dict(dyL=0, scL=1.0, dyR=0, scR=1.0, bob=25, rot=0),
          dict(dyL=-50, scL=0.88, dyR=60, scR=1.10, bob=-10, rot=-2),
          dict(dyL=0, scL=1.0, dyR=0, scR=1.0, bob=0, rot=0)]
WALK_R = [dict(dyL=-45, scL=0.88, dyR=40, scR=1.06, bob=-8, rot=-2),
          dict(dyL=0, scL=1.0, dyR=0, scR=1.0, bob=22, rot=0),
          dict(dyL=40, scL=1.06, dyR=-45, scR=0.88, bob=-8, rot=2),
          dict(dyL=0, scL=1.0, dyR=0, scR=1.0, bob=0, rot=0)]
ATK_F = [dict(dyL=0, scL=0.96, dyR=0, scR=0.96, bob=45, rot=0),      # crouch
         dict(dyL=40, scL=1.08, dyR=40, scR=1.08, bob=-30, rot=0),   # leap
         dict(dyL=50, scL=1.10, dyR=20, scR=1.05, bob=-10, rot=-3),  # bite
         dict(dyL=0, scL=1.0, dyR=0, scR=1.0, bob=15, rot=3),        # recoil
         dict(dyL=-20, scL=0.94, dyR=30, scR=1.06, bob=0, rot=0)]
ATK_R = [dict(dyL=0, scL=0.96, dyR=0, scR=0.96, bob=40, rot=0),
         dict(dyL=40, scL=1.06, dyR=-35, scR=0.9, bob=-20, rot=2)]
PLAN = {
 '270': {1: ('front', WALK_F[0]), 2: ('front', WALK_F[1]), 3: ('front', WALK_F[2]), 4: ('front', WALK_F[3]),
         5: ('rear', WALK_R[0]), 6: ('rear', WALK_R[1]), 7: ('rear', WALK_R[2]), 9: ('rear', WALK_R[3])},
 '271': {1: ('front', ATK_F[0]), 2: ('front', ATK_F[1]), 3: ('front', ATK_F[2]), 4: ('front', ATK_F[3]),
         10: ('front', ATK_F[4]), 5: ('rear', ATK_R[0]), 6: ('rear', ATK_R[1])},
}


def main():
    cache = {}
    for n, frames in PLAN.items():
        o = Image.open(R + n + '.png').convert('RGBA')
        o2 = o.resize((o.width * 2, o.height * 2), Image.NEAREST)
        for k, (view, kw) in frames.items():
            rect = RECTS[n][k]
            cache[(n, k)] = (rect, B.fit_img(render(view, **kw), rect, o2))
    for n in PLAN:
        for suf in B.SUFFIXES:
            path = f'{HD}{n}{suf}.png'
            sheet = Image.open(path).convert('RGBA')
            for (nn, k), (rect, fr) in cache.items():
                if nn != n:
                    continue
                x, y, w, h = rect
                t = B.tone(fr, *B.TONE[suf]) if suf else fr
                sheet.paste(Image.new('RGBA', (w, h), (0, 0, 0, 0)), (x, y))
                sheet.alpha_composite(t, (x, y))
            sheet.save(path)
            print('wrote', path)


if __name__ == '__main__':
    main()
