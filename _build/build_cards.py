import pymupdf, os, sys, json, re
import numpy as np
import cv2
from PIL import Image

PDF = r"C:\Users\gamao\Downloads\FORMULA CARD (Engr. APJO) - without grid.pdf"
HERE = os.path.dirname(os.path.abspath(__file__))
CARD_DIR = os.path.join(HERE, "..", "assets", "cards")
DPI = 150
OUT_DPI = 200
doc = pymupdf.open(PDF)

HEADER_BOT = 0.085
FOOTER_TOP = 0.945
CATEGORIES = [
    ("geotech", "GEOTECHNICAL ENGINEERING", (55, 128, 13)),
    ("hydraulics", "HYDRAULICS", (13, 68, 128)),
    ("structural", "PRINCIPLES OF STRUCTURAL ANALYSIS AND DESIGN", (255, 192, 0)),
    ("math", "MATH, SURV, AND TRANSPO ENGINEERING", (255, 107, 167)),
]


def page_np(i, dpi=DPI):
    pix = doc[i].get_pixmap(dpi=dpi)
    arr = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
    return np.ascontiguousarray(arr[:, :, :3])


def page_category(i):
    a = page_np(i, 40)
    H = a.shape[0]
    band = a[: int(H * 0.08)]
    mn = band.min(axis=2).astype(np.int16)
    mx = band.max(axis=2).astype(np.int16)
    colored = (mx - mn > 40) & (mn < 250)
    if colored.sum() < 200:
        return None
    mean = band[colored].mean(axis=0)
    best, bd = None, 1e9
    for key, name, c in CATEGORIES:
        d = sum((mean[k] - c[k]) ** 2 for k in range(3))
        if d < bd:
            bd, best = d, key
    return best


