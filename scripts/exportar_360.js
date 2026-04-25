const { chromium } = require('/opt/node22/lib/node_modules/playwright');
const fs = require('fs');
const path = require('path');

(async () => {
  const DOWNLOAD_DIR = path.resolve('/home/user/portal-do-gestor/data');
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({
    acceptDownloads: true,
    ignoreHTTPSErrors: true,
  });
  const page = await context.newPage();

  console.log('Acessando https://360.idata.com.br/plan/#/ ...');
  await page.goto('https://360.idata.com.br/plan/#/', { waitUntil: 'networkidle', timeout: 60000 });

  // Login
  console.log('Realizando login...');
  await page.fill('input[type="email"], input[name="email"], input[placeholder*="email" i], input[placeholder*="usuário" i], input[placeholder*="usuario" i]', 'bruno.picinini@3scorporate.com');
  await page.fill('input[type="password"]', '3035');
  await page.click('button[type="submit"], button:has-text("Entrar"), button:has-text("Login")');
  await page.waitForNavigation({ waitUntil: 'networkidle', timeout: 30000 }).catch(() => {});
  await page.waitForTimeout(3000);

  console.log('URL após login:', page.url());
  await page.screenshot({ path: '/tmp/after_login.png' });

  // Navegar para Fluxo de Importação > Itens
  console.log('Navegando para Fluxo de Importação > Itens...');

  // Tentar encontrar o menu lateral
  const menuItems = await page.$$eval('a, li, [role="menuitem"]', els => els.map(el => el.textContent?.trim()).filter(Boolean));
  console.log('Itens de menu encontrados:', menuItems.slice(0, 30));

  // Tentar clicar em "Fluxo de Importação" ou "Importação"
  const importacaoLink = page.locator('text=/fluxo de importa/i, text=/importa/i').first();
  if (await importacaoLink.isVisible().catch(() => false)) {
    await importacaoLink.click();
    await page.waitForTimeout(2000);
  }

  await page.screenshot({ path: '/tmp/after_menu.png' });

  // Clicar em "Itens"
  const itensLink = page.locator('text=/itens/i').first();
  if (await itensLink.isVisible().catch(() => false)) {
    await itensLink.click();
    await page.waitForTimeout(2000);
  }

  await page.screenshot({ path: '/tmp/after_itens.png' });
  console.log('URL atual:', page.url());

  // Clicar no botão exportar
  console.log('Procurando botão de exportar...');
  await page.screenshot({ path: '/tmp/before_export.png' });

  // Aguardar e clicar no botão exportar
  const exportBtn = page.locator('button:has-text("Exportar"), button[title*="xport" i], [data-action*="export" i]').first();
  await exportBtn.waitFor({ timeout: 15000 }).catch(async () => {
    console.log('Botão exportar não encontrado via texto, tentando outros seletores...');
    const allButtons = await page.$$eval('button', els => els.map(el => el.textContent?.trim()));
    console.log('Botões disponíveis:', allButtons);
  });

  const downloadPromise = page.waitForEvent('download', { timeout: 60000 });

  if (await exportBtn.isVisible().catch(() => false)) {
    await exportBtn.click();
  } else {
    // Tentar via ícone de download
    await page.click('[class*="export" i], [class*="download" i], button[aria-label*="xport" i]').catch(() => {});
  }

  await page.waitForTimeout(2000);
  await page.screenshot({ path: '/tmp/after_export_click.png' });

  // Selecionar CSV se aparecer modal
  const csvOption = page.locator('text=/csv/i').first();
  if (await csvOption.isVisible({ timeout: 5000 }).catch(() => false)) {
    await csvOption.click();
    await page.waitForTimeout(1000);
  }

  // Exportar com filtro salvo
  const filtroSalvoOption = page.locator('text=/filtro salvo/i, text=/saved filter/i').first();
  if (await filtroSalvoOption.isVisible({ timeout: 5000 }).catch(() => false)) {
    await filtroSalvoOption.click();
    await page.waitForTimeout(1000);
  }

  await page.screenshot({ path: '/tmp/after_filter_option.png' });

  // Selecionar filtro "desembaraço"
  const desembaracoOption = page.locator('text=/desembaraço/i, text=/desembaraco/i').first();
  if (await desembaracoOption.isVisible({ timeout: 5000 }).catch(() => false)) {
    await desembaracoOption.click();
    await page.waitForTimeout(1000);
  }

  await page.screenshot({ path: '/tmp/after_desembaraco.png' });

  // Clicar OK
  const okBtn = page.locator('button:has-text("OK"), button:has-text("Ok"), button:has-text("Confirmar")').first();
  if (await okBtn.isVisible({ timeout: 5000 }).catch(() => false)) {
    const dl = await Promise.race([
      page.waitForEvent('download', { timeout: 30000 }),
      okBtn.click().then(() => null),
    ]).catch(() => null);

    if (!dl) {
      await okBtn.click().catch(() => {});
    }
  }

  // Aguardar download
  let download;
  try {
    download = await downloadPromise;
  } catch (e) {
    console.log('Erro aguardando download:', e.message);
    await page.screenshot({ path: '/tmp/error_state.png' });
    await browser.close();
    process.exit(1);
  }

  const fileName = download.suggestedFilename();
  const destPath = path.join(DOWNLOAD_DIR, fileName);
  await download.saveAs(destPath);
  console.log('Arquivo baixado:', destPath);
  console.log('DOWNLOAD_OK:' + destPath);

  await browser.close();
})();
