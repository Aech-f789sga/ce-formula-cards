"""Draw two card boxes on the page to inspect an overlap."""
import os, sys, json
from PIL import Image, ImageDraw, ImageFont
import build_cards as B

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(HERE, "review")
S = 200 / 150
try:
    font = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 14)
except Exception:
    font = ImageFont.load_default()


def main(pairs, tag):
    boxes = json.load(open(os.path.join(HERE, "boxes.json")))
    rep = json.load(open(os.path.join(HERE, "export_report.json")))
    raw = open(os.path.join(ROOT, "data.js"), encoding="utf-8").read()
    cards = {c["id"]: c for c in json.loads(raw[len("window.DECK = "):].rstrip(";\n"))["cards"]}
    tiles = []
    for pair in pairs:
        a, b = pair.split(",")
        ba, bb = boxes[a.replace("-", "_")], boxes[b.replace("-", "_")]
        page = cards[a]["page"]
        x0 = min(ba[0], bb[0]) - 40
        y0 = min(ba[1], bb[1]) - 40
        x1 = max(ba[2], bb[2]) + 40
        y1 = max(ba[3], bb[3]) + 40
        pg = B.page_np(page, 150)
        im = Image.fromarray(pg[int(max(0, y0)):int(y1), int(max(0, x0)):int(x1)])
        sc = min(660 / im.width, 520 / im.height)
        im = im.resize((int(im.width * sc), int(im.height * sc)), Image.LANCZOS)
        d = ImageDraw.Draw(im)
        for box, col in ((ba, (220, 0, 0)), (bb, (0, 90, 220))):
            d.rectangle([(box[0] - x0) * sc, (box[1] - y0) * sc,
                         (box[2] - x0) * sc, (box[3] - y0) * sc], outline=col, width=2)
        tiles.append((f"{a} (red) vs {b} (blue)", im))
    W = max(t[1].width for t in tiles) + 8
    H = sum(t[1].height + 20 for t in tiles) + 8
    sheet = Image.new("RGB", (W, H), (246, 246, 246))
    y = 4
    d = ImageDraw.Draw(sheet)
    for label, im in tiles:
        d.text((5, y), label, fill=(150, 0, 0), font=font)
        sheet.paste(im, (4, y + 17))
        y += im.height + 20
    fn = os.path.join(OUT, f"{tag}.png")
    sheet.save(fn)
    print(fn)


if __name__ == "__main__":
    main(sys.argv[1].split(), sys.argv[2])
