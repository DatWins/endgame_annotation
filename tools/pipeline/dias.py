# Extract every diagram image (page-rendered, correct orientation) and cut into 64 squares
import pdfplumber, glob, os, json, numpy as np
from PIL import Image
os.makedirs('dia', exist_ok=True)
meta = []
for f in sorted(glob.glob('pdfs/*.pdf')):
    slug = os.path.basename(f)[:-4]
    with pdfplumber.open(f) as pdf:
        for pi, pg in enumerate(pdf.pages):
            ims = [im for im in pg.images if abs((im['x1']-im['x0'])-(im['bottom']-im['top'])) < 3 and im['x1']-im['x0'] > 80]
            if not ims: continue
            img = pg.to_image(resolution=400).original.convert('L')
            sx = img.width / float(pg.width)
            for k, im in enumerate(ims):
                ox, oy = pg.bbox[0], pg.bbox[1]
                box = [round(v * sx) for v in (im['x0']-ox, im['top']-oy, im['x1']-ox, im['bottom']-oy)]
                crop = img.crop(box)
                name = f'{slug}_p{pi}_{k}'
                crop.save(f'dia/{name}.png')
                meta.append(dict(name=name, slug=slug, page=pi, x0=im['x0'], top=im['top'], x1=im['x1'], bottom=im['bottom']))
json.dump(meta, open('dia_meta.json', 'w'), indent=0)
print(len(meta))
