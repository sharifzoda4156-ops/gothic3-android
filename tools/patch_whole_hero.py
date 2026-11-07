"""Experimental rendering hooks. Guarded against a different input or repeated patch."""
import hashlib, struct, zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BASE=''

def patch(data, owner, targets, calls=False):
    u2=lambda p:struct.unpack_from('>H',data,p)[0]
    p=10;cp=[None]*u2(8);i=1
    while i<len(cp):
        start=p;tag=data[p];p+=1
        if tag==1:
            n=u2(p);p+=2;value=data[p:p+n].decode('utf8','replace');p+=n
        elif tag in (7,8,16,19,20):value=u2(p);p+=2
        elif tag in (3,4,9,10,11,12,17,18):value=(u2(p),u2(p+2));p+=4
        elif tag in (5,6):value=None;p+=8
        elif tag==15:value=None;p+=3
        else:raise ValueError(tag)
        cp[i]=(tag,value,start,p)
        if tag in (5,6):i+=1
        i+=1
    end=p;extra=bytearray();count=len(cp)
    def add(blob):
        nonlocal count
        n=count;count+=1;extra.extend(blob);return n
    def utf(s):
        v=s.encode();return add(b'\1'+struct.pack('>H',len(v))+v)
    def clazz(s):return add(b'\7'+struct.pack('>H',utf(s)))
    if any(x and x[0]==1 and x[1]==owner for x in cp):raise ValueError('Already patched')
    klass=clazz(owner);replacements=[];matched=[]
    def ref(name,desc):
        nt=add(b'\x0c'+struct.pack('>HH',utf(name),utf(desc)))
        return add(b'\x0a'+struct.pack('>HH',klass,nt))
    if calls:
        for entry in cp:
            if not entry or entry[0]!=10:continue
            cl,nt=entry[1];cn=cp[cp[cl][1]][1];mn,ds=cp[nt][1];name,desc=cp[mn][1],cp[ds][1]
            if cn=='c' and (name,desc) in targets:
                newname=targets[name,desc];nt=add(b'\x0c'+struct.pack('>HH',utf(newname),utf(desc)))
                replacements.append((entry[2],entry[3],b'\x0a'+struct.pack('>HH',klass,nt)));matched.append(name)
    else:
        p+=6;p+=2+u2(p)*2
        for section in range(2):
            total=u2(p);p+=2
            for _ in range(total):
                flags,mn,ds,attrs=struct.unpack_from('>4H',data,p);p+=8
                name,desc=cp[mn][1],cp[ds][1]
                for _ in range(attrs):
                    start=p;an=u2(p);n=struct.unpack_from('>I',data,p+2)[0];p+=6
                    if section==1 and cp[an][1]=='Code' and (name,desc) in targets:
                        newname=targets[name,desc];args=desc[1:desc.index(')')];loads=bytearray();local=0;j=0
                        while j<len(args):
                            t=args[j];reference=t in '[L'
                            if t=='[':
                                while args[j]=='[':j+=1
                                t=args[j]
                            if t=='L':j=args.index(';',j)
                            loads.extend(bytes((0x19 if reference else 0x15,local)));local+=1;j+=1
                        code=loads+b'\xb8'+struct.pack('>H',ref(newname,desc))+bytes((0xb1 if desc.endswith('V') else 0xb0 if desc.split(')')[1][0] in '[L' else 0xac,))
                        body=struct.pack('>HHI',local,local,len(code))+code+b'\0\0\0\0'
                        replacements.append((start,p+n,struct.pack('>HI',an,len(body))+body));matched.append(name)
                    p+=n
    if calls:
        q=end+6; q+=2+u2(q)*2
        resized=0
        for section in range(2):
            total=u2(q);q+=2
            for _ in range(total):
                flags,mn,ds,attrs=struct.unpack_from('>4H',data,q);q+=8
                for _ in range(attrs):
                    an=u2(q);n=struct.unpack_from('>I',data,q+2)[0];start=q;q+=6
                    if section==1 and cp[mn][1]=='sizeChanged' and cp[ds][1]=='(II)V' and cp[an][1]=='Code':
                        length=struct.unpack_from('>I',data,q+4)[0];code=data[q+8:q+8+length]
                        if code.count(b'\x05\x6c')!=2:raise ValueError('Unexpected sizeChanged divisions')
                        replacements.append((q+8,q+8+length,code.replace(b'\x05\x6c',b'\x06\x6c')));resized+=1
                    q+=n
        if resized!=1:raise ValueError('Missing sizeChanged')
    if len(matched)!=len(targets):raise ValueError(('Hook mismatch',matched,list(targets)))
    for start,stop,value in sorted(replacements,reverse=True):data=data[:start]+value+data[stop:]
    # Changes inside the constant pool keep their lengths; method edits follow it.
    return data[:8]+struct.pack('>H',count)+data[10:end]+extra+data[end:]

G='Ljavax/microedition/lcdui/Graphics;';I='Ljavax/microedition/lcdui/Image;';C='Ljavax/microedition/lcdui/Canvas;'
HD={('fillRect',f'({G}IIII)V'):'fill',('drawRect',f'({G}IIII)V'):'rect',('drawLine',f'({G}IIII)V'):'line',('setClip',f'({G}IIII)V'):'clip',('drawRegion',f'({G}{I}IIIIIIII)V'):'region',('drawImage',f'({G}{I}III)V'):'image',('drawString',f'({G}Ljava/lang/String;III)V'):'text',('iw',f'({I})I'):'width',('ih',f'({I})I'):'height',('cm',f'(II){I}'):'buffer',('cw',f'({C})I'):'canvasWidth',('ch',f'({C})I'):'canvasHeight'}

def patch_jar(path):
    with zipfile.ZipFile(path) as z:items=[(x,z.read(x.filename)) for x in z.infolist()]
    out=[]
    for info,data in items:
        if info.filename=='Hd.class':data=patch(data,'GothicResolution',HD)
        elif info.filename=='HdVar.class':data=patch(data,'GothicCharacters',{('dp',f'({G}{I}IIIIIIII[I)V'):'part'})
        elif info.filename=='c.class':data=patch(data,'GothicCharacters',{('d',f'([I{G})V'):'draw'},True)
        out.append((info,data))
    with zipfile.ZipFile(path,'w') as z:
        for info,data in out:z.writestr(info,data)
if __name__=='__main__':patch_jar(ROOT/'app/libs/gothic3-classes.jar')
