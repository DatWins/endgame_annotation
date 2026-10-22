import numpy as np, glob, os, json
from PIL import Image, ImageDraw
names=[os.path.basename(p)[:-4] for p in sorted(glob.glob('dia/*.png'))]
def squares(path):
    im=np.asarray(Image.open(path).convert('L'),dtype=np.float32)
    h,w=im.shape; out=[]; raw=[]
    for r in range(8):
        for c in range(8):
            y0,y1=int(r*h/8),int((r+1)*h/8); x0,x1=int(c*w/8),int((c+1)*w/8); m=int((y1-y0)*0.08)
            sq=im[y0+m:y1-m,x0+m:x1-m]
            dark=(sq<90).astype(np.float32)          # black ink (outlines + black pieces)
            f=np.asarray(Image.fromarray((dark*255).astype(np.uint8)).resize((24,24),Image.BILINEAR),dtype=np.float32)/255
            out.append(f.ravel()); raw.append(Image.fromarray(sq.astype(np.uint8)).resize((40,40)))
    return np.array(out),raw
F=[];R=[];idx=[]
for n in names:
    f,r=squares(f'dia/{n}.png'); F.append(f); R+=r; idx+=[(n,k) for k in range(64)]
F=np.vstack(F); ink=F.mean(1)
np.save('F_b.npy',F); json.dump(idx,open('idx_b.json','w'))
print('squares',len(F)); print(np.percentile(ink,[10,50,60,70,75,80,90]).round(3))
import pickle; pickle.dump(R,open('R_b.pkl','wb'))
