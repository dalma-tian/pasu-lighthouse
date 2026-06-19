"""Generate static/lighthouse-watermark.png (transparent background) from
static/lighthouse-hero.png. Uses rembg when available; otherwise falls back to
a PIL flood-fill color-key of the cream background."""
import os

SRC = os.path.join("static", "lighthouse-hero.png")
DST = os.path.join("static", "lighthouse-watermark.png")


def via_rembg():
    from rembg import remove
    from PIL import Image
    img = Image.open(SRC).convert("RGBA")
    out = remove(img)
    out.save(DST)
    print("watermark written via rembg ->", DST)


def via_pil():
    from PIL import Image
    from collections import deque
    img = Image.open(SRC).convert("RGBA")
    px = img.load()
    w, h = img.size
    # Sample the four corners to learn the background color.
    corners = [px[0, 0], px[w - 1, 0], px[0, h - 1], px[w - 1, h - 1]]
    br = sum(c[0] for c in corners) // 4
    bg_ = sum(c[1] for c in corners) // 4
    bb = sum(c[2] for c in corners) // 4
    tol = 38

    def is_bg(p):
        return abs(p[0] - br) <= tol and abs(p[1] - bg_) <= tol and abs(p[2] - bb) <= tol

    # Flood fill from the border so interior cream-ish pixels stay opaque.
    visited = bytearray(w * h)
    q = deque()
    for x in range(w):
        for y in (0, h - 1):
            q.append((x, y))
    for y in range(h):
        for x in (0, w - 1):
            q.append((x, y))
    while q:
        x, y = q.popleft()
        idx = y * w + x
        if visited[idx]:
            continue
        visited[idx] = 1
        p = px[x, y]
        if not is_bg(p):
            continue
        px[x, y] = (p[0], p[1], p[2], 0)
        if x > 0:
            q.append((x - 1, y))
        if x < w - 1:
            q.append((x + 1, y))
        if y > 0:
            q.append((x, y - 1))
        if y < h - 1:
            q.append((x, y + 1))
    img.save(DST)
    print("watermark written via PIL flood-fill ->", DST)


if __name__ == "__main__":
    try:
        via_rembg()
    except Exception as e:
        print("rembg unavailable (%s); falling back to PIL" % e)
        via_pil()
