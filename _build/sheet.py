"""Contact sheets for visual review. usage: sheet.py out.png cols file1 file2 ..."""
import os, sys
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
CARD_DIR = os.environ.get("SHEET_DIR") or os.path.join(HERE, "..", "assets", "cards")

out = sys.argv[1]
cols = int(sys.argv[2])
files = sys.argv[3:]
cw, ch = 430, 520
rows = (len(files) + cols - 1) // cols
pad = 8
W = cols * (cw + pad) + pad
H = rows * (ch + 26 + pad) + pad
sheet = Image.new("RGB", (W, H), (245, 245, 245))
d = ImageDraw.Draw(sheet)
try:
    font = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 18)
except Exception:
    font = ImageFont.load_default()
for i, f in enumerate(files):
    r, c = divmod(i, cols)
    x = pad + c * (cw + pad)
    y = pad + r * (ch + 26 + pad)
    im = Image.open(os.path.join(CARD_DIR, f)).convert("RGB")
    sc = min(cw / im.width, ch / im.height)
    im = im.resize((max(1, int(im.width * sc)), max(1, int(im.height * sc))), Image.LANCZOS)
    sheet.paste(im, (x + (cw - im.width) // 2, y + 22))
    d.rectangle([x, y, x + cw, y + ch + 22], outline=(180, 180, 180))
    d.text((x + 4, y + 2), f, fill=(200, 0, 0), font=font)
sheet.save(out)
print(out, sheet.size)
