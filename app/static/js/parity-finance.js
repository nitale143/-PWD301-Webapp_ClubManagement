(() => {
  'use strict';

  const root = document.querySelector('[data-finance-parity]');
  if (!root) return;

  const openDialog = (trigger) => {
    const dialog = document.getElementById(trigger.dataset.dialogOpen);
    if (!dialog || typeof dialog.showModal !== 'function') return;
    const menu = trigger.closest('details');
    if (menu) menu.open = false;
    if (!dialog.open) dialog.showModal();
  };

  root.addEventListener('click', (event) => {
    const target = event.target instanceof Element ? event.target : null;
    if (!target) return;

    const openButton = target.closest('[data-dialog-open]');
    if (openButton) {
      openDialog(openButton);
      return;
    }

    const closeButton = target.closest('[data-dialog-close]');
    if (closeButton) {
      closeButton.closest('dialog')?.close();
      return;
    }

    const tabButton = target.closest('[data-finance-tab]');
    if (tabButton) {
      const selected = tabButton.dataset.financeTab;
      root.querySelectorAll('[data-finance-tab]').forEach((button) => {
        const active = button === tabButton;
        button.classList.toggle('active', active);
        button.setAttribute('aria-selected', String(active));
      });
      root.querySelectorAll('[data-finance-panel]').forEach((panel) => {
        panel.hidden = panel.dataset.financePanel !== selected;
      });
      return;
    }

    if (target.tagName === 'DIALOG' && target.open) target.close();
  });

  const search = root.querySelector('[data-finance-search]');
  const category = root.querySelector('[data-finance-category]');
  const applyFinanceFilters = () => {
    const query = (search?.value || '').trim().toLocaleLowerCase();
    const selectedCategory = category?.value || 'all';
    root.querySelectorAll('[data-filter-row]').forEach((row) => {
      const textMatches = !query || (row.dataset.filterText || '').includes(query);
      const categoryMatches = selectedCategory === 'all' || row.dataset.category === selectedCategory;
      row.hidden = !(textMatches && categoryMatches);
    });
  };
  search?.addEventListener('input', applyFinanceFilters);
  category?.addEventListener('change', applyFinanceFilters);

  const roleSearch = root.querySelector('[data-role-search]');
  roleSearch?.addEventListener('input', () => {
    const query = roleSearch.value.trim().toLocaleLowerCase();
    root.querySelectorAll('[data-role-row]').forEach((row) => {
      row.hidden = !((row.dataset.filterText || '').includes(query));
    });
  });

  root.querySelectorAll('[data-role-form]').forEach((form) => {
    const role = form.querySelector('[data-role-select]');
    const team = form.querySelector('[data-role-team-select]');
    if (!role || !team) return;
    const syncTeamRequirement = () => {
      team.required = role.value === 'TB';
    };
    role.addEventListener('change', syncTeamRequirement);
    syncTeamRequirement();
  });
})();
