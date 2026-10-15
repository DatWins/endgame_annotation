// Renders diagram PNGs (blue-grey board, coordinates outside) for the EPUB
const fs = require('fs'); const { chromium } = require('playwright');
const { makeBody, nodes } = require('./build.js');
const { dias } = makeBody('epub');
const css = fs.readFileSync('cg/assets/chessground.cburnett.css', 'utf8');
const P = { pawn: 'P', bishop: 'B', knight: 'N', rook: 'R', queen: 'Q', king: 'K' };
let pc = ''; for (const m of css.matchAll(/piece\.(\w+)\.(white|black)\s*\{\s*background-image:\s*(url\([^)]*\))/g)) pc += `.pc.${m[2][0]}${P[m[1]]}{background-image:${m[3]}}\n`;
const files = 'abcdefgh';
function board(id) {
  const n = nodes[id], g = []; n.fen.split(' ')[0].split('/').forEach((r, ri) => { let c = 0; for (const ch of r) { if (/\d/.test(ch)) c += +ch; else g[ri * 8 + c++] = ch } });
  let sq = ''; for (let i = 0; i < 64; i++) { const r = i >> 3, c = i & 7, name = files[c] + (8 - r), p = g[i];
    const lm = n.from && (name === n.from || name === n.to);
    sq += `<div class="sq ${(r + c) % 2 ? 'd' : 'l'}${lm ? ' lm' : ''}">${p ? `<div class="pc ${p === p.toUpperCase() ? 'w' : 'b'}${p.toUpperCase()}"></div>` : ''}</div>` }
  return `<div class="bw" id="b_${id}"><div class="rk">${[8,7,6,5,4,3,2,1].map(x => `<span>${x}</span>`).join('')}</div><div class="bd">${sq}</div><div class="fl">${[...files].map(x => `<span>${x}</span>`).join('')}</div></div>`;
}
const html = `<html><head><style>${pc}
body{margin:0;background:#fff;font-family:Arial,sans-serif}
.bw{display:inline-grid;grid-template-columns:22px 400px;grid-template-rows:400px 22px;padding:4px 8px 4px 2px;background:#fff;margin:4px}
.bd{display:grid;grid-template-columns:repeat(8,1fr);grid-template-rows:repeat(8,1fr);border:2px solid #5b6f79}
.sq{position:relative}.l{background:#dee3e6}.d{background:#8ca2ad}
.lm::after{content:"";position:absolute;inset:0;background:rgba(155,199,0,.45)}
.pc{position:absolute;inset:0;background-size:100% 100%;z-index:1}
.rk{display:grid;grid-template-rows:repeat(8,1fr);font-size:15px;color:#333;align-items:center;text-align:center}
.fl{grid-column:2;display:grid;grid-template-columns:repeat(8,1fr);font-size:15px;color:#333;text-align:center;align-items:center}
</style></head><body>${dias.map(board).join('')}</body></html>`;
(async () => { fs.mkdirSync('epub/OEBPS/images', { recursive: true });
  const b = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium' });
  const p = await b.newPage({ deviceScaleFactor: 2 }); await p.setContent(html);
  for (const id of dias) await (await p.$('#b_' + id)).screenshot({ path: `epub/OEBPS/images/${id}.png` });
  await b.close(); console.log('rendered', dias.length); })();
