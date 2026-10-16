# Chess Life column PDF → interactive HTML + Kobo EPUB

This folder turns a PDF of Chess Life columns into:

- an **interactive web page** per article: text on the left, a big live board on the right, every move clickable, step through main line and variations, choose between lines, flip the board, try your own moves, A−/A+ and dark mode;
- an **EPUB** per article for the Kobo: same text, main-line moves in **bold blue**, a diagram after each block of main-line moves, and a cover;
- an **index.html** library page with search, year links, and Read online / Download EPUB buttons.

It was first built for GM Daniel Naroditsky's *The Practical Endgame* (tools/pipeline) and adapted here
for WGM Tatev Abrahamyan's *Getting to Work* (Chess Life 2023–2025, 33 columns).

## How it works (the steps, in order)

| Step | Script | What it does |
|---|---|---|
| 1 | `extract_tt.py` (+ `extract_base.py`) | Reads `cols.pdf` with pdfplumber. Uses fonts, sizes and colours to tell apart body text (Source Serif), main-line moves (Source Sans bold), red game headers, section headings, diagram captions, drop caps, the title/subtitle/byline. Skips ads, pull quotes, sidebars. Writes `ext/<article>.json`. |
| 2 | `prep.py` | Joins lines into paragraphs, removes end-of-line hyphens, repairs split words, applies small fixes (`reorder.json`). Writes `prep/`. |
| 3 | diagram reading | Diagrams are cut from the PDF and read square by square (pieces grouped by shape, each group labelled once). Result: `fens.json` (one position per diagram). |
| 4 | `parse.js` | Finds every move in the text and replays it with chess.js, so each move is checked as legal. Builds a move tree per game, links diagrams to positions. Writes `model/`. Prints how many moves linked. |
| 5 | `build_tt.js` + `template.html` | Builds the interactive web pages (`site/articles/*.html`). |
| 6 | `epub_imgs.js`, `pack_epubs.py` | Renders diagram images and covers, packs EPUB 3 files (with NCX for Kobo). |
| 7 | `thumbs.js`, `make_index.py` | Board thumbnails and the library `index.html`. |

`make_all.sh` runs steps 1–2 and 4–7 in one go (step 3's `fens.json` is already saved).

## Small fix files (edit these, then run `./make_all.sh`)

- `arts.json` — which PDF pages belong to which article (0-based page numbers), title, month.
- `fens.json` — the position in each diagram. Fix a misread diagram here.
- `caption_fixes.json` — diagrams whose printed "White/Black to move" caption is a misprint.
- `reorder.json` — blocks printed out of reading order (e.g. a game header placed after its first moves).
- `img_dias.json` — diagrams with drawn lines/arrows; these keep the original picture instead of a redrawn board.
- `extract_tt.py` → `CROPS` (where a "continued from page N" part sits on a back page), `FIGS` (photos/screenshots to keep), `EXCLUDE` (ad boxes on article pages).

## Requirements

Python 3 with `pdfplumber`, `numpy`, `Pillow`; Node.js with `playwright` (Chromium) for rendering images.
`lib/chess.js` (chess.js 0.10, BSD) and `lib/pieces.css` (lichess "cburnett" pieces) are included.

## Adapting to a new column or author

1. Put the PDF in this folder as `cols.pdf` and list the articles in `arts.json`.
2. Check the fonts: `python3 -c "import pdfplumber; ..."` — if the magazine uses different fonts, adjust
   `OK_FONTS` and the `sans` test in `extract_base.py` (`style_of`) and the rules in `line_kind`.
3. Re-read the diagrams for `fens.json` (see the Naroditsky `tools/pipeline/classify.py` for the method).
4. Change the column name / author in `build_tt.js`, `epub_imgs.js`, `pack_epubs.py`, `make_index.py`, `template.html`.
5. Run `./make_all.sh`, open a few pages, and look at the "failed runs" list from `parse.js`.
