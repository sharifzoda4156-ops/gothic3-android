package android.graphics;
import java.awt.image.BufferedImage;
public class Bitmap {
 public enum Config { ARGB_8888 }
 public final BufferedImage image;
 public Bitmap(BufferedImage i){image=i;}
 public static Bitmap createBitmap(int w,int h,Config c){return new Bitmap(new BufferedImage(w,h,BufferedImage.TYPE_INT_ARGB));}
}
