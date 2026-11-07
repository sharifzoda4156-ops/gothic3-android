# Experimental 3x output and complete hero frames

Based on main 0000c640. Separate Android package org.gothic3.fanport.whole3x and separate saves. No art regenerated. No gameplay or model data modified.

The standalone canvas is 720x960, aspect-fit within the device area. Hd.cw/ch and c.sizeChanged divide by 3, retaining a 240x320 world. Drawing, text, clips and mutable terrain buffers use 3x output coordinates. Existing /hd art remains 2x; density metadata distinguishes 3x mutable buffers from 2x sprites. This avoids converting 2x assets to fake 3x detail. Existing text atlas is similarly scaled at rendering. The menu's existing rendering coordinates are updated to the same density.

The one c.d(int[],Graphics) call reference in c.class now invokes GothicCharacters.draw. Model zero (confirmed by c.d(O,0)) captures the existing four-layer renderer through HdVar.dp. Selected image, crop, mirror, order and offsets are preserved. Completed transparent frames are bounded to 256 logical pixels in each dimension and kept in a 64-entry LRU. Other models keep the existing renderer. Existing hero sheets are unchanged. The first use composes a pose at the source density; later draws reuse the complete image.

An optional /hd/whole/hero/SLOT_FRAME_SET_LAYOUT_APPEARANCE9_APPEARANCE10.png supplies a painted complete 3x frame. SLOT=entity[6] low 16 bits, FRAME=entity[7] low 16, SET=entity[8] low 16, LAYOUT=entity[8] high 16. The last two numbers are signed decimal packed appearance fields. Its dimensions must be exactly 3x the bounds of the composed logical frame. Missing/invalid frames fall back to the assembled existing art. These are internal numeric selectors, not yet semantic animation labels. No painted replacements are included in this experiment.

Local checks: original five Python tests, HD inventory, strict JVM loading of all 259 PNGs via three paths and 21 variants. Synthetic raster tests compare whole-frame drawing with layered drawing including alpha, mirroring, camera movement and 3x mutable buffer dimensions. They use a desktop raster backend, not an Android performance measurement. Runtime c.d model execution and all real animation states still need on-device verification.

Limitations: framebuffer pixel count is 2.25x the 2x build, plus a bounded hero cache. Higher resolution does not invent detail in existing 2x art. Final device resizing can resample pixels. Portrait aspect ratio is preserved; 3x does not make the hero larger relative to the world. Actual device performance, terrain scrolling, all attacks/casts/equipment, UI and save/load require acceptance before merging.

## Free-form character animation packs

The optional `hd/characters/hero/animation.properties` (version=1) supersedes the fixed-bound whole-frame mechanism. Each clip is selected by exact model set, slot, layout and both packed appearance words. It owns its PNG sheet, frame pixel dimensions, grid columns, frame durations in game animation ticks, logical display width/height and a foot pivot. Source resolution and display size are independent. No layered body parts or original crop coordinates are required in the new sheets. PNG alpha is preserved and filtering is applied while mapping the full artwork into the current output buffer.

The game remains authoritative for action changes and hit timing. Custom animation follows the game's tick counter, freezes when it does not advance and resets on action change; a non-looping action restarts when its tick counter resets. An animation that exceeds the original action duration is interrupted when gameplay switches actions. This is visual animation support, not a change to combat mechanics. Use a complete set of action/direction clips to avoid falling back to the old mismatched attack art.

Each clip prefix (for example `frontIdle`) has these required properties:

```
version=1
frontIdle.sheet=front-idle.png
frontIdle.set=0
frontIdle.slot=2
frontIdle.layout=0
frontIdle.appearance9=0
frontIdle.appearance10=0
frontIdle.frameWidth=192
frontIdle.frameHeight=320
frontIdle.columns=4
frontIdle.width=17
frontIdle.height=29
frontIdle.pivotX=8
frontIdle.pivotY=28
frontIdle.durations=3,3,3,3
frontIdle.loop=true
frontIdle.mirror=false
```

Appearance values in this example are placeholders; use the actual player's packed appearance. This example is deliberately not installed as an active pack. The source sheet dimensions must match the frame grid exactly. Clip durations and sheet bounds are validated, each sheet is limited to 4 million pixels before decoding, and decoded sheets share a 24 MiB LRU budget. Invalid/missing clips log a warning and fall back to the existing hero. Artwork for the new pack is not complete yet.

## Installed approved artwork (core pack)

The pack now contains 16 aligned PNG sheets / 52 drawings and 28 selectors: unarmed set 0 idle/walk/punch (slots 0–11) and magic set 3 idle/walk/cast (slots 0–15), layout zero. Direction slots follow the actual model table: 0 back, 1 right, 2 front, 3 left. Appearance words explicitly accept `*` for these complete fixed-costume illustrations; more specific selectors take priority. Weapons/equipment sets 1/2/4/5 and hurt/falling/death retain the legacy renderer and artwork. This is a core animation pack, not complete replacement of all hero states.

The approved turnaround, walk, punch and casting illustrations were cut into cells, resized with preserved aspect ratio, and aligned using the boot/ground region. Cells are 320×320 source pixels, displayed in a 40×40 logical box; the visible body is approximately 29 logical pixels tall, with foot pivot (20,38). Larger cell margins accommodate extended arms and strides without shrinking the body. Most source detail is necessarily reduced at the 3x display size. The punch sheet's generated light background was removed before packing. No source PNG, model, game class or gameplay timing was changed by this art integration.

`tools/build_hero_animation_pack.py SOURCE_DIR` rebuilds the pack from `idle.png`, `walk.png`, `punch.png`, `cast.png` (requires Pillow/numpy). Source SHA-256 values and output hashes are recorded in `inventory.json`. The input drawings are preserved in the user's Library. These generated poses have not been accepted as smooth animation on a phone; framing, direction, timing, camera anchoring, combat, casting and transitions back to legacy weapon/fall artwork need device testing. The new pack adds approximately 21 MiB of decoded RGBA sheets when all sheets are resident; its texture cache remains bounded to 24 MiB.
