"""Restore the alpha channel on assets/sast-icon.png.

The shipped icon is RGB with no alpha and 88.5% pure-black pixels, including all
four corners: it is a transparent-background mark that was flattened onto black.
Alpha is recovered from per-pixel brightness so the black field drops out while
the mark itself keeps its original colours. The 3x ramp makes anti-aliased edge
pixels mostly opaque instead of leaving a dark fringe.
"""

from PIL import Image

SRC = "assets/sast-icon.png"
DST = "assets/sast-icon-transparent.png"

src = Image.open(SRC).convert("RGB")
out = Image.new("RGBA", src.size)

src_px = src.load()
out_px = out.load()
w, h = src.size

for y in range(h):
    for x in range(w):
        r, g, b = src_px[x, y]
        alpha = min(255, max(r, g, b) * 3)
        out_px[x, y] = (r, g, b, alpha)

out.save(DST)
print(f"wrote {DST}  {out.size[0]}x{out.size[1]}  mode={out.mode}")
