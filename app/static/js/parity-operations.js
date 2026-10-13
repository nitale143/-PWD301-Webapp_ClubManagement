(() => {
    'use strict';

    const eventRoot = document.querySelector('[data-fia-events]');
    if (eventRoot) {
        const panel = eventRoot.closest('[data-events-panel]');
        const grid = panel?.querySelector('[data-event-grid-view]');
        const list = panel?.querySelector('[data-event-list-view]');
        const search = eventRoot.querySelector('[data-event-search]');
        const status = eventRoot.querySelector('[data-event-status]');
        const countLabel = panel?.querySelector('[data-event-count]');
        const viewButtons = [...eventRoot.querySelectorAll('[data-event-view]')];
        const gridCards = [...(grid?.querySelectorAll('[data-fia-event-item]') || [])];
        const listRows = [...(list?.querySelectorAll('[data-fia-event-item]') || [])];
        const total = gridCards.length;
        let view = 'grid';

        const normalized = value => String(value || '').trim().toLocaleLowerCase('vi');
        const ensureEmpty = () => {
            let gridEmpty = grid?.querySelector('[data-event-filter-empty]');
            let listEmpty = list?.querySelector('[data-event-filter-empty]');
            if (!gridEmpty && grid) {
                gridEmpty = document.createElement('div');
                gridEmpty.className = 'empty-state';
                gridEmpty.dataset.eventFilterEmpty = '';
                gridEmpty.innerHTML = '<strong>Không tìm thấy sự kiện</strong><span class="small muted">Thử đổi từ khóa hoặc trạng thái.</span>';
                grid.append(gridEmpty);
            }
            if (!listEmpty && list) {
                listEmpty = document.createElement('div');
                listEmpty.className = 'empty-state';
                listEmpty.dataset.eventFilterEmpty = '';
                listEmpty.innerHTML = '<strong>Không tìm thấy sự kiện</strong><span class="small muted">Thử đổi từ khóa hoặc trạng thái.</span>';
                list.append(listEmpty);
            }
            return { gridEmpty, listEmpty };
        };

        const update = () => {
            const query = normalized(search?.value);
            const selectedStatus = status?.value || 'all';
            const matches = item => {
                const matchesText = !query || normalized(item.dataset.eventSearchValue).includes(query);
                const matchesStatus = selectedStatus === 'all' || item.dataset.eventStatusValue === selectedStatus;
                return matchesText && matchesStatus;
            };
            gridCards.forEach(item => { item.hidden = !matches(item); });
            listRows.forEach(item => { item.hidden = !matches(item); });
            const visibleCount = gridCards.filter(matches).length;
            const { gridEmpty, listEmpty } = ensureEmpty();
            if (gridEmpty) gridEmpty.hidden = visibleCount !== 0 || total === 0;
            if (listEmpty) listEmpty.hidden = visibleCount !== 0 || total === 0;
            if (countLabel) countLabel.textContent = query || selectedStatus !== 'all'
                ? `${visibleCount} / ${total} sự kiện`
                : `${total} sự kiện`;
        };

        const setView = nextView => {
            view = nextView === 'list' ? 'list' : 'grid';
            if (grid) grid.hidden = view !== 'grid';
            if (list) list.hidden = view !== 'list';
            viewButtons.forEach(button => {
                const active = button.dataset.eventView === view;
                button.classList.toggle('active', active);
                button.setAttribute('aria-pressed', String(active));
            });
        };

        search?.addEventListener('input', update);
        status?.addEventListener('change', update);
        viewButtons.forEach(button => button.addEventListener('click', () => setView(button.dataset.eventView)));
        setView(view);
        update();
    }

    const detailRoot = document.querySelector('.ops-event-detail');
    if (detailRoot) {
        const tabs = [...detailRoot.querySelectorAll('[data-event-tab]')];
        const panels = [...detailRoot.querySelectorAll('[data-event-panel]')];
        const selectTab = (name, focus = false) => {
            tabs.forEach((tab, index) => {
                const selected = tab.dataset.eventTab === name;
                tab.classList.toggle('active', selected);
                tab.setAttribute('aria-selected', String(selected));
                tab.tabIndex = selected ? 0 : -1;
                if (selected && focus) tab.focus();
                if (selected) tabs[index]?.setAttribute('aria-current', 'page');
                else tabs[index]?.removeAttribute('aria-current');
            });
            panels.forEach(panel => { panel.hidden = panel.dataset.eventPanel !== name; });
            const url = new URL(window.location.href);
            if (name === 'attendance') url.searchParams.delete('tab');
            else url.searchParams.set('tab', name);
            window.history.replaceState({}, '', url);
        };
        tabs.forEach((tab, index) => {
            tab.addEventListener('click', () => selectTab(tab.dataset.eventTab));
            tab.addEventListener('keydown', event => {
                let nextIndex = index;
                if (event.key === 'ArrowRight') nextIndex = (index + 1) % tabs.length;
                else if (event.key === 'ArrowLeft') nextIndex = (index + tabs.length - 1) % tabs.length;
                else if (event.key === 'Home') nextIndex = 0;
                else if (event.key === 'End') nextIndex = tabs.length - 1;
                else return;
                event.preventDefault();
                selectTab(tabs[nextIndex].dataset.eventTab, true);
            });
        });
        const initial = tabs.find(tab => tab.getAttribute('aria-selected') === 'true')?.dataset.eventTab || 'attendance';
        selectTab(initial);
    }
})();
