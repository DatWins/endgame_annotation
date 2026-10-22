"""Extract structured content from GM Pal Benko's "Endgame Lab" columns (Chess Life 10/2008 - 12/2013).
Two pages per article; page 2 starts with the "Benko's Bafflers" problem box (treated like a practicum).
Three layout eras:
  2008-2012/07 : Bookman body, Akzidenz Grotesk bold main line, diagrams typeset in the DiagramTTUSCF font
  2012/08-2013 : Bookman body, FS Joey bold main line, Cairo titles, diagrams as images
Usage: python3 extract_benko.py   (reads arts.json + benko.pdf, writes ext/<slug>.json, fontfens.json)
"""
import pdfplumber, json, re, os, collections, sys, logging
logging.disable(logging.CRITICAL)
import extract_base
from extract_base import group_lines, column_bounds, assemble, MOVE_RE
from fontdia import clusters, grid

SANS = ('Akzidenz', 'Joey', 'Cairo', 'Helvetica')
SIDEBAR = re.compile(r'Download|pgn file of all|from this issue at|of this issue|uschess\.org|^Please e-mail|pbenko@|Chess Life —|Register to vote|USCF election|^azine,|Downloadable Files|Chess Life Magazine,|^\d+ Chess Life', re.I)
PIECES = set('KQRLNPkqrlnp')
BG = set('\x02\x03\x04\x05\x06\x07\x08!"#$%&zmtsvw')
DIACHARS = PIECES | BG | set('+-')
import html as _html
_PW = {}
def poppler_words(pno):
    if pno not in _PW:
        try: t = open(f'bbox/p{pno}.html', encoding='utf-8').read()
        except FileNotFoundError: t = ''
        _PW[pno] = [(float(m[1]), float(m[2]), _html.unescape(m[3])) for m in re.finditer(r'<word xMin="([\d.]+)" yMin="([\d.]+)" xMax="[\d.]+" yMax="[\d.]+">(.*?)</word>', t)]
    return _PW[pno]

def style_of(w):
    fn = w['fontname'].split('+')[-1]
    col = w.get('non_stroking_color') or (0,)
    if isinstance(col, (int, float)): col = (col,)
    col = tuple(col)
    red = len(col) == 3 and col[0] > 0.6 and col[1] < 0.35 or (len(col) == 4 and col[1] > 0.5 and col[2] > 0.5 and col[0] < 0.3)
    blue = (len(col) == 3 and col[2] > 0.5 and col[0] < 0.3) or (len(col) == 4 and col[0] > 0.6 and col[1] > 0.2 and col[2] < 0.2)
    sans = any(s in fn for s in SANS)
    bold = any(s in fn for s in ('Bold', 'Black', 'Heavy', 'Semibold'))
    ital = any(s in fn for s in ('Ital', '-It', 'Oblique'))
    return dict(fn=fn, sans=sans, bold=bold, ital=ital, red=red, blue=blue, size=round(w['size'], 1))
extract_base.style_of = style_of

def line_text_segments(L):
    return [[w['text'], ('i' if w['ital'] else '') + ('b' if w['bold'] and L['kind'] == 'body' else '')] for w in L['w']]
extract_base.line_text_segments = line_text_segments

def words_of(pg):
    ws = pg.extract_words(extra_attrs=['fontname', 'size', 'non_stroking_color'], keep_blank_chars=False, x_tolerance=1.5)
    for w in ws: w.update(style_of(w))
    return [w for w in ws if 'Diagram' not in w['fn']]

