"""Audit the real packaged PNGs and original-byte -> HD routing index.

No image conversion: inspect PNG IHDR and SHA-256 only.
"""
import argparse
import hashlib
import re
import struct
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESOURCES = ROOT / 'app/src/midlet/resources'


def dimensions(data):
    if len(data) < 33 or data[:8] != b'\x89PNG\r\n\x1a\n' or data[12:16] != b'IHDR':
        raise ValueError('Invalid PNG header')
    return struct.unpack_from('>II', data, 16)


def index_for(read, names):
    lines = ['# Original PNG SHA-256\tname\twidth\theight']
    digests = set()
    originals = sorted(n for n in names if '/' not in n and n.endswith('.png'))
    if not originals:
        raise ValueError('No original PNG resources')
    for name in originals:
        original = read(name)
        width, height = dimensions(original)
        hd = 'hd/' + name
        if hd not in names:
            raise ValueError('Missing ' + hd)
        if dimensions(read(hd)) != (width * 2, height * 2):
            raise ValueError('Wrong HD dimensions: ' + hd)
        digest = hashlib.sha256(original).hexdigest()
        if digest in digests:
            raise ValueError('Ambiguous source PNG: ' + name)
        digests.add(digest)
        lines.append(f'{digest}\t/{name}\t{width}\t{height}')
    for name in names:
        variant = re.fullmatch(r'hd/(\d+)_t\d+\.png', name)
        if variant:
            width, height = dimensions(read(variant[1] + '.png'))
            if dimensions(read(name)) != (width * 2, height * 2):
                raise ValueError('Wrong variant dimensions: ' + name)
    return '\n'.join(lines) + '\n'


def audit_apk(path):
    with zipfile.ZipFile(path) as apk:
        names = set(apk.namelist())
        # The standalone flavor stores Java resources directly at the APK root.
        wanted = index_for(apk.read, names)
        if apk.read('hd/source-index.tsv').decode() != wanted:
            raise ValueError('APK index differs from packaged originals')
        for file in (RESOURCES / 'hd').glob('*.png'):
            if apk.read('hd/' + file.name) != file.read_bytes():
                raise ValueError('APK contains stale HD artwork: ' + file.name)
        dex = b''.join(apk.read(n) for n in names if n.endswith('.dex'))
        for marker in (b'LGothicAssets;', b'GothicHD', b'/hd/source-index.tsv'):
            if marker not in dex:
                raise ValueError('Missing resolver in APK dex: ' + repr(marker))
        hooks = set()
        for name in names:
            if name.endswith('.dex'):
                hooks.update(dex_hooks(apk.read(name)))
        expected_hooks = {('LHd;', 'ci'), ('LHeroHD;', 'cb'), ('LHdVar;', 'load')}
        if hooks != expected_hooks:
            raise ValueError('APK loader call graph mismatch: ' + repr(hooks))
        print(f'APK audit passed: {len(wanted.splitlines()) - 1} originals route to HD; '
              'every packaged HD PNG matches the checkout; all three DEX loader hooks verified')


def dex_hooks(data):
    """Check the three actual invoke-static edges in the assembled debug DEX."""
    def u4(offset):
        return struct.unpack_from('<I', data, offset)[0]

    def leb(offset):
        value = shift = 0
        while True:
            byte = data[offset]
            offset += 1
            value |= (byte & 127) << shift
            if byte < 128:
                return value, offset
            shift += 7
            if shift > 28:
                raise ValueError('Invalid DEX ULEB128')

    if not data.startswith(b'dex\n'):
        raise ValueError('Unsupported DEX format')
    strings = []
    for i in range(u4(0x38)):
        _, start = leb(u4(u4(0x3c) + i * 4))
        end = data.index(0, start)
        strings.append(data[start:end].decode('utf8', 'replace'))
    types = [strings[u4(u4(0x44) + i * 4)] for i in range(u4(0x40))]
    methods = []
    for i in range(u4(0x58)):
        owner, _, name = struct.unpack_from('<HHI', data, u4(0x5c) + i * 8)
        methods.append((types[owner], strings[name]))
    wanted = {('LHd;', 'ci'): 'named', ('LHeroHD;', 'cb'): 'bytes',
              ('LHdVar;', 'load'): 'sized'}
    found = set()
    for i in range(u4(0x60)):
        offset = u4(u4(0x64) + i * 32 + 24)
        if not offset:
            continue
        counts = []
        for _ in range(4):
            count, offset = leb(offset)
            counts.append(count)
        for _ in range(counts[0] + counts[1]):
            _, offset = leb(offset)
            _, offset = leb(offset)
        for count in counts[2:]:
            method_index = 0
            for _ in range(count):
                diff, offset = leb(offset)
                method_index += diff
                _, offset = leb(offset)
                code_offset, offset = leb(offset)
                key = methods[method_index]
                if key not in wanted or not code_offset:
                    continue
                size = u4(code_offset + 12)
                words = struct.unpack_from('<' + 'H' * size, data, code_offset + 16)
                target = ('LGothicAssets;', wanted[key])
                for pc in range(len(words) - 2):
                    if words[pc] & 255 in (0x71, 0x77) and methods[words[pc + 1]] == target:
                        found.add(key)
                        break
    return found


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--write-index', action='store_true')
    parser.add_argument('--apk', type=Path)
    args = parser.parse_args()
    if args.apk:
        audit_apk(args.apk)
        return
    names = {str(p.relative_to(RESOURCES)) for p in RESOURCES.rglob('*') if p.is_file()}
    expected = index_for(lambda n: (RESOURCES / n).read_bytes(), names)
    index = RESOURCES / 'hd/source-index.tsv'
    if args.write_index:
        index.write_text(expected)
    elif index.read_text() != expected:
        raise ValueError('Stale HD index; run with --write-index')
    print(f'HD audit passed: {len(expected.splitlines()) - 1} indexed originals')


if __name__ == '__main__':
    main()
