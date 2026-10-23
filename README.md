# CE Board Review — Formula Deck & Term Quiz

Two study tools for the Philippine Civil Engineering Licensure Examination, built from review material and served as plain static files (no build step, no backend, no dependencies):

| Page | What it is |
| --- | --- |
| `index.html` | **Formula Deck** — 1,192 formula cards cropped straight out of Engr. APJO's RCE formula card PDF |
| `quiz.html` | **Term Quiz** — 1,059 definitions from the Engineereya definition-of-terms decks, as multiple choice or flashcards |

Both pages link to each other from the top bar.

---

## 1. Formula Deck (`index.html`)

Every card is a real crop taken from the source PDF — the handwritten topic heading plus its formulas — so what you flip to is exactly what is on the review card.

**1,192 cards**, split into the four areas the deck is organised by:

| Area | Cards |
| --- | --- |
| Geotechnical Engineering | 128 |
| Hydraulics | 137 |
| Principles of Structural Analysis and Design | 486 |
| Math, Surveying & Transportation Engineering | 441 |

Panels that stack several unrelated formulas are cut into one card per formula, and every crop is grown out until none of its own ink is sliced off.

- **Front** = topic title. Click the card or press `Space` to flip to the formula crop.
- **Zoom** opens the crop full-screen for reading small subscripts.
- **Category tabs** switch decks; *All decks* mixes them.
- **Browse** opens a drawer grouped by section (e.g. *Properties of Soil*, *Steel Design*, *Algebra*) with search.
- **Filters**: All / Unseen / Review / Known.
- **Still learning / Got it** marks are saved in `localStorage`, with a progress ring and bar per deck.

Keyboard: `←` `→` navigate · `Space` flip · `K` known · `R` review · `S` shuffle · `B` browse.

Every card has a shareable link (`index.html#p033-00`), so a specific formula can be sent to someone directly.

---

## 2. Term Quiz (`quiz.html`)

**1,059 term/definition pairs** from six decks:

| Deck | Terms |
| --- | --- |
| Geotechnical | 150 |
| Hydraulics | 101 |
| Structural | 99 |
| Transportation | 303 |
| Highway | 240 |
| Ports & Harbor | 166 |

Two modes, switched from the segmented control above the card:

### Multiple choice
The definition is shown and you pick the matching term from four choices. The three wrong choices are **not random** — they are drawn from the terms most easily confused with the answer: same section first, then terms that share wording, then definitions that overlap. So *Liquid Limit* is offered against *Plastic Limit*, *Shrinkage Limit* and *Atterberg's Limit*; *Berth* against *Wharf*, *Pier* and *Mole*; *Ductility* against *Toughness*, *Stiffness* and *Resilience*.

Answer with the mouse or keys `1`–`4`. A correct answer advances on its own; a wrong one shows the right term and files the card into **Needs review**. Score and missed count live in the top right.

### Flashcards
Flip between the two directions with **Term → Definition** / **Definition → Term** — the toggle changes which side starts face up.

- **Next / Previous** move through the deck.
- **Know** takes the card out of the session — you will not see it again until you reload.
- **Don't know** highlights the card and drops it back in about four cards later, so it keeps coming back until you know it.
- Marked cards show a *needs review* badge on the back, and a **Needs review** chip appears in the deck bar to filter straight to them.

Keyboard: `Space` flip · `←` `→` prev / next · `K` know · `X` don't know · `M` switch mode · `1`–`4` answer.

Progress is per device in `localStorage`: the *know* marks are session-only by design, while the *don't know* marks persist so you can pick the review pile back up tomorrow.

---

## Layout

```
index.html          formula deck (HTML + CSS + JS, no dependencies)
quiz.html           term quiz (HTML + CSS + JS, no dependencies)
data.js             formula deck data: 1,192 cards
terms.js            quiz data: 1,059 terms + precomputed confusion candidates
assets/cards/*.jpg  the cropped formula images
_build/             reproducible pipelines (Python + PyMuPDF)
```

