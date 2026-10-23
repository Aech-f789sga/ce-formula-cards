"""Render a page region (150-dpi plan coords) for inspection."""
import sys, os
import fitz
HERE = os.path.dirname(os.path.abspath(__file__))
PDF = r"C:\Users\gamao\Downloads\FORMULA CARD (Engr. APJO) - without grid.pdf"
OUT = os.path.join(HERE, "review")
DPI = 200

page = int(sys.argv[1])
x0, y0, x1, y1 = (float(v) for v in sys.argv[2:6])
tag = sys.argv[6] if len(sys.argv) > 6 else f"pg{page:03d}"
doc = fitz.open(PDF)
pg = doc[page]   # build scripts index the doc directly (page 1 == second PDF page)
k = 72.0 / 150.0          # 150-dpi px -> points
clip = fitz.Rect(x0 * k, y0 * k, x1 * k, y1 * k)
pix = pg.get_pixmap(matrix=fitz.Matrix(DPI / 72.0, DPI / 72.0), clip=clip)
fn = os.path.join(OUT, f"{tag}.png")
pix.save(fn)
print(fn, pix.width, pix.height)
