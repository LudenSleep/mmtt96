"""Amiga Imploder "IMP!" decoder (spec R1.1-003; ambiguities settled against the retail ROM in T3.c1).

decode(rom, start, end) -> (output bytes, bytes consumed); raises ValueError(reason) on any inconsistency.
Blob layout (BE): +0 "IMP!", +4 rawSize, +8 endOffset; trailer at endOffset: +0..+11 the packed stream's own first
12 bytes (overwritten by the header; stored as longs in reverse order), +12 initial literal run, +16 byte (bit7 clear
-> stream starts at endOffset-1), +17 partial bit buffer (lowest set bit = marker), +18 distance bases [2][4] BE16,
+34 distance bit widths [3][4], +0x2E checksum = 7 + sum of BE16 words over 0..endOffset+0x2D. Size endOffset+0x32.
Decoding runs backwards: output rawSize -> 0, input endOffset -> 0 (exactly 0 at the end), bits MSB first.
"""
MAGIC = b"IMP!"
TRAILER = 0x32
LIT_BITS = ((1, 1, 1, 1), (2, 3, 3, 4), (4, 5, 7, 14))
LIT_BASE4 = (6, 10, 10, 18)


def _be16(b, o):
    return (b[o] << 8) | b[o + 1]


def _be32(b, o):
    return int.from_bytes(b[o:o + 4], "big")


def declared_size(rom, start):
    """rawSize (BE32 at +4) of the IMP! blob at start."""
    return _be32(rom, start + 4)


def decode(rom, start, end):
    blob = rom[start:end]
    if len(blob) < 12 + TRAILER or blob[:4] != MAGIC:
        raise ValueError("bad magic")
    raw, eo = _be32(blob, 4), _be32(blob, 8)
    if raw == 0:
        raise ValueError("rawSize 0")
    if eo & 1 or eo < 0xC:
        raise ValueError(f"bad endOffset {eo:#x}")
    if eo + TRAILER != len(blob):
        raise ValueError(f"size mismatch: endOffset+0x32 = {eo + TRAILER:#x}, region {len(blob):#x}")
    ck = 7
    for o in range(0, eo + 0x2E, 2):
        ck += _be16(blob, o)
    if ck & 0xFFFFFFFF != _be32(blob, eo + 0x2E):
        raise ValueError("checksum mismatch")
    t = eo
    inp = bytearray(blob[:eo])
    inp[0:12] = blob[t + 8:t + 12] + blob[t + 4:t + 8] + blob[t:t + 4]
    pos = eo if blob[t + 16] & 0x80 else eo - 1
    bb = bn = 0
    h = blob[t + 17]
    for i in range(8):
        if h & (1 << i):
            bb, bn = h >> (i + 1), 7 - i
            break
    st = [pos, bb, bn]

    def rbyte():
        st[0] -= 1
        if st[0] < 0:
            raise ValueError("input underrun")
        return inp[st[0]]

    def rbit():
        if st[2] == 0:
            st[1], st[2] = rbyte(), 8
        st[2] -= 1
        return (st[1] >> st[2]) & 1

    def rbits(n):
        v = 0
        for _ in range(n):
            v = (v << 1) | rbit()
        return v

    lit = _be32(blob, t + 12)
    dv = [[_be16(blob, t + 18 + 2 * (4 * a + c)) for c in range(4)] for a in range(2)]
    db = [[blob[t + 34 + 4 * a + c] for c in range(4)] for a in range(3)]
    out = bytearray(raw)
    o = raw
    while True:
        for _ in range(lit):
            if o == 0:
                break
            o -= 1
            out[o] = rbyte()
        if o == 0:
            break
        i0 = 0
        while i0 < 5 and rbit():
            i0 += 1
        sel = min(i0, 3)
        cnt = i0 + 2
        if cnt == 6:
            cnt += rbits(3)
        elif cnt == 7:
            cnt = rbyte()
            if cnt == 0:
                raise ValueError("zero match count")
        i1 = 1 + rbit() if rbit() else 0
        base = LIT_BASE4[sel] if i1 == 2 else 2 * i1
        lit = base + rbits(LIT_BITS[i1][sel])
        i2 = 1 + rbit() if rbit() else 0
        dist = 1 + (dv[i2 - 1][sel] if i2 else 0) + rbits(db[i2][sel])
        if cnt > o:
            raise ValueError("match overfills output")
        if o - 1 + dist >= raw:
            raise ValueError("distance out of range")
        for _ in range(cnt):
            o -= 1
            out[o] = out[o + dist]
    if st[0] != 0:
        raise ValueError(f"input not fully consumed ({st[0]:#x} left)")
    return bytes(out), eo + TRAILER
