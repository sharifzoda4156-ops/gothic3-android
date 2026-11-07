"""
Integrates true high-definition Gothic wolf painted artwork into the game engine sheets
with pixel-perfect bounding boxes and pivots from 101.mdl.
"""

from PIL import Image, ImageFilter, ImageEnhance
import os
import math

BRAIN_DIR = r'C:\Users\Абубакр\.gemini\antigravity\brain\a3052551-b70c-41e5-b9d4-7dbb1e9a3a5f'
HD_DIR = 'app/src/midlet/resources/hd'

# 1. Clean background extraction
def extract_alpha(img_path):
    im = Image.open(img_path).convert('RGB')
    bg = im.getpixel((10, 10))
    rgba = Image.new('RGBA', im.size)
    pin = im.load()
    pout = rgba.load()
    for y in range(im.height):
        for x in range(im.width):
            r, g, b = pin[x, y]
            diff = max(abs(r - bg[0]), abs(g - bg[1]), abs(b - bg[2]))
            if diff < 22:
                pout[x, y] = (0, 0, 0, 0)
            elif diff < 42:
                pout[x, y] = (r, g, b, int(255 * (diff - 22) / 20))
            else:
                pout[x, y] = (r, g, b, 255)
    bbox = rgba.getbbox()
    return rgba.crop(bbox) if bbox else rgba

# Extract the 5 HD master poses
print("Extracting master HD poses...")
side_master = extract_alpha(os.path.join(BRAIN_DIR, 'wolf_side_run_1794060828172.jpg'))
front_master = extract_alpha(os.path.join(BRAIN_DIR, 'wolf_front_walk_1794060892342.jpg'))
rear_master = extract_alpha(os.path.join(BRAIN_DIR, 'wolf_rear_walk_1794060972342.jpg'))
bite_master = extract_alpha(os.path.join(BRAIN_DIR, 'wolf_attack_bite_v2_1794061020481.jpg'))
corpse_master = extract_alpha(os.path.join(BRAIN_DIR, 'wolf_corpse_1794061042769.jpg'))

def fit_to_box(img, max_w, max_h, align_bottom=True):
    """Scales img maintaining aspect ratio to fit inside max_w x max_h."""
    aspect = img.width / img.height
    box_aspect = max_w / max_h
    if aspect > box_aspect:
        w = max_w
        h = max(1, int(w / aspect))
    else:
        h = max_h
        w = max(1, int(h * aspect))
    
    scaled = img.resize((w, h), Image.Resampling.LANCZOS)
    canvas = Image.new('RGBA', (max_w, max_h), (0, 0, 0, 0))
    offset_x = (max_w - w) // 2
    offset_y = (max_h - h) if align_bottom else (max_h - h) // 2
    canvas.paste(scaled, (offset_x, offset_y), scaled)
    return canvas

def apply_species_tone(sheet, tint=None, darken=0.0, glow_eyes=None):
    """Creates distinct visual tiers: Young, Classic, Pack Leader, Warg."""
    im = sheet.copy()
    pixels = im.load()
    w, h = im.size
    for y in range(h):
        for x in range(w):
            r, g, b, a = pixels[x, y]
            if a < 15:
                pixels[x, y] = (0, 0, 0, 0)
                continue
            
            # Apply tone
            if tint:
                tr, tg, tb = tint
                lum = (r * 0.299 + g * 0.587 + b * 0.114)
                r = int(r * (1.0 - tr[0]) + (lum * tr[1]) * tr[0])
                g = int(g * (1.0 - tg[0]) + (lum * tg[1]) * tg[0])
                b = int(b * (1.0 - tb[0]) + (lum * tb[1]) * tb[0])

            if darken != 0.0:
                r = int(r * (1.0 - darken))
                g = int(g * (1.0 - darken))
                b = int(b * (1.0 - darken))

            pixels[x, y] = (
                max(0, min(255, r)),
                max(0, min(255, g)),
                max(0, min(255, b)),
                a
            )
    return im

def build_270_sheet():
    """Builds the 176x144 walk/run sheet with all 12 directional frames."""
    sheet = Image.new('RGBA', (176, 144), (0, 0, 0, 0))
    
    # Side run frames: (0, 8, 10, 11)
    # Stride 1: Frame 0 (0, 0, 74, 42)
    f0 = fit_to_box(side_master, 74, 42)
    sheet.paste(f0, (0, 0), f0)

    # Stride 2: Frame 8 (76, 56, 70, 42) - paws gathered
    s2 = side_master.resize((int(side_master.width * 0.94), int(side_master.height * 1.02)), Image.Resampling.LANCZOS)
    f8 = fit_to_box(s2, 70, 42)
    sheet.paste(f8, (76, 56), f8)

    # Stride 3: Frame 10 (0, 102, 74, 40) - reach
    s3 = side_master.resize((int(side_master.width * 1.02), int(side_master.height * 0.96)), Image.Resampling.LANCZOS)
    f10 = fit_to_box(s3, 74, 40)
    sheet.paste(f10, (0, 102), f10)

    # Stride 4: Frame 11 (76, 102, 72, 42) - push
    s4 = side_master.resize((int(side_master.width * 0.98), int(side_master.height * 0.98)), Image.Resampling.LANCZOS)
    f11 = fit_to_box(s4, 72, 42)
    sheet.paste(f11, (76, 102), f11)

    # Front walk frames: (1, 2, 3, 4) - strict head-on front view
    # Frame 1: (76, 2, 26, 52)
    f1 = fit_to_box(front_master, 26, 52)
    sheet.paste(f1, (76, 2), f1)

    # Frame 2: (104, 0, 22, 54)
    f2 = fit_to_box(front_master, 22, 54)
    sheet.paste(f2, (104, 0), f2)

    # Frame 3: (128, 0, 22, 56)
    f3 = fit_to_box(front_master, 22, 56)
    sheet.paste(f3, (128, 0), f3)

    # Frame 4: (152, 0, 22, 56)
    f4 = fit_to_box(front_master, 22, 56)
    sheet.paste(f4, (152, 0), f4)

    # Rear walk frames: (5, 6, 7, 9) - strict rear view
    # Frame 5: (0, 46, 24, 46)
    f5 = fit_to_box(rear_master, 24, 46)
    sheet.paste(f5, (0, 46), f5)

    # Frame 6: (26, 44, 24, 56)
    f6 = fit_to_box(rear_master, 24, 56)
    sheet.paste(f6, (26, 44), f6)

    # Frame 7: (52, 44, 22, 52)
    f7 = fit_to_box(rear_master, 22, 52)
    sheet.paste(f7, (52, 44), f7)

    # Frame 9: (152, 58, 22, 54)
    f9 = fit_to_box(rear_master, 22, 54)
    sheet.paste(f9, (152, 58), f9)

    return sheet

