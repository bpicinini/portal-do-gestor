const { chromium } = require('/opt/node22/lib/node_modules/playwright');
const fs = require('fs');

(async () => {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({ ignoreHTTPSErrors: true });
  const page = await context.newPage();

  console.log('Acessando página...');
  await page.goto('https://360.idata.com.br/plan/#/', { waitUntil: 'load', timeout: 60000 });
  await page.waitForTimeout(5000);

  console.log('URL:', page.url());
  console.log('Title:', await page.title());

  // Get all inputs
  const inputs = await page.$$eval('input', els => els.map(el => ({
    type: el.type,
    name: el.name,
    id: el.id,
    placeholder: el.placeholder,
    class: el.className
  })));
  console.log('Inputs:', JSON.stringify(inputs, null, 2));

  // Get all buttons
  const buttons = await page.$$eval('button', els => els.map(el => ({
    text: el.textContent?.trim(),
    type: el.type,
    class: el.className
  })));
  console.log('Buttons:', JSON.stringify(buttons, null, 2));

  await page.screenshot({ path: '/tmp/debug_page.png' });
  console.log('Screenshot salvo em /tmp/debug_page.png');

  const html = await page.content();
  fs.writeFileSync('/tmp/page_html.txt', html.substring(0, 10000));
  console.log('HTML (primeiros 10000 chars) salvo em /tmp/page_html.txt');

  await browser.close();
})();
