"""Export the repaired deck: crops + data.js."""
import os, json, sys
import numpy as np
from PIL import Image, ImageOps
import build_cards as B

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
CARD_DIR = os.path.join(ROOT, "assets", "cards")
OUT_DPI = 200
S = OUT_DPI / 150

CATS = {
    "geotech": dict(name="Geotechnical Engineering", short="Geotechnical",
                    blurb="Soil properties, classification, permeability, consolidation, shear strength, earth pressure, and foundations."),
    "hydraulics": dict(name="Hydraulics", short="Hydraulics",
                       blurb="Fluid properties, hydrostatics, buoyancy, pipe flow, open channels, weirs, and pumps."),
    "structural": dict(name="Principles of Structural Analysis and Design", short="Structural",
                       blurb="Engineering mechanics, theory of structures, steel, concrete, and earthquake engineering."),
    "math": dict(name="Math, Surveying, and Transportation Engineering", short="Math · Surv · Transpo",
                 blurb="Algebra, geometry, calculus, statistics, surveying, transportation, and engineering economy."),
}


def edge_flags(im):
    a = np.array(im.convert("L"))
    h, w = a.shape
    dark = a < 205
    out = []
    if dark[:2].mean() > 0.08:
        out.append("t")
    if dark[-2:].mean() > 0.08:
        out.append("b")
    if dark[:, :2].mean() > 0.08:
        out.append("l")
    if dark[:, -2:].mean() > 0.08:
        out.append("r")
    return out


def trim_panel_edge(im):
    """Drop a panel border line that ended up flush with the crop edge."""
    a = np.array(im.convert("L"))
    h, w = a.shape
    dark = a < 200
    x0, y0, x1, y1 = 0, 0, w, h
    for _ in range(8):
        if x0 < x1 and dark[:, x0].mean() > 0.55:
            x0 += 1
        else:
            break
    for _ in range(8):
        if x1 - 1 > x0 and dark[:, x1 - 1].mean() > 0.55:
            x1 -= 1
        else:
            break
    for _ in range(8):
        if y0 < y1 and dark[y0, :].mean() > 0.55:
            y0 += 1
        else:
            break
    for _ in range(8):
        if y1 - 1 > y0 and dark[y1 - 1, :].mean() > 0.55:
            y1 -= 1
        else:
            break
    return im.crop((x0, y0, x1, y1))


