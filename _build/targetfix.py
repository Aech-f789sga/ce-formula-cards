"""Expand specific cards until the crop edge lands on blank paper."""
import os, sys, json
import build_cards as B
import growfix as G

HERE = os.path.dirname(os.path.abspath(__file__))
LIMIT = 90
STEP = 4


def edge_blank(a, side, box, need=5):
    x0, y0, x1, y1 = [int(round(v)) for v in box]
    if side == "t":
        band = a[max(0, y0 - need):y0, x0:x1]
    elif side == "b":
        band = a[y1:y1 + need, x0:x1]
    elif side == "l":
        band = a[y0:y1, max(0, x0 - need):x0]
    else:
        band = a[y0:y1, x1:x1 + need]
    if band.size == 0:
        return True
    return not (band.min(axis=2) < 200).any()


def main(ids):
    boxes = json.load(open(os.path.join(HERE, "boxes.json")))
    raw = open(os.path.join(HERE, "..", "data.js"), encoding="utf-8").read()
    cards = {c["id"]: c for c in json.loads(raw[len("window.DECK = "):].rstrip(";\n"))["cards"]}
    for cid in ids:
        key = cid.replace("-", "_")
        if key not in boxes:
            print(cid, "no box"); continue
        page = cards[cid]["page"]
        a = B.page_np(page, 150)
        H, W = a.shape[:2]
        b = list(boxes[key])
        before = list(b)
        for side in "tblr":
            if G.cont(a, side, b) <= 0.25:
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
                b = t
                if edge_blank(a, side, b):
                    break
        boxes[key] = [round(v, 1) for v in b]
        print(cid, [int(v) for v in before], "->", [int(v) for v in b])
    json.dump(boxes, open(os.path.join(HERE, "boxes.json"), "w"), indent=0)


if __name__ == "__main__":
    main(sys.argv[1:])
