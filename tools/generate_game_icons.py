#!/usr/bin/env python3
"""Generate standalone Gothic launcher icons from the game's own HD G emblem.

Requires Pillow. Do not generate from the J2ME Loader icon.
"""
from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageOps

DENSITIES = {"mdpi": 1, "hdpi": 1.5, "xhdpi": 2, "xxhdpi": 3, "xxxhdpi": 4}
BACKGROUND = (80, 31, 21, 255)  # Same warm brown as Gothic 3's HD icon.


def generate(source: Path, out_root: Path) -> list[Path]:
    with Image.open(source) as image:
        image.load()
        emblem = image.convert("RGBA")
    if emblem.width < 16 or emblem.height < 16:
        raise ValueError("Gothic emblem is too small")
    if emblem.width != emblem.height:
        raise ValueError("Gothic emblem must be square")

    outputs = []
    for density, factor in DENSITIES.items():
        directory = out_root / f"mipmap-{density}"
        directory.mkdir(parents=True, exist_ok=True)

        legacy_size = round(48 * factor)
        legacy_logo_size = round(legacy_size * 0.92)
        legacy = Image.new("RGBA", (legacy_size, legacy_size), BACKGROUND)
        logo = ImageOps.contain(
            emblem, (legacy_logo_size, legacy_logo_size), Image.Resampling.LANCZOS
        )
        legacy.alpha_composite(logo, ((legacy_size - logo.width) // 2,
                                      (legacy_size - logo.height) // 2))
        path = directory / "ic_launcher.png"
        legacy.save(path, optimize=True)
        outputs.append(path)

        # Android adaptive icon: keep the G inside the central 66dp safe area.
        adaptive_size = round(108 * factor)
        adaptive_logo_size = round(64 * factor)
        foreground = Image.new("RGBA", (adaptive_size, adaptive_size), (0, 0, 0, 0))
        logo = ImageOps.contain(
            emblem, (adaptive_logo_size, adaptive_logo_size), Image.Resampling.LANCZOS
        )
        foreground.alpha_composite(logo, ((adaptive_size - logo.width) // 2,
                                          (adaptive_size - logo.height) // 2))
        path = directory / "ic_launcher_foreground.png"
        foreground.save(path, optimize=True)
        outputs.append(path)
    return outputs


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=Path("app/src/midlet/resources/hd/icon.png"))
    parser.add_argument("--output", type=Path, default=Path("app/src/midlet/res"))
    args = parser.parse_args()
    for created in generate(args.source, args.output):
        print(created)
