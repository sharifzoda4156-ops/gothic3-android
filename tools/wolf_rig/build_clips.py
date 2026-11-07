"""Free-animation clips for the HD wolf (not bound to the 270/271/272 frame sheets).

Writes one horizontal PNG strip per clip into app/src/midlet/resources/hd/characters/monsters/
plus wolf_clips.json (frame size, frame count, game-pixel size and pivot for animation.properties).
Facing: side clips face LEFT (nose left); the engine mirrors for the other direction.
"""
import sys, os, json, math
sys.path.insert(0, 'tools/wolf_rig')
import numpy as np
from PIL import Image
import rig
import build_fb_frames as F

OUT = 'app/src/midlet/resources/hd/characters/monsters/'
os.makedirs(OUT, exist_ok=True)
TAU = 2 * math.pi

# view -> (frame w, frame h, scale, anchor frame px, rig ground point, game w, game h)
VIEW = {
    'side':  dict(fw=360, fh=210, s=0.22, anchor=(180, 200), rig=(300 + 830, 150 + 881), gw=40, gh=23),
    'front': dict(fw=120, fh=225, s=0.17, anchor=(60, 215), rig=(100 + 450, 150 + 1230), gw=17, gh=32),
    'rear':  dict(fw=120, fh=225, s=0.17, anchor=(60, 215), rig=(100 + 450, 150 + 1230), gw=17, gh=32),
}


def place(img, view):
    v = VIEW[view]
    img = img.resize((max(int(img.width * v['s']), 1), max(int(img.height * v['s']), 1)), Image.LANCZOS)
    fr = Image.new('RGBA', (v['fw'], v['fh']), (0, 0, 0, 0))
    gx, gy = v['rig'][0] * v['s'], v['rig'][1] * v['s']
    fr.alpha_composite(img, (int(round(v['anchor'][0] - gx)), int(round(v['anchor'][1] - gy)))) if False else None
    ox, oy = int(round(v['anchor'][0] - gx)), int(round(v['anchor'][1] - gy))
    # alpha_composite needs non-negative dest; paste handles cropping
    fr.paste(img, (ox, oy), img)
    return fr


def side(t=0, A=26, bob_amp=8, atk=None, tail_amp=6):
    if atk:
        return rig.render(atk['pose'], atk['bob'], atk['tail'], atk['tilt'])
    pose = dict(fn=A * math.sin(TAU * t), ff=A * math.sin(TAU * t + 0.9),
                bn=A * math.sin(TAU * t + math.pi), bf=A * math.sin(TAU * t + math.pi + 0.9))
    return rig.render(pose, -abs(bob_amp * math.cos(TAU * t * 2)) + bob_amp / 2, tail_amp * math.sin(TAU * t + 1), 0)


def fb(view, t, dy=55, sc=0.09, bob=12, rot=1.5, A=1.0):
    s = math.sin(TAU * t)
    return F.render(view, dyL=dy * A * s, scL=1 + sc * A * s, dyR=-dy * A * s, scR=1 - sc * A * s,
                    bob=-bob * abs(math.cos(TAU * t)) + bob / 2, rot=rot * s)


def lerp(a, b, u):
    return {k: a[k] + (b[k] - a[k]) * u for k in a}


def keys_clip(keys, n, loop=False):
    """Interpolate a list of param dicts into n frames (looping back to the first if loop)."""
    ks = keys + ([keys[0]] if loop else [])
    out = []
    for i in range(n):
        u = i / (n if loop else n - 1) * (len(ks) - 1)
        j = min(int(u), len(ks) - 2)
        out.append(lerp(ks[j], ks[j + 1], u - j))
    return out


ATK_SIDE = [dict(fn=-8, ff=-12, bn=10, bf=16, bob=22, tail=-10, tilt=3),
            dict(fn=30, ff=22, bn=-32, bf=-24, bob=-6, tail=10, tilt=4),
            dict(fn=36, ff=28, bn=-18, bf=-10, bob=8, tail=14, tilt=9),
            dict(fn=6, ff=0, bn=-10, bf=-2, bob=4, tail=0, tilt=2)]
ATK_F = [dict(dyL=0, scL=0.96, dyR=0, scR=0.96, bob=45, rot=0),
         dict(dyL=40, scL=1.08, dyR=40, scR=1.08, bob=-30, rot=0),
         dict(dyL=50, scL=1.10, dyR=20, scR=1.05, bob=-10, rot=-3),
         dict(dyL=0, scL=1.0, dyR=0, scR=1.0, bob=15, rot=3)]
