// Render diagram PNGs and a cover for each article's EPUB
const fs = require('fs'); const { chromium } = require('playwright');
const pc = fs.readFileSync('lib/pieces.css', 'utf8');
const P = { pawn: 'P', bishop: 'B', knight: 'N', rook: 'R', queen: 'Q', king: 'K' };

const files = 'abcdefgh';
function board(id, fen, from, to, small) {
  const g = []; fen.split(' ')[0].split('/').forEach((r, ri) => { let c = 0; for (const ch of r) { if (/\d/.test(ch)) c += +ch; else g[ri * 8 + c++] = ch } });
  let sq = ''; for (let i = 0; i < 64; i++) { const r = i >> 3, c = i & 7, name = files[c] + (8 - r), p = g[i];
    const lm = from && (name === from || name === to);
    sq += `<div class="sq ${(r + c) % 2 ? 'd' : 'l'}${lm ? ' lm' : ''}">${p ? `<div class="pc ${p === p.toUpperCase() ? 'w' : 'b'}${p.toUpperCase()}"></div>` : ''}</div>` }
  return `<div class="bw" id="b_${id}"><div class="rk">${[8,7,6,5,4,3,2,1].map(x => `<span>${x}</span>`).join('')}</div><div class="bd">${sq}</div><div class="fl">${[...files].map(x => `<span>${x}</span>`).join('')}</div></div>`;
}
const STYLE = `<style>${pc}
body{margin:0;background:#fff;font-family:Arial,sans-serif}
.bw{display:inline-grid;grid-template-columns:22px 400px;grid-template-rows:400px 22px;padding:4px 8px 4px 2px;background:#fff;margin:4px}
.bd{display:grid;grid-template-columns:repeat(8,1fr);grid-template-rows:repeat(8,1fr);border:2px solid #5b6f79}
.sq{position:relative}.l{background:#dee3e6}.d{background:#8ca2ad}
.lm::after{content:"";position:absolute;inset:0;background:rgba(155,199,0,.45)}
.pc{position:absolute;inset:0;background-size:100% 100%;z-index:1}
.rk{display:grid;grid-template-rows:repeat(8,1fr);font-size:15px;color:#333;align-items:center;text-align:center}
.fl{grid-column:2;display:grid;grid-template-columns:repeat(8,1fr);font-size:15px;color:#333;text-align:center;align-items:center}
</style>`;
(async () => {
  const b = await chromium.launch();
  const dirs = fs.readdirSync('epubsrc').sort();
  const only = process.argv[2];
  for (const d of dirs) {
    if (only && !d.startsWith(only)) continue;
    const B = JSON.parse(fs.readFileSync(`epubsrc/${d}/body.json`, 'utf8'));
    const out = `epubsrc/${d}/OEBPS/images`; fs.mkdirSync(out, { recursive: true });
    const p = await b.newPage({ deviceScaleFactor: 2 });
    await p.setContent(`<html><head>${STYLE}</head><body>${B.imgs.map(x => board(x.id, x.fen, x.from, x.to)).join('')}</body></html>`);
    for (const x of B.imgs) await (await p.$('#b_' + x.id)).screenshot({ path: `${out}/${x.id}.png` });
    await p.close();
    // cover
    const c = await b.newPage({ viewport: { width: 800, height: 1200 } });
    const cb = B.cover ? `<div style="transform:scale(1.1);transform-origin:top center">${board('cv', B.cover.fen, '', '')}</div>` : '';
    await c.setContent(`<html><head>${STYLE}</head><body style="margin:0;width:800px;height:1200px;background:#1f4436;color:#fff;font-family:Georgia,serif;display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center">
<div style="font-family:Arial;letter-spacing:4px;font-size:22px;color:#c9e6d8">ENDGAME LAB · No. ${B.num}</div>
<div style="font-family:Arial;font-weight:800;font-size:${B.title.length > 24 ? 58 : 72}px;line-height:1.05;margin:24px 50px 12px">${B.title}</div>
${B.dek ? `<div style="font-size:26px;font-style:italic;color:#e3f3ea;margin:0 70px 18px">${B.dek}</div>` : ''}<div style="font-size:28px;color:#e3f3ea;margin-bottom:34px">GM Pal Benko</div>${cb}
<div style="font-family:Arial;font-size:22px;color:#c9e6d8;margin-top:40px">Chess Life · ${B.issue}</div></body></html>`);
    await c.screenshot({ path: `${out}/cover.png` }); await c.close();
    process.stdout.write('.');
  }
  await b.close(); console.log('\nimages done');
})();
