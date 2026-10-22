#!/bin/bash
# Full rebuild: PDF -> structured text -> verified move trees -> HTML pages + EPUBs + library page
set -e
cd "$(dirname "$0")"
export NODE_PATH=$(npm root -g)
# poppler word boxes for the font-typeset diagrams (pdfplumber glyph positions drift in that font)
mkdir -p bbox; [ -f bbox/p92.html ] || for p in $(seq 1 92); do pdftotext -bbox -f $p -l $p benko.pdf bbox/p$p.html 2>/dev/null; done
python3 extract_benko.py > /dev/null 2>&1
python3 -c "import json;F=json.load(open('fontfens.json'));F.update(json.load(open('imgfens.json')));json.dump(F,open('fens.json','w'),indent=0)"
python3 prep.py > /dev/null
node parse.js | tail -1
rm -rf site epubsrc
node build_tt.js
node epub_imgs.js | tail -1
python3 quantize.py
python3 pack_epubs.py
node thumbs.js
python3 -c "
import json
d=json.load(open('index_data.json'))
arts=[{k:a[k] for k in ('num','slug','title','dek','author','issue','date','players')} for a in d]
for a in arts: a['column']='Endgame Lab'
json.dump(arts,open('site/articles.json','w'),indent=1,ensure_ascii=False)"
python3 make_index.py site
