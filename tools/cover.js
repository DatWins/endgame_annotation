const { chromium } = require('playwright');
(async()=>{const b=await chromium.launch({executablePath:'/opt/pw-browsers/chromium'});
const p=await b.newPage({viewport:{width:800,height:1200}});
const img='data:image/png;base64,'+require('fs').readFileSync('epub/OEBPS/images/root.png').toString('base64');
await p.setContent(`<body style="margin:0;width:800px;height:1200px;background:#1f3550;color:#fff;font-family:Georgia,serif;display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center">
<div style="font-family:Arial;letter-spacing:4px;font-size:22px;color:#b8cbe0">THE PRACTICAL ENDGAME</div>
<div style="font-family:Arial;font-weight:800;font-size:76px;line-height:1.05;margin:24px 40px 10px">Logical<br>Illogicality</div>
<div style="font-size:28px;color:#cfe0f5;margin-bottom:36px">GM Daniel Naroditsky</div>
<img src="${img}" style="width:480px;border-radius:6px">
<div style="font-family:Arial;font-size:22px;color:#b8cbe0;margin-top:34px">Chess Life · June 2017</div></body>`);
await p.screenshot({path:'epub/OEBPS/images/cover.png'});await b.close();})();