def find_boxes(a):
    H, W = a.shape[:2]
    mask = (a.min(axis=2) < 245).astype(np.uint8)
    mask[: int(H * HEADER_BOT), :] = 0
    mask[int(H * FOOTER_TOP):, :] = 0
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8))
    cnts, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    boxes = []
    for c in cnts:
        x, y, w, h = cv2.boundingRect(c)
        ar = cv2.contourArea(c)
        if w < 100 or h < 60 or w * h < 6000:
            continue
        if ar / (w * h) < 0.7:
            continue
        if w > 0.9 * W and h < 90:
            continue
        # ignore borderless highlight pills (text markers, not formula boxes)
        ring = np.concatenate([
            a[y:y + 4, x:x + w].reshape(-1, 3),
            a[y + h - 4:y + h, x:x + w].reshape(-1, 3),
            a[y:y + h, x:x + 4].reshape(-1, 3),
            a[y:y + h, x + w - 4:x + w].reshape(-1, 3),
        ])
        if (ring.min(axis=1) < 200).mean() < 0.15 and h < 110:
            continue
        boxes.append([int(x), int(y), int(x + w), int(y + h)])
    boxes.sort(key=lambda b: -(b[2] - b[0]) * (b[3] - b[1]))
    keep = []
    for b in boxes:
        dup = False
        for k in keep:
            ix = min(b[2], k[2]) - max(b[0], k[0])
            iy = min(b[3], k[3]) - max(b[1], k[1])
            if ix > 0 and iy > 0:
                inter = ix * iy
                ua = (b[2] - b[0]) * (b[3] - b[1]) + (k[2] - k[0]) * (k[3] - k[1]) - inter
                if inter / ua > 0.6:
                    dup = True
                    break
        if not dup:
            keep.append(b)
    return sorted(keep, key=lambda b: (b[0] // 300, b[1]))


def cluster_columns(boxes, W):
    if not boxes:
        return []
    centers = sorted(((b[0] + b[2]) / 2, b) for b in boxes)
    groups = [[centers[0][1]]]
    for cx, b in centers[1:]:
        prev_cx = sum((q[0] + q[2]) / 2 for q in groups[-1]) / len(groups[-1])
        if cx - prev_cx > 0.15 * W:
            groups.append([b])
        else:
            groups[-1].append(b)
    return groups


def runs_of(rows, gap=6):
    if not len(rows):
        return []
    out = []
    s = p = rows[0]
    for r in rows[1:]:
        if r - p > gap:
            out.append((int(s), int(p)))
            s = r
        p = r
    out.append((int(s), int(p)))
    return out


def heading_above(a, box, prev_bottom, W):
    x0, y0, x1, y1 = box
    H = a.shape[0]
    band_top = max(prev_bottom + 3, y0 - 130, int(H * HEADER_BOT))
    bx0, bx1 = max(0, x0 - 150), min(W, x1 + 150)
    if y0 - 2 <= band_top:
        return None
    band = a[band_top:y0 - 2, bx0:bx1]
    ink = (band.min(axis=2) < 240)
    rows = np.nonzero(ink.sum(axis=1))[0]
    if not len(rows):
        return None
    rs = runs_of(rows)
    hs, he = rs[-1]
    if he - hs < 14:
        return None
    # extend upward through tightly spaced lines (multi-line heading)
    lines = [(hs, he)]
    for k in range(len(rs) - 2, -1, -1):
        if lines[0][0] - rs[k][1] < 18 and len(lines) < 3:
            lines.insert(0, rs[k])
        else:
            break
    hs = lines[0][0]
    he = lines[-1][1]
    sub = band[hs:he + 1]
    mn = sub.min(axis=2).astype(np.int16)
    mx = sub.max(axis=2).astype(np.int16)
    colored = ((mx - mn > 45) & (mn < 240)).mean()
    # full-width extent of the heading line, take run overlapping the box
    full = a[band_top + hs:band_top + he + 1, :]
    colink = (full.min(axis=2) < 240).sum(axis=0) > 0
    idx = np.nonzero(colink)[0]
    ext = (x0, x1)
    if len(idx):
        runs = runs_of(idx, gap=32)
        pick = None
        for r in runs:
            if r[1] >= x0 and r[0] <= x1:
                pick = r if pick is None else (min(pick[0], r[0]), max(pick[1], r[1]))
        if pick is None:
            pick = min(runs, key=lambda r: min(abs(r[0] - x0), abs(r[1] - x1)))
        ext = (int(pick[0]), int(pick[1]))
    return band_top + hs, band_top + he, colored, ext


def build_page(i):
    a = page_np(i)
    H, W = a.shape[:2]
    ink = (a.min(axis=2) < 240)
    boxes = find_boxes(a)
    cols = cluster_columns(boxes, W) if boxes else []
    bands = []
    for ci, col in enumerate(cols):
        cx0 = min(b[0] for b in col)
        cx1 = max(b[2] for b in col)
        lo = 0 if ci == 0 else (max(b[2] for b in cols[ci - 1]) + cx0) // 2
        hi = W if ci == len(cols) - 1 else (cx1 + min(b[0] for b in cols[ci + 1])) // 2
        bands.append((cx0, cx1, max(0, lo), min(W, hi)))

    def band_for(b):
        cxm = (b[0] + b[2]) / 2
        best, bd = (0, W), 1e18
        for (cx0, cx1, lo, hi) in bands:
            d = 0 if cx0 <= cxm <= cx1 else min(abs(cxm - cx0), abs(cxm - cx1))
            if d < bd:
                bd, best = d, (lo, hi)
        return best

    groups = []
    prev_bottom = int(H * HEADER_BOT)
    for b in boxes:
        hd = heading_above(a, b, prev_bottom, W)
        new_head = None
        if hd:
            htop, hbot, colored, ext = hd
            if colored > 0.004:
                new_head = (htop, ext[0], ext[1])
        joined = False
        if groups and new_head is None:
            g = groups[-1]
            last = g["boxes"][-1]
            gap = b[1] - last[3]
            ov = min(b[2], last[2]) - max(b[0], last[0])
            vov = min(b[3], last[3]) - max(b[1], last[1])
            hgap = b[0] - last[2]
            if (ov > 0 and 0 <= gap < 160) or (vov > 0.5 * min(b[3] - b[1], last[3] - last[1]) and 0 <= hgap < 50):
                g["boxes"].append(b)
                joined = True
        if not joined:
            groups.append({"boxes": [b], "head": new_head})
        prev_bottom = max(prev_bottom, b[3])

    cards = []
    for g in groups:
        gb = g["boxes"]
        left = min(b[0] for b in gb) - 12
        right = max(b[2] for b in gb) + 12
        top = min(b[1] for b in gb) - 8
        if g["head"]:
            top = min(top, g["head"][0] - 10)
            left = min(left, g["head"][1] - 12)
            right = max(right, g["head"][2] + 12)
        cards.append([left, top, right, max(b[3] for b in gb) + 10])

    # widen horizontally to include sibling notes inside the same column band
    for ci, c in enumerate(cards):
        lo, hi = band_for(groups[ci]["boxes"][0])
        x0, y0, x1, y1 = [int(v) for v in c]
        blocked = False
        for cj, k in enumerate(cards):
            if cj == ci:
                continue
            vy = min(y1, k[3]) - max(y0, k[1])
            if vy <= 0:
                continue
            if k[0] < x1 and k[2] > x0:
                blocked = True
                break
            if k[2] <= x0 + 8:
                lo = max(lo, int(k[2]) + 6)
            if k[0] >= x1 - 8:
                hi = min(hi, int(k[0]) - 6)
        if blocked or hi <= lo:
            continue
        y0c, y1c = max(0, y0), min(H, y1)
        prof = ink[y0c:y1c, lo:hi].sum(axis=0) > 0
        idx = np.nonzero(prof)[0]
        if len(idx):
            rs = runs_of(idx, gap=60)
            pick = None
            for r in rs:
                if r[1] >= (x0 - lo) and r[0] <= (x1 - lo):
                    pick = r if pick is None else (min(pick[0], r[0]), max(pick[1], r[1]))
            if pick:
                x0 = min(x0, lo + int(pick[0]))
                x1 = max(x1, lo + int(pick[1]))
        c[0], c[1], c[2], c[3] = x0, y0, x1, y1
    # safety: expand crop box to avoid clipping nearby ink
    for c in cards:
        x0, y0, x1, y1 = [int(v) for v in c]
        for _ in range(26):
            if y0 <= int(H * HEADER_BOT):
                break
            row = a[y0 - 1, max(0, x0):min(W, x1)]
            if (row.min(axis=1) < 240).any():
                y0 -= 1
            else:
                break
        for _ in range(26):
            if x0 <= 0:
                break
            col = a[max(0, y0):min(H, y1), x0 - 1]
            if (col.min(axis=1) < 240).any():
                x0 -= 1
            else:
                break
        for _ in range(26):
            if x1 >= W:
                break
            col = a[max(0, y0):min(H, y1), x1]
            if (col.min(axis=1) < 240).any():
                x1 += 1
            else:
                break
        c[0], c[1], c[2], c[3] = max(0, x0 - 6), max(0, y0 - 6), min(W, x1 + 6), min(H, y1 + 6)
    # merge strongly overlapping cards (tables / side-by-side fragments)
    changed = True
    while changed:
        changed = False
        out = []
        for c in cards:
            placed = False
            for k in out:
                ix = min(c[2], k[2]) - max(c[0], k[0])
                iy = min(c[3], k[3]) - max(c[1], k[1])
                if ix > 0 and iy > 0:
                    inter = ix * iy
                    amin = min((c[2] - c[0]) * (c[3] - c[1]), (k[2] - k[0]) * (k[3] - k[1]))
                    if amin > 0 and inter / amin > 0.22:
                        k[0], k[1] = min(k[0], c[0]), min(k[1], c[1])
                        k[2], k[3] = max(k[2], c[2]), max(k[3], c[3])
                        placed = True
                        changed = True
                        break
            if not placed:
                out.append(list(c))
        cards = out
    return cards, W, H


def export(i, cards, W, H):
    pix = doc[i].get_pixmap(dpi=OUT_DPI)
    img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
    s = OUT_DPI / DPI
    out = []
    for k, (x0, y0, x1, y1) in enumerate(cards):
        X0, Y0 = int(max(0, x0) * s), int(max(0, y0) * s)
        X1, Y1 = int(min(W, x1) * s), int(min(H, y1) * s)
        crop = img.crop((X0, Y0, X1, Y1))
        if crop.width > 1150:
            crop = crop.resize((1150, int(crop.height * 1150 / crop.width)), Image.LANCZOS)
        fn = f"p{i:03d}_{k:02d}.jpg"
        crop.save(os.path.join(CARD_DIR, fn), quality=84, optimize=True)
        out.append({"file": fn, "w": crop.width, "h": crop.height, "page": i, "idx": k})
    return out


if __name__ == "__main__":
    os.makedirs(CARD_DIR, exist_ok=True)
    for p in [int(x) for x in sys.argv[1:]]:
        cards, W, H = build_page(p)
        print("page", p, page_category(p), "cards", len(cards))
