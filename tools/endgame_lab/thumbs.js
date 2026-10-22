// Board thumbnails for the library page (articles/<slug>.jpg)
const fs = require('fs'); const { chromium } = require('playwright');
const pc = fs.readFileSync('lib/pieces.css', 'utf8');
const data = JSON.parse(fs.readFileSync('index_data.json', 'utf8'));
function board(fen) { const g = []; fen.split(' ')[0].split('/').forEach((r, ri) => { let c = 0; for (const ch of r) { if (/\d/.test(ch)) c += +ch; else g[ri * 8 + c++] = ch } });
  let s = ''; for (let i = 0; i < 64; i++) { const r = i >> 3, c = i & 7, p = g[i]; s += `<div class="sq ${(r + c) % 2 ? 'd' : 'l'}">${p ? `<div class="pc ${p === p.toUpperCase() ? 'w' : 'b'}${p.toUpperCase()}"></div>` : ''}</div>` } return s; }
(async () => { const b = await chromium.launch(); const p = await b.newPage({ viewport: { width: 360, height: 360 } });
  for (const a of data) { if (!a.thumbFen) continue;
    await p.setContent(`<style>${pc} body{margin:0} .bd{width:360px;height:360px;display:grid;grid-template-columns:repeat(8,1fr)} .sq{position:relative}.l{background:#dee3e6}.d{background:#8ca2ad}.pc{position:absolute;inset:0;background-size:100% 100%}</style><div class="bd">${board(a.thumbFen)}</div>`);
    await p.screenshot({ path: `site/articles/${a.slug}.jpg`, type: 'jpeg', quality: 85 }); }
  await b.close(); console.log('thumbs', data.length); })();
