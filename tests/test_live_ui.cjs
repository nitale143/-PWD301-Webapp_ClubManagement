// Start tests/ui_fixture_server.py first; never point this at the club database.
const assert = require('node:assert/strict');
const { chromium } = require('playwright');
const base = process.env.FIA_TEST_URL || 'http://127.0.0.1:5090';

(async () => {
  const browser = await chromium.launch({ channel: 'msedge', headless: true });
  const errors = [];
  try {
    const page = await browser.newPage({ viewport: { width: 1440, height: 1050 } });
    page.on('pageerror', error => errors.push(error.message));
    await page.goto(base + '/');
    assert.equal(await page.locator('.fia-landing').count(), 1);
    await page.goto(base + '/ai');
    assert.match(page.url(), /\/login/);
    await page.locator('[name=mssv]').fill('QA002');
    await page.locator('[name=password]').fill('ui-test-password');
    await Promise.all([page.waitForURL('**/home'), page.locator('button[type=submit]').click()]);
    assert.equal(await page.locator('.fia-admin-nav').count(), 0);
    await page.goto(base + '/ai');
    assert.equal(await page.locator('#ai-chat-form').count(), 1);
    assert.equal(await page.locator('script[src*="services.js"]').count(), 0);
    const stream = page.waitForResponse(response => response.url().endsWith('/ai/stream'));
    await page.locator('#chat-message').fill('hello');
    await page.locator('#ai-chat-form button[type=submit]').click();
    assert.equal((await stream).status(), 200);
    await page.waitForFunction(() => document.querySelector('#chat-stream-status')?.getAttribute('aria-busy') === 'false' && document.querySelectorAll('.chat-ai').length > 0);
    assert.match(await page.locator('#chat-history').innerText(), /hello/);
    assert.doesNotMatch(await page.locator('#chat-history').innerText(), /Đây là phản hồi mô phỏng/);
    assert.match(page.url(), /chat=\d+/);
    await page.reload();
    assert.match(await page.locator('#chat-history').innerText(), /hello/);
    for (const route of ['/home', '/event', '/funds', '/profile', '/ai']) {
      await page.goto(base + route);
      assert.ok(!await page.locator('body').innerText().then(text => /Internal Server Error/.test(text)), route);
    }
    await page.goto(base + '/logout');
    await page.goto(base + '/login');
    await page.locator('[name=mssv]').fill('QA001');
    await page.locator('[name=password]').fill('ui-test-password');
    await Promise.all([page.waitForURL('**/home'), page.locator('button[type=submit]').click()]);
    assert.equal(await page.locator('.fia-admin-nav').count(), 1);
    await page.goto(base + '/ai');
    await page.screenshot({ path: 'D:/PWD301/real-ui-ai-desktop.png', fullPage: true });
    await page.setViewportSize({ width: 390, height: 844 });
    await page.reload();
    assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1));
    await page.locator('#menu-toggle').click();
    assert.equal(await page.locator('#menu-toggle').getAttribute('aria-expanded'), 'true');
    await page.waitForFunction(() => getComputedStyle(document.querySelector('#sidebar')).transform === 'matrix(1, 0, 0, 1, 0, 0)');
    await page.screenshot({ path: 'D:/PWD301/real-ui-ai-mobile.png', fullPage: true });
    assert.deepEqual(errors, []);
    console.log('PASS: real login, role navigation, AI SSE, persisted history, routes, mobile layout');
  } finally {
    await browser.close();
  }
})().catch(error => { console.error(error); process.exitCode = 1; });
