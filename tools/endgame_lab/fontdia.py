import pdfplumber, collections, sys, json
def clusters(pg):
    ch=[c for c in pg.chars if 'Diagram' in c['fontname']]
    n=len(ch); par=list(range(n))
    def f(i):
        while par[i]!=i: par[i]=par[par[i]]; i=par[i]
        return i
    for i in range(n):
        for j in range(i+1,n):
            a,b=ch[i],ch[j]; s=a['size']
            if abs(a['size']-b['size'])<0.5 and abs(a['x0']-b['x0'])<=2.1*s and abs(a['top']-b['top'])<=2.1*s: par[f(i)]=f(j)
    G=collections.defaultdict(list)
    for i in range(n): G[f(i)].append(ch[i])
    out=[]
    for cs in G.values():
        out.append(dict(c=cs,x0=min(c['x0'] for c in cs),x1=max(c['x0'] for c in cs),t0=min(c['top'] for c in cs),t1=max(c['top'] for c in cs),s=cs[0]['size']))
    out.sort(key=lambda g:(g['x0']//150,g['t0']))
    return out
def grid(g):
    s=g['s']; G=[[[] for _ in range(8)] for _ in range(8)]
    for c in g['c']:
        col=round((c['x0']-g['x0'])/s); row=round((c['top']-g['t0'])/s)
        if 0<=col<8 and 0<=row<8: G[row][col].append(c['text'])
        else: G.append(('OUT',c['text'],col,row))
    return G
if __name__=='__main__':
    pdf=pdfplumber.open('benko.pdf')
    for p in map(int,sys.argv[1:]):
        for g in clusters(pdf.pages[p]):
            G=grid(g); print('page',p+1,'at',round(g['x0']),round(g['t0']),'size',g['s'],'span',round(g['x1']-g['x0']),round(g['t1']-g['t0']))
            for r in G[:8]: print('   ',' '.join((''.join(x for x in sq if x not in '+') or ('+' if '+' in sq else '.')).ljust(9) for sq in r))
            for o in G[8:]: print('   ',o)
