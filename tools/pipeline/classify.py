import numpy as np, json, glob, os
from PIL import Image
def squares(path):
    im = np.asarray(Image.open(path).convert('L'), dtype=np.float32)
    lo, hi = np.percentile(im, 0.5), np.percentile(im, 99.5)
    im = np.clip((im - lo) / max(hi - lo, 1) * 255, 0, 255)
    h, w = im.shape; out = []
    for r in range(8):
        for c in range(8):
            y0, y1 = int(r*h/8), int((r+1)*h/8); x0, x1 = int(c*w/8), int((c+1)*w/8)
            m = int((y1-y0)*0.06)
            sq = im[y0+m:y1-m, x0+m:x1-m]
            ink = (sq < 110).astype(np.float32)
            f = np.asarray(Image.fromarray((ink*255).astype(np.uint8)).resize((20, 20), Image.BILINEAR), dtype=np.float32)/255
            out.append(f.ravel())
    return np.array(out)
def fen_grid(fen):
    g = []
    for row in fen.split()[0].split('/'):
        for ch in row: g += ['.']*int(ch) if ch.isdigit() else [ch]
    return g
if __name__ == '__main__':
    known = {
     'June_2017_073_Logical_Illogicality_p0_0': '8/1r4p1/2n3K1/2kNp2P/1p2P3/1R6/8/8',
     'June_2017_073_Logical_Illogicality_p0_1': '8/1r4RK/8/4p2P/1n2k3/8/8/8',
     'June_2017_073_Logical_Illogicality_p1_1': '8/7K/1r4R1/4p2P/1n2k3/8/8/8',
     'June_2017_073_Logical_Illogicality_p1_2': '7Q/8/6K1/8/8/3kp3/2n5/8',
     'June_2017_073_Logical_Illogicality_p1_0': '8/1r4p1/6K1/2k1p2P/1n2P3/5R2/8/8',
     'June_2017_073_Logical_Illogicality_p1_3': '8/6kn/5pp1/4Nq2/3Qp2p/4P2P/6P1/7K',
     'June_2017_073_Logical_Illogicality_p1_4': '8/6p1/8/4kn2/3p2PP/3K4/8/6B1'}
    X=[];Y=[]
    for n,f in known.items():
        X.append(squares(f'dia/{n}.png')); Y += fen_grid(f)
    X=np.vstack(X); Y=np.array(Y)
    np.save('tX.npy',X); np.save('tY.npy',Y)
    # classify all with nearest template
    names=[os.path.basename(p)[:-4] for p in sorted(glob.glob('dia/*.png'))]
    feats={n:squares(f'dia/{n}.png') for n in names}
    allF=np.vstack([feats[n] for n in names])
    d=(allF**2).sum(1)[:,None]+(X**2).sum(1)[None,:]-2*allF@X.T
    j=d.argmin(1); lab=Y[j]; dist=d.min(1)
    np.save('allF.npy',allF); json.dump(names,open('names.json','w'))
    print('labels', dict(zip(*np.unique(lab,return_counts=True))))
    print('dist pct', np.percentile(dist,[50,90,99,99.9]).round(1))
    np.save('lab.npy',lab); np.save('dist.npy',dist)
