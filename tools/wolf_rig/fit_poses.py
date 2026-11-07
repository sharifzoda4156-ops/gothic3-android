"""Auto-fit rig poses so each HD frame's silhouette matches the ORIGINAL pixel frame.

Coordinate descent on pose parameters maximising silhouette IoU against the original
frame (2x, bbox-normalised like the final stretch). Writes tools/wolf_rig/fitted_poses.json,
which build_side_frames.py / build_fb_frames.py use when present.
"""
import sys, json, time
sys.path.insert(0, 'tools/wolf_rig')
import numpy as np
from PIL import Image
import build_side_frames as S
import build_fb_frames as F
import rig

THR = 20


def target_mask(n, rect):
    o = Image.open(S.R + n + '.png').convert('RGBA')
    o2 = o.resize((o.width * 2, o.height * 2), Image.NEAREST)
    x, y, w, h = rect
    a = np.asarray(o2)[y:y + h, x:x + w, 3] > THR
    ys, xs = np.nonzero(a)
    return a[ys.min():ys.max() + 1, xs.min():xs.max() + 1]


def score(img, tm):
    a = img.getchannel('A').point(lambda v: 255 if v > THR else 0)
    bb = a.getbbox()
    if not bb:
        return 0
    a = a.crop(bb).resize((tm.shape[1], tm.shape[0]), Image.BILINEAR)
    m = np.asarray(a) > 127
    return (m & tm).sum() / max((m | tm).sum(), 1)


def descend(render_fn, params, steps, tm, rounds=3):
    best = score(render_fn(params), tm)
    for r in range(rounds):
        improved = False
        for k, st in steps.items():
            for d in (st, -st, st / 2, -st / 2):
                p = dict(params); p[k] = p[k] + d
                s = score(render_fn(p), tm)
                if s > best + 1e-4:
                    best, params, improved = s, p, True
        if not improved:
            break
    return params, best


def main():
    out = {'side': {}, 'fb': {}}
    # side frames
    for n, frames in S.POSES.items():
        for k, (rect, pose, bob, tail, tilt) in frames.items():
            tm = target_mask(n, rect)
            p0 = dict(pose, bob=bob, tail=tail, tilt=tilt)
            fn = lambda p: rig.render({q: p[q] for q in ('fn', 'ff', 'bn', 'bf')}, p['bob'], p['tail'], p['tilt'])
            steps = dict(fn=10, ff=10, bn=10, bf=10, bob=14, tail=8, tilt=3)
            t = time.time()
            p, sc = descend(fn, p0, steps, tm)
            print('side', n, k, round(score(fn(p0), tm), 3), '->', round(sc, 3), round(time.time() - t), 's', flush=True)
            out['side'][f'{n}:{k}'] = p
    # front / rear
    for n, frames in F.PLAN.items():
        for k, (view, kw) in frames.items():
            tm = target_mask(n, F.RECTS[n][k])
            fn = lambda p, v=view: F.render(v, **p)
            steps = dict(dyL=25, scL=0.06, dyR=25, scR=0.06, bob=15, rot=2)
            p, sc = descend(fn, dict(kw), steps, tm)
            print('fb', n, k, view, round(score(fn(dict(kw)), tm), 3), '->', round(sc, 3), flush=True)
            out['fb'][f'{n}:{k}'] = p
    json.dump(out, open('tools/wolf_rig/fitted_poses.json', 'w'), indent=1)


if __name__ == '__main__':
    main()
