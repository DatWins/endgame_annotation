# Shrink EPUB diagram images: 32-colour palette PNGs look identical on an e-reader
import glob
from PIL import Image
n = 0
for f in glob.glob('epubsrc/*/OEBPS/images/*.png'):
    im = Image.open(f)
    if im.mode == 'P': continue
    im.convert('RGB').quantize(colors=32, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE).save(f, optimize=True); n += 1
print('quantized', n)
