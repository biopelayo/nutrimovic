import { chromium } from 'playwright';
const OUT = 'C:/Users/geope/AppData/Local/Temp/claude/D--Antigravity/0ec5481f-6987-4101-8fef-0f1b3220bd15/scratchpad';
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const b = await chromium.launch();
try {
  const ctx = await b.newContext({ viewport: { width: 1500, height: 780 }, deviceScaleFactor: 2 });
  const p = await ctx.newPage();
  await p.goto('http://localhost:5176/', { waitUntil: 'networkidle' });
  await sleep(2500);
  await p.getByRole('button', { name: 'Hoja de dieta' }).click();
  await sleep(2500);
  await p.getByPlaceholder('Filtrar alimento…').fill('aceite de oliva');
  await sleep(1500);
  // Escribir 1 intercambio de grasa en la primera fila (aceite)
  const gInput = p.locator('input[aria-label^="Intercambios de grasa"]').first();
  await gInput.fill('1');
  await gInput.press('Tab');
  await sleep(600);
  await p.screenshot({ path: OUT + '/j1_ex_editable.png' });
  console.log('j1 ok');
} catch (e) {
  console.error('ERR', e.message);
} finally {
  await b.close();
}
