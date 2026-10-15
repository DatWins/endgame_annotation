import numpy as np, json
from PIL import Image, ImageDraw
from montage import sqimg
F=np.load('allF.npy'); dist=np.load('dist.npy')
idx=np.where(dist>8)[0]; X=F[idx]
rng=np.random.default_rng(0); K=48
C=X[rng.choice(len(X),K,replace=False)]
for it in range(30):
    d=(X**2).sum(1)[:,None]+(C**2).sum(1)[None]-2*X@C.T; a=d.argmin(1)
    for k in range(K):
        if (a==k).any(): C[k]=X[a==k].mean(0)
np.save('cl_idx.npy',idx); np.save('cl_a.npy',a)
cols=12; W=Image.new('L',(cols*50+60,K*50),255); dr=ImageDraw.Draw(W)
for k in range(K):
    m=idx[a==k]; dr.text((2,k*50+20),f'{k}:{len(m)}',fill=0)
    for j,i in enumerate(rng.choice(m,min(cols,len(m)),replace=False) if len(m) else []):
        W.paste(sqimg(i).resize((46,46)),(60+j*50,k*50))
W.save('look/clus.png'); print(len(idx))
