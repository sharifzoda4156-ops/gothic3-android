import android.graphics.Canvas;
import android.graphics.Paint;
import android.graphics.Rect;
import android.graphics.RectF;
import android.util.Log;
import java.io.InputStream;
import java.io.IOException;
import java.io.DataInputStream;
import java.util.LinkedHashMap;
import java.util.Iterator;
import java.lang.reflect.Field;
import java.util.HashMap;
import java.util.Properties;
import java.util.WeakHashMap;
import javax.microedition.lcdui.Graphics;
import javax.microedition.lcdui.Image;

/** Optional complete-character animation pack. Game state remains authoritative. */
public final class GothicAnimation {
    private static final HashMap<String,Clip> clips=new HashMap<>();
    private static final WeakHashMap<int[],Playback> playback=new WeakHashMap<>();
    private static boolean loaded;
    private static final LinkedHashMap<String,Image> textures=new LinkedHashMap<>(16,.75f,true);
    private static long textureBytes;
    private static final Paint paint=new Paint();
    static { paint.setFilterBitmap(true); }
    private static synchronized void load(){
        if(loaded)return;loaded=true;
        // Hero pack plus optional monster pack; each pack is validated independently.
        for(String pack:new String[]{"hero","monsters"})try(InputStream stream=GothicAnimation.class.getResourceAsStream("/hd/characters/"+pack+"/animation.properties")){
            if(stream==null)continue;
            Properties p=new Properties();p.load(stream);
            if(!"1".equals(p.getProperty("version")))throw new IOException("Unsupported animation pack version");
            HashMap<String,Clip> ready=new HashMap<>();
            for(String key:p.stringPropertyNames())if(key.endsWith(".sheet")){
                String prefix=key.substring(0,key.length()-6);
                Clip clip=Clip.read(p,prefix,pack);
                String selector=selector(clip.model,clip.set,clip.slot,clip.layout,clip.appearance9,clip.appearance10);
                if(ready.put(selector,clip)!=null||clips.containsKey(selector))throw new IOException("Duplicate animation selector "+selector);
            }
            if(ready.size()>128)throw new IOException("Too many clips");
            clips.putAll(ready);
        }catch(IOException|RuntimeException bad){Log.w("GothicHD","Animation pack "+pack+" disabled: "+bad.getMessage());}
    }
    static String selector(int model,int set,int slot,int layout,int a9,int a10){return model+":"+set+":"+slot+":"+layout+":"+a9+":"+a10;}
    private static final java.util.HashSet<String> reported=new java.util.HashSet<>();
    public static boolean draw(int[] e,Graphics g){
        load();if(clips.isEmpty())return false;
        int model=(e[7]>>>16)&65535,set=e[8]&65535,slot=e[6]&65535,layout=(e[8]>>>16)&65535;
        String sel=selector(model,set,slot,layout,e[9],e[10]);
        // Non-hero selectors are logged once so wolf/monster clips can be keyed from real play.
        if(model!=0&&reported.add(sel)&&reported.size()<=512)Log.i("GothicHD","entity selector model:set:slot:layout:a9:a10 = "+sel);
        Clip clip=clips.get(sel);
        if(clip==null){playback.remove(e);return false;}
        try{
            int tick=(short)(e[6]>>>16);
            Playback state=playback.get(e);
            if(state==null){state=new Playback();playback.put(e,state);}
            int frame=state.frame(clip,tick);
            Image image=clip.image();
            int tile=worldTileSize();
            float x=(e[4]*tile>>12)-cameraX(),y=(e[5]*tile>>12)-cameraY();
            paintFrame(g,clip,image,frame,x,y);
            return true;
        }catch(IOException|ReflectiveOperationException|RuntimeException bad){
            // Disable this clip once; a malformed optional pack must not hide the player.
            clips.values().removeIf(value->value==clip);playback.remove(e);
            Log.w("GothicHD","Animation clip disabled: "+bad.getMessage());return false;
        }
    }
    static void paintFrame(Graphics g,Clip clip,Image image,int frame,float x,float y){
        int col=frame%clip.columns,row=frame/clip.columns;
        Rect src=new Rect(col*clip.frameWidth,row*clip.frameHeight,(col+1)*clip.frameWidth,(row+1)*clip.frameHeight);
        float s=GothicResolution.scale();
        RectF dst=new RectF((x-clip.pivotX)*s,(y-clip.pivotY)*s,(x-clip.pivotX+clip.width)*s,(y-clip.pivotY+clip.height)*s);
        Canvas canvas=g.getCanvas();int save=canvas.save();
        try{
            if(clip.mirror){canvas.translate(2*x*s,0);canvas.scale(-1,1);}
            canvas.drawBitmap(image.getBitmap(),src,dst,paint);
        }finally{canvas.restoreToCount(save);}
    }
    private static Field field(Class<?> owner,String name)throws ReflectiveOperationException{
        for(Field f:owner.getDeclaredFields())if(f.getName().equals(name)&&f.getType()==int.class){f.setAccessible(true);return f;}
        throw new NoSuchFieldException(owner.getName()+"."+name+":int");
    }
    private static Field cameraX,cameraY,tileSize;
    private static int cameraX()throws ReflectiveOperationException{if(cameraX==null)cameraX=field(c.class,"q");return cameraX.getInt(null);}
    private static int cameraY()throws ReflectiveOperationException{if(cameraY==null)cameraY=field(c.class,"c");return cameraY.getInt(null);}
    private static int worldTileSize()throws ReflectiveOperationException{if(tileSize==null)tileSize=field(a.class,"g");return tileSize.getInt(null);}
    static final class Playback{
        Clip clip;int lastTick,elapsed;
        int frame(Clip next,int tick){
            if(clip!=next){clip=next;lastTick=tick;elapsed=0;}
            else if(tick!=lastTick){
                if(tick<lastTick&&!clip.loop)elapsed=0;
                else elapsed=Math.min(Integer.MAX_VALUE-65536,elapsed)+(tick>lastTick?tick-lastTick:1);
                lastTick=tick;
            }
            int phase=clip.loop?elapsed%clip.total:Math.min(elapsed,clip.total-1);
            for(int i=0;i<clip.durations.length;i++){if(phase<clip.durations[i])return i;phase-=clip.durations[i];}
            return clip.durations.length-1;
        }
    }
    static final class Clip{
        String sheet,pack;int model,set,slot,layout,appearance9,appearance10,frameWidth,frameHeight,columns,total;
        float width,height,pivotX,pivotY;boolean loop,mirror;int[] durations;
        static int number(Properties p,String key,int lo,int hi)throws IOException{
            int n=Integer.parseInt(required(p,key));if(n<lo||n>hi)throw new IOException("Out of range "+key);return n;
        }
        static String required(Properties p,String key)throws IOException{String v=p.getProperty(key);if(v==null)throw new IOException("Missing "+key);return v.trim();}
        static float decimal(Properties p,String key,float lo,float hi)throws IOException{float f=Float.parseFloat(required(p,key));if(!Float.isFinite(f)||f<lo||f>hi)throw new IOException("Out of range "+key);return f;}
        static boolean bool(Properties p,String key)throws IOException{String v=required(p,key);if(!v.equals("true")&&!v.equals("false"))throw new IOException("Expected boolean "+key);return Boolean.parseBoolean(v);}
        static Clip read(Properties p,String name)throws IOException{return read(p,name,"hero");}
        static Clip read(Properties p,String name,String pack)throws IOException{
            Clip c=new Clip();String k=name+".";c.pack=pack;
            c.model=p.getProperty(k+"model")==null?0:number(p,k+"model",0,4096);
            if("hero".equals(pack)&&c.model!=0)throw new IOException("Hero pack clips must use model 0");
            if(!"hero".equals(pack)&&c.model==0)throw new IOException("Monster pack clips need a nonzero model");
            c.sheet=required(p,k+"sheet");
            if(!c.sheet.matches("[A-Za-z0-9_-]+\\.png"))throw new IOException("Unsafe sheet path");
            c.set=number(p,k+"set",0,5);c.slot=number(p,k+"slot",0,16);c.layout=number(p,k+"layout",0,3);
            c.appearance9=number(p,k+"appearance9",Integer.MIN_VALUE,Integer.MAX_VALUE);c.appearance10=number(p,k+"appearance10",Integer.MIN_VALUE,Integer.MAX_VALUE);
            c.frameWidth=number(p,k+"frameWidth",1,2048);c.frameHeight=number(p,k+"frameHeight",1,2048);c.columns=number(p,k+"columns",1,128);
            c.width=decimal(p,k+"width",1,256);c.height=decimal(p,k+"height",1,256);c.pivotX=decimal(p,k+"pivotX",-256,512);c.pivotY=decimal(p,k+"pivotY",-256,512);
            c.loop=bool(p,k+"loop");c.mirror=bool(p,k+"mirror");
            String[] ds=required(p,k+"durations").split(",");if(ds.length<1||ds.length>128)throw new IOException("Invalid frame count");c.durations=new int[ds.length];
            for(int i=0;i<ds.length;i++){int d=Integer.parseInt(ds[i].trim());if(d<1||d>1000)throw new IOException("Invalid duration");c.durations[i]=d;c.total+=d;}
            return c;
        }
        Image image()throws IOException{
            synchronized(textures){
                int rows=(durations.length+columns-1)/columns;
                Image cached=textures.get(pack+"/"+sheet);
                if(cached!=null){if(cached.getWidth()!=columns*frameWidth||cached.getHeight()!=rows*frameHeight)throw new IOException("Inconsistent shared sheet geometry "+sheet);return cached;}
                String path="/hd/characters/"+pack+"/"+sheet;
                try(InputStream raw=GothicAnimation.class.getResourceAsStream(path)){
                    if(raw==null)throw new IOException("Missing "+sheet);
                    DataInputStream header=new DataInputStream(raw);
                    if(header.readLong()!=0x89504e470d0a1a0aL||header.readInt()!=13||header.readInt()!=0x49484452)throw new IOException("Invalid PNG "+sheet);
                    int w=header.readInt(),h=header.readInt();
                    if(w<1||h<1||(long)w*h>4194304L||w!=columns*frameWidth||h!=rows*frameHeight)throw new IOException("Wrong sheet dimensions "+sheet);
                }
                Image image=Image.createImage(path);
                long bytes=(long)image.getWidth()*image.getHeight()*4;
                Iterator<Image> oldest=textures.values().iterator();
                while(textureBytes+bytes>24*1024*1024L&&oldest.hasNext()){
                    Image old=oldest.next();textureBytes-=(long)old.getWidth()*old.getHeight()*4;oldest.remove();
                }
                textures.put(pack+"/"+sheet,image);textureBytes+=bytes;return image;
            }
        }
    }
}
