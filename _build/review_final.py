"""Review sheets over final deck cards, driven by a list of ids."""
import os, sys, json
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
CARD_DIR = os.path.join(ROOT, "assets", "cards")
OUT = os.path.join(HERE, "review")
try:
    font = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 16)
except Exception:
    font = ImageFont.load_default()

CW, CH, COLS = 470, 480, 3


def main(list_file, start, count, tag):
    ids = [l.strip() for l in open(list_file) if l.strip()]
    raw = open(os.path.join(ROOT, "data.js"), encoding="utf-8").read()
    cards = {c["id"]: c for c in json.loads(raw[len("window.DECK = "):].rstrip(";\n"))["cards"]}
    batch = ids[start:start + count]
    rows = (len(batch) + COLS - 1) // COLS
    sheet = Image.new("RGB", (COLS * CW + 8, rows * (CH + 24) + 8), (245, 245, 245))
    d = ImageDraw.Draw(sheet)
    for i, cid in enumerate(batch):
        c = cards.get(cid)
        if not c:
            continue
        r, col = divmod(i, COLS)
        x, y = 4 + col * CW, 4 + r * (CH + 24)
        im = Image.open(os.path.join(ROOT, c["img"].split("?")[0])).convert("RGB")
        sc = min((CW - 8) / im.width, CH / im.height)
        im = im.resize((max(1, int(im.width * sc)), max(1, int(im.height * sc))), Image.LANCZOS)
        sheet.paste(im, (x + (CW - im.width) // 2, y + 20))
        d.rectangle([x, y, x + CW - 6, y + CH + 20], outline=(175, 175, 175))
        d.text((x + 3, y + 1), f"{cid}  {c['title'][:40]}", fill=(185, 0, 0), font=font)
    fn = os.path.join(OUT, f"{tag}_{start:03d}.png")
    sheet.save(fn)
    print(fn, len(batch), "of", len(ids))


if __name__ == "__main__":
    main(sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4] if len(sys.argv) > 4 else "fin")
