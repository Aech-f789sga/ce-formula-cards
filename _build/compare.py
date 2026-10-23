"""Side-by-side review of a split piece against its parent card."""
import os, sys, json
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(HERE, "review")
try:
    font = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 15)
except Exception:
    font = ImageFont.load_default()

CW, CH = 560, 520


def main(list_file, start, count, tag):
    ids = [l.strip() for l in open(list_file) if l.strip()]
    raw = open(os.path.join(ROOT, "data.js"), encoding="utf-8").read()
    cards = {c["id"]: c for c in json.loads(raw[len("window.DECK = "):].rstrip(";\n"))["cards"]}
    batch = ids[start:start + count]
    sheet = Image.new("RGB", (2 * CW + 12, len(batch) * (CH + 22) + 8), (245, 245, 245))
    d = ImageDraw.Draw(sheet)
    for i, cid in enumerate(batch):
        y = 4 + i * (CH + 22)
        pairs = []
        parent = cid[:-1] if cid.endswith("b") else None
        if parent and parent in cards:
            pairs.append((parent, cards[parent]))
        if cid in cards:
            pairs.append((cid, cards[cid]))
        for j, (k, c) in enumerate(pairs[:2]):
            x = 4 + j * (CW + 4)
            d.rectangle([x, y, x + CW - 4, y + CH + 18], outline=(150, 150, 150))
            d.text((x + 3, y + 2), f"#{i} {'PARENT' if j == 0 else 'CHILD'}  {c['title'][:46]}", fill=(185, 0, 0), font=font)
            try:
                im = Image.open(os.path.join(ROOT, c["img"].split("?")[0])).convert("RGB")
            except Exception:
                continue
            sc = min((CW - 10) / im.width, CH / im.height)
            im = im.resize((max(1, int(im.width * sc)), max(1, int(im.height * sc))), Image.LANCZOS)
            sheet.paste(im, (x + (CW - im.width) // 2, y + 20))
    fn = os.path.join(OUT, f"{tag}_{start:03d}.png")
    sheet.save(fn)
    print(fn, len(batch), "of", len(ids))


if __name__ == "__main__":
    main(sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4] if len(sys.argv) > 4 else "dup")
