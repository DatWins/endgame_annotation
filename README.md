# The Practical Endgame — GM Daniel Naroditsky (Chess Life, 2014–2020)

All 70 columns, each published two ways:
- `articles/<slug>.html` — web page with a live board: click any move in the text, step through the main line and variations with the arrow keys, flip the board, or try your own moves.
- `articles/<slug>.epub` — e-reader edition (Kobo): same text, main line in bold blue, a diagram after each main-line move block.

`index.html` is the library home page, generated from `articles.json` by `tools/make_index.py`.

## How the articles were built (`tools/pipeline/`)
1. `dias.py` crops every diagram from the PDFs; `classify.py` / `relabel.py` read the position square by square (`fens.json`, with corrections in `fen_overrides.json`).
2. `fontfix.py` recovers text set in fonts without a character map (`cidmap.json`).
3. `extract.py` reads columns, paragraphs, headings, game headers, captions and the Practicum box; `prep.py` cleans hyphenation and spacing.
4. `parse.js` finds every move in the text and attaches it to a verified move tree (chess.js legality check).
5. `build_all.js` writes the HTML pages; `epub_imgs.js` + `pack_epubs.py` render diagrams and package the EPUBs.
