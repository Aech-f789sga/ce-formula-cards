"""Rank cards by how likely their crop slices through ink, for visual review."""
import os, json, collections
import numpy as np
import build_cards as B

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
S = 200 / 150
PAD = 16
INK = 200


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


def score_side(a, side, x0, y0, x1, y1):
    if side == "t":
        ins = dark(a, x0, x1, y0, y0 + 2).any(axis=0)
        out = dark(a, x0, x1, y0 - 3, y0).any(axis=0)
    elif side == "b":
        ins = dark(a, x0, x1, y1 - 2, y1).any(axis=0)
        out = dark(a, x0, x1, y1, y1 + 3).any(axis=0)
    elif side == "l":
        ins = dark(a, x0, x0 + 2, y0, y1).any(axis=1)
        out = dark(a, x0 - 3, x0, y0, y1).any(axis=1)
    else:
        ins = dark(a, x1 - 2, x1, y0, y1).any(axis=1)
        out = dark(a, x1, x1 + 3, y0, y1).any(axis=1)
    if ins.ndim == 2:
        return 0.0
    n = int(ins.sum())
    if n < 3:
        return 0.0
    span = ins.size
    # a rule / panel border runs most of the edge: not clipped content
    if longest_run(ins) > 0.55 * span:
        return 0.0
    return float((ins & out).sum()) / n


def main():
    raw = open(os.path.join(ROOT, "data.js"), encoding="utf-8").read()
    cards = json.loads(raw[len("window.DECK = "):].rstrip(";\n"))["cards"]
    rep = json.load(open(os.path.join(HERE, "export_report.json")))
    by_page = collections.defaultdict(list)
    for c in cards:
        by_page[c["page"]].append(c)

    scored = []
    for p, group in sorted(by_page.items()):
        a = B.page_np(p, 150)
        for c in group:
            name = c["img"].split("?")[0].split("/")[-1].replace(".jpg", "")
            r = rep.get(name)
            if not r:
                continue
            x0, y0, x1, y1 = [v / S + PAD for v in r["box"][:2]] + [v / S - PAD for v in r["box"][2:]]
            sides = {s: score_side(a, s, x0, y0, x1, y1) for s in "tblr"}
            best = max(sides.values())
            if best >= 0.45:
                scored.append((round(best, 2), c["id"], "".join(k for k, v in sides.items() if v >= 0.45)))
        print("page", p, len(scored), flush=True)

    scored.sort(reverse=True)
    print("suspect", len(scored))
    json.dump(scored, open(os.path.join(HERE, "suspect.json"), "w"), indent=0)
    with open(os.path.join(HERE, "suspect.txt"), "w") as f:
        for s, cid, sides in scored:
            f.write(f"{cid}\t{sides}\t{s}\n")


if __name__ == "__main__":
    main()
