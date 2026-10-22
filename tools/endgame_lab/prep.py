"""Turn extracted line segments into clean paragraph HTML (dehyphenation, split-word repair, italics)."""
import json, glob, re, html, collections, os

exts = {os.path.basename(f)[:-5]: json.load(open(f)) for f in sorted(glob.glob('ext/*.json'))}
WORD = re.compile(r"^[A-Za-z]+$")
freq = collections.Counter(); hyph = collections.Counter()
for d in exts.values():
    for b in d['blocks']:
        for segs in b.get('lines', []):
            toks = [s[0] for s in segs]
            for t in toks[1:-1]:
                t2 = t.strip('.,;:!?()“”"’‘—').lower()
                if WORD.match(t2): freq[t2] += 1
                elif re.match(r'^[a-z]+-[a-z]+$', t2): hyph[t2] += 1

def known(w): return freq[w.lower()] >= 1

def fix_splits(tokens):
    out = []; i = 0
    while i < len(tokens):
        t = tokens[i]
        done = False
        for n in (3, 2):
            if i + n <= len(tokens):
                parts = [x[0] for x in tokens[i:i + n]]
                core = [p.strip('.,;:!?)”’') for p in parts]
                if all(WORD.match(c) for c in core[:-1]) and WORD.match(core[-1] or 'x') and parts[0][:1].isalpha():
                    joined = ''.join(core)
                    if freq[joined.lower()] >= 2 and any(not known(c) for c in core):
                        out.append([''.join(parts), tokens[i][1]]); i += n; done = True; break
        if not done: out.append(t); i += 1
    return out

def join_lines(lines):
    toks = []
    for segs in lines:
        segs = [list(s) for s in segs if s[0]]
        if len(segs) >= 2 and segs[-1][0] in ('-', '‐'):
            segs[-2][0] += '-'; segs = segs[:-1]
        if toks and segs:
            left, right = toks[-1][0], segs[0][0]
            lcore = left.rstrip('-‐')
            rcore = right.strip('.,;:!?)”’')
            if left.endswith(('-', '‐')) and len(left) > 1:
                keep = bool(re.search(r'[a-h][1-8]$|\d$', lcore)) or '-' in lcore or right[:1].isupper() or right[:1].isdigit()
                if not keep:
                    j = (re.sub(r'^\W+', '', lcore) + rcore).lower()
                    hy = (re.sub(r'^\W+', '', lcore) + '-' + rcore).lower()
                    keep = freq[j] == 0 and hyph[hy] > 0
                toks[-1][0] = (left if keep else lcore) + right
                segs = segs[1:]
            elif WORD.match(left) and right[:1].islower() and WORD.match(rcore) and freq[(left + rcore).lower()] >= 1 and not known(rcore):
                toks[-1][0] = left + right; segs = segs[1:]
        toks += segs
    toks = fix_splits(toks)
    # build html with italic/bold runs
    out = []; cur = None; buf = []
    def flush():
        if buf:
            t = html.escape(' '.join(buf), quote=False)
            if cur and 'i' in cur: t = f'<i>{t}</i>'
            if cur and 'b' in cur: t = f'<b>{t}</b>'
            out.append(t)
    for t, st in toks:
        if st != cur: flush(); buf = []; cur = st
        buf.append(t)
    flush()
    s = ' '.join(out)
    s = re.sub(r'</i> <i>', ' ', s)
    s = re.sub(r'\s+([,;:)]|\.(?!\.))', r'\1', s)  # no space before punctuation (but keep '. ...')
    s = re.sub(r'\(\s+', '(', s)
    s = re.sub(r'\b([a-h])- (pawns?|file|files)\b', r'\1-\2', s)
    s = re.sub(r'(</[ib]>)\s+([,.;:!?)’”])', r'\1\2', s)
    return s

