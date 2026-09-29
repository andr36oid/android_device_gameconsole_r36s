#!/usr/bin/env python3
"""Turn an extracted ext4 image into a PAX tar on stdout, for mkfs.erofs --tar=f.

Usage: ext4tar.py <rdump dir> <debugfs ea_list output>

<rdump dir> is the output of `debugfs -R "rdump / dir" image` run as root, so owner,
group and mode are already right. Extended attributes are not restored by rdump, and
this host can't set security.* on files anyway, so they are read from the ea_list
dump and put into the tar as SCHILY.xattr.* records. That keeps the SELinux labels
and file capabilities byte for byte (file_contexts alone gives different labels for
the flattened APEX files).
"""
import os
import re
import sys
import tarfile

root, eafile = sys.argv[1], sys.argv[2]

xattrs = {}
cur = None
for line in open(eafile, 'rb'):
    m = re.match(rb'debugfs: ea_list (.*)', line)
    if m:
        cur = m.group(1).rstrip(b'\n').decode()
        xattrs[cur] = {}
        continue
    m = re.match(rb'\s+(\S+) \((\d+)\) = (.*)', line)
    if not (m and cur):
        continue
    name, size, val = m.group(1).decode(), int(m.group(2)), m.group(3).rstrip(b'\n')
    if val.startswith(b'"'):
        # "text\000": printable string with octal escapes
        raw = val.rstrip()[1:-1]
        out = bytearray()
        i = 0
        while i < len(raw):
            if raw[i:i + 1] == b'\\' and raw[i + 1:i + 4].isdigit():
                out.append(int(raw[i + 1:i + 4], 8))
                i += 4
            elif raw[i:i + 1] == b'\\':
                out.append(raw[i + 1])
                i += 2
            else:
                out.append(raw[i])
                i += 1
        data = bytes(out)
    else:
        data = bytes.fromhex(val.decode().replace(' ', ''))
    if len(data) != size:
        sys.exit('xattr size mismatch for %s %s: %d != %d' % (cur, name, len(data), size))
    xattrs[cur][name] = data

tar = tarfile.open(fileobj=sys.stdout.buffer, mode='w|', format=tarfile.PAX_FORMAT)
missing = 0


def add(path):
    global missing
    rel = os.path.relpath(path, root)
    fspath = '/' if rel == '.' else '/' + rel
    ti = tar.gettarinfo(path, arcname=rel if rel != '.' else '.')
    ti.mtime = 0
    ti.uname = ti.gname = ''
    x = xattrs.get(fspath)
    if x is None:
        missing += 1
        x = {}
    ti.pax_headers = {'SCHILY.xattr.' + k: v.decode('utf-8', 'surrogateescape')
                      for k, v in x.items()}
    if ti.isreg():
        with open(path, 'rb') as f:
            tar.addfile(ti, f)
    else:
        tar.addfile(ti)


for dirpath, dirnames, filenames in os.walk(root):
    dirnames.sort()
    add(dirpath)
    for n in sorted(filenames):
        add(os.path.join(dirpath, n))
    # symlinks to directories show up in dirnames but are not walked
    for n in dirnames:
        p = os.path.join(dirpath, n)
        if os.path.islink(p):
            add(p)
    dirnames[:] = [n for n in dirnames if not os.path.islink(os.path.join(dirpath, n))]
tar.close()
if missing:
    sys.exit('%d paths had no ea_list entry' % missing)
