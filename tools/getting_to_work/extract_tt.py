"""Extract structured content from Tatev Abrahamyan's "Getting to Work" columns (Chess Life 2023-2025).
Adapted from the Naroditsky pipeline's extract.py: three-column layout, Source Serif body,
Source Sans bold main line, red game headers, Remora display fonts for title/dek/byline, drop caps.
Usage: python3 extract_tt.py   (reads arts.json + cols.pdf, writes ext/<slug>.json)
"""
import pdfplumber, json, re, os, collections, sys
from extract_base import style_of, group_lines, column_bounds, assemble, MOVE_RE

# Regions holding the column on back pages where it was "continued from page N" (x0, top, x1, bottom)
CROPS = {
    21: [(390, 95, 594, 752)],
    54: [(378, 132, 594, 372)],
    60: [(284, 392, 416, 572), (414, 48, 594, 572)],
    63: [(40, 395, 594, 752)],
}
OK_FONTS = ('SourceSerif', 'SourceSans')
# Pictures that belong to the article (screenshots, photos): (pdf page, x0, top) of the image
EXCLUDE = {49: [(50, 388, 560, 726)]}   # benefactors box
FIGS = {(7, 35, 53), (8, 218, 58), (56, 35, 56), (57, 226, 497)}
SIDEBAR = re.compile(r'Chess Life Online|uschess\.org/|up-to-date chess news|on a regular basis|^clo\b', re.I)

def words_of(pg):
    ws = pg.extract_words(extra_attrs=['fontname', 'size', 'non_stroking_color'], keep_blank_chars=False, x_tolerance=1.5)
    for w in ws: w.update(style_of(w))
    return ws

import extract_base
def line_text_segments(L):
    segs = []
    for w in L['w']:
        # in prose, black sans-bold moves are main line; blue sans-bold moves are highlighted variations
        b = w['bold'] and (not w['sans'] or (L['kind'] == 'body' and not w['blue']))
        segs.append([w['text'], ('i' if w['ital'] else '') + ('b' if b else '')])
    return segs
extract_base.line_text_segments = line_text_segments

def line_kind(L):
    ws = L['w']; n = len(ws)
    # a line mixing main-line moves (sans bold) with prose (serif) is prose with bold moves
    sb = sum(w['sans'] and w['bold'] for w in ws) / n; serif = sum(not w['sans'] for w in ws) / n
    if sb >= .2 and serif >= .25: return 'body'
    sans = sum(w['sans'] for w in ws) / n; bold = sum(w['bold'] for w in ws) / n
    red = sum(w['red'] for w in ws) / n; blue = sum(w['blue'] for w in ws) / n
    ital = sum(w['ital'] for w in ws) / n
    size = collections.Counter(w['size'] for w in ws).most_common(1)[0][0]
    txt = ' '.join(w['text'] for w in ws); up = txt.upper()
    if txt.lower().startswith(('(see diagram', '(continued', 'continued from')): return 'note'
    if sans > .6 and bold > .6 and size >= 10.5: return 'heading'
    if sans > .6 and red > .5: return 'gamehead'
    if sans > .6 and size <= 9 and ('TO MOVE' in up or up.startswith(('POSITION AFTER', 'ANALYSIS AFTER', 'AFTER '))): return 'caption'
    if sans > .6 and blue > .5 and size <= 9 and not MOVE_RE.search(txt): return 'caption'
    if sans > .6 and bold > .6 and size < 10.5: return 'ml'
    if sans > .6 and bold > .6 and size >= 10.5: return 'heading'
    if sans > .6 and bold > .6: return 'ml'
    if sans > .6 and ital > .5: return 'aside'
    if sans > .6: return 'small'
    return 'body'

