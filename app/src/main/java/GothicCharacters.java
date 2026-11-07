import android.graphics.Bitmap;
import android.graphics.Canvas;
import android.graphics.Paint;
import android.graphics.Rect;
import android.util.Log;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.Map;
import javax.microedition.lcdui.Graphics;
import javax.microedition.lcdui.Image;

/** Cache complete hero frames; accepts independently painted whole frames first. */
public final class GothicCharacters {
    private static final ThreadLocal<ArrayList<Part>> capture = new ThreadLocal<>();
    private static final LinkedHashMap<String, Image> whole = new LinkedHashMap<String, Image>(64,.75f,true){
        protected boolean removeEldestEntry(Map.Entry<String,Image> e){return size()>64;}
    };
    public static void draw(int[] entity,Graphics g){
        // Model zero is the player model. Other NPC/model renderers are left alone.
        if(entity==null||entity.length<12||(entity[3]&4)==0||((entity[7]>>>16)&65535)!=0||capture.get()!=null){c.d(entity,g);return;}
        if(GothicAnimation.draw(entity,g))return;
        ArrayList<Part> parts=new ArrayList<>();capture.set(parts);
        try{c.d(entity,g);}finally{capture.remove();}
        render(entity,g,parts);
    }
    static void render(int[] entity,Graphics g,ArrayList<Part> parts){
        // A null sentinel means capture switched to direct rendering for an unsupported part.
        if(parts.isEmpty()||parts.get(0)==null)return;
        int x=Integer.MAX_VALUE,y=Integer.MAX_VALUE,right=Integer.MIN_VALUE,bottom=Integer.MIN_VALUE;
        for(Part p:parts){x=Math.min(x,p.dx);y=Math.min(y,p.dy);right=Math.max(right,p.dx+p.w);bottom=Math.max(bottom,p.dy+p.h);}
        if(right<=x||bottom<=y||right-x>256||bottom-y>256){for(Part p:parts)p.draw(g);return;}
        String state=(entity[6]&65535)+"_"+(entity[7]&65535)+"_"+(entity[8]&65535)+"_"+((entity[8]>>>16)&65535);
        StringBuilder key=new StringBuilder(state).append('_').append(entity[9]).append('_').append(entity[10]);
        for(Part p:parts)key.append('/').append(System.identityHashCode(p.image)).append(':').append(p.sx).append(',').append(p.sy).append(',').append(p.w).append(',').append(p.h).append(',').append(p.transform).append(',').append(p.dx-x).append(',').append(p.dy-y);
        Image frame=whole.get(key.toString());
        if(frame==null){
            Bitmap bitmap=Bitmap.createBitmap((right-x)*2,(bottom-y)*2,Bitmap.Config.ARGB_8888);
            Canvas canvas=new Canvas(bitmap);Paint paint=new Paint();paint.setFilterBitmap(false);
            for(Part p:parts){
                int save=canvas.save();int dx=(p.dx-x)*2,dy=(p.dy-y)*2;
                if(p.transform==2){canvas.translate(dx+p.w*2,dy);canvas.scale(-1,1);dx=0;dy=0;}
                canvas.drawBitmap(p.image.getBitmap(),new Rect(p.sx*2,p.sy*2,(p.sx+p.w)*2,(p.sy+p.h)*2),new Rect(dx,dy,dx+p.w*2,dy+p.h*2),paint);
                canvas.restoreToCount(save);
            }
            frame=new Image(bitmap);whole.put(key.toString(),frame);
            // Diagnostic (once per new composed pose): which numbered sheets build this hero frame.
            // Read with: adb logcat -s GothicHD:I
            StringBuilder ids=new StringBuilder();
            for(Part p:parts){Object id=HdVar.partOf.get(p.image);ids.append(id instanceof Integer?String.valueOf(id):"?").append('@').append(p.image.getWidth()).append('x').append(p.image.getHeight()).append(' ');}
            Log.i("GothicHD","hero pose slot_frame_set_layout="+state+" app="+entity[9]+"/"+entity[10]+" sheets="+ids.toString().trim());
        }
        // A replacement uses the exact composite bounds, 3 pixels per world pixel.
        // Include equipment/appearance in filename to avoid applying art to another loadout.
        String path="/hd/whole/hero/"+state+"_"+entity[9]+"_"+entity[10]+".png";
        Image replacement=WholeFiles.get(path,(right-x)*3,(bottom-y)*3);
        if(replacement!=null)GothicResolution.draw(g,replacement,0,0,right-x,bottom-y,0,x,y,20,3);
        else GothicResolution.region(g,frame,0,0,right-x,bottom-y,0,x,y,20);
    }
    public static void part(Graphics g,Image image,int sx,int sy,int w,int h,int transform,int dx,int dy,int anchor,int[] entity){
        Image selected=image;
        Object id=HdVar.partOf.get(image);
        try { if(id instanceof Integer&&entity!=null&&entity.length>11)selected=HdVar.pick((Integer)id,entity,image); }
        catch (RuntimeException badVariant) { selected=image; }
        ArrayList<Part> parts=capture.get();
        if(parts==null||(!parts.isEmpty()&&parts.get(0)==null)){
            GothicResolution.region(g,selected,sx,sy,w,h,transform,dx,dy,anchor);
            return;
        }
        if(anchor!=20||(transform!=0&&transform!=2)){
            // Preserve the original draw order and avoid re-running game code.
            // Flush any queued layers, then draw this and all following layers directly.
            for(Part part:parts)part.draw(g);
            parts.clear();
            parts.add(null); // pass-through marker; render() must not composite it
            Log.w("GothicHD","Unsupported hero part; using legacy renderer");
            GothicResolution.region(g,selected,sx,sy,w,h,transform,dx,dy,anchor);
            return;
        }
        parts.add(new Part(selected,sx,sy,w,h,transform,dx,dy));
    }
    static final class Part{
        final Image image;final int sx,sy,w,h,transform,dx,dy;
        Part(Image i,int x,int y,int w,int h,int t,int dx,int dy){image=i;sx=x;sy=y;this.w=w;this.h=h;transform=t;this.dx=dx;this.dy=dy;}
        void draw(Graphics g){GothicResolution.region(g,image,sx,sy,w,h,transform,dx,dy,20);}
    }
    static final class WholeFiles{
        static final Map<String,Image> found=new LinkedHashMap<String,Image>(64,.75f,true){protected boolean removeEldestEntry(Map.Entry<String,Image> e){return size()>64;}};
        static Image get(String path,int w,int h){
            if(found.containsKey(path))return found.get(path);
            Image image=null;
            try{image=Image.createImage(path);if(image.getWidth()!=w||image.getHeight()!=h){Log.w("GothicHD","whole frame wrong size "+path);image=null;}}
            catch(java.io.IOException missing){ }
            found.put(path,image);return image;
        }
    }
}
