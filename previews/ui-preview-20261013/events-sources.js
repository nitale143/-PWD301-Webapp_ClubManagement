(() => {
  'use strict';

  const CACHE_MS = 5 * 60 * 1000;
  const CALENDAR_URL = 'https://ctftime.org/calendar/';
  const EVENT_URL_BASE = 'https://ctftime.org/event/';
  const escape = (value) => window.UI?.escape?.(value) ?? String(value ?? '').replace(/[&<>"']/g, (char) => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
  })[char]);
  const parseDate = (value) => {
    const date = value ? new Date(value) : null;
    return date && Number.isFinite(date.getTime()) ? date : null;
  };
  const dateFormatter = new Intl.DateTimeFormat('vi-VN', {
    timeZone: 'Asia/Bangkok', dateStyle: 'medium', timeStyle: 'short'
  });
  const formatDate = (value) => {
    const date = parseDate(value);
    return date ? dateFormatter.format(date) : '';
  };
  const normaliseEvent = (event) => {
    if (!event || typeof event !== 'object') return null;
    const id = String(event.id ?? '').trim();
    const title = String(event.title ?? '').trim();
    const start = parseDate(event.start);
    if (!/^[1-9]\d{0,11}$/.test(id) || !title || !start) return null;
    const finish = parseDate(event.finish);
    let onsite = null;
    if (event.onsite === true || event.onsite === 1) onsite = true;
    else if (event.onsite === false || event.onsite === 0) onsite = false;
    const numericWeight = event.weight === null || event.weight === undefined || event.weight === ''
      ? null
      : Number(event.weight);
    return {
      id,
      title,
      start: start.toISOString(),
      finish: finish ? finish.toISOString() : null,
      ctftime_url: typeof event.ctftime_url === 'string' ? event.ctftime_url : '',
      url: typeof event.url === 'string' ? event.url : '',
      format: String(event.format ?? '').trim(),
      onsite,
      weight: Number.isFinite(numericWeight) ? numericWeight : null,
      location: String(event.location ?? '').trim()
    };
  };

  let eventCache = null;
  let pendingFetch = null;

  function errorText(value, fallback) {
    const message = typeof value === 'string' ? value.trim() : '';
    return message ? message.slice(0, 300) : fallback;
  }

  function loadEvents(force = false) {
    if (!force && eventCache && Date.now() - eventCache.cachedAt < CACHE_MS) {
      return Promise.resolve(eventCache);
    }
    if (pendingFetch) return pendingFetch;

    const previous = eventCache;
    const request = fetch('/api/ctftime/events', {
      method: 'GET',
      credentials: 'same-origin',
      headers: { Accept: 'application/json' },
      cache: 'no-store'
    }).then(async (response) => {
      let payload;
      try {
        payload = await response.json();
      } catch {
        throw new Error('Máy chủ trả về dữ liệu CTFtime không đọc được.');
      }
      if (!response.ok) {
        throw new Error(errorText(payload?.error, `Không tải được lịch CTFtime (HTTP ${response.status}).`));
      }
      if (!payload || !Array.isArray(payload.events)) {
        throw new Error('Dữ liệu lịch CTFtime không đúng định dạng.');
      }
      const events = payload.events.map(normaliseEvent).filter(Boolean);
      if (payload.events.length && !events.length) {
        throw new Error('Không tìm thấy sự kiện hợp lệ trong dữ liệu CTFtime.');
      }
      const record = {
        events,
        source: 'CTFtime',
        fetchedAt: typeof payload.fetched_at === 'string' ? payload.fetched_at : '',
        window: payload.window && typeof payload.window === 'object' ? payload.window : null,
        cached: Boolean(payload.cached),
        stale: Boolean(payload.stale),
        sourceError: errorText(payload.error, ''),
        requestError: '',
        cachedAt: Date.now()
      };
      eventCache = record;
      return record;
    }).catch((error) => ({
      ...(previous || {
        events: [], source: 'CTFtime', fetchedAt: '', window: null, cached: false,
        stale: false, sourceError: '', cachedAt: 0
      }),
      stale: Boolean(previous) || Boolean(previous?.stale),
      requestError: errorText(error?.message, 'Không thể tải lịch CTFtime lúc này.')
    })).finally(() => {
      if (pendingFetch === request) pendingFetch = null;
    });

    pendingFetch = request;
    return request;
  }

  function eventHref(event) {
    const id = String(event.id ?? '');
    if (!/^[1-9]\d{0,11}$/.test(id)) return '';
    for (const candidate of [event.ctftime_url, event.url]) {
      if (typeof candidate !== 'string' || !candidate) continue;
      try {
        const parsed = new URL(candidate);
        if ((parsed.protocol === 'https:' || parsed.protocol === 'http:') &&
            parsed.hostname === 'ctftime.org' && !parsed.port && !parsed.username && !parsed.password &&
            new RegExp(`^/event/${id}/?$`).test(parsed.pathname)) {
          return `${EVENT_URL_BASE}${id}/`;
        }
      } catch {
        // Ignore malformed or non-official upstream links; the numeric ID below is safe.
      }
    }
    return `${EVENT_URL_BASE}${id}/`;
  }

  function metadata(record) {
    const windowStart = formatDate(record?.window?.start);
    const windowFinish = formatDate(record?.window?.finish);
    const range = windowStart && windowFinish ? `${windowStart} – ${windowFinish}` : '';
    const updated = formatDate(record?.fetchedAt);
    const parts = [];
    if (range) parts.push(`Khoảng thời gian: ${range} (giờ Việt Nam).`);
    if (updated) parts.push(`Cập nhật: ${updated}.`);
    return parts.join(' ');
  }

  function eventCard(event) {
    const startLabel = formatDate(event.start);
    const finishLabel = formatDate(event.finish);
    const range = finishLabel ? `${startLabel} – ${finishLabel}` : startLabel;
    const href = eventHref(event);
    let modality = 'Xem hình thức tại CTFtime';
    if (event.onsite === true) modality = 'Tại địa điểm';
    else if (event.onsite === false) modality = 'Trực tuyến';
    const detailsLink = href
      ? `<a class="btn btn-secondary btn-sm" href="${escape(href)}" target="_blank" rel="noopener noreferrer">Chi tiết tại CTFtime</a>`
      : '';
    const weight = Number.isFinite(event.weight)
      ? `<span class="badge neutral">Điểm ${escape(event.weight)}</span>`
      : '';
    const format = event.format
      ? `<span class="badge neutral">${escape(event.format)}</span>`
      : '';
    const isBoard = window.PreviewSession?.current?.()?.role === 'board';
    const imported = window.FiaEventImports?.has(event.id);
    const importButton = isBoard && window.FiaEventImports
      ? `<button class="btn btn-primary btn-sm" type="button" data-ctf-import="${escape(event.id)}">${imported ? 'Đã tạo · Xem FIA' : 'Tạo sự kiện FIA'}</button>`
      : '';
    return `<article class="events-ctf-card">
      <div class="events-ctf-card-top"><span class="badge green">CTFtime</span><div class="events-ctf-card-tags">${format}${weight}</div></div>
      <h3>${escape(event.title)}</h3>
      <p class="events-ctf-time"><time datetime="${escape(event.start)}">${escape(range || 'Chưa có thời gian')}</time><span>Giờ Việt Nam · Asia/Bangkok</span></p>
      <div class="events-ctf-details"><span>${escape(modality)}</span>${event.location ? `<span>${escape(event.location)}</span>` : ''}</div>
      <div class="events-ctf-card-actions">${detailsLink}${importButton}</div>
    </article>`;
  }

  function sourceFooter() {
    return `<p class="events-ctf-source">Nguồn: <a href="${CALENDAR_URL}" target="_blank" rel="noopener noreferrer">Lịch công khai CTFtime</a>. Nội dung sự kiện do CTFtime cung cấp.</p>`;
  }

  function wrap(originalScreen) {
    let activeSource = 'fia';
    let lastRecord = null;
    let loading = false;
    let currentError = '';
    let searchText = '';
    let onsiteOnly = false;
    let sortBy = 'start';

    return {
      title: 'Sự kiện',
      subtitle: 'Lịch hoạt động FIA và các cuộc thi CTFtime.',
      render() {
        const fiaMarkup = typeof originalScreen?.render === 'function' ? originalScreen.render() : '';
        return `<div class="events-sources page-stack">
          <div class="events-source-tabs" role="tablist" aria-label="Nguồn sự kiện">
            <button type="button" class="events-source-tab active" id="events-source-tab-fia" role="tab" aria-controls="events-source-panel-fia" aria-selected="true" tabindex="0" data-events-source="fia">Sự kiện FIA</button>
            <button type="button" class="events-source-tab" id="events-source-tab-ctftime" role="tab" aria-controls="events-source-panel-ctftime" aria-selected="false" tabindex="-1" data-events-source="ctftime">CTFtime</button>
          </div>
          <section class="events-source-panel" id="events-source-panel-fia" role="tabpanel" aria-labelledby="events-source-tab-fia" data-events-panel="fia">
            <div class="events-fia-pane">${fiaMarkup}</div>
          </section>
          <section class="events-source-panel events-ctf-pane" id="events-source-panel-ctftime" role="tabpanel" aria-labelledby="events-source-tab-ctftime" data-events-panel="ctftime" hidden>
            <div class="events-ctf-toolbar">
              <label class="field events-ctf-search"><span class="field-label">Tìm cuộc thi</span><input class="input" type="search" data-ctf-search placeholder="Tên sự kiện CTFtime" autocomplete="off"></label>
              <label class="events-ctf-checkbox"><input type="checkbox" data-ctf-onsite> <span>Chỉ sự kiện tại địa điểm</span></label>
              <label class="field events-ctf-sort"><span class="field-label">Sắp xếp</span><select class="select" data-ctf-sort><option value="start">Thời gian bắt đầu</option><option value="weight" data-ctf-weight-option hidden>Điểm CTFtime</option></select></label>
              <button type="button" class="btn btn-secondary btn-sm" data-ctf-retry hidden>Tải lại</button>
            </div>
            <p class="events-ctf-window" data-ctf-window></p>
            <div class="events-ctf-status" data-ctf-status role="status" aria-live="polite"></div>
            <div class="events-ctf-results" data-ctf-results aria-busy="false"></div>
            ${sourceFooter()}
          </section>
        </div>`;
      },
      bind(root) {
        const fiaPane = root.querySelector('.events-fia-pane');
        if (fiaPane && typeof originalScreen?.bind === 'function') originalScreen.bind(fiaPane);

        const tabs = Array.from(root.querySelectorAll('[data-events-source]'));
        const panels = new Map(Array.from(root.querySelectorAll('[data-events-panel]')).map((panel) => [panel.dataset.eventsPanel, panel]));
        const ctfPanel = panels.get('ctftime');
        const status = ctfPanel?.querySelector('[data-ctf-status]');
        const results = ctfPanel?.querySelector('[data-ctf-results]');
        const windowLabel = ctfPanel?.querySelector('[data-ctf-window]');
        const retryButton = ctfPanel?.querySelector('[data-ctf-retry]');
        const searchInput = ctfPanel?.querySelector('[data-ctf-search]');
        const onsiteInput = ctfPanel?.querySelector('[data-ctf-onsite]');
        const sortSelect = ctfPanel?.querySelector('[data-ctf-sort]');
        const weightOption = ctfPanel?.querySelector('[data-ctf-weight-option]');

        const isCurrentCtfPane = () => Boolean(
          activeSource === 'ctftime' && root.isConnected && root.dataset.screen === 'events' &&
          ctfPanel?.isConnected && root.contains(ctfPanel) && !ctfPanel.hidden
        );

        const paintResults = () => {
          if (!status || !results) return;
          const record = lastRecord;
          const events = record?.events || [];
          const hasWeight = events.some((event) => Number.isFinite(event.weight));
          const hasModality = events.some((event) => typeof event.onsite === 'boolean');
          if (onsiteInput) {
            onsiteInput.closest('label').hidden = !hasModality;
            if (!hasModality) { onsiteOnly = false; onsiteInput.checked = false; }
          }
          if (weightOption) weightOption.hidden = !hasWeight;
          if (!hasWeight && sortSelect?.value === 'weight') {
            sortSelect.value = 'start';
            sortBy = 'start';
          }
          if (windowLabel) windowLabel.textContent = metadata(record);
          retryButton.hidden = !(currentError || record?.sourceError || record?.stale);
          results.setAttribute('aria-busy', String(loading));

          const clientCacheExpired = Boolean(record?.cachedAt && Date.now() - record.cachedAt >= CACHE_MS);
          const stale = Boolean(record?.fetchedAt && (record?.stale || clientCacheExpired || currentError || record?.requestError || record?.sourceError));
          const messages = [];
          if (loading) messages.push(record?.events?.length ? 'Đang cập nhật lịch CTFtime…' : 'Đang tải lịch CTFtime…');
          if (stale) messages.push('Đang hiển thị dữ liệu CTFtime đã lưu; có thể chưa phải bản mới nhất.');
          else if (!loading && record?.cached) messages.push('Dữ liệu được cung cấp từ bộ nhớ đệm gần đây.');
          const detailError = currentError || record?.requestError || record?.sourceError;
          if (detailError) messages.push(detailError);
          status.innerHTML = messages.length
            ? `<div class="events-ctf-notice ${stale ? 'is-stale' : ''}">${messages.map((message) => `<p>${escape(message)}</p>`).join('')}</div>`
            : '';

          const query = searchText.trim().toLocaleLowerCase('vi');
          let visible = events.filter((event) => (!query || event.title.toLocaleLowerCase('vi').includes(query)) && (!onsiteOnly || event.onsite === true));
          if (sortBy === 'weight' && hasWeight) {
            visible = visible.slice().sort((left, right) => {
              const leftWeight = Number.isFinite(left.weight) ? left.weight : Number.NEGATIVE_INFINITY;
              const rightWeight = Number.isFinite(right.weight) ? right.weight : Number.NEGATIVE_INFINITY;
              return rightWeight - leftWeight || Date.parse(left.start) - Date.parse(right.start);
            });
          } else {
            visible = visible.slice().sort((left, right) => Date.parse(left.start) - Date.parse(right.start));
          }

          if (visible.length) {
            results.innerHTML = `<div class="events-ctf-grid">${visible.map(eventCard).join('')}</div>`;
          } else if (loading && !record) {
            results.innerHTML = '<div class="empty-state">Đang tải danh sách cuộc thi CTFtime…</div>';
          } else if (detailError && !events.length) {
            results.innerHTML = `<div class="empty-state"><strong>Chưa tải được lịch CTFtime</strong><span class="small muted">Kiểm tra kết nối rồi thử tải lại. Lịch chính thức vẫn có thể xem tại CTFtime.</span></div>`;
          } else if (events.length) {
            results.innerHTML = '<div class="empty-state"><strong>Không có kết quả phù hợp</strong><span class="small muted">Thử đổi từ khóa hoặc bỏ bộ lọc sự kiện tại địa điểm.</span></div>';
          } else {
            results.innerHTML = '<div class="empty-state"><strong>Không có cuộc thi trong khoảng thời gian này</strong><span class="small muted">Lịch được đồng bộ từ nguồn công khai CTFtime.</span></div>';
          }
        };

        const requestEvents = (force = false) => {
          if (!isCurrentCtfPane()) return;
          loading = true;
          currentError = '';
          if (!lastRecord && eventCache) lastRecord = eventCache;
          paintResults();
          loadEvents(force).then((record) => {
            if (!isCurrentCtfPane()) return;
            lastRecord = record;
            loading = false;
            currentError = record.requestError || '';
            paintResults();
          });
        };

        const selectSource = (source, focus = false) => {
          activeSource = source === 'ctftime' ? 'ctftime' : 'fia';
          for (const tab of tabs) {
            const selected = tab.dataset.eventsSource === activeSource;
            tab.classList.toggle('active', selected);
            tab.setAttribute('aria-selected', String(selected));
            tab.tabIndex = selected ? 0 : -1;
            if (selected && focus) tab.focus();
          }
          for (const [name, panel] of panels) panel.hidden = name !== activeSource;
          if (activeSource === 'ctftime') requestEvents(false);
        };

        tabs.forEach((tab, index) => {
          tab.addEventListener('click', () => selectSource(tab.dataset.eventsSource));
          tab.addEventListener('keydown', (event) => {
            let nextIndex = index;
            if (event.key === 'ArrowRight') nextIndex = (index + 1) % tabs.length;
            else if (event.key === 'ArrowLeft') nextIndex = (index - 1 + tabs.length) % tabs.length;
            else if (event.key === 'Home') nextIndex = 0;
            else if (event.key === 'End') nextIndex = tabs.length - 1;
            else return;
            event.preventDefault();
            selectSource(tabs[nextIndex].dataset.eventsSource, true);
          });
        });
        searchInput?.addEventListener('input', (event) => {
          searchText = event.currentTarget.value;
          paintResults();
        });
        onsiteInput?.addEventListener('change', (event) => {
          onsiteOnly = event.currentTarget.checked;
          paintResults();
        });
        sortSelect?.addEventListener('change', (event) => {
          sortBy = event.currentTarget.value;
          paintResults();
        });
        retryButton?.addEventListener('click', () => requestEvents(true));
        results?.addEventListener('click', (event) => {
          const button = event.target.closest('[data-ctf-import]');
          if (!button || !results.contains(button)) return;
          if (window.PreviewSession?.current?.()?.role !== 'board') {
            window.UI?.toast('Chỉ BDH mới được tạo sự kiện FIA.');
            return;
          }
          const sourceEvent = lastRecord?.events.find((item) => item.id === button.dataset.ctfImport);
          if (!sourceEvent || !window.FiaEventImports) return;
          try {
            const existed = window.FiaEventImports.has(sourceEvent.id);
            window.FiaEventImports.create(sourceEvent);
            fiaPane.innerHTML = originalScreen.render();
            originalScreen.bind?.(fiaPane);
            selectSource('fia', true);
            window.UI?.toast(existed ? 'Sự kiện FIA đã có, không tạo trùng.' : 'Đã tạo sự kiện FIA tham gia CTF (demo).');
          } catch {
            window.UI?.toast('Chưa tạo được sự kiện. Kiểm tra thời gian cuộc thi và thử lại.');
          }
        });
      }
    };
  }

  window.EventSources = { wrap };
})();
