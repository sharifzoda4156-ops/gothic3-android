package javax.microedition.lcdui;
import android.graphics.Canvas;
import android.graphics.Rect;
public class Graphics {
 private final Canvas canvas;
 public Graphics(Image image){canvas=new Canvas(image.getBitmap());}
 public Canvas getCanvas(){return canvas;}
 public void fillRect(int x,int y,int w,int h){canvas.graphics.fillRect(x,y,w,h);}
 public void drawLine(int x,int y,int x2,int y2){canvas.graphics.drawLine(x,y,x2,y2);}
 public void setClip(int x,int y,int w,int h){canvas.graphics.setClip(x,y,w,h);}
 public void setColor(int c){canvas.graphics.setColor(new java.awt.Color(c));}
 public int getColor(){return canvas.graphics.getColor().getRGB();}
 public void drawString(String s,int x,int y,int anchor){}
 public void drawRegion(Image i,int sx,int sy,int w,int h,int t,int x,int y,int anchor){
  if(anchor!=20)throw new AssertionError("test anchor "+anchor);
  int save=canvas.save();
  if(t==2){canvas.translate(x+w,y);canvas.scale(-1,1);x=0;y=0;}
  else if(t!=0)throw new AssertionError("test transform "+t);
  canvas.drawBitmap(i.getBitmap(),new Rect(sx,sy,sx+w,sy+h),new Rect(x,y,x+w,y+h),null);canvas.restoreToCount(save);
 }
}
