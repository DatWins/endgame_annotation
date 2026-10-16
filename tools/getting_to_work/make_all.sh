#!/bin/bash
# Full rebuild: PDF -> structured text -> verified move trees -> HTML pages + EPUBs + library page
set -e
cd "$(dirname "$0")"
export NODE_PATH=$(npm root -g)
python3 extract_tt.py > /dev/null
python3 prep.py > /dev/null
node parse.js | tail -1
rm -rf site epubsrc
node build_tt.js
node epub_imgs.js | tail -1
python3 pack_epubs.py
node thumbs.js
python3 -c "
import json
d=json.load(open('index_data.json'))
arts=[{k:a[k] for k in ('num','slug','title','dek','author','issue','date','players')} for a in d]
for a in arts: a['column']='Getting to Work'
json.dump(arts,open('site/articles.json','w'),indent=1,ensure_ascii=False)"
python3 make_index.py site
