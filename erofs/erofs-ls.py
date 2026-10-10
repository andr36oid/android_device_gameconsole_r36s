#!/usr/bin/env python3
"""List every path of an EROFS image with mode, uid, gid, SELinux label and file
capabilities (hex), to compare against the ext4 image it was made from.
Usage: erofs-ls.py image > list.txt. Only uncompressed directories are read (mkfs.erofs
never compresses them); file data is not read."""
import struct, sys

img = open(sys.argv[1], 'rb').read()
sb = 1024
magic, = struct.unpack_from('<I', img, sb)
assert magic == 0xE0F5E1E2, hex(magic)
blkbits = img[sb + 12]; bs = 1 << blkbits
root_nid, = struct.unpack_from('<H', img, sb + 14)
meta, xat = struct.unpack_from('<II', img, sb + 40)
incompat, = struct.unpack_from('<I', img, sb + 80)
PREFIX = {1: 'user.', 2: 'system.posix_acl_access', 3: 'system.posix_acl_default',
          4: 'trusted.', 6: 'security.'}


def entry(off):
    nl, idx, vs = struct.unpack_from('<BBH', img, off)
    name = PREFIX.get(idx, '?%d.' % idx) + img[off + 4:off + 4 + nl].decode()
    val = img[off + 4 + nl:off + 4 + nl + vs]
    return name, val, (4 + nl + vs + 3) & ~3


def inode(nid):
    off = meta * bs + nid * 32
    fmt, icount, mode = struct.unpack_from('<HHH', img, off)
    ext = fmt & 1; layout = (fmt >> 1) & 7
    if ext:
        size, = struct.unpack_from('<Q', img, off + 8)
        raw, _, uid, gid = struct.unpack_from('<IIII', img, off + 16)
        isz = 64
    else:
        _, size, _, raw, _, uid, gid = struct.unpack_from('<HIIIIHH', img, off + 6)
        isz = 32
    xsz = 0 if icount == 0 else 12 + (icount - 1) * 4
    xattrs = {}
    if xsz:
        p = off + isz
        shared = img[p + 4]
        q = p + 12
        for i in range(shared):
            sid, = struct.unpack_from('<I', img, q); q += 4
            n, v, _ = entry(xat * bs + sid * 4); xattrs[n] = v
        end = p + xsz
        while q < end:
            n, v, l = entry(q); xattrs[n] = v; q += l
    return dict(mode=mode, size=size, raw=raw, uid=uid, gid=gid, layout=layout,
                xattrs=xattrs, inline=off + isz + xsz)


def data(ino):
    size, lay = ino['size'], ino['layout']
    if lay == 0:
        return img[ino['raw'] * bs: ino['raw'] * bs + size]
    if lay == 2:
        full = size // bs * bs
        return img[ino['raw'] * bs: ino['raw'] * bs + full] + img[ino['inline']: ino['inline'] + size - full]
    raise ValueError('compressed dir/symlink layout %d' % lay)


def readdir(ino):
    d = data(ino)
    for b in range(0, len(d), bs):
        blk = d[b:b + bs]
        n = struct.unpack_from('<H', blk, 8)[0] // 12
        ents = [struct.unpack_from('<QHBB', blk, i * 12) for i in range(n)]
        for i, (nid, noff, ft, _) in enumerate(ents):
            nend = ents[i + 1][1] if i + 1 < n else len(blk)
            name = blk[noff:nend].split(b'\0')[0].decode()
            yield name, nid


def walk(nid, path):
    ino = inode(nid)
    lab = ino['xattrs'].get('security.selinux', b'').rstrip(b'\0').decode()
    cap = ino['xattrs'].get('security.capability', b'').hex()
    print('%s %o %d %d %s %s' % (path or '/', ino['mode'], ino['uid'], ino['gid'], lab, cap))
    if ino['mode'] & 0o170000 == 0o040000:
        for name, cnid in readdir(ino):
            if name in ('.', '..'):
                continue
            walk(cnid, path + '/' + name)


print('# incompat=%#x blocksize=%d' % (incompat, bs), file=sys.stderr)
walk(root_nid, '')
