#!/usr/bin/env python3
"""Make the U-Boot panel DTB for one experimental clone DT.

U-Boot reads rg351p-, rg351v- or rg351mp-kernel.dtb (picked by the board's
hardware revision ADC) only to light the panel for the boot logo and the
charge screen. This takes the R36S one (BOOT/uboot-dtb) and copies the
clone's panel settings into it: init and exit sequences, delays, DSI flags,
size, the native timing, the reset GPIO, the LCD enable or LCD power GPIO
(as enable-gpios) and the LDO4 and LDO8 voltages. Nothing else changes.
LDO9 (a 1.1 V or 1.5 V rail on some clones) is not in this DTB at all.

usage: mk-uboot-dtb.py <BOOT/uboot-dtb> <kernel clone .dtb> <output .dtb>
Plain python3, no device-tree tools needed.
"""
import struct
import sys

PANEL = '/dsi@ff450000/panel@0'
REGS = '/i2c@ff180000/pmic@20/regulators/'
FDT_BEGIN_NODE, FDT_END_NODE, FDT_PROP, FDT_NOP, FDT_END = 1, 2, 3, 4, 9


class Node:
    def __init__(self, name):
        self.name = name
        self.props = []  # [name, bytes], kept in order
        self.children = []

    def get(self, name):
        for k, v in self.props:
            if k == name:
                return v
        return None

    def set(self, name, value):
        for p in self.props:
            if p[0] == name:
                p[1] = value
                return
        self.props.append([name, value])

    def delete(self, name):
        self.props = [p for p in self.props if p[0] != name]


def load(path):
    data = open(path, 'rb').read()
    hdr = struct.unpack('>10I', data[:40])
    assert hdr[0] == 0xd00dfeed, path
    off_struct, off_strings, off_rsv, version, last_comp, boot_cpu, sz_str = hdr[2], hdr[3], hdr[4], hdr[5], hdr[6], hdr[7], hdr[8]
    strs = data[off_strings:off_strings + sz_str]
    rsv = []
    p = off_rsv
    while True:
        addr, size = struct.unpack('>QQ', data[p:p + 16])
        p += 16
        if addr == 0 and size == 0:
            break
        rsv.append((addr, size))
    p, stack, root = off_struct, [], None
    while True:
        tok, = struct.unpack('>I', data[p:p + 4])
        p += 4
        if tok == FDT_BEGIN_NODE:
            e = data.index(b'\0', p)
            n = Node(data[p:e].decode())
            p = (e + 4) & ~3
            if stack:
                stack[-1].children.append(n)
            else:
                root = n
            stack.append(n)
        elif tok == FDT_END_NODE:
            stack.pop()
        elif tok == FDT_PROP:
            ln, no = struct.unpack('>II', data[p:p + 8])
            p += 8
            stack[-1].props.append([strs[no:strs.index(b'\0', no)].decode(), data[p:p + ln]])
            p = (p + ln + 3) & ~3
        elif tok == FDT_NOP:
            continue
        elif tok == FDT_END:
            break
    return root, rsv, boot_cpu


def save(path, root, rsv, boot_cpu):
    strtab, stroff = b'', {}

    def soff(name):
        nonlocal strtab
        if name not in stroff:
            stroff[name] = len(strtab)
            strtab += name.encode() + b'\0'
        return stroff[name]

    def pad(b):
        return b + b'\0' * (-len(b) % 4)

    def emit(n):
        out = struct.pack('>I', FDT_BEGIN_NODE) + pad(n.name.encode() + b'\0')
        for k, v in n.props:
            out += struct.pack('>III', FDT_PROP, len(v), soff(k)) + pad(v)
        for c in n.children:
            out += emit(c)
        return out + struct.pack('>I', FDT_END_NODE)

    dt_struct = emit(root) + struct.pack('>I', FDT_END)
    rsvmap = b''.join(struct.pack('>QQ', a, s) for a, s in rsv) + struct.pack('>QQ', 0, 0)
    off_rsv = 40
    off_struct = off_rsv + len(rsvmap)
    off_strings = off_struct + len(dt_struct)
    total = off_strings + len(strtab)
    hdr = struct.pack('>10I', 0xd00dfeed, total, off_struct, off_strings, off_rsv, 17, 16, boot_cpu,
                      len(strtab), len(dt_struct))
    open(path, 'wb').write(hdr + rsvmap + dt_struct + strtab)


def index(root):
    paths, phandles = {}, {}

    def walk(n, path):
        paths[path] = n
        ph = n.get('phandle')
        if ph is not None:
            phandles[struct.unpack('>I', ph)[0]] = path
        for c in n.children:
            walk(c, (path.rstrip('/') + '/' + c.name) if path != '/' else '/' + c.name)

    walk(root, '/')
    return paths, phandles


def u32(v, i=0):
    return struct.unpack('>I', v[4 * i:4 * i + 4])[0]


def main():
    base, kdtb, out = sys.argv[1:4]
    kroot, _, _ = load(kdtb)
    broot, rsv, boot_cpu = load(base)
    kn, kph = index(kroot)
    bn, bph = index(broot)
    bpath2ph = {p: h for h, p in bph.items()}
    kp, bp = kn[PANEL], bn[PANEL]

    for prop in ('prepare-delay-ms', 'reset-delay-ms', 'init-delay-ms', 'enable-delay-ms',
                 'disable-delay-ms', 'unprepare-delay-ms', 'width-mm', 'height-mm', 'dsi,flags',
                 'dsi,lanes', 'dsi,format', 'panel-init-sequence', 'panel-exit-sequence'):
        v = kp.get(prop)
        if v is not None:
            bp.set(prop, v)

    def phandle_in_base(path):
        # a GPIO bank nothing in the base points at has no phandle yet
        if path not in bpath2ph:
            ph = max(bph) + 1
            bn[path].set('phandle', struct.pack('>I', ph))
            bph[ph], bpath2ph[path] = path, ph
        return bpath2ph[path]

    def gpio_for_base(spec):
        return struct.pack('>3I', phandle_in_base(kph[u32(spec, 0)]), u32(spec, 1), u32(spec, 2))

    bp.set('reset-gpios', gpio_for_base(kp.get('reset-gpios')))
    enable = kp.get('enable-gpios')
    if enable is None:
        supply = kn[kph[u32(kp.get('power-supply'))]]
        enable = supply.get('gpio')  # LCD power switched by a GPIO: U-Boot drives it as enable
    if enable is not None:
        bp.set('enable-gpios', gpio_for_base(enable))
    else:
        bp.delete('enable-gpios')

    # LDO8 powers the LCD on most boards; LDO4 is 3.0 V on the EE and Soy boards
    for reg in ('LDO_REG4', 'LDO_REG8'):
        for prop in ('regulator-min-microvolt', 'regulator-max-microvolt'):
            bn[REGS + reg].set(prop, kn[REGS + reg].get(prop))

    kt = kn[kph[u32(kn[PANEL + '/display-timings'].get('native-mode'))]]
    bt = bn[bph[u32(bn[PANEL + '/display-timings'].get('native-mode'))]]
    for prop in ('clock-frequency', 'hactive', 'vactive', 'hfront-porch', 'hsync-len', 'hback-porch',
                 'vfront-porch', 'vsync-len', 'vback-porch', 'hsync-active', 'vsync-active',
                 'de-active', 'pixelclk-active'):
        v = kt.get(prop)
        if v is not None:
            bt.set(prop, v)

    save(out, broot, rsv, boot_cpu)


main()
