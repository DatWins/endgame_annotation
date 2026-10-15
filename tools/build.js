// Builds "Logical Illogicality.html" — interactive single-file article page
const fs = require('fs');
const { nodes, L } = require('./tree.js');

// ---------- move-text helpers ----------
const esc = s => s.replace(/&/g, '&amp;').replace(/</g, '&lt;');
let MODE = 'html', DRAWN = new Set(), DIAS = [];
function span(id, withNum) {
  const n = nodes[id];
  const txt = (withNum || n.white) ? n.label : n.san;
  if (MODE === 'epub') return `<span class="mv">${esc(txt)}${n.ann || ''}</span>`;
  return `<a class="mv" data-id="${id}">${esc(txt)}${n.ann || ''}</a>`;
}
// S(ids, a, b): moves ids[a..b] inclusive, number on first move and every white move
function S(ids, a, b = a) {
  const out = [];
  for (let i = a; i <= b; i++) out.push(span(ids[i], i === a));
  return out.join(' ');
}
const X = id => span(id, true);
const M = L.main;
const ML = (a, b, tail = '') => `<p class="ml">${S(M, a, b)}${tail}</p>` +
  (MODE === 'epub' ? dia(M[b], 'After ' + nodes[M[b]].label + (nodes[M[b]].ann || '')) : '');
function dia(id, caption, cls = '') {
  if (MODE === 'epub') {
    if (DRAWN.has(id)) return '';
    DRAWN.add(id); DIAS.push(id);
    return `<div class="dia"><img src="images/${id}.png" alt="Diagram: ${caption.replace(/"/g, '')}"/><p class="cap">${caption}</p></div>`;
  }
  return `<figure class="dia ${cls}" data-id="${id}"><div class="sb" data-fen="${nodes[id].fen}"></div><figcaption>${caption}</figcaption></figure>`;
}

