"""Recover text for glyphs without ToUnicode by matching glyph outlines against fonts that do have it."""
import glob, io, json, collections, hashlib
import pdfplumber
from pdfminer.pdftypes import resolve1
from pdfminer.cmapdb import CMapParser, FileUnicodeMap
from pdfminer.psparser import PSLiteral
from fontTools.cffLib import CFFFontSet
from fontTools.pens.recordingPen import RecordingPen
from fontTools.agl import toUnicode

Q = 1
def sig(cs):
    pen = RecordingPen()
    try: cs.draw(pen)
    except Exception: return None
    s = repr([(op, [tuple(round(v / Q) for v in p) for p in pts]) for op, pts in pen.value])
    return hashlib.md5(s.encode()).hexdigest()

def font_info(fobj):
    f = resolve1(fobj)
    sub = f.get('Subtype'); sub = sub.name if isinstance(sub, PSLiteral) else str(sub)
    desc = None; cid = False
    if sub == 'Type0':
        d = resolve1(resolve1(f['DescendantFonts'])[0]); desc = resolve1(d.get('FontDescriptor')); cid = True
    else:
        desc = resolve1(f.get('FontDescriptor')) if f.get('FontDescriptor') else None
    if not desc or 'FontFile3' not in desc: return None
    name = desc.get('FontName'); name = name.name if isinstance(name, PSLiteral) else str(name)
    data = resolve1(desc['FontFile3']).get_data()
    try:
        c = CFFFontSet(); c.decompile(io.BytesIO(data), None); top = c[c.fontNames[0]]
    except Exception: return None
    tu = None
    if 'ToUnicode' in f:
        try:
            cmap = FileUnicodeMap(); CMapParser(cmap, io.BytesIO(resolve1(f['ToUnicode']).get_data())).run(); tu = cmap.cid2unichr
        except Exception: tu = None
    return dict(name=name, top=top, cid=cid, tu=tu, f=f)

import sys
Q = int(sys.argv[1]) if len(sys.argv) > 1 else 1
ref = collections.defaultdict(collections.Counter)   # sig -> unicode counts
needs = {}                                            # fontname -> {cid: sig}
for path in sorted(glob.glob('pdfs/*.pdf')):
    with pdfplumber.open(path) as pdf:
        for pg in pdf.pages:
            res = resolve1(pg.page_obj.resources); fonts = resolve1(res.get('Font', {})) or {}
            for k, v in fonts.items():
                fi = font_info(v)
                if not fi: continue
                top = fi['top']; cs = top.CharStrings
                charset = top.charset
                if fi['cid']:
                    # glyph names 'cidNNNNN' -> cid
                    for gname in charset:
                        if gname == '.notdef': continue
                        cidn = int(gname[3:]) if gname.startswith('cid') else None
                        if cidn is None: continue
                        s = sig(cs[gname])
                        if not s: continue
                        if fi['tu'] and cidn in fi['tu']: ref[s][fi['tu'][cidn]] += 1
                        elif not fi['tu']: needs.setdefault(fi['name'], {})[cidn] = s
                else:
                    for gname in charset:
                        if gname == '.notdef': continue
                        u = toUnicode(gname)
                        s = sig(cs[gname])
                        if s and u: ref[s][u] += 1
table = {}; missing = collections.Counter()
for fname, m in needs.items():
    table[fname] = {}
    for cidn, s in m.items():
        if s in ref: table[fname][cidn] = ref[s].most_common(1)[0][0]
        else: missing[fname] += 1
json.dump(table, open(f'cidmap_q{Q}.json', 'w'), ensure_ascii=False, indent=0)
print('fonts needing map', len(needs), 'resolved glyphs', sum(len(v) for v in table.values()), 'unresolved', sum(missing.values()))
print(missing.most_common(10))

if __name__ == '__main__' and len(sys.argv) > 2:
    # render unresolved glyphs to a sheet for manual labelling
    from fontTools.pens.svgPathPen import SVGPathPen
    out = []
    for path in sorted(glob.glob('pdfs/*.pdf')):
        with pdfplumber.open(path) as pdf:
            for pg in pdf.pages:
                res = resolve1(pg.page_obj.resources); fonts = resolve1(res.get('Font', {})) or {}
                for k, v in fonts.items():
                    fi = font_info(v)
                    if not fi or fi['tu'] or not fi['cid']: continue
                    for gname in fi['top'].charset:
                        if not gname.startswith('cid'): continue
                        cidn = int(gname[3:])
                        if str(cidn) in table.get(fi['name'], {}) or cidn in table.get(fi['name'], {}): continue
                        pen = SVGPathPen(None); fi['top'].CharStrings[gname].draw(pen)
                        out.append((fi['name'], cidn, pen.getCommands()))
    seen = set(); cells = []
    for i, (n, c, d) in enumerate(out):
        if (n, c) in seen: continue
        seen.add((n, c)); cells.append((n, c, d))
    svg = ['<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="%d">' % (110 * ((len(cells) + 9) // 10))]
    for i, (n, c, d) in enumerate(cells):
        x, y = (i % 10) * 120, (i // 10) * 110
        svg.append(f'<g transform="translate({x+20},{y+80}) scale(0.07,-0.07)"><path d="{d}"/></g><text x="{x+5}" y="{y+100}" font-size="11">{i}</text>')
    svg.append('</svg>')
    open('look/glyphs.svg', 'w').write('\n'.join(svg))
    json.dump([(n, c) for n, c, d in cells], open('look/glyphs.json', 'w'))
    print('cells', len(cells))
