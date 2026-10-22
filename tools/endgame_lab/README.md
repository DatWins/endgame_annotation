# Benko's Endgame Lab (Chess Life 10/2008 – 12/2013) → interactive HTML + Kobo EPUB

63 two-page columns by GM Pal Benko. Same output and design as the Naroditsky (`tools/pipeline`) and
Tatev Abrahamyan (`tools/getting_to_work`) versions: an interactive web page per article (text left,
live board right, clickable moves), an EPUB per article (main line bold blue, diagrams, cover), and an
`index.html` library page. Page 2 of each column starts with **Benko's Bafflers** (two composed problems);
these become a "Benko's Bafflers" section with clickable puzzle diagrams. Their solutions were printed
elsewhere in the magazine and are not included.

Put the PDF here as `benko.pdf` and run `./make_all.sh`.

## What is special about this PDF

**Two kinds of diagrams.**
- Oct 2008 – Jul 2012 (PDF pages 1–92): diagrams are *typeset in a chess font* (DiagramTTUSCF), so the
  position can be read exactly from the characters: `K Q R L N P` = White king, queen, rook, bishop,
  knight, pawn; lower case = Black; `+`/`-` = empty squares. Pieces on dark squares are drawn as a
  zero-width "hole" glyph (`\x02`–`\x08`, `! " # $ % &`, or `z m t s v w`) plus the piece letter.
  - pdfplumber's per-character x positions **drift** after some glyphs in this font, so the board is
    read from **poppler's word boxes** (`pdftotext -bbox`, saved in `bbox/`), where hole glyphs don't
    advance and every other glyph moves one square.
  - The magazine itself sometimes printed a piece letter one square to the right of its hole (the hole
    shows as a "ghost" piece). The decoder moves such a letter back onto its hole; the game moves confirm it.
- Aug 2012 – Dec 2013 (pages 93–126): diagrams are pictures. They were read square by square using the
  labelled squares from the Tatev Abrahamyan diagrams (same Chess Life piece style) plus self-training;
  results are stored in `imgfens.json`. `verify_sheet.js` draws each picture next to its reading.
- Page origins differ between pages (mediabox offsets); the extractor uses each page's `bbox` offset.

**Text styles.** Body Bookman; main-line moves Akzidenz Grotesk Bold (2008–12) or FS Joey Bold (2012–13);
section titles Bookman Bold (or Joey Bold 10); game headers in italics / red Joey; diagram captions
Bookman Bold 7 or Joey capitals. Benko writes doubtful/interesting marks as `(?)` / `(!)`; the parser
accepts these after a move.

**Move checking.** `parse.js` replays every move with chess.js. Final run: 16,509 of 17,153 moves
linked (96%); the rest are threats, twin-study variants and typos in the magazine, shown as plain text.

## Files
- `extract_benko.py` (+ `extract_base.py`, `fontdia.py`): layout → `ext/*.json`, `fontfens.json`
- `prep.py` → `prep/`; `parse.js` → `model/`; `build_tt.js` + `template.html` → `site/articles/*.html`
- `epub_imgs.js`, `pack_epubs.py` → EPUBs; `thumbs.js`, `make_index.py` → `site/index.html`
- `arts.json`: article → PDF pages, month, title, file name