def extract(art, pdf):
    out = dict(name=art['slug'], blocks=[], practicum=None, header={})
    allitems = []; unit = 0
    for k, pi in enumerate(art['pages']):
        pg = pdf.pages[pi]
        allw = words_of(pg)
        ims = [im for im in pg.images if abs((im['x1'] - im['x0']) - (im['bottom'] - im['top'])) < 3 and im['x1'] - im['x0'] > 80]
        others = [im for im in pg.images if im not in ims and im['x1'] - im['x0'] >= 60 and im['bottom'] - im['top'] >= 40]
        figs = [im for im in others if (pi, int(im['x0']), int(im['top'])) in FIGS]
        inside = lambda w, im: w['x0'] >= im['x0'] - 2 and w['x1'] <= im['x1'] + 2 and w['top'] >= im['top'] - 2 and w['bottom'] <= im['bottom'] + 2
        for im in figs:
            im['caption'] = ' '.join(w['text'] for w in sorted(allw, key=lambda w: (round(w['top']), w['x0'])) if inside(w, im) and w['size'] > 5 and 'Semibold' in w['fn'])
        allw = [w for w in allw if not any(inside(w, im) for im in others)]
        allw = [w for w in allw if not any(inside(w, dict(zip(('x0', 'top', 'x1', 'bottom'), b))) for b in EXCLUDE.get(pi, []))]
        if k == 0:  # title block: title (huge), dek (medium ~19pt), byline (the line naming the author)
            disp = [w for w in allw if 'Remora' in w['fn'] and w['top'] > 45]
            byw = [w for w in allw if w['top'] > 45 and w['top'] < 330 and 10 <= w['size'] < 14 and w['text'].upper() in ('TATEV', 'ABRAHAMYAN', 'WGM', 'IM', 'GM')]
            for w in byw: w['text'] = '\u0000'   # keep the byline out of the body text
            by_top = min((w['top'] for w in byw), default=300); by_bot = max((w['bottom'] for w in byw), default=300)
            big = [w for w in disp if w['size'] >= 30]
            cap = [w for w in big if len(w['text']) == 1 and w['text'].isalpha() and w['size'] > 40 and
                   w['top'] > min(x['top'] for x in big) + 60]
            title = [w for w in big if w not in cap]
            dek = [w for w in disp if 17.5 <= w['size'] < 21 and 'W1' in w['fn'] and w['top'] < by_top]
            j = lambda ws: ' '.join(' '.join(x['text'] for x in L['w']) for L in sorted(group_lines(ws, 6), key=lambda L: (L['top'], L['x0'])))
            out['header'] = dict(title=j(title), dek=j(dek), byline='WGM Tatev Abrahamyan')
        def keep(w):
            if any(f in w['fn'] for f in OK_FONTS): return True
            # section headings set in the display font (later issues)
            if 'Remora' in w['fn'] and 11.5 <= w['size'] <= 17.5 and not w['ital'] and not (k == 0 and w['top'] < by_bot + 15):
                return True
            return False
        boxes = CROPS.get(pi, [(0, 45, pg.width, 735)])
        for bx in boxes:
            inb = lambda o: o['x0'] >= bx[0] - 1 and o['x1'] <= bx[2] + 1 and o['top'] >= bx[1] - 1 and o['bottom'] <= bx[3] + 1
            ws = [w for w in allw if inb(w) and keep(w) and w['size'] >= 5.5 and w['text'] != '\u0000'
                  and not (not w['sans'] and w['size'] >= 9.6)]   # pull quotes are set in large serif
            if k == 0 and not out.get('_leadin'):
                out['_leadin'] = True
                lower_vocab = VOCAB
                f = None
                if cap:
                    d = cap[0]
                    cands = [w for w in ws if w['x0'] > d['x1'] - 2 and d['top'] - 5 < w['top'] < d['bottom'] and w['x0'] - d['x1'] < 50]
                    if cands:
                        f = min(cands, key=lambda w: (w['top'], w['x0']))
                        joined = (d['text'] + f['text']).strip('.,;:’\'').lower()
                        sep = ' ' if d['text'] in ('I', 'A') and len(f['text'].strip('.,;:’')) > 1 and joined not in lower_vocab else ''
                        f['text'] = d['text'] + sep + f['text']
                if f is None:   # no drop cap: the first line of capitals in the body
                    caps = [w for w in ws if not w['sans'] and w['text'].isupper()]
                    if caps:
                        top = min(w['top'] for w in caps)
                        if sum(abs(w['top'] - top) < 2 for w in caps) >= 3: f = min((w for w in caps if abs(w['top'] - top) < 2), key=lambda w: w['x0'])
                if f is not None:
                    for w in ws:
                        if abs(w['top'] - f['top']) < 2 and (w['text'].isupper() or w is f) and not w['sans'] and w['x0'] >= f['x0'] - 1:
                            core = w['text'].strip('.,;:’\'')
                            first = w is f
                            parts = core.split(' ')
                            def fix(t, cap1):
                                if t.startswith(('I’', "I'")) or t == 'I': return t[:2] + t[2:].lower()
                                if len(t) == 1: return t if cap1 else t.lower()
                                if t == 'U.S.': return t
                                tt = t[0] + t[1:].lower()
                                if cap1: return tt
                                if t.endswith('-'): return t.lower()
                                if t.lower() not in lower_vocab and tt in CAPS: return tt   # a name
                                return t.lower()
                            rep = ' '.join(fix(p, first and i == 0) for i, p in enumerate(parts))
                            w['text'] = w['text'].replace(core, rep)
            dias = [im for im in ims if inb(im)]
            body = [w for w in ws if 7.5 <= w['size'] <= 11.5 and not w['sans']]
            cols = column_bounds(body or ws, pg.width)
            if not cols: cols = [[bx[0], bx[2]]]
            def colof(x0, x1):
                cx = (x0 + x1) / 2
                for ci, c in enumerate(cols):
                    if c[0] - 8 <= cx <= c[1] + 8: return ci
                return min(range(len(cols)), key=lambda ci: abs((cols[ci][0] + cols[ci][1]) / 2 - cx))
            bycol = collections.defaultdict(list)
            for w in ws: bycol[colof(w['x0'], min(w['x1'], w['x0'] + 10))].append(w)
            items = []
            for ci, cws in bycol.items():
                capmode = False
                for L in sorted(group_lines(cws), key=lambda L: L['top']):
                    lt = ' '.join(w['text'] for w in L['w'])
                    if SIDEBAR.search(lt): continue
                    if re.match(r'^(Above|Below|Left|Right):', lt): capmode = True; out.setdefault('figcap', {})[unit] = lt; last_cap_top = L['top']; continue
                    if capmode and L['top'] - last_cap_top < 13 and all(w['sans'] and not w['bold'] or 'Semibold' in w['fn'] for w in L['w']):
                        out['figcap'][unit] += ' ' + lt; last_cap_top = L['top']; continue
                    capmode = False
                    L['col'] = ci; L['kind'] = line_kind(L); L['page'] = unit
                    items.append(('line', ci, L['top'], L))
            for fi, im in enumerate(f for f in figs if inb(f)):
                ci = colof(im['x0'], im['x0'] + 10)
                items.append(('dia', ci, im['top'], dict(name=f"{art['slug']}_fig{unit}_{fi}", top=im['top'], bottom=im['bottom'], x0=im['x0'], x1=im['x1'], col=ci, page=unit, pdfpage=pi, caption=im.get('caption', ''))))
            for di, im in enumerate(dias):
                ci = colof(im['x0'], im['x1'])
                name = f"{art['slug']}_u{unit}_{di}"
                items.append(('dia', ci, im['top'], dict(name=name, top=im['top'], bottom=im['bottom'], x0=im['x0'], x1=im['x1'], col=ci, page=unit, pdfpage=pi)))
            items.sort(key=lambda t: (t[1], t[2]))
            for t in items: t[3]['colL'], t[3]['colR'] = cols[t[1]] if t[1] < len(cols) else (bx[0], bx[2])
            allitems += [(unit,) + t for t in items]
            unit += 1
    figitems = [t for t in allitems if t[1] == 'dia' and '_fig' in t[4]['name']]
    blocks = assemble(allitems)
    figcap = {t[4]['name']: t[4].get('caption', '') for t in figitems}
    for b in blocks:
        if b['type'] == 'dia' and '_fig' in b['name']:
            b['type'] = 'fig'; u = int(re.search(r'_fig(\d+)_', b['name']).group(1))
            b['caption'] = figcap.get(b['name']) or out.get('figcap', {}).get(u, '')
    blocks = [b for b in blocks if not (b['type'] == 'heading' and 'TATEV ABRAHAMYAN' in ' '.join(s[0] for L in b['lines'] for s in L))]
    # an opening-name heading directly followed by the red player lines belongs to the game header
    for i, b in enumerate(blocks):
        if b['type'] == 'heading' and i + 1 < len(blocks) and blocks[i + 1]['type'] == 'gamehead':
            b['type'] = 'gamehead'; b['opening'] = True
    out['blocks'] = blocks
    out['figs'] = [dict(name=t[4]['name'], pdfpage=t[4]['pdfpage'], box=[t[4]['x0'], t[4]['top'], t[4]['x1'], t[4]['bottom']]) for t in figitems]
    out['dias'] = [dict(name=t[4]['name'], pdfpage=t[4]['pdfpage'], box=[t[4]['x0'], t[4]['top'], t[4]['x1'], t[4]['bottom']]) for t in allitems if t[1] == 'dia' and '_fig' not in t[4]['name']]
    return out

VOCAB = set(); CAPS = set()
if __name__ == '__main__':
    arts = json.load(open('arts.json'))
    import subprocess
    txt = subprocess.run(['pdftotext', 'cols.pdf', '-'], capture_output=True, text=True).stdout
    VOCAB.update(m.lower() for m in re.findall(r"\b[a-z][a-z’']*\b", txt))
    CAPS.update(re.findall(r"\b[A-Z][a-z][a-z’']*\b", txt))
    os.makedirs('ext', exist_ok=True)
    with pdfplumber.open('cols.pdf') as pdf:
        for a in arts:
            d = extract(a, pdf)
            json.dump(d, open(f"ext/{a['slug']}.json", 'w'), indent=1, ensure_ascii=False)
            print(a['slug'], '|', d['header']['title'], '|', len(d['blocks']), 'blocks', len(d['dias']), 'dias')
