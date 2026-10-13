const assert = require('node:assert/strict');
const { chromium } = require('playwright');

const base = 'http://127.0.0.1:5082';
const origin = new URL(base).origin;
const fixedEventStart = '2026-11-10T10:00:00Z';

function payload(events) {
  return {
    events,
    source: 'CTFtime',
    source_url: 'https://ctftime.org/calendar/',
    fetched_at: '2026-10-13T00:00:00+00:00',
    window: { start: '2026-10-13T00:00:00+00:00', finish: '2027-01-11T00:00:00+00:00' },
    cached: false,
    stale: false,
    limited: false
  };
}

const sampleEvents = [
  {
    id: 9001,
    title: '<img src=x onerror=window.__ctfXss=1> CFA "Alpha" & Beta',
    start: fixedEventStart,
    finish: '2026-11-11T10:00:00Z',
    ctftime_url: 'https://ctftime.org/event/9001/',
    url: 'https://ctftime.org/event/9001/',
    format: '<b>Jeopardy</b>',
    onsite: false,
    weight: 15.5,
    location: '<b>Online</b>'
  },
  {
    id: 9002,
    title: 'Bravo CTF',
    start: '2026-11-12T04:30:00Z',
    finish: '2026-11-12T08:00:00Z',
    ctftime_url: 'https://attacker.test/event/9002/',
    url: 'javascript:alert(1)',
    format: 'Attack & Defense',
    onsite: true,
    weight: 30,
    location: 'Hanoi'
  }
];

async function makePage(browser, role, onApi) {
  const context = await browser.newContext({ viewport: { width: 1440, height: 1050 } });
  if (role) {
    await context.addInitScript(({ actorRole }) => {
      sessionStorage.setItem('fia-preview-session-v1', JSON.stringify({
        role: actorRole, name: actorRole === 'board' ? 'Nguyễn Minh An' : 'Lê Minh Anh', code: `QA-${actorRole}`
      }));
    }, { actorRole: role });
  }
  const page = await context.newPage();
  page.setDefaultTimeout(5000);
  const state = { apiCount: 0, apiFinished: 0, apiMethods: [], externalRequests: [], pageErrors: [] };
  page.on('pageerror', error => state.pageErrors.push(error.message));
  page.on('request', request => {
    const url = new URL(request.url());
    if (url.origin !== origin) state.externalRequests.push(request.url());
  });
  await page.route('**/*', async route => {
    const request = route.request();
    const url = new URL(request.url());
    if (url.origin !== origin) {
      state.externalRequests.push(request.url());
      return route.abort();
    }
    if (url.pathname === '/api/ctftime/events') {
      state.apiCount += 1;
      state.apiMethods.push(request.method());
      try {
        await onApi(route, state.apiCount);
      } finally {
        state.apiFinished += 1;
      }
      return;
    }
    return route.continue();
  });
  await page.goto(`${base}/#landing`);
  await page.waitForFunction(actorRole => window.PreviewSession && document.title.includes('FIA UI Preview') &&
    document.querySelector('#view')?.dataset.screen === 'landing' &&
    document.body.dataset.previewRole === (actorRole || 'guest'), role);
  return { context, page, state };
}

async function go(page, key) {
  await page.evaluate(key => { location.hash = key; }, key);
  await page.waitForFunction(key => location.hash === `#${key}` &&
    document.querySelector('#view')?.dataset.screen === key &&
    document.body.dataset.previewRole === (window.PreviewSession?.current?.()?.role || 'guest'), key);
}

async function selectSource(page, source) {
  await page.locator(`[data-events-source="${source}"]`).click();
  await page.waitForFunction(source => {
    const tab = document.querySelector(`[data-events-source="${source}"]`);
    const panel = document.querySelector(`[data-events-panel="${source}"]`);
    return tab?.getAttribute('aria-selected') === 'true' && panel && !panel.hidden;
  }, source);
}

async function selectCtf(page) {
  await selectSource(page, 'ctftime');
}

async function waitForCards(page, count) {
  await page.waitForFunction(expected => document.querySelectorAll('.events-ctf-card').length === expected, count);
}

