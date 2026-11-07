package javax.microedition.lcdui;

import java.awt.image.BufferedImage;
import java.io.ByteArrayInputStream;
import java.io.IOException;
import java.io.InputStream;
import javax.imageio.ImageIO;

/** Desktop PNG decoder for exercising the actual patched game loader classes. */
public class Image {
    public static String lastPath;
    public static String rejectPath;
    public static String wrongSizePath;
    private final BufferedImage image;
    private Image(BufferedImage image) { this.image = image; }
    public static Image createImage(String name) throws IOException {
        lastPath = name;
        if (name.equals(rejectPath)) throw new IOException("simulated missing resource");
        if (name.equals(wrongSizePath)) return createImage(1, 1);
        try (InputStream stream = Image.class.getResourceAsStream(name)) {
            if (stream == null) throw new IOException(name);
            BufferedImage bitmap = ImageIO.read(stream);
            if (bitmap == null) throw new IOException("invalid PNG");
            return new Image(bitmap);
        }
    }
    public static Image createImage(byte[] data, int offset, int length) {
        try {
            BufferedImage bitmap = ImageIO.read(new ByteArrayInputStream(data, offset, length));
            if (bitmap == null) throw new IllegalArgumentException("invalid PNG");
            return new Image(bitmap);
        } catch (IOException e) { throw new IllegalArgumentException(e); }
    }
    public static Image createImage(int width, int height) {
        return new Image(new BufferedImage(width, height, BufferedImage.TYPE_INT_ARGB));
    }
    public static Image createRGBImage(int[] data, int width, int height, boolean alpha) {
        Image result = createImage(width, height);
        result.image.setRGB(0, 0, width, height, data, 0, width);
        return result;
    }
    public int getWidth() { return image.getWidth(); }
    public int getHeight() { return image.getHeight(); }
    public void getRGB(int[] data, int offset, int stride, int x, int y, int width, int height) {
        image.getRGB(x, y, width, height, data, offset, stride);
    }
}
