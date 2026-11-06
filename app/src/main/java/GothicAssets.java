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
            report("HD " + path, false);
            return image;
        } catch (IOException e) {
            report("missing or invalid " + path, true);
            return null;
        }
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