os.makedirs('prep', exist_ok=True)
REORDER = json.load(open('reorder.json')) if os.path.exists('reorder.json') else {}
for name, d in exts.items():
    blocks = []
    for b in d['blocks']:
        t = b['type']
        if t == 'dia':
            blocks.append(dict(type='dia', name=b['name'], caption=b['caption'])); continue
        if t == 'fig':
            cp = re.sub(r'^(Above|Below|Left|Right):\s*', '', b.get('caption', '')); blocks.append(dict(type='fig', name=b['name'], caption=cp[:1].upper() + cp[1:])); continue
        if t == 'caption_orphan':
            if blocks and blocks[-1]['type'] == 'aside': blocks[-1]['html'] += ' ' + html.escape(b['text'])
            else: blocks.append(dict(type='aside', html=html.escape(b['text'])))
            continue
        if t == 'gamehead':
            blocks.append(dict(type='gamehead', html=join_lines(b['lines']))); continue
        blocks.append(dict(type=t, html=join_lines(b['lines'])))
    # merge consecutive gamehead lines that wrapped (line not starting with title/name pattern)
    merged = []
    for b in blocks:
        if b['type'] == 'gamehead' and merged and merged[-1]['type'] == 'gamehead' and (b['html'][:1].islower() or re.match(r'^[A-Z][a-z]+, \d', b['html']) or merged[-1]['html'].endswith(',')):
            merged[-1]['html'] += ' ' + b['html']
        else: merged.append(b)
    # headings that wrapped onto two lines arrive as two blocks
    m2 = []
    for b in merged:
        if b['type'] == 'heading' and m2 and m2[-1]['type'] == 'heading': m2[-1]['html'] += ' ' + b['html']
        else: m2.append(b)
    merged = m2
    for b in merged:
        if b['type'] in ('heading', 'gamehead'):
            b['html'] = re.sub(r"([A-Za-z]+)-([A-Za-z’']+)", lambda m: m.group(1) + m.group(2) if freq[(m.group(1) + m.group(2)).lower().strip("’'")] or freq[(m.group(1) + m.group(2)).lower().split('’')[0]] else m.group(0), b['html'])
    # words split by a line/column break that the line joiner missed ("submis sion", "prac-tically")
    for b in merged:
        if b.get('html') and b['type'] in ('p', 'aside', 'small'):
            def _j(m):
                a_, b_ = m.group(1), m.group(3)
                if freq[(a_ + b_).lower()] and (not freq[a_.lower()] or not freq[b_.lower()]): return a_ + b_
                return m.group(0)
            b['html'] = re.sub(r"\b([A-Za-z]{2,})(-? )([a-z]{2,})\b", _j, b['html'])
            b['html'] = re.sub(r"\b([a-z]{2,})-([a-z]{2,})\b", lambda m: m.group(1) + m.group(2) if freq[(m.group(1) + m.group(2)).lower()] >= 2 and not hyph[m.group(0).lower()] else m.group(0), b['html'])
    WORDFIX = [(r'\bblackthis\b', 'black this'), (r'\btheposition\b', 'the position'), (r'\bbish-op', 'bishop'), (r'\bYou-Tube', 'YouTube'), (r'\bBuda[ -]pest', 'Budapest'), (r'\bSinga[ -]pore', 'Singapore')]
    for b in merged:
        if b.get('html'):
            for a_, b_ in WORDFIX: b['html'] = re.sub(a_, b_, b['html'])
    # manual reading-order fixes: move blocks [a, b) to position c (game header printed after its first moves)
    for a, b, c in REORDER.get(name, []):
        seg = merged[a:b]; del merged[a:b]; merged[c:c] = seg
    pr = d['practicum']
    d['header']['dek'] = re.sub(r'\s+([,.;:!?])', r'\1', d['header'].get('dek', ''))
    json.dump(dict(name=name, header=d['header'], blocks=merged, practicum=pr), open(f'prep/{name}.json', 'w'), indent=1, ensure_ascii=False)
print('prepared', len(exts), 'vocab', len(freq))
