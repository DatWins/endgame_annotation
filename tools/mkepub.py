import re, zipfile, os, uuid, datetime
body = open('epub_body.html', encoding='utf-8').read()
body = body.replace('<br>', '<br/>')
head, rest = body.split('<section id="intro">', 1)
parts = re.findall(r'<section id="(\w+)">(.*?)</section>', '<section id="intro">' + rest, re.S)
titles = {'intro': 'Introduction', 'game': 'Breaking Through the Ramparts', 'draw': 'The Hidden Draw: 50.Nxb4!!', 'practicum': 'Practicum'}
CSS = """
body{font-family:serif;line-height:1.5;margin:0 .4em}
.kicker{font-family:sans-serif;font-size:.75em;font-weight:bold;text-transform:uppercase;color:#555;margin-top:1em}
h1{font-family:sans-serif;font-size:2em;line-height:1.1;margin:.2em 0}
.dek{color:#1f4fa3;font-size:1.2em;margin:.3em 0}
.byline{font-family:sans-serif;font-size:.85em;font-weight:bold}
.byline span{font-weight:normal;color:#555}
h2{font-family:sans-serif;font-size:1.3em;margin:.6em 0 .5em}
h3{font-family:sans-serif;font-size:1.05em;margin:.8em 0 .2em}
p{margin:.5em 0;text-indent:0}
.gamehead{margin:.4em 0 .8em;color:#333}
p.ml{font-weight:bold;font-size:1.15em;margin:1em 0 .4em}
p.ml .mv{color:#1f4fa3}
p.key{font-size:1.25em}
.lines{border-left:3px solid #bbb;padding-left:.8em;margin:1em 0}
.tip{display:none}
.note{font-style:italic;color:#444}
.pmeta{font-size:.9em;color:#444}
.dia{text-align:center;margin:1em 0;page-break-inside:avoid}
.dia img{width:85%;max-width:430px}
.cap{font-family:sans-serif;font-size:.85em;font-weight:bold;color:#1f4fa3;text-align:center;margin:.2em 0 0}
"""
def xhtml(title, inner):
    return f'''<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" lang="en" xml:lang="en">
<head><meta charset="utf-8"/><title>{title}</title><link rel="stylesheet" type="text/css" href="style.css"/></head>
<body>
{inner}
</body></html>'''
os.makedirs('epub/META-INF', exist_ok=True)
files = []
for i, (sid, inner) in enumerate(parts):
    if sid == 'intro': inner = head.strip() + '\n' + inner
    else: inner = inner
    if sid == 'intro': inner = inner.replace('<p class="first">', '<h2>Introduction</h2>\n<p class="first">', 1) if False else inner
    fn = f'{i+1:02d}_{sid}.xhtml'
    open('epub/OEBPS/' + fn, 'w', encoding='utf-8').write(xhtml(titles[sid], inner))
    files.append((fn, titles[sid]))
open('epub/OEBPS/style.css', 'w').write(CSS)
open('epub/OEBPS/cover.xhtml', 'w', encoding='utf-8').write(xhtml('Cover', '<div style="text-align:center"><img src="images/cover.png" alt="Cover" style="max-width:100%;height:auto"/></div>'))
nav = '\n'.join(f'<li><a href="{f}">{t}</a></li>' for f, t in files)
open('epub/OEBPS/nav.xhtml', 'w', encoding='utf-8').write(xhtml('Contents', f'<nav epub:type="toc" id="toc"><h2>Contents</h2><ol>\n{nav}\n</ol></nav>'))
uid = 'urn:uuid:' + str(uuid.uuid5(uuid.NAMESPACE_URL, 'chesslife-2017-06-logical-illogicality'))
ncx = ''.join(f'<navPoint id="np{i}" playOrder="{i}"><navLabel><text>{t}</text></navLabel><content src="{f}"/></navPoint>' for i, (f, t) in enumerate(files, 1))
open('epub/OEBPS/toc.ncx', 'w', encoding='utf-8').write(f'''<?xml version="1.0" encoding="utf-8"?>
<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1"><head><meta name="dtb:uid" content="{uid}"/></head>
<docTitle><text>Logical Illogicality</text></docTitle><navMap>{ncx}</navMap></ncx>''')
imgs = sorted(os.listdir('epub/OEBPS/images'))
man = '\n'.join(f'<item id="img_{os.path.splitext(x)[0]}" href="images/{x}" media-type="image/png"{" properties=\"cover-image\"" if x=="cover.png" else ""}/>' for x in imgs)
man += '\n' + '\n'.join(f'<item id="c{i}" href="{f}" media-type="application/xhtml+xml"/>' for i, (f, t) in enumerate(files))
spine = '<itemref idref="cover"/>' + ''.join(f'<itemref idref="c{i}"/>' for i in range(len(files)))
now = datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
open('epub/OEBPS/content.opf', 'w', encoding='utf-8').write(f'''<?xml version="1.0" encoding="utf-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="bookid">
<metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
<dc:identifier id="bookid">{uid}</dc:identifier><dc:title>Logical Illogicality</dc:title>
<dc:creator>Daniel Naroditsky</dc:creator><dc:publisher>Chess Life (US Chess)</dc:publisher><dc:date>2017-06</dc:date>
<dc:language>en</dc:language><meta property="dcterms:modified">{now}</meta><meta name="cover" content="img_cover"/>
</metadata>
<manifest>
<item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/>
<item id="ncx" href="toc.ncx" media-type="application/x-dtbncx+xml"/>
<item id="css" href="style.css" media-type="text/css"/>
<item id="cover" href="cover.xhtml" media-type="application/xhtml+xml"/>
{man}
</manifest>
<spine toc="ncx">{spine}</spine>
<guide><reference type="cover" title="Cover" href="cover.xhtml"/></guide>
</package>''')
open('epub/META-INF/container.xml', 'w').write('<?xml version="1.0"?><container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container"><rootfiles><rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/></rootfiles></container>')
out = 'Logical Illogicality.epub'
with zipfile.ZipFile(out, 'w') as z:
    z.writestr(zipfile.ZipInfo('mimetype'), 'application/epub+zip', compress_type=zipfile.ZIP_STORED)
    for root, _, fs in os.walk('epub'):
        for f in fs:
            full = os.path.join(root, f); arc = os.path.relpath(full, 'epub')
            z.write(full, arc, compress_type=zipfile.ZIP_DEFLATED)
print(out, os.path.getsize(out), [f for f, _ in files])
