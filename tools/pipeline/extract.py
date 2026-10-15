"""Extract structured article content (header, paragraphs, diagrams, practicum) from the 2-page PDFs."""
import pdfplumber, json, re, glob, os, html, collections, sys

MOVE_RE = re.compile(r'\b\d{1,3}\s*\.\s*(?:\.\.\.|…)?\s*(?:[KQRBN]?[a-h]?[1-8]?x?[a-h][1-8](?:=?[QRBN])?|0-0(?:-0)?|O-O(?:-O)?)')

def style_of(w):
    fn = w['fontname'].split('+')[-1]
    col = w.get('non_stroking_color') or (0,)
    if isinstance(col, (int, float)): col = (col,)
    col = tuple(col)
    red = len(col) == 3 and col[0] > 0.6 and col[1] < 0.35
    if len(col) == 4: red = col[1] > 0.5 and col[2] > 0.5 and col[0] < 0.3  # CMYK red-ish
    blue = (len(col) == 3 and col[2] > 0.5 and col[0] < 0.3) or (len(col) == 4 and col[0] > 0.6 and col[1] > 0.2 and col[2] < 0.2)
    sans = any(s in fn for s in ('Gotham', 'Joey', 'Arial', 'Cairo', 'Tahoma'))
    bold = any(s in fn for s in ('Bold', 'Black', 'Heavy', 'Semibold', 'Medium'))
    ital = any(s in fn for s in ('Ital', '-It', 'Oblique'))
    return dict(fn=fn, sans=sans, bold=bold, ital=ital, red=red, blue=blue, size=round(w['size'], 1))

CIDMAP = json.load(open('/home/claude/batch/cidmap.json'))
CIDRE = re.compile(r'\(cid:(\d+)\)')
def fix_cids(pg):
    for c in pg.chars:
        if '(cid:' in c['text']:
            m = CIDMAP.get(c['fontname'], {})
            c['text'] = CIDRE.sub(lambda g: m.get(g.group(1), '?'), c['text'])

def words_of(pg):
    fix_cids(pg)
    ws = pg.extract_words(extra_attrs=['fontname', 'size', 'non_stroking_color'], keep_blank_chars=False, x_tolerance=1.5)
    for w in ws: w.update(style_of(w))
    return ws

def group_lines(ws, tol=2.0):
    ws = sorted(ws, key=lambda w: ((w['top'] + w['bottom']) / 2, w['x0']))
    lines = []
    for w in ws:
        cy = (w['top'] + w['bottom']) / 2
        for L in lines[-4:]:
            if abs((L['top'] + L['bottom']) / 2 - cy) <= tol + 1:
                L['w'].append(w); L['x1'] = max(L['x1'], w['x1']); L['x0'] = min(L['x0'], w['x0']); break
        else:
            lines.append(dict(top=w['top'], bottom=w['bottom'], x0=w['x0'], x1=w['x1'], w=[w]))
    for L in lines: L['w'].sort(key=lambda w: w['x0'])
    return lines

def column_bounds(body, page_w):
    cov = [0] * (int(page_w) + 2)
    for w in body:
        for x in range(int(w['x0']), int(w['x1']) + 1): cov[x] += 1
    cols, inside, start = [], False, 0
    for x, c in enumerate(cov):
        if c and not inside: inside, start = True, x
        if not c and inside:
            # gap must be >= 6pt to count as gutter
            if all(cov[x + k] == 0 for k in range(6) if x + k < len(cov)):
                inside = False; cols.append([start, x])
    if inside: cols.append([start, len(cov) - 1])
    cols = [c for c in cols if c[1] - c[0] > 60]
    return cols

def line_text_segments(L):
    segs = []
    for w in L['w']:
        st = ('i' if w['ital'] else '') + ('b' if w['bold'] and not w['sans'] else '')
        segs.append([w['text'], st])
    return segs

def line_kind(L):
    ws = L['w']; n = len(ws)
    sans = sum(w['sans'] for w in ws) / n; bold = sum(w['bold'] for w in ws) / n
    red = sum(w['red'] for w in ws) / n; blue = sum(w['blue'] for w in ws) / n
    size = collections.Counter(w['size'] for w in ws).most_common(1)[0][0]
    txt = ' '.join(w['text'] for w in ws)
    ital = sum(w['ital'] for w in ws) / n
    hasmove = bool(MOVE_RE.search(txt))
    up = txt.upper()
    if sans > .6 and size <= 8.5 and (up.startswith('AFTER') or up.startswith('ANALYSIS') or 'TO MOVE' in up or up.startswith('POSITION') or up.startswith('VARIATION') or up.startswith('(ANALYSIS')): return 'caption'
    if sans > .6 and bold > .6 and hasmove: return 'ml'
    if sans > .6 and blue > .6 and size <= 8.5: return 'caption'
    if sans > .6 and ital > .5: return 'aside'
    if sans > .6 and red > .5: return 'gamehead'
    if sans > .6 and bold > .6:
        if txt.startswith('(see diagram') or txt.startswith('(See diagram'): return 'note'
        if MOVE_RE.search(txt) or re.match(r'^\d+\s*\.', txt): return 'ml'
        return 'heading'
    if sans > .6 and size <= 8.5: return 'small'
    return 'body'

