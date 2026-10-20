# Formula Deck — Civil Engineering Board Review Flashcards

A single-page flashcard app built from **Engr. APJO's RCE formula card** deck (Philippine Civil Engineering Licensure Examination review). Every card is a real crop taken straight from the source PDF — the handwritten topic heading plus its formulas — so what you flip to is exactly what's on the review card.

**971 cards**, split into the four areas the deck is organised by:

| Area | Cards |
| --- | --- |
| Geotechnical Engineering | 102 |
| Hydraulics | 112 |
| Principles of Structural Analysis and Design | 399 |
| Math, Surveying & Transportation Engineering | 358 |

## Using it

Open `index.html` in any browser. No build step, no server, no dependencies — everything (including progress) stays on the device.

- **Front** = topic title. Click the card or press `Space` to flip to the formula crop.
- **Zoom** opens the crop full-screen for reading small subscripts.
- **Category tabs** switch decks; *All decks* mixes them.
- **Browse** opens a drawer grouped by section (e.g. *Properties of Soil*, *Steel Design*, *Algebra*) with search.
- **Filters**: All / Unseen / Review / Known.
- **Still learning / Got it** marks are saved in `localStorage`, with a progress ring and bar per deck.

Keyboard: `←` `→` navigate · `Space` flip · `K` known · `R` review · `S` shuffle · `B` browse.

Every card has a shareable link (`index.html#p033-00`), so a specific formula can be sent to someone directly.

## Layout

```
index.html          the whole app (HTML + CSS + JS, no dependencies)
data.js             deck data: 971 cards with category, section, title, crop size
assets/cards/*.jpg  the cropped formula images
_build/             reproducible crop pipeline (Python + PyMuPDF)
```

## How the cards were cut

`_build/build_cards.py` is not a naive page-splitter. For each PDF page it:

1. finds the actual formula boxes via contour detection (aspect ratio + fill ratio + border darkness, so decorative pills and header bars are rejected);
2. groups boxes that belong to one topic — stacked boxes, or side-by-side boxes in the same row;
3. walks upward from each group to pick up its handwritten heading, and only treats it as a new card when the heading is actually written in colour;
4. clusters boxes into columns, then widens each crop to the sibling notes in its own column band — never across the gutter into the next card;
5. crops at 200 dpi and trims to content.

`build_data.py` then merges the crop boxes with the titles in `titles.json` and writes `data.js`.

To re-cut from the source PDF:

```bash
python -m pip install pymupdf pillow opencv-python-headless numpy
python _build/build_all.py     # writes assets/cards/*.jpg + _build/cards_raw.json
python _build/build_data.py    # writes data.js
```

`_build/overlays.py` renders numbered QA overlays per page if you want to check crop boundaries visually.

## Credit

All formulas and handwriting come from **FORMULA CARD (Engr. APJO)** — a review deck compiled by Engr. APJO for the Philippine CE board exam. This repo only re-presents that material as interactive flashcards; the engineering content is theirs.
