// side-by-side: original crop | board drawn from the reading, for visual checking
const fs=require('fs');const {chromium}=require('playwright');
const pc=fs.readFileSync('lib/pieces.css','utf8');const F=JSON.parse(fs.readFileSync('imgfens.json','utf8'));
const names=Object.keys(F).sort();
function board(fen){const g=[];fen.split('/').forEach((r,ri)=>{let c=0;for(const ch of r){if(/\d/.test(ch))c+=+ch;else g[ri*8+c++]=ch}});
 let s='';for(let i=0;i<64;i++){const r=i>>3,c=i&7,p=g[i];s+=`<div class="sq ${(r+c)%2?'d':'l'}">${p?`<div class="pc ${p===p.toUpperCase()?'w':'b'}${p.toUpperCase()}"></div>`:''}</div>`}return `<div class="bd">${s}</div>`}
(async()=>{const b=await chromium.launch();const p=await b.newPage({viewport:{width:1400,height:900}});
 for(let s=0;s<names.length;s+=24){const part=names.slice(s,s+24);
  const html=part.map(n=>`<div class="pair"><img src="data:image/png;base64,${fs.readFileSync('dia/'+n+'.png').toString('base64')}">${board(F[n])}<span>${n.slice(0,2)}${n.slice(-5)}</span></div>`).join('');
  await p.setContent(`<style>${pc} body{margin:0;display:flex;flex-wrap:wrap;font:10px sans-serif}.pair{display:flex;gap:2px;margin:3px;align-items:flex-start;position:relative}img{width:110px;height:110px}.bd{width:110px;height:110px;display:grid;grid-template-columns:repeat(8,1fr)}.sq{position:relative}.l{background:#fff}.d{background:#bbb}.pc{position:absolute;inset:0;background-size:100% 100%}span{position:absolute;top:-1px;left:0;background:#ff0}</style>${html}`);
  await p.screenshot({path:`look/verify_${s/24}.png`,fullPage:true});}
 await b.close();console.log('sheets',Math.ceil(names.length/24))})();
