#!/usr/bin/env python3
"""Pair each embedded /FontName with its /ItalicAngle and /StemV, to prove which
font actually carries a synthesized slant/weight (xeCJK AutoFakeBold/AutoFakeSlant)."""
import re, sys, zlib

data = open(sys.argv[1], 'rb').read()
blobs = [data]
for m in re.finditer(rb'stream\r?\n', data):
    s = m.end()
    e = data.find(b'endstream', s)
    if e < 0:
        continue
    try:
        blobs.append(zlib.decompress(data[s:e]))
    except zlib.error:
        pass

want = sys.argv[2] if len(sys.argv) > 2 else ''
rows = {}
for b in blobs:
    for m in re.finditer(rb'/FontName\s*/([-+#\w]+)', b):
        name = m.group(1).decode('latin-1')
        if want and want not in name:
            continue
        lo, hi = max(0, m.start() - 600), m.end() + 600
        win = b[lo:hi]
        ang = re.search(rb'/ItalicAngle\s*(-?[\d.]+)', win)
        stem = re.search(rb'/StemV\s*(-?[\d.]+)', win)
        rows[name] = (ang.group(1).decode() if ang else '?',
                      stem.group(1).decode() if stem else '?')

print(f"{'FontName':34s} {'ItalicAngle':>12s} {'StemV':>7s}")
for n in sorted(rows):
    a, s = rows[n]
    print(f"{n:34s} {a:>12s} {s:>7s}")
angles = {a for a, _ in rows.values()}
print("\ndistinct ItalicAngle:", sorted(angles))
print("distinct StemV:", sorted({s for _, s in rows.values()}, key=lambda x: (x == '?', x)))
