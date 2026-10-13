(() => {
  const labels = {landing:'Giới thiệu FIA',dashboard:'Tổng quan',members:'Thành viên',events:'Sự kiện','event-detail':'Chi tiết sự kiện',tasks:'Công việc',funds:'Quỹ câu lạc bộ',ai:'Trợ lý AI',approvals:'Phê duyệt',roles:'Vai trò & phân quyền',profile:'Hồ sơ cá nhân',login:'Đăng nhập',register:'Đăng ký thành viên',pending:'Chờ phê duyệt',checkin:'Xác nhận điểm danh'};
  const authViews = new Set(['login','register','pending']);
  const view = document.getElementById('view');
  const sidebar = document.getElementById('sidebar');
  const toggle = document.getElementById('menu-toggle');
  const overlay = document.getElementById('sidebar-overlay');
  document.querySelector('.skip-link').addEventListener('click',event=>{event.preventDefault();document.getElementById('main-content').focus();});
  function menu(open) { sidebar.classList.toggle('is-open',open); overlay.hidden=!open; toggle.setAttribute('aria-expanded',String(open)); }
  toggle.onclick = () => menu(!sidebar.classList.contains('is-open'));
  overlay.onclick = () => menu(false);
  document.addEventListener('keydown', e => {if(e.key==='Escape') menu(false);});
  document.querySelectorAll('[data-icon]').forEach(el => {el.innerHTML=UI.icon(el.dataset.icon);});
  function render() {
    const key = location.hash.slice(1).split('?')[0] || 'landing';
    const screen = window.previewScreens?.[key];
    if(!screen) {location.hash='dashboard';return;}
    document.body.classList.toggle('auth-view', authViews.has(key));
    document.body.classList.toggle('landing-view', key === 'landing');
    document.getElementById('topbar-view').textContent=labels[key] || screen.title;
    document.getElementById('page-title').textContent=screen.title;
    document.getElementById('page-subtitle').textContent=screen.subtitle || '';
    document.title=`${labels[key] || screen.title} · FIA UI Preview`;
    document.querySelectorAll('[data-nav]').forEach(link=> {const active=link.dataset.nav===key||(key==='event-detail'&&link.dataset.nav==='events');link.classList.toggle('active',active);if(active) link.setAttribute('aria-current','page');else link.removeAttribute('aria-current');});
    view.dataset.screen = key;
    view.innerHTML=screen.render();
    screen.bind?.(view);
    view.querySelectorAll('[data-route]').forEach(el=>{el.addEventListener('click',()=>UI.navigate(el.dataset.route));});
    menu(false); window.scrollTo(0,0);
  }
  function search() {
    UI.modal({title:'Đi tới màn hình',body:`<label class="field"><span class="field-label">Tìm nhanh</span><input id="screen-search" class="input" placeholder="Ví dụ: thành viên, quỹ, AI…" autocomplete="off"></label><div id="screen-results" class="quick-links"></div><p class="small muted">Các màn hình dùng dữ liệu mẫu. Chưa kết nối backend hiện tại.</p>`,onMount(dialog){const input=dialog.querySelector('#screen-search');const results=dialog.querySelector('#screen-results');const paint=()=>{const term=input.value.normalize('NFD').replace(/\p{Diacritic}/gu,'').toLowerCase();const matches=Object.entries(labels).filter(([,label])=>label.normalize('NFD').replace(/\p{Diacritic}/gu,'').toLowerCase().includes(term));results.innerHTML=matches.length?matches.map(([key,label])=>`<button class="quick-link" data-screen="${key}"><span>${label}</span>${UI.icon('arrow')}</button>`).join(''):'<p class="empty-state">Không tìm thấy màn hình phù hợp.</p>';results.querySelectorAll('[data-screen]').forEach(btn=>btn.onclick=()=>{UI.closeModal();UI.navigate(btn.dataset.screen);});};input.addEventListener('input',paint);paint();}});
  }
  document.getElementById('global-search').onclick=search;
  document.getElementById('preview-options').onclick=search;
  document.addEventListener('keydown',event=>{if((event.ctrlKey||event.metaKey)&&event.key.toLowerCase()==='k'){event.preventDefault();search();}});
  document.getElementById('notification-button').onclick=()=>UI.modal({title:'Thông báo của bạn',body:`<div class="notice-list"><div class="list-item">${UI.avatar('LT','orange')}<div><strong>5 hồ sơ đang chờ phê duyệt</strong><p class="small muted">Hãy chào đón những thành viên mới.</p></div></div><div class="list-item">${UI.avatar('AI','indigo')}<div><strong>Bản nháp email đã sẵn sàng</strong><p class="small muted">AI chưa gửi email. Cần BDH kiểm tra và duyệt.</p></div></div><div class="list-item">${UI.avatar('EV','green')}<div><strong>Workshop sắp diễn ra</strong><p class="small muted">Kiểm tra danh sách đăng ký và task của ban.</p></div></div></div><p class="small muted">Đây là thông báo minh họa trong preview.</p>`,footer:'<button class="btn btn-primary" id="open-approvals">Mở trang phê duyệt</button>',onMount(dialog){dialog.querySelector('#open-approvals').onclick=()=>{UI.closeModal();UI.navigate('approvals');};}});
  window.addEventListener('hashchange',render);render();
})();
