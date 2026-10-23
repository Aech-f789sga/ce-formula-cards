"""Find cards whose crop actually slices through ink.

A crop is "cut" on a side when the dark pixels on the box's last inside row/col
continue into the pixels just outside the box.  A panel border line stops at the
box edge (white beyond), so borders are not reported.
"""
import os, json, collections
import numpy as np
import build_cards as B

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
S = 200 / 150
PAD = 16          # padding added at export time, in 150-dpi units
INK = 200


def dark(a, x0, x1, y0, y1):
    h, w = a.shape[:2]
    x0, x1 = max(0, min(w - 1, int(round(x0)))), max(1, min(w, int(round(x1))))
    y0, y1 = max(0, min(h - 1, int(round(y0)))), max(1, min(h, int(round(y1))))
    if x1 <= x0 or y1 <= y0:
        return np.zeros((1, 1), bool)
    return a[y0:y1, x0:x1].min(axis=2) < INK


def cont(a, side, x0, y0, x1, y1):
    """Overlap of ink on the edge line with ink just outside it."""
    if side in "tb":
        if side == "t":
            inside = dark(a, x0, x1, y0, y0 + 2).any(axis=0)
            outside = dark(a, x0, x1, y0 - 3, y0).any(axis=0)
        else:
            inside = dark(a, x0, x1, y1 - 2, y1).any(axis=0)
            outside = dark(a, x0, x1, y1, y1 + 3).any(axis=0)
    else:
        if side == "l":
            inside = dark(a, x0, x0 + 2, y0, y1).any(axis=1)
            outside = dark(a, x0 - 3, x0, y0, y1).any(axis=1)
        else:
            inside = dark(a, x1 - 2, x1, y0, y1).any(axis=1)
            outside = dark(a, x1, x1 + 3, y0, y1).any(axis=1)
    n = int(inside.sum())
    if inside.ndim == 2:
        return 0.0
    if n < 2:
        return 0.0
    return float((inside & outside).sum()) / n


def main():
    raw = open(os.path.join(ROOT, "data.js"), encoding="utf-8").read()
    cards = json.loads(raw[len("window.DECK = "):].rstrip(";\n"))["cards"]
    rep = json.load(open(os.path.join(HERE, "export_report.json")))
    by_page = collections.defaultdict(list)
    for c in cards:
        by_page[c["page"]].append(c)

    hits = {}
    for p, group in sorted(by_page.items()):
        a = B.page_np(p, 150)
        for c in group:
            name = c["img"].split("?")[0].split("/")[-1].replace(".jpg", "")
            r = rep.get(name)
            if not r:
                continue
            x0, y0, x1, y1 = [v / S + PAD for v in r["box"]]
            bad = []
            for side in "tblr":
                if cont(a, side, x0, y0, x1, y1) > 0.35:
                    bad.append(side)
            if bad:
                hits[c["id"]] = "".join(bad)
        print("page", p, "clipped so far", len(hits), flush=True)

    print("cards", len(cards), "clipped", len(hits))
    with open(os.path.join(HERE, "cuts.txt"), "w", encoding="utf-8") as f:
        for cid, sides in sorted(hits.items()):
            f.write(f"{cid}\t{sides}\n")
    json.dump(hits, open(os.path.join(HERE, "cuts.json"), "w"), indent=0)


if __name__ == "__main__":
    main()
