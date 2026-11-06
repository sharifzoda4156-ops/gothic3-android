"""Build the atlas consumed by RpgFont; requires Pillow and fontTools.
Run: python tools/build_readable_font.py --jar app/libs/gothic3-classes.jar \
  --font tools/fonts/DejaVuSans-Dialogue.ttf --output app/src/midlet/resources/font/rpg.png
The bytecode is read only to recover the existing advance table, never modified.
"""
import argparse, io, struct, zipfile
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

CHARS = ''.join(map(chr, range(32,127))) + ''.join(map(chr,range(0x410,0x450))) + 'Ёё№—–«»…'

def advances(jar):
    b=zipfile.ZipFile(jar).read('RpgFont.class')
    # Every WIDTHS initializer entry is dup; index constant; width constant; iastore.
    # Decode instructions, rather than matching bytes inside arbitrary attributes.
    p=8; n=int.from_bytes(b[p:p+2],'big'); p+=2; cp=[None]*n; i=1
    def u2(pos): return int.from_bytes(b[pos:pos+2],'big')
    while i<n:
        t=b[p];p+=1
        if t==1:
            l=u2(p);p+=2;cp[i]=b[p:p+l].decode('utf8','replace');p+=l
        elif t in (3,4):p+=4
        elif t in (7,8,16):p+=2
        elif t in (9,10,11,12,18):p+=4
        elif t in (5,6):p+=8;i+=1
        else:raise ValueError(('constant',t))
        i+=1
    p+=6; ni=u2(p);p+=2+2*ni
    code=None
    for section in range(2):
        count=u2(p);p+=2
        for _ in range(count):
            _,name,_,na=struct.unpack_from('>HHHH',b,p);p+=8
            for _ in range(na):
                an=u2(p);length=int.from_bytes(b[p+2:p+6],'big');p+=6
                if section==1 and cp[name]=='<clinit>' and cp[an]=='Code':
                    size=int.from_bytes(b[p+4:p+8],'big');code=b[p+8:p+8+size]
                p+=length
    assert code is not None
    p=code.index(bytes.fromhex('1100a7bc0a'))+5
    widths=[]
    def const():
        nonlocal p
        op=code[p];p+=1
        if 2<=op<=8:return op-3
        if op==16:v=code[p];p+=1;return v
        if op==17:v=int.from_bytes(code[p:p+2],'big');p+=2;return v
        raise ValueError(('opcode',op))
    for index in range(len(CHARS)):
        assert code[p]==89;p+=1
        assert const()==index
        widths.append(const())
        assert code[p]==79;p+=1
    assert all(0<w<=14 for w in widths)
    return widths

def build(font_path,widths):
    scale=4
    font=ImageFont.truetype(str(font_path),18*scale)
    atlas=Image.new('RGBA',(224,242))
    for i,(char,advance) in enumerate(zip(CHARS,widths)):
        if char==' ':continue
        box=font.getbbox(char,anchor='ls')
        mask=Image.new('L',(box[2]-box[0],box[3]-box[1]))
        ImageDraw.Draw(mask).text((-box[0],-box[1]),char,font=font,fill=255,anchor='ls')
        # Leave one transparent pixel before the next character's advance.
        limit=max(1,advance-1)*scale
        if mask.width>limit:mask=mask.resize((limit,mask.height),Image.Resampling.LANCZOS)
        mask=mask.resize((max(1,round(mask.width/scale)),max(1,round(mask.height/scale))),Image.Resampling.LANCZOS)
        y=17+round(box[1]/scale)
        assert y>=0 and y+mask.height<=22,(char,y,mask.height)
        glyph=Image.new('RGBA',mask.size,'white');glyph.putalpha(mask)
        atlas.paste(glyph,((i%16)*14,(i//16)*22+y))
    return atlas

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--jar',required=True);p.add_argument('--font',required=True);p.add_argument('--output',required=True);a=p.parse_args()
    widths=advances(a.jar);atlas=build(a.font,widths)
    Path(a.output).parent.mkdir(parents=True,exist_ok=True);atlas.save(a.output)
    print(f'Built {len(CHARS)} glyphs; 224x242 RGBA; original advances preserved')
