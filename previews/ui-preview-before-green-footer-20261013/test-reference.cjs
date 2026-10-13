const { chromium } = require('playwright');
const assert = require('node:assert/strict');

const base = 'http://127.0.0.1:5082';
const origin = new URL(base).origin;
const screens = [
  'landing', 'dashboard', 'members', 'events', 'event-detail', 'tasks', 'funds',
  'ai', 'approvals', 'roles', 'profile', 'login', 'register', 'pending', 'checkin'
];

(async () => {
  const browser = await chromium.launch({ channel: 'msedge', headless: true });
  const page = await browser.newPage({ viewport: { width: 1440, height: 1000 }, reducedMotion: 'reduce' });
  page.setDefaultTimeout(5000);

  const results = [];
  const pageErrors = [];
  const consoleErrors = [];
  const externalRequests = new Set();
  const badResponses = [];

  page.on('pageerror', error => pageErrors.push(error.message));
  page.on('console', message => {
    if (message.type() === 'error') consoleErrors.push(message.text());
  });
  page.on('request', request => {
    if (new URL(request.url()).origin !== origin) externalRequests.add(request.url());
  });
  page.on('response', response => {
    if (response.status() >= 400) badResponses.push(`${response.status()} ${response.url()}`);
  });
  await page.route('**/*', route => {
    if (new URL(route.request().url()).origin === origin) return route.continue();
    return route.abort();
  });

  const check = async (name, run) => {
    try {
      const detail = await run();
      results.push({ name, status: 'PASS', ...(detail === undefined ? {} : { detail }) });
    } catch (error) {
      results.push({ name, status: 'FAIL', error: String(error.stack || error) });
    }
  };
  const waitForScreen = async key => {
    await page.waitForFunction(expected => document.querySelector('#view')?.dataset.screen === expected, key);
  };
  const routeTo = async key => {
    await page.evaluate(value => { location.hash = `#${value}`; }, key);
    await waitForScreen(key);
  };
  const routeFromLanding = async (selector, key) => {
    await routeTo('landing');
    await page.locator(selector).click();
    await waitForScreen(key);
    assert.equal(new URL(page.url()).hash, `#${key}`);
  };

  try {
    await page.goto(`${base}/#landing`);
    await waitForScreen('landing');

    await check('landing section anchors scroll without replacing the SPA route hash', async () => {
      for (const [label, id] of [['Tính năng', 'rl-features'], ['Hoạt động', 'rl-activities'], ['Hỏi đáp', 'rl-faq']]) {
        await page.evaluate(() => window.scrollTo(0, 0));
        await page.locator(`.rl-nav a[href="#${id}"]`).click();
        await page.waitForFunction(targetId => document.getElementById(targetId)?.getBoundingClientRect().top < 100, id);
        assert.equal(new URL(page.url()).hash, '#landing', `${label} changed the route hash`);
        assert.equal(await page.locator('#view').getAttribute('data-screen'), 'landing');
      }
      await page.setViewportSize({ width: 390, height: 844 });
      await page.evaluate(() => window.scrollTo(0, 0));
      await page.locator('.rl-footer-links a[href="#rl-activities"]').click();
      await page.waitForFunction(() => document.getElementById('rl-activities')?.getBoundingClientRect().top < 100);
      assert.equal(new URL(page.url()).hash, '#landing', 'mobile footer anchor changed the route hash');
    });

    await check('FAQ disclosures open and close by keyboard with a visible focus ring', async () => {
      await routeTo('landing');
      const first = page.locator('.rl-faq-list details').nth(0);
      const firstSummary = first.locator('summary');
      await firstSummary.press('Enter');
      assert.equal(await first.getAttribute('open'), '');
      assert.equal(await first.locator('p').isVisible(), true);
      const focus = await firstSummary.evaluate(element => ({
        focused: document.activeElement === element,
        width: getComputedStyle(element).outlineWidth,
        color: getComputedStyle(element).outlineColor
      }));
      assert.equal(focus.focused, true);
      assert.equal(focus.width, '3px');
      assert.match(focus.color, /255, 117, 160/);
      await firstSummary.press('Space');
      assert.equal(await first.getAttribute('open'), null);
      const second = page.locator('.rl-faq-list details').nth(1);
      await second.locator('summary').press('Space');
      assert.equal(await second.getAttribute('open'), '');
    });

    await check('landing CTAs reach dashboard, login, register, events, and event detail routes', async () => {
      await page.setViewportSize({ width: 1440, height: 1000 });
      await routeFromLanding('.rl-header-actions a[data-route="dashboard"]', 'dashboard');
      await routeFromLanding('.rl-header-actions a[data-route="login"]', 'login');
      await routeFromLanding('.rl-hero-actions a[data-route="register"]', 'register');
      await routeFromLanding('.rl-events-heading a[data-route="events"]', 'events');
      await routeFromLanding('.rl-public-event-body a[data-route="event-detail"]', 'event-detail');
      await page.setViewportSize({ width: 390, height: 844 });
      await routeFromLanding('.rl-mobile-workspace[data-route="dashboard"]', 'dashboard');
    });

    await check('landing and all workspace screens have no desktop or mobile page overflow', async () => {
      const overflow = [];
      for (const [width, height] of [[1440, 1000], [390, 844]]) {
        await page.setViewportSize({ width, height });
        for (const key of screens) {
          await routeTo(key);
          const metrics = await page.evaluate(() => ({
            viewport: innerWidth,
            document: document.documentElement.scrollWidth,
            body: document.body.scrollWidth,
            view: document.querySelector('#view').scrollWidth
          }));
          if (metrics.document > metrics.viewport + 1 || metrics.body > metrics.viewport + 1) {
            overflow.push({ width, screen: key, ...metrics });
          }
        }
      }
      assert.deepEqual(overflow, []);
    });

    await check('mobile workspace menu opens and closes by toggle, overlay, and route navigation', async () => {
      await page.setViewportSize({ width: 390, height: 844 });
      await routeTo('dashboard');
      const toggle = page.locator('#menu-toggle');
      const sidebar = page.locator('#sidebar');
      const overlay = page.locator('#sidebar-overlay');
      await toggle.click();
      assert.equal(await toggle.getAttribute('aria-expanded'), 'true');
      assert.equal(await sidebar.evaluate(element => element.classList.contains('is-open')), true);
      assert.equal(await overlay.isVisible(), true);
      await page.keyboard.press('Escape');
      assert.equal(await toggle.getAttribute('aria-expanded'), 'false');
      assert.equal(await overlay.isVisible(), false);
      await toggle.click();
      await overlay.click({ position: { x: 350, y: 400 } });
      assert.equal(await toggle.getAttribute('aria-expanded'), 'false');
      await toggle.click();
      await page.locator('#primary-navigation a[data-nav="members"]').click();
      await waitForScreen('members');
      assert.equal(await toggle.getAttribute('aria-expanded'), 'false');
    });

    await check('dark workspace event list has no large light surfaces with low-contrast text', async () => {
      await page.setViewportSize({ width: 1440, height: 1000 });
      await routeTo('events');
      await page.locator('[data-event-view="list"]').click();
      const audit = await page.locator('.events-table-card').evaluate(element => {
        const parse = value => {
          const match = value.match(/[\d.]+/g);
          return match ? match.slice(0, 3).map(Number) : null;
        };
        const luminance = color => {
          const channels = parse(color);
          if (!channels) return 0;
          const linear = channels.map(channel => {
            const value = channel / 255;
            return value <= 0.04045 ? value / 12.92 : ((value + 0.055) / 1.055) ** 2.4;
          });
          return linear[0] * 0.2126 + linear[1] * 0.7152 + linear[2] * 0.0722;
        };
        const contrast = (a, b) => {
          const values = [luminance(a), luminance(b)].sort((x, y) => y - x);
          return (values[0] + 0.05) / (values[1] + 0.05);
        };
        const background = getComputedStyle(element).backgroundColor;
        const cells = [...element.querySelectorAll('tbody td')].map(cell => ({
          selector: 'tbody td',
          text: cell.innerText.trim().slice(0, 44),
          color: getComputedStyle(cell).color,
          contrast: Number(contrast(background, getComputedStyle(cell).color).toFixed(2))
        }));
        return {
          background,
          backgroundLuminance: Number(luminance(background).toFixed(3)),
          bounds: { width: element.getBoundingClientRect().width, height: element.getBoundingClientRect().height },
          lowestTextContrast: cells.sort((a, b) => a.contrast - b.contrast)[0]
        };
      });
      assert.ok(audit.backgroundLuminance < 0.12, `unexpected light table surface: ${JSON.stringify(audit)}`);
      assert.ok(audit.lowestTextContrast.contrast >= 4.5, `table text contrast is below 4.5: ${JSON.stringify(audit)}`);
      return audit;
    });

    await check('all checked routes stay local and produce no browser errors or failed resources', async () => {
      assert.deepEqual([...externalRequests], []);
      assert.deepEqual(pageErrors, []);
      assert.deepEqual(consoleErrors, []);
      assert.deepEqual(badResponses, []);
    });
  } finally {
    await browser.close();
  }

  console.log(JSON.stringify({ results, pageErrors, consoleErrors, externalRequests: [...externalRequests], badResponses }, null, 2));
  if (results.some(result => result.status === 'FAIL')) process.exitCode = 1;
})().catch(error => {
  console.error(error);
  process.exitCode = 1;
});