def extract(path):
    out = dict(file=os.path.basename(path), blocks=[], practicum=None, header={})
    with pdfplumber.open(path) as pdf:
        allitems = []
        for pi, pg in enumerate(pdf.pages):
            ox, oy, pw, ph = pg.bbox[0], pg.bbox[1], pg.bbox[2], pg.bbox[3]
            ws = words_of(pg)
            dias = [im for im in pg.images if abs((im['x1'] - im['x0']) - (im['bottom'] - im['top'])) < 3 and im['x1'] - im['x0'] > 80]
            dnames = {}
            for k, im in enumerate(dias): dnames[id(im)] = f"{os.path.basename(path)[:-4]}_p{pi}_{k}"
            # header/footer
            ws = [w for w in ws if w['top'] > oy + 40 and w['bottom'] < ph - 30 and w['size'] >= 5.5 and '_20' not in w['text']]
            if pi == 0:
                big = [w for w in ws if w['size'] >= 13]
                if big:
                    hb = max(w['bottom'] for w in big)
                    by = [w for w in ws if w['top'] < hb + 40 and w['top'] > hb - 5 and (w['text'] == 'By' or w['bold'] and w['sans'] and w['text'].isupper())]
                    title = [w for w in big if w['size'] >= 25]; dek = [w for w in big if w['size'] < 25]
                    tl = group_lines(title, 6); dl = group_lines(dek, 4)
                    out['header']['title'] = ' '.join(' '.join(x['text'] for x in L['w']) for L in sorted(tl, key=lambda L: (L['top'], L['x0'])))
                    out['header']['dek'] = ' '.join(' '.join(x['text'] for x in L['w']) for L in sorted(dl, key=lambda L: (L['top'], L['x0'])))
                    byl = group_lines(by, 3)
                    out['header']['byline'] = ' '.join(' '.join(x['text'] for x in L['w']) for L in byl)
                    hdr_bottom = max([hb] + [w['bottom'] for w in by])
                    ws = [w for w in ws if w['top'] > hdr_bottom + 2]
            # practicum box
            rects = [r for r in pg.rects if (r['x1'] - r['x0']) > 150 and (r['bottom'] - r['top']) > 60 and r['top'] < oy + 120]
            box = None
            if rects and pi == 1:
                box = (min(r['x0'] for r in rects), min(r['top'] for r in rects), max(r['x1'] for r in rects), max(r['bottom'] for r in rects))
                inb = lambda o: o['x0'] >= box[0] - 2 and o['x1'] <= box[2] + 2 and o['top'] >= box[1] - 2 and o['bottom'] <= box[3] + 2
                bws = [w for w in ws if inb(w)]; bd = [im for im in dias if inb(im)]
                out['practicum'] = parse_practicum(bws, bd, dnames, rects)
                ws = [w for w in ws if not inb(w)]; dias = [im for im in dias if not inb(im)]
            body = [w for w in ws if 8.5 <= w['size'] <= 11.5 and not w['sans']]
            cols = column_bounds(body, pw)
            def colof(x0, x1):
                cx = (x0 + x1) / 2
                for ci, c in enumerate(cols):
                    if c[0] - 8 <= cx <= c[1] + 8: return ci
                return min(range(len(cols)), key=lambda ci: abs((cols[ci][0] + cols[ci][1]) / 2 - cx))
            bycol = collections.defaultdict(list)
            for w in ws:
                bycol[colof(w['x0'], min(w['x1'], w['x0'] + 10))].append(w)
            lines = []
            for ci, cws in bycol.items():
                for L in group_lines(cws):
                    L['col'] = ci; lines.append(L)
            items = []
            for L in lines:
                ci = L['col']
                L['col'] = ci; L['kind'] = line_kind(L); L['page'] = pi
                items.append(('line', ci, L['top'], L))
            for im in dias:
                ci = colof(im['x0'], im['x1'])
                items.append(('dia', ci, im['top'], dict(name=dnames[id(im)], top=im['top'], bottom=im['bottom'], x0=im['x0'], x1=im['x1'], col=ci, page=pi)))
            items.sort(key=lambda t: (t[1], t[2]))
            for t in items:
                t[3]['colL'], t[3]['colR'] = cols[t[1]] if cols else (0, pw)
            allitems += [(pi,) + t for t in items]
        out['blocks'] = assemble(allitems)
    return out

