import numpy as np, json, sys
from PIL import Image, ImageDraw
names=json.load(open('names.json')); lab=np.load('lab.npy'); dist=np.load('dist.npy')
def sqimg(idx):
    n=names[idx//64]; s=idx%64; im=Image.open(f'dia/{n}.png').convert('L'); h,w=im.height,im.width
    r,c=divmod(s,8); return im.crop((int(c*w/8),int(r*h/8),int((c+1)*w/8),int((r+1)*h/8))).resize((48,48))
def mont(idxs,out,cols=30):
    rows=(len(idxs)+cols-1)//cols; W=Image.new('L',(cols*52,rows*64),255); d=ImageDraw.Draw(W)
    for k,i in enumerate(idxs):
        x,y=(k%cols)*52,(k//cols)*64; W.paste(sqimg(i),(x,y)); d.text((x+2,y+49),f'{k}{lab[i]}',fill=0)
    W.save(out)
if __name__=='__main__':
    thr=float(sys.argv[1]); idx=np.where(dist>thr)[0]; idx=idx[np.argsort(-dist[idx])]
    print(len(idx)); np.save('unc.npy',idx[:300]); mont(idx[:300],'look/unc.png')
