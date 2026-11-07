import android.util.Log;
import java.awt.image.BufferedImage;
import java.io.ByteArrayOutputStream;
import java.nio.file.Files;
import java.nio.file.Path;
import javax.imageio.ImageIO;
import javax.microedition.lcdui.Image;

public class HdRoutingTest {
    private static void check(boolean value, String message) {
        if (!value) throw new AssertionError(message);
    }

    public static void main(String[] args) throws Exception {
        Path resources = Path.of(args[0]);
        int count = 0;
        for (String line : Files.readAllLines(resources.resolve("hd/source-index.tsv"))) {
            if (line.startsWith("#") || line.isEmpty()) continue;
            String[] fields = line.split("\t");
            String original = fields[1];
            String expected = "/hd" + original;
            int width = Integer.parseInt(fields[2]) * 2;
            int height = Integer.parseInt(fields[3]) * 2;
            byte[] data = Files.readAllBytes(resources.resolve(original.substring(1)));
            Image named = Hd.ci(original);
            check(expected.equals(Image.lastPath), "named path: " + original);
            check(named.getWidth() == width && named.getHeight() == height, "named dimensions");
            Image bytes = Hd.cb(data, 0, data.length);
            check(expected.equals(Image.lastPath), "byte path: " + original);
            check(bytes.getWidth() == width && bytes.getHeight() == height, "byte dimensions");
            // Exercise the real numbered-part route, including the previous <200 gap.
            String stem = original.substring(1, original.length() - 4);
            HdVar.np(stem.matches("[0-9]+") ? Integer.parseInt(stem) : -1);
            Image model = HdVar.cb(data, 0, data.length);
            check(expected.equals(Image.lastPath), "model path: " + original);
            check(model.getWidth() == width && model.getHeight() == height, "model dimensions");
            count++;
        }
        byte[] hero = Files.readAllBytes(resources.resolve("105.png"));
        int variants = 0;
        java.lang.reflect.Method load = HdVar.class.getDeclaredMethod("load", String.class, int.class, int.class);
        load.setAccessible(true);
        try (java.util.stream.Stream<Path> files = Files.list(resources.resolve("hd"))) {
            for (Path file : files.filter(p -> p.getFileName().toString().matches("[0-9]+_t[0-9]+\\.png"))
                    .toArray(Path[]::new)) {
                String name = file.getFileName().toString();
                String base = name.substring(0, name.indexOf('_')) + ".png";
                BufferedImage original = ImageIO.read(resources.resolve(base).toFile());
                String expected = "/hd/" + name;
                Image variant = (Image) load.invoke(null, expected, original.getWidth() * 2, original.getHeight() * 2);
                check(variant != null && expected.equals(Image.lastPath), "variant path: " + name);
                variants++;
            }
        }
        byte[] padded = new byte[hero.length + 17];
        System.arraycopy(hero, 0, padded, 7, hero.length);
        HeroHD.cb(padded, 7, hero.length);
        check("/hd/105.png".equals(Image.lastPath), "sliced PNG offset");
        Hd.ci("101.png");
        check("/hd/101.png".equals(Image.lastPath), "relative named path");

        Image.rejectPath = "/hd/105.png";
        Image fallback = HeroHD.cb(hero, 0, hero.length);
        check(fallback.getWidth() == 168 && fallback.getHeight() == 120, "missing HD fallback scale");
        check(Log.messages.contains("fallback /105.png"), "fallback must be visible");
        Image.rejectPath = null;
        Image.wrongSizePath = "/hd/105.png";
        fallback = Hd.ci("/105.png");
        check(fallback.getWidth() == 168, "bad HD geometry must not be accepted");
        check(Log.messages.contains("rejected dimensions /hd/105.png"), "bad geometry warning");
        Image.wrongSizePath = null;

        BufferedImage unknown = new BufferedImage(3, 5, BufferedImage.TYPE_INT_ARGB);
        unknown.setRGB(1, 1, 0xffbada55);
        ByteArrayOutputStream stream = new ByteArrayOutputStream();
        ImageIO.write(unknown, "PNG", stream);
        byte[] unindexed = stream.toByteArray();
        fallback = Hd.cb(unindexed, 0, unindexed.length);
        check(fallback.getWidth() == 6 && fallback.getHeight() == 10, "unknown PNG fallback");
        check(Log.messages.contains("fallback unindexed byte image"), "unknown image warning");
        try {
            GothicAssets.bytes(hero, 1, Integer.MAX_VALUE);
            throw new AssertionError("overflowing range was accepted");
        } catch (IndexOutOfBoundsException expected) { }
        System.out.println("Passed " + count + " PNGs through named, bytes and model routes and "
                + variants + " equipment/NPC variant PNGs through HdVar.load; "
                + "offset, relative path, missing/wrong-size HD, unknown PNG and range tests passed");
    }
}
