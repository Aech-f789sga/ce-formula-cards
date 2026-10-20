"""Parse term/definition pairs out of the Engineereya terms PDFs.

The term is the bold run at the start of a line and the definition is the
regular-face text that follows it, so the split is driven by font weight.
Fully-bold lines with no definition are section banners ("Soil Properties"),
except when a single-word banner is a term that simply wrapped ("Submerged" /
"Density").
"""

import json
import os
import re

import pymupdf

BASE = r"C:\Users\gamao\Downloads\drive-download-20261018T054114Z-1-001"

FILES = {
    "geotech": ("GEOTECHNICAL ENGINEERING TERMS.pdf", "Geotechnical"),
    "hydraulics": ("FLUID MECHANICS  AND HYDRAULICS TERMS.pdf", "Hydraulics"),
    "structural": ("STRUCTURAL ENGINEERING  AND CONSTRUCTION TERMS.pdf", "Structural"),
    "transport": ("Definition of Terms.pdf", "Transportation"),
    "highway": (
        "HIGHWAY AND TRANSPORTAION ENGINEERING TERMS & PORTS AND HARBOR TERMS.pdf",
        "Highway",
    ),
}

NOISE = re.compile(r"^(engineereya.{0,14}|definition of terms.*|page \d+|\d+)$", re.I)
EDGE = re.compile(r"^[\s\-–—:.•]*|[\s\-–—:.]+$")


def clean(s):
    s = s.replace("\uf0a7", "•").replace("\uf0b7", "•").replace("\u00a0", " ")
    s = re.sub(r"[ \t]+", " ", s)
    return s.strip()


def join_spans(pieces):
    """Concatenate span texts, inserting a space only where one is missing."""
    out = ""
    for piece in pieces:
        if out and piece and out[-1].isalnum() and piece[0].isalnum():
            out += " "
        out += piece
    return out


def lines_of(doc):
    """(page_no, [spans]) in content order, skipping display-size headers."""
    for pno, page in enumerate(doc):
        for block in page.get_text("dict")["blocks"]:
            if block["type"] != 0:
                continue
            for line in block["lines"]:
                spans = [
                    (bool(s["flags"] & 16) or "Bold" in s["font"], s["text"], s["size"])
                    for s in line["spans"]
                    if s["text"].strip()
                ]
                spans = [s for s in spans if s[2] <= 15]
                if spans:
                    yield pno, spans


STOP_TAIL = {
    "in", "of", "the", "a", "an", "to", "for", "and", "or", "are", "is", "as",
    "by", "on", "at", "with", "from", "that", "which", "include", "includes",
    "following", "be", "was", "were", "shall", "may", "can", "will", "used",
}
SPLIT_DASH = re.compile(r"\s+[-–—]\s*")


def term_ok(term):
    """Reject bold sentence fragments that are really headings or bullets."""
    words = term.split()
    if not words or len(words) > 6 or len(term) > 52:
        return False
    if term[-1] in ";:,.":
        return False
    if words[-1].lower().strip(",.;:") in STOP_TAIL:
        return False
    if not (term[0].isupper() or term[0].isdigit()):
        return False
    if sum(c.isalpha() for c in term) < 3:
        return False
    return True


def section_ok(text):
    return 1 <= len(text.split()) <= 6 and len(text) <= 44 and term_ok(text)


def build(doc, cat):
    raw = []  # [term, def, section, page, def_started_with_dash]
    cur = None

    for pno, spans in lines_of(doc):
        text = clean(join_spans([s[1] for s in spans]))
        if NOISE.match(text):
            continue

        if spans[0][0]:
            term_parts, rest_parts = [], []
            for bold, t, _ in spans:
                (term_parts if bold and not rest_parts else rest_parts).append(t)
            bold_run = clean(join_spans(term_parts))
            # "Broken Line – a type of line that ..." -> term stops at the dash
            m = SPLIT_DASH.search(bold_run)
            if m and m.start() > 2:
                term, inline = bold_run[: m.start()], bold_run[m.end():]
                rest_parts = [inline] + rest_parts
            else:
                term = bold_run
            term = EDGE.sub("", term)
            body = clean(join_spans(rest_parts))
            if not term:
                continue
            cur = [term, body, pno + 1, body.lstrip().startswith(("-", "–", "—"))]
            raw.append(cur)
        elif cur is not None:
            cur[1] = (cur[1] + " " + text).strip()

    out = []
    i = 0
    section = ""
    while i < len(raw):
        term, body, page, dashed = raw[i]
        body = EDGE.sub("", body)
        if not body:
            nxt = raw[i + 1] if i + 1 < len(raw) else None
            if nxt and len(term.split()) == 1 and nxt[3]:
                merged = term + " " + nxt[0]
                out.append([merged, EDGE.sub("", nxt[1]), section, page, cat])
                i += 2
                continue
            if section_ok(term):
                section = term
            i += 1
            continue
        if len(body) >= 15 and term_ok(term):
            out.append([term, body, section, page, cat])
        i += 1

    return out


def main():
    rows = []
    for key, (fname, cat) in FILES.items():
        got = build(pymupdf.open(os.path.join(BASE, fname)), cat)
        if key == "highway":
            # the deck carries two subjects: highway engineering, then ports & harbor
            for r in got:
                r[4] = "Ports" if r[3] >= 26 else "Highway"
        print(f"{key:11s} {len(got):4d}")
        rows.extend(got)

    seen = set()
    clean_rows = []
    for term, body, section, page, cat in rows:
        key = (cat, re.sub(r"[^a-z0-9]", "", term.lower()))
        if key in seen or len(body) < 30:
            continue
        seen.add(key)
        body = re.sub(r"\s*[•·]\s*", " · ", body).strip(" ·")
        clean_rows.append([term, body, section, page, cat])

    json.dump(clean_rows, open("terms_raw.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("total", len(clean_rows))
    for c in sorted({r[4] for r in clean_rows}):
        print(f"  {c:15s} {sum(1 for r in clean_rows if r[4] == c)}")


if __name__ == "__main__":
    main()