const F = L.nxb4[2];
function makeBody(mode) {
MODE = mode; DRAWN = new Set(); DIAS = [];
const body = `
<header class="art-head" id="top">
  <div class="kicker">The Practical Endgame / Instruction</div>
  <h1>Logical Illogicality</h1>
  <p class="dek">This month, an ending selected for its beauty and instructive value.</p>
  <p class="byline">By GM Daniel Naroditsky · <span>Chess Life, June 2017, pp. 52–53</span></p>
</header>

<section id="intro">
<p class="first">It was only on the flight back to San Francisco, somewhere in the turbulent skies above Colorado, that the exhaustion and stress of the preceding 12 days fully caught up to me. I was halfway into <i>Better Call Saul</i> Season 1, Episode 3, when I felt an overpowering urge to shut my laptop, stretch out my legs (taking full and unabashed advantage of United Airline’s two inches of legroom—after all, you never know when you’ll be dragged off the plane!), and drift off into a deep slumber. Despite my mediocre performance in the tournament, and despite the massive amount of school catch-up that needed to be done, it was a satisfying slumber indeed. The 2017 U.S. Championship, like its predecessors in years past, was a special event in every way, and it has been a great honor and pleasure to play a role in its unfolding.</p>
<p>This month I present a fascinating endgame from my third-round battle against GM Var Akobian, who would go on to have a fantastic tournament (finishing third overall). Before we plunge in, a disclaimer is in order: I have selected this game not because I think it is somehow the best endgame played at the championship (far from it), but for the beauty of its ideas and for its instructive content. Was there any ego involved in the selection process? Nah …</p>
</section>

<section id="game">
<h2>Breaking Through the Ramparts</h2>
<div class="gamehead">
  <div><b>White:</b> GM Varuzhan Akobian (2739)</div>
  <div><b>Black:</b> GM Daniel Naroditsky (2731)</div>
  <div>2017 U.S. Championship, St. Louis, Missouri, 04.04.17</div>
</div>
${dia('root', 'After 49…Kc5 — White to move')}
<p>After a long and sloppy endgame slog, I finally managed to break through Var’s defensive ramparts. Black has a pawn to the good, and what a pawn it is: White’s rook and knight are powerless in the face of its impending advance. Indeed, Black threatens … Kc4 (not to mention the alternative plan of … Kd4-xe4), followed by … Nd4, b4-b3, and, well, you get the point. In order to prolong the game, White must find a source of counterplay on the other flank, but my rook seems to be permanently deterring any h-pawn related shenanigans.</p>
<p>Endgames, as I have repeatedly stressed in this column, are as much about creativity and grit as they are about technical calculation and theoretical knowledge. Var Akobian, one of the most tenacious players that I have come across in my career, uncorks a fantastic defensive concept:</p>
${ML(0, 0)}
<p>Objectively speaking, this is a grave error that costs White the game. But two exclamation marks are nonetheless in order: Akobian had the right intention, and it was only the tiniest imprecision in execution that made the difference. Once this move is made, White’s idea becomes evident: he will give up his knight for the b4-pawn(!), and then send the newly-liberated rook off to g3, where it will aid the king in cornering the g7-pawn. After it is eliminated, White will be the one possessing a far-advanced passer, and the battle will revolve around whether or not Black’s combined forces can unite in time to stop it (gee, that sounds like some B-movie plot). Let’s watch the events unfold.</p>
${ML(1, 1)}
<p>An important detail. The naïve ${X(L.kc4[0])} would have fallen right into the mousetrap after ${S(L.kc4, 1)} and it turns out that ${S(L.kc4, 2)} meets with ${S(L.kc4, 3)} when Black has to be careful not to lose: ${S(L.kc4, 4, 20)}, and Black draws by the skin of his teeth.</p>
${ML(2, 2)}
<p>Now this is forced, since ${X(L.rg3[0])} no longer does the trick on account of ${S(L.rg3, 1)} and ${S(L.rg3, 2)} falls well short: ${S(L.rg3, 3, 4)} and during the game I intended the simple ${S(L.rg3, 5, 11)}, and Black is completely winning. White can give a few perfunctory checks, but he is down way too much material to put up any actual resistance.</p>
${ML(3, 6)}
${dia(M[6], 'After 53.Rxg7')}
<p>This is where things get interesting. I had about 10 minutes on the clock at this point, and I could sense that Black should be winning. After all, I have some extra time to consolidate because White’s king will inevitably get in the pawn’s way. The key, then, is to find the optimal squares for the rook and knight. Fortunately, with a bit of precise calculation, this is not too hard to do.</p>
${ML(7, 7)}
<p>Avoiding ${S(L.rxg7, 0, 1)} when Black cannot stop the pawn!</p>
${ML(8, 8)}
${dia(M[8], 'After 54.Rg6!?')}
${ML(9, 9)}
<p>Permanently ending White’s hopes. For a moment, I was actually tempted by ${X(L.rxg6[0])}, when I had calculated ${S(L.rxg6, 1)} (${S(L.hxg6, 0, 1)} is easy) ${S(L.rxg6, 2, 4)}. Now, I saw that ${S(L.rxg6, 5, 8)} wins for Black, but, right in the nick of time, I realized that White has ${X(L.kg5[0])} and the knight is beautifully circumscribed by the king. It is worth mentioning, though, that Black can still salvage the game with ${X(L.kd3[0])} (instead of ${X(L.rxg6[2])}) ${S(L.kd3, 1, 6)}</p>
${dia(L.kd3[6], 'After 58…Nc2! (analysis)')}
<p>White will not be able to make progress against the knight and far-advanced passer. I cannot help but mention that the ultra-natural ${X(L.e2[0])} actually loses according to the tablebase: the breathtaking zigzag maneuver that the queen must undertake to separate the king from the pawn is left as an exercise to the reader.</p>
${ML(10, 15)}
<p>The last finesse; Black’s monarch closes in for the kill.</p>
${ML(16, 17, ', White resigned.')}
<p>Due to the presence of the h-pawn, White does not even have any stalemate traps. With his clock ticking down, Akobian threw in the towel.</p>
<p><i>Gee</i>, I told myself when I got back home. <i>If only my Var could have salvaged a draw with some sort of study-like idea, this would make a great game for my next column! Of course, such too-good-to-be-true moments never happen in real life. Oh wait …</i></p>
</section>

<section id="draw">
<h2>The Hidden Draw: 50.Nxb4!!</h2>
<p>Let’s return to the initial position for a moment. Var was onto something with his knight-sacrifice idea: the only issue is that his implementation was too unwieldy; first he had to bring his king to h7, then maneuver his rook to g7, then remove his king from h7, but that takes about as much time as our president’s handshake. What if there was a way to accomplish this idea in half the time?</p>
<p>Behold:</p>
<p class="ml key">${S(L.nxb4, 0, 2)}</p>
${dia(F, 'After 51.Rf3!! (analysis)')}
<p>Like most paradoxical ideas, this one takes a bit of getting used to. White <i>voluntarily</i> gives his knight away, and then casually brings his rook to f3? Surely, Black must have a way to stop the prosaic threat of Rf7, followed by Kxg7 and h6-h7! Well, he doesn’t (and don’t call me Shirley). By keeping his rook on f7, and his king on g7, White will guarantee safe passage for the pawn and simultaneously block off both Black’s knight and king from reaching any meaningful squares. In my opinion, the reason this idea is so beautiful (and so difficult to see) is that it appears so ineffective: for the moment, White is actually down a full piece, and the g7-pawn is still intact! And yet, Black can do nothing but bail out. Take a look:</p>
<div class="lines">
<p>${S(L.a, 0, 3)} is an immediate draw: ${S(L.a, 4, 9)} and Black has to repeat.</p>
<p>${S(L.b, 0, 1)} (${X(L.b2[0])} also draws.) ${S(L.b, 2, 4)} is somewhat more testing, but similarly futile: the cleanest draw is ${S(L.b, 5, 9)}.</p>
<p>${S(L.c, 0, 2)} would probably be my choice, but ${S(L.c, 3, 5)}, is once again, an easy draw.</p>
<p>A fourth possibility is ${X(L.d[0])} which is a draw but the path is tricky. <span class="tip">Try it yourself: you can move the pieces on the board.</span></p>
</div>
<p>And there we have it: every rational, logical, human indicator points to the initial position being totally won for Black, but the beauty of chess (and of endgames in particular) often consists in this kind of logical illogicality (Yeah, sorry. Sue me). And it is only with the kind of creativity and even playfulness demonstrated by those at the very top that we can begin to grapple with Caissa’s irascible spirit.</p>
</section>

<section id="practicum">
<h2>Practicum</h2>
<p>Each month GM Naroditsky will present two problems taken from actual games that illustrate the theme of this month’s column. Your task is to find the best line of play. Problem I should be solvable by a player at roughly a 1500 rating and Problem II by a player roughly at a 2000 rating.</p>
<div class="problems">
  <div class="prob">
    <h3>Problem I: 1500 level</h3>
    <div class="pmeta">GM Varuzhan Akobian (2739)<br>GM Fabiano Caruana (2895)<br>U.S. Championship, 04.07.2017</div>
    ${dia('p1', 'White to move')}
  </div>
  <div class="prob">
    <h3>Problem II: 2000 level</h3>
    <div class="pmeta">WIM Jennifer Yu (2336)<br>WFM Emily Nguyen (2280)<br>U.S. Women’s Champ., 04.08.2017</div>
    ${dia('p2', 'White to move')}
  </div>
</div>
<p class="note">Click a diagram to set it up on the board, then play your moves for both sides. The solutions are on page 79 of the magazine, which isn’t part of these two pages.</p>
</section>
`;
return { body, dias: DIAS };
}
module.exports = { makeBody, nodes };
if (require.main !== module) return;
const body = makeBody('html').body;

