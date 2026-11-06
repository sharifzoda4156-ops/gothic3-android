# Canonical HD resources and hero animation inventory

`app/src/midlet/resources/hd/` is the canonical artwork directory. The old
`hero_hd/` PNGs have been moved into it without resizing, recoloring, changing
alpha, or changing any frame coordinates. This preserves the detailed hero
artwork instead of reverting him to the simpler old `hd/` drawings. Future art
updates belong in `hd/` only.

## What was bypassing HD

Before this change, `Hd.ci(String)` preferred `hd/`, but the model byte loader
`HeroHD.cb(byte[], int, int)` recognized only 24 hero/weapon PNGs and loaded
them from `hero_hd/`. Other unmatched byte images fell back to a scaled
original. `HdVar.cb` preferred numbered HD images only for IDs >= 200. Merely
updating an HD PNG therefore did not guarantee that every loading route used it.

The hero's `100.mdl` references 24 external PNG sheets. The checked model files
do not embed PNG images; model parts with a zero-length payload load the named
external PNG before calling the byte-image loader.

## Hero sheets

| Sheets | Content |
| --- | --- |
| 100 | Legs and boots |
| 101 | Main torso, directions and movement poses |
| 102 | Torso transition, falling/ground poses |
| 104, 114 | Torso with casting effects |
| 105, 106, 120, 121, 125 | Torso/action pose variants (including unarmed/weapon poses) |
| 112, 113, 116–119, 126, 130 | Weapon overlays |
| 122, 123, 127–129, 131 | Swing/trail overlays |

Content labels come from visual inspection. Exact animation-to-action indices
still require gameplay observation. Weapon/trail sheets are shared with NPC
models, so this migration keeps their existing geometry and artwork intact.

## Routing

Three small method bodies in the shipped game JAR delegate to `GothicAssets`:

- `Hd.ci` -> named original path -> matching `hd/` file;
- `HeroHD.cb` -> SHA-256 of the exact original PNG slice -> matching `hd/` file;
- `HdVar.load` -> validated numbered/variant HD file, retaining its original
  model-part association and equipment variant selection.

The index covers all 259 root PNGs, including non-hero assets. Comparing complete
source bytes avoids accidentally equating indexed PNGs with different palettes.
Expected HD dimensions are exactly twice the original. Unknown byte images and
missing/invalid HD files retain the original Scale2x fallback, with a visible
`GothicHD` warning. Successful HD loads are logged once per path. No fallback to
the retired `hero_hd/` folder exists in the active loaders.

`patch_hd_assets.py` also removes stale, non-executable debug tables from the
three loader classes: pre-existing shortened methods contained debug PCs beyond
their code length and failed strict JVM verification. Other method instructions,
exception handlers and verification frames are retained.

## Verification

```
python3 tools/audit_hd_assets.py
python3 tools/test_hd_routing.py
python3 tools/audit_hd_assets.py --apk path/to/build.apk
```

The JVM test runs the **actual patched game JAR**, using a desktop PNG decoder
in place of Android's `Image` implementation. Every original PNG is exercised
through named, byte-buffer, and model-part routes. Tests also cover a nonzero
buffer offset, missing and wrong-size HD, unindexed PNGs, and invalid ranges.

CI checks the assembled APK itself: all 280 HD PNGs must equal the checkout,
the index must match packaged originals, and the three actual DEX methods must
invoke the native resolver. `adb logcat -s GothicHD:I` exposes actual Android
load selections and fallback warnings during play.

This establishes resource routing and packaging, not on-device animation
appearance. Verify normal movement -> unarmed attack -> casting -> movement on
the phone, plus combat, NPCs, inventory and menus. A visual difference remaining
after this change is an artwork issue rather than a hidden legacy folder.

To regenerate the index after changing original source PNGs (HD-only art changes
do not require regeneration):

```
python3 tools/audit_hd_assets.py --write-index
```
