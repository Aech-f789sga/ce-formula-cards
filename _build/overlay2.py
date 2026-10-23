"""Draw the crop box on the page around it, to see what a card actually keeps."""
import os, sys, json
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import build_cards as B

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(HERE, "review")
S = 200 / 150
PAD = 16
MARGIN = 80
try:
    font = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 15)
except Exception:
    font = ImageFont.load_default()


def main(list_file, start, count, tag):
    ids = [l.strip() for l in open(list_file) if l.strip()]
    rep = json.load(open(os.path.join(HERE, "export_report.json")))
    raw = open(os.path.join(ROOT, "data.js"), encoding="utf-8").read()
    cards = {c["id"]: c for c in json.loads(raw[len("window.DECK = "):].rstrip(";\n"))["cards"]}
    batch = ids[start:start + count]
    CW, CH = 620, 470
    sheet = Image.new("RGB", (2 * CW + 10, ((len(batch) + 1) // 2) * (CH + 20) + 6), (246, 246, 246))
    d = ImageDraw.Draw(sheet)
    for i, cid in enumerate(batch):
        c = cards.get(cid)
        if not c:
            continue
        name = c["img"].split("?")[0].split("/")[-1].replace(".jpg", "")
        r = rep.get(name)
        if not r:
            continue
        x0, y0 = r["box"][0] / S + PAD, r["box"][1] / S + PAD
        x1, y1 = r["box"][2] / S - PAD, r["box"][3] / S - PAD
        page = B.page_np(c["page"], 150)
        X0, Y0 = max(0, x0 - MARGIN), max(0, y0 - MARGIN)
        X1, Y1 = min(page.shape[1], x1 + MARGIN), min(page.shape[0], y1 + MARGIN)
        im = Image.fromarray(page[int(Y0):int(Y1), int(X0):int(X1)])
        sc = min((CW - 8) / im.width, CH / im.height)
        im = im.resize((max(1, int(im.width * sc)), max(1, int(im.height * sc))), Image.LANCZOS)
        cx, cy = 4 + (i % 2) * (CW + 2), 4 + (i // 2) * (CH + 20)
        sheet.paste(im, (cx, cy + 18))
        d.rectangle([cx + (x0 - X0) * sc, cy + 18 + (y0 - Y0) * sc,
                     cx + (x1 - X0) * sc, cy + 18 + (y1 - Y0) * sc], outline=(220, 0, 0), width=2)
        d.rectangle([cx, cy, cx + CW - 4, cy + CH + 16], outline=(160, 160, 160))
        d.text((cx + 3, cy + 1), f"{cid}  {c['title'][:44]}", fill=(150, 0, 0), font=font)
    fn = os.path.join(OUT, f"{tag}_{start:03d}.png")
    sheet.save(fn)
    print(fn)


if __name__ == "__main__":
    main(sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4] if len(sys.argv) > 4 else "ov")
