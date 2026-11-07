import android.graphics.Canvas;
import java.util.WeakHashMap;
import javax.microedition.lcdui.Image;
import javax.microedition.lcdui.Graphics;

/** Output density is independent of the 2x legacy artwork and world coordinates. */
public final class GothicResolution {
    public static int scale() { return 3; }
    private static final WeakHashMap<Image, Integer> densities = new WeakHashMap<>();
    public static synchronized int density(Image image) { return densities.getOrDefault(image, 2); }
    public static synchronized Image buffer(int w, int h) {
        Image image = Image.createImage(w * scale(), h * scale());
        densities.put(image, scale());
        return image;
    }
    public static int width(Image image) { return image.getWidth() / density(image); }
    public static int height(Image image) { return image.getHeight() / density(image); }
    public static int canvasWidth(javax.microedition.lcdui.Canvas c) { return c.getWidth() / scale(); }
    public static int canvasHeight(javax.microedition.lcdui.Canvas c) { return c.getHeight() / scale(); }
    public static void fill(Graphics g,int x,int y,int w,int h) { g.fillRect(x*scale(),y*scale(),w*scale(),h*scale()); }
    public static void rect(Graphics g,int x,int y,int w,int h) {
        if(w<0||h<0)return;
        fill(g,x,y,w+1,1); if(h>0)fill(g,x,y+h,w+1,1);
        if(h>1){fill(g,x,y+1,1,h-1);fill(g,x+w,y+1,1,h-1);}
    }
    public static void line(Graphics g,int x,int y,int x2,int y2) {
        int s=scale(); for(int i=0;i<s;i++)for(int j=0;j<s;j++)g.drawLine(x*s+i,y*s+j,x2*s+i,y2*s+j);
    }
    public static void clip(Graphics g,int x,int y,int w,int h){g.setClip(x*scale(),y*scale(),w*scale(),h*scale());}
    public static void region(Graphics g,Image image,int x,int y,int w,int h,int transform,int dx,int dy,int anchor){
        draw(g,image,x,y,w,h,transform,dx,dy,anchor,density(image));
    }
    static void draw(Graphics g,Image image,int x,int y,int w,int h,int transform,int dx,int dy,int anchor,int density){
        Canvas canvas=g.getCanvas();int save=canvas.save();
        try {canvas.scale((float)scale()/density,(float)scale()/density);
            g.drawRegion(image,x*density,y*density,w*density,h*density,transform,dx*density,dy*density,anchor);
        } finally {canvas.restoreToCount(save);}
    }
    public static void image(Graphics g,Image image,int x,int y,int anchor){region(g,image,0,0,width(image),height(image),0,x,y,anchor);}
    public static void text(Graphics g,String text,int x,int y,int anchor){
        Canvas c=g.getCanvas();int save=c.save();try{c.scale(scale()/2f,scale()/2f);RpgFont.draw(g,text,x,y,anchor);}finally{c.restoreToCount(save);}
    }
}
