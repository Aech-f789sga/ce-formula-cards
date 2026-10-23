"""Detect genuinely cut-off ink on exported cards, using the saved crop boxes.

Cards are saved with a 12 px white frame, so the frame is skipped before probing.
"""
import os, json
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)


def edge_profile(a, side, skip, depth=4):
    dark = a < 200
    h, w = dark.shape
    if side == "t":
        band = dark[skip:skip + depth].max(axis=0)
    elif side == "b":
        band = dark[h - skip - depth:h - skip].max(axis=0)
    elif side == "l":
        band = dark[:, skip:skip + depth].max(axis=1)
    else:
        band = dark[:, w - skip - depth:w - skip].max(axis=1)
    n = band.size
    cov = float(band.mean())
    best = run = 0
    for v in band:
        run = run + 1 if v else 0
        best = max(best, run)
    return cov, best / n


def main():
    raw = open(os.path.join(ROOT, "data.js"), encoding="utf-8").read()
    cards = json.loads(raw[len("window.DECK = "):].rstrip(";\n"))["cards"]
    cut, border = [], []
    for c in cards:
        name = c["img"].split("?")[0].split("/")[-1].replace(".jpg", "")
        fn = os.path.join(ROOT, c["img"].split("?")[0])
        im = Image.open(fn).convert("L")
        a = np.array(im)
        # white frame thickness: 12 px at save time, scaled if the card was downscaled
        rep = json.load(open(os.path.join(HERE, "export_report.json"))).get(name, {})
        wpx = rep.get("box", [0, 0, 1150, 1])
        raw_w = max(1, wpx[2] - wpx[0])
        sc = min(1.0, 1150 / raw_w)
        skip = int(round(12 * sc)) + 1
        bad = []
        for side in "tblr":
            cov, run = edge_profile(a, side, skip)
            if cov < 0.012:
                continue
            if run > 0.55:
                continue
            bad.append(side)
        if bad:
            cut.append((c["id"], "".join(bad), c["title"][:44], round(float(im.size[0]))))
        else:
            border.append(c["id"])
    print("cards", len(cards), "real cuts", len(cut))
    with open(os.path.join(HERE, "cuts.txt"), "w") as f:
        for cid, sides, t, w in cut:
            f.write(f"{cid}\t{sides}\t{t}\n")
    for cid, sides, t, w in cut:
        print(f"  {cid:10s} {sides:4s} {t}")


if __name__ == "__main__":
    main()
