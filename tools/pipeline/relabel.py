import numpy as np, json
L="B r P q K b R K K p B p K B k K P n r b r b p R Q B b P N R p p q k P K p n k K P q B k b k P b".split()
F=np.load('allF.npy'); idx=np.load('cl_idx.npy'); a=np.load('cl_a.npy')
X=[np.load('tX.npy')]; Y=[np.load('tY.npy')]
for k in range(48):
    m=idx[a==k]; c=F[m].mean(0); d=((F[m]-c)**2).sum(1); keep=m[d<=np.percentile(d,60)]
    X.append(F[keep]); Y.append(np.array([L[k]]*len(keep)))
X=np.vstack(X); Y=np.concatenate(Y); np.save('tX2.npy',X); np.save('tY2.npy',Y)
d=(F**2).sum(1)[:,None]+(X**2).sum(1)[None]-2*F@X.T
o=np.argsort(d,1)[:,:3]; lab=Y[o[:,0]]; dist=d[np.arange(len(F)),o[:,0]]
# disagreement among 3 nearest
dis=(Y[o[:,0]]!=Y[o[:,1]])|(Y[o[:,0]]!=Y[o[:,2]])
np.save('lab.npy',lab); np.save('dist.npy',dist)
names=json.load(open('names.json')); bad=[]
fens={}
for i,n in enumerate(names):
    g=lab[i*64:(i+1)*64]; rows=[]
    for r in range(8):
        s='';e=0
        for c in range(8):
            ch=g[r*8+c]
            if ch=='.': e+=1
            else:
                if e: s+=str(e);e=0
                s+=ch
        if e: s+=str(e)
        rows.append(s)
    fen='/'.join(rows); fens[n]=fen
    issues=[]
    if list(g).count('K')!=1: issues.append(f"K={list(g).count('K')}")
    if list(g).count('k')!=1: issues.append(f"k={list(g).count('k')}")
    if any(x in 'Pp' for x in list(g[:8])+list(g[56:])): issues.append('pawn on back rank')
    nd=int(dis[i*64:(i+1)*64].sum());
    if nd: issues.append(f'{nd} unsure')
    if issues: bad.append((n,fen,issues))
json.dump(fens,open('fens.json','w'),indent=0)
print('diagrams',len(names),'flagged',len(bad))
for b in bad: print(b)