## How the formula cards were cut

`_build/build_cards.py` is not a naive page-splitter. For each PDF page it:

1. finds the actual formula boxes via contour detection (aspect ratio + fill ratio + border darkness, so decorative pills and header bars are rejected);
2. groups boxes that belong to one topic — stacked boxes, or side-by-side boxes in the same row;
3. walks upward from each group to pick up its handwritten heading, and only treats it as a new card when the heading is actually written in colour;
4. clusters boxes into columns, then widens each crop to the sibling notes in its own column band — never across the gutter into the next card;
5. crops at 200 dpi and trims to content.

That first pass merged anything that shared a panel, so a second pass (`_build/plan.py` → `build_plan.py`) re-reads every panel and separates it:

1. **panel borders** — the first 70 px of each crop are scanned for a full-height / full-width ink line and the box is inset past it, so a border is never mistaken for content;
2. **topic boundaries** — a split is placed on a wide blank band (≥ 44 px at 150 dpi) that has real content above and below, or on a coloured heading run that sits outside every detected box; panels that stack four or five unrelated formulas become four or five cards;
3. **gap-bridging growth** — each piece then grows outward stroke by stroke (bridging letter gaps up to 12 px) until it reaches blank paper, blocked by the *core* of its neighbours rather than their loose boxes, with an overlap rollback so a grown piece never swallows another card.

`_build/growfix.py` then writes `boxes.json`: it snaps shared boundaries onto the nearest blank row, and grows any edge that still slices a glyph. `_build/export2.py` crops at 200 dpi, and pads each side only as far as the nearest foreign ink — so a crop shows its own content and nothing of the card next to it.

Hand corrections live in `_build/fixes.json` (`box`, `expand`, `union`, `drop`, `title`) and `_build/drop.json`.

```bash
python -m pip install pymupdf pillow opencv-python-headless numpy
python _build/build_plan.py    # plan_all.json: the piece boxes for every page
python _build/growfix.py       # boxes.json: boundary snapping + edge growth
python _build/export2.py       # assets/cards/*.jpg + data.js
```

`_build/overlay2.py` and `_build/pairov.py` draw crop boxes back onto the page if you want to check a boundary visually.

## How the terms were parsed

The definition PDFs mark each term in a bold font, so `_build/parse_terms.py` splits on font weight rather than guessing at dashes: the bold run at the start of a line is the term, the regular text after it is the definition, and a bold line with no definition is a section banner. It also unwraps terms that broke across lines, strips list numbering, drops bold sentence fragments that are really headings, and splits the combined highway deck into *Highway* and *Ports & Harbor* at page 26.

`_build/build_terms.py` cleans the text and precomputes, for every term, the 16 terms it is most easily confused with — same section, shared term wording, overlapping definition wording — which is what the multiple-choice options are drawn from.

```bash
python _build/parse_terms.py   # PDFs -> _build/terms_raw.json
python _build/build_terms.py   # -> terms.js
```

`terms.js` is committed, so the site works without ever running these.

## Deploying

The repo is a plain static site. On Vercel: import the repo, framework preset **Other**, no build command, output directory `.` — then `/` serves the formula deck and `/quiz.html` the term quiz. Any static host works the same way; you can also just open `index.html` locally.

## Credit

- **Formulas** — **Engr. Aleah Pearl Javier Once, RCE 2024** ("Engr. APJO"). Her formula card deck is the source of all 1,192 formula cards; the handwriting and every equation on them are hers.
- **Terms** — **Engineereya's Vlog**, whose definition-of-terms decks (Geotechnical, Fluid Mechanics & Hydraulics, Structural & Construction, Transportation, Highway & Ports/Harbor) are the source of all 1,059 definitions.

Both credits are also shown at the bottom of their page on the site. This repo only re-presents that material as interactive study tools; the engineering content is theirs. Terms are reproduced as written in the source PDFs, including their wording and any source typos.