def raw_kind(L):
    ws = L['w']; n = len(ws)
    sans = sum(w['sans'] for w in ws) / n; bold = sum(w['bold'] for w in ws) / n
    ital = sum(w['ital'] for w in ws) / n; red = sum(w['red'] for w in ws) / n
    size = collections.Counter(w['size'] for w in ws).most_common(1)[0][0]
    txt = ' '.join(w['text'] for w in ws); up = txt.upper()
    if txt.lower().startswith(('(see diagram', '(continued', 'continued from', '(diagram')): return 'note'
    if sans > .6 and size <= 8.6 and re.search(r'TO (PLAY|MOVE)|^(POSITION )?AFTER|^ANALYSIS', up) and not (bold and MOVE_RE.match(txt)): return 'caption'
    if sans > .6 and bold > .6 and size >= 9.6: return 'heading'
    if sans > .6 and bold > .6: return 'ml'
    if sans > .6 and red > .5 and size <= 9: return 'gamehead'
    if sans > .6 and ital > .5: return 'aside'
    if sans > .6: return 'small'
    if bold > .6 and size <= 7.6: return 'caption'
    if bold > .6 and size >= 8.3: return 'sbold'
    if ital > .9 and size >= 8.3 and n <= 10: return 'sital'
    return 'body'

