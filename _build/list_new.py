"""List new pieces (pi>0) in deck order, in batches, for titling."""
import json, sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
plan_all = json.load(open(os.path.join(HERE, "plan_all.json")))
drop = set(json.load(open(os.path.join(HERE, "drop.json"))))
start, count = int(sys.argv[1]), int(sys.argv[2])
items = []
for p in sorted(plan_all, key=int):
    for q in plan_all[p]["pieces"]:
        if q["pi"] == 0:
            continue
        nm = f"p{int(p):03d}_{q['src']:02d}{chr(97 + q['pi'])}"
        if nm in drop:
            continue
        items.append(nm)
print(len(items), "total")
for i, nm in enumerate(items[start:start + count], start=start):
    print(i, nm)
