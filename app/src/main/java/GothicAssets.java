import android.util.Log;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.HashMap;
import java.util.HashSet;
import java.util.Map;
import java.util.Set;

import javax.microedition.lcdui.Image;

/** One HD source for both named images and the model loader's byte buffers. */
public final class GothicAssets {
    private static final String TAG = "GothicHD";
    private static final Map<String, Entry> BY_DIGEST = new HashMap<>();
    private static final Map<String, Entry> BY_NAME = new HashMap<>();
    private static final Set<String> REPORTED = new HashSet<>();

    static {
        try (InputStream stream = GothicAssets.class.getResourceAsStream("/hd/source-index.tsv")) {
            if (stream == null) throw new IOException("Missing HD source index");
            try (BufferedReader reader = new BufferedReader(new InputStreamReader(stream, "UTF-8"))) {
                String line;
                while ((line = reader.readLine()) != null) {
                    if (line.isEmpty() || line.startsWith("#")) continue;
                    String[] fields = line.split("\t");
                    if (fields.length != 4) throw new IOException("Invalid HD index row");
                    Entry entry = new Entry(fields[1], Integer.parseInt(fields[2]),
                            Integer.parseInt(fields[3]));
                    if (BY_DIGEST.put(fields[0], entry) != null
                            || BY_NAME.put(entry.name, entry) != null) {
                        throw new IOException("Ambiguous HD source index");
                    }
                }
            }
        } catch (IOException | RuntimeException e) {
            throw new ExceptionInInitializerError(e);
        }
    }

    private GothicAssets() { }

    public static Image named(String name) throws IOException {
        String path = name.startsWith("/") ? name : "/" + name;
        // Explicit resource paths already specify their scale (font atlases included).
        if (path.startsWith("/hd/") || path.startsWith("/font/")) {
            return Image.createImage(path);
        }
        Entry entry = BY_NAME.get(path);
        if (entry != null) {
            Image hd = sized("/hd" + path, entry.width * 2, entry.height * 2);
            if (hd != null) return hd;
        } else {
            // Preserve the previous named-image rule for non-indexed resources.
            try {
                Image original = Image.createImage(path);
                Image hd = sized("/hd" + path, original.getWidth() * 2, original.getHeight() * 2);
                if (hd != null) return hd;
                report("fallback " + path, true);
                return Hd.scale(original);
            } catch (IOException e) {
                report("unreadable " + path, true);
                throw e;
            }
        }
        report("fallback " + path, true);
        return Hd.scale(Image.createImage(path));
    }

    public static Image bytes(byte[] data, int offset, int length) {
        if (data == null) throw new NullPointerException("image data");
        if (offset < 0 || length < 0 || offset > data.length - length) {
            throw new IndexOutOfBoundsException("image range");
        }
        Entry entry = BY_DIGEST.get(digest(data, offset, length));
        if (entry != null) {
            Image hd = sized("/hd" + entry.name, entry.width * 2, entry.height * 2);
            if (hd != null) return hd;
        }
        report("fallback " + (entry == null ? "unindexed byte image" : entry.name), true);
        return Hd.scale(Image.createImage(data, offset, length));
    }

    /** Also used by HdVar for numbered model parts and equipment variants. */
    public static Image sized(String path, int width, int height) {
        try {
            Image image = Image.createImage(path);
            if (width <= 0 || image.getWidth() != width || image.getHeight() != height) {
                report("rejected dimensions " + path, true);
                return null;
            }
            if ("/hd/120.png".equals(path) && width == 136 && height == 112) {
                if (isKnownPunchSheet()) image = normalizePunchSkin(image);
                else report("punch sheet changed; skin correction skipped", true);
            }
            report("HD " + path, false);
            return image;
        } catch (IOException e) {
            report("missing or invalid " + path, true);
            return null;
        }
    }

