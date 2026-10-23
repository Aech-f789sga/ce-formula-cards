"""Cut every proposed piece out of the PDF for review, and lay them out in sheets."""
import os, sys, json
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import build_cards as B
import plan

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "review")
PIECES = os.path.join(OUT, "pieces")
os.makedirs(PIECES, exist_ok=True)

cache = json.load(open(os.path.join(HERE, "pages_cache.json")))
titles = json.load(open(os.path.join(HERE, "titles.json")))


def card_title(p, k):
    return titles.get(str(p), {}).get("titles", {}).get(str(k), "")


def pieces_for(p, k, info):
    a = B.page_np(p, plan.DPI)
    x0, y0, x1, y1 = info["box"]
    ys = [y0] + list(info["splits"]) + [y1]
    out = []
    for i in range(len(ys) - 1):
        bb = plan.ink_bbox(a, x0, x1, ys[i], ys[i + 1])
        if bb is None:
            continue
        pad = 8
        bb = [max(0, bb[0] - pad), max(0, bb[1] - pad), min(a.shape[1], bb[2] + pad), min(a.shape[0], bb[3] + pad)]
        out.append(bb)
    return out


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "make"
    if mode == "make":
        cands = [(int(p), it["idx"], it) for p, v in cache.items() for it in v["cards"] if it["splits"]]
        cands.sort()
        manifest = {}
        for p, k, info in cands:
            pcs = pieces_for(p, k, info)
            a = B.page_np(p, plan.DPI)
            img = Image.fromarray(a)
            names = []
            for j, bb in enumerate(pcs):
                nm = f"p{p:03d}_{k:02d}{chr(97 + j)}"
                img.crop(tuple(int(v) for v in bb)).save(os.path.join(PIECES, nm + ".png"))
                names.append(nm)
            manifest[f"p{p:03d}_{k:02d}"] = dict(page=p, idx=k, pieces=names, boxes=pcs,
                                               title=card_title(p, k))
        json.dump(manifest, open(os.path.join(HERE, "pieces_manifest.json"), "w"), indent=1)
        print("pieces", sum(len(v["pieces"]) for v in manifest.values()), "cards", len(manifest))
    else:
        # sheet.py style: show N pieces per sheet
        man = json.load(open(os.path.join(HERE, "pieces_manifest.json")))
        keys = list(man)
        start = int(sys.argv[2]); count = int(sys.argv[3])
        batch = keys[start:start + count]
        try:
            font = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 17)
        except Exception:
            font = ImageFont.load_default()
        CW, CH, COLS = 460, 470, 3
        cells = []
        for key in batch:
            for nm in man[key]["pieces"]:
                cells.append((key, nm))
        rows = (len(cells) + COLS - 1) // COLS
        sheet = Image.new("RGB", (COLS * CW + 8, rows * (CH + 28) + 8), (246, 246, 246))
        d = ImageDraw.Draw(sheet)
        for i, (key, nm) in enumerate(cells):
            r, c = divmod(i, COLS)
            x = 4 + c * CW
            y = 4 + r * (CH + 28)
            im = Image.open(os.path.join(PIECES, nm + ".png")).convert("RGB")
            sc = min((CW - 10) / im.width, CH / im.height)
            im = im.resize((max(1, int(im.width * sc)), max(1, int(im.height * sc))), Image.LANCZOS)
            sheet.paste(im, (x + (CW - im.width) // 2, y + 22))
            d.rectangle([x, y, x + CW - 6, y + CH + 22], outline=(180, 180, 180))
            d.text((x + 3, y + 2), f"{nm}  [{key}] {man[key]['title'][:28]}", fill=(190, 0, 0), font=font)
        fn = os.path.join(OUT, f"pc_{start:03d}.png")
        sheet.save(fn)
        print(fn, len(cells), "cells", len(keys), "cards")
