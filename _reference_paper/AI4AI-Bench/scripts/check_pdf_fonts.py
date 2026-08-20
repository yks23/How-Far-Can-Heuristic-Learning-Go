#!/usr/bin/env python3
"""Report embedded /BaseFont names in a PDF, decompressing object streams."""
import re, sys, zlib

data = open(sys.argv[1], 'rb').read()
blobs = [data]
for m in re.finditer(rb'stream\r?\n', data):
    start = m.end()
    end = data.find(b'endstream', start)
    if end < 0:
        continue
    try:
        blobs.append(zlib.decompress(data[start:end]))
    except zlib.error:
        pass

fonts = set()
for b in blobs:
    for f in re.findall(rb'/BaseFont\s*/([-+#\w]+)', b):
        fonts.add(f.decode('latin-1'))
print(f"blobs scanned: {len(blobs)}")
for f in sorted(fonts):
    print("  ", f)
print("CJK font present:", any('Droid' in f for f in fonts))
