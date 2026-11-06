"""Route only verified HG menu fill callsites to the native Android skin.
No instructions are inserted: branch offsets, frames and exception tables stay intact.
Usage: python tools/patch_menu_skin.py input.jar output.jar
"""
import io,struct,sys,zipfile
from pathlib import Path

TARGETS = {
 ('b','(Ljavax/microedition/lcdui/Graphics;)V'):{31:'background',431:'panel'},
 ('a','(Ljavax/microedition/lcdui/Graphics;Ljava/lang/String;IZI)I'):{96:'selection'},
 ('a','(Ljavax/microedition/lcdui/Graphics;Ljava/lang/String;IIZ)I'):{126:'selection',262:'panel'},
 ('a','(Ljavax/microedition/lcdui/Graphics;Ljava/lang/String;ZII)I'):{547:'selection',707:'panel'},
 ('a','(Ljavax/microedition/lcdui/Graphics;Ljava/lang/String;IZ)I'):{58:'selection'},
}

def patch(b):
    b=bytearray(b);p=8
    def u2(p):return int.from_bytes(b[p:p+2],'big')
    n=u2(p);p+=2;cp=[None]*n;i=1
    while i<n:
        t=b[p];p+=1
        if t==1:
            size=u2(p);p+=2;cp[i]=bytes(b[p:p+size]).decode('utf8','replace');p+=size
        elif t in (3,4):p+=4
        elif t in (7,8,16):cp[i]=(t,u2(p));p+=2
        elif t in (9,10,11,12,18):cp[i]=(t,u2(p),u2(p+2));p+=4
        elif t in (5,6):p+=8;i+=1
        else:raise ValueError(('constant tag',t))
        i+=1
    cp_end=p;extra=bytearray();count=n
    def add(data):
        nonlocal count
        idx=count;count+=1;extra.extend(data);return idx
    def utf(s):
        data=s.encode();return add(b'\x01'+struct.pack('>H',len(data))+data)
    owner=add(b'\x07'+struct.pack('>H',utf('org/gothic3/ui/GothicMenuSkin')))
    desc=utf('(Ljavax/microedition/lcdui/Graphics;IIII)V');refs={}
    for method in ('background','panel','selection'):
        nt=add(b'\x0c'+struct.pack('>HH',utf(method),desc))
        refs[method]=add(b'\x0a'+struct.pack('>HH',owner,nt))
    p+=6;interfaces=u2(p);p+=2+interfaces*2;seen=[]
    for section in range(2):
        total=u2(p);p+=2
        for _ in range(total):
            _,name,descriptor,attrs=struct.unpack_from('>HHHH',b,p);p+=8
            key=(cp[name],cp[descriptor])
            for _ in range(attrs):
                an=u2(p);size=int.from_bytes(b[p+2:p+6],'big');p+=6
                if section==1 and cp[an]=='Code' and key in TARGETS:
                    for offset,hook in TARGETS[key].items():
                        pos=p+8+offset
                        assert b[pos]==184,('not invokestatic',key,offset)
                        ref=cp[u2(pos+1)];assert ref[0]==10
                        assert cp[cp[ref[1]][1]]=='Hd',('wrong owner',key,offset)
                        nt=cp[ref[2]];assert cp[nt[1]]=='fillRect'
                        assert cp[nt[2]]=='(Ljavax/microedition/lcdui/Graphics;IIII)V'
                        b[pos+1:pos+3]=struct.pack('>H',refs[hook]);seen.append((key,offset))
                p+=size
    assert len(seen)==8,seen
    b[8:10]=struct.pack('>H',count)
    return bytes(b[:cp_end]+extra+b[cp_end:])

if __name__=='__main__':
    src,dst=map(Path,sys.argv[1:]);assert src.resolve()!=dst.resolve()
    with zipfile.ZipFile(src) as z,zipfile.ZipFile(dst,'w',zipfile.ZIP_DEFLATED) as out:
        for info in z.infolist():
            data=z.read(info.filename)
            out.writestr(info,patch(data) if info.filename=='HG.class' else data)
    print('Patched 8 verified menu fill calls in HG.class')