def extract(art, pdf):
    out = dict(name=art['slug'], blocks=[], practicum=None, header={})
    allitems = []; unit = 0; fens = {}
    for k, pi in enumerate(art['pages']):
        pg = pdf.pages[pi]
        allw = words_of(pg)
        # --- diagrams: font-typeset (older issues) or images (later issues)
        dias = []
        pw = poppler_words(pi + 1)
        ox, oy = pg.bbox[0], pg.bbox[1]
        for g in clusters(pg):
            if len(g['c']) < 20: continue
            s = g['s']
            # decode from poppler's word boxes (pdfplumber's per-glyph x positions drift in this font)
            bx0, bt0, bx1, bt1 = g['x0'] - 4, g['t0'] - 4, g['x1'] + s + 4, g['t1'] + s + 4
            ws_ = [(x + ox, y + oy, t) for x, y, t in pw if bx0 <= x + ox <= bx1 and bt0 <= y + oy <= bt1 and set(t) <= DIACHARS]
            if not ws_: continue
            X0 = min(w[0] for w in ws_); T0 = min(w[1] for w in ws_)
            board = [['.'] * 8 for _ in range(8)]
            pending = {}   # row -> column of a dark-square 'hole' glyph whose piece letter was printed one square late
            for x, y, t in sorted(ws_, key=lambda w: (round(w[1]), w[0])):
                r = round((y - T0) / s); cx = x
                for i, ch in enumerate(t):
                    c = round((cx - X0) / s)
                    if ch in BG:
                        if i == len(t) - 1: pending[r] = c
                        continue
                    if ch in PIECES and 0 <= r < 8 and 0 <= c < 8:
                        if pending.get(r) == c: pending.pop(r)          # the hole got its piece
                        cc = pending.pop(r) if (i == 0 and pending.get(r) == c - 1 and board[r][c - 1] == '.') else c
                        board[r][cc] = {'L': 'B', 'l': 'b'}.get(ch, ch)
                    cx += s
            rows = []
            for r in board:
                row = ''; e = 0
                for ch in r:
                    if ch == '.': e += 1
                    else:
                        if e: row += str(e); e = 0
                        row += ch
                if e: row += str(e)
                rows.append(row)
            dias.append(dict(x0=X0, top=T0, x1=X0 + 8 * s, bottom=T0 + 8 * s, fen='/'.join(rows)))
        for im in pg.images:
            w_, h_ = im['x1'] - im['x0'], im['bottom'] - im['top']
            if abs(w_ - h_) < 4 and w_ > 60: dias.append(dict(x0=im['x0'], top=im['top'], x1=im['x1'], bottom=im['bottom'], fen=None))
        # --- title block
        if k == 0:
            big = [w for w in allw if w['sans'] and w['size'] >= 20 and w['top'] < 200]
            dek = [w for w in allw if w['top'] < 260 and ((not w['sans'] and w['ital'] and 12 <= w['size'] < 20) or ('Joey' in w['fn'] and 15 <= w['size'] < 20))]
            byl = [w for w in allw if w['top'] < 270 and 8.8 <= w['size'] <= 9.6 and w['text'].strip('.').upper() in ('BY', 'GM', 'PAL', 'BENKO')]
            j = lambda ws: ' '.join(' '.join(x['text'] for x in L['w']) for L in sorted(group_lines(ws, 6), key=lambda L: (L['top'], L['x0'])))
            out['header'] = dict(title=j(big), dek=j(dek), byline='GM Pal Benko')
            head_bot = max([w['bottom'] for w in big + dek + byl] or [0])
            allw = [w for w in allw if w['top'] > head_bot + 1]
        # --- Bafflers box on the second page
        box = None
        if k == 1:
            rs = [r for r in pg.rects if r['width'] > 120 and r['height'] > 50 and r['top'] < 140]
            if rs: box = (min(r['x0'] for r in rs), min(r['top'] for r in rs), max(r['x1'] for r in rs), max(r['bottom'] for r in rs))
        inbox = lambda o: box and o['x0'] >= box[0] - 3 and o['x1'] <= box[2] + 3 and o['top'] >= box[1] - 3 and o['bottom'] <= box[3] + 3
        def keep(w):
            f = w['fn']
            if not ('Bookman' in f or 'Akzidenz' in f or 'Joey' in f): return False
            if 'Heavy' in f or 'Medium' in f: return False          # page header / footer / byline
            if w['size'] < 6.5 or w['size'] > 10.6: return False
            if not w['sans'] and w['size'] >= 9.6: return False      # pull quotes
            return True
        if box:
            bws = [w for w in allw if inbox(w) and keep(w)]
            bd = [d for d in dias if inbox(d)]
            out['practicum'] = bafflers(bws, bd, art['slug'], unit, fens)
            allw = [w for w in allw if not inbox(w)]; dias = [d for d in dias if not inbox(d)]
        ws = [w for w in allw if keep(w) and pg.bbox[1] + 40 < w["top"] < pg.bbox[1] + pg.height - 30]
        # lead-in set in capitals
        if k == 0:
            caps = [w for w in ws if not w['sans'] and w['text'].isupper() and len(w['text']) > 1]
            if caps:
                top = min(w['top'] for w in caps)
                line = sorted([w for w in ws if abs(w['top'] - top) < 2 and not w['sans']], key=lambda w: w['x0'])
                for i, w in enumerate(line):
                    t = w['text']
                    if not t.isupper(): continue
                    if i == 0: w['text'] = t[0] + t[1:].lower()
                    elif t in ('I', 'U.S.') or t.startswith('I’'): pass
                    elif t.lower() in VOCAB: w['text'] = t.lower()
                    elif t[0] + t[1:].lower() in CAPS: w['text'] = t[0] + t[1:].lower()
                    else: w['text'] = t.lower()
        body = [w for w in ws if 7.5 <= w['size'] <= 9.5 and not w['sans']]
        cols = column_bounds(body or ws, pg.width)
        if not cols: cols = [[0, pg.width]]
        def colof(x0, x1):
            cx = (x0 + x1) / 2
            for ci, c in enumerate(cols):
                if c[0] - 8 <= cx <= c[1] + 8: return ci
            return min(range(len(cols)), key=lambda ci: abs((cols[ci][0] + cols[ci][1]) / 2 - cx))
        bycol = collections.defaultdict(list)
        for w in ws: bycol[colof(w['x0'], min(w['x1'], w['x0'] + 10))].append(w)
        items = []
        for ci, cws in bycol.items():
            prev = None
            for L in sorted(group_lines(cws), key=lambda L: L['top']):
                lt = ' '.join(w['text'] for w in L['w'])
                if SIDEBAR.search(lt): continue
                kd = raw_kind(L)
                near = prev is not None and L['top'] - prev[1] < 15
                if kd == 'sbold': kd = 'gamehead' if near and prev[0] in ('heading', 'gamehead') else 'heading'
                elif kd == 'sital': kd = 'gamehead' if near and prev[0] in ('heading', 'gamehead') else 'body'
                L['col'] = ci; L['kind'] = kd; L['page'] = unit
                items.append(('line', ci, L['top'], L)); prev = (kd, L['top'])
        for di, d in enumerate(sorted(dias, key=lambda d: (d['x0'], d['top']))):
            ci = colof(d['x0'], d['x1'])
            name = f"{art['slug']}_u{unit}_{di}"
            if d['fen']: fens[name] = d['fen']
            items.append(('dia', ci, d['top'], dict(name=name, top=d['top'], bottom=d['bottom'], x0=d['x0'], x1=d['x1'], col=ci, page=unit, pdfpage=pi)))
        items.sort(key=lambda t: (t[1], t[2]))
        for t in items: t[3]['colL'], t[3]['colR'] = cols[t[1]] if t[1] < len(cols) else (0, pg.width)
        allitems += [(unit,) + t for t in items]
        unit += 1
    blocks = assemble(allitems)
    # heading directly followed by player/source lines: keep heading as the section title
    out['blocks'] = blocks
    out['dias'] = [dict(name=t[4]['name'], pdfpage=t[4]['pdfpage'], box=[t[4]['x0'], t[4]['top'], t[4]['x1'], t[4]['bottom']]) for t in allitems if t[1] == 'dia']
    if out['practicum']:
        out['dias'] += [dict(name=p['dia'], pdfpage=art['pages'][1], box=p['box']) for p in out['practicum']['problems']]
    return out, fens