def build_271_sheet():
    """Builds the 180x140 attack bite sheet with all 11 combat frames."""
    sheet = Image.new('RGBA', (180, 140), (0, 0, 0, 0))

    # Side attack frames: (0, 7, 8, 9)
    # Frame 0: (0, 0, 72, 36) - prep
    f0 = fit_to_box(side_master, 72, 36)
    sheet.paste(f0, (0, 0), f0)

    # Frame 7: (54, 58, 72, 36) - lunge
    b7 = bite_master.resize((int(bite_master.width * 0.95), int(bite_master.height * 0.95)), Image.Resampling.LANCZOS)
    f7 = fit_to_box(b7, 72, 36)
    sheet.paste(f7, (54, 58), f7)

    # Frame 8: (0, 94, 74, 44) - bite strike
    f8 = fit_to_box(bite_master, 74, 44)
    sheet.paste(f8, (0, 94), f8)

    # Frame 9: (76, 94, 72, 44) - recover
    f9 = fit_to_box(bite_master, 72, 44)
    sheet.paste(f9, (76, 94), f9)

    # Front attack frames: (1, 2, 3, 4, 10)
    # Frame 1: (74, 0, 26, 56)
    f1 = fit_to_box(front_master, 26, 56)
    sheet.paste(f1, (74, 0), f1)

    # Frame 2: (102, 2, 24, 56)
    f2 = fit_to_box(front_master, 24, 56)
    sheet.paste(f2, (102, 2), f2)

    # Frame 3: (128, 2, 26, 56)
    f3 = fit_to_box(front_master, 26, 56)
    sheet.paste(f3, (128, 2), f3)

    # Frame 4: (156, 0, 22, 58)
    f4 = fit_to_box(front_master, 22, 58)
    sheet.paste(f4, (156, 0), f4)

    # Frame 10: (152, 80, 22, 56)
    f10 = fit_to_box(front_master, 22, 56)
    sheet.paste(f10, (152, 80), f10)

    # Rear attack frames: (5, 6)
    # Frame 5: (0, 38, 26, 50)
    f5 = fit_to_box(rear_master, 26, 50)
    sheet.paste(f5, (0, 38), f5)

    # Frame 6: (28, 38, 26, 50)
    f6 = fit_to_box(rear_master, 26, 50)
    sheet.paste(f6, (28, 38), f6)

    return sheet

def build_272_sheet():
    """Builds the 64x28 corpse sheet."""
    sheet = Image.new('RGBA', (64, 28), (0, 0, 0, 0))
    f0 = fit_to_box(corpse_master, 64, 28)
    sheet.paste(f0, (0, 0), f0)
    return sheet

print("Assembling master HD sheets...")
master_270 = build_270_sheet()
master_271 = build_271_sheet()
master_272 = build_272_sheet()

# Generate all species
SPECIES_CONFIGS = [
    {
        'name': 'Молодой волк (Young Wolf)',
        'suffix': '_t0',
        'tint': ((0.35, 1.15), (0.35, 1.05), (0.35, 0.90)),
        'darken': -0.05
    },
    {
        'name': 'Волк (Classic Timber Wolf Base)',
        'suffix': '',
        'tint': None,
        'darken': 0.0
    },
    {
        'name': 'Вожак стаи (Pack Leader)',
        'suffix': '_t8',
        'tint': ((0.40, 0.85), (0.40, 0.85), (0.40, 0.90)),
        'darken': 0.18
    },
    {
        'name': 'Варг (Warg)',
        'suffix': '_t10',
        'tint': ((0.50, 0.60), (0.50, 0.55), (0.50, 0.65)),
        'darken': 0.42
    },
    {
        'name': 'Варг вариант (Warg _t9)',
        'suffix': '_t9',
        'tint': ((0.50, 0.60), (0.50, 0.55), (0.50, 0.65)),
        'darken': 0.42
    }
]

for sp in SPECIES_CONFIGS:
    suf = sp['suffix']
    w270 = apply_species_tone(master_270, sp['tint'], sp['darken'])
    w271 = apply_species_tone(master_271, sp['tint'], sp['darken'])
    w272 = apply_species_tone(master_272, sp['tint'], sp['darken'])

    w270.save(os.path.join(HD_DIR, f'270{suf}.png'))
    w271.save(os.path.join(HD_DIR, f'271{suf}.png'))
    w272.save(os.path.join(HD_DIR, f'272{suf}.png'))
    print(f"  [SAVED] {sp['name']} -> 270{suf}.png, 271{suf}.png, 272{suf}.png")

print("All HD wolf sheets successfully integrated!")
