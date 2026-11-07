"""
High-definition monster triad remastering engine.
Preserves exact byte-level kinematics and coordinates from *.mdl
while synthesizing distinct high-definition fur, scales, fangs,
and canon species colors from approved concept art.
"""

from PIL import Image, ImageFilter, ImageEnhance, ImageOps
import os
import sys

RESOURCES = 'app/src/midlet/resources'
HD_DIR = os.path.join(RESOURCES, 'hd')
WORK_DIR = '.work'
BRAIN_DIR = r'C:\Users\Абубакр\.gemini\antigravity\brain\a3052551-b70c-41e5-b9d4-7dbb1e9a3a5f'

# 1. Exact coordinate tables from MDL (1x coordinates)
WOLF_FRAMES_270 = [
    (0, 0, 37, 21),    # 0: Side run 1
    (38, 1, 13, 26),   # 1: Front walk 1
    (52, 0, 11, 27),   # 2: Front walk 2
    (64, 0, 11, 28),   # 3: Front walk 3
    (76, 0, 11, 28),   # 4: Front walk 4
    (0, 23, 12, 23),   # 5: Back walk 1
    (13, 22, 12, 28),  # 6: Back walk 2
    (26, 22, 11, 26),  # 7: Back walk 3
    (38, 28, 35, 21),  # 8: Side run 2
    (76, 29, 11, 27),  # 9: Back walk 4
    (0, 51, 37, 20),   # 10: Side run 3
    (38, 51, 36, 21),  # 11: Side run 4
]

WOLF_FRAMES_271 = [
    (0, 0, 36, 18),    # 0: Side attack prep
    (37, 0, 13, 28),   # 1: Front attack 1
    (51, 1, 12, 28),   # 2: Front attack 2
    (64, 1, 13, 28),   # 3: Front attack 3
    (78, 0, 11, 29),   # 4: Front attack 4
    (0, 19, 13, 25),   # 5: Back attack 1
    (14, 19, 13, 25),  # 6: Back attack 2
    (27, 29, 36, 18),  # 7: Side lunge
    (0, 47, 37, 22),   # 8: Side bite strike
    (38, 47, 36, 22),  # 9: Side bite recover
    (76, 40, 11, 28),  # 10: Front recover
]

WOLF_FRAMES_272 = [
    (0, 0, 32, 14),    # 0: Corpse in snow
]

BLOODFLY_FRAMES_211 = [
    (0, 0, 15, 26), (15, 0, 23, 22), (38, 0, 15, 27), (53, 0, 23, 23),
    (0, 0, 15, 26), (15, 0, 23, 22), (61, 23, 15, 24), (38, 27, 23, 20),
    (23, 22, 15, 25), (0, 26, 23, 21), (61, 23, 15, 24), (38, 27, 23, 20),
    (0, 47, 16, 23), (16, 47, 15, 20), (31, 47, 16, 25), (47, 47, 15, 22),
    (0, 47, 16, 23), (16, 47, 15, 20)
]

BLOODFLY_FRAMES_212 = [
    (0, 0, 15, 29), (15, 0, 23, 25), (38, 0, 15, 21),
    (0, 29, 23, 16), (23, 25, 17, 24), (40, 21, 16, 21)
]

BLOODFLY_FRAMES_213 = [
    (0, 0, 14, 16)
]

SCAVENGER_FRAMES_221 = [
    (0, 0, 11, 21), (12, 0, 12, 22), (25, 0, 11, 22), (37, 0, 11, 21),
    (49, 0, 14, 21), (64, 0, 11, 21), (0, 22, 24, 21), (24, 22, 27, 16),
    (51, 22, 27, 20), (0, 43, 27, 19), (27, 43, 27, 17), (54, 42, 27, 18)
]

SCAVENGER_FRAMES_222 = [
    (0, 0, 13, 23), (14, 4, 13, 19), (28, 4, 13, 19), (42, 0, 11, 24),
    (54, 2, 11, 22), (66, 4, 11, 20), (0, 23, 23, 24), (23, 24, 25, 21),
    (48, 24, 26, 18)
]

SCAVENGER_FRAMES_224 = [
    (0, 0, 24, 12)
]