    // A replacement HD atlas can reuse the same dimensions with new poses. Do
    // not apply coordinates/color corrections to art they were not made for.
    private static boolean isKnownPunchSheet() {
        try (InputStream stream = GothicAssets.class.getResourceAsStream("/hd/120.png")) {
            if (stream == null) return false;
            MessageDigest sha = MessageDigest.getInstance("SHA-256");
            byte[] buffer = new byte[8192];
            int count;
            while ((count = stream.read(buffer)) != -1) sha.update(buffer, 0, count);
            StringBuilder result = new StringBuilder(64);
            for (byte value : sha.digest()) {
                result.append(Character.forDigit((value >>> 4) & 15, 16));
                result.append(Character.forDigit(value & 15, 16));
            }
            return result.toString().equals("86509132fcca0964fd6f6939d7bbb9543ccff0bfe280db9b21c7d773279edb3e");
        } catch (IOException | NoSuchAlgorithmException e) {
            return false;
        }
    }

    // Coordinates refer to the existing 2x atlas. Restrict the adjustment to
    // face/hand areas so armor, clothing, equipment and alpha remain intact.
    private static Image normalizePunchSkin(Image image) {
        int width = image.getWidth(), height = image.getHeight();
        int[] pixels = new int[width * height];
        image.getRGB(pixels, 0, width, 0, 0, width, height);
        for (int y = 0; y < height; y++) {
            for (int x = 0; x < width; x++) {
                boolean face = in(x, y, 11, 3, 22, 15) || in(x, y, 47, 3, 59, 15)
                        || in(x, y, 79, 3, 92, 15) || in(x, y, 114, 3, 125, 15)
                        || in(x, y, 12, 42, 23, 54) || in(x, y, 45, 42, 56, 54)
                        || in(x, y, 85, 42, 96, 54);
                boolean fist = in(x, y, 4, 13, 13, 23) || in(x, y, 17, 16, 26, 25)
                        || in(x, y, 36, 13, 45, 23) || in(x, y, 48, 19, 59, 27)
                        || in(x, y, 86, 27, 96, 36) || in(x, y, 97, 23, 105, 31)
                        || in(x, y, 112, 22, 120, 31) || in(x, y, 120, 22, 130, 31)
                        || in(x, y, 0, 50, 10, 61) || in(x, y, 31, 49, 41, 60)
                        || in(x, y, 65, 49, 74, 60) || in(x, y, 83, 61, 93, 71)
                        || in(x, y, 8, 42, 13, 48) || in(x, y, 73, 81, 79, 89);
                if (!face && !fist) continue;
                int i = y * width + x, color = pixels[i];
                int a = color >>> 24, r = color >>> 16 & 255, g = color >>> 8 & 255, b = color & 255;
                // Select warm, illuminated skin. Dark contours and neutral armor stay as they are.
                if (a == 0 || r <= 115 || g <= 75 || b <= 30 || r <= g + 5 || g <= b + 5
                        || g * 100 < r * 52) continue;
                int nr = face ? (r * 92 / 100 + 5) : (r * 80 / 100 + 10);
                int ng = face ? (g * 84 / 100 + 5) : (g * 70 / 100 + 5);
                int nb = face ? (b * 94 / 100 + 3) : (b * 78 / 100 + 3);
                pixels[i] = (a << 24) | (nr << 16) | (ng << 8) | nb;
            }
        }
        return Image.createRGBImage(pixels, width, height, true);
    }

    private static boolean in(int x, int y, int left, int top, int right, int bottom) {
        return x >= left && x < right && y >= top && y < bottom;
    }

    private static String digest(byte[] data, int offset, int length) {
        try {
            MessageDigest sha = MessageDigest.getInstance("SHA-256");
            sha.update(data, offset, length);
            byte[] bytes = sha.digest();
            StringBuilder result = new StringBuilder(64);
            for (byte value : bytes) {
                result.append(Character.forDigit((value >>> 4) & 15, 16));
                result.append(Character.forDigit(value & 15, 16));
            }
            return result.toString();
        } catch (NoSuchAlgorithmException e) {
            throw new AssertionError(e);
        }
    }

    private static synchronized void report(String message, boolean warning) {
        if (!REPORTED.add(message)) return;
        if (warning) Log.w(TAG, message);
        else Log.i(TAG, message);
    }

    private static final class Entry {
        final String name;
        final int width;
        final int height;

        Entry(String name, int width, int height) {
            this.name = name;
            this.width = width;
            this.height = height;
        }
    }
}
