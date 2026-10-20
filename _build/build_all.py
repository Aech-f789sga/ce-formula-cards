import os, json, sys
import build_cards as B

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_JSON = os.path.join(HERE, "cards_raw.json")

if __name__ == "__main__":
    os.makedirs(B.CARD_DIR, exist_ok=True)
    all_cards = []
    sections = {}
    for p in range(1, 137):
        cat = B.page_category(p)
        if cat is None:
            print("skip", p)
            continue
        cards, W, H = B.build_page(p)
        info = B.export(p, cards, W, H)
        for c in info:
            c["category"] = cat
            all_cards.append(c)
        print(p, cat, len(info))
    with open(OUT_JSON, "w") as f:
        json.dump(all_cards, f, indent=1)
    print("total", len(all_cards))
