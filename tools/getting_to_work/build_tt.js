// Generate interactive HTML + EPUB sources for every article model
const fs = require('fs'), path = require('path');
const OUT = __dirname + '/site';
const ARTS = Object.fromEntries(JSON.parse(fs.readFileSync('arts.json', 'utf8')).map(a => [a.slug, a]));
const MONTHS = ['January','February','March','April','May','June','July','August','September','October','November','December'];
const tpl = fs.readFileSync('template.html', 'utf8');

const P = { pawn: 'P', bishop: 'B', knight: 'N', rook: 'R', queen: 'Q', king: 'K' };
const pieceCss = fs.readFileSync('lib/pieces.css', 'utf8');
const chessjs = fs.readFileSync('lib/chess.js', 'utf8');
const esc = s => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
const SMALL = new Set(['a','an','the','and','or','of','in','on','for','to','at','by','vs','vs.','with','from']);
function titleCase(s) {
  if (s !== s.toUpperCase()) return s;
  return s.toLowerCase().split(/(\s+)/).map((w, i) => (i > 0 && SMALL.has(w)) ? w : w.charAt(0).toUpperCase() + w.slice(1)).join('')
    .replace(/\b(Ii|Iii|Iv)\b/g, m => m.toUpperCase()).replace(/\b(Gm|Im|Fm|Us|U\.s\.)\b/g, m => m.toUpperCase());
}
function slugify(s) { return s.toLowerCase().replace(/[’'“”"!?.,:()]/g, '').replace(/&/g, 'and').replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, ''); }
function fixSan(s) {
  s = s.replace(/[.,;]+$/, '');
  if (/^[KQRBN][A-Ha-hXx1-8]/i.test(s) && /^[KQRBN]/.test(s) && s.length > 2) return s[0] + s.slice(1).toLowerCase().replace(/=([qrbn])/, (m, p) => '=' + p.toUpperCase());
  return s.toLowerCase().replace(/=([qrbn])/, (m, p) => '=' + p.toUpperCase()).replace(/^o-o(-o)?/, m => m.toUpperCase());
}
function capText(cap, node, nodes) {
  cap = (cap || '').replace(/\s+/g, ' ').trim().replace(/A N ALY SIS AFT E R/i, 'ANALYSIS AFTER');
  const analysis = /ANALYSIS/i.test(cap);
  const tm = cap.match(/(WHITE|BLACK) TO MOVE/i);
  let main = '';
  if (node && node.parent) main = 'After ' + node.label + (node.ann || '');
  else {
    const m = cap.match(/(\d{1,3})\s*((?:\s*[.…])+)\s*([A-Za-z0-9=+#!?-]+)/);
    if (m) { const black = (m[2].match(/\./g) || []).length >= 3 || m[2].includes('…'); main = 'After ' + m[1] + (black ? '...' : '.') + fixSan(m[3]); }
  }
  let out = main;
  if (tm) out = (out ? out + ' · ' : '') + (tm[1].toUpperCase() === 'WHITE' ? 'White' : 'Black') + ' to move';
  if (analysis) out = out ? out + ' (analysis)' : 'Analysis diagram';
  if (!out && cap) out = cap.charAt(0) + cap.slice(1).toLowerCase();
  return out;
}

const IMGDIA = new Set(fs.existsSync('img_dias.json') ? JSON.parse(fs.readFileSync('img_dias.json', 'utf8')) : []);
const files = fs.readdirSync('model').filter(f => f.endsWith('.json'));
const arts = files.map(f => { const A = JSON.parse(fs.readFileSync('model/' + f, 'utf8')); const a = ARTS[A.name]; A.ym = a.ym; A.issue = MONTHS[+a.ym.slice(5) - 1] + ' ' + a.ym.slice(0, 4); A.fixedTitle = a.title; return A; });
arts.sort((a, b) => a.ym.localeCompare(b.ym));
fs.mkdirSync(OUT + '/articles', { recursive: true });
const index = [];
arts.forEach((A, k) => {
  const num = k + 1;
  const title = A.header.title.replace(/\s+/g, ' ').trim() || A.fixedTitle;
  const slug = A.name;
  A.slug = slug; A.num = num;
  const N = A.nodes;
  // ---- ROOTS info ----
  const ROOTS = {}; let curHeading = '', players = [];
  const diaCap = {};
  const firstPlayers = [];
  A.blocks.forEach(b => {
    if (b.type === 'gamehead' && !/\(\d{3,4}\)|^(GM|IM|FM|WGM|WIM|WFM|NM|CM)\s|\d{2}\.\d{2}\.\d{4}|\(\d+\)/.test(b.html.replace(/<[^>]+>/g, ''))) { players = []; }
    if (b.type === 'heading') { curHeading = titleCase(b.html.replace(/<[^>]+>/g, '')); players = []; }
    if (b.type === 'gamehead' && /\(\d{3,4}\)|^(GM|IM|FM|WGM|WIM|WFM|NM|CM)\s/.test(b.html.replace(/<[^>]+>/g, ''))) { players.push(b.html.replace(/<[^>]+>/g, '')); if (firstPlayers.length < 2 && players.length <= 2) firstPlayers.push(b.html.replace(/<[^>]+>/g, '')); }
    if ((b.type === 'ml' || b.type === 'p') && b.html) {
      const who = players.length >= 2 ? players[0].replace(/\s*\(.*$/, '').replace(/^(GM|IM|FM|WGM|WIM|WFM|NM|CM)\s+/, '') + ' – ' + players[1].replace(/\s*\(.*$/, '').replace(/^(GM|IM|FM|WGM|WIM|WFM|NM|CM)\s+/, '') : curHeading;
      for (const m of b.html.matchAll(/data-id="(n\d+)"/g)) { let r = m[1]; while (N[r].parent) r = N[r].parent; if (!ROOTS[r]) ROOTS[r] = [who, '']; }
    }
    if (b.type === 'dia') {
      const id = A.diaNode[b.name]; if (!id) return;
      let r = id; while (N[r].parent) r = N[r].parent;
      const who = players.length >= 2 ? players[0].replace(/\s*\(.*$/, '').replace(/^(GM|IM|FM|WGM|WIM|WFM|NM|CM)\s+/, '') + ' – ' + players[1].replace(/\s*\(.*$/, '').replace(/^(GM|IM|FM|WGM|WIM|WFM|NM|CM)\s+/, '') : curHeading;
      if (!ROOTS[r]) ROOTS[r] = [who, r === id ? capText(b.caption, N[id], N) : ''];
      diaCap[b.name] = capText(b.caption, N[id], N);
    }
  });
  const prac = A.practicum;
  if (prac) prac.problems.forEach((pb, i) => { if (pb.node) ROOTS[pb.node] = [titleCase(pb.heading.replace(/:.*$/, '')) || `Problem ${i + 1}`, capText(pb.caption, N[pb.node], N)]; });
  for (const id in N) if (!N[id].parent && !ROOTS[id]) ROOTS[id] = [curHeading, ''];
  const firstDia = A.blocks.find(b => b.type === 'dia' && A.diaNode[b.name]);
  let FIRST = firstDia ? A.diaNode[firstDia.name] : Object.keys(N)[0];
  if (FIRST) { let r = FIRST; while (N[r].parent) r = N[r].parent; FIRST = r; }

  // ---- body (html or epub mode) ----
  function body(mode) {
    const toc = [['top', 'Introduction']]; const out = []; const drawn = new Set(); const imgs = []; const figs = [];
    const diaHTML = (id, cap, cls = '', dname = '') => {
      if (!id || !N[id]) return '';
      if (dname && IMGDIA.has(dname)) {   // diagram with drawn lines/arrows: keep the original picture
        if (mode === 'epub') { figs.push(dname); return `<div class="dia"><img src="images/${dname}.jpg" alt="Diagram"/><p class="cap">${esc(cap)}</p></div>`; }
        return `<figure class="dia ${cls}" data-id="${id}"><img class="orig" src="data:image/jpeg;base64,${fs.readFileSync('figs/' + dname + '.jpg').toString('base64')}" alt="Diagram"><figcaption>${esc(cap)}</figcaption></figure>`;
      }
      if (mode === 'epub') { if (drawn.has(id)) return ''; drawn.add(id); imgs.push(id); return `<div class="dia"><img src="images/${id}.png" alt="Diagram"/><p class="cap">${esc(cap)}</p></div>`; }
      return `<figure class="dia ${cls}" data-id="${id}"><div class="sb" data-fen="${N[id].fen}"></div><figcaption>${esc(cap)}</figcaption></figure>`;
    };
    const mv = h => mode === 'epub' ? h.replace(/<a class="mv" data-id="n\d+">([^<]*)<\/a>/g, '<span class="mv">$1</span>') : h;
    out.push(`<header class="art-head" id="top"><div class="kicker">Getting to Work · No. ${num}</div><h1>${esc(title)}</h1>` +
      (A.header.dek ? `<p class="dek">${esc(A.header.dek.replace(/\s+/g, ' '))}</p>` : '') +
      `<p class="byline">By WGM Tatev Abrahamyan · <span>Chess Life, ${esc(A.issue)}</span></p></header>`);
    out.push('<section id="intro">');
    let sec = 0, ghOpen = false;
    const closeGH = () => { if (ghOpen) { out.push('</div>'); ghOpen = false; } };
    A.blocks.forEach(b => {
      if (b.type !== 'gamehead') closeGH();
      if (b.type === 'heading') {
        const t = titleCase(b.html.replace(/<[^>]+>/g, '').trim()); sec++;
        out.push(`</section><section id="s${sec}"><h2>${esc(t)}</h2>`); toc.push([`s${sec}`, t]);
      } else if (b.type === 'gamehead') {
        if (!ghOpen) { out.push('<div class="gamehead">'); ghOpen = true; }
        out.push(`<div>${b.html}</div>`);
      } else if (b.type === 'fig') {
        if (mode === 'epub') { figs.push(b.name); out.push(`<div class="pic"><img src="images/${b.name}.jpg" alt="Illustration"/>${b.caption ? `<p class="cap">${esc(b.caption)}</p>` : ''}</div>`); }
        else out.push(`<figure class="pic"><img src="data:image/jpeg;base64,${fs.readFileSync('figs/' + b.name + '.jpg').toString('base64')}" alt="Illustration from the article">${b.caption ? `<figcaption>${esc(b.caption)}</figcaption>` : ''}</figure>`);
      } else if (b.type === 'dia') {
        out.push(diaHTML(A.diaNode[b.name], diaCap[b.name] || '', '', b.name));
      } else if (b.type === 'ml') {
        out.push(`<p class="ml">${mv(b.html)}</p>`);
        if (mode === 'epub') {
          const ids = [...b.html.matchAll(/data-id="(n\d+)"/g)].map(m => m[1]);
          if (ids.length) { const last = ids[ids.length - 1]; out.push(diaHTML(last, 'After ' + N[last].label + (N[last].ann || ''))); }
        }
      } else if (b.type === 'p') out.push(`<p>${mv(b.html)}</p>`);
      else if (b.type === 'aside' || b.type === 'small') out.push(`<p class="note">${mv(b.html)}</p>`);
    });
    closeGH();
    out.push('</section>');
    if (prac && prac.problems.length) {
      toc.push(['practicum', 'Practicum']);
      const intro = (prac.intro || '').replace(/\s*See the solutions? on page \d+\.?/i, '');
      out.push(`<section id="practicum"><h2>Practicum${prac.title && !/^practicum$/i.test(prac.title) ? ': ' + esc(prac.title) : ''}</h2><p>${esc(intro)}</p><div class="problems">`);
      prac.problems.forEach((pb, i) => {
        out.push(`<div class="prob"><h3>${esc(titleCase(pb.heading))}</h3><div class="pmeta">${pb.meta.map(esc).join('<br/>')}</div>${diaHTML(pb.node, capText(pb.caption, N[pb.node], N) || 'White to move')}</div>`);
      });
      out.push(`</div><p class="note">${mode === 'epub' ? 'Set up the position on a board and find the best line of play.' : 'Click a diagram to set it up on the board, then play your moves for both sides.'} The solutions were printed elsewhere in the magazine and aren’t part of these two pages.</p></section>`);
    }
    return { html: out.join('\n'), toc, imgs, figs };
  }
  // ---- HTML ----
  const h = body('html');
  const table = {};
  for (const id in N) { const n = N[id]; table[id] = [n.fen, n.parent, n.children, n.san ? n.san + (n.ann || '') : '', n.label ? n.label + (n.ann || '') : '', n.from || '', n.to || '', n.white ? 1 : 0]; }
  const tocHTML = h.toc.map(([id, t]) => `    <a data-t="${id}">${esc(t)}</a>`).join('\n');
  const page = tpl.replace(/%%TITLE%%/g, esc(title)).replace('%%TOC%%', tocHTML).replace('/*PIECES*/', () => pieceCss)
    .replace('<!--BODY-->', () => h.html).replace('/*CHESSJS*/', () => chessjs)
    .replace('/*NODES*/', () => 'const NODES=' + JSON.stringify(table) + ';const ROOTS=' + JSON.stringify(ROOTS) + ';const FIRST=' + JSON.stringify(FIRST) + ';const SLUG=' + JSON.stringify(slug) + ';');
  fs.writeFileSync(`${OUT}/articles/${slug}.html`, page);
  // ---- EPUB sources ----
  const e = body('epub');
  const dir = `${__dirname}/epubsrc/${slug}`; fs.mkdirSync(dir, { recursive: true });
  fs.writeFileSync(dir + '/body.json', JSON.stringify({ title, dek: A.header.dek, issue: A.issue, num, toc: e.toc, html: e.html,
    imgs: e.imgs.map(id => ({ id, fen: N[id].fen, from: N[id].from, to: N[id].to })), figs: e.figs, dek: A.header.dek, cover: (firstDia && A.diaNode[firstDia.name]) ? { fen: N[A.diaNode[firstDia.name]].fen } : (FIRST ? { fen: N[FIRST].fen } : null) }));
  const linked = A.report.linked, tokens = A.report.tokens;
  index.push({ num, slug, title, dek: (A.header.dek || '').replace(/\s+/g, ' '), author: 'WGM Tatev Abrahamyan', issue: A.issue, date: A.ym,
    players: firstPlayers.length === 2 ? firstPlayers.map(p => p.replace(/\s*\(.*$/, '')).join(' – ') : '', source: A.name, linked, tokens, thumbFen: (firstDia && A.diaNode[firstDia.name]) ? N[A.diaNode[firstDia.name]].fen : (FIRST ? N[FIRST].fen : null) });
});
fs.writeFileSync(__dirname + '/index_data.json', JSON.stringify(index, null, 1));
console.log('built', index.length);