ATK_R = [dict(dyL=0, scL=0.96, dyR=0, scR=0.96, bob=40, rot=0),
         dict(dyL=40, scL=1.06, dyR=-35, scR=0.9, bob=-20, rot=2),
         dict(dyL=0, scL=1.0, dyR=0, scR=1.0, bob=10, rot=0)]


def corpse():
    """Lying on its side: body layer squashed, tail alongside, no legs."""
    c = Image.new('RGBA', (rig.SZ[0] + 600, rig.SZ[1] + 300), (0, 0, 0, 0))
    ox, oy = 300, 150
    body = rig.body
    tail = rig.rot(rig.L['tail'], 'tail', -25)
    lay = Image.new('RGBA', c.size, (0, 0, 0, 0))
    lay.alpha_composite(tail, (ox, oy)); lay.alpha_composite(body, (ox, oy))
    bb = lay.getbbox(); lay = lay.crop(bb)
    lay = lay.resize((lay.width, int(lay.height * 0.55)), Image.LANCZOS).rotate(-3, expand=True, resample=Image.BICUBIC)
    # place so that its bottom edge sits on the same ground point as the standing wolf
    c = Image.new('RGBA', (rig.SZ[0] + 600, rig.SZ[1] + 300), (0, 0, 0, 0))
    gx, gy = 300 + 830, 150 + 881
    c.alpha_composite(lay, (gx - lay.width // 2, gy - lay.height))
    return c


def strip(frames, view):
    fr = [place(f, view) for f in frames]
    v = VIEW[view]
    sheet = Image.new('RGBA', (v['fw'] * len(fr), v['fh']), (0, 0, 0, 0))
    for i, f in enumerate(fr):
        sheet.paste(f, (i * v['fw'], 0))
    return sheet


def main():
    clips = {}
    def add(name, view, frames, ticks, loop=True):
        strip(frames, view).save(OUT + name + '.png')
        v = VIEW[view]
        clips[name] = dict(sheet=name, frameWidth=v['fw'], frameHeight=v['fh'], columns=len(frames),
                           frames=len(frames), width=v['gw'], height=v['gh'],
                           pivotX=round(v['anchor'][0] / v['fw'] * v['gw'], 2),
                           pivotY=round(v['anchor'][1] / v['fh'] * v['gh'], 2),
                           durations=[ticks] * len(frames), loop=loop, facing='left' if view == 'side' else view)
        print('clip', name, len(frames))
    N = 8
    add('wolf_walk_side', 'side', [side(i / N, A=22) for i in range(N)], 2)
    add('wolf_run_side', 'side', [side(i / N, A=30, bob_amp=12) for i in range(N)], 1)
    add('wolf_walk_front', 'front', [fb('front', i / N) for i in range(N)], 2)
    add('wolf_walk_rear', 'rear', [fb('rear', i / N, dy=45, sc=0.07) for i in range(N)], 2)
    add('wolf_idle_side', 'side', [side(i / 6, A=0, bob_amp=3, tail_amp=8) for i in range(6)], 4)
    add('wolf_idle_front', 'front', [fb('front', i / 6, dy=0, sc=0, bob=6, rot=1) for i in range(6)], 4)
    add('wolf_idle_rear', 'rear', [fb('rear', i / 6, dy=0, sc=0, bob=6, rot=1) for i in range(6)], 4)
    ks = keys_clip(ATK_SIDE, 8)
    add('wolf_attack_side', 'side',
        [side(atk=dict(pose={q: k[q] for q in ('fn', 'ff', 'bn', 'bf')}, bob=k['bob'], tail=k['tail'], tilt=k['tilt'])) for k in ks], 2, loop=False)
    add('wolf_attack_front', 'front', [F.render('front', **k) for k in keys_clip(ATK_F, 8)], 2, loop=False)
    add('wolf_attack_rear', 'rear', [F.render('rear', **k) for k in keys_clip(ATK_R, 6)], 2, loop=False)
    add('wolf_corpse', 'side', [corpse()], 1000, loop=False)
    json.dump(clips, open(OUT + 'wolf_clips.json', 'w'), indent=1)


if __name__ == '__main__':
    main()
