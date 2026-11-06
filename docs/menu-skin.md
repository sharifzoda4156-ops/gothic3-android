# Gothic menu skin

HG.b(Graphics) draws the shared full-screen menu frame. Its fill at bytecode offset 31 paints the outer background, and offset 431 paints the inner content panel. The title, borders and logo are separate drawing calls and assets. HG.a text helpers paint the selected row before rendering the label. These are the paths used by the title and pause menus.

Eight verified fill calls are redirected to org.gothic3.ui.GothicMenuSkin. It draws a quiet dark brown outer surface, charcoal content panel and a burgundy selected row with aged gold bevels. All drawing follows Hd's 2x coordinate convention and restores the previous Graphics colour. The clipping region and menu geometry are preserved. Shared HG text helpers mean other menus/dialogues using these helpers also receive the skin.

The patch changes only invokestatic constant-pool operands; instruction lengths, branch offsets, exception tables and stack frames are preserved. All other classes in the packaged JAR are identical. The native helper is compiled with the Android application and reached directly from the packaged game class.

Validation: parsed the patched class and checked exactly eight redirected calls, identical method code lengths and instruction positions, and byte-identical other classes. This is structural validation, not device rendering validation. Android acceptance remains pending for title/pause/settings/help, scrolling and coloured text. Check frame/logo colour transitions and touch-controller input.

Reproduce against the pre-skin JAR (the patch refuses an already-patched or unexpected class):

```sh
python tools/patch_menu_skin.py original-gothic3-classes.jar patched-gothic3-classes.jar
```

No device screenshots or performance claims are included. The skin uses no per-frame image allocation; its horizontal surface strips are rendered only when the game draws a menu.
