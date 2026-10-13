const { chromium } = require('playwright');
const assert = require('node:assert/strict');

const base = 'http://127.0.0.1:5082';
const origin = new URL(base).origin;
const sessionKey = 'fia-preview-session-v1';

(async () => {
  const browser = await chromium.launch({ channel: 'msedge', headless: true });
  const results = [];
  const pageErrors = [];
  const consoleErrors = [];
  const externalRequests = [];
  const nonStaticRequests = [];
  let pageNumber = 0;

  const newPage = async (viewport = { width: 1440, height: 1000 }) => {
    const context = await browser.newContext({ viewport });
    const page = await context.newPage();
    page.setDefaultTimeout(5000);
    page.on('pageerror', (error) => pageErrors.push(error.message));
    page.on('console', (message) => {
      if (message.type() === 'error') consoleErrors.push(message.text());
    });
    page.on('request', (request) => {
      const url = new URL(request.url());
      if (url.origin !== origin) externalRequests.push(request.url());
      if (request.method() !== 'GET' || /\/api(?:\/|$)/i.test(url.pathname)) {
        nonStaticRequests.push({ method: request.method(), url: request.url() });
      }
    });
    await page.route('**/*', (route) => {
      if (new URL(route.request().url()).origin === origin) return route.continue();
      externalRequests.push(route.request().url());
      return route.abort();
    });
    return { context, page };
  };

  const visit = async (page, hash) => {
    const caseId = ++pageNumber;
    await page.goto(`${base}/?auth-case=${caseId}#${hash}`);
    await page.waitForFunction(() => document.querySelector('#view')?.textContent.trim().length > 20);
  };

  const goHash = async (page, hash) => {
    await page.evaluate((value) => { location.hash = value; }, hash);
    await page.waitForFunction((value) => location.hash === `#${value}`, hash);
    await page.waitForFunction(() => document.querySelector('#view')?.textContent.trim().length > 20);
  };

  const check = async (name, run) => {
    let resources;
    try {
      resources = await newPage();
      await run(resources.page);
      results.push({ name, status: 'PASS' });
    } catch (error) {
      results.push({ name, status: 'FAIL', error: String(error.stack || error) });
    } finally {
      await resources?.context.close();
    }
  };

  const login = async (page, { code = 'QA-24124012', password = 'demo-pass-123', role = 'member' } = {}) => {
    await page.locator('#login-form [name="studentId"]').fill(code);
    await page.locator('#login-form [name="password"]').fill(password);
    await page.locator('#login-form [name="demoRole"]').selectOption(role);
    await page.locator('#login-form button[type="submit"]').click();
    await page.waitForFunction(() => document.querySelector('body')?.dataset.previewRole !== 'guest' && document.querySelector('#view')?.dataset.screen !== 'login');
  };

  try {
    await check('guest landing workspace CTA redirects to demo login', async (page) => {
      await visit(page, 'landing');
      await page.locator('.rl-header-actions [data-route="dashboard"]').click();
      await page.waitForFunction(() => location.hash === '#login');
      assert.match(await page.locator('#view').innerText(), /Dùng thông tin mẫu bất kỳ/);
      assert.match(await page.locator('#view').innerText(), /Demo · không có xác thực/);
      assert.equal(await page.locator('#login-form [name="demoRole"]').inputValue(), 'member');
    });

    await check('guest direct dashboard, roles, and funds routes require login and resume safely', async (page) => {
      for (const [requested, expected] of [['dashboard', 'dashboard'], ['roles', 'dashboard'], ['funds', 'funds']]) {
        await visit(page, requested);
        await page.waitForFunction(() => location.hash === '#login');
        assert.equal(await page.locator('#view').getAttribute('data-screen'), 'login');
        assert.doesNotMatch(await page.locator('#view').innerText(), /danh sách thành viên/);
        await login(page, { code: `QA-${requested}` });
        await page.waitForFunction((value) => location.hash === `#${value}`, expected);
        assert.equal(await page.locator('#view').getAttribute('data-screen'), expected);
        assert.equal(await page.locator('body').getAttribute('data-preview-role'), 'member');
        await page.locator('#logout-preview').click();
        await page.waitForFunction(() => location.hash === '#landing');
      }
    });

    await check('synthetic member login stores identity only and opens personal dashboard', async (page) => {
      await visit(page, 'login');
      assert.equal(await page.locator('#login-form [name="demoRole"]').inputValue(), 'member');
      assert.match(await page.locator('#view').innerText(), /Thông tin không được gửi hoặc lưu lại/);
      const invalidPassword = page.locator('#login-form [name="password"]');
      await invalidPassword.fill('12345');
      assert.equal(await page.locator('#login-form').evaluate((form) => form.checkValidity()), false);
      await login(page, { code: '99999999', password: '123456' });
      await page.waitForFunction(() => location.hash === '#dashboard');
      assert.equal(await page.locator('body').getAttribute('data-preview-role'), 'member');
      assert.match(await page.locator('#view').innerText(), /dữ liệu minh họa cho phiên xem trước/);
      const stored = await page.evaluate((key) => JSON.parse(sessionStorage.getItem(key)), sessionKey);
      assert.deepEqual(Object.keys(stored).sort(), ['code', 'name', 'role']);
      assert.equal(stored.role, 'member');
      assert.equal(stored.code, '99999999');
      assert.doesNotMatch(JSON.stringify(stored), /123456|password/i);
    });

    await check('member sees personal tasks, funds, and AI without administration controls', async (page) => {
      await visit(page, 'login');
      await login(page);
      await page.waitForFunction(() => location.hash === '#dashboard');

      await goHash(page, 'tasks');
      assert.match(await page.locator('#view').innerText(), /Nhiệm vụ cá nhân/);
      assert.match(await page.locator('#view').innerText(), /Chỉ hiển thị hai nhiệm vụ mẫu/);
      assert.ok(await page.locator('[data-submit-task]').count() > 0);
      assert.equal(await page.locator('[data-task-add], [data-task-assign], [data-member-action]').count(), 0);

      await goHash(page, 'funds');
      assert.match(await page.locator('#view').innerText(), /Khoản đóng góp của tôi/);
      assert.match(await page.locator('#view').innerText(), /không có danh sách hoặc quyền xử lý giao dịch/);
      assert.equal(await page.locator('[data-open-collection], [data-fund-tab], [data-fund-action]').count(), 0);

      await goHash(page, 'ai');
      assert.match(await page.locator('#view').innerText(), /Trợ lý của bạn/);
      assert.match(await page.locator('#view').innerText(), /Không tạo đề xuất gửi Ban Điều hành/);
      assert.equal(await page.locator('[data-ai-preview], [data-member-action], [data-approve]').count(), 0);
    });

    await check('member direct administration routes redirect to dashboard', async (page) => {
      await visit(page, 'login');
      await login(page);
      await page.waitForFunction(() => location.hash === '#dashboard');
      for (const key of ['members', 'approvals', 'roles']) {
        await page.evaluate((value) => { location.hash = value; }, key);
        await page.waitForFunction(() => location.hash === '#dashboard' && document.querySelector('#view')?.dataset.screen === 'dashboard');
        assert.equal(await page.locator('#view').getAttribute('data-screen'), 'dashboard');
      }
      for (const key of ['members', 'approvals', 'roles']) {
        assert.equal(await page.locator(`[data-nav="${key}"]`).isHidden(), true);
      }
    });

    await check('member Ctrl+K screen list excludes administration pages', async (page) => {
      await visit(page, 'login');
      await login(page);
      await page.waitForFunction(() => location.hash === '#dashboard');
      await page.keyboard.press('Control+k');
      assert.equal(await page.locator('#preview-dialog').getAttribute('open'), '');
      await page.locator('#screen-search').fill('thành viên');
      const searchKeys = await page.locator('#screen-results button').evaluateAll((buttons) => buttons.map((button) => button.dataset.screen));
      assert.ok(searchKeys.every((key) => !['members', 'approvals', 'roles'].includes(key)));
      await page.locator('#screen-search').fill('phê duyệt');
      assert.equal(await page.locator('#screen-results button[data-screen="approvals"]').count(), 0);
      assert.equal(await page.locator('#screen-results button[data-screen="roles"]').count(), 0);
      await page.keyboard.press('Escape');
      assert.equal(await page.locator('#preview-dialog').getAttribute('open'), null);
    });

    await check('member notification dialog contains only personal demo updates', async (page) => {
      await visit(page, 'login');
      await login(page);
      await page.waitForFunction(() => location.hash === '#dashboard');
      await page.locator('#notification-button').click();
      assert.equal(await page.locator('#preview-dialog').getAttribute('open'), '');
      const notice = await page.locator('#preview-dialog').innerText();
      assert.match(notice, /Thông báo cá nhân · Demo/);
      assert.match(notice, /Lịch workshop mẫu/);
      assert.doesNotMatch(notice, /hồ sơ đang chờ phê duyệt|bản nháp email|Mở trang phê duyệt/i);
      assert.equal(await page.locator('#open-approvals').count(), 0);
    });

    await check('explicit board design mode opens legacy BDH screens with preview labeling', async (page) => {
      await visit(page, 'login');
      assert.match(await page.locator('#login-form [name="demoRole"] option[value="board"]').innerText(), /BDH — chỉ xem thiết kế mẫu/);
      await login(page, { code: 'QA-BOARD-01', role: 'board' });
      await page.waitForFunction(() => location.hash === '#dashboard');
      assert.equal(await page.locator('body').getAttribute('data-preview-role'), 'board');
      assert.match(await page.locator('#toast-region').innerText(), /không phải quyền admin thật/);
      await page.locator('#notification-button').click();
      assert.match(await page.locator('#preview-dialog').innerText(), /5 hồ sơ đang chờ phê duyệt/);
      assert.equal(await page.locator('#open-approvals').count(), 1);
      await page.locator('#open-approvals').click();
      await page.waitForFunction(() => location.hash === '#approvals');
      for (const key of ['members', 'approvals', 'roles']) {
        assert.equal(await page.locator(`#primary-navigation [data-nav="${key}"]`).isHidden(), false);
        await goHash(page, key);
        assert.equal(await page.locator('#view').getAttribute('data-screen'), key);
      }
    });

    await check('board demo session signs out from pending and dashboard returns to login', async (page) => {
      await visit(page, 'login');
      await login(page, { code: 'QA-BOARD-PENDING', role: 'board' });
      await page.waitForFunction(() => location.hash === '#dashboard');
      await goHash(page, 'pending');
      assert.equal(await page.locator('body').getAttribute('data-preview-role'), 'board');
      await page.locator('#view button[data-nav="login"]').click();
      await page.waitForFunction(() => location.hash === '#login' && document.querySelector('#view')?.dataset.screen === 'login');
      assert.equal(await page.evaluate((key) => sessionStorage.getItem(key), sessionKey), null);
      assert.equal(await page.locator('body').getAttribute('data-preview-role'), 'guest');
      await page.evaluate(() => { location.hash = 'dashboard'; });
      await page.waitForFunction(() => location.hash === '#login' && document.querySelector('#view')?.dataset.screen === 'login');
      assert.equal(await page.evaluate((key) => sessionStorage.getItem(key), sessionKey), null);
    });

    await check('logout clears session and browser back cannot restore a protected screen', async (page) => {
      await visit(page, 'landing');
      await page.locator('.rl-header-actions [data-route="dashboard"]').click();
      await page.waitForFunction(() => location.hash === '#login');
      await login(page);
      await page.waitForFunction(() => location.hash === '#dashboard');
      await goHash(page, 'tasks');
      await page.locator('#logout-preview').click();
      await page.waitForFunction(() => location.hash === '#landing');
      assert.equal(await page.evaluate((key) => sessionStorage.getItem(key), sessionKey), null);
      await page.goBack();
      await page.waitForFunction(() => ['#login', '#landing'].includes(location.hash));
      assert.notEqual(await page.locator('#view').getAttribute('data-screen'), 'tasks');
      assert.notEqual(await page.locator('#view').getAttribute('data-screen'), 'dashboard');
    });

    await check('reload keeps the member tab session and never stores the password', async (page) => {
      await visit(page, 'login');
      await login(page, { code: 'QA-RELOAD-01', password: 'private-demo-123' });
      await page.waitForFunction(() => location.hash === '#dashboard');
      await goHash(page, 'tasks');
      await page.reload();
      await page.waitForFunction(() => location.hash === '#tasks' && document.querySelector('#view')?.dataset.screen === 'tasks');
      assert.equal(await page.locator('body').getAttribute('data-preview-role'), 'member');
      const stored = await page.evaluate((key) => JSON.parse(sessionStorage.getItem(key)), sessionKey);
      assert.equal(stored.code, 'QA-RELOAD-01');
      assert.equal(stored.role, 'member');
      assert.equal(Object.hasOwn(stored, 'password'), false);
      assert.doesNotMatch(JSON.stringify(stored), /private-demo-123/);
    });

    await check('390px mobile member login, navigation, and workspace avoid horizontal overflow', async () => {
      const { context, page } = await newPage({ width: 390, height: 844 });
      try {
        await visit(page, 'login');
        assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth + 1), false);
        await login(page, { code: 'QA-MOBILE-01' });
        await page.waitForFunction(() => location.hash === '#dashboard');
        assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth + 1), false);
        await page.locator('#menu-toggle').click();
        assert.equal(await page.locator('#menu-toggle').getAttribute('aria-expanded'), 'true');
        assert.equal(await page.locator('[data-nav="members"]').isHidden(), true);
        await page.locator('[data-nav="events"]').click();
        await page.waitForFunction(() => location.hash === '#events');
        assert.equal(await page.locator('#menu-toggle').getAttribute('aria-expanded'), 'false');
        assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth + 1), false);
      } finally {
        await context.close();
      }
    });

    await check('auth flow makes no external, API, or non-GET requests and raises no browser errors', async () => {
      assert.deepEqual(externalRequests, []);
      assert.deepEqual(nonStaticRequests, []);
      assert.deepEqual(pageErrors, []);
      assert.deepEqual(consoleErrors, []);
    });
  } finally {
    await browser.close();
  }

  console.log(JSON.stringify({ results, pageErrors, consoleErrors, externalRequests, nonStaticRequests }, null, 2));
  if (results.some((result) => result.status === 'FAIL')) process.exitCode = 1;
})().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
