#!/usr/bin/env python3
"""Prepare a privately supplied Gothic 3 JAR for J2ME Loader's midlet flavor.

No game files should be committed to this public repository.
"""
import argparse
import hashlib
import re
import sys
import zipfile
from pathlib import Path, PurePosixPath

GAME_DEP = "implementation files('libs/gothic3-classes.jar')"


def prepare(game: Path, checkout: Path):
    game = game.resolve(strict=True)
    app = checkout / "app"
    flavor = app / "src/midlet"
    gradle_path = app / "build.gradle"
    if not (flavor / "AndroidManifest.xml").exists() or not gradle_path.exists():
        raise ValueError("Expected a J2ME Loader source checkout with the midlet flavor")
    with zipfile.ZipFile(game) as src:
        entries = {e.filename: e for e in src.infolist() if not e.is_dir()}
        if len(entries) > 10000 or sum(e.file_size for e in entries.values()) > 128 * 1024 * 1024:
            raise ValueError("Input game JAR exceeds safe bounds")
        for n, e in entries.items():
            if n.startswith("/") or "\\" in n or ".." in PurePosixPath(n).parts:
                raise ValueError("Unsafe ZIP path: " + n)
            if (e.external_attr >> 16) & 0o170000 == 0o120000:
                raise ValueError("Symlink in game JAR")
        raw_manifest = src.read("META-INF/MANIFEST.MF").decode("utf-8-sig", "replace")
        midlet = re.search(r"(?im)^MIDlet-1:\s*([^\r\n]*)", raw_manifest)
        if not midlet:
            raise ValueError("Missing MIDlet-1 declaration")
        fields = [x.strip() for x in midlet.group(1).split(",", 2)]
        if len(fields) != 3:
            raise ValueError("Malformed MIDlet-1 declaration")
        midlet_class = fields[2]
        class_path = midlet_class.replace(".", "/") + ".class"
        if class_path not in entries:
            raise ValueError("MIDlet class missing: " + class_path)
        if "005.png" not in entries:
            raise ValueError("Expected Gothic map tile atlas 005.png missing")
        classes = sorted(n for n in entries if n.endswith(".class"))
        assets = sorted(n for n in entries if not n.endswith(".class") and not n.upper().startswith("META-INF/"))
        library = app / "libs/gothic3-classes.jar"
        library.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(library, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as out:
            for n in classes:
                out.writestr(n, src.read(n))
        resources = flavor / "resources"
        for n in assets:
            path = resources / n
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(src.read(n))
        props = {}
        for line in raw_manifest.splitlines():
            if ":" in line and not line.startswith(" "):
                key, value = line.split(":", 1)
                props[key.strip()] = value.strip()
        props["Manifest-Version"] = props.get("Manifest-Version", "1.0")
        props["MIDlet-1"] = "Gothic 3 The Beginning, " + fields[1] + ", " + midlet_class
        props["MIDlet-Name"] = "Gothic 3 The Beginning"
        props.setdefault("MIDlet-Version", "1.0")
        props.setdefault("MIDlet-Vendor", "Handy-Games")
        props.setdefault("MicroEdition-Configuration", "CLDC-1.1")
        props.setdefault("MicroEdition-Profile", "MIDP-2.0")
        result_manifest = resources / "MIDLET-META-INF/MANIFEST.MF"
        result_manifest.parent.mkdir(parents=True, exist_ok=True)
        order = ["Manifest-Version", "MIDlet-1", "MIDlet-Name", "MIDlet-Vendor",
                 "MIDlet-Version", "MicroEdition-Configuration", "MicroEdition-Profile"]
        keys = order + [k for k in props if k not in order]
        result_manifest.write_bytes(("\r\n".join(k + ": " + props[k] for k in keys) + "\r\n\r\n").encode())
    sample_java = flavor / "java/com/example/porting/HelloMidlet.java"
    if sample_java.exists():
        sample_java.unlink()
    sample_res = flavor / "resources/com/example/porting/sample.ext"
    if sample_res.exists():
        sample_res.unlink()
    gradle = gradle_path.read_text()
    if GAME_DEP not in gradle:
        if gradle.count("dependencies {") != 1:
            raise ValueError("Unexpected upstream Gradle dependencies layout")
        gradle = gradle.replace("dependencies {", "dependencies {\n    " + GAME_DEP, 1)
    upstream_id = 'applicationId "com.example.androidlet.' + '$' + '{apkName.toLowerCase()}"'
    gradle = gradle.replace(upstream_id, 'applicationId "org.gothic3.fanport"', 1)
    gradle_path.write_text(gradle)
    return {
        "sha256": hashlib.sha256(game.read_bytes()).hexdigest(),
        "midlet_class": midlet_class,
        "classes": len(classes),
        "resources": len(assets),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--jar", required=True, type=Path, help="Local private Gothic JAR")
    parser.add_argument("--upstream", required=True, type=Path, help="J2ME Loader checkout")
    args = parser.parse_args()
    try:
        print(prepare(args.jar, args.upstream))
    except (OSError, zipfile.BadZipFile, ValueError) as exc:
        print("Error: " + str(exc), file=sys.stderr)
        sys.exit(1)
