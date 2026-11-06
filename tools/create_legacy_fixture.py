#!/usr/bin/env python3
"""Generate harmless class-file 46/52 samples, NOT the Gothic game code."""
import argparse
import struct
import subprocess
import tempfile
import zipfile
from pathlib import Path


def generate(output: Path):
    with tempfile.TemporaryDirectory() as folder:
        root = Path(folder)
        (root / "SyntheticOld.java").write_text(
            'public class SyntheticOld { public static int answer() { return 42; } }\n'
        )
        (root / "SyntheticModern.java").write_text(
            'public class SyntheticModern { public static int answer() { return 52; } }\n'
        )
        subprocess.run(
            ["javac", "--release", "8", "-d", str(root),
             str(root / "SyntheticOld.java"), str(root / "SyntheticModern.java")],
            check=True,
        )
        old = bytearray((root / "SyntheticOld.class").read_bytes())
        modern = (root / "SyntheticModern.class").read_bytes()
        if old[:4] != b'\xca\xfe\xba\xbe' or struct.unpack_from(">H", old, 6)[0] != 52:
            raise ValueError("Unexpected compiler class-file format")
        struct.pack_into(">H", old, 6, 46)
        if struct.unpack_from(">H", modern, 6)[0] != 52:
            raise ValueError("Unexpected modern class major version")
        output.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as z:
            z.writestr("SyntheticOld.class", old)
            z.writestr("SyntheticModern.class", modern)


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("output", type=Path)
    args = p.parse_args()
    generate(args.output)
    print("Generated mixed-version non-game JAR:", args.output)
