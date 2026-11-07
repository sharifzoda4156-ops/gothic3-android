"""Side-view wolf rig: cut legs/tail out of side_full.png and re-pose them over side_body.png."""
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

SRC = 'tools/wolf_rig/src/'
full = Image.open(SRC + 'side_full.png').convert('RGBA')
body = Image.open(SRC + 'side_body.png').convert('RGBA')
SZ = full.size


def cut(poly, feather=5):
    m = Image.new('L', SZ, 0)
    ImageDraw.Draw(m).polygon(poly, fill=255)
    m = m.filter(ImageFilter.GaussianBlur(feather))
    a = np.minimum(np.asarray(full)[:, :, 3], np.asarray(m))
    out = full.copy()
    out.putalpha(Image.fromarray(a.astype(np.uint8)))
    return out

# divider lines between legs (see grid_full.png)
L = {
 'front_far':  cut([(330,430),(545,470),(445,900),(250,900),(250,700)]),
 'front_near': cut([(545,470),(720,470),(720,900),(445,900)]),
 'back_far':   cut([(840,420),(1010,470),(1115,740),(1115,900),(840,900)]),
 'back_near':  cut([(1010,470),(1330,470),(1330,900),(1115,900),(1115,740)]),
 'tail':       cut([(1090,180),(1250,180),(1620,300),(1620,520),(1300,500),(1230,430),(1180,320),(1090,270)], 3),
}
PIV = {'front_far': (470, 470), 'front_near': (620, 470), 'back_far': (930, 440), 'back_near': (1130, 450), 'tail': (1150, 270)}


def rot(layer, key, ang):
    """ang>0: foot/tip swings toward the nose (left)."""
    return layer.rotate(-ang, resample=Image.BICUBIC, center=PIV[key])


def render(pose, bob=0, tail=0):
    c = Image.new('RGBA', (SZ[0] + 600, SZ[1] + 300), (0, 0, 0, 0))
    ox, oy = 300, 150
    def put(im, dy=0):
        c.alpha_composite(im, (ox, oy + dy))
    put(rot(L['tail'], 'tail', tail), bob)
    put(rot(L['back_far'], 'back_far', pose['bf']), 0)
    put(rot(L['front_far'], 'front_far', pose['ff']), 0)
    put(body, bob)
    put(rot(L['back_near'], 'back_near', pose['bn']), 0)
    put(rot(L['front_near'], 'front_near', pose['fn']), 0)
    return c