async function waitForApiCount(state, count, field = 'apiCount') {
  const deadline = Date.now() + 5000;
  while (state[field] < count && Date.now() < deadline) {
    await new Promise(resolve => setTimeout(resolve, 10));
  }
  assert.ok(state[field] >= count, `timed out waiting for ${field} >= ${count}; saw ${state[field]}`);
}

const checks = [];
async function check(name, run) {
  try {
    await run();
    checks.push({ name, status: 'PASS' });
  } catch (error) {
    checks.push({ name, status: 'FAIL', error: String(error.stack || error) });
  }
}

(async () => {
  const browser = await chromium.launch({ channel: 'msedge', headless: true });
  const contexts = [];
  const runs = [];
  const keep = async (made) => { contexts.push(made.context); runs.push(made); return made; };

  try {
    await check('board role keeps FIA filters/actions and lazily loads the CTFtime tab', async () => {
      const made = await keep(await makePage(browser, 'board', async route => route.fulfill({
        status: 200, contentType: 'application/json', body: JSON.stringify(payload(sampleEvents))
      })));
      const { page, state } = made;
      await go(page, 'events');
      assert.equal(await page.locator('[data-events-source]').count(), 2);
      assert.equal(state.apiCount, 0, 'CTFtime request ran before selecting its tab');

      await page.locator('[data-event-status]').selectOption('live');
      assert.equal(await page.locator('[data-event-open]').count(), 1);
      assert.match(await page.locator('[data-event-results]').innerText(), /CTF FIA Welcome 2026/);
      await page.locator('[data-event-add]').click();
      assert.equal(await page.locator('#preview-dialog').getAttribute('open'), '');
      assert.equal(await page.locator('#preview-event-form').count(), 1);
      await page.locator('#preview-dialog [data-close-dialog]').click();

      await selectCtf(page);
      await waitForCards(page, 2);
      assert.equal(state.apiCount, 1);
      assert.deepEqual(state.apiMethods, ['GET']);
      assert.equal(await page.locator('[data-events-source="ctftime"]').getAttribute('aria-selected'), 'true');
      await selectSource(page, 'fia');
      assert.equal(await page.locator('[data-events-panel="fia"]').isVisible(), true);
      assert.equal(await page.locator('[data-event-status]').inputValue(), 'live');
      assert.equal(await page.locator('[data-event-open]').count(), 1);
      assert.equal(await page.locator('[data-event-add]').count(), 1);

      await selectCtf(page);
      await waitForCards(page, 2);
      assert.equal(state.apiCount, 1, 'client cache did not avoid a repeated request');
      assert.deepEqual(state.externalRequests, []);
      assert.deepEqual(state.pageErrors, []);
    });

    await check('member role keeps its private FIA event action and only fetches on CTFtime selection', async () => {
      const made = await keep(await makePage(browser, 'member', async route => route.fulfill({
        status: 200, contentType: 'application/json', body: JSON.stringify(payload(sampleEvents))
      })));
      const { page, state } = made;
      await go(page, 'events');
      assert.equal(state.apiCount, 0);
      assert.equal(await page.locator('[data-event-add]').count(), 0);
      await page.locator('[data-member-event="welcome"]').click();
      await page.waitForFunction(() => location.hash === '#event-detail');
      await page.locator('[data-member-rsvp]').click();
      assert.match(await page.locator('#view').innerText(), /Bạn đã đăng ký demo/);
      await page.locator('[data-member-nav="events"]').click();
      await page.waitForFunction(() => location.hash === '#events');
      await selectCtf(page);
      await waitForCards(page, 2);
      assert.equal(state.apiCount, 1);
      await selectSource(page, 'fia');
      assert.equal(await page.locator('[data-member-event="welcome"]').count(), 1);
      assert.deepEqual(state.externalRequests, []);
      assert.deepEqual(state.pageErrors, []);
    });

    await check('events source wrapping stays one level across navigation for both roles', async () => {
      for (const role of ['board', 'member']) {
        const made = await keep(await makePage(browser, role, async route => route.fulfill({
          status: 200, contentType: 'application/json', body: JSON.stringify(payload(sampleEvents))
        })));
        const { page } = made;
        await page.evaluate(actorRole => {
          const canonical = actorRole === 'member' ? window.memberPreviewScreens.events : window.previewScreens.events;
          window.__canonicalEventScreen = canonical;
          window.__eventRenderCalls = 0;
          window.__eventBindCalls = 0;
          window.__eventWrapCalls = 0;
          const render = canonical.render;
          const bind = canonical.bind;
          canonical.render = function (...args) {
            window.__eventRenderCalls += 1;
            return render.apply(this, args);
          };
          canonical.bind = function (...args) {
            window.__eventBindCalls += 1;
            return bind.apply(this, args);
          };
          const wrap = window.EventSources.wrap;
          window.EventSources.wrap = function (screen) {
            window.__eventWrapCalls += 1;
            return wrap(screen);
          };
        }, role);

        await go(page, 'events');
        await page.waitForFunction(() => window.__eventBindCalls === 1);
        assert.equal(await page.evaluate(() => window.__eventRenderCalls), 1, `${role}: first render must call the canonical screen once`);
        assert.equal(await page.evaluate(() => window.__eventWrapCalls), 1);
        await go(page, 'dashboard');
        await go(page, 'events');
        await page.waitForFunction(() => window.__eventBindCalls === 2);
        assert.equal(await page.evaluate(() => window.__eventRenderCalls), 2, `${role}: navigation must not nest wrappers`);
        assert.equal(await page.evaluate(() => window.__eventWrapCalls), 2);
        assert.equal(await page.evaluate(actorRole => window.__canonicalEventScreen === (actorRole === 'member' ? window.memberPreviewScreens.events : window.previewScreens.events), role), true);
        assert.deepEqual(made.state.pageErrors, []);
      }
    });

    await check('CTFtime title and event metadata are escaped, searchable, and shown in Bangkok time', async () => {
      const made = await keep(await makePage(browser, 'board', async route => route.fulfill({
        status: 200, contentType: 'application/json', body: JSON.stringify(payload(sampleEvents))
      })));
      const { page, state } = made;
      await go(page, 'events');
      await selectCtf(page);
      await waitForCards(page, 2);

      const firstCard = page.locator('.events-ctf-card').filter({ hasText: 'CFA "Alpha"' });
      assert.equal(await firstCard.locator('img, b, script').count(), 0);
      assert.equal(await page.evaluate(() => window.__ctfXss), undefined);
      assert.match(await firstCard.locator('h3').innerText(), /<img src=x onerror=window\.__ctfXss=1>/);
      assert.equal(await firstCard.locator('time').getAttribute('datetime'), new Date(fixedEventStart).toISOString());
      assert.match(await firstCard.locator('time').innerText(), /17:00/);
      assert.match(await firstCard.innerText(), /Giờ Việt Nam/);
      assert.equal(await firstCard.locator('a').getAttribute('href'), 'https://ctftime.org/event/9001/');
      assert.equal(await page.locator('.events-ctf-card').nth(1).locator('a').getAttribute('href'), 'https://ctftime.org/event/9002/');

      await page.locator('[data-ctf-search]').fill('Beta');
      await waitForCards(page, 1);
      assert.match(await page.locator('.events-ctf-card').innerText(), /Beta/);
      await page.locator('[data-ctf-search]').fill('<img');
      await waitForCards(page, 1);
      assert.equal(await page.locator('.events-ctf-card h3').count(), 1);
      assert.deepEqual(state.externalRequests, []);
      assert.deepEqual(state.pageErrors, []);
    });

    await check('board import creates one escaped FIA event and members can list and view it', async () => {
      const made = await keep(await makePage(browser, 'board', async route => route.fulfill({
        status: 200, contentType: 'application/json', body: JSON.stringify(payload(sampleEvents))
      })));
      const { page, state } = made;
      const source = sampleEvents[0];
      const importedName = `FIA tham gia ${source.title}`;

      await go(page, 'events');
      await selectCtf(page);
      await waitForCards(page, 2);
      assert.deepEqual(await page.evaluate(() => window.FiaEventImports.list()), []);
      const ctfCard = page.locator('.events-ctf-card').filter({ hasText: 'CFA "Alpha"' });
      await ctfCard.locator('[data-ctf-import]').click();
      await selectSource(page, 'fia');

      const imported = await page.evaluate(() => window.FiaEventImports.list()[0]);
      assert.ok(imported, 'the bridge should list the created event');
      assert.equal(imported.name, importedName);
      assert.equal(imported.start, new Date(source.start).toISOString());
      assert.equal(imported.end, new Date(source.finish).toISOString());
      assert.equal(imported.source, 'CTFtime');
      assert.equal(imported.ctftimeId, String(source.id));
      assert.equal(imported.sourceUrl, source.ctftime_url);
      assert.equal(imported.capacity, null);
      assert.equal(await page.evaluate(id => window.FiaEventImports.has(id), source.id), true);

      const nativeCard = page.locator('[data-event-open]').filter({ hasText: importedName });
      assert.equal(await nativeCard.count(), 1);
      assert.equal(await nativeCard.locator('img, b, script').count(), 0, 'imported title text must remain escaped');
      await nativeCard.click();
      await go(page, 'event-detail');
      assert.equal(await page.locator('.event-detail-hero h2').innerText(), importedName);
      assert.equal(await page.locator('.event-source-link').getAttribute('href'), source.ctftime_url);
      const detailDates = await page.locator('.event-detail-hero .detail-meta-line').innerText();
      for (const value of [source.start, source.finish]) {
        const fullDate = new Intl.DateTimeFormat('vi-VN', {
          day: '2-digit', month: '2-digit', year: 'numeric', timeZone: 'Asia/Bangkok'
        }).format(new Date(value));
        assert.ok(detailDates.includes(fullDate), `detail should show full date ${fullDate}; got ${detailDates}`);
      }
      const boardDetail = await page.locator('#view').innerText();
      assert.doesNotMatch(boardDetail, /NaN/);
      assert.match(boardDetail, /Sức chứa chưa xác nhận/);
      assert.equal(await page.locator('#view img, #view b, #view script').count(), 0);

      await page.locator('[data-detail-back]').click();
      await go(page, 'events');
      await selectCtf(page);
      await waitForCards(page, 2);
      const duplicateButton = page.locator('[data-ctf-import="9001"]');
      assert.equal(await duplicateButton.innerText(), 'Đã tạo · Xem FIA');
      await duplicateButton.click();
      await selectSource(page, 'fia');
      assert.equal((await page.evaluate(() => window.FiaEventImports.list())).length, 1);
      assert.equal(await page.locator('[data-event-open]').filter({ hasText: importedName }).count(), 1);

      await go(page, 'dashboard');
      await page.evaluate(() => window.PreviewSession.signIn({ role: 'member', name: 'QA member', code: 'QA-CTF' }));
      await go(page, 'events');
      await page.waitForFunction(name => document.body.dataset.previewRole === 'member' &&
        document.querySelector('#view')?.textContent.includes(name), importedName);
      const memberCard = page.locator('[data-member-event="ctf-9001"]');
      const memberArticle = page.locator('article.card').filter({ hasText: importedName });
      assert.equal(await memberCard.count(), 1, `member event list should include the imported CTF; content: ${await page.locator('#view').innerText()}`);
      assert.equal(await memberArticle.count(), 1);
      assert.equal(await memberArticle.locator('img, b, script').count(), 0, 'member title text must remain escaped');
      await memberCard.click();
      await go(page, 'event-detail');
      assert.equal(await page.locator('#view h2').filter({ hasText: importedName }).count(), 1);
      const memberSourceLink = page.locator('#view a').filter({ hasText: 'Nguồn: CTFtime' });
      assert.equal(await memberSourceLink.count(), 1);
      assert.equal(await memberSourceLink.getAttribute('href'), source.ctftime_url);
      const memberDetail = await page.locator('#view').innerText();
      for (const value of [source.start, source.finish]) {
        const fullDate = new Intl.DateTimeFormat('vi-VN', {
          day: '2-digit', month: '2-digit', year: 'numeric', timeZone: 'Asia/Bangkok'
        }).format(new Date(value));
        assert.ok(memberDetail.includes(fullDate), `member detail should show full date ${fullDate}`);
      }
      assert.equal(await page.locator('#view [data-detail-export], #view [data-detail-add-task]').count(), 0);

      const rejection = await page.evaluate(sourceEvent => {
        try {
          window.FiaEventImports.create(sourceEvent);
          return '';
        } catch (error) {
          return String(error.message || error);
        }
      }, sampleEvents[1]);
      assert.match(rejection, /BDH/);
      assert.equal((await page.evaluate(() => window.FiaEventImports.list())).length, 1);
      assert.equal(await page.evaluate(id => window.FiaEventImports.has(id), sampleEvents[1].id), false);

      await page.locator('[data-member-nav="events"]').click();
      await go(page, 'events');
      await selectCtf(page);
      await waitForCards(page, 2);
      assert.equal(await page.locator('[data-ctf-import]').count(), 0, 'member CTF cards must not offer import controls');
      assert.equal(state.apiCount, 1);
      assert.deepEqual(state.externalRequests, []);
      assert.deepEqual(state.pageErrors, []);
    });

    await check('request loading state, safe failure message, and retry work', async () => {
      let releaseFailure;
      const failedResponse = new Promise(resolve => { releaseFailure = resolve; });
      const made = await keep(await makePage(browser, 'board', async (route, count) => {
        if (count === 1) {
          await failedResponse;
          return route.fulfill({
            status: 503, contentType: 'application/json', body: JSON.stringify({ error: 'Temporary calendar failure' })
          });
        }
        return route.fulfill({
          status: 200, contentType: 'application/json', body: JSON.stringify(payload(sampleEvents))
        });
      }));
      const { page, state } = made;
      await go(page, 'events');
      await selectCtf(page);
      await waitForApiCount(state, 1);
      await page.waitForFunction(() => document.querySelector('[data-ctf-results]')?.getAttribute('aria-busy') === 'true');
      assert.match(await page.locator('[data-ctf-status]').innerText(), /Đang tải lịch CTFtime/);
      releaseFailure();
      await waitForApiCount(state, 1, 'apiFinished');
      await page.waitForFunction(() => document.querySelector('[data-ctf-results]')?.getAttribute('aria-busy') === 'false' && document.querySelector('[data-ctf-retry]')?.hidden === false);
      assert.match(await page.locator('[data-ctf-status]').innerText(), /Temporary calendar failure/);
      assert.match(await page.locator('[data-ctf-results]').innerText(), /Chưa tải được lịch CTFtime/);
      assert.doesNotMatch(await page.locator('[data-ctf-status]').innerText(), /Đang hiển thị dữ liệu CTFtime đã lưu/,
        'a first-request failure without a prior successful response must not claim stale cached data');
      assert.equal(await page.locator('[data-ctf-retry]').isVisible(), true);
      assert.equal(state.apiCount, 1);

      await page.locator('[data-ctf-retry]').click();
      await waitForApiCount(state, 2);
      await waitForApiCount(state, 2, 'apiFinished');
      await waitForCards(page, 2);
      assert.equal(state.apiCount, 2);
      assert.equal(await page.locator('[data-ctf-retry]').isVisible(), false);
      assert.deepEqual(state.externalRequests, []);
      assert.deepEqual(state.pageErrors, []);
    });

    await check('empty feed renders an explicit empty state', async () => {
      const made = await keep(await makePage(browser, 'member', async route => route.fulfill({
        status: 200, contentType: 'application/json', body: JSON.stringify(payload([]))
      })));
      const { page, state } = made;
      await go(page, 'events');
      await selectCtf(page);
      await waitForApiCount(state, 1);
      await waitForApiCount(state, 1, 'apiFinished');
      await page.waitForFunction(() => document.querySelector('[data-ctf-results]')?.getAttribute('aria-busy') === 'false');
      await page.waitForFunction(() => document.querySelector('[data-ctf-results]')?.textContent.includes('Không có cuộc thi trong khoảng thời gian này'));
      assert.match(await page.locator('[data-ctf-results]').innerText(), /Không có cuộc thi trong khoảng thời gian này/);
      assert.equal(state.apiCount, 1);
      assert.deepEqual(state.pageErrors, []);
    });

    await check('onsite-only filter is hidden when the feed has no known modality', async () => {
      const unknownModality = [{
        id: 9010,
        title: 'Modality Not Listed CTF',
        start: fixedEventStart,
        finish: '2026-11-11T10:00:00Z',
        ctftime_url: 'https://ctftime.org/event/9010/',
        url: 'https://ctftime.org/event/9010/',
        onsite: null,
        location: ''
      }];
      const made = await keep(await makePage(browser, 'member', async route => route.fulfill({
        status: 200, contentType: 'application/json', body: JSON.stringify(payload(unknownModality))
      })));
      const { page, state } = made;
      await go(page, 'events');
      await selectCtf(page);
      await waitForCards(page, 1);
      const onsite = page.locator('[data-ctf-onsite]');
      assert.equal(await onsite.count(), 1);
      assert.equal(await onsite.isVisible(), false);
      assert.equal(await onsite.locator('xpath=ancestor::label').getAttribute('hidden'), '');
      assert.match(await page.locator('.events-ctf-card').innerText(), /Modality Not Listed CTF/);
      assert.equal(state.apiCount, 1);
      assert.deepEqual(state.pageErrors, []);
    });

    await check('late response after switching FIA or navigating away is ignored by the detached CTFtime pane', async () => {
      let releaseResponse;
      const responseReady = new Promise(resolve => { releaseResponse = resolve; });
      const made = await keep(await makePage(browser, 'board', async route => {
        await responseReady;
        return route.fulfill({
          status: 200, contentType: 'application/json', body: JSON.stringify(payload(sampleEvents))
        });
      }));
      const { page, state } = made;
      await go(page, 'events');
      await selectCtf(page);
      await waitForApiCount(state, 1);
      await page.waitForFunction(() => document.querySelector('[data-ctf-results]')?.getAttribute('aria-busy') === 'true');
      await selectSource(page, 'fia');
      assert.equal(await page.locator('[data-events-panel="fia"]').isVisible(), true);
      releaseResponse();
      await waitForApiCount(state, 1, 'apiFinished');
      assert.equal(await page.locator('[data-events-panel="fia"]').isVisible(), true);
      assert.equal(await page.locator('[data-events-panel="ctftime"]').isVisible(), false);

      // Starting another request and leaving the screen must not let its completion paint a detached root.
      await selectCtf(page);
      await go(page, 'dashboard');
      assert.equal(state.apiCount, 1, 'the client cache should satisfy the second selection');
      assert.deepEqual(state.pageErrors, []);
    });

    await check('late response after navigation away does not alter the new screen', async () => {
      let releaseResponse;
      const responseReady = new Promise(resolve => { releaseResponse = resolve; });
      const made = await keep(await makePage(browser, 'member', async route => {
        await responseReady;
        return route.fulfill({
          status: 200, contentType: 'application/json', body: JSON.stringify(payload(sampleEvents))
        });
      }));
      const { page, state } = made;
      await go(page, 'events');
      await selectCtf(page);
      await waitForApiCount(state, 1);
      await page.waitForFunction(() => document.querySelector('[data-ctf-results]')?.getAttribute('aria-busy') === 'true');
      await go(page, 'dashboard');
      assert.equal(await page.locator('#view').getAttribute('data-screen'), 'dashboard');
      releaseResponse();
      await waitForApiCount(state, 1, 'apiFinished');
      assert.equal(await page.locator('#view').getAttribute('data-screen'), 'dashboard');
      assert.deepEqual(state.pageErrors, []);
    });

    await check('guest direct-link guard still redirects to login without fetching CTFtime', async () => {
      const made = await keep(await makePage(browser, null, async route => route.fulfill({
        status: 200, contentType: 'application/json', body: JSON.stringify(payload(sampleEvents))
      })));
      const { page, state } = made;
      await page.evaluate(() => { location.hash = 'events'; });
      await page.waitForFunction(() => location.hash === '#login' && document.querySelector('#view')?.dataset.screen === 'login' && document.body.dataset.previewRole === 'guest');
      assert.equal(await page.locator('#view').getAttribute('data-screen'), 'login');
      assert.equal(state.apiCount, 0);
      assert.deepEqual(state.externalRequests, []);
      assert.deepEqual(state.pageErrors, []);
    });

    for (const made of runs) {
      assert.deepEqual(made.state.apiMethods, made.state.apiMethods.map(method => method === 'GET' ? method : 'non-GET'), 'unexpected API method');
    }
  } finally {
    await Promise.all(contexts.map(context => context.close()));
    await browser.close();
  }

  console.log(JSON.stringify({ checks }, null, 2));
  if (checks.some(result => result.status === 'FAIL')) process.exitCode = 1;
})().catch(error => {
  console.error(error);
  process.exitCode = 1;
});
