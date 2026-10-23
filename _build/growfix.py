"""Grow card boxes outward wherever the crop slices through ink.

Writes boxes.json, a per-card override consumed by export2.py.
"""
import os, json, collections
import numpy as np
import build_cards as B

HERE = os.path.dirname(os.path.abspath(__file__))
INK = 200
LIMIT = 56          # max growth per side, in 150-dpi px
STEP = 4
BLOCK = 3           # keep this much clear of a neighbouring card


def dark(a, x0, x1, y0, y1):
    h, w = a.shape[:2]
    x0, x1 = max(0, min(w - 1, int(round(x0)))), max(1, min(w, int(round(x1))))
    y0, y1 = max(0, min(h - 1, int(round(y0)))), max(1, min(h, int(round(y1))))
    if x1 <= x0 or y1 <= y0:
        return np.zeros((1, 1), bool)
    return a[y0:y1, x0:x1].min(axis=2) < INK


def longest_run(mask):
    best = run = 0
    for v in mask:
        run = run + 1 if v else 0
        best = max(best, run)
    return best


def cont(a, side, box):
    x0, y0, x1, y1 = box
    if side == "t":
        ins, out = dark(a, x0, x1, y0, y0 + 2).any(axis=0), dark(a, x0, x1, y0 - 3, y0).any(axis=0)
    elif side == "b":
        ins, out = dark(a, x0, x1, y1 - 2, y1).any(axis=0), dark(a, x0, x1, y1, y1 + 3).any(axis=0)
    elif side == "l":
        ins, out = dark(a, x0, x0 + 2, y0, y1).any(axis=1), dark(a, x0 - 3, x0, y0, y1).any(axis=1)
    else:
        ins, out = dark(a, x1 - 2, x1, y0, y1).any(axis=1), dark(a, x1, x1 + 3, y0, y1).any(axis=1)
    if ins.ndim == 2:
        return 0.0
    n = int(ins.sum())
    if n < 3:
        return 0.0
    if longest_run(ins) > 0.55 * ins.size:      # a rule line, not a sliced glyph
        return 0.0
    return float((ins & out).sum()) / n


def resolve(page_pieces, fixes):
    """Card name -> box, after drop / union / box / expand overrides."""
    merge = {}
    for k, v in fixes.items():
        for s in v.get("union", []):
            merge[s] = k
    names = {}
    for q in page_pieces:
        nm = q["name"]
        names[nm] = q
    out = []
    for q in page_pieces:
        nm = q["name"]
        if nm in merge:
            continue
        bx = list(q["box"])
        fx = fixes.get(nm) or {}
        if fx.get("drop"):
            continue
        for other in fx.get("union", []):
            o = names[other]["box"]
            bx = [min(bx[0], o[0]), min(bx[1], o[1]), max(bx[2], o[2]), max(bx[3], o[3])]
        if "box" in fx:
            bx = list(fx["box"])
        if "expand" in fx:
            e = fx["expand"]
            bx = [bx[0] - e[0], bx[1] - e[1], bx[2] + e[2], bx[3] + e[3]]
        out.append((nm, [float(v) for v in bx]))
    return out


def blank_bands(a, x0, x1, y0, y1, minh=6):
    """Horizontal bands with no ink across [x0,x1), as (top, bottom) pairs."""
    h, w = a.shape[:2]
    x0, x1 = max(0, int(x0)), min(w, int(x1))
    y0, y1 = max(0, int(y0)), min(h, int(y1))
    if x1 <= x0 or y1 <= y0:
        return []
    rows = (a[y0:y1, x0:x1].min(axis=2) < INK).any(axis=1)
    out, s = [], None
    for i, v in enumerate(rows):
        if not v and s is None:
            s = i
        elif v and s is not None:
            if i - s >= minh:
                out.append((y0 + s, y0 + i))
            s = None
    if s is not None and len(rows) - s >= minh:
        out.append((y0 + s, y0 + len(rows)))
    return out