def bafflers(bws, bd, slug, unit, fens):
    bd = sorted(bd, key=lambda d: d['x0'])
    edges = [d['x0'] - 18 for d in bd] + [1e9]
    def wreg(w):
        cx = (w['x0'] + w['x1']) / 2
        for i in range(len(bd)):
            if edges[i] <= cx < edges[i + 1]: return i
        return -1
    byreg = collections.defaultdict(list)
    for w in bws: byreg[wreg(w)].append(w)
    regs = {r: group_lines(ws, 2) for r, ws in byreg.items()}
    intro = regs.get(-1, [])
    probs = []
    for i, d in enumerate(bd):
        name = f"{slug}_bx_{i}"
        if d['fen']: fens[name] = d['fen']
        mine = sorted(regs.get(i, []), key=lambda L: L["top"])
        above = [L for L in mine if L['bottom'] <= d['top'] + 2]
        below = [L for L in mine if L['top'] >= d['bottom'] - 2]
        t = lambda L: ' '.join(w['text'] for w in L['w'])
        heading = (t(above[0]) if above else f'Problem {"I" * (i + 1)}').rstrip(':')
        meta = []
        for L in above[1:]:
            s = t(L)
            if meta and (L['w'][0]['ital'] and re.match(r'^\d{4}|^[A-Z]', s) and len(s) < 12): meta[-1] += ' ' + s
            else: meta.append(s)
        probs.append(dict(dia=name, heading=heading, meta=meta, caption=' '.join(t(L) for L in below), box=[d['x0'], d['top'], d['x1'], d['bottom']]))
    txt = []
    for L in sorted(intro, key=lambda L: L['top']):
        s = ' '.join(w['text'] for w in L['w'])
        if re.search(r'Please e-mail|pbenko|uschess\.org', s): break
        txt.append(s)
    s = ''
    for x in txt:
        s = s[:-1] + x if s.endswith('-') and x[:1].islower() else (s + ' ' + x).strip()
    s = re.sub(r'\s*Solutions? (can be )?found on page \d+\.?', '', s)
    return dict(title="Benko’s Bafflers", intro=s, problems=probs)

VOCAB = set(); CAPS = set()
if __name__ == '__main__':
    arts = json.load(open('arts.json'))
    import subprocess
    txt = subprocess.run(['pdftotext', 'benko.pdf', '-'], capture_output=True, text=True).stdout
    VOCAB.update(m.lower() for m in re.findall(r"\b[a-z][a-z’']*\b", txt))
    CAPS.update(re.findall(r"\b[A-Z][a-z][a-z’']*\b", txt))
    os.makedirs('ext', exist_ok=True)
    allf = {}
    with pdfplumber.open('benko.pdf') as pdf:
        for a in arts:
            if 'slug' not in a: continue
            d, f = extract(a, pdf); allf.update(f)
            json.dump(d, open(f"ext/{a['slug']}.json", 'w'), indent=1, ensure_ascii=False)
            print(a['slug'], '|', d['header']['title'], '|', len(d['blocks']), 'blocks', len(d['dias']), 'dias', 'bafflers' if d['practicum'] else '')
    json.dump(allf, open('fontfens.json', 'w'), indent=0)
