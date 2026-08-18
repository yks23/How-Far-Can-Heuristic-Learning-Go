"""Measure title baseline spacing by finding rows of dark ink in a render.

pdftotext -bbox crashes on this file, so the leading is measured from pixels
instead: rasterise page 1, look at the title band, and report the pitch between
successive bands of dark ink. Run at a known DPI so px can be converted to pt.
"""

import subprocess
import sys

from PIL import Image

DPI = 300
PNG = "build/_measure"

subprocess.run(
    ["pdftoppm", "-png", "-r", str(DPI), "-f", "1", "-l", "1",
     "-singlefile", "build/main.pdf", PNG],
    check=True,
)

im = Image.open(f"{PNG}.png").convert("L")
w, h = im.size
px = im.load()

# Dark ink only: the title is near-black, the tinted panel is light.
rows = []
for y in range(h):
    dark = sum(1 for x in range(0, w, 2) if px[x, y] < 100)
    rows.append(dark)

bands = []
in_band = False
for y, n in enumerate(rows):
    if n > 3 and not in_band:
        in_band, start = True, y
    elif n <= 3 and in_band:
        in_band = False
        if y - start > 4:  # ignore specks
            bands.append((start, y))

pt = 72.0 / DPI
print(f"page {w}x{h}px @ {DPI}dpi     {len(bands)} ink bands\n")
prev = None
for i, (a, b) in enumerate(bands[:8]):
    top = a * pt
    delta = "" if prev is None else f"   pitch={(a - prev) * pt:6.2f}pt"
    print(f"band {i}:  top={top:7.2f}pt  height={(b - a) * pt:5.2f}pt{delta}")
    prev = a

pitches = [(bands[i + 1][0] - bands[i][0]) * pt for i in range(min(3, len(bands) - 1))]
if pitches:
    avg = sum(pitches) / len(pitches)
    print(f"\ntitle line pitch (first {len(pitches)} gaps): "
          + ", ".join(f"{p:.2f}" for p in pitches)
          + f"   mean={avg:.2f}pt")
