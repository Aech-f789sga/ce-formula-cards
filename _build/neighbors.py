"""Show a card's neighbours on its page so a fix can be written."""
import json, sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
plan_all = json.load(open(os.path.join(HERE, "plan_all.json")))

for arg in sys.argv[1:]:
    cid = arg
    page = int(cid[1:4])
    v = plan_all[str(page)]
    target = None
    for q in v["pieces"]:
        nm = f"p{page:03d}-{q['src']:02d}" + ("" if q["pi"] == 0 else chr(97 + q["pi"]))
        if nm == cid:
            target = (nm, q["box"])
    if not target:
        print(cid, "not found")
        continue
    nm, b = target
    print(f"\n{nm} box={[int(x) for x in b]}  w={b[2]-b[0]} h={b[3]-b[1]}")
    for q in v["pieces"]:
        n2 = f"p{page:03d}-{q['src']:02d}" + ("" if q["pi"] == 0 else chr(97 + q["pi"]))
        if n2 == nm:
            continue
        c = q["box"]
        if c[2] < b[0] - 200 or c[0] > b[2] + 200:
            continue
        if c[3] < b[1] - 200 or c[1] > b[3] + 200:
            continue
        rel = []
        if c[0] >= b[2] - 5:
            rel.append(f"right gap={int(c[0]-b[2])}")
        if c[2] <= b[0] + 5:
            rel.append(f"left gap={int(b[0]-c[2])}")
        if c[1] >= b[3] - 5:
            rel.append(f"below gap={int(c[1]-b[3])}")
        if c[3] <= b[1] + 5:
            rel.append(f"above gap={int(b[1]-c[3])}")
        print(f"   {n2} {[int(x) for x in c]} {' '.join(rel)}")
