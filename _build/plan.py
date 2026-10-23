"""Plan the repaired deck: split multi-topic cards, re-crop every card.

Rules
  * interior analysis ignores the panel border (near-full-height/width ink lines)
  * a card splits where a wide blank band sits between two content blocks, or
    where a coloured heading sits outside any box
  * a card whose ink is cut at an edge, with a neighbour panel right next to it,
    is first unioned with that neighbour and then re-split, so nothing is cut
  * every piece then grows into surrounding whitespace, so nothing is cropped short
"""
import os, json, sys
import numpy as np
from PIL import Image
import build_cards as B

HERE = os.path.dirname(os.path.abspath(__file__))
CARD_DIR = os.path.join(HERE, "..", "assets", "cards")
DPI = 150
OUT_DPI = 200
S = OUT_DPI / DPI

BLANK_MIN = 44
HEAD_MIN, HEAD_MAX = 12, 80
GROW = 130
PAD = 16
INK = 200          # the grey panel background is ~234, so this keeps only real ink


def mask(a):
    return a.min(axis=2) < INK


def trim_border(m, span=70, frac=0.55):
    """Insets that skip panel border lines, which sit just inside the crop edge."""
    h, w = m.shape
    cols = m.mean(axis=0)
    rows = m.mean(axis=1)
    lim = min(span, max(4, w // 4))
    hit = [i for i in range(lim) if cols[i] > frac]
    l = hit[-1] + 3 if hit else 0
    lim = min(span, max(4, w // 4))
    hit = [i for i in range(lim) if cols[w - 1 - i] > frac]
    r = hit[-1] + 3 if hit else 0
    lim = min(span, max(4, h // 4))
    hit = [i for i in range(lim) if rows[i] > frac]
    t = hit[-1] + 3 if hit else 0
    lim = min(span, max(4, h // 4))
    hit = [i for i in range(lim) if rows[h - 1 - i] > frac]
    b = hit[-1] + 3 if hit else 0
    return l, t, r, b


def runs(flags, minlen):
    idx = np.nonzero(flags)[0]
    if not len(idx):
        return []
    out = []
    s = p = int(idx[0])
    for v in idx[1:]:
        v = int(v)
        if v - p > 2:
            out.append((s, p))
            s = v
        p = v
    out.append((s, p))
    return [x for x in out if x[1] - x[0] + 1 >= minlen]


def inside(boxes, y, margin=3):
    return any(b[1] + margin <= y <= b[3] - margin for b in boxes)


def find_splits(a, box, page_boxes):
    x0, y0, x1, y1 = [int(v) for v in box]
    x0, y0 = max(0, x0), max(0, y0)
    x1, y1 = min(a.shape[1], x1), min(a.shape[0], y1)
    if y1 - y0 < 90:
        return []
    sub = a[y0:y1, x0:x1]
    m = mask(sub)
    l, t, r, b = trim_border(m)
    core = m[t:m.shape[0] - b, l:m.shape[1] - r]
    if core.size == 0 or core.shape[0] < 60:
        return []
    card_area = (x1 - x0) * (y1 - y0)
    inner = [q for q in page_boxes
             if (q[2] - q[0]) * (q[3] - q[1]) < 0.85 * card_area
             and q[0] >= x0 - 4 and q[2] <= x1 + 4 and q[1] >= y0 - 4 and q[3] <= y1 + 4]
    csub = sub[t:m.shape[0] - b, l:m.shape[1] - r]
    mn = csub.min(axis=2).astype(np.int16)
    mx = csub.max(axis=2).astype(np.int16)
    colr = (mx - mn > 45) & (mn < INK)
    cands = []
    for (s, e) in runs(~core.any(axis=1), BLANK_MIN):
        above = int(core[:s].any(axis=1).sum())
        below = int(core[e + 1:].any(axis=1).sum())
        if above < 80 or below < 60:
            continue
        mid = y0 + t + (s + e) // 2
        if inside(inner, mid):
            continue
        cands.append((e - s + 1, mid))
    for (s, e) in runs(colr.any(axis=1), HEAD_MIN):
        if e - s + 1 > HEAD_MAX or s < 30:
            continue
        if inside(inner, y0 + t + s) or inside(inner, y0 + t + e):
            continue
        if int(core[:s].any(axis=1).sum()) < 80:
            continue
        cands.append((60, y0 + t + s - 2))
    cands.sort(reverse=True)
    picked = []
    for size, y in cands:
        if len(picked) >= 6:
            break
        if all(abs(y - q) > 58 for q in picked):
            picked.append(y)
    return sorted(picked)


def ink_bbox(a, x0, x1, y0, y1):
    sub = a[max(0, y0):y1, max(0, x0):x1]
    m = mask(sub)
    rows = np.nonzero(m.any(axis=1))[0]
    cols = np.nonzero(m.any(axis=0))[0]
    if not len(rows):
        return None
    return [max(0, x0) + int(cols[0]), max(0, y0) + int(rows[0]),
            max(0, x0) + int(cols[-1]) + 1, max(0, y0) + int(rows[-1]) + 1]


def clipped_edges(a, box):
    x0, y0, x1, y1 = [int(v) for v in box]
    H, W = a.shape[:2]
    x0, y0, x1, y1 = max(0, x0), max(0, y0), min(W, x1), min(H, y1)
    m = mask(a[y0:y1, x0:x1])
    if m.size == 0:
        return []
    out = []
    if m[:3].any():
        out.append("top")
    if m[-3:].any():
        out.append("bottom")
    if m[:, :3].any():
        out.append("left")
    if m[:, -3:].any():
        out.append("right")
    return out


def near(box, other, side, tol=30):
    x0, y0, x1, y1 = box
    ox0, oy0, ox1, oy1 = other
    vov = min(y1, oy1) - max(y0, oy0)
    hov = min(x1, ox1) - max(x0, ox0)
    if side == "right":
        return 0 <= ox0 - x1 <= tol and vov > 0.3 * (y1 - y0)
    if side == "left":
        return 0 <= x0 - ox1 <= tol and vov > 0.3 * (y1 - y0)
    if side == "bottom":
        return 0 <= oy0 - y1 <= tol and hov > 0.3 * (x1 - x0)
    if side == "top":
        return 0 <= y0 - oy1 <= tol and hov > 0.3 * (x1 - x0)
    return False


def has_ink(a, box, min_rows=8):
    x0, y0, x1, y1 = [int(v) for v in box]
    sub = a[max(0, y0):y1, max(0, x0):x1]
    m = mask(sub)
    l, t, r, b = trim_border(m)
    core = m[t:m.shape[0] - b, l:m.shape[1] - r] if m.size else m
    return core.size > 0 and core.any(axis=1).sum() >= min_rows


def plan_page(p, overrides=None):
    """-> list of dicts: box(150dpi), src(old card idx), piece index, splits used.

    overrides maps old card index -> list of split y values (empty list = keep whole).
    """
    cards, W, H = B.build_page(p)
    a = B.page_np(p, DPI)
    page_boxes = B.find_boxes(a)
    regions = [dict(box=[int(v) for v in c], src=k) for k, c in enumerate(cards)]
    changed = True
    while changed:
        changed = False
        for i in range(len(regions)):
            for side in clipped_edges(a, regions[i]["box"]):
                for j in range(len(regions)):
                    if i == j:
                        continue
                    if near(regions[i]["box"], regions[j]["box"], side):
                        r, s = regions[i]["box"], regions[j]["box"]
                        regions[i]["box"] = [min(r[0], s[0]), min(r[1], s[1]), max(r[2], s[2]), max(r[3], s[3])]
                        regions.pop(j)
                        changed = True
                        break
                if changed:
                    break
            if changed:
                break
    pieces = []
    for r in regions:
        if overrides and r["src"] in overrides:
            sp = overrides[r["src"]]
        else:
            sp = find_splits(a, r["box"], page_boxes)
        ys = [r["box"][1]] + list(sp) + [r["box"][3]]
        segs = [[ys[i], ys[i + 1]] for i in range(len(ys) - 1) if ys[i + 1] - ys[i] >= 34]
        # a short block right above a boundary is a heading: keep it with what follows
        merged = []
        for seg in segs:
            if merged and merged[-1][1] - merged[-1][0] < 95:
                merged[-1][1] = seg[1]
            else:
                merged.append(list(seg))
        if len(merged) > 1 and merged[-1][1] - merged[-1][0] < 95:
            merged[-2][1] = merged[-1][1]
            merged.pop()
        pi = 0
        for (sy0, sy1) in merged:
            bb = ink_bbox(a, r["box"][0], r["box"][2], sy0, sy1)
            if bb is None or not has_ink(a, bb):
                continue
            pieces.append(dict(box=bb, src=r["src"], pi=pi, splits=sp))
            pi += 1
    # grow each piece outward, bridging small gaps (letter spacing, cell padding)
    ink = mask(a)
    top_lim = int(H * B.HEADER_BOT)
    bot_lim = int(H * B.FOOTER_TOP)
    ink[:top_lim] = False
    ink[bot_lim:] = False

    def push(box, side, gap, limit, others=None):
        x0, y0, x1, y1 = box
        n = 0
        while n < limit:
            if side == "r":
                step = None
                for d in range(1, gap + 1):
                    if x1 + d >= W:
                        break
                    if ink[y0:y1, x1 + d].any():
                        step = d
                        break
                if step is None:
                    break
                if others is not None and others[y0:y1, x1 + 1:x1 + step + 1].any():
                    break
                x1 += step
                n += step
            elif side == "l":
                step = None
                for d in range(1, gap + 1):
                    if x0 - d <= 0:
                        break
                    if ink[y0:y1, x0 - d].any():
                        step = d
                        break
                if step is None:
                    break
                if others is not None and others[y0:y1, x0 - step:x0].any():
                    break
                x0 -= step
                n += step
            elif side == "d":
                step = None
                for d in range(1, gap + 1):
                    if y1 + d >= bot_lim:
                        break
                    if ink[y1 + d, x0:x1].any():
                        step = d
                        break
                if step is None:
                    break
                if others is not None and others[y1 + 1:y1 + step + 1, x0:x1].any():
                    break
                y1 += step
                n += step
            else:
                step = None
                for d in range(1, gap + 1):
                    if y0 - d <= top_lim:
                        break
                    if ink[y0 - d, x0:x1].any():
                        step = d
                        break
                if step is None:
                    break
                if others is not None and others[y0 - step:y0, x0:x1].any():
                    break
                y0 -= step
                n += step
        return [x0, y0, x1, y1]

    cores = [list(p["box"]) for p in pieces]
    for i, pc in enumerate(pieces):
        others = np.zeros((H, W), dtype=bool)
        for j, kb in enumerate(cores):
            if j == i:
                continue
            others[max(0, kb[1] - 2):min(H, kb[3] + 2), max(0, kb[0] - 2):min(W, kb[2] + 2)] = True
        box = list(pc["box"])
        for side in "udlr":
            box = push(box, side, 12, GROW, others)
        pc["box"] = box

    # second pass: ignore neighbours so a heading wider than its formula is kept whole
    snap = [list(p["box"]) for p in pieces]
    for pc in pieces:
        box = list(pc["box"])
        box = push(box, "l", 16, 200)
        box = push(box, "r", 16, 200)
        pc["box"] = box
    bad = set()
    for i in range(len(pieces)):
        for j in range(i + 1, len(pieces)):
            a2, b2 = pieces[i]["box"], pieces[j]["box"]
            ix = min(a2[2], b2[2]) - max(a2[0], b2[0])
            iy = min(a2[3], b2[3]) - max(a2[1], b2[1])
            if ix > 3 and iy > 3:
                inter = ix * iy
                small = min((a2[2] - a2[0]) * (a2[3] - a2[1]), (b2[2] - b2[0]) * (b2[3] - b2[1]))
                if small > 0 and inter / small > 0.15:
                    bad.add(i)
                    bad.add(j)
    for i in bad:
        pieces[i]["box"] = snap[i]
    pieces.sort(key=lambda q: (q["box"][1] // 110, q["box"][0]))
    return pieces, cards, W, H


if __name__ == "__main__":
    pages = [int(x) for x in sys.argv[1:]] or list(range(1, 137))
    for p in pages:
        pieces, cards, W, H = plan_page(p)
        if len(pieces) != len(cards):
            print(f"p{p:03d} {len(cards)} -> {len(pieces)}")
