(() => {
  const paths = {
    grid: '<rect x="3" y="3" width="7" height="7" rx="2"/><rect x="14" y="3" width="7" height="7" rx="2"/><rect x="3" y="14" width="7" height="7" rx="2"/><rect x="14" y="14" width="7" height="7" rx="2"/>',
    users: '<circle cx="9" cy="8" r="3"/><path d="M3 21v-2a6 6 0 0 1 12 0v2M16 5a3 3 0 0 1 0 6M21 21v-2a6 6 0 0 0-4-5.65"/>',
    calendar: '<rect x="3" y="5" width="18" height="16" rx="3"/><path d="M16 3v4M8 3v4M3 11h18M8 15h2M14 15h2"/>',
    wallet: '<path d="M20 8V5a2 2 0 0 0-2-2L5 5a2 2 0 0 0 0 4h15v12H5a2 2 0 0 1-2-2V7M20 12h-5v5h5"/>',
    sparkles: '<path d="m12 3 2.5 6.5L21 12l-6.5 2.5L12 21l-2.5-6.5L3 12l6.5-2.5L12 3ZM20 2v4M18 4h4"/>',
    shield: '<path d="m12 3 8 3v6c0 5-8 9-8 9s-8-4-8-9V6l8-3Z"/><path d="m8 12 3 3 5-6"/>',
    check: '<path d="m5 12 4 4L19 6"/>',
    plus: '<path d="M12 5v14M5 12h14"/>',
    search: '<circle cx="10.5" cy="10.5" r="6.5"/><path d="m16 16 5 5"/>',
    arrow: '<path d="M4 12h16m-6-6 6 6-6 6"/>',
    chevron: '<path d="m9 5 7 7-7 7"/>',
    download: '<path d="M12 3v12m-5-5 5 5 5-5M4 16v4h16v-4"/>',
    more: '<circle cx="5" cy="12" r="1"/><circle cx="12" cy="12" r="1"/><circle cx="19" cy="12" r="1"/>',
    clock: '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
    location: '<path d="M19 10c0 5-7 11-7 11S5 15 5 10a7 7 0 1 1 14 0Z"/><circle cx="12" cy="10" r="2"/>',
    mail: '<rect x="3" y="5" width="18" height="14" rx="3"/><path d="m3 7 9 6 9-6"/>',
    close: '<path d="m6 6 12 12M18 6 6 18"/>',
    filter: '<path d="M4 6h16M7 12h10M10 18h4"/><circle cx="8" cy="6" r="2"/><circle cx="15" cy="12" r="2"/>',
    edit: '<path d="m15 4 5 5M4 20l4-1L20 7a3 3 0 0 0-4-4L4 15v5Z"/>',
    logout: '<path d="M9 3H4v18h5M9 12h12m-5-5 5 5-5 5"/>',
    settings: '<path d="M12 3v3M12 18v3M3 12h3M18 12h3M5.6 5.6l2.1 2.1M16.3 16.3l2.1 2.1M5.6 18.4l2.1-2.1M16.3 7.7l2.1-2.1"/><circle cx="12" cy="12" r="5"/><circle cx="12" cy="12" r="1"/>',
    file: '<path d="M14 3H5v18h14V8l-5-5Z"/><path d="M14 3v6h5M8 13h8M8 17h5"/>',
    bell: '<path d="M18 8a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9M9 21h6"/>',
    briefcase: '<rect x="3" y="7" width="18" height="14" rx="3"/><path d="M8 7V3h8v4M3 12a20 20 0 0 0 18 0M12 12v3"/>',
  };
  const escape = value => String(value ?? '').replace(/[&<>"']/g, char => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[char]));
  let previousFocus = null;
  window.UI = {
    escape,
    icon: name => `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.65" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${paths[name] || paths.file}</svg>`,
    avatar: (initials, tone='indigo') => `<span class="avatar ${escape(tone)}">${escape(initials)}</span>`,
    badge: (text, tone='neutral') => `<span class="badge ${escape(tone)}">${escape(text)}</span>`,
    money: value => new Intl.NumberFormat('vi-VN', {style:'currency',currency:'VND',maximumFractionDigits:0}).format(Number(value) || 0),
    navigate: key => { window.location.hash = key; },
    toast: message => {
      const region = document.getElementById('toast-region');
      const toast = document.createElement('div');
      toast.className = 'toast'; toast.textContent = message;
      region.append(toast); window.setTimeout(() => toast.remove(), 5000);
    },
    modal: ({title,body='',footer='',onMount}) => {
      const dialog = document.getElementById('preview-dialog');
      previousFocus = document.activeElement;
      document.getElementById('dialog-content').innerHTML = `<div class="dialog-heading"><div><p class="eyebrow">FIA WORKSPACE · PREVIEW</p><h2 id="dialog-title">${escape(title)}</h2></div><button class="icon-button" data-close-dialog aria-label="Đóng hộp thoại">${UI.icon('close')}</button></div><div class="dialog-body">${body}</div>${footer ? `<div class="dialog-footer">${footer}</div>` : ''}`;
      dialog.setAttribute('aria-labelledby','dialog-title');
      dialog.querySelector('[data-close-dialog]').onclick = UI.closeModal;
      dialog.querySelectorAll('[data-modal-close]').forEach(button => {button.onclick=UI.closeModal;});
      if (!dialog.open) dialog.showModal();
      if (onMount) onMount(dialog);
      (dialog.querySelector('input:not([type=hidden]),textarea,select') || dialog.querySelector('[data-close-dialog]')).focus();
    },
    closeModal: () => { document.getElementById('preview-dialog').close(); if(previousFocus?.isConnected) previousFocus.focus(); },
  };
  document.addEventListener('DOMContentLoaded', () => {
    const dialog = document.getElementById('preview-dialog');
    dialog.addEventListener('click', event => { if(event.target === dialog) { const r=dialog.getBoundingClientRect(); if(event.clientX<r.left||event.clientX>r.right||event.clientY<r.top||event.clientY>r.bottom) UI.closeModal(); } });
    dialog.addEventListener('close', () => { if(previousFocus?.isConnected) previousFocus.focus(); });
  });
})();
