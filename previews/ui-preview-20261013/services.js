(() => {
  'use strict';

  const { icon, avatar, badge, money, modal, closeModal, toast, navigate } = window.UI;

  const esc = (value) => String(value ?? '').replace(/[&<>"']/g, (char) => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
  })[char]);
  const moneyText = (value) => money(Number(value) || 0);
  const pageHeading = (eyebrow, title, description, actions = '') => `
    <div class="row preview-page-heading">
      <div class="grow">
        <p class="eyebrow">${esc(eyebrow)}</p>
      </div>
      ${actions ? `<div class="toolbar-right">${actions}</div>` : ''}
    </div>`;
  const field = (label, control, hint = '') => `
    <label class="field"><span class="field-label">${esc(label)}</span>${control}${hint ? `<span class="small muted">${esc(hint)}</span>` : ''}</label>`;
  const input = (name, attrs = '') => `<input class="input" name="${esc(name)}" ${attrs}>`;
  const select = (name, options, attrs = '', selectedValue = null) => `<select class="select" name="${esc(name)}" ${attrs}>${options.map(([value, label]) => `<option value="${esc(value)}"${selectedValue !== null && String(value) === String(selectedValue) ? ' selected' : ''}>${esc(label)}</option>`).join('')}</select>`;
  const repaint = (root, screen) => {
    root.innerHTML = screen.render();
    screen.bind(root);
  };
  const closeAndToast = (message) => {
    closeModal();
    toast(message);
  };
  const confirmModal = ({ title, body, confirmLabel = 'Xác nhận demo', tone = 'primary' }, onConfirm) => {
    modal({
      title,
      body: `<div class="page-stack"><p>${body}</p><div class="badge">Bản xem trước · không ghi dữ liệu thật</div></div>`,
      footer: `<button type="button" class="btn btn-secondary" data-modal-close>Để sau</button><button type="button" class="btn btn-${tone}" data-modal-confirm>${esc(confirmLabel)}</button>`,
      onMount(dialog) {
        dialog.querySelector('[data-modal-close]')?.addEventListener('click', closeModal);
        dialog.querySelector('[data-modal-confirm]')?.addEventListener('click', () => {
          closeModal();
          onConfirm?.();
        });
      }
    });
  };

  const fundsState = {
    tab: 'collections',
    collections: [
      { name: 'Quỹ hoạt động tháng 10', category: 'monthly', amount: 150000, paid: 19, total: 24, due: '25/10/2026', status: 'Đang mở' },
      { name: 'Quỹ học kỳ I', category: 'semester', amount: 350000, paid: 22, total: 24, due: '31/10/2026', status: 'Đang mở' },
      { name: 'Workshop Chạm', category: 'event', amount: 80000, paid: 16, total: 20, due: '20/10/2026', status: 'Đang mở' },
      { name: 'Đóng góp tự nguyện', category: 'voluntary', amount: 0, paid: 8, total: 24, due: '—', status: 'Đang mở' }
    ],
    payments: [
      { id: 'P-1028', member: 'Nguyễn Minh Anh', collection: 'Quỹ học kỳ I', amount: 350000, method: 'Chuyển khoản', code: 'VCB-840214', status: 'Chờ xác nhận' },
      { id: 'P-1027', member: 'Trần Gia Huy', collection: 'Workshop Chạm', amount: 80000, method: 'Tiền mặt', code: '—', status: 'Chờ xác nhận' },
      { id: 'P-1023', member: 'Lê Hoàng Yến', collection: 'Quỹ hoạt động tháng 10', amount: 150000, method: 'Chuyển khoản', code: 'MB-190322', status: 'Chờ xác nhận' }
    ],
    transactions: [
      { date: '12/10/2026', category: 'Hậu cần', note: 'In ấn tài liệu Workshop Chạm', amount: -420000, type: 'expense' },
      { date: '10/10/2026', category: 'Quỹ học kỳ I', note: 'Thu quỹ thành viên', amount: 2450000, type: 'income' },
      { date: '08/10/2026', category: 'Truyền thông', note: 'Thuê thiết bị chụp ảnh', amount: -650000, type: 'expense' },
      { date: '05/10/2026', category: 'Quỹ hoạt động', note: 'Thu quỹ tháng 10', amount: 1800000, type: 'income' }
    ]
  };

  const fundsScreen = {
    title: 'Quỹ CLB',
    subtitle: 'Theo dõi khoản thu, chi và các xác nhận thanh toán.',
    render() {
      const panels = {
        collections: `
          <div class="table-wrap"><table class="data-table"><thead><tr><th>Khoản thu</th><th>Hạn đóng</th><th>Tiến độ</th><th>Số tiền</th><th>Trạng thái</th></tr></thead><tbody>
            ${fundsState.collections.map((item) => `<tr data-filter-row data-category="${esc(item.category)}" data-filter-text="${esc(`${item.name} ${item.status}`.toLowerCase())}">
              <td><div class="row">${icon('wallet')}<div><strong>${esc(item.name)}</strong><div class="small muted">${esc(item.category === 'monthly' ? 'Hằng tháng' : item.category === 'semester' ? 'Học kỳ' : item.category === 'event' ? 'Sự kiện' : 'Tự nguyện')}</div></div></div></td>
              <td>${esc(item.due)}</td><td><strong>${item.paid}/${item.total}</strong><div class="progress-bar"><span style="width:${Math.round((item.paid / item.total) * 100)}%"></span></div></td>
              <td>${item.amount ? moneyText(item.amount) : 'Tùy tâm'}</td><td>${badge(item.status, 'success')}</td>
            </tr>`).join('')}
          </tbody></table></div>` ,
        transactions: `
          <div class="table-wrap"><table class="data-table"><thead><tr><th>Ngày</th><th>Danh mục</th><th>Nội dung</th><th>Loại</th><th>Số tiền</th></tr></thead><tbody>
            ${fundsState.transactions.map((item) => `<tr data-filter-row data-category="${esc(item.type)}" data-filter-text="${esc(`${item.date} ${item.category} ${item.note}`.toLowerCase())}">
              <td>${esc(item.date)}</td><td><strong>${esc(item.category)}</strong></td><td>${esc(item.note)}</td><td>${badge(item.type === 'income' ? 'Thu' : 'Chi', item.type === 'income' ? 'success' : 'warning')}</td><td class="${item.type === 'income' ? 'text-positive' : 'text-negative'}"><strong>${item.amount > 0 ? '+' : '−'}${moneyText(Math.abs(item.amount))}</strong></td>
            </tr>`).join('')}
          </tbody></table></div>`,
        payments: `
          <div class="table-wrap"><table class="data-table"><thead><tr><th>Mã</th><th>Thành viên</th><th>Khoản thu</th><th>Số tiền</th><th>Phương thức / mã giao dịch</th><th>Trạng thái</th><th></th></tr></thead><tbody>
            ${fundsState.payments.map((payment) => `<tr data-filter-row data-category="pending" data-filter-text="${esc(`${payment.id} ${payment.member} ${payment.collection} ${payment.code}`.toLowerCase())}">
              <td><strong>${esc(payment.id)}</strong></td><td>${esc(payment.member)}</td><td>${esc(payment.collection)}</td><td>${moneyText(payment.amount)}</td><td>${esc(payment.method)}<div class="small muted">${esc(payment.code)}</div></td><td>${badge(payment.status, 'warning')}</td>
              <td><div class="row"><button class="btn btn-primary btn-sm" data-payment-action="confirm" data-payment-id="${esc(payment.id)}">Xác nhận</button><button class="btn btn-ghost btn-sm" data-payment-action="reject" data-payment-id="${esc(payment.id)}">Từ chối</button></div></td>
            </tr>`).join('') || `<tr><td colspan="7"><div class="empty-state">${icon('check')}<strong>Đã xử lý hết</strong><span class="muted">Không còn giao dịch chờ xác nhận.</span></div></td></tr>`}
          </tbody></table></div>`
      };
      const activeTab = fundsState.tab;
      return `<div class="page-stack preview-funds">
        ${pageHeading('TÀI CHÍNH · KỲ THU 2026', 'Quỹ CLB', 'Dữ liệu mẫu cho kỳ Thu 2026. Các thao tác trong trang này chỉ cập nhật bản xem trước.', `<button class="btn btn-primary" data-open-collection>${icon('plus')} Tạo khoản thu</button><button class="btn btn-secondary" data-export-demo>${icon('download')} Xuất báo cáo</button>`)}
        <div class="grid-12">
          <div class="span-3 stat-card"><div class="stat-icon">${icon('wallet')}</div><div class="stat-value">${moneyText(12850000)}</div><div class="stat-label">Số dư hiện tại</div><div class="stat-note">Kỳ Thu 2026</div></div>
          <div class="span-3 stat-card"><div class="stat-icon">${icon('arrow')}</div><div class="stat-value">${moneyText(18400000)}</div><div class="stat-label">Tổng thu</div><div class="stat-note">+12% so với kỳ trước</div></div>
          <div class="span-3 stat-card"><div class="stat-icon">${icon('briefcase')}</div><div class="stat-value">${moneyText(5550000)}</div><div class="stat-label">Tổng chi</div><div class="stat-note">4 khoản chi đã ghi nhận</div></div>
          <div class="span-3 stat-card"><div class="stat-icon">${icon('clock')}</div><div class="stat-value">${fundsState.payments.length}</div><div class="stat-label">Thanh toán cần xác nhận</div><div class="stat-note">Chờ thủ quỹ xử lý</div></div>
        </div>
        <section class="card"><div class="card-header"><div><h2>Quản lý quỹ</h2><p class="muted small">Lọc theo tên, khoản thu và giao dịch mẫu.</p></div></div><div class="card-body page-stack"><div class="toolbar"><div class="toolbar-left"><label class="field preview-search"><span class="field-label">Tìm kiếm</span><span class="input-with-icon">${icon('search')}<input class="input" id="fund-search" type="search" placeholder="Tên khoản thu, thành viên…"></span></label><label class="field"><span class="field-label">Danh mục</span>${select('category', [['all', 'Tất cả danh mục'], ['monthly', 'Hằng tháng'], ['semester', 'Học kỳ'], ['event', 'Sự kiện'], ['voluntary', 'Tự nguyện'], ['income', 'Thu'], ['expense', 'Chi'], ['pending', 'Chờ xác nhận']], 'id="fund-category"')}</label></div></div>
          <div class="tabs" role="tablist"><button class="${activeTab === 'collections' ? 'active' : ''}" data-fund-tab="collections" role="tab" aria-selected="${activeTab === 'collections'}">Khoản thu</button><button class="${activeTab === 'transactions' ? 'active' : ''}" data-fund-tab="transactions" role="tab" aria-selected="${activeTab === 'transactions'}">Thu / chi</button><button class="${activeTab === 'payments' ? 'active' : ''}" data-fund-tab="payments" role="tab" aria-selected="${activeTab === 'payments'}">Thanh toán ${fundsState.payments.length ? badge(String(fundsState.payments.length), 'warning') : ''}</button></div>
          <div class="fund-panel" data-fund-panel="${activeTab}">${panels[activeTab]}</div>
        </div></section>
        <div class="row preview-footnote"><span class="muted small">${icon('shield')} Dữ liệu minh họa. Không có giao dịch thật được tạo hoặc cập nhật.</span><button class="btn btn-ghost btn-sm" data-reminder>${icon('mail')} Xem trước nhắc đóng quỹ</button></div>
      </div>`;
    },
    bind(root) {
      const applyFilters = () => {
        const query = (root.querySelector('#fund-search')?.value || '').trim().toLowerCase();
        const category = root.querySelector('#fund-category')?.value || 'all';
        root.querySelectorAll('[data-filter-row]').forEach((row) => {
          const textMatch = !query || row.dataset.filterText.includes(query);
          const categoryMatch = category === 'all' || row.dataset.category === category;
          row.hidden = !(textMatch && categoryMatch);
        });
      };
      root.querySelector('#fund-search')?.addEventListener('input', applyFilters);
      root.querySelector('#fund-category')?.addEventListener('change', applyFilters);
      root.querySelectorAll('[data-fund-tab]').forEach((button) => button.addEventListener('click', () => {
        fundsState.tab = button.dataset.fundTab;
        repaint(root, fundsScreen);
      }));
      root.querySelector('[data-open-collection]')?.addEventListener('click', () => {
        modal({
          title: 'Tạo khoản thu mới',
          body: `<p class="muted">Biểu mẫu dùng dữ liệu mẫu và không mở khoản thu thật.</p><form class="page-stack" id="preview-collection-form">
            ${field('Tên khoản thu', input('name', 'type="text" maxlength="180" required placeholder="Ví dụ: Quỹ hoạt động tháng 11"'))}
            ${field('Loại khoản thu', select('type', [['monthly', 'Hằng tháng'], ['semester', 'Học kỳ'], ['yearly', 'Hằng năm'], ['event', 'Sự kiện'], ['voluntary', 'Tự nguyện'], ['other', 'Khác']]))}
            ${field('Số tiền (₫)', input('amount', 'type="number" min="1" step="1" required placeholder="150000"'))}
            <div class="form-grid">${field('Ngày bắt đầu', input('start_date', 'type="date" required'))}${field('Hạn đóng', input('due_date', 'type="date" required'))}</div>
            ${field('Mô tả', '<textarea class="textarea" name="description" rows="3" maxlength="500" placeholder="Ghi chú cho thành viên"></textarea>')}
          </form>`,
          footer: `<button type="button" class="btn btn-secondary" data-modal-close>Hủy</button><button type="submit" form="preview-collection-form" class="btn btn-primary">Tạo bản xem trước</button>`,
          onMount(dialog) {
            dialog.querySelector('[data-modal-close]')?.addEventListener('click', closeModal);
            dialog.querySelector('#preview-collection-form')?.addEventListener('submit', (event) => {
              event.preventDefault();
              const form = event.currentTarget;
              if (!form.reportValidity()) return;
              const values = Object.fromEntries(new FormData(form).entries());
              if (values.due_date < values.start_date) {
                form.querySelector('[name="due_date"]').setCustomValidity('Hạn đóng phải sau ngày bắt đầu.');
                form.reportValidity();
                form.querySelector('[name="due_date"]').setCustomValidity('');
                return;
              }
              fundsState.collections.unshift({ name: values.name.trim(), category: values.type, amount: Number(values.amount), paid: 0, total: 24, due: new Date(`${values.due_date}T00:00:00`).toLocaleDateString('vi-VN'), status: 'Bản xem trước' });
              closeAndToast('Đã thêm khoản thu vào dữ liệu mẫu.');
              repaint(root, fundsScreen);
            });
          }
        });
      });
      root.querySelectorAll('[data-payment-action]').forEach((button) => button.addEventListener('click', () => {
        const payment = fundsState.payments.find((item) => item.id === button.dataset.paymentId);
        if (!payment) return;
        const action = button.dataset.paymentAction;
        confirmModal({
          title: action === 'confirm' ? 'Xác nhận khoản thanh toán?' : 'Từ chối khoản thanh toán?',
          body: `Giao dịch <strong>${esc(payment.id)}</strong> của ${esc(payment.member)} · ${moneyText(payment.amount)}. Đây chỉ là thao tác mẫu trong bản xem trước.`,
          confirmLabel: action === 'confirm' ? 'Xác nhận demo' : 'Từ chối demo',
          tone: action === 'confirm' ? 'primary' : 'danger'
        }, () => {
          fundsState.payments = fundsState.payments.filter((item) => item.id !== payment.id);
          closeModal();
          toast(action === 'confirm' ? 'Đã xác nhận trong dữ liệu mẫu.' : 'Đã từ chối trong dữ liệu mẫu.');
          repaint(root, fundsScreen);
        });
      }));
      root.querySelector('[data-export-demo]')?.addEventListener('click', () => toast('Đây là bản xem trước; không tạo tệp xuất.'));
      root.querySelector('[data-reminder]')?.addEventListener('click', () => modal({
        title: 'Xem trước email nhắc đóng quỹ',
        body: `<p>Email mẫu gửi đến 5 thành viên còn thiếu khoản thu Quỹ học kỳ I.</p><div class="card"><p><strong>Tiêu đề</strong><br>Nhắc đóng quỹ học kỳ I</p><p><strong>Nội dung</strong><br>Chào bạn, quỹ học kỳ I của CLB đang chờ xác nhận. Vui lòng xem lại thông tin khoản thu trong hệ thống.</p></div><p class="small muted">Không có email nào được gửi.</p>`,
        footer: `<button type="button" class="btn btn-secondary" data-modal-close>Đóng</button>`,
        onMount(dialog) { dialog.querySelector('[data-modal-close]')?.addEventListener('click', closeModal); }
      }));
    }
  };

  const aiState = {
    showArchived: false,
    activeId: 'chat-1',
    chats: [
      { id: 'chat-1', title: 'Kế hoạch Workshop An toàn thông tin', archived: false, messages: [{ role: 'assistant', text: 'Chào bạn! Mình có thể hỗ trợ xem lại kế hoạch mẫu, thành viên và sự kiện của FIA.' }, { role: 'user', text: 'Tóm tắt các đầu việc hậu cần tuần này.' }, { role: 'assistant', text: 'Theo dữ liệu minh họa: nhóm hậu cần có 3 đầu việc trong tuần, gồm chuẩn bị địa điểm, in tài liệu và kiểm tra thiết bị. Hãy đối chiếu với ban tổ chức trước khi áp dụng.' }], log: ['Đã đọc yêu cầu trong cuộc trò chuyện hiện tại.', 'Đã chuẩn bị phản hồi mô phỏng dựa trên bộ dữ liệu mẫu.'] },
      { id: 'chat-2', title: 'Tổng hợp hoạt động tháng 10', archived: false, messages: [{ role: 'assistant', text: 'Đây là cuộc trò chuyện mẫu về tổng hợp hoạt động tháng 10.' }], log: ['Đã mở lịch sử hội thoại mẫu.'] },
      { id: 'chat-3', title: 'Ý tưởng tuyển thành viên', archived: true, messages: [{ role: 'assistant', text: 'Cuộc trò chuyện lưu trữ chỉ để xem trong bản demo.' }], log: ['Đã mở lịch sử hội thoại lưu trữ mẫu.'] }
    ],
    emailDraft: { to: 'ban.dieu.hanh@example.test', subject: 'Tổng hợp hoạt động tháng 10', body: 'Chào Ban Điều hành,\n\nĐây là bản nháp tổng hợp hoạt động tháng 10 để xem lại trước khi gửi.\n\nTrân trọng,\nFIA' },
    proposal: { title: 'Workshop An toàn thông tin · buổi chia sẻ kỹ năng', summary: 'Thời gian dự kiến: 28/10/2026 · Ban phụ trách: Hậu cần, Truyền thông · 4 đầu việc dự kiến' }
  };
  const aiScreen = {
    title: 'AI Agent',
    subtitle: 'Trợ lý hội thoại và khu vực xem trước đề xuất.',
    render() {
      const chat = aiState.chats.find((item) => item.id === aiState.activeId) || aiState.chats[0];
      const chats = aiState.chats.filter((item) => item.archived === aiState.showArchived);
      return `<div class="page-stack preview-ai">
        ${pageHeading('TRỢ LÝ · BẢN XEM TRƯỚC', 'AI Agent', 'Hội thoại và nội dung bên dưới là mô phỏng. Không gọi AI bên ngoài, không gửi email và không áp dụng đề xuất.')}
        <div class="chat-layout">
          <aside class="chat-conversations card">
            <div class="card-header"><div><h2>Cuộc trò chuyện</h2><p class="small muted">${aiState.showArchived ? 'Đang xem mục lưu trữ' : 'Các cuộc trò chuyện đã lưu'}</p></div><button class="btn btn-ghost btn-sm" data-chat-filter="${aiState.showArchived ? 'active' : 'archived'}">${aiState.showArchived ? 'Đang dùng' : 'Đã lưu trữ'}</button></div>
            <form id="new-chat-form" class="toolbar"><input class="input" name="title" maxlength="100" placeholder="Tên chat mới (không bắt buộc)"><button class="btn btn-primary btn-sm" type="submit">${icon('plus')} Chat mới</button></form>
            <nav class="page-stack" aria-label="Danh sách hội thoại">${chats.map((item) => `<button class="list-item ${item.id === chat?.id ? 'active' : ''}" data-chat-id="${esc(item.id)}"><span>${icon('calendar')}</span><span class="grow"><strong>${esc(item.title)}</strong><span class="small muted">${item.archived ? 'Đã lưu trữ' : 'Đang dùng'}</span></span>${item.id === chat?.id ? icon('chevron') : ''}</button>`).join('') || `<div class="empty-state"><span>Chưa có cuộc trò chuyện.</span></div>`}</nav>
          </aside>
          <section class="chat-thread card"><header class="card-header"><div><p class="eyebrow">${chat?.archived ? 'ĐÃ LƯU TRỮ' : 'CUỘC TRÒ CHUYỆN'}</p><h2>${esc(chat?.title || 'Chat mới')}</h2></div>${badge('Mô phỏng', 'warning')}</header>
            <div class="chat-history" id="preview-chat-history" aria-live="polite">${chat?.messages.map((message) => `<div class="chat-bubble ${message.role === 'user' ? 'user' : ''}"><span class="small muted">${message.role === 'user' ? 'Bạn' : 'Trợ lý · Demo'}</span><p>${esc(message.text)}</p></div>`).join('') || `<div class="empty-state">Bắt đầu cuộc trò chuyện mẫu của bạn.</div>`}</div>
            ${chat?.archived ? `<p class="small muted">Cuộc trò chuyện đã lưu trữ, chỉ xem trong bản demo.</p>` : `<form class="chat-composer" id="preview-chat-form"><input class="input" name="message" maxlength="2000" placeholder="Hỏi về thành viên, sự kiện, task…" required autocomplete="off"><button class="btn btn-primary" type="submit">${icon('arrow')} Gửi demo</button></form>`}
            <details class="card-body preview-operation-log"><summary><strong>Nhật ký thao tác xem trước</strong><span class="small muted">· Hoạt động hiển thị, không bao gồm suy luận riêng</span></summary><ol class="small">${(chat?.log || []).map((item) => `<li>${esc(item)}</li>`).join('')}</ol></details>
          </section>
        </div>
        <section class="card"><div class="card-header"><div><p class="eyebrow">XEM LẠI TRƯỚC KHI ÁP DỤNG</p><h2>Bản nháp email & đề xuất</h2><p class="muted small">BDH duyệt thủ công ở hệ thống thật. Hai nút dưới đây chỉ mở bản xem trước.</p></div>${icon('shield')}</div>
          <div class="grid-12"><article class="span-6 card-body preview-draft"><div class="row">${icon('mail')}<strong>Nháp email</strong>${badge('Chờ xem lại', 'warning')}</div><p class="small muted">${esc(aiState.emailDraft.subject)} · ${esc(aiState.emailDraft.to)}</p><button class="btn btn-secondary btn-sm" data-ai-preview="email">${icon('file')} Xem nội dung nháp</button></article>
          <article class="span-6 card-body preview-draft"><div class="row">${icon('sparkles')}<strong>Đề xuất hoạt động</strong>${badge('Bản xem trước', 'neutral')}</div><p class="small muted">${esc(aiState.proposal.title)}</p><button class="btn btn-secondary btn-sm" data-ai-preview="proposal">${icon('file')} Xem đề xuất</button></article></div>
        </section>
        <p class="small muted">${icon('shield')} Chế độ an toàn: nội dung do người dùng nhập chỉ hiển thị trong trình duyệt; không có backend hoặc dịch vụ mạng.</p>
      </div>`;
    },
    bind(root) {
      root.querySelector('#new-chat-form')?.addEventListener('submit', (event) => {
        event.preventDefault();
        const form = event.currentTarget;
        if (!form.reportValidity()) return;
        const title = new FormData(form).get('title').trim() || 'Cuộc trò chuyện mới';
        const id = `chat-${Date.now()}`;
        aiState.chats.unshift({ id, title, archived: false, messages: [], log: ['Đã tạo cuộc trò chuyện mẫu trong trình duyệt.'] });
        aiState.activeId = id;
        aiState.showArchived = false;
        repaint(root, aiScreen);
      });
      root.querySelector('[data-chat-filter]')?.addEventListener('click', () => {
        aiState.showArchived = !aiState.showArchived;
        const firstChat = aiState.chats.find((item) => item.archived === aiState.showArchived);
        if (firstChat) aiState.activeId = firstChat.id;
        repaint(root, aiScreen);
      });
      root.querySelectorAll('[data-chat-id]').forEach((button) => button.addEventListener('click', () => {
        aiState.activeId = button.dataset.chatId;
        repaint(root, aiScreen);
      }));
      root.querySelector('#preview-chat-form')?.addEventListener('submit', (event) => {
        event.preventDefault();
        const form = event.currentTarget;
        if (!form.reportValidity()) return;
        const message = new FormData(form).get('message').trim();
        if (!message) return;
        const chat = aiState.chats.find((item) => item.id === aiState.activeId);
        if (!chat) return;
        chat.messages.push({ role: 'user', text: message });
        chat.messages.push({ role: 'assistant', text: 'Đây là phản hồi mô phỏng dựa trên dữ liệu mẫu của bản xem trước. Hãy kiểm tra thông tin với người phụ trách trước khi sử dụng.' });
        chat.log.push('Đã hiển thị một phản hồi mô phỏng; không gọi model hoặc công cụ bên ngoài.');
        repaint(root, aiScreen);
      });
      root.querySelectorAll('[data-ai-preview]').forEach((button) => button.addEventListener('click', () => {
        const isEmail = button.dataset.aiPreview === 'email';
        const draft = aiState.emailDraft;
        modal({
          title: isEmail ? 'Xem trước nháp email' : 'Xem trước đề xuất',
          body: isEmail ? `<div class="page-stack">${badge('Chờ BDH xem xét', 'warning')}<p><strong>Người nhận</strong><br>${esc(draft.to)}</p><p><strong>Tiêu đề</strong><br>${esc(draft.subject)}</p><div class="card card-body"><strong>Nội dung</strong><p style="white-space:pre-wrap">${esc(draft.body)}</p></div><p class="small muted">Không gửi email trong bản xem trước.</p></div>` : `<div class="page-stack">${badge('Đề xuất mẫu · chưa áp dụng')}<h3>${esc(aiState.proposal.title)}</h3><p>${esc(aiState.proposal.summary)}</p><p class="small muted">Cần BĐH xác nhận trước khi tạo sự kiện hoặc giao task.</p></div>`,
          footer: `<button type="button" class="btn btn-secondary" data-modal-close>Đóng</button><button type="button" class="btn btn-primary" data-modal-preview-ok>Đã xem bản demo</button>`,
          onMount(dialog) {
            dialog.querySelector('[data-modal-close]')?.addEventListener('click', closeModal);
            dialog.querySelector('[data-modal-preview-ok]')?.addEventListener('click', () => closeAndToast('Đã xem nội dung mẫu. Không có email hoặc đề xuất nào được áp dụng.'));
          }
        });
      }));
    }
  };

  const approvalState = [
    { id: 'm-221', name: 'Đỗ Ngọc Mai', initials: 'ĐM', studentId: '22110418', dob: '08/04/2005', phone: '0912 345 678', email: 'ngocmai@example.test', team: 'Truyền thông', applied: '11/10/2026', status: 'pending' },
    { id: 'm-222', name: 'Phạm Quốc Bảo', initials: 'PB', studentId: '22110563', dob: '19/11/2004', phone: '0987 210 456', email: 'quocbao@example.test', team: 'Hậu cần', applied: '10/10/2026', status: 'pending' },
    { id: 'm-223', name: 'Vũ Thanh Trúc', initials: 'VT', studentId: '22110730', dob: '22/02/2005', phone: '0904 333 188', email: 'thanhtruc@example.test', team: 'Nội dung', applied: '09/10/2026', status: 'pending' }
  ];
  const approvalScreen = {
    title: 'Duyệt thành viên mới',
    subtitle: 'Xem thông tin đăng ký và ghi nhận quyết định mẫu của Ban Điều hành.',
    render() {
      const pending = approvalState.filter((member) => member.status === 'pending');
      return `<div class="page-stack">
        ${pageHeading('BAN ĐIỀU HÀNH · THÀNH VIÊN', 'Duyệt thành viên mới', 'Kiểm tra thông tin đăng ký trước khi chấp nhận. Mọi quyết định tại đây chỉ thay đổi trạng thái demo.', `<button class="btn btn-secondary" data-nav="roles">${icon('users')} Quản lý chức vụ</button>`)}
        <div class="grid-12"><div class="span-4 stat-card"><div class="stat-icon">${icon('users')}</div><div class="stat-value">${pending.length}</div><div class="stat-label">Đơn đang chờ</div><div class="stat-note">Cập nhật trong 7 ngày</div></div><div class="span-4 stat-card"><div class="stat-icon">${icon('check')}</div><div class="stat-value">12</div><div class="stat-label">Đã duyệt tháng này</div><div class="stat-note">Dữ liệu minh họa</div></div><div class="span-4 stat-card"><div class="stat-icon">${icon('clock')}</div><div class="stat-value">1,4 ngày</div><div class="stat-label">Thời gian xử lý trung bình</div><div class="stat-note">Theo mẫu demo</div></div></div>
        <div class="row preview-status-note"><span class="muted small">${icon('shield')} Duyệt hoặc từ chối không gửi email thật; email thông báo chỉ có thể xem trước.</span></div>
        ${pending.length ? `<div class="grid-12">${pending.map((member) => `<article class="span-6 card member-review-card"><div class="card-header"><div class="row">${avatar(member.initials)}<div><h2>${esc(member.name)}</h2><p class="small muted">MSSV ${esc(member.studentId)} · Nộp ${esc(member.applied)}</p></div></div>${badge('Chờ duyệt', 'warning')}</div><div class="card-body"><dl class="preview-member-details"><div><dt>Ngày sinh</dt><dd>${esc(member.dob)}</dd></div><div><dt>Số điện thoại</dt><dd>${esc(member.phone)}</dd></div><div><dt>Email</dt><dd>${esc(member.email)}</dd></div><div><dt>Ban đăng ký</dt><dd>${esc(member.team)}</dd></div></dl><div class="toolbar"><button class="btn btn-primary" data-member-action="approve" data-member-id="${esc(member.id)}">${icon('check')} Duyệt</button><button class="btn btn-danger" data-member-action="reject" data-member-id="${esc(member.id)}">${icon('close')} Từ chối</button><button class="btn btn-ghost" data-member-action="email" data-member-id="${esc(member.id)}">${icon('mail')} Xem email thông báo</button></div></div></article>`).join('')}</div>` : `<div class="card empty-state">${icon('check')}<strong>Không còn đơn chờ duyệt</strong><span class="muted">Các cập nhật chỉ tồn tại trong phiên xem trước này.</span></div>`}
      </div>`;
    },
    bind(root) {
      root.querySelectorAll('[data-nav]').forEach((button) => button.addEventListener('click', () => navigate(button.dataset.nav)));
      root.querySelectorAll('[data-member-action]').forEach((button) => button.addEventListener('click', () => {
        const member = approvalState.find((item) => item.id === button.dataset.memberId);
        if (!member) return;
        const action = button.dataset.memberAction;
        if (action === 'email') {
          modal({ title: 'Xem trước email thông báo', body: `<div class="page-stack">${badge('Chỉ là bản nháp', 'warning')}<p><strong>Đến:</strong> ${esc(member.email)}</p><p><strong>Tiêu đề:</strong> Kết quả đăng ký thành viên FIA</p><p>Chào ${esc(member.name)},<br><br>Ban Điều hành đã xem xét thông tin đăng ký của bạn. Bản xem trước này không được gửi.</p></div>`, footer: `<button type="button" class="btn btn-secondary" data-modal-close>Đóng</button><button type="button" class="btn btn-primary" data-modal-reviewed>Đã xem</button>`, onMount(dialog) { dialog.querySelector('[data-modal-close]')?.addEventListener('click', closeModal); dialog.querySelector('[data-modal-reviewed]')?.addEventListener('click', () => closeAndToast('Đã xem email mẫu. Không gửi thư thật.')); } });
          return;
        }
        const approve = action === 'approve';
        confirmModal({ title: approve ? `Duyệt ${member.name}?` : `Từ chối ${member.name}?`, body: `${approve ? 'Xác nhận demo rằng BĐH chấp nhận đơn đăng ký của' : 'Xác nhận demo rằng BĐH từ chối đơn đăng ký của'} <strong>${esc(member.name)}</strong>, MSSV ${esc(member.studentId)}.`, confirmLabel: approve ? 'BĐH xác nhận duyệt' : 'BĐH xác nhận từ chối', tone: approve ? 'primary' : 'danger' }, () => {
          member.status = approve ? 'approved' : 'rejected';
          toast(approve ? 'Đã ghi nhận quyết định duyệt mẫu.' : 'Đã ghi nhận quyết định từ chối mẫu.');
          repaint(root, approvalScreen);
        });
      }));
    }
  };

  const roleState = {
    currentUserId: 'r-1',
    currentUserRole: 'Chủ nhiệm',
    transferCompleted: false,
    members: [
      { id: 'r-1', name: 'Nguyễn Minh An', initials: 'NA', studentId: '22110018', team: 'Ban Chủ nhiệm', role: 'Chủ nhiệm' },
      { id: 'r-2', name: 'Trần Gia Huy', initials: 'GH', studentId: '22110024', team: 'Hậu cần', role: 'Trưởng ban' },
      { id: 'r-3', name: 'Lê Hoàng Yến', initials: 'HY', studentId: '22110037', team: 'Truyền thông', role: 'Trưởng ban' },
      { id: 'r-4', name: 'Đỗ Ngọc Mai', initials: 'ĐM', studentId: '22110418', team: 'Truyền thông', role: 'Thành viên' },
      { id: 'r-5', name: 'Phạm Quốc Bảo', initials: 'PB', studentId: '22110563', team: 'Hậu cần', role: 'Thư ký / Thủ quỹ' },
      { id: 'r-6', name: 'Vũ Thanh Trúc', initials: 'VT', studentId: '22110730', team: 'Nội dung', role: 'Thành viên' }
    ]
  };
  const roleChoices = [['Thành viên', 'Thành viên'], ['Thư ký / Thủ quỹ', 'Thư ký / Thủ quỹ'], ['Trưởng ban', 'Trưởng ban'], ['Phó Chủ nhiệm', 'Phó Chủ nhiệm'], ['Chủ nhiệm', 'Chủ nhiệm']];
  const roleRank = { 'Thành viên': 0, 'Thư ký / Thủ quỹ': 1, 'Trưởng ban': 2, 'Phó Chủ nhiệm': 3, 'Chủ nhiệm': 4 };
  const rolesScreen = {
    title: 'Quản lý chức vụ BDH',
    subtitle: 'Phân quyền vai trò và xem trước việc chuyển giao chức vụ.',
    render() {
      return `<div class="page-stack">
        ${pageHeading('BAN ĐIỀU HÀNH · PHÂN QUYỀN', 'Quản lý chức vụ', 'Vai trò mẫu được giới hạn theo cơ cấu CLB. Thay đổi tại trang này chỉ lưu trong trình duyệt.', `<button class="btn btn-secondary" data-transfer-role ${roleState.transferCompleted || roleState.currentUserRole === 'Thành viên' ? 'disabled' : ''}>${icon('arrow')} ${roleState.transferCompleted ? 'Đã chuyển giao' : roleState.currentUserRole === 'Thành viên' ? 'Không có chức vụ để chuyển' : 'Nhượng chức vụ'}</button>`)}
        <div class="card card-body preview-role-guidance"><div class="row">${icon('shield')}<div><strong>Giới hạn vai trò</strong><p class="muted small">Chủ nhiệm tối đa 1 · Phó Chủ nhiệm tối đa 2 · Trưởng ban tối đa 3 · Thư ký / Thủ quỹ tối đa 1. Chỉ người có quyền cao hơn mới được chỉ định xuống.</p></div></div></div>
        <section class="card"><div class="card-header"><div><h2>Thành viên & chức vụ</h2><p class="small muted">${roleState.members.length} thành viên trong dữ liệu mẫu</p></div><label class="field"><span class="field-label">Tìm thành viên</span><input class="input" id="role-search" type="search" placeholder="Tên hoặc MSSV"></label></div>
          <div class="table-wrap"><table class="data-table"><thead><tr><th>Thành viên</th><th>MSSV</th><th>Ban quản lý</th><th>Chức vụ hiện tại</th><th></th></tr></thead><tbody>${roleState.members.map((member) => `<tr data-role-row data-filter-text="${esc(`${member.name} ${member.studentId} ${member.team} ${member.role}`.toLowerCase())}"><td><div class="row">${avatar(member.initials)}<strong>${esc(member.name)}</strong>${member.id === roleState.currentUserId ? badge('Bạn', 'indigo') : ''}</div></td><td>${esc(member.studentId)}</td><td>${esc(member.team)}</td><td>${badge(member.role, member.role === 'Thành viên' ? 'neutral' : 'indigo')}</td><td><button class="btn btn-secondary btn-sm" data-assign-role="${esc(member.id)}">${icon('edit')} Gán chức vụ</button></td></tr>`).join('')}</tbody></table></div>
        </section><p class="small muted">${icon('shield')} Không thay đổi tài khoản, phân quyền hoặc dữ liệu thật.</p>
      </div>`;
    },
    bind(root) {
      root.querySelector('#role-search')?.addEventListener('input', (event) => {
        const query = event.currentTarget.value.trim().toLowerCase();
        root.querySelectorAll('[data-role-row]').forEach((row) => { row.hidden = !row.dataset.filterText.includes(query); });
      });
      root.querySelectorAll('[data-assign-role]').forEach((button) => button.addEventListener('click', () => {
        const member = roleState.members.find((item) => item.id === button.dataset.assignRole);
        if (!member) return;
        modal({ title: `Gán chức vụ · ${member.name}`, body: `<p class="muted">Chỉ cập nhật bảng minh họa trong trình duyệt.</p><form id="role-form" class="page-stack">${field('Thành viên', `<div class="input">${esc(member.name)} · ${esc(member.studentId)}</div>`)}${field('Chức vụ mới', select('role', roleChoices, '', member.role))}${field('Ban quản lý (nếu là Trưởng ban)', select('team', [['Ban Chủ nhiệm', 'Ban Chủ nhiệm'], ['Hậu cần', 'Hậu cần'], ['Truyền thông', 'Truyền thông'], ['Nội dung', 'Nội dung']], '', member.team))}</form>`, footer: `<button type="button" class="btn btn-secondary" data-modal-close>Hủy</button><button type="submit" form="role-form" class="btn btn-primary">Lưu vai trò demo</button>`, onMount(dialog) { dialog.querySelector('[data-modal-close]')?.addEventListener('click', closeModal); dialog.querySelector('#role-form')?.addEventListener('submit', (event) => { event.preventDefault(); const values = Object.fromEntries(new FormData(event.currentTarget).entries()); const teamChanged = values.role === 'Trưởng ban' && values.team !== member.team; if (values.role === member.role && !teamChanged) { closeModal(); toast('Chức vụ hiện tại đã được giữ nguyên.'); return; } member.role = values.role; if (values.role === 'Trưởng ban') member.team = values.team; if (member.id === roleState.currentUserId) { roleState.currentUserRole = values.role; profileState.role = values.role; } closeAndToast('Đã cập nhật chức vụ trong dữ liệu mẫu.'); repaint(root, rolesScreen); }); } });
      }));
      root.querySelector('[data-transfer-role]')?.addEventListener('click', () => {
        if (roleState.transferCompleted || roleState.currentUserRole === 'Thành viên') return;
        const actorRank = roleRank[roleState.currentUserRole] ?? -1;
        const options = roleState.members.filter((member) => member.id !== roleState.currentUserId && (roleRank[member.role] ?? -1) < actorRank).map((member) => [member.id, `${member.name} · ${member.studentId}`]);
        if (!options.length) { toast('Chưa có thành viên đủ điều kiện nhận chức vụ trong dữ liệu mẫu.'); return; }
        modal({ title: `Nhượng chức vụ ${roleState.currentUserRole}`, body: `<p>Chọn thành viên có chức vụ thấp hơn để tiếp nhận. Bước xác nhận sẽ hạ vai trò hiện tại của bạn xuống Thành viên trong dữ liệu mẫu.</p><form id="transfer-form">${field('Người tiếp nhận', select('memberId', options, 'required'))}</form><p class="small muted">Đây là bước xác nhận quan trọng và chỉ mô phỏng thao tác BĐH.</p>`, footer: `<button type="button" class="btn btn-secondary" data-modal-close>Hủy</button><button type="submit" form="transfer-form" class="btn btn-danger">Xác nhận chuyển giao demo</button>`, onMount(dialog) { dialog.querySelector('[data-modal-close]')?.addEventListener('click', closeModal); dialog.querySelector('#transfer-form')?.addEventListener('submit', (event) => { event.preventDefault(); if (roleState.transferCompleted || roleState.currentUserRole === 'Thành viên') { closeModal(); toast('Chức vụ đã được chuyển giao trong bản demo.'); repaint(root, rolesScreen); return; } const recipient = roleState.members.find((member) => member.id === new FormData(event.currentTarget).get('memberId')); const actorRankNow = roleRank[roleState.currentUserRole] ?? -1; if (!recipient || recipient.id === roleState.currentUserId || (roleRank[recipient.role] ?? -1) >= actorRankNow) { toast('Chọn một thành viên đủ điều kiện nhận chức vụ.'); return; } const outgoing = roleState.members.find((member) => member.id === roleState.currentUserId); if (!outgoing) { toast('Không tìm thấy người đang chuyển giao trong dữ liệu mẫu.'); return; } const formerRole = roleState.currentUserRole; recipient.role = formerRole; outgoing.role = 'Thành viên'; roleState.currentUserRole = 'Thành viên'; roleState.transferCompleted = true; profileState.role = 'Thành viên'; closeAndToast(`Đã chuyển ${formerRole} cho ${recipient.name} trong dữ liệu mẫu.`); repaint(root, rolesScreen); }); } });
      });
    }
  };

  const profileState = {
    name: 'Nguyễn Minh An', studentId: '22110018', role: 'Chủ nhiệm', team: 'Ban Chủ nhiệm',
    phone: '0901 234 567', email: 'minhanh@example.test', facebook: 'https://facebook.com/pwd301.demo', skills: 'Điều phối, truyền thông, viết nội dung', maxTasks: 3, unavailableUntil: ''
  };
  const profileScreen = {
    title: 'Hồ sơ cá nhân',
    subtitle: 'Cập nhật thông tin liên hệ và khả năng nhận task trong dữ liệu xem trước.',
    render() {
      const initials = profileState.name.split(/\s+/).slice(-2).map((part) => part[0]).join('');
      return `<div class="page-stack">
        <section class="card profile-cover"><div class="profile-cover-art"></div><div class="profile-cover-content">${avatar(initials, 'indigo')}<div class="grow"><p class="eyebrow">THÀNH VIÊN CLB</p><h1>${esc(profileState.name)}</h1><p class="muted">MSSV ${esc(profileState.studentId)} · ${esc(profileState.role)} · ${esc(profileState.team)}</p></div>${badge('Đang hoạt động', 'success')}</div></section>
        <div class="grid-12"><section class="span-7 card"><div class="card-header"><div><h2>Thông tin liên hệ</h2><p class="small muted">Các thay đổi chỉ giữ trong phiên xem trước.</p></div>${icon('edit')}</div><div class="card-body"><form id="profile-form" class="page-stack">
          <div class="form-grid">${field('Họ và tên', input('name', `type="text" maxlength="120" required value="${esc(profileState.name)}"`))}${field('MSSV', `<input class="input" value="${esc(profileState.studentId)}" disabled>`)}
          ${field('Số điện thoại', input('phone', `type="tel" maxlength="20" required value="${esc(profileState.phone)}"`))}${field('Email', input('email', `type="email" maxlength="180" required value="${esc(profileState.email)}"`))}</div>
          ${field('Facebook', input('facebook', `type="url" maxlength="300" value="${esc(profileState.facebook)}" placeholder="https://facebook.com/…"`))}
          <div class="toolbar"><button class="btn btn-primary" type="submit">${icon('check')} Lưu hồ sơ demo</button><span class="small muted">Không tải ảnh hoặc cập nhật tài khoản thật.</span></div>
        </form></div></section>
        <section class="span-5 card"><div class="card-header"><div><h2>Khả năng nhận task</h2><p class="small muted">Thông tin dùng cho bản xem trước đề xuất AI.</p></div>${icon('sparkles')}</div><div class="card-body"><form id="preferences-form" class="page-stack">${field('Kỹ năng (phân cách bằng dấu phẩy)', `<textarea class="textarea" name="skills" rows="3" maxlength="320">${esc(profileState.skills)}</textarea>`)}${field('Số task đang làm tối đa', input('maxTasks', `type="number" min="1" max="10" required value="${esc(profileState.maxTasks)}"`))}${field('Tạm không nhận task đến ngày', input('unavailableUntil', `type="date" value="${esc(profileState.unavailableUntil)}"`))}<button class="btn btn-secondary" type="submit">Lưu tùy chọn demo</button></form></div></section>
        <section class="span-6 card"><div class="card-header"><div><h2>Hoạt động theo ban / kỳ</h2><p class="small muted">Tổng quan dữ liệu mẫu</p></div>${icon('calendar')}</div><div class="table-wrap"><table class="data-table"><thead><tr><th>Kỳ</th><th>Ban</th><th>Task hoàn thành / tổng</th><th>Đánh giá</th></tr></thead><tbody><tr><td>Thu 2026</td><td>Truyền thông</td><td>8 / 10</td><td>${badge('Tốt', 'success')}</td></tr><tr><td>Hè 2026</td><td>Ban Chủ nhiệm</td><td>6 / 7</td><td>${badge('Rất tốt', 'indigo')}</td></tr></tbody></table></div></section>
        <section class="span-6 card"><div class="card-header"><div><h2>Tình trạng đóng quỹ</h2><p class="small muted">Các kỳ gần đây</p></div>${icon('wallet')}</div><div class="table-wrap"><table class="data-table"><thead><tr><th>Kỳ</th><th>Trạng thái</th><th>Ngày</th></tr></thead><tbody><tr><td>Thu 2026</td><td>${badge('Đã đóng', 'success')}</td><td>10/10/2026</td></tr><tr><td>Hè 2026</td><td>${badge('Đã đóng', 'success')}</td><td>19/07/2026</td></tr></tbody></table></div></section></div>
        <p class="small muted">${icon('shield')} Không tải tệp, gửi thông tin hoặc ghi thay đổi lên hệ thống.</p>
      </div>`;
    },
    bind(root) {
      const profileNameField = root.querySelector('#profile-form [name="name"]');
      profileNameField?.addEventListener('input', (event) => {
        const nameField = event.currentTarget;
        nameField.setCustomValidity(nameField.value.trim() ? '' : 'Họ và tên không được để trống.');
      });
      root.querySelector('#profile-form')?.addEventListener('submit', (event) => {
        event.preventDefault();
        const form = event.currentTarget;
        const nameField = form.querySelector('[name="name"]');
        nameField.setCustomValidity(nameField.value.trim() ? '' : 'Họ và tên không được để trống.');
        if (!form.reportValidity()) return;
        const values = Object.fromEntries(new FormData(form).entries());
        profileState.name = values.name.trim(); profileState.phone = values.phone.trim(); profileState.email = values.email.trim(); profileState.facebook = values.facebook.trim();
        toast('Đã cập nhật hồ sơ trong bản xem trước.');
        repaint(root, profileScreen);
      });
      root.querySelector('#preferences-form')?.addEventListener('submit', (event) => {
        event.preventDefault();
        const form = event.currentTarget;
        if (!form.reportValidity()) return;
        const values = Object.fromEntries(new FormData(form).entries());
        profileState.skills = values.skills.trim(); profileState.maxTasks = Number(values.maxTasks); profileState.unavailableUntil = values.unavailableUntil;
        toast('Đã lưu tùy chọn nhận task mẫu.');
        repaint(root, profileScreen);
      });
    }
  };

  const loginScreen = {
    title: 'Đăng nhập thành viên',
    subtitle: 'Màn hình đăng nhập mẫu, không xác thực tài khoản.',
    render() {
      return `<div class="auth-layout preview-auth"><section class="auth-art"><div class="auth-art-mark">${icon('sparkles')}</div><p class="eyebrow">FIA · CỘNG ĐỒNG</p><h1>Kết nối để cùng tạo điều ý nghĩa.</h1><p>Một góc nhìn tổng quan về thành viên, hoạt động và những dự án đang diễn ra.</p><div class="auth-art-stats"><div><strong>120+</strong><span>Thành viên</span></div><div><strong>18</strong><span>Hoạt động</span></div></div></section><section class="auth-card card"><div class="card-body"><p class="eyebrow">CHÀO MỪNG TRỞ LẠI</p><h1>Đăng nhập</h1><p class="muted">Dùng thông tin mẫu bất kỳ để xem luồng giao diện.</p>${badge('Demo · không có xác thực', 'warning')}<form id="login-form" class="page-stack">${field('MSSV', input('studentId', 'type="text" autocomplete="username" required placeholder="Ví dụ: 22110018"'))}${field('Mật khẩu', input('password', 'type="password" autocomplete="current-password" required minlength="6" placeholder="Nhập mật khẩu mẫu"'))}${field('Vai trò xem thử', select('demoRole', [['member', 'Thành viên (mặc định)'], ['board', 'BDH — chỉ xem thiết kế mẫu']]))}<div class="row"><span class="small muted">Phiên demo chỉ dùng trong tab hiện tại.</span><a href="#" data-forgot-password>Quên mật khẩu?</a></div><button class="btn btn-primary" type="submit">Đăng nhập ${icon('arrow')}</button></form><p class="muted">Chưa có tài khoản? <button class="btn btn-ghost btn-sm" data-nav="register">Đăng ký thành viên mới</button></p><p class="small muted">Thông tin không được gửi hoặc lưu lại.</p></div></section></div>`;
    },
    bind(root) {
      root.querySelector('#login-form')?.addEventListener('submit', (event) => {
        event.preventDefault();
        if (!event.currentTarget.reportValidity()) return;
        const data = new FormData(event.currentTarget);
        const code = String(data.get('studentId') || '').trim();
        if (!code) {toast('Hãy nhập MSSV mẫu hợp lệ.');return;}
        const role = data.get('demoRole') === 'board' ? 'board' : 'member';
        PreviewSession.signIn({role,code,name:role === 'board' ? 'Nguyễn Minh An' : 'Thành viên FIA'});
        const destination = PreviewSession.takeNext();
        toast(role === 'board' ? 'Đang xem giao diện BDH mẫu — không phải quyền admin thật.' : 'Đã mở phiên thành viên mô phỏng.');
        navigate(PreviewSession.canVisit(destination) ? destination : 'dashboard');
      });
      root.querySelector('[data-nav="register"]')?.addEventListener('click', () => navigate('register'));
      root.querySelector('[data-forgot-password]')?.addEventListener('click', (event) => { event.preventDefault(); toast('Luồng khôi phục tài khoản chưa có trong bản xem trước.'); });
    }
  };

  const registerScreen = {
    title: 'Đăng ký thành viên mới',
    subtitle: 'Biểu mẫu dùng kiểm tra ràng buộc HTML và chuyển đến trạng thái chờ duyệt demo.',
    render() {
      return `<div class="auth-layout preview-auth preview-register"><section class="auth-art"><div class="auth-art-mark">${icon('users')}</div><p class="eyebrow">THAM GIA FIA</p><h1>Góp sức trong một đội ngũ nhiều màu sắc.</h1><p>Điền biểu mẫu mẫu để xem bước gửi đăng ký và trạng thái chờ duyệt.</p><div class="auth-art-quote">“Cùng học hỏi, cùng làm nên những dự án có ích.”</div></section><section class="auth-card card"><div class="card-body"><p class="eyebrow">TẠO TÀI KHOẢN</p><h1>Đăng ký thành viên</h1><p class="muted">Các trường bắt buộc được kiểm tra trên trình duyệt.</p>${badge('Demo · không tạo tài khoản thật', 'warning')}<form id="register-form" class="page-stack"><div class="form-grid">${field('Họ và tên', input('name', 'type="text" required maxlength="120" autocomplete="name" placeholder="Nguyễn Văn A"'))}${field('MSSV', input('studentId', 'type="text" required maxlength="20" autocomplete="username" placeholder="22110018"'))}${field('Ngày sinh', input('birthDate', 'type="date" required autocomplete="bday"'))}${field('Số điện thoại', input('phone', 'type="tel" required maxlength="20" autocomplete="tel" placeholder="09xx xxx xxx"'))}${field('Email', input('email', 'type="email" required maxlength="180" autocomplete="email" placeholder="ban@example.com"'))}${field('Facebook', input('facebook', 'type="url" required maxlength="300" placeholder="https://facebook.com/…"'))}</div>${field('Ban hoạt động', select('teams', [['media', 'Truyền thông'], ['hr', 'Nhân sự'], ['tech', 'Kỹ thuật']], 'multiple required size="3"'))}<p class="small muted">Giữ Ctrl (Windows) hoặc Command (Mac) để chọn nhiều ban.</p>${field('Mật khẩu', input('password', 'type="password" required minlength="8" autocomplete="new-password" placeholder="Tối thiểu 8 ký tự"'))}<label class="checkbox"><input type="checkbox" name="terms" required> <span>Tôi xác nhận thông tin đăng ký là chính xác.</span></label><button class="btn btn-primary" type="submit">Gửi đăng ký demo ${icon('arrow')}</button></form><p class="muted">Đã có tài khoản? <button class="btn btn-ghost btn-sm" data-nav="login">Đăng nhập</button></p><p class="small muted">Thông tin chỉ được đọc để kiểm tra form trong trình duyệt.</p></div></section></div>`;
    },
    bind(root) {
      root.querySelector('#register-form')?.addEventListener('submit', (event) => {
        event.preventDefault();
        if (!event.currentTarget.reportValidity()) return;
        toast('Đã gửi đăng ký mẫu.');
        navigate('pending');
      });
      root.querySelector('[data-nav="login"]')?.addEventListener('click', () => navigate('login'));
    }
  };

  const pendingScreen = {
    title: 'Tài khoản chờ xét duyệt',
    subtitle: 'Trạng thái mẫu sau khi gửi biểu mẫu đăng ký.',
    render() {
      return `<div class="auth-layout preview-auth"><section class="auth-art"><div class="auth-art-mark">${icon('clock')}</div><p class="eyebrow">BƯỚC TIẾP THEO</p><h1>Ban Điều hành sẽ xem xét thông tin của bạn.</h1><p>Trạng thái mẫu giúp minh họa những gì thành viên nhìn thấy sau khi đăng ký.</p></section><section class="auth-card card"><div class="card-body page-stack"><div class="preview-pending-icon">${icon('clock')}</div><p class="eyebrow">HỒ SƠ · FIA</p><h1>Tài khoản đang chờ xét duyệt</h1><p class="muted">Cảm ơn bạn đã đăng ký. Ban Điều hành sẽ xem xét thông tin của bạn trong thời gian sớm nhất.</p><div class="card card-body preview-timeline"><div class="list-item">${badge('Đã nhận', 'success')}<span>Đơn đăng ký mẫu đã gửi</span><span class="small muted">Hôm nay</span></div><div class="list-item">${badge('Đang chờ', 'warning')}<span>Ban Điều hành xem xét</span></div><div class="list-item">${badge('Tiếp theo', 'neutral')}<span>Thông báo kết quả</span></div></div><div class="row"><button class="btn btn-secondary" data-nav="login">${icon('logout')} Đăng xuất demo</button><button class="btn btn-ghost" data-nav="profile">Xem hồ sơ mẫu</button></div><p class="small muted">Không có hồ sơ được tạo và không gửi thông báo.</p></div></section></div>`;
    },
    bind(root) {
      root.querySelectorAll('[data-nav]').forEach((button) => button.addEventListener('click', () => {
        if (button.dataset.nav === 'login') {PreviewSession.signOut();closeModal();}
        navigate(button.dataset.nav);
      }));
    }
  };

  const checkinState = { confirmed: false };
  const qrPattern = [
    '1111111001011', '1000001010101', '1011101011101', '1011101000011', '1011101011011', '1000001010001', '1111111010101',
    '0000000011110', '1101011100101', '0100110011010', '1110101110101', '1001010001100', '1011101110111'
  ];
  const checkinScreen = {
    title: 'Điểm danh sự kiện',
    subtitle: 'Xem thông tin sự kiện và xác nhận điểm danh mẫu.',
    render() {
      return `<div class="page-stack">
        ${pageHeading('SỰ KIỆN · CHECK-IN', 'Xác nhận điểm danh', 'Đối chiếu thông tin trước khi ghi nhận. Mã QR bên dưới chỉ là hình minh họa, không thể quét.')}
        <div class="grid-12"><section class="span-7 card"><div class="card-header"><div><p class="eyebrow">THỨ TƯ · 28 THÁNG 10, 2026</p><h2>FIA · Workshop An toàn thông tin</h2><p class="muted">Buổi chia sẻ kỹ năng bảo mật cơ bản và nhận diện rủi ro trên mạng.</p></div>${badge(checkinState.confirmed ? 'Đã xác nhận demo' : 'Đang diễn ra', checkinState.confirmed ? 'success' : 'warning')}</div><div class="card-body"><div class="grid-12 preview-event-details"><div class="span-6 list-item">${icon('clock')}<span><strong>18:30 – 20:30</strong><span class="small muted">Thời gian</span></span></div><div class="span-6 list-item">${icon('location')}<span><strong>Phòng A2.04</strong><span class="small muted">Tòa nhà A</span></span></div><div class="span-6 list-item">${avatar('NA')}<span><strong>Nguyễn Minh An</strong><span class="small muted">MSSV 22110018</span></span></div><div class="span-6 list-item">${icon('users')}<span><strong>Thành viên FIA</strong><span class="small muted">Người tham dự</span></span></div></div><div class="preview-checkin-summary"><div><p class="eyebrow">MÃ XÁC NHẬN</p><strong>DEMO-28OCT-018</strong><p class="small muted">Chỉ dùng để xem bố cục</p></div><div class="preview-qr-grid" aria-label="Mã QR minh họa, không thể quét">${qrPattern.join('').split('').map((bit) => `<span class="${bit === '1' ? 'filled' : ''}"></span>`).join('')}</div></div><button class="btn btn-primary" data-checkin-confirm ${checkinState.confirmed ? 'disabled' : ''}>${icon('check')} ${checkinState.confirmed ? 'Đã xác nhận mẫu' : 'Xác nhận điểm danh demo'}</button><p class="small muted">${icon('shield')} Không gửi vị trí, không dùng camera và không ghi nhận check-in thật.</p></div></section>
        <aside class="span-5 card"><div class="card-header"><div><h2>Trước khi xác nhận</h2><p class="small muted">Kiểm tra ba thông tin sau.</p></div>${icon('check')}</div><div class="card-body page-stack"><div class="list-item">${badge('01', 'indigo')}<span><strong>Đúng sự kiện</strong><span class="small muted">An toàn thông tin · 28/10</span></span></div><div class="list-item">${badge('02', 'indigo')}<span><strong>Đúng tài khoản</strong><span class="small muted">Nguyễn Minh An · 22110018</span></span></div><div class="list-item">${badge('03', 'indigo')}<span><strong>Đang trong thời gian</strong><span class="small muted">18:30 – 20:30</span></span></div><div class="card card-body"><strong>Trạng thái ghi nhận</strong><p class="muted small">${checkinState.confirmed ? 'Đã xác nhận trong dữ liệu demo của phiên hiện tại.' : 'Chưa xác nhận. Nhấn nút màu tím để xem hộp thoại xác nhận.'}</p></div></div></aside></div>
      </div>`;
    },
    bind(root) {
      root.querySelector('[data-checkin-confirm]')?.addEventListener('click', () => {
        if (checkinState.confirmed) return;
        confirmModal({ title: 'Xác nhận điểm danh?', body: 'Bạn xác nhận tham dự <strong>FIA · Workshop An toàn thông tin</strong> bằng tài khoản mẫu Nguyễn Minh An. Hệ thống demo sẽ không ghi nhận dữ liệu thật.', confirmLabel: 'Xác nhận demo' }, () => {
          checkinState.confirmed = true;
          toast('Đã xác nhận điểm danh trong bản xem trước.');
          repaint(root, checkinScreen);
        });
      });
    }
  };

  window.previewScreens = window.previewScreens || {};
  Object.assign(window.previewScreens, {
    funds: fundsScreen,
    ai: aiScreen,
    approvals: approvalScreen,
    roles: rolesScreen,
    profile: profileScreen,
    login: loginScreen,
    register: registerScreen,
    pending: pendingScreen,
    checkin: checkinScreen
  });
})();
