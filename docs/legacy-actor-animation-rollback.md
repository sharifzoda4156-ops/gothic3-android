# Compatibility rollback: original character animation, HD world retained

The HDx3 output path and HD artwork for the environment, menus, font and effects remain enabled.
This branch changes **only the runtime character image/rendering paths**:

1. `GothicCharacters.draw` delegates directly to the original `c.d` game renderer. The optional whole-frame compositor and independent hero animation pack are bypassed.
2. The model byte-image path (`HeroHD.cb` / `HdVar.cb` -> `GothicAssets.bytes`) uses the original PNG atlas and the existing 2x `Hd.scale` fallback. This restores frame silhouettes, crop coordinates and poses for heroes, NPCs and mobs without touching game simulation, action selection, timing or combat.
3. Numbered model variant lookups (`HdVar.load` -> `GothicAssets.sized`) ending in `_tN.png` use the corresponding original base PNG, not custom recoloured HD atlases. This intentionally sacrifices those custom appearance variations to restore animation geometry. The base original must exist and match the requested dimensions; an invalid base is rejected rather than drawing mismatched frames.
4. Named resources (`Hd.ci` -> `GothicAssets.named`) are **unchanged**. HD world tiles, interface artwork, effects and the 720x960 (3x) renderer stay active.

No 2D character sprites or experimental files are deleted from Git history. The original model rendering is simply selected at runtime. PR #9 is still an art archive and must not be merged as-is. Open wolf PR #13 contains remastered character assets that this rollback would intentionally bypass; assess separately before merging.

## Verification

Run:

```sh
python3 tools/audit_hd_assets.py
python3 tools/test_hd_routing.py
python3 -m unittest discover -s tests -v
./gradlew :app:testMidletDebugUnitTest :app:assembleMidletDebug
```

`HdRoutingTest` checks named HD imagery still loads and that original model and variant sheets preserve their source pixels and dimensions. Only **on-device testing** can confirm animation quality, silhouettes, directions, hit/death transitions and equipment across all characters. Inspect a hero walking, punching, casting, changing equipment, NPC movement/attacks, wolves, scavengers and bloodflies before merge.

This is a **selective visual rollback**, not an APK/game-state downgrade. Existing saves and touch controls must remain unchanged.
