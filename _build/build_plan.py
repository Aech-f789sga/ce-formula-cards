"""Run plan_page over the whole PDF and cache the piece boxes."""
import json, os, sys
import build_cards as B
import plan

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "plan_all.json")

if __name__ == "__main__":
    data = {}
    for p in range(1, 137):
        pieces, cards, W, H = plan.plan_page(p)
        data[p] = dict(W=W, H=H, pieces=pieces, old=[ [int(v) for v in c] for c in cards])
        print(p, len(cards), len(pieces), flush=True)
    json.dump(data, open(OUT, "w"))
    print("done", sum(len(v["pieces"]) for v in data.values()))
