const { chromium } = require('playwright');
const assert = require('node:assert/strict');

const base = 'http://127.0.0.1:5080';
const origin = new URL(base).origin;

(async () => {
  const browser = await chromium.launch({ channel: 'msedge', headless: true });
  const page = await browser.newPage({ viewport: { width: 1440, height: 1050 } });
  page.setDefaultTimeout(4000);
  const results = [];
  const pageErrors = [];
  const externalRequests = [];
  let resetCounter = 0;

  page.on('pageerror', (error) => pageErrors.push(error.message));
  page.on('request', (request) => {
    if (new URL(request.url()).origin !== origin) externalRequests.push(request.url());
  });
  await page.route('**/*', (route) => {
    if (new URL(route.request().url()).origin === origin) return route.continue();
    externalRequests.push(route.request().url());
    return route.abort();
  });

  const fresh = async (screen) => {
    await page.goto(`${base}/?interaction=${++resetCounter}#${screen}`);
    await page.waitForFunction((key) => location.hash === `#${key}` && document.querySelector('#view')?.textContent.trim().length > 30, screen);
  };
  const check = async (name, run) => {
    try {
      await run();
      results.push({ name, status: 'PASS' });
    } catch (error) {
      results.push({ name, status: 'FAIL', error: String(error.stack || error) });
    }
  };

  try {
    await check('member search and validated add modal', async () => {
      await fresh('members');
      await page.locator('[data-member-search]').fill('23124025');
      assert.equal(await page.locator('[data-member-rows] tr').count(), 1);
      assert.match(await page.locator('[data-member-rows]').innerText(), /Phạm Đức Long/);
      await page.locator('[data-member-search]').fill('');
      await page.locator('[data-member-add]').click();
      const dialog = page.locator('#preview-dialog');
      await page.locator('button[form="preview-member-form"]').click();
      assert.equal(await dialog.getAttribute('open'), '');
      assert.equal(await page.locator('#preview-member-form').evaluate((form) => form.checkValidity()), false);
      await page.locator('#preview-member-form [name="name"]').fill('QA Member Preview');
      await page.locator('#preview-member-form [name="studentId"]').fill('99900001');
      await page.locator('#preview-member-form [name="team"]').selectOption({ label: 'Ban Nội dung' });
      await page.locator('#preview-member-form [name="email"]').fill('not-an-email');
      await page.locator('button[form="preview-member-form"]').click();
      assert.equal(await dialog.getAttribute('open'), '');
      await page.locator('#preview-member-form [name="email"]').fill('qa.member.preview@example.test');
      await page.locator('button[form="preview-member-form"]').click();
      await page.waitForFunction(() => !document.querySelector('#preview-dialog').open);
      assert.match(await page.locator('[data-member-rows]').innerText(), /QA Member Preview/);
      assert.match(await page.locator('[data-member-rows]').innerText(), /Chờ duyệt/);
    });

    await check('event filters, detail tabs, and event creation validation', async () => {
      await fresh('events');
      await page.locator('[data-event-status]').selectOption('live');
      assert.equal(await page.locator('[data-event-open]').count(), 1);
      assert.match(await page.locator('[data-event-results]').innerText(), /CTF FIA Welcome 2026/);
      await page.locator('[data-event-status]').selectOption('ended');
      assert.equal(await page.locator('[data-event-open]').count(), 1);
      assert.match(await page.locator('[data-event-results]').innerText(), /Sinh hoạt chuyên môn tháng 9/);
      await page.locator('[data-event-status]').selectOption('all');
      await page.locator('[data-event-view="list"]').click();
      await page.locator('[data-event-open="ev01"]').click();
      await page.waitForFunction(() => location.hash === '#event-detail');
      assert.equal(await page.locator('[data-detail-tab="attendance"]').getAttribute('aria-selected'), 'true');
      await page.locator('[data-detail-tab="tasks"]').click();
      assert.equal(await page.locator('[data-detail-tab="tasks"]').getAttribute('aria-selected'), 'true');
      assert.match(await page.locator('[data-detail-panel]').innerText(), /Đầu việc sự kiện/);
      await page.locator('[data-detail-tab="attendance"]').click();
      assert.match(await page.locator('[data-detail-panel]').innerText(), /Danh sách đăng ký/);
      await page.locator('[data-detail-back]').click();
      await page.locator('[data-event-add]').click();
      const dialog = page.locator('#preview-dialog');
      await page.locator('button[form="preview-event-form"]').click();
      assert.equal(await dialog.getAttribute('open'), '');
      assert.equal(await page.locator('#preview-event-form').evaluate((form) => form.checkValidity()), false);
      await page.locator('#preview-event-form [name="name"]').fill('QA Event Preview');
      await page.locator('#preview-event-form [name="category"]').selectOption({ label: 'Workshop' });
      await page.locator('#preview-event-form [name="capacity"]').fill('45');
      await page.locator('#preview-event-form [name="start"]').fill('2026-11-10T18:00');
      await page.locator('#preview-event-form [name="end"]').fill('2026-11-10T17:00');
      await page.locator('#preview-event-form [name="location"]').fill('QA Demo Room');
      await page.locator('button[form="preview-event-form"]').click();
      assert.equal(await dialog.getAttribute('open'), '');
      assert.match(await page.locator('#toast-region').innerText(), /kết thúc cần sau thời gian bắt đầu/i);
      await page.locator('#preview-event-form [name="end"]').fill('2026-11-10T19:00');
      await page.locator('button[form="preview-event-form"]').click();
      await page.waitForFunction(() => !document.querySelector('#preview-dialog').open);
      assert.match(await page.locator('[data-event-results]').innerText(), /QA Event Preview/);
    });

    await check('task status filters and validated task modal', async () => {
      await fresh('tasks');
      await page.locator('[data-task-filter="cho_duyet"]').click();
      assert.equal(await page.locator('[data-task-next]').count(), 2);
      await page.locator('[data-task-view="list"]').click();
      assert.equal(await page.locator('[data-task-next]').count(), 2);
      await page.locator('[data-task-filter="dang_lam"]').click();
      assert.equal(await page.locator('[data-task-next]').count(), 2);
      await page.locator('[data-task-add]').click();
      const dialog = page.locator('#preview-dialog');
      await page.locator('button[form="preview-task-form"]').click();
      assert.equal(await dialog.getAttribute('open'), '');
      assert.equal(await page.locator('#preview-task-form').evaluate((form) => form.checkValidity()), false);
      await page.locator('#preview-task-form [name="title"]').fill('QA Task Preview');
      await page.locator('#preview-task-form [name="deadline"]').fill('2026-11-12T18:00');
      await page.locator('#preview-task-form [name="team"]').selectOption({ label: 'Ban Nội dung' });
      await page.locator('#preview-task-form [name="assignee"]').selectOption({ label: 'Nguyễn Minh Anh' });
      await page.locator('button[form="preview-task-form"]').click();
      await page.waitForFunction(() => !document.querySelector('#preview-dialog').open);
      await page.locator('[data-task-filter="all"]').click();
      assert.match(await page.locator('[data-task-content]').innerText(), /QA Task Preview/);
    });

    await check('fund tabs remain clickable when switching between panels', async () => {
      await fresh('funds');
      await page.locator('[data-fund-tab="transactions"]').click();
      assert.equal(await page.locator('[data-fund-panel="transactions"]').isVisible(), true);
      assert.equal(await page.locator('[data-fund-panel="collections"]').isVisible(), false);
      await page.locator('[data-fund-tab="payments"]').click();
      assert.equal(await page.locator('[data-fund-panel="payments"]').isVisible(), true);
      await page.locator('[data-fund-tab="collections"]').click();
      assert.equal(await page.locator('[data-fund-panel="collections"]').isVisible(), true);
    });

    await check('fund collection creation validation', async () => {
      await fresh('funds');
      await page.locator('[data-open-collection]').click();
      const dialog = page.locator('#preview-dialog');
      await page.locator('button[form="preview-collection-form"]').click();
      assert.equal(await dialog.getAttribute('open'), '');
      assert.equal(await page.locator('#preview-collection-form').evaluate((form) => form.checkValidity()), false);
      await page.locator('#preview-collection-form [name="name"]').fill('QA Dues Preview');
      await page.locator('#preview-collection-form [name="amount"]').fill('125000');
      await page.locator('#preview-collection-form [name="start_date"]').fill('2026-10-20');
      await page.locator('#preview-collection-form [name="due_date"]').fill('2026-10-19');
      await page.locator('#preview-collection-form [name="due_date"]').evaluate((input) => {
        window.__dueDateInvalidEvents = 0;
        input.addEventListener('invalid', () => window.__dueDateInvalidEvents++, { once: true });
      });
      await page.locator('button[form="preview-collection-form"]').click();
      assert.equal(await dialog.getAttribute('open'), '');
      assert.equal(await page.evaluate(() => window.__dueDateInvalidEvents), 1);
      assert.doesNotMatch(await page.locator('[data-fund-panel="collections"]').innerText(), /QA Dues Preview/);
      await page.locator('#preview-collection-form [name="due_date"]').fill('2026-10-28');
      await page.locator('button[form="preview-collection-form"]').click();
      await page.waitForFunction(() => !document.querySelector('#preview-dialog').open);
      assert.match(await page.locator('[data-fund-panel="collections"]').innerText(), /QA Dues Preview/);
    });

    await check('AI chat creation, simulated reply, switching, and draft preview', async () => {
      await fresh('ai');
      await page.locator('#new-chat-form [name="title"]').fill('QA Chat Preview');
      await page.locator('#new-chat-form button[type="submit"]').click();
      assert.match(await page.locator('.chat-thread h2').innerText(), /QA Chat Preview/);
      await page.locator('#preview-chat-form [name="message"]').fill('Summarize demo tasks');
      await page.locator('#preview-chat-form button[type="submit"]').click();
      assert.match(await page.locator('#preview-chat-history').innerText(), /Summarize demo tasks/);
      assert.match(await page.locator('#preview-chat-history').innerText(), /phản hồi mô phỏng/);
      assert.match(await page.locator('#view').innerText(), /không có backend hoặc dịch vụ mạng/);
      await page.locator('[data-chat-filter]').click();
      await page.locator('[data-chat-id="chat-3"]').click();
      assert.match(await page.locator('.chat-thread').innerText(), /Ý tưởng tuyển thành viên/);
      assert.equal(await page.locator('#preview-chat-form').count(), 0);
      await page.locator('[data-chat-filter]').click();
      await page.locator('[data-chat-id="chat-1"]').click();
      assert.match(await page.locator('.chat-thread h2').innerText(), /Kế hoạch Workshop An toàn thông tin/);
      await page.locator('[data-ai-preview="email"]').click();
      assert.match(await page.locator('#preview-dialog').innerText(), /Không gửi email/);
      await page.locator('[data-modal-preview-ok]').click();
      await page.waitForFunction(() => !document.querySelector('#preview-dialog').open);
    });

    await check('approval and rejection require explicit demo confirmation', async () => {
      await fresh('approvals');
      assert.equal(await page.locator('.member-review-card').count(), 3);
      let card = page.locator('.member-review-card').filter({ hasText: 'Đỗ Ngọc Mai' });
      await card.locator('[data-member-action="approve"]').click();
      assert.match(await page.locator('#preview-dialog').innerText(), /không ghi dữ liệu thật/);
      await page.locator('#preview-dialog [data-modal-close]').click();
      assert.equal(await page.locator('.member-review-card').count(), 3);
      card = page.locator('.member-review-card').filter({ hasText: 'Đỗ Ngọc Mai' });
      await card.locator('[data-member-action="approve"]').click();
      await page.locator('#preview-dialog [data-modal-confirm]').click();
      assert.equal(await page.locator('.member-review-card').count(), 2);
      assert.doesNotMatch(await page.locator('#view').innerText(), /Đỗ Ngọc Mai/);
      card = page.locator('.member-review-card').filter({ hasText: 'Phạm Quốc Bảo' });
      await card.locator('[data-member-action="reject"]').click();
      assert.match(await page.locator('#preview-dialog').innerText(), /không ghi dữ liệu thật/);
      await page.locator('#preview-dialog [data-modal-confirm]').click();
      assert.equal(await page.locator('.member-review-card').count(), 1);
      assert.doesNotMatch(await page.locator('#view').innerText(), /Phạm Quốc Bảo/);
    });

    await check('role search, current-role preselection, and eligible one-time transfer', async () => {
      await fresh('roles');
      await page.locator('#role-search').fill('22110037');
      assert.equal(await page.locator('[data-role-row]:visible').count(), 1);
      await page.locator('#role-search').fill('');
      await page.locator('[data-assign-role="r-4"]').click();
      assert.equal(await page.locator('#preview-dialog [name="role"]').inputValue(), 'Thành viên');
      assert.equal(await page.locator('#preview-dialog [name="team"]').inputValue(), 'Truyền thông');
      await page.locator('#preview-dialog [data-modal-close]').click();
      await page.locator('[data-assign-role="r-1"]').click();
      assert.equal(await page.locator('#preview-dialog [name="role"]').inputValue(), 'Chủ nhiệm');
      assert.equal(await page.locator('#preview-dialog [name="team"]').inputValue(), 'Ban Chủ nhiệm');
      await page.locator('#preview-dialog [data-modal-close]').click();

      await page.locator('[data-transfer-role]').click();
      assert.match(await page.locator('#dialog-title').innerText(), /Nhượng chức vụ Chủ nhiệm/);
      const eligible = await page.locator('#transfer-form [name="memberId"] option').evaluateAll((options) => options.map((option) => option.value));
      assert.deepEqual(eligible, ['r-2', 'r-3', 'r-4', 'r-5', 'r-6']);
      await page.locator('#transfer-form [name="memberId"]').selectOption('r-2');
      await page.locator('button[form="transfer-form"]').click();
      await page.waitForFunction(() => !document.querySelector('#preview-dialog').open);
      assert.match(await page.locator('[data-role-row]').filter({ hasText: 'Nguyễn Minh An' }).innerText(), /Thành viên/);
      assert.match(await page.locator('[data-role-row]').filter({ hasText: 'Trần Gia Huy' }).innerText(), /Chủ nhiệm/);
      assert.equal(await page.locator('[data-transfer-role]').isDisabled(), true);
      await page.evaluate(() => { location.hash = 'profile'; });
      await page.waitForFunction(() => location.hash === '#profile');
      assert.match(await page.locator('.profile-cover').innerText(), /Thành viên/);
    });

    await check('profile form validation', async () => {
      await fresh('profile');
      await page.locator('#profile-form [name="email"]').fill('invalid-email');
      await page.locator('#profile-form button[type="submit"]').click();
      assert.equal(await page.locator('#profile-form').evaluate((form) => form.checkValidity()), false);
      assert.match(await page.locator('#view h1').first().innerText(), /Nguyễn Minh An/);
      await page.locator('#profile-form [name="email"]').fill('minhanh@example.test');
      await page.locator('#profile-form [name="name"]').fill('   ');
      await page.locator('#profile-form button[type="submit"]').click();
      assert.equal(await page.locator('#profile-form [name="name"]').evaluate((input) => input.validity.customError), true);
      assert.match(await page.locator('.profile-cover h1').innerText(), /Nguyễn Minh An/);
      await page.locator('#profile-form [name="name"]').fill('QA Profile Preview');
      await page.locator('#profile-form [name="phone"]').fill('0900000000');
      await page.locator('#profile-form [name="email"]').fill('qa.profile@example.test');
      await page.locator('#profile-form [name="facebook"]').fill('https://example.test/qa-profile');
      await page.locator('#profile-form button[type="submit"]').click();
      assert.match(await page.locator('.profile-cover h1').innerText(), /QA Profile Preview/);
      await page.locator('#preferences-form [name="skills"]').fill('QA, kiểm thử');
      await page.locator('#preferences-form [name="maxTasks"]').fill('11');
      await page.locator('#preferences-form button[type="submit"]').click();
      assert.equal(await page.locator('#preferences-form').evaluate((form) => form.checkValidity()), false);
      await page.locator('#preferences-form [name="maxTasks"]').fill('4');
      await page.locator('#preferences-form [name="unavailableUntil"]').fill('2026-11-01');
      await page.locator('#preferences-form button[type="submit"]').click();
      assert.equal(await page.locator('#preferences-form [name="maxTasks"]').inputValue(), '4');
    });

    await check('login and registration invalid and valid demo flows', async () => {
      await fresh('login');
      await page.locator('#login-form button[type="submit"]').click();
      assert.equal(await page.locator('#login-form').evaluate((form) => form.checkValidity()), false);
      assert.equal(new URL(page.url()).hash, '#login');
      await page.locator('#login-form [name="studentId"]').fill('99900002');
      await page.locator('#login-form [name="password"]').fill('demo-pass-123');
      await page.locator('#login-form button[type="submit"]').click();
      await page.waitForFunction(() => location.hash === '#funds');

      await fresh('register');
      await page.locator('#register-form button[type="submit"]').click();
      assert.equal(await page.locator('#register-form').evaluate((form) => form.checkValidity()), false);
      assert.equal(new URL(page.url()).hash, '#register');
      await page.locator('#register-form [name="name"]').fill('QA Registration Preview');
      await page.locator('#register-form [name="studentId"]').fill('99900003');
      await page.locator('#register-form [name="birthDate"]').fill('2004-01-01');
      await page.locator('#register-form [name="phone"]').fill('0900000001');
      await page.locator('#register-form [name="email"]').fill('qa.registration@example.test');
      await page.locator('#register-form [name="facebook"]').fill('https://example.test/qa-registration');
      await page.locator('#register-form [name="teams"]').selectOption(['media', 'content']);
      await page.locator('#register-form [name="password"]').fill('preview-pass-123');
      await page.locator('#register-form [name="terms"]').check();
      await page.locator('#register-form button[type="submit"]').click();
      await page.waitForFunction(() => location.hash === '#pending');
      assert.match(await page.locator('#view').innerText(), /Tài khoản đang chờ xét duyệt/);
      assert.match(await page.locator('#view').innerText(), /không có hồ sơ được tạo/i);
    });

    await check('all interactions remain local and produce no browser exceptions', async () => {
      assert.deepEqual(externalRequests, []);
      assert.deepEqual(pageErrors, []);
    });
  } finally {
    await browser.close();
  }

  console.log(JSON.stringify({ results, pageErrors, externalRequests }, null, 2));
  if (results.some((result) => result.status === 'FAIL')) process.exitCode = 1;
})().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