def parse_practicum(bws, bd, dnames, rects):
    lines = group_lines(bws, 2)
    bd = sorted(bd, key=lambda im: im['x0'])
    left_edge = min(im['x0'] for im in bd) - 10 if bd else 1e9
    intro = [L for L in lines if L['x1'] < left_edge + 5]
    probs = []
    for k, im in enumerate(bd):
        lo = im['x0'] - 12; hi = bd[k + 1]['x0'] - 12 if k + 1 < len(bd) else 1e9
        mine = [L for L in lines if lo <= L['x0'] < hi]
        above = [L for L in mine if L['bottom'] <= im['top'] + 2]
        below = [L for L in mine if L['top'] >= im['bottom'] - 2]
        heading = ' '.join(w['text'] for L in above[:1] for w in L['w'])
        meta = [' '.join(w['text'] for w in L['w']) for L in above[1:]]
        probs.append(dict(dia=dnames[id(im)], heading=heading, meta=meta, caption=' '.join(w['text'] for L in below for w in L['w'])))
    title = ''; ptxt = []
    for L in sorted(intro, key=lambda L: L['top']):
        t = ' '.join(w['text'] for w in L['w'])
        if not title and L['w'][0]['size'] >= 11: title = t; continue
        ptxt.append(t)
    return dict(title=title, intro=dehyphen_join(ptxt), problems=probs)

def dehyphen_join(lines):
    s = ''
    for t in lines:
        if s.endswith('-') and t[:1].islower(): s = s[:-1] + t
        else: s = (s + ' ' + t).strip()
    return s

def assemble(allitems):
    """Turn ordered lines/diagrams into blocks: p, ml, heading, gamehead, dia."""
    blocks = []
    last_body = None  # last body paragraph block (for column continuation)
    prev = None
    for pi, typ, ci, top, o in allitems:
        if typ == 'dia':
            blocks.append(dict(type='dia', name=o['name'], caption='', top=o['top'], bottom=o['bottom'], page=pi, col=ci))
            prev = ('dia', o); continue
        L = o; k = L['kind']
        if k == 'caption':
            # attach to the nearest diagram above in same column/page
            for b in reversed(blocks[-4:]):
                if b['type'] == 'dia' and b['page'] == pi and b['col'] == ci and 0 <= L['top'] - b['bottom'] < 30:
                    b['caption'] = (b['caption'] + ' ' + ' '.join(w['text'] for w in L['w'])).strip(); break
            else:
                blocks.append(dict(type='caption_orphan', text=' '.join(w['text'] for w in L['w'])))
            continue
        if k == 'note': prev = ('note', L); continue
        segs = line_text_segments(L)
        if k == 'heading' and prev and prev[0] == 'line' and prev[1]['kind'] == 'ml':
            txt0 = ' '.join(w['text'] for w in L['w'])
            if re.match(r'^(?:[KQRBN]?[a-h]?[1-8]?x?[a-h][1-8]|O-O|0-0)', txt0): k = L['kind'] = 'ml'
        if k in ('heading', 'gamehead', 'ml', 'small', 'aside'):
            same = blocks and blocks[-1]['type'] == k and prev and prev[0] == 'line' and prev[1]['kind'] == k and \
                (prev[1]['col'] != L['col'] or L['top'] - prev[1]['top'] < 16)
            if same and k != 'gamehead': blocks[-1]['lines'].append(segs)
            else: blocks.append(dict(type=k, lines=[segs]))
            prev = ('line', L); continue
        # body
        colL, colR = L['colL'], L['colR']
        indent = L['x0'] - colL
        newpara = True
        if prev and prev[0] == 'line' and prev[1]['kind'] == 'body':
            P = prev[1]
            if P['col'] == L['col'] and P['page'] == L['page']:
                short = P['x1'] < colR - 14
                gap = L['top'] - P['top'] > 17
                ptxt = P['w'][-1]['text']
                ind = L['x0'] > P['x0'] + 3 and re.search(r'[.!?:”"]$', ptxt) is not None
                newpara = short or gap or ind
            else:
                ptxt = P['w'][-1]['text']
                newpara = P['x1'] < P['colR'] - 14 or (indent > 4 and re.search(r'[.!?:”"]$', ptxt) is not None)
        elif prev and prev[0] in ('dia', 'note') and last_body is not None and indent <= 4:
            newpara = False  # paragraph continues after a diagram / column break
        if not newpara and last_body is not None:
            last_body['lines'].append(segs)
            last_body['blockind'] = last_body.get('blockind', False)
        else:
            last_body = dict(type='p', lines=[segs], ind=round(indent))
            blocks.append(last_body)
        prev = ('line', L)
    return blocks

if __name__ == '__main__':
    files = sys.argv[1:] or sorted(glob.glob('pdfs/*.pdf'))
    os.makedirs('ext', exist_ok=True)
    for f in files:
        d = extract(f)
        json.dump(d, open('ext/' + os.path.basename(f)[:-4] + '.json', 'w'), indent=1, ensure_ascii=False)
    print('done', len(files))
