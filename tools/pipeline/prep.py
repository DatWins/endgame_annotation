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
    s = re.sub(r'(</[ib]>)\s+([,.;:!?)’”])', r'\1\2', s)
    return s

os.makedirs('prep', exist_ok=True)
for name, d in exts.items():
    blocks = []
    for b in d['blocks']:
        t = b['type']
        if t == 'dia':
            blocks.append(dict(type='dia', name=b['name'], caption=b['caption'])); continue
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
    pr = d['practicum']
    d['header']['dek'] = re.sub(r'\s+([,.;:!?])', r'\1', d['header'].get('dek', ''))
    json.dump(dict(name=name, header=d['header'], blocks=merged, practicum=pr), open(f'prep/{name}.json', 'w'), indent=1, ensure_ascii=False)
print('prepared', len(exts), 'vocab', len(freq))
