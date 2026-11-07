import java.util.Properties;
import javax.microedition.lcdui.Image;
public class AnimationPackTest {
 static void check(boolean b,String m){if(!b)throw new AssertionError(m);}
 static Properties properties(){Properties p=new Properties();String[] pairs={"sheet=sample.png","set=0","slot=2","layout=0","appearance9=0","appearance10=0","frameWidth=8","frameHeight=12","columns=2","width=4","height=6","pivotX=2","pivotY=6","loop=true","mirror=false","durations=2,3"};for(String s:pairs){int i=s.indexOf('=');p.setProperty("test."+s.substring(0,i),s.substring(i+1));}return p;}
 public static void main(String[] args)throws Exception{
  Properties p=properties();GothicAnimation.Clip clip=GothicAnimation.Clip.read(p,"test");GothicAnimation.Playback player=new GothicAnimation.Playback();
  check(player.frame(clip,5)==0,"start");check(player.frame(clip,5)==0,"pause must not advance");check(player.frame(clip,7)==1,"independent frame duration");check(player.frame(clip,10)==0,"custom loop");
  p.setProperty("test.loop","false");GothicAnimation.Clip attack=GothicAnimation.Clip.read(p,"test");
  check(player.frame(attack,10)==0,"action change resets");check(player.frame(attack,40)==1,"nonloop clamps");check(player.frame(attack,0)==0,"repeated attack restarts");
  p.setProperty("test.width","NaN");try{GothicAnimation.Clip.read(p,"test");throw new AssertionError("NaN accepted");}catch(java.io.IOException expected){}
  p=properties();p.setProperty("test.sheet","../hero.png");try{GothicAnimation.Clip.read(p,"test");throw new AssertionError("path traversal accepted");}catch(java.io.IOException expected){}
  int[] red=new int[16*12];java.util.Arrays.fill(red,0xffff0000);Image atlas=Image.createRGBImage(red,16,12,true),out=Image.createImage(90,90);
  GothicAnimation.paintFrame(out.getGraphics(),clip,atlas,0,10,20);
  int[] pixel=new int[1];out.getRGB(pixel,0,1,24,42,1,1);check(pixel[0]==0xffff0000,"custom dimensions and feet anchor");out.getRGB(pixel,0,1,24,60,1,1);check(pixel[0]==0,"must end at foot position");
  java.lang.reflect.Method load=GothicAnimation.class.getDeclaredMethod("load");load.setAccessible(true);load.invoke(null);
  int selectors=0;java.util.Set<String> sheets=new java.util.HashSet<>();
  for(int set:new int[]{0,3})for(int slot=0;slot<(set==0?12:16);slot++){
   GothicAnimation.Clip active=GothicAnimation.select(set,slot,0,12345,-67890);
   check(active!=null,"installed pack selector "+set+":"+slot);
   Image texture=active.image();check(texture.getWidth()==active.columns*active.frameWidth,"actual texture columns");
   check(active.pivotY==38&&active.height==40,"stable foot anchor");sheets.add(active.sheet);selectors++;
  }
  check(selectors==28&&sheets.size()==16,"full installed core pack coverage");
  check(GothicAnimation.select(1,8,0,0,0)==null,"weapon attacks must retain their actual weapons");
  check(GothicAnimation.select(0,16,0,0,0)==null,"falling keeps genuine old pose");
  System.out.println("Animation packs: timing, pause, action restart, independent dimensions, pivot and unsafe manifest rejection and all 28 installed selectors/16 PNG sheets passed");
 }
}
