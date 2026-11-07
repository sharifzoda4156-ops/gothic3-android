import java.util.ArrayList;
import javax.microedition.lcdui.*;
public class WholeHeroTest {
 static void check(boolean b,String m){if(!b)throw new AssertionError(m);}
 static int[] pixels(Image i){int[] p=new int[i.getWidth()*i.getHeight()];i.getRGB(p,0,i.getWidth(),0,0,i.getWidth(),i.getHeight());return p;}
 static final class RecordingGraphics extends Graphics {
  int directCalls;
  RecordingGraphics(Image image){super(image);}
  @Override public void drawRegion(Image image,int sx,int sy,int w,int h,int transform,int x,int y,int anchor){
   directCalls++;
   if(transform==0&&anchor==20)super.drawRegion(image,sx,sy,w,h,transform,x,y,anchor);
  }
 }
 public static void main(String[] args)throws Exception{
  check(Hd.cw(new Canvas())==240&&Hd.ch(new Canvas())==320,"3x keeps world size");
  Image buffer=Hd.cm(8,7);check(buffer.getWidth()==24&&buffer.getHeight()==21,"3x offscreen allocation");
  check(Hd.iw(buffer)==8&&Hd.ih(buffer)==7,"offscreen logical dimensions");
  Image artwork=Image.createRGBImage(new int[]{0xffff0000,0xff00ff00,0xff0000ff,0x80ffff00,0,0xffffffff,0xff008888,0xff880088,0xff888800,0xffffffff,0,0xffffffff,0xff111111,0xff222222,0xff333333,0xff444444},4,4,true);
  ArrayList<GothicCharacters.Part> parts=new ArrayList<>();
  parts.add(new GothicCharacters.Part(artwork,0,0,2,2,0,2,3));
  parts.add(new GothicCharacters.Part(artwork,0,0,2,2,2,3,4));
  int[] entity=new int[12];Image actual=Image.createImage(30,30),expected=Image.createImage(30,30);
  GothicCharacters.render(entity,actual.getGraphics(),parts);
  for(GothicCharacters.Part p:parts)p.draw(expected.getGraphics());
  check(java.util.Arrays.equals(pixels(actual),pixels(expected)),"whole frame matches layered drawing, including alpha and mirror");
  // Camera translation must not change appearance or reuse a frame at its old position.
  ArrayList<GothicCharacters.Part> moved=new ArrayList<>();
  for(GothicCharacters.Part p:parts)moved.add(new GothicCharacters.Part(p.image,p.sx,p.sy,p.w,p.h,p.transform,p.dx+1,p.dy+2));
  actual=Image.createImage(30,30);expected=Image.createImage(30,30);
  GothicCharacters.render(entity,actual.getGraphics(),moved);for(GothicCharacters.Part p:moved)p.draw(expected.getGraphics());
  check(java.util.Arrays.equals(pixels(actual),pixels(expected)),"camera independent cached frame");
  // An unexpected model transform must not crash capture or replay game code twice.
  java.lang.reflect.Field captureField=GothicCharacters.class.getDeclaredField("capture");
  captureField.setAccessible(true);
  @SuppressWarnings("unchecked")
  ThreadLocal<ArrayList<GothicCharacters.Part>> capture=
      (ThreadLocal<ArrayList<GothicCharacters.Part>>)captureField.get(null);
  ArrayList<GothicCharacters.Part> queued=new ArrayList<>();
  RecordingGraphics tracking=new RecordingGraphics(Image.createImage(40,40));
  capture.set(queued);
  try{
   GothicCharacters.part(tracking,artwork,0,0,2,2,0,2,3,20,entity);
   check(queued.size()==1&&tracking.directCalls==0,"supported hero parts stay buffered");
   GothicCharacters.part(tracking,artwork,0,0,2,2,1,3,4,20,entity);
   check(queued.size()==1&&queued.get(0)==null,"unsupported part switches capture to legacy mode");
   check(tracking.directCalls==2,"flush previous layers and draw unsupported part once");
   GothicCharacters.part(tracking,artwork,0,0,2,2,0,4,5,20,entity);
   check(tracking.directCalls==3,"later layers stay in legacy mode");
   GothicCharacters.render(entity,tracking,queued);
   check(tracking.directCalls==3,"fallback must not composite duplicate frame");
  }finally{capture.remove();}
  System.out.println("Whole hero: alpha/mirror equivalence, translated cache, 3x geometry and safe legacy fall-through passed");
 }
}
