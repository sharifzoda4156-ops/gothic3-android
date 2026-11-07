package android.graphics;
import java.awt.Graphics2D;
import java.awt.geom.AffineTransform;
import java.util.ArrayList;
public class Canvas {
 public final Graphics2D graphics;
 private final ArrayList<AffineTransform> stack=new ArrayList<>();
 public Canvas(Bitmap bitmap){graphics=bitmap.image.createGraphics();}
 public int save(){stack.add(graphics.getTransform());return stack.size();}
 public void restoreToCount(int n){graphics.setTransform(stack.get(n-1));while(stack.size()>=n)stack.remove(stack.size()-1);}
 public void scale(float x,float y){graphics.scale(x,y);}
 public void translate(float x,float y){graphics.translate(x,y);}
 public void drawBitmap(Bitmap bitmap,Rect src,RectF dst,Paint p){graphics.drawImage(bitmap.image,(int)dst.left,(int)dst.top,(int)dst.right,(int)dst.bottom,src.left,src.top,src.right,src.bottom,null);}
 public void drawBitmap(Bitmap bitmap,Rect src,Rect dst,Paint p){graphics.drawImage(bitmap.image,dst.left,dst.top,dst.right,dst.bottom,src.left,src.top,src.right,src.bottom,null);}
}
