import json, os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
cards = json.load(open(os.path.join(HERE, "cards_raw.json")))
titles = json.load(open(os.path.join(HERE, "titles.json")))

missing = []
out = []
for c in cards:
    t = titles.get(str(c["page"]), {})
    title = t.get("titles", {}).get(str(c["idx"]))
    section = t.get("section", "")
    if not title:
        missing.append((c["page"], c["idx"]))
        title = f"Formula Set — p. {c['page']}"
    out.append({
        "id": f"p{c['page']:03d}-{c['idx']:02d}",
        "cat": c["category"],
        "title": title,
        "section": section,
        "page": c["page"],
        "img": "assets/cards/" + c["file"],
        "w": c["w"],
        "h": c["h"],
    })

CATS = {
    "geotech": {
        "name": "Geotechnical Engineering",
        "short": "Geotechnical",
        "blurb": "Soil properties, classification, permeability, consolidation, shear strength, earth pressure, and foundations.",
    },
    "hydraulics": {
        "name": "Hydraulics",
        "short": "Hydraulics",
        "blurb": "Fluid properties, hydrostatics, buoyancy, pipe flow, open channels, weirs, and pumps.",
    },
    "structural": {
        "name": "Principles of Structural Analysis and Design",
        "short": "Structural",
        "blurb": "Engineering mechanics, theory of structures, steel, concrete, and earthquake engineering.",
    },
    "math": {
        "name": "Math, Surveying, and Transportation Engineering",
        "short": "Math · Surv · Transpo",
        "blurb": "Algebra, geometry, calculus, statistics, surveying, transportation, and engineering economy.",
    },
}

data = {"categories": CATS, "cards": out}
js = "window.DECK = " + json.dumps(data, ensure_ascii=False, separators=(",", ":")) + ";\n"
with open(os.path.join(ROOT, "data.js"), "w", encoding="utf-8") as f:
    f.write(js)

print("cards", len(out), "missing titles", len(missing), missing[:10])
for k in CATS:
    print(k, sum(1 for c in out if c["cat"] == k))
print("size KB", round(len(js.encode()) / 1024, 1))
