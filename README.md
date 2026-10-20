# CE Board Review — Formula Deck & Term Quiz

Two study tools for the Philippine Civil Engineering Licensure Examination, built from review material and served as plain static files (no build step, no backend, no dependencies):

| Page | What it is |
| --- | --- |
| `index.html` | **Formula Deck** — 971 formula cards cropped straight out of Engr. APJO's RCE formula card PDF |
| `quiz.html` | **Term Quiz** — 1,059 definitions from the Engineereya definition-of-terms decks, as multiple choice or flashcards |

Both pages link to each other from the top bar.

---

## 1. Formula Deck (`index.html`)

Every card is a real crop taken from the source PDF — the handwritten topic heading plus its formulas — so what you flip to is exactly what is on the review card.

**971 cards**, split into the four areas the deck is organised by:

| Area | Cards |
| --- | --- |
| Geotechnical Engineering | 102 |
| Hydraulics | 112 |
| Principles of Structural Analysis and Design | 399 |
| Math, Surveying & Transportation Engineering | 358 |

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
data.js             formula deck data: 971 cards
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

`build_data.py` then merges the crop boxes with the titles in `titles.json` and writes `data.js`.

```bash
python -m pip install pymupdf pillow opencv-python-headless numpy
python _build/build_all.py     # writes assets/cards/*.jpg + _build/cards_raw.json
python _build/build_data.py    # writes data.js
```

`_build/overlays.py` renders numbered QA overlays per page if you want to check crop boundaries visually.

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

- Formulas and handwriting: **FORMULA CARD (Engr. APJO)**, a review deck compiled by Engr. APJO for the Philippine CE board exam.
- Definitions: the **Engineereya** definition-of-terms decks (Geotechnical, Fluid Mechanics & Hydraulics, Structural & Construction, Transportation, Highway & Ports/Harbor).

This repo only re-presents that material as interactive study tools; the engineering content is theirs. Terms are reproduced as written in the source PDFs, including their wording and any source typos.
