package org.gothic3.ui;

import javax.microedition.lcdui.Graphics;

/** Menu-only drawing hooks. Coordinates follow Hd's doubled logical pixels. */
public final class GothicMenuSkin {
    private GothicMenuSkin() {}

    public static void background(Graphics g, int x, int y, int w, int h) {
        surface(g, x, y, w, h, true);
    }

    public static void panel(Graphics g, int x, int y, int w, int h) {
        surface(g, x, y, w, h, false);
    }

    private static void surface(Graphics g, int x, int y, int w, int h, boolean outer) {
        if (w <= 0 || h <= 0) return;
        int saved = g.getColor();
        x *= 3; y *= 3; w *= 3; h *= 3;
        // Quiet horizontal grain; text always remains the strongest element.
        for (int row = 0; row < h; row += 2) {
            int shade = ((row * 13 + row / 7) & 3);
            int edge = Math.abs(2 * row - h) * 5 / Math.max(1, h);
            int base = (outer ? 34 : 19) + shade - edge;
            g.setColor(base + (outer ? 15 : 3), base, Math.max(0, base - 5));
            g.fillRect(x, y + row, w, Math.min(2, h - row));
        }
        g.setColor(saved);
    }

    public static void selection(Graphics g, int x, int y, int w, int h) {
        if (w <= 0 || h <= 0) return;
        int saved = g.getColor();
        x *= 3; y *= 3; w *= 3; h *= 3;
        for (int row = 0; row < h; row++) {
            int glow = (h - Math.abs(2 * row - h)) * 23 / Math.max(1, h);
            g.setColor(52 + glow, 19 + glow / 3, 17 + glow / 4);
            g.fillRect(x, y + row, w, 1);
        }
        // Aged gold bevel and small side accents frame the selected label.
        g.setColor(0x9d8051); g.fillRect(x, y, w, 1);
        g.setColor(0x493622); g.fillRect(x, y + h - 1, w, 1);
        g.setColor(0xc4a66a);
        g.fillRect(x, y + h / 2 - 3, 2, 6);
        g.fillRect(x + w - 2, y + h / 2 - 3, 2, 6);
        g.setColor(saved);
    }
}
