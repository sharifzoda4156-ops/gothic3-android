"""Replace three loader method bodies; preserve all other game bytecode.

python tools/patch_hd_assets.py input.jar output.jar
The input must be the pre-patch JAR; applying twice is rejected.
"""
import struct
import sys
import zipfile
from pathlib import Path

TARGETS = {
    'Hd.class': ('ci', '(Ljava/lang/String;)Ljavax/microedition/lcdui/Image;', 'named', 1),
    'HeroHD.class': ('cb', '([BII)Ljavax/microedition/lcdui/Image;', 'bytes', 3),
    'HdVar.class': ('load', '(Ljava/lang/String;II)Ljavax/microedition/lcdui/Image;', 'sized', 3),
}


def patch(data, target):
    name, descriptor, hook, arguments = target
    u2 = lambda p: struct.unpack_from('>H', data, p)[0]
    p = 10
    count = u2(8)
    cp = [None] * count
    i = 1
    while i < count:
        tag = data[p]
        p += 1
        if tag == 1:
            length = u2(p)
            p += 2
            cp[i] = data[p:p + length].decode('utf8', 'replace')
            p += length
        elif tag in (7, 8, 16, 19, 20):
            cp[i] = (tag, u2(p))
            p += 2
        elif tag in (3, 4, 9, 10, 11, 12, 17, 18):
            p += 4
        elif tag in (5, 6):
            p += 8
            i += 1
        elif tag == 15:
            p += 3
        else:
            raise ValueError(('constant tag', tag))
        i += 1
    if 'GothicAssets' in cp:
        raise ValueError('Loader already patched')
    cp_end = p
    additions = bytearray()

    def add(blob):
        nonlocal count
        index = count
        count += 1
        additions.extend(blob)
        return index

    def utf(value):
        value = value.encode()
        return add(b'\x01' + struct.pack('>H', len(value)) + value)

    owner = add(b'\x07' + struct.pack('>H', utf('GothicAssets')))
    nt = add(b'\x0c' + struct.pack('>HH', utf(hook), utf(descriptor)))
    ref = add(b'\x0a' + struct.pack('>HH', owner, nt))
    code = (b'\x2a' if arguments == 1 else b'\x2a\x1b\x1c') + b'\xb8' + struct.pack('>H', ref) + b'\xb0'
    body = struct.pack('>HHI', arguments, arguments, len(code)) + code + b'\x00\x00\x00\x00'
    p += 6
    interfaces = u2(p)
    p += 2 + interfaces * 2
    replacements = []
    matched = 0
    for section in range(2):
        total = u2(p)
        p += 2
        for _ in range(total):
            _, method_name, desc, attributes = struct.unpack_from('>HHHH', data, p)
            p += 8
            for _ in range(attributes):
                start = p
                attr = u2(p)
                size = struct.unpack_from('>I', data, p + 2)[0]
                p += 6
                if section == 1 and cp[attr] == 'Code':
                    if cp[method_name] == name and cp[desc] == descriptor:
                        replacement_body = body
                        matched += 1
                    else:
                        # Legacy loader patches left debug PCs past the end of their
                        # shortened methods. Drop only non-executable debug tables.
                        end_code = p + 8 + struct.unpack_from('>I', data, p + 4)[0]
                        nested = end_code + 2 + u2(end_code) * 8
                        q = nested + 2
                        keep = []
                        for _ in range(u2(nested)):
                            nested_start = q
                            nested_name = cp[u2(q)]
                            nested_size = struct.unpack_from('>I', data, q + 2)[0]
                            q += 6 + nested_size
                            if nested_name not in ('LineNumberTable', 'LocalVariableTable',
                                                   'LocalVariableTypeTable'):
                                keep.append(data[nested_start:q])
                        replacement_body = data[p:nested] + struct.pack('>H', len(keep)) + b''.join(keep)
                    replacements.append((start, p + size,
                                         struct.pack('>HI', attr, len(replacement_body)) + replacement_body))
                p += size
    # The target descriptor must exist, even if a future input changes the class.
    if matched != 1:
        raise ValueError(('Expected one hook', name))
    tail = bytearray(data[cp_end:])
    for start, end, replacement in reversed(replacements):
        tail[start - cp_end:end - cp_end] = replacement
    return data[:8] + struct.pack('>H', count) + data[10:cp_end] + additions + tail


def patch_jar(source, destination):
    if source.resolve() == destination.resolve():
        raise ValueError('Use a separate output JAR')
    with zipfile.ZipFile(source) as src, zipfile.ZipFile(destination, 'w') as out:
        if not TARGETS.keys() <= set(src.namelist()):
            raise ValueError('Missing loader classes')
        for info in src.infolist():
            data = src.read(info.filename)
            if info.filename in TARGETS:
                data = patch(data, TARGETS[info.filename])
            out.writestr(info, data)


if __name__ == '__main__':
    patch_jar(*map(Path, sys.argv[1:]))
    print('Patched Hd.ci, HeroHD.cb and HdVar.load')
