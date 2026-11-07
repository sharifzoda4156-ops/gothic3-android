#!/usr/bin/env python3
"""Fail a Gothic build if its APK omitted our native input or HD3x classes."""
from __future__ import annotations

import argparse
from pathlib import Path
from zipfile import ZipFile

# D8 debug APKs include JVM type descriptors as strings in classes*.dex.
# Check the *output artifact*, not just the presence of source files.
REQUIRED_CLASSES = (
    b"Ljavax/microedition/shell/gothic/GothicControlsView;",
    b"Ljavax/microedition/shell/gothic/GothicDirections;",
    b"Lru/playsoftware/j2meloader/config/GothicProfileDefaults;",
    b"LGothicResolution;",
    b"LGothicAssets;",
)


def verify(apk: Path) -> None:
    if not apk.is_file():
        raise FileNotFoundError(apk)
    with ZipFile(apk) as archive:
        dex_files = [p for p in archive.namelist() if p.startswith("classes")
                     and p.endswith(".dex") and "/" not in p]
        if not dex_files:
            raise ValueError(f"{apk}: no compiled DEX found")
        dex = b"".join(archive.read(p) for p in dex_files)
        missing = [name.decode("ascii") for name in REQUIRED_CLASSES if name not in dex]
        if missing:
            raise ValueError(f"{apk}: missing Gothic game features from DEX: {missing}")
    print(f"Verified native Gothic control deck, first-launch preset and HD3x renderer: {apk}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apk", type=Path, required=True)
    args = parser.parse_args()
    verify(args.apk)
