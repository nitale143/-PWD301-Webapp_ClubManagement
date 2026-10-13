(() => {
  'use strict';

  const { icon, avatar, badge, money, modal, closeModal, toast, navigate, escape } = window.UI;
  const esc = escape;
  const initials = (name) => String(name || '').trim().split(/\s+/).slice(-2).map((part) => Array.from(part)[0] || '').join('').toLocaleUpperCase('vi') || 'TV';
  const seededEvents = [
    { id: 'welcome', name: 'Ngày hội Chào Tân sinh viên FIA', kind: 'CỘNG ĐỒNG', date: '18/10/2026 · 08:00', place: 'Sảnh Gamma', description: 'Gặp gỡ cộng đồng FIA, làm quen với các ban hoạt động và khám phá những dự án sắp tới.' },
    { id: 'security', name: 'An toàn thông tin cá nhân', kind: 'WORKSHOP', date: '22/10/2026 · 18:30', place: 'Phòng A2.04', description: 'Cùng tìm hiểu những thói quen thiết thực để bảo vệ tài khoản và dữ liệu cá nhân trên mạng.' }
  ];
  const memberDateTime = (value) => {
    const date = value ? new Date(value) : null;
    return date && Number.isFinite(date.getTime())
      ? new Intl.DateTimeFormat('vi-VN', {
        timeZone: 'Asia/Bangkok', day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit'
      }).format(date)
      : '';
  };
  const officialSourceUrl = (value) => {
    if (typeof value !== 'string') return '';
    try {
      const url = new URL(value);
      return url.protocol === 'https:' && url.hostname === 'ctftime.org' && !url.port && !url.username && !url.password && /^\/event\/\d+\/$/.test(url.pathname)
        ? url.href
        : '';
    } catch {
      return '';
    }
  };
  const memberEvents = () => {
    const imported = window.FiaEventImports?.list?.() || [];
    const mapped = imported.map((event) => {
      const start = memberDateTime(event.start);
      const finish = memberDateTime(event.end);
      return {
        id: `ctf-${event.ctftimeId}`,
        name: event.name,
        kind: 'CUỘC THI CTF',
        date: start && finish && start !== finish ? `${start} – ${finish}` : start || 'Chưa cập nhật thời gian',
        place: event.location || 'Địa điểm FIA chưa xác nhận',
        description: 'Sự kiện CTFtime được đưa vào lịch FIA để thành viên theo dõi và đăng ký demo.',
        sourceUrl: officialSourceUrl(event.sourceUrl)
      };
    });
    return [...seededEvents, ...mapped];
  };
  const findMemberEvent = (id) => memberEvents().find((item) => item.id === id);
  const states = new Map();
  const actor = () => {
    const current = window.PreviewSession?.current?.();
    return current?.role === 'member' ? current : { role: 'member', name: 'Thành viên mẫu', code: 'FIA-000' };
  };
  const state = () => {
    const key = String(actor().code || 'FIA-000');
    if (!states.has(key)) states.set(key, {
      tasks: [
        { id: 'brief', title: 'Đọc tài liệu giới thiệu FIA', due: '16/10/2026', status: 'Đang làm' },
        { id: 'idea', title: 'Gợi ý một chủ đề cho buổi chia sẻ', due: '20/10/2026', status: 'Đang làm' }
      ],
      dues: [
        { id: 'monthly', name: 'Quỹ hoạt động tháng 10', amount: 150000, due: '25/10/2026', status: 'Chưa thanh toán' },
        { id: 'semester', name: 'Quỹ học kỳ I', amount: 350000, due: '31/10/2026', status: 'Chưa thanh toán' }
      ],
      chat: [{ role: 'assistant', text: 'Xin chào! Đây là trợ lý mô phỏng trong bản xem trước. Bạn có thể hỏi về task hoặc lịch hoạt động mẫu của mình.' }],
      registrations: {},
      checkin: false
    });
    return states.get(key);
  };
  const heading = (eyebrow, title, subtitle, actions = '') => `<div class="row preview-page-heading"><div class="grow"><p class="eyebrow">${esc(eyebrow)}</p><h2>${esc(title)}</h2><p class="small muted">${esc(subtitle)}</p></div>${actions ? `<div class="toolbar-right">${actions}</div>` : ''}</div>`;
  const empty = (message) => `<div class="empty-state"><span>${esc(message)}</span></div>`;
  const pageNote = (message) => `<p class="small muted">${icon('shield')} ${esc(message)}</p>`;
  const eventCard = (event, compact = false) => `<article class="card"><div class="card-header"><div><p class="eyebrow">${esc(event.kind)} · ${esc(event.date)}</p><h3>${esc(event.name)}</h3><p>${icon('location')} ${esc(event.place)}</p></div>${badge(event.sourceUrl ? 'CTFtime' : 'Sự kiện mẫu', 'neutral')}</div><div class="card-body page-stack"><p>${esc(event.description)}</p><button type="button" class="btn btn-secondary btn-sm" data-member-event="${esc(event.id)}">${compact ? 'Xem lịch' : 'Xem chi tiết'} ${icon('arrow')}</button></div></article>`;

  const dashboardScreen = {
    title: 'Tổng quan của tôi',
    subtitle: 'Lịch hoạt động, nhiệm vụ và khoản cần đóng của bạn.',
    render() {
      const member = actor();
      const own = state();
      const events = memberEvents();
      const due = own.dues.filter((item) => item.status === 'Chưa thanh toán');
      return `<div class="page-stack">
        ${heading('GÓC THÀNH VIÊN', `Chào bạn, ${member.name}`, 'Một góc nhìn riêng với dữ liệu minh họa cho phiên xem trước.')}
        <div class="grid-12">
          <article class="span-4 stat-card"><div class="stat-icon">${icon('briefcase')}</div><div class="stat-value">${own.tasks.length}</div><div class="stat-label">Nhiệm vụ của bạn</div><div class="stat-note">${own.tasks.filter((task) => task.status === 'Đang làm').length} đang thực hiện</div></article>
          <article class="span-4 stat-card"><div class="stat-icon">${icon('wallet')}</div><div class="stat-value">${due.length}</div><div class="stat-label">Khoản quỹ cần đóng</div><div class="stat-note">${money(due.reduce((total, item) => total + item.amount, 0))}</div></article>
          <article class="span-4 stat-card"><div class="stat-icon">${icon('calendar')}</div><div class="stat-value">${events.length}</div><div class="stat-label">Sự kiện sắp tới</div><div class="stat-note">Dành cho thành viên</div></article>
          <section class="span-12 card"><div class="card-header"><div><h2>Lịch sắp tới</h2><p>Sự kiện mẫu dành cho cộng đồng FIA.</p></div><button class="btn btn-ghost btn-sm" type="button" data-member-nav="events">Xem tất cả ${icon('arrow')}</button></div><div class="card-body grid-12">${events.map((event) => `<div class="span-6">${eventCard(event, true)}</div>`).join('')}</div></section>
        </div>
        ${pageNote('Đây là dữ liệu mẫu gắn với thành viên hiện tại; không tải hoặc cập nhật dữ liệu thật.')}
      </div>`;
    },
    bind(root) {
      root.querySelector('[data-member-nav="events"]')?.addEventListener('click', () => navigate('events'));
      root.querySelectorAll('[data-member-event]').forEach((button) => button.addEventListener('click', () => {
        const event = findMemberEvent(button.dataset.memberEvent);
        if (event) { state().selectedEvent = event.id; navigate('event-detail'); }
      }));
    }
  };

  const tasksScreen = {
    title: 'Nhiệm vụ của tôi',
    subtitle: 'Theo dõi đầu việc được giao và gửi cập nhật demo của riêng bạn.',
    render() {
      const own = state();
      return `<div class="page-stack">${heading('CÔNG VIỆC CỦA BẠN', 'Nhiệm vụ cá nhân', 'Chỉ hiển thị hai nhiệm vụ mẫu của thành viên hiện tại.')}
        <div class="grid-12"><div class="span-12 card"><div class="card-header"><div><h2>Danh sách nhiệm vụ</h2><p>Không có công cụ phân công hoặc duyệt nhiệm vụ.</p></div>${badge(`${own.tasks.length} nhiệm vụ`, 'neutral')}</div><div class="card-body page-stack">${own.tasks.map((task) => `<article class="list-item"><span>${icon('briefcase')}</span><div class="grow"><strong>${esc(task.title)}</strong><p class="small muted">Hạn ${esc(task.due)} · Chỉ bạn xem được</p></div>${badge(task.status, task.status === 'Đang làm' ? 'indigo' : 'warning')}<button type="button" class="btn btn-secondary btn-sm" data-submit-task="${esc(task.id)}" ${task.status !== 'Đang làm' ? 'disabled' : ''}>${task.status === 'Đang làm' ? 'Gửi cập nhật demo' : 'Đã gửi demo'}</button></article>`).join('')}</div></div></div>
        ${pageNote('Nội dung gửi chỉ lưu tạm trong trình duyệt này; không có người khác được giao hoặc duyệt.')}</div>`;
    },
    bind(root) {
      root.querySelectorAll('[data-submit-task]').forEach((button) => button.addEventListener('click', () => {
        const task = state().tasks.find((item) => item.id === button.dataset.submitTask);
        if (!task || task.status !== 'Đang làm') return;
        modal({
          title: 'Gửi cập nhật nhiệm vụ demo',
          body: `<form id="member-task-form" class="page-stack"><p>${esc(task.title)}</p><label class="field"><span class="field-label">Ghi chú của bạn</span><textarea class="textarea" name="note" maxlength="300" placeholder="Mô tả ngắn tiến độ mẫu"></textarea></label><p class="small muted">Bản gửi chỉ đổi trạng thái trong dữ liệu xem trước cá nhân.</p></form>`,
          footer: '<button type="button" class="btn btn-secondary" data-modal-close>Hủy</button><button type="submit" form="member-task-form" class="btn btn-primary">Gửi demo</button>',
          onMount(dialog) {
            dialog.querySelector('#member-task-form')?.addEventListener('submit', (event) => {
              event.preventDefault(); task.status = 'Đã gửi demo'; closeModal(); toast('Đã gửi cập nhật trong bản xem trước cá nhân.'); root.innerHTML = tasksScreen.render(); tasksScreen.bind(root);
            });
          }
        });
      }));
    }
  };

  const fundsScreen = {
    title: 'Quỹ của tôi',
    subtitle: 'Các khoản mẫu gắn với tài khoản thành viên hiện tại.',
    render() {
      const own = state();
      return `<div class="page-stack">${heading('TÀI CHÍNH CÁ NHÂN', 'Khoản đóng góp của tôi', 'Chỉ xem nghĩa vụ quỹ mẫu của bạn; không có danh sách hoặc quyền xử lý giao dịch.')}
        <section class="card"><div class="card-header"><div><h2>Các khoản cần đóng</h2><p>Gửi xác nhận thanh toán demo để xem trạng thái cá nhân.</p></div>${badge(`${own.dues.filter((item) => item.status === 'Chưa thanh toán').length} đang chờ`, 'warning')}</div><div class="card-body page-stack">${own.dues.map((item) => `<div class="list-item"><span>${icon('wallet')}</span><div class="grow"><strong>${esc(item.name)}</strong><p class="small muted">Hạn ${esc(item.due)} · ${money(item.amount)}</p></div>${badge(item.status, item.status === 'Chưa thanh toán' ? 'warning' : 'success')}<button type="button" class="btn btn-secondary btn-sm" data-pay-demo="${esc(item.id)}" ${item.status !== 'Chưa thanh toán' ? 'disabled' : ''}>${item.status === 'Chưa thanh toán' ? 'Gửi xác nhận demo' : 'Đã gửi demo'}</button></div>`).join('')}</div></section>
        ${pageNote('Không tạo khoản thu mới, không xác nhận giao dịch và không gửi thông tin thanh toán.')}</div>`;
    },
    bind(root) {
      root.querySelectorAll('[data-pay-demo]').forEach((button) => button.addEventListener('click', () => {
        const due = state().dues.find((item) => item.id === button.dataset.payDemo);
        if (!due || due.status !== 'Chưa thanh toán') return;
        modal({
          title: 'Xác nhận thanh toán demo',
          body: `<form id="member-payment-form" class="page-stack"><p><strong>${esc(due.name)}</strong> · ${money(due.amount)}</p><label class="field"><span class="field-label">Phương thức minh họa</span><select class="select" name="method"><option>Chuyển khoản mẫu</option><option>Tiền mặt mẫu</option></select></label><label class="field"><span class="field-label">Ghi chú (không bắt buộc)</span><input class="input" name="note" maxlength="80" placeholder="Không nhập thông tin ngân hàng thật"></label><p class="small muted">Biểu mẫu không gửi hoặc lưu dữ liệu ra ngoài.</p></form>`,
          footer: '<button type="button" class="btn btn-secondary" data-modal-close>Hủy</button><button type="submit" form="member-payment-form" class="btn btn-primary">Gửi xác nhận demo</button>',
          onMount(dialog) {
            dialog.querySelector('#member-payment-form')?.addEventListener('submit', (event) => {
              event.preventDefault(); due.status = 'Đã gửi demo'; closeModal(); toast('Đã cập nhật trạng thái cá nhân trong bản xem trước.'); root.innerHTML = fundsScreen.render(); fundsScreen.bind(root);
            });
          }
        });
      }));
    }
  };

  const aiScreen = {
    title: 'Trợ lý cá nhân',
    subtitle: 'Trò chuyện mô phỏng về lịch và nhiệm vụ mẫu của riêng bạn.',
    render() {
      const own = state();
      return `<div class="page-stack">${heading('HỖ TRỢ CÁ NHÂN', 'Trợ lý của bạn', 'Mô phỏng trong trình duyệt, không kết nối dịch vụ AI hoặc dữ liệu bên ngoài.')}
        <section class="card"><div class="card-header"><div><h2>Cuộc trò chuyện cá nhân</h2><p>Không tạo đề xuất gửi Ban Điều hành hoặc bản nháp email.</p></div>${badge('Mô phỏng', 'indigo')}</div><div class="card-body page-stack"><div class="chat-history" aria-live="polite">${own.chat.map((message) => `<div class="chat-message ${message.role === 'user' ? 'user' : 'assistant'}"><p>${esc(message.text)}</p></div>`).join('')}</div><form id="member-chat-form" class="chat-composer"><label class="sr-only" for="member-chat-input">Tin nhắn</label><input id="member-chat-input" class="input" name="message" maxlength="300" placeholder="Hỏi về lịch hoặc nhiệm vụ mẫu của bạn" required><button class="btn btn-primary" type="submit">Gửi demo ${icon('arrow')}</button></form></div></section>
        ${pageNote('Tin nhắn chỉ được giữ trong bộ nhớ trang và sẽ mất khi tải lại.')}</div>`;
    },
    bind(root) {
      root.querySelector('#member-chat-form')?.addEventListener('submit', (event) => {
        event.preventDefault();
        const form = event.currentTarget;
        const message = String(new FormData(form).get('message') || '').trim();
        if (!message) return;
        state().chat.push({ role: 'user', text: message }, { role: 'assistant', text: 'Đây là phản hồi mô phỏng. Bạn có thể xem nhiệm vụ hoặc lịch mẫu của mình trong các mục tương ứng.' });
        root.innerHTML = aiScreen.render(); aiScreen.bind(root);
        root.querySelector('#member-chat-input')?.focus();
      });
    }
  };

  const profileScreen = {
    title: 'Hồ sơ của tôi',
    subtitle: 'Thông tin hiển thị của thành viên trong phiên demo này.',
    render() {
      const member = actor();
      return `<div class="page-stack">${heading('TÀI KHOẢN CỦA BẠN', 'Hồ sơ cá nhân', 'Thông tin lấy từ phiên xem trước; không chỉnh sửa hồ sơ thật.')}
        <section class="card"><div class="card-header"><div><h2>Thông tin thành viên</h2><p>Chỉ hiển thị tài khoản hiện tại.</p></div>${avatar(initials(member.name), 'green')}</div><div class="card-body page-stack"><div class="grid-12"><div class="span-6 list-item"><span>${icon('users')}</span><div><strong>Họ và tên</strong><p class="small muted">${esc(member.name)}</p></div></div><div class="span-6 list-item"><span>${icon('file')}</span><div><strong>Mã thành viên</strong><p class="small muted">${esc(member.code)}</p></div></div></div>${badge('Thành viên FIA', 'success')}</div></section>
        ${pageNote('Thông tin danh tính được cung cấp bởi phiên preview và không được gửi đến máy chủ.')}</div>`;
    },
    bind(root) {}
  };

  const eventsScreen = {
    title: 'Sự kiện FIA',
    subtitle: 'Khám phá hoạt động mẫu dành cho thành viên.',
    render: () => `<div class="page-stack">${heading('LỊCH CỘNG ĐỒNG', 'Sự kiện sắp tới', 'Thông tin mẫu; không có công cụ tạo hoặc quản lý sự kiện.')}
      <div class="grid-12">${memberEvents().map((event) => `<div class="span-6">${eventCard(event)}</div>`).join('')}</div>${pageNote('Đăng ký hoặc hủy tham gia chỉ thay đổi trạng thái demo của bạn.')}</div>`,
    bind(root) {
      root.querySelectorAll('[data-member-event]').forEach((button) => button.addEventListener('click', () => {
        const event = findMemberEvent(button.dataset.memberEvent);
        if (event) { state().selectedEvent = event.id; navigate('event-detail'); }
      }));
    }
  };

  const eventDetailScreen = {
    title: 'Chi tiết sự kiện',
    subtitle: 'Thông tin sự kiện và trạng thái đăng ký cá nhân.',
    render() {
      const own = state();
      const event = findMemberEvent(own.selectedEvent) || memberEvents()[0];
      const registered = Boolean(own.registrations[event.id]);
      return `<div class="page-stack">${heading('SỰ KIỆN CỘNG ĐỒNG', 'Chi tiết sự kiện', 'Chế độ thành viên · chỉ thao tác đăng ký của bạn.', `<button type="button" class="btn btn-ghost btn-sm" data-member-nav="events">${icon('arrow')} Trở lại sự kiện</button>`)}
        <section class="card"><div class="card-header"><div><p class="eyebrow">${esc(event.kind)} · ${esc(event.date)}</p><h2>${esc(event.name)}</h2><p>${icon('location')} ${esc(event.place)}</p></div>${badge(registered ? 'Bạn đã đăng ký demo' : 'Còn nhận đăng ký', registered ? 'success' : 'neutral')}</div><div class="card-body page-stack"><p>${esc(event.description)}</p>${event.sourceUrl ? `<p><a class="btn btn-secondary btn-sm" href="${esc(event.sourceUrl)}" target="_blank" rel="noopener noreferrer">Nguồn: CTFtime ↗</a></p>` : ''}<div class="list-item">${avatar(initials(actor().name), 'green')}<div><strong>${esc(actor().name)}</strong><p class="small muted">Trạng thái của bạn</p></div>${badge(registered ? 'Đã đăng ký' : 'Chưa đăng ký', registered ? 'success' : 'neutral')}</div><button type="button" class="btn ${registered ? 'btn-secondary' : 'btn-primary'}" data-member-rsvp>${registered ? 'Hủy đăng ký demo' : 'Đăng ký tham gia demo'}</button></div></section>
        ${pageNote('Trang này không hiển thị danh sách người tham gia, công cụ điểm danh hoặc quản lý sự kiện.')}</div>`;
    },
    bind(root) {
      root.querySelector('[data-member-nav="events"]')?.addEventListener('click', () => navigate('events'));
      root.querySelector('[data-member-rsvp]')?.addEventListener('click', () => {
        const own = state();
        const event = findMemberEvent(own.selectedEvent) || memberEvents()[0];
        own.registrations[event.id] = !own.registrations[event.id];
        toast(own.registrations[event.id] ? 'Đã đăng ký sự kiện trong bản xem trước.' : 'Đã hủy đăng ký trong bản xem trước.');
        root.innerHTML = eventDetailScreen.render(); eventDetailScreen.bind(root);
      });
    }
  };

  const checkinScreen = {
    title: 'Điểm danh của tôi',
    subtitle: 'Xem trạng thái điểm danh minh họa của chính bạn.',
    render() {
      const own = state();
      const event = seededEvents[1];
      return `<div class="page-stack">${heading('SỰ KIỆN · CÁ NHÂN', 'Điểm danh của tôi', 'Chỉ xem trạng thái demo của thành viên hiện tại.')}
        <section class="card"><div class="card-header"><div><p class="eyebrow">${esc(event.date)}</p><h2>${esc(event.name)}</h2><p>${icon('location')} ${esc(event.place)}</p></div>${badge(own.checkin ? 'Đã xác nhận demo' : 'Chưa xác nhận', own.checkin ? 'success' : 'warning')}</div><div class="card-body page-stack"><div class="list-item">${avatar(initials(actor().name), 'green')}<div><strong>${esc(actor().name)}</strong><p class="small muted">Mã ${esc(actor().code)}</p></div></div><button class="btn btn-primary" type="button" data-member-checkin ${own.checkin ? 'disabled' : ''}>${own.checkin ? 'Đã xác nhận demo' : 'Xác nhận điểm danh demo'}</button></div></section>
        ${pageNote('Không dùng camera, tạo mã QR hoặc ghi nhận tham dự thật.')}</div>`;
    },
    bind(root) {
      root.querySelector('[data-member-checkin]')?.addEventListener('click', () => {
        state().checkin = true; toast('Đã xác nhận điểm danh trong dữ liệu demo cá nhân.');
        root.innerHTML = checkinScreen.render(); checkinScreen.bind(root);
      });
    }
  };

  window.memberPreviewScreens = Object.assign(window.memberPreviewScreens || {}, {
    dashboard: dashboardScreen,
    events: eventsScreen,
    'event-detail': eventDetailScreen,
    tasks: tasksScreen,
    funds: fundsScreen,
    ai: aiScreen,
    profile: profileScreen,
    checkin: checkinScreen
  });
})();
