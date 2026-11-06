# Readable dialogue font

The packaged game draws custom text through `Hd` → `RpgFont.draw` → `Graphics.drawRegion`, not the emulator's system Typeface. `RpgFont` loads `/font/rpg.png`, keeps its alpha channel when tinting text, and caches two tinted atlas images. Its width helpers use the embedded WIDTHS array. Its logical line height is 11; drawing uses doubled coordinates and a 14×22 cell in a 224×242 atlas.

This change replaces that atlas with glyphs rasterized from DejaVu Sans, with 4× supersampling and a common baseline. The 167-character ordering, per-character advances, cell dimensions and line height are preserved. Glyphs wider than their existing advance are fitted horizontally to leave a one-pixel gap. All callers of this shared font receive the new glyphs.

`tools/fonts/DejaVuSans-Dialogue.ttf` is a subset of DejaVu Sans containing exactly the existing character repertoire. Its license is alongside it. It is a reproducible build input; the runtime continues loading the PNG.

Regenerate from the repository root (Python, Pillow required):

```sh
python tools/build_readable_font.py --jar app/libs/gothic3-classes.jar --font tools/fonts/DejaVuSans-Dialogue.ttf --output app/src/midlet/resources/font/rpg.png
```

Validation performed: all 167 characters exist in the source font; every non-space glyph has ink; every glyph fits its cell and original advance; output is byte-for-byte reproducible at the pixel level. The width table is read from the packaged class, which is not modified. Comparison image uses the real atlas cells and original advances on a sample Russian dialogue; it is not an Android screenshot.

Android acceptance pending: inspect a long dialogue, quest journal, inventory and coloured text on device. No APK build or physical-device test was performed in this environment.
