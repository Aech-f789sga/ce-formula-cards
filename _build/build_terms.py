"""Turn terms_raw.json into terms.js for the quiz page.

Besides cleaning the text, this precomputes each term's "near" list: the other
terms that are most easily confused with it (same section first, then shared
wording in the term, then overlapping wording in the definition). The page
draws its three wrong choices from that list, so the distractors are related
or opposite rather than random.
"""

import json
import math
import re

STOP = set(
    """a an the of to in for on at by with from and or is are was were be been being
    that this these those it its as which who whom whose when where while than then
    can may shall will would should could not no nor but if so such into over under
    between within without about above below more most less least other another
    same each any all both few many some own only very too also use used using
    """.split()
)

ENUM = re.compile(r"^\s*(?:\d{1,2}|[A-Za-z]|[IVXivx]{1,4})\s*[.)]\s+")
DASHES = str.maketrans({"–": "-", "—": "-", "’": "'", "‘": "'", "“": '"', "”": '"'})


def tokens(s):
    return {w for w in re.findall(r"[a-z0-9]+", s.lower()) if len(w) > 2 and w not in STOP}


def tidy(term, body):
    term = ENUM.sub("", term).strip()
    term = re.sub(r"\s+", " ", term)
    body = re.sub(r"\s+", " ", body).strip()
    body = re.sub(r"\s*·\s*(?=[a-z(])", "; ", body)
    body = re.sub(r"\s+([,.;:])", r"\1", body)
    if body and body[0].islower():
        body = body[0].upper() + body[1:]
    if body and not body.endswith((".", "!", "?")):
        body += "."
    return term, body


CATS = {
    "geotech": ("Geotechnical", "#2f6b1e"),
    "hydraulics": ("Hydraulics", "#1c4f7c"),
    "structural": ("Structural", "#a4700a"),
    "transport": ("Transportation", "#c2185b"),
    "highway": ("Highway", "#8a5a1b"),
    "ports": ("Ports & Harbor", "#1f6f6b"),
}

KEY = {
    "Geotechnical": "geotech",
    "Hydraulics": "hydraulics",
    "Structural": "structural",
    "Transportation": "transport",
    "Highway": "highway",
    "Ports": "ports",
}


def main():
    raw = json.load(open("terms_raw.json", encoding="utf-8"))

    items = []
    for term, body, section, page, cat in raw:
        term, body = tidy(term.translate(DASHES), body.translate(DASHES))
        if not term or len(term) > 60 or len(body) < 30:
            continue
        items.append(
            {
                "cat": KEY[cat],
                "sec": section.translate(DASHES) if section else "",
                "t": term,
                "d": body,
                "p": page,
            }
        )

    # the source deck lists the ideal-fluid and real-fluid bullets under each
    # other's heading; put each description back with its own term
    for a in items:
        if a["t"] == "Ideal fluids":
            for b in items:
                if b["t"] == "Real Fluids" and b["cat"] == a["cat"]:
                    a["d"], b["d"] = b["d"], a["d"]

    # ---- confusion candidates -------------------------------------------------
    toks = [tokens(i["t"]) for i in items]
    dtoks = [tokens(i["d"]) for i in items]
    by_cat = {}
    for idx, it in enumerate(items):
        by_cat.setdefault(it["cat"], []).append(idx)

    for idx, it in enumerate(items):
        scored = []
        pool = by_cat[it["cat"]]
        for j in pool:
            if j == idx:
                continue
            other = items[j]
            s = 0.0
            if other["sec"] and other["sec"] == it["sec"]:
                s += 4.0
            a, b = toks[idx], toks[j]
            if a and b:
                s += 6.0 * len(a & b) / len(a | b)
            da, db = dtoks[idx], dtoks[j]
            if da and db:
                s += 5.0 * len(da & db) / len(da | db)
            # terms of similar shape are easier to mix up than "Wharf" vs "Port"
            s -= 0.35 * abs(len(it["t"]) - len(other["t"]))
            s += 0.8 if abs(len(it["t"].split()) - len(other["t"].split())) <= 1 else 0
            scored.append((s, j))
        scored.sort(reverse=True)
        it["near"] = [j for _, j in scored[:16]]

    for n, it in enumerate(items):
        it["i"] = n

    cats = []
    for cid, (name, colour) in CATS.items():
        count = sum(1 for i in items if i["cat"] == cid)
        if count:
            cats.append({"id": cid, "name": name, "color": colour, "count": count})

    order = ["geotech", "hydraulics", "structural", "transport", "highway", "ports"]
    cats.sort(key=lambda c: order.index(c["id"]))

    payload = {"cats": cats, "items": items}
    js = "window.TERMS = " + json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + ";\n"
    open("../terms.js", "w", encoding="utf-8").write(js)

    print("items", len(items), "size", round(len(js) / 1024), "KB")
    for c in cats:
        print(f"  {c['name']:16s} {c['count']:4d}")

    # a quick look at the distractor quality for a few well-known terms
    for want in ("Void Ratio", "Liquid Limit", "Ductility", "Berth", "Alligator cracking"):
        for it in items:
            if it["t"] == want:
                near = ", ".join(items[j]["t"] for j in it["near"][:5])
                print(f"  {want:20s} -> {near}")
                break


if __name__ == "__main__":
    main()
