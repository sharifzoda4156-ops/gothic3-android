#!/usr/bin/env python3
"""Static read-only 2x geometry audit of a private Java ME Gothic game JAR.

Does not extract or distribute game assets; does not prove Android rendering.
"""
from __future__ import annotations
import argparse
import json
import struct
import zipfile
from pathlib import Path

PNG_SIG = b'\x89PNG\r\n\x1a\n'


def png_size(data: bytes):
    if len(data) < 24 or data[:8] != PNG_SIG or data[12:16] != b'IHDR':
        return None
    w, h = struct.unpack_from('>II', data, 16)
    return (w, h) if w > 0 and h > 0 else None


def audit(jar: Path) -> dict:
    with zipfile.ZipFile(jar) as archive:
        names = set(archive.namelist())
        hd_names = sorted(n for n in names if n.startswith('hd/') and n.lower().endswith('.png'))
        matched, variants, invalid = [], [], []
        for hd_name in hd_names:
            base = hd_name[3:]
            if base not in names:
                variants.append(hd_name)
                continue
            original = png_size(archive.read(base))
            enlarged = png_size(archive.read(hd_name))
            if not original or not enlarged or enlarged != (original[0] * 2, original[1] * 2):
                invalid.append({'name': hd_name, 'original': original, 'hd': enlarged})
            else:
                matched.append(hd_name)
        majors = {}
        for filename in sorted(n for n in names if n.endswith('.class')):
            data = archive.read(filename)
            if len(data) >= 8 and data[:4] == b'\xca\xfe\xba\xbe':
                majors[filename] = struct.unpack_from('>H', data, 6)[0]
        return {
            'hd_png_total': len(hd_names),
            'hd_png_matched_2x': len(matched),
            'hd_png_variant_only': len(variants),
            'hd_png_invalid': invalid,
            'hd_png_variant_examples': variants[:21],
            'original_atlas_005': png_size(archive.read('005.png')) if '005.png' in names else None,
            'hd_atlas_005': png_size(archive.read('hd/005.png')) if 'hd/005.png' in names else None,
            'class_file_major_versions': majors,
            'static_checks_passed': len(invalid) == 0 and 'Hd.class' in names and '005.png' in names and 'hd/005.png' in names,
            'note': 'Only verifies static atlas geometry, not actual game rendering or FPS.'
        }


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('jar', type=Path, help='Private local game JAR')
    results = audit(p.parse_args().jar)
    print(json.dumps(results, ensure_ascii=False, indent=2))
    raise SystemExit(0 if results['static_checks_passed'] else 1)
