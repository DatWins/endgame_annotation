const { chromium } = require('playwright');
(async () => {
  const b = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium-1194/chrome-linux/chrome' }).catch(async () => chromium.launch());
  const p = await b.newPage({ viewport: { width: 1500, height: 950 } });
  const errs = []; p.on('pageerror', e => errs.push(e.message)); p.on('console', m => { if (m.type() === 'error') errs.push(m.text()); });
  const files = process.argv.slice(2);
  for (const f of files) {
    await p.goto('file://' + require('path').resolve(f)); await p.waitForTimeout(400);
    const base = require('path').basename(f, '.html');
    await p.screenshot({ path: `look/${base}.png` });
    const n = await p.$$eval('main a.mv', a => a.length);
    console.log(base, 'links', n, 'errors', errs.length ? errs.join(' | ') : 0); errs.length = 0;
  }
  await b.close();
})();