def main(dry=False):
    plan_all = json.load(open(os.path.join(HERE, "plan_all.json")))
    titles = json.load(open(os.path.join(HERE, "titles.json")))
    extra_p = os.path.join(HERE, "titles_split.json")
    extra = json.load(open(extra_p)) if os.path.exists(extra_p) else {}
    fix_p = os.path.join(HERE, "fixes.json")
    fixes = json.load(open(fix_p)) if os.path.exists(fix_p) else {}
    boxes_p = os.path.join(HERE, "boxes.json")
    boxes = json.load(open(boxes_p)) if os.path.exists(boxes_p) else {}
    drop_p = os.path.join(HERE, "drop.json")
    drop = set(json.load(open(drop_p))) if os.path.exists(drop_p) else set()

    # a card whose heading was split off is joined back to it
    merge_into = {}
    for k, v in fixes.items():
        for src in v.get("union", []):
            merge_into[src] = k
    out = []
    report = {}
    missing = []
    used = set()
    for p in sorted(plan_all, key=int):
        v = plan_all[p]
        cat = B.page_category(int(p))
        if cat is None:
            continue
        sec = titles.get(str(p), {})
        page_title = sec.get("section", "")
        img = None
        batch = []
        for q in v["pieces"]:
            src, pi = q["src"], q["pi"]
            suffix = "" if pi == 0 else chr(97 + pi)
            name = f"p{int(p):03d}_{src:02d}{suffix}"
            if name in drop or name in merge_into:
                continue
            cid = f"p{int(p):03d}-{src:02d}{suffix}"
            if pi == 0:
                title = sec.get("titles", {}).get(str(src), "")
            else:
                title = extra.get(name, "")
            if fixes.get(name, {}).get("title"):
                title = fixes[name]["title"]
            if not title:
                missing.append(name)
                title = extra.get(name) or f"Formula Set — p. {int(p)}"
            bx = q["box"]
            fx = fixes.get(name)
            if fx and fx.get("union"):
                for other in fx["union"]:
                    for qq in v["pieces"]:
                        nm2 = f"p{int(p):03d}_{qq['src']:02d}" + ("" if qq["pi"] == 0 else chr(97 + qq["pi"]))
                        if nm2 == other:
                            o = qq["box"]
                            bx = [min(bx[0], o[0]), min(bx[1], o[1]), max(bx[2], o[2]), max(bx[3], o[3])]
            if fx:
                if fx.get("drop"):
                    continue
                if "box" in fx:
                    bx = fx["box"]
                if "expand" in fx:
                    e = fx["expand"]
                    bx = [bx[0] - e[0], bx[1] - e[1], bx[2] + e[2], bx[3] + e[3]]
            if name in boxes:
                bx = boxes[name]
            batch.append(dict(name=name, cid=cid, title=title, box=list(bx)))

        # padding stops before any foreign ink, so a crop never picks up a
        # sliver of the next card's formula
        if not dry:
            pix = B.doc[int(p)].get_pixmap(dpi=OUT_DPI)
            img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
            gray = np.array(img.convert("L"))
            dark = gray < 200
            Hp, Wp = dark.shape
        for c in batch:
            b = c["box"]
            padt = padb = padl = padr = 16
            if not dry:
                bx0, by0, bx1, by1 = [int(round(v2 * S)) for v2 in b]
                xa, xb = max(0, bx0), min(Wp, bx1)
                ya, yb = max(0, by0), min(Hp, by1)
                span = dark[ya:yb, xa:xb]
                if span.size:
                    d = 0
                    for k in range(1, 22):
                        y = by0 - k
                        if y < 0 or dark[y, xa:xb].any():
                            break
                        d = k
                    padt = min(padt, max(0, d - 2))
                    d = 0
                    for k in range(1, 22):
                        y = by1 + k - 1
                        if y >= Hp or dark[y, xa:xb].any():
                            break
                        d = k
                    padb = min(padb, max(0, d - 2))
                    d = 0
                    for k in range(1, 22):
                        x = bx0 - k
                        if x < 0 or dark[ya:yb, x].any():
                            break
                        d = k
                    padl = min(padl, max(0, d - 2))
                    d = 0
                    for k in range(1, 22):
                        x = bx1 + k - 1
                        if x >= Wp or dark[ya:yb, x].any():
                            break
                        d = k
                    padr = min(padr, max(0, d - 2))
            c["pad"] = (padl, padt, padr, padb)

        for c in batch:
            name, cid, title = c["name"], c["cid"], c["title"]
            bx = c["box"]
            pl, pt, pr, pb = c["pad"]
            x0, y0, x1, y1 = [int(round(v2 * S)) for v2 in
                              (max(0, bx[0] - pl), max(0, bx[1] - pt), bx[2] + pr, bx[3] + pb)]
            if not dry:
                crop = img.crop((x0, y0, x1, y1))
                flags = edge_flags(crop)
                report[name] = dict(clipped=flags, box=[x0, y0, x1, y1])
                crop = trim_panel_edge(crop)
                crop = ImageOps.expand(crop, border=12, fill=(255, 255, 255))
                if crop.width > 1150:
                    crop = crop.resize((1150, int(crop.height * 1150 / crop.width)), Image.LANCZOS)
                tmp = os.path.join(CARD_DIR, "_tmp_" + name + ".jpg")
                crop.save(tmp, quality=86, optimize=True)
                os.replace(tmp, os.path.join(CARD_DIR, name + ".jpg"))
            else:
                w = min(1150, x1 - x0)
                crop = None
            out.append(dict(id=cid, cat=cat, title=title, section=page_title, page=int(p),
                            img="assets/cards/" + name + ".jpg?v=2",
                            w=min(1150, x1 - x0),
                            h=int((y1 - y0) * min(1.0, 1150 / max(1, x1 - x0)))))
            used.add(name + ".jpg")
        print("page", p, len(v["pieces"]), flush=True)

    data = {"categories": CATS, "cards": out}
    js = "window.DECK = " + json.dumps(data, ensure_ascii=False, separators=(",", ":")) + ";\n"
    if not dry:
        with open(os.path.join(ROOT, "data.js"), "w", encoding="utf-8") as f:
            f.write(js)
    print("cards", len(out), "missing titles", len(missing))
    print(missing[:40])
    for k in CATS:
        print(k, sum(1 for c in out if c["cat"] == k))
    # orphan images
    have = {f for f in os.listdir(CARD_DIR) if f.endswith(".jpg")}
    orphans = sorted(have - used)
    print("orphans", len(orphans))
    if orphans and not dry:
        for f in orphans:
            os.remove(os.path.join(CARD_DIR, f))
    json.dump(report, open(os.path.join(HERE, "export_report.json"), "w"), indent=1)
    print("clipped", sum(1 for v in report.values() if v["clipped"]))
    return out


if __name__ == "__main__":
    main(dry="--dry" in sys.argv)
