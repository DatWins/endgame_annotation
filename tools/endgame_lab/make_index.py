"""Builds index.html for the article library from articles.json.
Run from the repository root:  python tools/make_index.py
"""
import json, html, pathlib

import sys
root = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else pathlib.Path(__file__).resolve().parent.parent
arts = json.loads((root / 'articles.json').read_text(encoding='utf-8'))
arts.sort(key=lambda a: (a.get('date', ''), a.get('num', 0)))
e = html.escape

cards = []
years = []
for a in arts:
    y = a.get('date', '')[:4]
    if y and y not in years:
        years.append(y); cards.append(f'<h2 class="year" id="y{y}">{y}</h2>')
    s = a['slug']
    search = ' '.join(str(a.get(k, '')) for k in ('title', 'dek', 'author', 'column', 'issue', 'players', 'num')).lower()
    cards.append(f'''<article class="card" data-s="{e(search)}">
  <a class="thumb" href="articles/{s}.html"><img src="articles/{s}.jpg" alt="A diagram from {e(a['title'])}" loading="lazy"></a>
  <div class="info">
    <div class="meta">No. {a.get('num', '')} · {e(a.get('issue', ''))}</div>
    <h2><a href="articles/{s}.html">{e(a['title'])}</a></h2>
    <p class="dek">{e(a.get('dek', ''))}</p>
    <p class="by">{e(a.get('author', ''))}{' · ' + e(a['players']) if a.get('players') else ''}</p>
    <div class="btns"><a class="b main" href="articles/{s}.html">Read online</a><a class="b" href="articles/{s}.epub" download>Download EPUB</a></div>
  </div>
</article>''')

page = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Benko Endgame Articles — Endgame Lab</title>
<style>
:root{{--fs:20px;--paper:#fbfaf7;--ink:#1d1f22;--muted:#5d6670;--line:#e2e0da;--card:#fff;--main:#1f4fa3;--mainbg:#1f4fa3;--mainfg:#fff;--btn:#fff;--btnb:#cfd5db}}
:root[data-theme="dark"]{{--paper:#16191d;--ink:#e4e6e9;--muted:#9aa3ad;--line:#2c3238;--card:#1d2126;--main:#86b4ff;--mainbg:#2f5ea8;--mainfg:#fff;--btn:#232930;--btnb:#3a434c}}
*{{box-sizing:border-box}}
html,body{{margin:0;background:var(--paper);color:var(--ink)}}
body{{font-family:Georgia,"Iowan Old Style","Palatino Linotype",serif;font-size:var(--fs);line-height:1.5}}
.home{{color:var(--main);text-decoration:none;white-space:nowrap;font-weight:600}}
.home{{color:var(--main);text-decoration:none;white-space:nowrap;font-weight:600}}
.top{{position:sticky;top:0;z-index:5;display:flex;gap:10px;align-items:center;padding:8px 16px;background:var(--paper);border-bottom:1px solid var(--line);font-family:system-ui,"Segoe UI",sans-serif;font-size:15px}}
.top input{{flex:1;max-width:420px;font:inherit;padding:7px 12px;border:1px solid var(--btnb);border-radius:8px;background:var(--btn);color:var(--ink)}}
.top .sp{{flex:1}}
button{{font:inherit;background:var(--btn);color:var(--ink);border:1px solid var(--btnb);border-radius:7px;padding:6px 12px;cursor:pointer;min-width:40px}}
header.hero{{max-width:1100px;margin:0 auto;padding:36px 16px 10px}}
.kicker{{font-family:system-ui,"Segoe UI",sans-serif;font-size:.7em;font-weight:700;letter-spacing:.06em;text-transform:uppercase;color:var(--muted)}}
h1{{font-family:system-ui,"Segoe UI",sans-serif;font-size:2.2em;line-height:1.1;margin:.15em 0 .2em}}
.sub{{color:var(--muted);margin:0}}
main{{max-width:1100px;margin:0 auto;padding:16px 16px 80px;display:grid;gap:18px}}
.card{{display:flex;gap:22px;background:var(--card);border:1px solid var(--line);border-radius:12px;padding:18px}}
.thumb img{{width:190px;height:auto;display:block;border-radius:4px}}
.info{{min-width:0}}
.meta{{font-family:system-ui,"Segoe UI",sans-serif;font-size:.7em;font-weight:700;letter-spacing:.04em;color:var(--muted)}}
h2{{font-family:system-ui,"Segoe UI",sans-serif;font-size:1.35em;margin:.15em 0}}
h2 a{{color:var(--ink);text-decoration:none}} h2 a:hover{{color:var(--main)}}
.dek{{color:var(--main);margin:.2em 0}}
.by{{color:var(--muted);font-size:.85em;margin:.3em 0 .8em}}
.btns{{display:flex;gap:10px;flex-wrap:wrap;font-family:system-ui,"Segoe UI",sans-serif;font-size:15px}}
.b{{padding:8px 16px;border-radius:8px;border:1px solid var(--btnb);color:var(--ink);text-decoration:none;background:var(--btn)}}
.b.main{{background:var(--mainbg);color:var(--mainfg);border-color:var(--mainbg);font-weight:600}}
.count{{font-family:system-ui,"Segoe UI",sans-serif;font-size:14px;color:var(--muted)}}
h2.year{{font-family:system-ui,"Segoe UI",sans-serif;font-size:1.1em;color:var(--muted);margin:1.2em 0 0;border-bottom:1px solid var(--line);padding-bottom:4px;scroll-margin-top:60px}}
.years{{font-family:system-ui,"Segoe UI",sans-serif;font-size:15px;margin-top:12px;display:flex;gap:8px;flex-wrap:wrap}}
.years a{{padding:5px 12px;border:1px solid var(--btnb);border-radius:16px;color:var(--ink);text-decoration:none;background:var(--btn)}}
.none{{color:var(--muted);font-style:italic}}
@media (max-width:640px){{.card{{flex-direction:column}} .thumb img{{width:100%;max-width:320px}} .top{{flex-wrap:wrap;padding:8px 12px}} .top input{{flex:1 1 100%;max-width:none}} .top .sp{{display:none}}}}
</style>
</head>
<body>
<div class="top">
  <a class="home" href="../" title="Back to My Chess Projects">← My Chess Projects</a>
  <input id="q" type="search" placeholder="Search title, player, issue…" aria-label="Search articles">
  <span class="sp"></span>
  <span class="count" id="count"></span>
  <button id="fm" title="Smaller text">A−</button><button id="fp" title="Larger text">A+</button><button id="dk">Dark</button>
</div>
<header class="hero">
  <div class="kicker">Endgame Lessons · GM Pal Benko · Chess Life, 2008–2013</div>
  <h1>Endgame Lab</h1>
  <p class="sub">All {len(arts)} columns. Read each one online with a live board you can click through, or download the EPUB for your e-reader.</p>
  <nav class="years">{' '.join(f'<a href="#y{y}">{y}</a>' for y in years)}</nav>
</header>
<main id="list">
{chr(10).join(cards)}
<p class="none" id="none" hidden>No articles match your search.</p>
</main>
<script>
(function(){{
const st={{get(k){{try{{return localStorage.getItem('lib_'+k)}}catch(e){{return null}}}},set(k,v){{try{{localStorage.setItem('lib_'+k,v)}}catch(e){{}}}}}};
const cards=[...document.querySelectorAll('.card')], q=document.getElementById('q'), cnt=document.getElementById('count');
function filt(){{const t=q.value.trim().toLowerCase();let n=0;cards.forEach(c=>{{const ok=!t||c.dataset.s.includes(t);c.hidden=!ok;if(ok)n++}});document.querySelectorAll('h2.year').forEach(h=>{{let e=h.nextElementSibling,any=false;while(e&&e.classList.contains('card')){{if(!e.hidden)any=true;e=e.nextElementSibling}}h.hidden=!any}});cnt.textContent=n+(n===1?' article':' articles');document.getElementById('none').hidden=n>0}}
q.addEventListener('input',filt);filt();
let fs=+st.get('fs')||20;const sf=v=>{{fs=Math.max(15,Math.min(30,v));document.documentElement.style.setProperty('--fs',fs+'px');st.set('fs',fs)}};
document.getElementById('fp').onclick=()=>sf(fs+2);document.getElementById('fm').onclick=()=>sf(fs-2);sf(fs);
let d=st.get('dark')==='1';const sd=()=>{{document.documentElement.dataset.theme=d?'dark':'light';document.getElementById('dk').textContent=d?'Light':'Dark';st.set('dark',d?'1':'0')}};
document.getElementById('dk').onclick=()=>{{d=!d;sd()}};sd();
}})();
</script>
</body>
</html>
'''
(root / 'index.html').write_text(page, encoding='utf-8')
print('index.html written with', len(arts), 'article(s)')