// ---------- compact node table for the page ----------
const table = {};
for (const id in nodes) {
  const n = nodes[id];
  table[id] = [n.fen, n.parent, n.children, n.san ? n.san + (n.ann || '') : '', n.label ? n.label + (n.ann || '') : '', n.from || '', n.to || '', n.white ? 1 : 0];
}

// ---------- pieces ----------
const css = fs.readFileSync('cg/assets/chessground.cburnett.css', 'utf8');
const P = { pawn: 'P', bishop: 'B', knight: 'N', rook: 'R', queen: 'Q', king: 'K' };
let pieceCss = '';
for (const m of css.matchAll(/piece\.(\w+)\.(white|black)\s*\{\s*background-image:\s*(url\([^)]*\))/g)) {
  pieceCss += `.pc.${m[2][0]}${P[m[1]]}{background-image:${m[3]}}\n`;
}
let chessjs = fs.readFileSync('cjs/chess.js', 'utf8');

const tpl = fs.readFileSync('template.html', 'utf8');
const out = tpl
  .replace('/*PIECES*/', () => pieceCss)
  .replace('<!--BODY-->', () => body)
  .replace('/*CHESSJS*/', () => chessjs)
  .replace('/*NODES*/', () => 'const NODES=' + JSON.stringify(table) + ';');
fs.writeFileSync('Logical Illogicality.html', out);
console.log('written', out.length, 'bytes; nodes', Object.keys(table).length);