def snap_pairs(a, cards, minh=50, reach=64):
    """Move shared boundaries that slice a line to the nearest blank band."""
    moves = 0
    for i in range(len(cards)):
        for j in range(i + 1, len(cards)):
            A, B = cards[i][1], cards[j][1]
            # vertical neighbour: A above B
            for (U, L) in ((A, B), (B, A)):
                if abs(U[3] - L[1]) <= 10 and min(U[2], L[2]) - max(U[0], L[0]) > 40:
                    y = (U[3] + L[1]) / 2
                    w = min(U[2], L[2]) - max(U[0], L[0])
                    xa = max(U[0], L[0]) + w * 0.18
                    xb = min(U[2], L[2]) - w * 0.18
                    bands = blank_bands(a, xa, xb, y - reach, y + reach, minh=4)
                    if not bands:
                        continue
                    best = min(bands, key=lambda b: abs((b[0] + b[1]) / 2 - y))
                    ny = (best[0] + best[1]) / 2
                    if abs(ny - y) < 2:
                        continue
                    if ny - U[1] < minh or L[3] - ny < minh:
                        continue
                    U[3], L[1] = ny, ny
                    moves += 1
            # horizontal neighbour: A left of B
            for (U, L) in ((A, B), (B, A)):
                if abs(U[2] - L[0]) <= 10 and min(U[3], L[3]) - max(U[1], L[1]) > 40:
                    x = (U[2] + L[0]) / 2
                    hh, ww = a.shape[:2]
                    hgt = min(U[3], L[3]) - max(U[1], L[1])
                    ya, yb = max(U[1], L[1]) + hgt * 0.18, min(U[3], L[3]) - hgt * 0.18
                    ya, yb = max(0, int(ya)), min(hh, int(yb))
                    if yb <= ya:
                        continue
                    m = (a[ya:yb, :].min(axis=2) < INK).any(axis=0)
                    cols, s = [], None
                    for k in range(max(0, int(x - reach)), min(ww, int(x + reach))):
                        v = m[k]
                        if not v and s is None:
                            s = k
                        elif v and s is not None:
                            if k - s >= 4:
                                cols.append((s, k))
                            s = None
                    if not cols:
                        continue
                    best = min(cols, key=lambda b: abs((b[0] + b[1]) / 2 - x))
                    nx = (best[0] + best[1]) / 2
                    if abs(nx - x) < 2 or nx - U[0] < 40 or L[2] - nx < 40:
                        continue
                    U[2], L[0] = nx, nx
                    moves += 1
    return moves


def main():
    plan = json.load(open(os.path.join(HERE, "plan_all.json")))
    fixes = json.load(open(os.path.join(HERE, "fixes.json")))
    result, grown = {}, 0
    for p in sorted(plan, key=int):
        v = plan[p]
        pieces = []
        for q in v["pieces"]:
            sfx = "" if q["pi"] == 0 else chr(97 + q["pi"])
            pieces.append(dict(name=f"p{int(p):03d}_{q['src']:02d}{sfx}", box=q["box"]))
        cards = resolve(pieces, {k: v2 for k, v2 in fixes.items() if k.startswith(f"p{int(p):03d}_")})
        a = B.page_np(int(p), 150)
        H, W = a.shape[:2]
        snaps = snap_pairs(a, cards)
        for i, (nm, box) in enumerate(cards):
            b = list(box)
            others = [c[1] for j, c in enumerate(cards) if j != i]
            for side in "tblr":
                if cont(a, side, b) <= 0.45:
                    continue
                base = list(b)
                for d in range(STEP, LIMIT + 1, STEP):
                    t = list(base)
                    if side == "t":
                        t[1] = base[1] - d
                    elif side == "b":
                        t[3] = base[3] + d
                    elif side == "l":
                        t[0] = base[0] - d
                    else:
                        t[2] = base[2] + d
                    if t[0] < 0 or t[1] < 0 or t[2] > W or t[3] > H:
                        break
                    # do not eat into a neighbour (ignore hairline overlaps)
                    clash = False
                    for o in others:
                        ox = min(t[2], o[2]) - max(t[0], o[0])
                        oy = min(t[3], o[3]) - max(t[1], o[1])
                        if side in "tb":
                            if ox > 20 and oy > BLOCK:
                                clash = True
                                break
                        else:
                            if oy > 20 and ox > BLOCK:
                                clash = True
                                break
                    if clash:
                        break
                    b = t
                    if cont(a, side, b) <= 0.35:
                        break
                if b != base:
                    grown += 1
            result[nm] = [round(x, 1) for x in b]
        print("page", p, len(cards), "snaps", snaps, flush=True)

    json.dump(result, open(os.path.join(HERE, "boxes.json"), "w"), indent=0)
    print("cards", len(result), "sides grown", grown)


if __name__ == "__main__":
    main()
