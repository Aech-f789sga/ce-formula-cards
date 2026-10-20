import os, sys
from PIL import Image, ImageDraw
import build_cards as B

HERE = os.path.dirname(os.path.abspath(__file__))
QADIR = os.path.join(HERE, "qa")
os.makedirs(QADIR, exist_ok=True)

for p in [int(x) for x in sys.argv[1:]]:
    cards, W, H = B.build_page(p)
    a = B.page_np(p)
    img = Image.fromarray(a)
    d = ImageDraw.Draw(img)
    for k, b in enumerate(cards):
        d.rectangle(b, outline=(220, 0, 0), width=4)
        d.rectangle([b[0], b[1], b[0] + 44, b[1] + 32], fill=(255, 255, 255))
        d.text((b[0] + 12, b[1] + 8), str(k), fill=(0, 0, 255))
    img.resize((1700, int(1700 * H / W))).save(os.path.join(QADIR, f"ov{p}.png"))

    pix = B.doc[p].get_pixmap(dpi=200)
    page = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
    s = 200 / 150
    for k, (x0, y0, x1, y1) in enumerate(cards):
        crop = page.crop((int(x0 * s), int(y0 * s), int(x1 * s), int(y1 * s)))
        if crop.width > 900:
            crop = crop.resize((900, int(crop.height * 900 / crop.width)), Image.LANCZOS)
        crop.save(os.path.join(QADIR, f"c{p:03d}_{k:02d}.png"))
    print(p, len(cards))
