// Parse moves in article text, build verified move trees, link diagrams. Output model/<name>.json
const fs = require('fs');
const { Chess } = require('./lib/chess.js');
const FENS = Object.assign(JSON.parse(fs.readFileSync('fens.json', 'utf8')), JSON.parse(fs.readFileSync('fen_overrides.json', 'utf8')));
const CAPFIX = fs.existsSync('caption_fixes.json') ? JSON.parse(fs.readFileSync('caption_fixes.json', 'utf8')) : {};
const START = 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1';

const SAN = '(?:[KQRBN][a-h]?[1-8]?x?[a-h][1-8]|[a-h](?:x[a-h])?[1-8](?:=?[QRBN])?|O-O-O|O-O|0-0-0|0-0)[+#]?';
const TOK = new RegExp(`(?<![\\w.=]|[a-h1-8]-)(?:(\\d{1,3})((?:\\s*[.…])+)\\s*)?(${SAN})([!?]{0,3})(?![\\w=]|-[a-hx])`, 'g');

function castling(placement) {
  const rows = placement.split('/'); const r1 = expand(rows[7]), r8 = expand(rows[0]);
  let c = '';
  if (r1[4] === 'K' && r1[7] === 'R') c += 'K'; if (r1[4] === 'K' && r1[0] === 'R') c += 'Q';
  if (r8[4] === 'k' && r8[7] === 'r') c += 'k'; if (r8[4] === 'k' && r8[0] === 'r') c += 'q';
  return c || '-';
}
function expand(row) { let s = ''; for (const ch of row) s += /\d/.test(ch) ? '.'.repeat(+ch) : ch; return s; }
function makeFen(placement, white, num) { return `${placement} ${white ? 'w' : 'b'} ${castling(placement)} - 0 ${num}`; }
function tryMove(fen, san, epOk) {
  try { return tryMove0(fen, san, epOk); } catch (e) { return null; }
}
function tryMove0(fen, san, epOk) {
  const g = new Chess();
  if (!g.load(fen)) return null;
  const s = san.replace(/0/g, 'O').replace(/[+#]/g, '');
  let m = g.move(s, { sloppy: true });
  if (!m && epOk) {
    const ep = s.match(/^[a-h]x([a-h])([36])/);
    const parts = fen.split(' ');
    if (ep && parts[3] === '-' && ((parts[1] === 'w' && ep[2] === '6') || (parts[1] === 'b' && ep[2] === '3'))) {
      parts[3] = ep[1] + ep[2]; const g2 = new Chess();
      if (g2.load(parts.join(' '))) { m = g2.move(s, { sloppy: true }); if (m) return { fen: g2.fen(), san: m.san, from: m.from, to: m.to }; }
    }
  }
  return m ? { fen: g.fen(), san: m.san, from: m.from, to: m.to } : null;
}
const placementOf = fen => fen.split(' ')[0];

function parseArticle(A) {
  const nodes = {}; let seq = 0; const report = { tokens: 0, linked: 0, failed: [] };
  const recency = [];
  const touch = id => { const i = recency.indexOf(id); if (i >= 0) recency.splice(i, 1); recency.unshift(id); if (recency.length > 60) recency.pop(); };
  function addNode(fen, parent, mv, ply, block) {
    const id = 'n' + (++seq);
    nodes[id] = { id, fen, parent, children: [], san: mv ? mv.san : '', from: mv ? mv.from : '', to: mv ? mv.to : '', ply, block, main: false, ann: '' };
    if (parent) nodes[parent].children.push(id);
    return id;
  }
  // diagram roots (created lazily)
  const diaBlocks = [];
  A.blocks.forEach((b, i) => { if (b.type === 'dia') { if (b.name in CAPFIX) b.caption = CAPFIX[b.name]; diaBlocks.push({ name: b.name, caption: b.caption, idx: i }); } });
  function capPly(cap, pl) {
    cap = (cap || '').replace(/(\d{1,3}\s*\.[\s.…]*)([KQRBN]?)([A-HX0-9=+#O-]+)/, (all, a, pc, rest) => a + pc + rest.toLowerCase().replace(/o/g, 'O'));
    const m = (cap || '').match(/(\d{1,3})\s*((?:\s*[.…])+)\s*([KQRBNa-hO0][^\s,]*)/);
    if (!m) return null;
    const n = +m[1];
    let black = (m[2].match(/\./g) || []).length >= 3 || m[2].includes('…');
    const sq = (m[3].match(/([a-h][1-8])(?!.*[a-h][1-8])/) || [])[1];
    if (pl && sq) {
      const rows = pl.split('/').map(expand); const ch = rows[8 - +sq[1]][sq.charCodeAt(0) - 97];
      if (ch && ch !== '.') black = ch === ch.toLowerCase();
    } else if (pl && /^O-O|^0-0/.test(m[3])) {
      const rows = pl.split('/').map(expand); if (rows[7][6] === 'K' || rows[7][2] === 'K') black = false; if (rows[0][6] === 'k' || rows[0][2] === 'k') black = true;
    }
    return black ? 2 * n : 2 * (n - 1) + 1; // half-moves played after the captioned move
  }
  const rootOf = {}; // dia name -> root node id
  function diaRoot(d, ply) {
    if (rootOf[d.name]) return rootOf[d.name];
    const pl = FENS[d.name]; if (!pl) return null;
    const white = ply % 2 === 0, num = Math.floor(ply / 2) + 1;
    const id = addNode(makeFen(pl, white, num), null, null, ply, d.idx);
    nodes[id].dia = d.name; rootOf[d.name] = id; return id;
  }
  let startRoot = null;
  // score a candidate parent: how many moves of the run play legally from it
  function score(fen, run, root) {
    let f = fen, k = 0;
    let first = true; for (const t of run) { const r = tryMove(f, t.san, first && root); first = false; if (!r) break; f = r.fen; k++; }
    return k;
  }
  let lastMain = null, gameFloor = 0, prevType = '';
  function attach(run, bi, isMain) {
    const p = run[0].ply;
    const cands = [];
    const seen = new Set();
    const consider = (id, pri) => { if (!id || seen.has(id) || +id.slice(1) <= gameFloor) return; seen.add(id); const n = nodes[id]; if (n.ply !== p) return; const s = score(n.fen, run, !n.parent); if (s > 0) cands.push({ id, s, pri }); };
    if (isMain && lastMain) consider(lastMain, 0);
    recency.forEach((id, i) => consider(id, 1 + i));
    Object.keys(nodes).forEach(id => consider(id, 100));
    // diagram roots: diagrams near this block, nearest first
    let best = cands.length ? Math.max(...cands.map(c => c.s)) : 0;
    if (best < run.length) {
      const ds = diaBlocks.slice().sort((a, b) => Math.abs(a.idx - bi) - Math.abs(b.idx - bi) + (a.idx > bi) - (b.idx > bi));
      for (const d of ds) {
        if (rootOf[d.name] && nodes[rootOf[d.name]].ply !== p) {
          // root exists with another ply: maybe the diagram is mid-line; can't reuse
          continue;
        }
        const cp = capPly(d.caption, FENS[d.name]);
        if (cp !== null && cp !== p) continue;
        if (/WHITE TO MOVE/i.test(d.caption) && p % 2 !== 0) continue;
        if (/BLACK TO MOVE/i.test(d.caption) && p % 2 !== 1) continue;
        const pl = FENS[d.name]; if (!pl) continue;
        const fen = makeFen(pl, p % 2 === 0, Math.floor(p / 2) + 1);
        const s = score(fen, run, true);
        if (s > 0) cands.push({ dia: d, s, pri: 200 + Math.abs(d.idx - bi) });
      }
      if (p === 0 || run[0].num === 1) {
        const s = score(START, run); if (s > 0) cands.push({ start: true, s, pri: 150 });
      }
    }
    if (!cands.length) return null;
    cands.sort((a, b) => b.s - a.s || a.pri - b.pri);
    // two alternative moves from the same position both fit: continue the one whose line is still open
    if (cands.length > 1 && cands[0].id && cands[1].id && cands[0].s === cands[1].s && cands[0].pri !== 0) {
      const x = nodes[cands[0].id], y = nodes[cands[1].id];
      // ...prefer the alternative that was written first (the line the text is following), not the side branch
      if (x.parent && x.parent === y.parent && !x.main && !y.main && +y.id.slice(1) < +x.id.slice(1) && x.children.length) cands.unshift(cands.splice(1, 1)[0]);
    }
    const c = cands[0];
    let pid = c.id;
    if (c.dia) pid = diaRoot(c.dia, p);
    if (c.start) { if (!startRoot) { startRoot = addNode(START, null, null, 0, bi); } pid = startRoot; }
    // walk
    const ids = [];
    for (const t of run) {
      const par = nodes[pid];
      const r = tryMove(par.fen, t.san, !par.parent);
      if (!r) break;
      let child = par.children.find(cid => nodes[cid].san === r.san);
      if (!child) child = addNode(r.fen, pid, r, par.ply + 1, bi);
      if (t.ann && !nodes[child].ann) nodes[child].ann = t.ann;
      if (isMain) {
        nodes[child].main = true;
        const ch = par.children; ch.splice(ch.indexOf(child), 1); ch.unshift(child);
      }
      t.id = child; ids.push(child); pid = child;
    }
    touch(run[0].id ? nodes[run[0].id].parent : pid);
    ids.forEach(touch);
    if (isMain && ids.length) lastMain = ids[ids.length - 1];
    return ids;
  }

  // ---- tokenize blocks and attach runs ----
  A.blocks.forEach((b, bi) => {
    // a new game header: positions from earlier games can no longer be continued
    let fresh = b.type === 'gamehead' && prevType !== 'gamehead';
    // a section heading followed by a new diagram also starts a new example
    if (b.type === 'heading') { for (let k = bi + 1; k < Math.min(A.blocks.length, bi + 4); k++) { const t = A.blocks[k].type; if (t === 'dia') { fresh = true; break; } if (t === 'ml') break; } }
    if (fresh) { gameFloor = seq; lastMain = null; recency.length = 0; if (b.type === 'gamehead') startRoot = null; }
    prevType = b.type;
    if (!b.html || b.type === 'heading' || b.type === 'gamehead' || b.type === 'aside') return;
    const isMain = b.type === 'ml';
    // operate on text outside tags; remember which stretches are bold (main-line moves inside prose)
    const parts = b.html.split(/(<[^>]+>)/);
    let text = '', map = [], inB = 0; const boldR = [];
    parts.forEach((pt, i) => {
      if (pt === '<b>') inB++; else if (pt === '</b>') inB = Math.max(0, inB - 1);
      if (!pt.startsWith('<')) { if (inB) boldR.push([text.length, text.length + pt.length]); map.push([text.length, i]); text += pt + '\u0000'; }
    });
    const isBold = pos => boldR.some(([a, z]) => pos >= a && pos < z);
    const toks = []; let m; TOK.lastIndex = 0;
    while ((m = TOK.exec(text))) {
      toks.push({ start: m.index, end: m.index + m[0].length, num: m[1] ? +m[1] : null, black: !!m[2] && ((m[2].match(/\./g) || []).length >= 3 || m[2].includes('…')), san: m[3], ann: m[4] });
    }
    // runs
    const runs = []; let cur = null;
    for (const t of toks) {
      if (t.num !== null) {
        t.ply = 2 * (t.num - 1) + (t.black ? 1 : 0);
        if (cur && t.ply === cur[cur.length - 1].ply + 1 && /^[\s,\u0000]*(e\.\s?p\.)?[\s,\u0000]*$/.test(text.slice(cur[cur.length - 1].end, t.start))) cur.push(t);
        else { cur = [t]; runs.push(cur); }
      } else if (cur && /^[\s\u0000]*(e\.\s?p\.)?[\s\u0000]*$/.test(text.slice(cur[cur.length - 1].end, t.start))) {
        t.ply = cur[cur.length - 1].ply + 1; cur.push(t);
      } else t.skip = true;
    }
    for (const run of runs) {
      report.tokens += run.length;
      const ids = attach(run, bi, isMain || (b.type === 'p' && isBold(run[0].start))) || [];
      report.linked += ids.length;
      if (ids.length < run.length) {
        const bad = run[ids.length];
        report.failed.push({ block: bi, text: text.slice(bad.start, bad.end), ctx: text.slice(Math.max(0, run[0].start - 30), bad.end + 10).replace(/\u0000/g, ''), linkedBefore: ids.length });
      }
    }
    // rebuild html with spans
    let out = text;
    const linked = toks.filter(t => t.id).sort((a, b) => b.start - a.start);
    for (const t of linked) {
      const n = nodes[t.id];
      const label = (t.num !== null ? (n.ply % 2 === 1 ? `${Math.floor((n.ply - 1) / 2) + 1}.` : `${Math.floor((n.ply - 2) / 2) + 1}...`) : '') + n.san + (t.ann || '');
      out = out.slice(0, t.start) + `<a class="mv" data-id="${t.id}">${label}</a>` + out.slice(t.end);
    }
    // re-insert tags
    const segs = out.split('\u0000'); let res = '';
    let si = 0;
    parts.forEach(pt => { if (pt.startsWith('<')) res += pt; else res += segs[si++]; });
    b.html = res;
  });
  // ---- link diagrams to nodes ----
  const diaNode = {};
  for (const d of diaBlocks) {
    if (rootOf[d.name]) { diaNode[d.name] = rootOf[d.name]; continue; }
    const pl = FENS[d.name]; if (!pl) continue;
    const matches = Object.values(nodes).filter(n => placementOf(n.fen) === pl);
    if (matches.length) {
      matches.sort((a, b) => Math.abs(a.block - d.idx) - Math.abs(b.block - d.idx) || (b.main - a.main));
      diaNode[d.name] = matches[0].id;
    } else {
      const cp = capPly(d.caption, pl);
      let white = true;
      if (/BLACK TO MOVE/i.test(d.caption)) white = false;
      const ply = cp !== null ? cp : (white ? 0 : 1);
      const id = addNode(makeFen(pl, ply % 2 === 0, Math.floor(ply / 2) + 1), null, null, ply, d.idx);
      nodes[id].dia = d.name; diaNode[d.name] = id; report.unlinkedDia = (report.unlinkedDia || 0) + 1;
    }
  }
  // practicum roots
  const prac = A.practicum;
  if (prac) for (const pb of prac.problems) {
    const pl = FENS[pb.dia]; if (!pl) continue;
    const white = !/BLACK TO MOVE/i.test(pb.caption);
    const id = addNode(makeFen(pl, white, 1), null, null, white ? 0 : 1, -1);
    nodes[id].dia = pb.dia; pb.node = id;
  }
  // labels
  for (const n of Object.values(nodes)) {
    if (n.parent) {
      const mvNum = Math.floor((n.ply - 1) / 2) + 1, white = n.ply % 2 === 1;
      n.label = (white ? mvNum + '.' : mvNum + '...') + n.san; n.white = white;
    } else { n.label = ''; n.white = false; }
  }
  return { nodes, diaNode, report };
}

if (require.main === module) {
  fs.mkdirSync('model', { recursive: true });
  const files = process.argv.slice(2).length ? process.argv.slice(2) : fs.readdirSync('prep').map(f => 'prep/' + f);
  const summary = [];
  for (const f of files) {
    const A = JSON.parse(fs.readFileSync(f, 'utf8'));
    const r = parseArticle(A);
    A.nodes = r.nodes; A.diaNode = r.diaNode; A.report = r.report;
    fs.writeFileSync('model/' + A.name + '.json', JSON.stringify(A));
    summary.push([A.name.slice(0, 40), r.report.tokens, r.report.linked, r.report.failed.length, r.report.unlinkedDia || 0]);
  }
  let T = 0, Lk = 0, F = 0;
  for (const s of summary) { T += s[1]; Lk += s[2]; F += s[3]; }
  console.log(summary.map(s => s.join('\t')).join('\n'));
  console.log('TOTAL tokens', T, 'linked', Lk, 'failed runs', F);
}
module.exports = { parseArticle };
