#!/usr/bin/env python3
"""Report the vertical rhythm of the title box off a rasterized page 1.

Finds rows containing dark ink, groups consecutive ones into bands (text lines),
and prints each band's height plus the whitespace gap to the next one. Used to
check that the gaps in company_light.cls come out as specified, since
`pdftotext -bbox` segfaults on this file.

Usage: python3 scripts/measure_titlebox.py build/main.pdf
"""
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image

DPI = 300
PT_PER_INCH = 72.0
CM_PER_INCH = 2.54


def rasterize(pdf: Path, outdir: Path) -> Image.Image:
    stem = outdir / "page"
    subprocess.run(
        ["pdftoppm", "-png", "-r", str(DPI), "-f", "1", "-l", "1", str(pdf), str(stem)],
        check=True,
    )
    return Image.open(next(outdir.glob("page*.png"))).convert("L")


def ink_bands(im: Image.Image, threshold: int = 100, min_px: int = 2):
    """Rows whose darkest pixel is below `threshold`, grouped into runs."""
    px = im.load()
    inked = []
    for y in range(im.height):
        for x in range(im.width):
            if px[x, y] < threshold:
                inked.append(y)
                break

    bands, start, prev = [], None, None
    for y in inked:
        if start is None:
            start, prev = y, y
        elif y - prev > min_px:
            bands.append((start, prev))
            start, prev = y, y
        else:
            prev = y
    if start is not None:
        bands.append((start, prev))
    return bands


def main() -> int:
    pdf = Path(sys.argv[1] if len(sys.argv) > 1 else "build/main.pdf")
    if not pdf.exists():
        print(f"no such file: {pdf}", file=sys.stderr)
        return 1

    with tempfile.TemporaryDirectory() as td:
        im = rasterize(pdf, Path(td))
        bands = ink_bands(im)

    to_pt = PT_PER_INCH / DPI
    print(f"{pdf} at {DPI} dpi, {len(bands)} ink bands, 1 px = {to_pt:.3f} pt\n")
    print(f"{'#':>3} {'top..bot (px)':>16} {'height':>9} {'gap below':>11} {'gap':>8}")
    print("-" * 54)
    for i, (top, bot) in enumerate(bands):
        height = (bot - top + 1) * to_pt
        if i + 1 < len(bands):
            gap_pt = (bands[i + 1][0] - bot - 1) * to_pt
            gap = f"{gap_pt:8.2f}pt"
            gap_cm = f"{gap_pt / PT_PER_INCH * CM_PER_INCH:7.2f}cm"
        else:
            gap, gap_cm = " " * 10, " " * 9
        print(f"{i:>3} {top:>7}..{bot:<7} {height:7.2f}pt {gap} {gap_cm}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
