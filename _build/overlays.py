import os
from PIL import Image, ImageDraw, ImageFont
import build_cards as B

HERE = os.path.dirname(os.path.abspath(__file__))
QADIR = os.path.join(HERE, "qa")
os.makedirs(QADIR, exist_ok=True)
try:
    FONT = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 34)
except Exception:
    FONT = ImageFont.load_default()

for p in range(1, 137):
    if B.page_category(p) is None:
        continue
    cards, W, H = B.build_page(p)
    a = B.page_np(p)
    img = Image.fromarray(a)
    d = ImageDraw.Draw(img)
    for k, b in enumerate(cards):
        d.rectangle(b, outline=(230, 20, 20), width=5)
        label = str(k)
        tw = d.textlength(label, font=FONT) if hasattr(d, "textlength") else 20
        d.rectangle([b[0], b[1], b[0] + tw + 16, b[1] + 42], fill=(255, 255, 255))
        d.text((b[0] + 8, b[1] + 4), label, fill=(20, 20, 220), font=FONT)
    img.resize((1700, int(1700 * H / W))).save(os.path.join(QADIR, f"ov{p:03d}.png"))
    print(p, len(cards), flush=True)
