// Builds and verifies the move tree for "Logical Illogicality" (Naroditsky, Chess Life June 2017)
const { Chess } = require('./cjs/chess.js');
const START = '8/1r4p1/2n3K1/2kNp2P/1p2P3/1R6/8/8 w - - 0 50';
const nodes = {};
let seq = 0;
function addRoot(id, fen) { nodes[id] = { id, fen, parent: null, children: [], san: '', label: '' }; return id; }
addRoot('root', START);

// line(parentId, "Kh7 Kd4 ...", annotations{idx:'!'} , main) -> array of node ids
function line(parentId, sans, opts = {}) {
  const ids = [];
  let pid = parentId;
  const toks = sans.trim().split(/\s+/);
  toks.forEach((tokRaw, i) => {
    const m = tokRaw.match(/^([^!?]+)([!?]*)$/);
    const san = m[1], ann = m[2];
    const p = nodes[pid];
    const g = new Chess(p.fen);
    // reuse an existing child with the same move
    const existing = p.children.map(c => nodes[c]).find(c => c.san === san);
    if (existing) { if (ann) existing.ann = ann; ids.push(existing.id); pid = existing.id; return; }
    const mv = g.move(san, { sloppy: true });
    if (!mv) throw new Error(`Illegal ${san} after ${p.label || p.id} fen ${p.fen}`);
    const fenParts = p.fen.split(' ');
    const num = +fenParts[5], white = fenParts[1] === 'w';
    const id = 'n' + (++seq);
    nodes[id] = { id, fen: g.fen(), parent: pid, children: [], san: mv.san, ann, from: mv.from, to: mv.to,
      num, white, main: !!opts.main, label: (white ? num + '.' : num + '...') + mv.san };
    p.children.push(id);
    ids.push(id); pid = id;
  });
  return ids;
}
const L = {};
// ---------- Main game ----------
L.main = line('root', 'Kh7??!! Kd4! Nxb4 Nxb4 Rg3 Kxe4 Rxg7 Rb6 Rg6!? Rb8 h6 Nd5 Kg7 Rb7+ Kf8 Kf5! Rg1 Nf6', { main: true });
const M = i => L.main[i]; // M(0)=50.Kh7, M(1)=50...Kd4, M(2)=51.Nxb4 ...
// 50...Kc4? line
L.kc4 = line(M(0), 'Kc4? Rg3 b3 Rc3+ Kd4 Rxc6 b2 Nc3 b1=Q Nxb1 Rxb1 Kxg7 Kxe4 h6 Rb7+ Kg6 Kf3 h7 Rxh7 Kxh7 e4');
// 51.Rg3 instead of 51.Nxb4
L.rg3 = line(M(1), 'Rg3 Kxe4 Rxg7 Rxg7+ Kxg7 Kxd5 h6 b3 h7 b2 h8=Q b1=Q');
// 53...Rxg7+??
L.rxg7 = line(M(6), 'Rxg7+?? Kxg7');
// 54...Rxg6??
L.rxg6 = line(M(8), 'Rxg6?? Kxg6 Nd5 h6 Ne7+ Kf7 Kf5! Kxe7 Kg6');
L.hxg6 = line(L.rxg6[0], 'hxg6 Nd5');
L.kg5 = line(L.rxg6[4], 'Kg5!!');           // 57.Kg5!! instead of 57.Kf7
L.kd3 = line(L.rxg6[1], 'Kd3 h6 e4 h7 e3 h8=Q Nc2!');
L.e2 = line(L.kd3[5], 'e2');                // 58...e2 loses (tablebase)
// ---------- The hidden draw: 50.Nxb4!! ----------
L.nxb4 = line('root', 'Nxb4!! Nxb4 Rf3!!');
const F = L.nxb4[2];
L.a = line(F, 'Kd4 Rf7 Rxf7 Kxf7 Nd3! Kxg7 Nf4 h6 Ne6+ Kf6');
L.b = line(F, 'Nc2 Rf7 Rb6+ Kxg7 Nd4 Rf6! Ne6+ Kf7 Ng5+ Kg6');
L.b2 = line(L.b[0], 'Rc3+');
L.c = line(F, 'Kd6 Rf7 Rb8 Kxg7 Ke6 Rf6+');
L.d = line(F, 'Nd5!');
// ---------- Practicum ----------
addRoot('p1', '8/6kn/5pp1/4Nq2/3Qp2p/4P2P/6P1/7K w - - 0 1');
addRoot('p2', '8/6p1/8/4kn2/3p2PP/3K4/8/6B1 w - - 0 1');

module.exports = { nodes, L, START };
if (require.main === module) {
  const show = k => L[k].map(i => nodes[i].label + (nodes[i].ann || '')).join(' ');
  for (const k in L) console.log(k.padEnd(5), show(k));
  console.log('nodes', Object.keys(nodes).length);
  console.log('after 53.Rxg7  :', nodes[M(6)].fen);
  console.log('after 51.Rf3   :', nodes[F].fen);
  console.log('after 54.Rg6   :', nodes[M(8)].fen);
  console.log('after 58...Nc2 :', nodes[L.kd3[6]].fen);
}