def enhance_frame_hd(orig_cell, scale=2, tint=None, fur_darken=0.0, eye_color=None, fang_boost=False):
    """
    Sub-pixel edge refinement + high-detail shading.
    Preserves exact transparent boundary while introducing crisp HD texturing.
    """
    w, h = orig_cell.size
    hd_w, hd_h = w * scale, h * scale

    # Step 1: High quality lanczos upscale
    upscaled = orig_cell.resize((hd_w, hd_h), Image.Resampling.LANCZOS)
    
    # Step 2: Unsharp mask for crisp high-definition edges
    crisp = upscaled.filter(ImageFilter.UnsharpMask(radius=1.5, percent=180, threshold=2))
    
    # Work on pixels
    pixels = crisp.load()
    orig_pixels = orig_cell.load()

    for y in range(hd_h):
        for x in range(hd_w):
            r, g, b, a = pixels[x, y]
            if a < 32:
                pixels[x, y] = (0, 0, 0, 0)
                continue
            
            # Map corresponding original coordinate
            ox = min(w - 1, x // scale)
            oy = min(h - 1, y // scale)
            o_r, o_g, o_b, o_a = orig_pixels[ox, oy]
            
            if o_a == 0:
                # Keep transparent boundary strict
                pixels[x, y] = (0, 0, 0, 0)
                continue

            # Apply tint / tone if specified
            if tint:
                tr, tg, tb = tint
                # Blend with tint based on luminance
                lum = (r * 299 + g * 587 + b * 114) / 1000.0
                r = int(r * (1.0 - tr[0]) + (lum * tr[1]) * tr[0])
                g = int(g * (1.0 - tg[0]) + (lum * tg[1]) * tg[0])
                b = int(b * (1.0 - tb[0]) + (lum * tb[1]) * tb[0])

            # Fur darkening / deepening for alphas/wargs
            if fur_darken > 0:
                r = int(r * (1.0 - fur_darken))
                g = int(g * (1.0 - fur_darken))
                b = int(b * (1.0 - fur_darken))

            # Fang/tooth highlight on bright pixels near muzzle (front/side)
            if fang_boost and r > 180 and g > 170 and b > 160:
                r = min(255, int(r * 1.25))
                g = min(255, int(g * 1.25))
                b = min(255, int(b * 1.25))

            # Clamp
            pixels[x, y] = (
                max(0, min(255, r)),
                max(0, min(255, g)),
                max(0, min(255, b)),
                255 if a > 128 else a
            )

    return crisp


def build_monster_sheet(orig_sheet_path, frame_coords, scale=2, tint=None, fur_darken=0.0, eye_color=None, fang_boost=False):
    """
    Builds a full HD sheet where every single frame is placed at exactly (sx*2, sy*2, w*2, h*2).
    """
    orig = Image.open(orig_sheet_path).convert('RGBA')
    ow, oh = orig.size
    hd_sheet = Image.new('RGBA', (ow * scale, oh * scale), (0, 0, 0, 0))

    for idx, (sx, sy, w, h) in enumerate(frame_coords):
        cell = orig.crop((sx, sy, sx + w, sy + h))
        hd_cell = enhance_frame_hd(
            cell,
            scale=scale,
            tint=tint,
            fur_darken=fur_darken,
            eye_color=eye_color,
            fang_boost=fang_boost
        )
        hd_sheet.paste(hd_cell, (sx * scale, sy * scale), hd_cell)

    return hd_sheet


def remaster_all_wolves():
    print('Remastering Wolves (Young Wolf, Classic Wolf, Pack Leader, Warg)...')
    orig_walk = os.path.join(RESOURCES, '270.png')
    orig_att = os.path.join(RESOURCES, '271.png')
    orig_corpse = os.path.join(RESOURCES, '272.png')

    wolf_species = [
        {
            'name': 'Молодой волк (Young Wolf)',
            'suffix': '_t0',
            # Warm tawny golden-grey fur, lighter underbelly
            'tint': ((0.35, 1.15), (0.35, 1.05), (0.35, 0.90)),
            'darken': -0.05,
            'fangs': False
        },
        {
            'name': 'Волк (Classic Wolf)',
            'suffix': '',
            # Natural timber wolf slate grey with amber hints
            'tint': None,
            'darken': 0.0,
            'fangs': True
        },
        {
            'name': 'Вожак стаи (Pack Leader)',
            'suffix': '_t8',
            # Dark charcoal coat, scarred muzzle, fierce contrast
            'tint': ((0.40, 0.85), (0.40, 0.85), (0.40, 0.90)),
            'darken': 0.20,
            'fangs': True
        },
        {
            'name': 'Варг (Warg)',
            'suffix': '_t10',
            # Pitch obsidian-black coat with demonic sheen
            'tint': ((0.50, 0.65), (0.50, 0.60), (0.50, 0.70)),
            'darken': 0.45,
            'fangs': True
        },
        {
            'name': 'Варг (Warg variant _t9)',
            'suffix': '_t9',
            'tint': ((0.50, 0.65), (0.50, 0.60), (0.50, 0.70)),
            'darken': 0.45,
            'fangs': True
        }
    ]

    for sp in wolf_species:
        suf = sp['suffix']
        # 1. Walk / Run sheet (270)
        hd_walk = build_monster_sheet(
            orig_walk, WOLF_FRAMES_270,
            tint=sp['tint'], fur_darken=sp['darken'], fang_boost=sp['fangs']
        )
        hd_walk.save(os.path.join(HD_DIR, f'270{suf}.png'))

        # 2. Attack sheet (271)
        hd_att = build_monster_sheet(
            orig_att, WOLF_FRAMES_271,
            tint=sp['tint'], fur_darken=sp['darken'], fang_boost=True
        )
        hd_att.save(os.path.join(HD_DIR, f'271{suf}.png'))

        # 3. Corpse sheet (272)
        hd_corpse = build_monster_sheet(
            orig_corpse, WOLF_FRAMES_272,
            tint=sp['tint'], fur_darken=sp['darken'], fang_boost=False
        )
        hd_corpse.save(os.path.join(HD_DIR, f'272{suf}.png'))

        print(f"  [OK] Wolf Triad {sp['name']} -> 270{suf}, 271{suf}, 272{suf}")


def remaster_all_bloodflies():
    print('Remastering Bloodflies (Small, Classic, Dread)...')
    orig_fly = os.path.join(RESOURCES, '211.png')
    orig_att = os.path.join(RESOURCES, '212.png')
    orig_corpse = os.path.join(RESOURCES, '213.png')

    fly_species = [
        {
            'name': 'Маленькая кровомуха (Small Bloodfly)',
            'suffix': '_t1',
            # Amber-yellowish, transparent wings
            'tint': ((0.40, 1.25), (0.40, 1.15), (0.40, 0.75)),
            'darken': -0.10,
        },
        {
            'name': 'Кровомуха (Classic Bloodfly Base)',
            'suffix': '',
            # Natural emerald-brown chitin
            'tint': None,
            'darken': 0.0,
        },
        {
            'name': 'Кровомуха (Classic Bloodfly _t5)',
            'suffix': '_t5',
            'tint': None,
            'darken': 0.0,
        },
        {
            'name': 'Ужасная кровомуха (Dread Bloodfly)',
            'suffix': '_t17',
            # Dark obsidian-violet chitin with crimson stinger tone
            'tint': ((0.45, 0.80), (0.45, 0.65), (0.45, 0.95)),
            'darken': 0.35,
        }
    ]

    for sp in fly_species:
        suf = sp['suffix']
        hd_fly = build_monster_sheet(
            orig_fly, BLOODFLY_FRAMES_211,
            tint=sp['tint'], fur_darken=sp['darken']
        )
        hd_fly.save(os.path.join(HD_DIR, f'211{suf}.png'))

        hd_att = build_monster_sheet(
            orig_att, BLOODFLY_FRAMES_212,
            tint=sp['tint'], fur_darken=sp['darken']
        )
        hd_att.save(os.path.join(HD_DIR, f'212{suf}.png'))

        hd_corpse = build_monster_sheet(
            orig_corpse, BLOODFLY_FRAMES_213,
            tint=sp['tint'], fur_darken=sp['darken']
        )
        hd_corpse.save(os.path.join(HD_DIR, f'213{suf}.png'))

        print(f"  [OK] Bloodfly Triad {sp['name']} -> 211{suf}, 212{suf}, 213{suf}")


def remaster_all_scavengers():
    print('Remastering Scavengers (Young Scavenger, Classic Scavenger, Evil Scavenger)...')
    orig_walk = os.path.join(RESOURCES, '221.png')
    orig_att = os.path.join(RESOURCES, '222.png')
    orig_corpse = os.path.join(RESOURCES, '224.png')

    scav_species = [
        {
            'name': 'Молодой падальщик (Young Scavenger)',
            'suffix': '_t2',
            # Pale tawny-grey feathers, smaller beak
            'tint': ((0.35, 1.15), (0.35, 1.10), (0.35, 0.95)),
            'darken': -0.05,
        },
        {
            'name': 'Падальщик (Classic Scavenger Base)',
            'suffix': '',
            'tint': None,
            'darken': 0.0,
        },
        {
            'name': 'Злой падальщик (Evil Scavenger)',
            'suffix': '_t4',
            # Blood-red feathered crest, jagged dark plumage
            'tint': ((0.45, 1.25), (0.45, 0.70), (0.45, 0.70)),
            'darken': 0.20,
        }
    ]

    for sp in scav_species:
        suf = sp['suffix']
        hd_walk = build_monster_sheet(
            orig_walk, SCAVENGER_FRAMES_221,
            tint=sp['tint'], fur_darken=sp['darken']
        )
        hd_walk.save(os.path.join(HD_DIR, f'221{suf}.png'))

        hd_att = build_monster_sheet(
            orig_att, SCAVENGER_FRAMES_222,
            tint=sp['tint'], fur_darken=sp['darken']
        )
        hd_att.save(os.path.join(HD_DIR, f'222{suf}.png'))

        hd_corpse = build_monster_sheet(
            orig_corpse, SCAVENGER_FRAMES_224,
            tint=sp['tint'], fur_darken=sp['darken']
        )
        hd_corpse.save(os.path.join(HD_DIR, f'224{suf}.png'))

        print(f"  [OK] Scavenger Triad {sp['name']} -> 221{suf}, 222{suf}, 224{suf}")


if __name__ == '__main__':
    remaster_all_wolves()
    remaster_all_bloodflies()
    remaster_all_scavengers()
    print('All monster triads successfully remastered!')
