(() => {
  "use strict";

  const UI = window.UI;
  if (!UI) throw new Error("operations.js requires shared window.UI");

  const escapeHtml = (value) => String(value ?? "").replace(/[&<>"']/g, (char) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
  })[char]);
  const icon = (name) => UI.icon(name);
  const initials = (name) => String(name ?? "")
    .trim().split(/\s+/).slice(-2).map((part) => part[0] || "").join("").toUpperCase();
  const avatar = (name, tone = "indigo") => UI.avatar(initials(name), tone);
  const badge = (text, tone = "neutral") => UI.badge(text, tone);
  const memberStatusLabel = (status) => ({ active: "Đang hoạt động", pending: "Chờ duyệt", paused: "Tạm khóa" })[status] || status;
  const memberStatusTone = (status) => ({ active: "success", pending: "warning", paused: "danger" })[status] || "neutral";
  const eventStatusLabel = (status) => ({ upcoming: "Sắp diễn ra", live: "Đang diễn ra", ended: "Đã kết thúc" })[status] || status;
  const eventStatusTone = (status) => ({ upcoming: "indigo", live: "success", ended: "neutral" })[status] || "neutral";
  const taskStatusLabel = (status) => ({ dang_lam: "Đang làm", cho_duyet: "Chờ duyệt", lam_lai: "Cần làm lại", hoan_thanh: "Hoàn thành", huy: "Đã hủy" })[status] || status;
  const taskStatusTone = (status) => ({ dang_lam: "indigo", cho_duyet: "amber", lam_lai: "violet", hoan_thanh: "success", huy: "rose" })[status] || "neutral";
  const dateLabel = (value, options = { day: "2-digit", month: "2-digit", year: "numeric" }) => {
    const date = value instanceof Date ? value : new Date(value);
    return Number.isNaN(date.getTime()) ? "Chưa cập nhật" : new Intl.DateTimeFormat("vi-VN", options).format(date);
  };
  const dateTimeLabel = (value) => dateLabel(value, { day: "2-digit", month: "2-digit", hour: "2-digit", minute: "2-digit" });
  const eventDateTime = (day, hour, minute = "00") => `2026-10-${String(day).padStart(2, "0")}T${hour}:${minute}:00`;
  const dateTimeInput = (value) => {
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return "";
    const local = new Date(date.getTime() - date.getTimezoneOffset() * 60000);
    return local.toISOString().slice(0, 16);
  };
  const refresh = (root, key) => {
    const screen = window.previewScreens[key];
    if (!screen || !root) return;
    root.innerHTML = screen.render();
    screen.bind(root);
  };
  const closeModal = (dialog) => {
    if (dialog?.querySelector("[data-modal-cancel]")) dialog.querySelector("[data-modal-cancel]").addEventListener("click", UI.closeModal);
  };
  const label = (text, html) => `<label class="field"><span class="field-label">${escapeHtml(text)}</span>${html}</label>`;
  const viewStyles = () => `<style>
    .ops-preview .hero { position:relative; overflow:hidden; min-height:230px; padding:30px 34px; }
    .ops-preview .hero-copy { position:relative; z-index:1; max-width:690px; }
    .ops-preview .hero-copy h2 { margin:12px 0 8px; font-size:clamp(24px,3vw,34px); letter-spacing:-.035em; }
    .ops-preview .hero-art { position:absolute; right:5%; top:10px; width:210px; height:210px; border-radius:50%; display:grid; place-items:center; color:#fff; background:radial-gradient(circle at 35% 30%,#9698ff 0,#7476ed 35%,#484bc4 72%); box-shadow:0 24px 60px #5457cb38; }
    .ops-preview .hero-art-orbit { position:absolute; inset:19px -12px 21px 17px; border:1px solid #ffffff6e; border-radius:50%; transform:rotate(-24deg); }
    .ops-preview .hero-art-orbit::before,.ops-preview .hero-art-orbit::after { content:""; position:absolute; width:12px; height:12px; border-radius:50%; background:#ffb45f; box-shadow:0 0 0 7px #ffb45f30; }
    .ops-preview .hero-art-orbit::before { left:16px; top:33px; }.ops-preview .hero-art-orbit::after { right:28px; bottom:15px; width:7px; height:7px; background:#fff; box-shadow:none; }
    .ops-preview .hero-art-star { position:absolute; right:30px; top:31px; color:#ffd18c; font-size:22px; }.ops-preview .hero-art-dot { position:absolute; left:35px; bottom:34px; width:10px; height:10px; border-radius:50%; background:#b7bcff; }
    .ops-preview .hero-art-caption { text-align:center; font-size:25px; line-height:1.05; font-weight:750; letter-spacing:.08em; }.ops-preview .hero-art-caption span { font-size:13px; font-weight:500; opacity:.8; letter-spacing:.25em; }
    .ops-preview .chart-legend { display:flex; align-items:center; gap:8px; margin-bottom:6px; font-size:13px; }.ops-preview .chart-legend-dot { width:9px; height:9px; border-radius:50%; background:#5558d9; }
    .ops-preview .approval-list,.ops-preview .activity-list,.ops-preview .dashboard-events { display:flex; flex-direction:column; }.ops-preview .approval-item,.ops-preview .dashboard-event { width:100%; border:0; border-bottom:1px solid #eef0f5; background:transparent; text-align:left; color:inherit; cursor:pointer; padding:14px 2px; }.ops-preview .approval-item:last-child,.ops-preview .dashboard-event:last-child { border-bottom:0; }
    .ops-preview .approval-icon,.ops-preview .rsvp-symbol { display:grid; place-items:center; width:38px; height:38px; flex:0 0 38px; border-radius:12px; color:#5558d9; background:#efefff; }.ops-preview .approval-icon-orange { color:#c36b19; background:#fff3e5; }.ops-preview .approval-footnote { display:flex; align-items:center; gap:7px; margin-top:11px; padding:12px; border-radius:10px; color:#656a7d; background:#f7f7fb; font-size:12px; }.ops-preview .approval-pulse { width:7px; height:7px; border-radius:50%; background:#25a879; box-shadow:0 0 0 4px #25a8791c; }
    .ops-preview .event-date-chip { display:flex; flex:0 0 48px; flex-direction:column; align-items:center; justify-content:center; width:48px; height:52px; border-radius:12px; color:#4f52ca; background:#f0f0ff; }.ops-preview .event-date-chip strong { font-size:19px; line-height:1.05; }.ops-preview .event-date-chip span { margin-top:3px; font-size:10px; text-transform:uppercase; }
    .ops-preview .activity-item { align-items:flex-start; gap:12px; padding:13px 2px; }.ops-preview .activity-mark { display:grid; place-items:center; width:30px; height:30px; flex:0 0 30px; border-radius:10px; font-weight:700; }.ops-preview .activity-violet { color:#7652bc; background:#f2edff; }.ops-preview .activity-indigo { color:#5558d9; background:#efefff; }.ops-preview .activity-orange { color:#ca741b; background:#fff3e5; }
    .ops-preview .demo-note { display:flex; align-items:center; gap:8px; margin:0; }.ops-preview .members-toolbar-card .card-body { padding:17px 20px; }.ops-preview .member-filter-fields,.ops-preview .event-filter-fields { align-items:flex-end; flex-wrap:wrap; }.ops-preview .member-filter-fields .field,.ops-preview .event-filter-fields .field { min-width:170px; }.ops-preview .member-filter-fields .search-field,.ops-preview .event-filter-fields .search-field { min-width:245px; }
    .ops-preview .input-with-icon { position:relative; display:flex; align-items:center; }.ops-preview .input-with-icon > svg { position:absolute; left:11px; width:17px; height:17px; color:#9296a8; pointer-events:none; }.ops-preview .input-with-icon .input { padding-left:36px; }
    .ops-preview .member-cell { display:flex; align-items:center; gap:11px; min-width:200px; }.ops-preview .member-cell > span:last-child { display:flex; flex-direction:column; gap:3px; }.ops-preview .member-id { color:#676b7c; font-variant-numeric:tabular-nums; }.ops-preview .count-label { display:inline-grid; place-items:center; min-width:23px; height:23px; margin-left:5px; border-radius:8px; color:#5c5fc8; background:#f0f0ff; font-size:12px; vertical-align:2px; }.ops-preview .table-foot { display:flex; justify-content:space-between; gap:12px; padding-top:13px; padding-bottom:13px; border-top:1px solid #eef0f5; }
    .ops-preview .events-heading { justify-content:space-between; align-items:end; margin:2px 0 15px; }.ops-preview .events-heading h3 { margin:5px 0 0; }.ops-preview .event-grid { display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:18px; }.ops-preview .event-tile { min-width:0; overflow:hidden; padding:0; border:1px solid #e9eaf1; border-radius:16px; color:inherit; background:#fff; text-align:left; cursor:pointer; box-shadow:0 5px 18px #20264a08; transition:transform .18s ease,box-shadow .18s ease,border-color .18s ease; }.ops-preview .event-tile:hover { transform:translateY(-2px); border-color:#c9caf5; box-shadow:0 14px 28px #20264a12; }
    .ops-preview .event-cover { position:relative; display:block; height:148px; overflow:hidden; padding:17px; color:#fff; }.ops-preview .cover-indigo { background:linear-gradient(125deg,#5558d9,#9495f5); }.ops-preview .cover-orange { background:linear-gradient(125deg,#d77c30,#f2bb78); }.ops-preview .cover-violet { background:linear-gradient(125deg,#724db6,#bd9be7); }.ops-preview .cover-teal { background:linear-gradient(125deg,#208c89,#80c8bf); }
    .ops-preview .event-cover::before,.ops-preview .event-cover::after { content:""; position:absolute; border:1px solid #ffffff48; border-radius:50%; }.ops-preview .event-cover::before { width:195px; height:195px; right:-33px; top:-65px; }.ops-preview .event-cover::after { width:134px; height:134px; right:43px; top:44px; }.ops-preview .event-cover-label,.ops-preview .event-cover-code { position:absolute; z-index:1; left:17px; font-size:11px; letter-spacing:.08em; text-transform:uppercase; }.ops-preview .event-cover-label { top:17px; opacity:.9; }.ops-preview .event-cover-code { bottom:17px; opacity:.8; }.ops-preview .event-cover-mark { position:absolute; top:47px; right:54px; z-index:1; display:grid; place-items:center; width:64px; height:64px; border:1px solid #ffffff70; border-radius:20px; background:#ffffff20; transform:rotate(8deg); }.ops-preview .event-cover-mark svg { width:32px; height:32px; }
    .ops-preview .event-tile-body { display:flex; flex-direction:column; gap:11px; padding:16px 18px 17px; }.ops-preview .event-tile-top { align-items:flex-start; justify-content:space-between; gap:10px; }.ops-preview .event-tile-top strong { font-size:16px; line-height:1.4; }.ops-preview .event-tile-meta,.ops-preview .event-attendee-count { display:flex; align-items:center; gap:7px; color:#73778a; font-size:12px; }.ops-preview .event-tile-meta svg,.ops-preview .event-attendee-count svg { width:15px; height:15px; }.ops-preview .event-tile-bottom { display:flex; align-items:center; justify-content:space-between; gap:16px; margin-top:2px; }.ops-preview .event-progress { width:85px; }.ops-preview .event-progress .progress-bar { height:5px; }.ops-preview .events-table-card { background:#fff; }.ops-preview .text-button { display:flex; flex-direction:column; gap:4px; padding:0; border:0; color:inherit; background:none; text-align:left; cursor:pointer; }
    .ops-preview .detail-back-toolbar { margin-bottom:-3px; }.ops-preview .event-detail-hero { position:relative; display:flex; align-items:center; min-height:225px; overflow:hidden; padding:30px 34px; border-radius:18px; color:#fff; }.ops-preview .event-detail-hero::after { content:""; position:absolute; width:350px; height:350px; right:3%; top:-67px; border:1px solid #ffffff40; border-radius:50%; box-shadow:0 0 0 34px #ffffff0c,0 0 0 70px #ffffff0b; }.ops-preview .event-detail-copy { position:relative; z-index:1; max-width:720px; }.ops-preview .event-detail-copy h2 { margin:10px 0 12px; font-size:clamp(25px,3.3vw,36px); letter-spacing:-.035em; }.ops-preview .event-detail-copy .eyebrow,.ops-preview .event-detail-copy .detail-meta-line { color:#ffffffd6; }.ops-preview .detail-meta-line { display:flex; align-items:center; flex-wrap:wrap; gap:8px; margin:0 0 17px; font-size:13px; }.ops-preview .detail-meta-line svg { width:16px; height:16px; }.ops-preview .event-detail-art { position:absolute; z-index:1; right:13%; top:50%; display:grid; place-items:center; width:94px; height:94px; border:1px solid #ffffff75; border-radius:28px; color:#fff; background:#ffffff22; transform:translateY(-50%) rotate(10deg); }.ops-preview .event-detail-art svg { width:48px; height:48px; }
    .ops-preview .rsvp-card .card-body { padding:16px 20px; }.ops-preview .rsvp-card .toolbar-left { gap:13px; }.ops-preview .rsvp-symbol { color:#19845f; background:#eaf8f2; }.ops-preview .rsvp-card p { margin:4px 0 0; }.ops-preview .tabs { display:flex; gap:5px; border-bottom:1px solid #e8e9f0; }.ops-preview .tabs button { display:flex; align-items:center; gap:8px; margin-bottom:-1px; padding:12px 14px; border:0; border-bottom:2px solid transparent; color:#73778a; background:transparent; cursor:pointer; }.ops-preview .tabs button.active { border-bottom-color:#5558d9; color:#4f52ca; }.ops-preview .tabs button svg { width:17px; height:17px; }.ops-preview .tabs button span { display:grid; place-items:center; min-width:20px; height:20px; border-radius:7px; background:#f1f1f6; font-size:11px; }.ops-preview .detail-panel { gap:17px; }.ops-preview .detail-stats .stat-card { min-height:100px; }.ops-preview .event-task-toolbar { margin-bottom:4px; }.ops-preview .event-task-toolbar h3,.ops-preview .event-task-toolbar p { margin:0; }.ops-preview .detail-task-card { padding:16px 18px; }.ops-preview .task-card-footer { justify-content:space-between; gap:10px; margin-top:14px; }.ops-preview .task-card-footer > span { display:flex; align-items:center; gap:6px; }.ops-preview .task-card-footer svg { width:15px; height:15px; }
    .ops-preview .task-summary-grid .stat-card { min-height:108px; }.ops-preview .task-toolbar { align-items:center; }.ops-preview .task-status-filters { flex-wrap:wrap; }.ops-preview .task-status-filters button { white-space:nowrap; }.ops-preview .task-status-filters button span { margin-left:3px; opacity:.7; }.ops-preview .task-board { display:grid; grid-template-columns:repeat(5,minmax(0,1fr)); gap:13px; align-items:start; }.ops-preview .task-column { min-width:0; padding:13px; border:1px solid #e9eaf1; border-radius:14px; background:#f8f8fb; }.ops-preview .task-column-header { display:flex; align-items:center; gap:8px; padding:2px 2px 12px; }.ops-preview .task-column-header strong { font-size:13px; }.ops-preview .task-column-count { display:grid; place-items:center; min-width:21px; height:21px; margin-left:auto; border-radius:7px; color:#676b7c; background:#fff; font-size:11px; }.ops-preview .task-column-dot { width:8px; height:8px; border-radius:50%; background:#a3a6b3; }.ops-preview .task-dot-dang_lam { background:#5558d9; }.ops-preview .task-dot-cho_duyet { background:#d59734; }.ops-preview .task-dot-lam_lai { background:#8561c5; }.ops-preview .task-dot-hoan_thanh { background:#31a67c; }.ops-preview .task-dot-huy { background:#d66b76; }.ops-preview .task-column-body { display:flex; flex-direction:column; gap:10px; }.ops-preview .task-column-empty { padding:15px 8px; border:1px dashed #d9dbe5; border-radius:10px; color:#9296a8; text-align:center; font-size:12px; }
    .ops-preview .task-card { min-width:0; padding:13px; border:1px solid #e7e8ef; border-radius:12px; background:#fff; box-shadow:0 3px 10px #20264a06; }.ops-preview .task-card-title { align-items:flex-start; gap:8px; }.ops-preview .task-card-title strong { font-size:13px; line-height:1.45; }.ops-preview .task-more { flex:0 0 auto; padding:3px; }.ops-preview .task-more svg { width:17px; height:17px; }.ops-preview .task-card > p { margin:6px 0 10px; font-size:11px; }.ops-preview .task-card-tags { display:flex; flex-wrap:wrap; gap:5px; }.ops-preview .task-card-tags .badge { font-size:10px; }.ops-preview .task-assignee { display:flex; align-items:center; gap:6px; min-width:0; }.ops-preview .task-assignee .avatar { width:25px; height:25px; flex:0 0 25px; font-size:9px; }.ops-preview .task-assignee .small { overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }.ops-preview .task-card-footer { font-size:10px; }.ops-preview .task-card-action { margin-top:9px; padding-top:8px; border-top:1px solid #f0f0f4; }.ops-preview .task-card-action .btn { padding:3px 0; font-size:11px; }.ops-preview .task-list { display:flex; flex-direction:column; gap:10px; }.ops-preview .task-card-compact { padding:15px 17px; }.ops-preview .task-view-container .task-list { max-width:900px; }
    .ops-preview .modal-intro { margin:0 0 16px; }.ops-preview .modal-form { display:flex; flex-direction:column; gap:13px; }.ops-preview .form-grid { gap:12px; }.ops-preview .form-hint { display:flex; align-items:center; gap:8px; padding:11px 12px; border-radius:10px; color:#74788a; background:#f7f7fb; font-size:11px; }
    @media (max-width:1000px) { .ops-preview .task-board { grid-template-columns:repeat(2,minmax(0,1fr)); }.ops-preview .event-grid { grid-template-columns:repeat(2,minmax(0,1fr)); }.ops-preview .hero-art { right:3%; width:165px; height:165px; } }
    @media (max-width:680px) { .ops-preview .hero { padding:24px 20px; }.ops-preview .hero-copy { max-width:100%; padding-right:35px; }.ops-preview .hero-art { right:-57px; top:64px; width:130px; height:130px; opacity:.35; }.ops-preview .hero-copy .toolbar { position:relative; z-index:2; }.ops-preview .event-grid,.ops-preview .task-board { grid-template-columns:1fr; }.ops-preview .task-status-filters { width:100%; }.ops-preview .task-toolbar { align-items:flex-start; flex-direction:column; gap:15px; }.ops-preview .task-toolbar .toolbar-right { width:100%; justify-content:space-between; }.ops-preview .member-filter-fields .field,.ops-preview .event-filter-fields .field,.ops-preview .member-filter-fields .search-field,.ops-preview .event-filter-fields .search-field { width:100%; }.ops-preview .table-foot { flex-direction:column; }.ops-preview .event-detail-hero { min-height:240px; padding:23px 20px; }.ops-preview .event-detail-art { right:8%; top:23%; width:68px; height:68px; opacity:.5; }.ops-preview .detail-meta-line { max-width:85%; }.ops-preview .event-tile-bottom { align-items:flex-start; flex-direction:column; gap:8px; } }
  </style>`;

  const members = [
    { id: "m01", name: "Nguyễn Minh Anh", studentId: "22124001", email: "minhanh.nguyen@sv.example.edu.vn", team: "Ban Nội dung", role: "Chủ nhiệm", status: "active", joined: "2025-08-18", tone: "indigo" },
    { id: "m02", name: "Trần Gia Huy", studentId: "22124018", email: "giahuy.tran@sv.example.edu.vn", team: "Ban Sự kiện", role: "Phó chủ nhiệm", status: "active", joined: "2025-08-22", tone: "blue" },
    { id: "m03", name: "Lê Thảo Vy", studentId: "23124007", email: "thaovy.le@sv.example.edu.vn", team: "Ban Đối ngoại", role: "Trưởng ban", status: "active", joined: "2025-09-04", tone: "violet" },
    { id: "m04", name: "Phạm Đức Long", studentId: "23124025", email: "duclong.pham@sv.example.edu.vn", team: "Ban Kỹ thuật", role: "Thành viên", status: "pending", joined: "2026-10-08", tone: "teal" },
    { id: "m05", name: "Võ Khánh Linh", studentId: "22124036", email: "khanhlinh.vo@sv.example.edu.vn", team: "Ban Truyền thông", role: "Thành viên", status: "active", joined: "2025-09-10", tone: "rose" },
    { id: "m06", name: "Đặng Hoàng Nam", studentId: "23124041", email: "hoangnam.dang@sv.example.edu.vn", team: "Ban Sự kiện", role: "Thành viên", status: "paused", joined: "2025-10-01", tone: "amber" },
    { id: "m07", name: "Bùi Ngọc Hà", studentId: "24124012", email: "ngocha.bui@sv.example.edu.vn", team: "Ban Nội dung", role: "Thành viên", status: "active", joined: "2026-09-16", tone: "blue" },
    { id: "m08", name: "Đỗ Quang Khải", studentId: "24124033", email: "quangkhai.do@sv.example.edu.vn", team: "Ban Kỹ thuật", role: "Thành viên", status: "pending", joined: "2026-10-10", tone: "teal" },
    { id: "m09", name: "Nguyễn Phương Thảo", studentId: "22124052", email: "phuongthao.nguyen@sv.example.edu.vn", team: "Ban Đối ngoại", role: "Thành viên", status: "active", joined: "2025-09-12", tone: "violet" }
  ];

  const events = [
    {
      id: "ev01", code: "CLB-026", name: "Ngày hội Chào Tân sinh viên FIA", category: "Sự kiện cộng đồng", status: "upcoming", start: eventDateTime(18, "08", "00"), end: eventDateTime(18, "16", "30"),
      location: "Sân trường · Đại học FPT", capacity: 180, registered: true, accent: "indigo", icon: "sparkles",
      registrations: [
        { name: "Nguyễn Minh Anh", team: "Nội dung", attended: true }, { name: "Trần Gia Huy", team: "Sự kiện", attended: true },
        { name: "Lê Thảo Vy", team: "Đối ngoại", attended: false }, { name: "Võ Khánh Linh", team: "Truyền thông", attended: false },
        { name: "Bùi Ngọc Hà", team: "Nội dung", attended: false }
      ]
    },
    {
      id: "ev02", code: "CLB-025", name: "Workshop: An toàn thông tin cá nhân", category: "Workshop", status: "upcoming", start: eventDateTime(22, "13", "30"), end: eventDateTime(22, "17", "00"),
      location: "Phòng Lab An ninh mạng · Đại học FPT", capacity: 80, registered: false, accent: "orange", icon: "sparkles",
      registrations: [
        { name: "Phạm Đức Long", team: "Kỹ thuật", attended: false }, { name: "Đỗ Quang Khải", team: "Kỹ thuật", attended: false },
        { name: "Đặng Hoàng Nam", team: "Sự kiện", attended: false }, { name: "Nguyễn Phương Thảo", team: "Đối ngoại", attended: false }
      ]
    },
    {
      id: "ev03", code: "CLB-024", name: "CTF FIA Welcome 2026", category: "Cuộc thi CTF", status: "live", start: eventDateTime(12, "18", "00"), end: eventDateTime(12, "21", "30"),
      location: "Lab An ninh mạng · Đại học FPT", capacity: 250, registered: false, accent: "violet", icon: "shield",
      registrations: [
        { name: "Nguyễn Minh Anh", team: "Nội dung", attended: true }, { name: "Trần Gia Huy", team: "Sự kiện", attended: true },
        { name: "Võ Khánh Linh", team: "Truyền thông", attended: true }, { name: "Bùi Ngọc Hà", team: "Nội dung", attended: true },
        { name: "Đỗ Quang Khải", team: "Kỹ thuật", attended: false }, { name: "Nguyễn Phương Thảo", team: "Đối ngoại", attended: true }
      ]
    },
    {
      id: "ev04", code: "CLB-023", name: "Sinh hoạt chuyên môn tháng 9", category: "Sinh hoạt CLB", status: "ended", start: "2026-09-20T09:00:00", end: "2026-09-20T11:00:00",
      location: "Phòng sinh hoạt CLB · Đại học FPT", capacity: 60, registered: false, accent: "teal", icon: "users",
      registrations: [
        { name: "Nguyễn Minh Anh", team: "Nội dung", attended: true }, { name: "Lê Thảo Vy", team: "Đối ngoại", attended: true },
        { name: "Đặng Hoàng Nam", team: "Sự kiện", attended: true }
      ]
    }
  ];

  const tasks = [
    { id: "t01", title: "Hoàn thiện kịch bản khai mạc", eventId: "ev01", team: "Nội dung", assignee: "Nguyễn Minh Anh", deadline: eventDateTime(15, "20", "00"), status: "cho_duyet", priority: "Cao", description: "Chốt lời dẫn, thứ tự nội dung và cue chuyển cảnh." },
    { id: "t02", title: "Thiết kế bộ nhận diện sự kiện", eventId: "ev01", team: "Truyền thông", assignee: "Võ Khánh Linh", deadline: eventDateTime(16, "18", "00"), status: "dang_lam", priority: "Cao", description: "Poster, story và khung ảnh check-in." },
    { id: "t03", title: "Xác nhận đơn vị đồng hành", eventId: "ev01", team: "Đối ngoại", assignee: "Lê Thảo Vy", deadline: eventDateTime(14, "17", "30"), status: "hoan_thanh", priority: "Vừa", description: "Gửi thư cảm ơn và xác nhận quyền lợi đồng hành." },
    { id: "t04", title: "Rà soát trạm trải nghiệm an toàn thông tin", eventId: "ev01", team: "Sự kiện", assignee: "Trần Gia Huy", deadline: eventDateTime(18, "07", "00"), status: "lam_lai", priority: "Vừa", description: "Cập nhật hướng dẫn trải nghiệm theo góp ý của Ban Chủ nhiệm." },
    { id: "t05", title: "Kiểm tra máy chiếu và âm thanh", eventId: "ev02", team: "Kỹ thuật", assignee: "Phạm Đức Long", deadline: eventDateTime(21, "16", "00"), status: "dang_lam", priority: "Cao", description: "Kiểm tra kết nối, micro dự phòng và slide." },
    { id: "t06", title: "Chuẩn bị tài liệu số cho workshop", eventId: "ev02", team: "Nội dung", assignee: "Bùi Ngọc Hà", deadline: eventDateTime(20, "12", "00"), status: "huy", priority: "Thấp", description: "Đầu việc in tài liệu được hủy để chuyển sang bộ tài liệu số." },
    { id: "t07", title: "Tổng hợp báo cáo CTF", eventId: "ev03", team: "Truyền thông", assignee: "Võ Khánh Linh", deadline: eventDateTime(14, "19", "00"), status: "cho_duyet", priority: "Vừa", description: "Tổng hợp số đội thi, kết quả và hình ảnh chương trình." },
    { id: "t08", title: "Đối soát chi phí hậu cần", eventId: "ev04", team: "Sự kiện", assignee: "Đặng Hoàng Nam", deadline: "2026-09-23T17:00:00", status: "hoan_thanh", priority: "Thấp", description: "Tổng hợp hóa đơn vào bảng chi phí tháng." }
  ];

  const teams = ["Ban Đối ngoại", "Ban Kỹ thuật", "Ban Nội dung", "Ban Sự kiện", "Ban Truyền thông"];
  let nextMemberId = 10;
  let nextEventId = 5;
  let nextTaskId = 9;
  let memberFilters = { search: "", team: "all", status: "all" };
  let eventFilters = { search: "", status: "all" };
  let eventView = "grid";
  let selectedEventId = "ev01";
  let detailTab = "attendance";
  let taskFilter = "all";
  let taskView = "board";

  const findEvent = (id) => events.find((event) => event.id === id) || events[0];
  const eventName = (id) => findEvent(id).name;
  const memberById = (id) => members.find((member) => member.id === id);

  const dashboardChart = () => `
    <div class="chart" style="height:230px" aria-label="Biểu đồ hoạt động thành viên 6 tháng gần đây">
      <svg viewBox="0 0 720 240" width="100%" height="230" role="img" aria-labelledby="activity-chart-title">
        <title id="activity-chart-title">Mức độ tham gia sự kiện tăng đều trong sáu tháng gần đây</title>
        <defs><linearGradient id="ops-chart-fill" x1="0" x2="0" y1="0" y2="1"><stop offset="0%" stop-color="#5558d9" stop-opacity=".22"/><stop offset="100%" stop-color="#5558d9" stop-opacity="0"/></linearGradient></defs>
        <g stroke="#e9eaf2" stroke-width="1"><line x1="56" y1="35" x2="690" y2="35"/><line x1="56" y1="80" x2="690" y2="80"/><line x1="56" y1="125" x2="690" y2="125"/><line x1="56" y1="170" x2="690" y2="170"/></g>
        <g fill="#9195a7" font-size="11" font-family="inherit"><text x="18" y="39">100</text><text x="24" y="84">75</text><text x="24" y="129">50</text><text x="24" y="174">25</text><text x="30" y="215">0</text></g>
        <path d="M70 150 L190 128 L310 139 L430 91 L550 80 L670 48 L670 188 L70 188 Z" fill="url(#ops-chart-fill)"/>
        <path d="M70 150 L190 128 L310 139 L430 91 L550 80 L670 48" fill="none" stroke="#5558d9" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>
        <g fill="#fff" stroke="#5558d9" stroke-width="3"><circle cx="70" cy="150" r="5"/><circle cx="190" cy="128" r="5"/><circle cx="310" cy="139" r="5"/><circle cx="430" cy="91" r="5"/><circle cx="550" cy="80" r="5"/><circle cx="670" cy="48" r="5"/></g>
        <g fill="#777b8f" font-size="12" font-family="inherit" text-anchor="middle"><text x="70" y="214">Tháng 5</text><text x="190" y="214">Tháng 6</text><text x="310" y="214">Tháng 7</text><text x="430" y="214">Tháng 8</text><text x="550" y="214">Tháng 9</text><text x="670" y="214">Tháng 10</text></g>
      </svg>
    </div>`;

  const dashboardScreen = {
    title: "Tổng quan",
    subtitle: "Một nhịp nhìn nhanh để CLB vận hành thật nhẹ nhàng.",
    render: () => {
      const pendingCount = members.filter((member) => member.status === "pending").length;
      const upcoming = events.filter((event) => event.status === "upcoming").slice(0, 2);
      const activity = [
        { title: "Lê Thảo Vy gửi đề xuất tài trợ", meta: "Ban Đối ngoại · 12 phút trước", tone: "violet", symbol: "↗" },
        { title: "Kịch bản khai mạc đã được gửi duyệt", meta: "Ngày hội Chào Tân sinh viên FIA · 1 giờ trước", tone: "indigo", symbol: "✓" },
        { title: "Đăng ký thành viên mới", meta: "Phạm Đức Long · hôm nay, 09:24", tone: "orange", symbol: "+" }
      ];
      return `${viewStyles()}<div class="page-stack ops-preview">
        <section class="hero">
          <div class="hero-copy">
            <span class="eyebrow">THỨ BA, 13 THÁNG 10, 2026</span>
            <h2>Chào buổi sáng, Ban Chủ nhiệm <span aria-hidden="true">✦</span></h2>
            <p class="muted">Mọi việc đang đi đúng nhịp. Đây là những điều cần bạn chú ý hôm nay.</p>
            <div class="toolbar"><div class="toolbar-left"><button class="btn btn-primary" type="button" data-dashboard-new-event>${icon("plus")} Tạo sự kiện</button><button class="btn btn-secondary" type="button" data-dashboard-members>${icon("users")} Xem thành viên</button></div></div>
          </div>
          <div class="hero-art" aria-hidden="true"><div class="hero-art-orbit"></div><div class="hero-art-star">✦</div><div class="hero-art-dot"></div><div class="hero-art-caption">CLB<br><span>2026</span></div></div>
        </section>
        <div class="grid-12">
          <div class="span-3"><article class="stat-card"><div class="stat-icon">${icon("users")}</div><span class="stat-value">${members.filter((m) => m.status === "active").length + 142}</span><span class="stat-label">Thành viên hoạt động</span><span class="stat-note">${badge("+12%", "success")} so với học kỳ trước</span></article></div>
          <div class="span-3"><article class="stat-card"><div class="stat-icon">${icon("calendar")}</div><span class="stat-value">${events.filter((event) => event.status !== "ended").length + 8}</span><span class="stat-label">Sự kiện trong năm</span><span class="stat-note">${badge("2 sắp tới", "indigo")} cần chuẩn bị</span></article></div>
          <div class="span-3"><article class="stat-card"><div class="stat-icon">${icon("check")}</div><span class="stat-value">${tasks.filter((task) => task.status === "hoan_thanh").length + 27}</span><span class="stat-label">Đầu việc hoàn thành</span><span class="stat-note">${badge("+8", "success")} trong tuần này</span></article></div>
          <div class="span-3"><article class="stat-card"><div class="stat-icon">${icon("wallet")}</div><span class="stat-value">${UI.money(18450000)}</span><span class="stat-label">Quỹ hoạt động</span><span class="stat-note">Cập nhật ngày 10/10</span></article></div>
        </div>
        <div class="grid-12">
          <section class="card span-7">
            <div class="card-header"><div><span class="eyebrow">GẮN KẾT CỘNG ĐỒNG</span><h3>Mức độ tham gia</h3><p class="muted small">Lượt tham gia sự kiện trong 6 tháng gần đây</p></div><button class="btn btn-ghost btn-sm" type="button" data-demo-export>${icon("download")} Tải báo cáo</button></div>
            <div class="card-body"><div class="chart-legend"><span class="chart-legend-dot"></span> Lượt tham gia <span class="muted small">·</span> <strong>86</strong><span class="muted small">tháng này</span></div>${dashboardChart()}</div>
          </section>
          <section class="card span-5">
            <div class="card-header"><div><span class="eyebrow">CẦN BẠN XEM QUA</span><h3>Phê duyệt nhanh</h3><p class="muted small">Một vài việc đang chờ Ban Chủ nhiệm</p></div>${badge(`${pendingCount} mới`, "orange")}</div>
            <div class="card-body approval-list">
              <button class="list-item approval-item" type="button" data-dashboard-pending><span class="approval-icon">${icon("users")}</span><span class="grow"><strong>${pendingCount} hồ sơ thành viên</strong><span class="small muted">Phạm Đức Long và Đỗ Quang Khải</span></span>${icon("chevron")}</button>
              <button class="list-item approval-item" type="button" data-dashboard-review><span class="approval-icon approval-icon-orange">${icon("file")}</span><span class="grow"><strong>2 nhiệm vụ chờ duyệt</strong><span class="small muted">Kịch bản và album ảnh sự kiện</span></span>${icon("chevron")}</button>
              <div class="approval-footnote"><span class="approval-pulse"></span> Bạn đã xử lý <strong>8/10</strong> việc ưu tiên trong tuần.</div>
            </div>
          </section>
        </div>
        <div class="grid-12">
          <section class="card span-7">
            <div class="card-header"><div><span class="eyebrow">LỊCH HOẠT ĐỘNG</span><h3>Sự kiện sắp tới</h3></div><button class="btn btn-ghost btn-sm" type="button" data-dashboard-events>Xem tất cả ${icon("arrow")}</button></div>
            <div class="card-body dashboard-events">${upcoming.map((event) => `<button type="button" class="list-item dashboard-event" data-dashboard-open-event="${escapeHtml(event.id)}"><span class="event-date-chip"><strong>${escapeHtml(dateLabel(event.start, { day: "2-digit" }))}</strong><span>${escapeHtml(dateLabel(event.start, { month: "short" }))}</span></span><span class="grow"><strong>${escapeHtml(event.name)}</strong><span class="small muted">${icon("clock")} ${escapeHtml(dateLabel(event.start, { hour: "2-digit", minute: "2-digit" }))} · ${icon("location")} ${escapeHtml(event.location)}</span></span>${badge(eventStatusLabel(event.status), eventStatusTone(event.status))}</button>`).join("")}</div>
          </section>
          <section class="card span-5">
            <div class="card-header"><div><span class="eyebrow">NHỊP CLB</span><h3>Hoạt động gần đây</h3></div><button class="btn btn-ghost btn-sm" type="button" data-dashboard-activity>Tất cả</button></div>
            <div class="card-body activity-list">${activity.map((item) => `<div class="list-item activity-item"><span class="activity-mark activity-${escapeHtml(item.tone)}">${escapeHtml(item.symbol)}</span><span class="grow"><strong>${escapeHtml(item.title)}</strong><span class="small muted">${escapeHtml(item.meta)}</span></span></div>`).join("")}</div>
          </section>
        </div>
        <p class="small muted demo-note">${badge("DỮ LIỆU MẪU", "neutral")} Bảng điều khiển này là bản xem trước tương tác, không kết nối dữ liệu thật.</p>
      </div>`;
    },
    bind: (root) => {
      root.querySelectorAll("[data-dashboard-members], [data-dashboard-pending]").forEach((button) => button.addEventListener("click", () => UI.navigate("members")));
      root.querySelectorAll("[data-dashboard-events], [data-dashboard-activity]").forEach((button) => button.addEventListener("click", () => UI.navigate("events")));
      root.querySelector("[data-dashboard-new-event]")?.addEventListener("click", () => openEventModal(root, "dashboard"));
      root.querySelector("[data-dashboard-review]")?.addEventListener("click", () => UI.navigate("tasks"));
      root.querySelectorAll("[data-dashboard-open-event]").forEach((button) => button.addEventListener("click", () => {
        selectedEventId = button.getAttribute("data-dashboard-open-event");
        detailTab = "attendance";
        UI.navigate("event-detail");
      }));
      root.querySelector("[data-demo-export]")?.addEventListener("click", () => UI.toast("Bản demo: báo cáo chỉ hiển thị mẫu, chưa tạo hoặc tải tệp."));
    }
  };

  const memberRows = () => {
    const filtered = members.filter((member) => {
      const query = memberFilters.search.trim().toLocaleLowerCase("vi");
      const matchesSearch = !query || [member.name, member.studentId, member.email].some((value) => value.toLocaleLowerCase("vi").includes(query));
      return matchesSearch && (memberFilters.team === "all" || member.team === memberFilters.team) && (memberFilters.status === "all" || member.status === memberFilters.status);
    });
    if (!filtered.length) return `<tr><td colspan="6"><div class="empty-state"><span class="empty-state-icon">${icon("search")}</span><strong>Chưa tìm thấy thành viên</strong><span class="small muted">Thử đổi từ khóa hoặc bộ lọc của bạn.</span></div></td></tr>`;
    return filtered.map((member) => `<tr>
      <td><div class="member-cell">${avatar(member.name, member.tone)}<span><strong>${escapeHtml(member.name)}</strong><span class="small muted">${escapeHtml(member.email)}</span></span></div></td>
      <td><span class="member-id">${escapeHtml(member.studentId)}</span></td><td>${escapeHtml(member.team.replace(/^Ban /, ""))}</td>
      <td>${escapeHtml(member.role)}</td><td>${badge(memberStatusLabel(member.status), memberStatusTone(member.status))}</td>
      <td><button class="btn btn-ghost btn-sm" type="button" data-member-toggle="${escapeHtml(member.id)}" aria-label="${member.status === "active" ? "Tạm khóa" : member.status === "pending" ? "Duyệt" : "Kích hoạt"} ${escapeHtml(member.name)}">${icon(member.status === "active" ? "shield" : "check")} ${member.status === "active" ? "Tạm khóa" : member.status === "pending" ? "Duyệt" : "Kích hoạt"}</button></td>
    </tr>`).join("");
  };

  const membersScreen = {
    title: "Thành viên",
    subtitle: "Quản lý cộng đồng và các ban hoạt động của CLB.",
    render: () => `${viewStyles()}<div class="page-stack ops-preview">
      <section class="card members-toolbar-card"><div class="card-body"><div class="toolbar"><div class="toolbar-left member-filter-fields">
        <label class="field search-field"><span class="field-label">Tìm kiếm</span><span class="input-with-icon">${icon("search")}<input class="input" type="search" data-member-search placeholder="Tên, MSSV hoặc email" value="${escapeHtml(memberFilters.search)}"></span></label>
        <label class="field"><span class="field-label">Ban hoạt động</span><select class="select" data-member-team><option value="all">Tất cả các ban</option>${teams.map((team) => `<option value="${escapeHtml(team)}" ${memberFilters.team === team ? "selected" : ""}>${escapeHtml(team)}</option>`).join("")}</select></label>
        <label class="field"><span class="field-label">Tình trạng</span><select class="select" data-member-status><option value="all">Tất cả trạng thái</option><option value="active" ${memberFilters.status === "active" ? "selected" : ""}>Đang hoạt động</option><option value="pending" ${memberFilters.status === "pending" ? "selected" : ""}>Chờ duyệt</option><option value="paused" ${memberFilters.status === "paused" ? "selected" : ""}>Tạm khóa</option></select></label>
      </div><div class="toolbar-right"><button type="button" class="btn btn-secondary" data-member-export>${icon("download")} Xuất danh sách</button><button type="button" class="btn btn-primary" data-member-add>${icon("plus")} Thêm thành viên</button></div></div></div></section>
      <div class="grid-12">
        <div class="span-4"><article class="stat-card compact-stat"><div class="stat-icon">${icon("users")}</div><span class="stat-value">${members.length}</span><span class="stat-label">Tổng thành viên mẫu</span><span class="stat-note">${badge("+4", "success")} trong học kỳ này</span></article></div>
        <div class="span-4"><article class="stat-card compact-stat"><div class="stat-icon">${icon("check")}</div><span class="stat-value">${members.filter((member) => member.status === "active").length}</span><span class="stat-label">Đang hoạt động</span><span class="stat-note">Tham gia ít nhất một ban</span></article></div>
        <div class="span-4"><article class="stat-card compact-stat"><div class="stat-icon">${icon("clock")}</div><span class="stat-value">${members.filter((member) => member.status === "pending").length}</span><span class="stat-label">Chờ duyệt hồ sơ</span><span class="stat-note">${badge("Cần xử lý", "orange")} trong hôm nay</span></article></div>
      </div>
      <section class="card"><div class="card-header"><div><span class="eyebrow">CỘNG ĐỒNG CLB</span><h3>Danh sách thành viên <span class="count-label">${members.length}</span></h3></div><button class="btn btn-ghost btn-sm" type="button" data-member-reset-filter>${icon("filter")} Đặt lại lọc</button></div>
        <div class="table-wrap"><table class="data-table"><thead><tr><th>Thành viên</th><th>MSSV</th><th>Ban hoạt động</th><th>Vai trò</th><th>Tình trạng</th><th></th></tr></thead><tbody data-member-rows>${memberRows()}</tbody></table></div>
        <div class="card-body table-foot"><span class="small muted">Đang hiển thị danh sách dữ liệu mẫu</span><span class="small muted">Cập nhật lần cuối: hôm nay, 09:24</span></div>
      </section><p class="small muted demo-note">${badge("BẢN DEMO", "neutral")} Thay đổi trạng thái chỉ có hiệu lực trong bản xem trước này.</p>
    </div>`,
    bind: (root) => {
      const updateRows = () => { const body = root.querySelector("[data-member-rows]"); if (body) body.innerHTML = memberRows(); };
      root.querySelector("[data-member-search]")?.addEventListener("input", (event) => { memberFilters.search = event.target.value; updateRows(); });
      root.querySelector("[data-member-team]")?.addEventListener("change", (event) => { memberFilters.team = event.target.value; updateRows(); });
      root.querySelector("[data-member-status]")?.addEventListener("change", (event) => { memberFilters.status = event.target.value; updateRows(); });
      root.querySelector("[data-member-reset-filter]")?.addEventListener("click", () => { memberFilters = { search: "", team: "all", status: "all" }; refresh(root, "members"); });
      root.querySelector("[data-member-add]")?.addEventListener("click", () => openMemberModal(root));
      root.querySelector("[data-member-export]")?.addEventListener("click", () => UI.toast("Bản demo: chức năng xuất danh sách chưa tạo tệp."));
      root.querySelector("[data-member-rows]")?.addEventListener("click", (event) => {
        const button = event.target.closest("[data-member-toggle]");
        if (!button) return;
        const member = memberById(button.getAttribute("data-member-toggle"));
        if (!member) return;
        member.status = member.status === "active" ? "paused" : "active";
        UI.toast(`Bản demo: đã cập nhật tình trạng của ${member.name}.`);
        refresh(root, "members");
      });
    }
  };

  function openMemberModal(root) {
    UI.modal({
      title: "Thêm thành viên mới",
      body: `<p class="muted small modal-intro">Thêm hồ sơ mẫu vào danh sách để xem trạng thái chờ duyệt.</p><form id="preview-member-form" class="modal-form" novalidate>
        ${label("Họ và tên", `<input class="input" name="name" autocomplete="name" placeholder="Ví dụ: Nguyễn Minh Anh" required maxlength="80">`)}
        <div class="grid-12 form-grid"><div class="span-6">${label("MSSV", `<input class="input" name="studentId" inputmode="numeric" placeholder="Ví dụ: 24124012" required maxlength="12">`)}</div><div class="span-6">${label("Ban hoạt động", `<select class="select" name="team" required><option value="">Chọn ban</option>${teams.map((team) => `<option value="${escapeHtml(team)}">${escapeHtml(team)}</option>`).join("")}</select>`)}</div></div>
        ${label("Email sinh viên", `<input class="input" name="email" type="email" autocomplete="email" placeholder="ten@sv.example.edu.vn" required maxlength="120">`)}
        <div class="form-hint">${badge("DỮ LIỆU MẪU", "neutral")} Hồ sơ mới sẽ được thêm với trạng thái chờ duyệt.</div>
      </form>`,
      footer: `<button type="button" class="btn btn-ghost" data-modal-cancel>Để sau</button><button type="submit" form="preview-member-form" class="btn btn-primary">${icon("plus")} Thêm vào danh sách</button>`,
      onMount: (dialog) => {
        closeModal(dialog);
        const form = dialog.querySelector("#preview-member-form");
        form?.addEventListener("submit", (event) => {
          event.preventDefault();
          if (!form.reportValidity()) return;
          const data = new FormData(form);
          const name = String(data.get("name") || "").trim();
          const studentId = String(data.get("studentId") || "").trim();
          const email = String(data.get("email") || "").trim();
          const duplicate = members.some((member) => member.studentId.toLocaleLowerCase("vi") === studentId.toLocaleLowerCase("vi") || member.email.toLocaleLowerCase("vi") === email.toLocaleLowerCase("vi"));
          if (duplicate) { UI.toast("MSSV hoặc email đã có trong danh sách mẫu."); return; }
          members.unshift({ id: `m${String(nextMemberId++).padStart(2, "0")}`, name, studentId, email, team: String(data.get("team")), role: "Thành viên", status: "pending", joined: new Date().toISOString(), tone: "indigo" });
          UI.closeModal();
          UI.toast("Bản demo: đã thêm thành viên vào danh sách mẫu.");
          refresh(root, "members");
        });
      }
    });
  }

  const eventCards = () => {
    const query = eventFilters.search.trim().toLocaleLowerCase("vi");
    const visible = events.filter((event) => (!query || `${event.name} ${event.code} ${event.location}`.toLocaleLowerCase("vi").includes(query)) && (eventFilters.status === "all" || event.status === eventFilters.status));
    if (!visible.length) return `<div class="empty-state"><span class="empty-state-icon">${icon("calendar")}</span><strong>Không tìm thấy sự kiện</strong><span class="small muted">Thử xóa bộ lọc hoặc tạo sự kiện mẫu mới.</span></div>`;
    return visible.map((event) => `<button class="event-tile" type="button" data-event-open="${escapeHtml(event.id)}">
      <span class="event-cover cover-${escapeHtml(event.accent)}"><span class="event-cover-label">${escapeHtml(event.category)}</span><span class="event-cover-mark">${icon(event.icon)}</span><span class="event-cover-code">${escapeHtml(event.code)}</span></span>
      <span class="event-tile-body"><span class="row event-tile-top"><strong>${escapeHtml(event.name)}</strong>${badge(eventStatusLabel(event.status), eventStatusTone(event.status))}</span><span class="event-tile-meta">${icon("calendar")} ${escapeHtml(dateTimeLabel(event.start))}</span><span class="event-tile-meta">${icon("location")} ${escapeHtml(event.location)}</span><span class="event-tile-bottom"><span class="event-attendee-count">${icon("users")} ${event.registrations.length + (event.registered ? 1 : 0)} / ${event.capacity} người</span><span class="event-progress"><span class="progress-bar"><span style="width:${Math.min(100, Math.round((event.registrations.length / event.capacity) * 100))}%"></span></span></span></span></span>
    </button>`).join("");
  };

  const eventTableRows = () => {
    const query = eventFilters.search.trim().toLocaleLowerCase("vi");
    const visible = events.filter((event) => (!query || `${event.name} ${event.code} ${event.location}`.toLocaleLowerCase("vi").includes(query)) && (eventFilters.status === "all" || event.status === eventFilters.status));
    if (!visible.length) return `<tr><td colspan="5"><div class="empty-state"><strong>Không tìm thấy sự kiện</strong><span class="small muted">Thử xóa bộ lọc của bạn.</span></div></td></tr>`;
    return visible.map((event) => `<tr><td><button class="text-button" type="button" data-event-open="${escapeHtml(event.id)}"><strong>${escapeHtml(event.name)}</strong><span class="small muted">${escapeHtml(event.code)} · ${escapeHtml(event.category)}</span></button></td><td>${escapeHtml(dateTimeLabel(event.start))}</td><td>${escapeHtml(event.location)}</td><td>${badge(eventStatusLabel(event.status), eventStatusTone(event.status))}</td><td>${event.registrations.length + (event.registered ? 1 : 0)} / ${event.capacity}</td></tr>`).join("");
  };

  const eventsScreen = {
    title: "Sự kiện",
    subtitle: "Lên lịch, theo dõi và cùng nhau tạo nên những khoảnh khắc đáng nhớ.",
    render: () => `${viewStyles()}<div class="page-stack ops-preview">
      <section class="card"><div class="card-body"><div class="toolbar"><div class="toolbar-left event-filter-fields">
        <label class="field search-field"><span class="field-label">Tìm sự kiện</span><span class="input-with-icon">${icon("search")}<input type="search" class="input" data-event-search placeholder="Tên, mã hoặc địa điểm" value="${escapeHtml(eventFilters.search)}"></span></label>
        <label class="field"><span class="field-label">Trạng thái</span><select class="select" data-event-status><option value="all">Tất cả sự kiện</option><option value="upcoming" ${eventFilters.status === "upcoming" ? "selected" : ""}>Sắp diễn ra</option><option value="live" ${eventFilters.status === "live" ? "selected" : ""}>Đang diễn ra</option><option value="ended" ${eventFilters.status === "ended" ? "selected" : ""}>Đã kết thúc</option></select></label>
      </div><div class="toolbar-right"><div class="segmented" role="group" aria-label="Kiểu hiển thị"><button type="button" data-event-view="grid" class="${eventView === "grid" ? "active" : ""}" aria-pressed="${eventView === "grid"}">${icon("grid")} Thẻ</button><button type="button" data-event-view="list" class="${eventView === "list" ? "active" : ""}" aria-pressed="${eventView === "list"}">${icon("file")} Danh sách</button></div><button type="button" class="btn btn-primary" data-event-add>${icon("plus")} Tạo sự kiện</button></div></div></div></section>
      <section class="events-results"><div class="row events-heading"><div><span class="eyebrow">LỊCH CLB</span><h3>Sự kiện của chúng ta</h3></div><span class="muted small">${events.length} sự kiện mẫu</span></div><div data-event-results class="${eventView === "grid" ? "event-grid" : "table-wrap card events-table-card"}">${eventView === "grid" ? eventCards() : `<table class="data-table"><thead><tr><th>Sự kiện</th><th>Thời gian</th><th>Địa điểm</th><th>Trạng thái</th><th>Đăng ký</th></tr></thead><tbody>${eventTableRows()}</tbody></table>`}</div></section>
      <p class="small muted demo-note">${badge("BẢN DEMO", "neutral")} Các sự kiện và số lượt đăng ký là dữ liệu mẫu.</p>
    </div>`,
    bind: (root) => {
      const update = () => refresh(root, "events");
      root.querySelector("[data-event-search]")?.addEventListener("input", (event) => { eventFilters.search = event.target.value; const focused = true; update(); if (focused) { const input = root.querySelector("[data-event-search]"); input?.focus(); input?.setSelectionRange(input.value.length, input.value.length); } });
      root.querySelector("[data-event-status]")?.addEventListener("change", (event) => { eventFilters.status = event.target.value; update(); });
      root.querySelectorAll("[data-event-view]").forEach((button) => button.addEventListener("click", () => { eventView = button.getAttribute("data-event-view"); update(); }));
      root.querySelector("[data-event-add]")?.addEventListener("click", () => openEventModal(root, "events"));
      root.querySelector("[data-event-results]")?.addEventListener("click", (event) => {
        const button = event.target.closest("[data-event-open]");
        if (!button) return;
        selectedEventId = button.getAttribute("data-event-open");
        detailTab = "attendance";
        UI.navigate("event-detail");
      });
    }
  };

  function openEventModal(root, returnKey = "events") {
    UI.modal({
      title: "Tạo sự kiện mới",
      body: `<p class="muted small modal-intro">Tạo một sự kiện mẫu để khám phá trang chi tiết và danh sách đăng ký.</p><form id="preview-event-form" class="modal-form" novalidate>
        ${label("Tên sự kiện", `<input class="input" name="name" placeholder="Ví dụ: Workshop An toàn thông tin" required maxlength="100">`)}
        <div class="grid-12 form-grid"><div class="span-6">${label("Loại sự kiện", `<select class="select" name="category" required><option value="">Chọn loại</option><option>Workshop</option><option>Sự kiện cộng đồng</option><option>Sinh hoạt CLB</option><option>Cuộc thi CTF</option></select>`)}</div><div class="span-6">${label("Sức chứa", `<input class="input" name="capacity" type="number" min="1" max="5000" value="80" required>`)}</div></div>
        <div class="grid-12 form-grid"><div class="span-6">${label("Bắt đầu", `<input class="input" name="start" type="datetime-local" required>`)} </div><div class="span-6">${label("Kết thúc", `<input class="input" name="end" type="datetime-local" required>`)}</div></div>
        ${label("Địa điểm", `<input class="input" name="location" placeholder="Tên phòng hoặc địa chỉ" required maxlength="120">`)}
        <div class="form-hint">${badge("DỮ LIỆU MẪU", "neutral")} Không gửi thông báo hay đặt chỗ thật.</div>
      </form>`,
      footer: `<button type="button" class="btn btn-ghost" data-modal-cancel>Hủy</button><button type="submit" form="preview-event-form" class="btn btn-primary">${icon("plus")} Tạo sự kiện</button>`,
      onMount: (dialog) => {
        closeModal(dialog);
        const form = dialog.querySelector("#preview-event-form");
        form?.addEventListener("submit", (event) => {
          event.preventDefault();
          if (!form.reportValidity()) return;
          const data = new FormData(form);
          const start = new Date(String(data.get("start")));
          const end = new Date(String(data.get("end")));
          if (end <= start) { UI.toast("Thời gian kết thúc cần sau thời gian bắt đầu."); return; }
          const newEvent = {
            id: `ev${String(nextEventId++).padStart(2, "0")}`, code: `CLB-${String(27 + nextEventId - 6).padStart(3, "0")}`,
            name: String(data.get("name")).trim(), category: String(data.get("category")), status: "upcoming", start: start.toISOString(), end: end.toISOString(),
            location: String(data.get("location")).trim(), capacity: Number(data.get("capacity")), registered: false, accent: "indigo", icon: "calendar", registrations: []
          };
          events.unshift(newEvent);
          selectedEventId = newEvent.id;
          UI.closeModal();
          UI.toast("Bản demo: đã tạo sự kiện mẫu.");
          if (returnKey === "dashboard") UI.navigate("events");
          else refresh(root, "events");
        });
      }
    });
  }

  const eventAttendancePanel = (event) => {
    const total = event.registrations.length + (event.registered ? 1 : 0);
    const rows = event.registrations.map((registration) => `<tr><td><div class="member-cell">${avatar(registration.name, "indigo")}<span><strong>${escapeHtml(registration.name)}</strong><span class="small muted">Ban ${escapeHtml(registration.team)}</span></span></div></td><td>${badge("Đã đăng ký", "success")}</td><td>${registration.attended ? badge("Có mặt", "success") : badge("Chưa điểm danh", "neutral")}</td></tr>`).join("");
    return `<div class="grid-12 detail-stats"><div class="span-4"><article class="stat-card compact-stat"><span class="stat-value">${total}</span><span class="stat-label">Đã đăng ký</span></article></div><div class="span-4"><article class="stat-card compact-stat"><span class="stat-value">${event.registrations.filter((item) => item.attended).length}</span><span class="stat-label">Đã điểm danh</span></article></div><div class="span-4"><article class="stat-card compact-stat"><span class="stat-value">${Math.max(0, event.capacity - total)}</span><span class="stat-label">Chỗ còn lại</span></article></div></div>
      <section class="card"><div class="card-header"><div><h3>Danh sách đăng ký</h3><p class="small muted">Dữ liệu người tham gia được tạo để minh họa giao diện.</p></div><button type="button" class="btn btn-secondary btn-sm" data-detail-export>${icon("download")} Tải danh sách</button></div><div class="table-wrap"><table class="data-table"><thead><tr><th>Thành viên</th><th>Đăng ký</th><th>Điểm danh</th></tr></thead><tbody>${rows || `<tr><td colspan="3"><div class="empty-state"><strong>Chưa có đăng ký</strong><span class="small muted">Mời thành viên tham gia sự kiện.</span></div></td></tr>`}</tbody></table></div></section>`;
  };

  const eventTasksPanel = (event) => {
    const related = tasks.filter((task) => task.eventId === event.id);
    return `<div class="toolbar event-task-toolbar"><div class="toolbar-left"><div><h3>Đầu việc sự kiện</h3><p class="small muted">${related.length} nhiệm vụ đang theo dõi</p></div></div><div class="toolbar-right"><button class="btn btn-primary btn-sm" type="button" data-detail-add-task>${icon("plus")} Thêm nhiệm vụ</button></div></div>
      <div class="task-list">${related.length ? related.map((task) => `<article class="task-card detail-task-card"><div class="row"><div class="grow"><strong>${escapeHtml(task.title)}</strong><span class="small muted">${escapeHtml(task.team)} · ${escapeHtml(task.assignee)}</span></div>${badge(taskStatusLabel(task.status), taskStatusTone(task.status))}</div><div class="row task-card-footer"><span class="small muted">${icon("clock")} Hạn ${escapeHtml(dateTimeLabel(task.deadline))}</span>${badge(`Ưu tiên ${task.priority}`, task.priority === "Cao" ? "orange" : "neutral")}</div></article>`).join("") : `<div class="empty-state"><strong>Chưa có nhiệm vụ cho sự kiện này</strong><span class="small muted">Tạo nhiệm vụ đầu tiên để cùng chuẩn bị.</span></div>`}</div>`;
  };

  const eventDetailScreen = {
    title: "Chi tiết sự kiện",
    subtitle: "Theo dõi đăng ký, điểm danh và tiến độ chuẩn bị.",
    render: () => {
      const event = findEvent(selectedEventId);
      const count = event.registrations.length + (event.registered ? 1 : 0);
      return `${viewStyles()}<div class="page-stack ops-preview">
        <div class="toolbar detail-back-toolbar"><div class="toolbar-left"><button class="btn btn-ghost btn-sm" type="button" data-detail-back>${icon("arrow")} Tất cả sự kiện</button><span class="muted small">/ ${escapeHtml(event.code)}</span></div><div class="toolbar-right">${badge("BẢN DEMO", "neutral")}<button class="btn btn-secondary btn-sm" type="button" data-detail-share>${icon("more")} Tùy chọn</button></div></div>
        <section class="event-detail-hero cover-${escapeHtml(event.accent)}"><div class="event-detail-copy"><span class="eyebrow">${escapeHtml(event.category.toLocaleUpperCase("vi"))} · ${escapeHtml(event.code)}</span><h2>${escapeHtml(event.name)}</h2><p class="detail-meta-line">${icon("calendar")} ${escapeHtml(dateTimeLabel(event.start))} – ${escapeHtml(dateLabel(event.end, { hour: "2-digit", minute: "2-digit" }))}<span>·</span>${icon("location")} ${escapeHtml(event.location)}</p><div class="toolbar"><div class="toolbar-left">${badge(eventStatusLabel(event.status), eventStatusTone(event.status))}${badge(`${count} / ${event.capacity} người đăng ký`, "neutral")}</div></div></div><div class="event-detail-art" aria-hidden="true">${icon(event.icon)}</div></section>
        <section class="card rsvp-card"><div class="card-body toolbar"><div class="toolbar-left"><div class="rsvp-symbol">${icon("check")}</div><div><strong>${event.registered ? "Bạn đang tham gia sự kiện này" : "Cùng tham gia sự kiện nhé?"}</strong><p class="small muted">${event.registered ? "Vị trí của bạn đã được ghi nhận trong bản xem trước." : "Đăng ký thử để khám phá trạng thái RSVP."}</p></div></div><button class="btn ${event.registered ? "btn-secondary" : "btn-primary"}" type="button" data-detail-rsvp>${event.registered ? "Hủy đăng ký mẫu" : "Đăng ký tham gia"}</button></div></section>
        <div class="tabs" role="tablist" aria-label="Thông tin sự kiện"><button type="button" role="tab" data-detail-tab="attendance" class="${detailTab === "attendance" ? "active" : ""}" aria-selected="${detailTab === "attendance"}">${icon("users")} Người tham gia <span>${count}</span></button><button type="button" role="tab" data-detail-tab="tasks" class="${detailTab === "tasks" ? "active" : ""}" aria-selected="${detailTab === "tasks"}">${icon("check")} Nhiệm vụ <span>${tasks.filter((task) => task.eventId === event.id).length}</span></button></div>
        <div class="page-stack detail-panel" data-detail-panel>${detailTab === "attendance" ? eventAttendancePanel(event) : eventTasksPanel(event)}</div>
        <p class="small muted demo-note">${badge("BẢN DEMO", "neutral")} RSVP, điểm danh và danh sách người tham gia chỉ mô phỏng.</p>
      </div>`;
    },
    bind: (root) => {
      root.querySelector("[data-detail-back]")?.addEventListener("click", () => UI.navigate("events"));
      root.querySelector("[data-detail-share]")?.addEventListener("click", () => UI.toast("Bản demo: chưa có liên kết chia sẻ thật."));
      root.querySelector("[data-detail-rsvp]")?.addEventListener("click", () => {
        const event = findEvent(selectedEventId);
        event.registered = !event.registered;
        UI.toast(`Bản demo: ${event.registered ? "đã đăng ký tham gia" : "đã hủy đăng ký"} ${event.name}.`);
        refresh(root, "event-detail");
      });
      root.querySelectorAll("[data-detail-tab]").forEach((button) => button.addEventListener("click", () => { detailTab = button.getAttribute("data-detail-tab"); refresh(root, "event-detail"); }));
      root.querySelector("[data-detail-export]")?.addEventListener("click", () => UI.toast("Bản demo: chưa tạo tệp danh sách người tham gia."));
      root.querySelector("[data-detail-add-task]")?.addEventListener("click", () => openTaskModal(root, "event-detail", selectedEventId));
    }
  };

  const statusOrder = ["dang_lam", "cho_duyet", "lam_lai", "hoan_thanh", "huy"];
  const taskMatchesFilter = (task) => taskFilter === "all" || task.status === taskFilter;
  const taskCard = (task, compact = false) => `<article class="task-card ${compact ? "task-card-compact" : ""}">
    <div class="row task-card-title"><strong>${escapeHtml(task.title)}</strong><button type="button" class="btn btn-ghost btn-sm task-more" data-task-more="${escapeHtml(task.id)}" aria-label="Mở nhiệm vụ">${icon("more")}</button></div>
    <p class="small muted">${escapeHtml(eventName(task.eventId))}</p><div class="task-card-tags">${badge(task.team.replace(/^Ban /, ""), "neutral")}${badge(`Ưu tiên ${task.priority}`, task.priority === "Cao" ? "orange" : "neutral")}</div>
    <div class="row task-card-footer"><span class="task-assignee">${avatar(task.assignee, "indigo")}<span class="small">${escapeHtml(task.assignee)}</span></span><span class="small muted">${icon("clock")} ${escapeHtml(dateLabel(task.deadline, { day: "2-digit", month: "short" }))}</span></div>
    <div class="task-card-action"><button type="button" class="btn btn-ghost btn-sm" data-task-next="${escapeHtml(task.id)}">${({ dang_lam: "Gửi duyệt", cho_duyet: "Duyệt hoàn thành", lam_lai: "Gửi lại duyệt", hoan_thanh: "Mở lại", huy: "Khôi phục" })[task.status]} ${icon("arrow")}</button></div>
  </article>`;
  const taskBoard = () => {
    const filtered = tasks.filter(taskMatchesFilter);
    return `<div class="task-board">${statusOrder.map((status) => {
      const inColumn = filtered.filter((task) => task.status === status);
      return `<section class="task-column task-column-${status}"><div class="task-column-header"><span class="task-column-dot task-dot-${status}"></span><strong>${taskStatusLabel(status)}</strong><span class="task-column-count">${inColumn.length}</span></div><div class="task-column-body">${inColumn.map((task) => taskCard(task)).join("") || `<div class="task-column-empty">Chưa có nhiệm vụ</div>`}</div></section>`;
    }).join("")}</div>`;
  };
  const taskList = () => {
    const filtered = tasks.filter(taskMatchesFilter);
    if (!filtered.length) return `<div class="empty-state"><strong>Chưa có nhiệm vụ ở trạng thái này</strong><span class="small muted">Thử chọn trạng thái khác hoặc thêm đầu việc.</span></div>`;
    return `<div class="task-list">${filtered.map((task) => taskCard(task, true)).join("")}</div>`;
  };

  const tasksScreen = {
    title: "Nhiệm vụ",
    subtitle: "Chia nhỏ công việc, phối hợp nhịp nhàng và cùng hoàn thành mục tiêu.",
    render: () => `${viewStyles()}<div class="page-stack ops-preview">
      <div class="grid-12 task-summary-grid"><div class="span-3"><article class="stat-card compact-stat"><span class="stat-value">${tasks.length}</span><span class="stat-label">Tổng nhiệm vụ</span></article></div><div class="span-3"><article class="stat-card compact-stat"><span class="stat-value">${tasks.filter((task) => task.status === "dang_lam").length}</span><span class="stat-label">Đang làm</span></article></div><div class="span-3"><article class="stat-card compact-stat"><span class="stat-value">${tasks.filter((task) => task.status === "cho_duyet").length}</span><span class="stat-label">Chờ duyệt</span></article></div><div class="span-3"><article class="stat-card compact-stat"><span class="stat-value">${tasks.filter((task) => task.status === "hoan_thanh").length}</span><span class="stat-label">Đã hoàn thành</span></article></div></div>
      <section class="card"><div class="card-body"><div class="toolbar task-toolbar"><div class="toolbar-left"><div class="segmented task-status-filters" role="group" aria-label="Lọc theo trạng thái"><button type="button" data-task-filter="all" class="${taskFilter === "all" ? "active" : ""}">Tất cả <span>${tasks.length}</span></button>${statusOrder.map((status) => `<button type="button" data-task-filter="${status}" class="${taskFilter === status ? "active" : ""}">${taskStatusLabel(status)}</button>`).join("")}</div></div><div class="toolbar-right"><div class="segmented" role="group" aria-label="Kiểu hiển thị"><button type="button" data-task-view="board" class="${taskView === "board" ? "active" : ""}" aria-pressed="${taskView === "board"}">${icon("grid")} Bảng</button><button type="button" data-task-view="list" class="${taskView === "list" ? "active" : ""}" aria-pressed="${taskView === "list"}">${icon("file")} Danh sách</button></div><button type="button" class="btn btn-primary" data-task-add>${icon("plus")} Thêm nhiệm vụ</button></div></div></div></section>
      <div class="task-view-container" data-task-content>${taskView === "board" ? taskBoard() : taskList()}</div>
      <p class="small muted demo-note">${badge("BẢN DEMO", "neutral")} Trạng thái và người phụ trách được lưu tạm trong bản xem trước.</p>
    </div>`,
    bind: (root) => {
      root.querySelectorAll("[data-task-filter]").forEach((button) => button.addEventListener("click", () => { taskFilter = button.getAttribute("data-task-filter"); refresh(root, "tasks"); }));
      root.querySelectorAll("[data-task-view]").forEach((button) => button.addEventListener("click", () => { taskView = button.getAttribute("data-task-view"); refresh(root, "tasks"); }));
      root.querySelector("[data-task-add]")?.addEventListener("click", () => openTaskModal(root, "tasks"));
      root.querySelector("[data-task-content]")?.addEventListener("click", (event) => {
        const nextButton = event.target.closest("[data-task-next]");
        const moreButton = event.target.closest("[data-task-more]");
        if (moreButton) { UI.toast("Bản demo: chi tiết nhiệm vụ đang được minh họa ngay trên thẻ."); return; }
        if (!nextButton) return;
        const task = tasks.find((item) => item.id === nextButton.getAttribute("data-task-next"));
        if (!task) return;
        task.status = ({ dang_lam: "cho_duyet", cho_duyet: "hoan_thanh", lam_lai: "cho_duyet", hoan_thanh: "dang_lam", huy: "dang_lam" })[task.status];
        UI.toast(`Bản demo: nhiệm vụ đã chuyển sang “${taskStatusLabel(task.status)}”.`);
        refresh(root, "tasks");
      });
    }
  };

  function openTaskModal(root, returnKey = "tasks", eventId = "") {
    const defaultEvent = eventId || events.find((event) => event.status === "upcoming")?.id || events[0].id;
    UI.modal({
      title: "Thêm nhiệm vụ",
      body: `<p class="muted small modal-intro">Tạo đầu việc mẫu, có thể theo dõi ngay trong bảng nhiệm vụ.</p><form id="preview-task-form" class="modal-form" novalidate>
        ${label("Tên nhiệm vụ", `<input class="input" name="title" placeholder="Ví dụ: Chuẩn bị tài liệu sự kiện" required maxlength="100">`)}
        ${label("Sự kiện liên quan", `<select class="select" name="eventId" required>${events.map((event) => `<option value="${escapeHtml(event.id)}" ${event.id === defaultEvent ? "selected" : ""}>${escapeHtml(event.name)}</option>`).join("")}</select>`)}
        <div class="grid-12 form-grid"><div class="span-6">${label("Ban phụ trách", `<select class="select" name="team" required>${teams.map((team) => `<option value="${escapeHtml(team)}">${escapeHtml(team)}</option>`).join("")}</select>`)}</div><div class="span-6">${label("Người phụ trách", `<select class="select" name="assignee" required>${members.filter((member) => member.status === "active").map((member) => `<option value="${escapeHtml(member.name)}">${escapeHtml(member.name)}</option>`).join("")}</select>`)}</div></div>
        <div class="grid-12 form-grid"><div class="span-6">${label("Hạn hoàn thành", `<input class="input" name="deadline" type="datetime-local" required>`)} </div><div class="span-6">${label("Mức ưu tiên", `<select class="select" name="priority"><option>Vừa</option><option>Cao</option><option>Thấp</option></select>`)}</div></div>
        ${label("Mô tả ngắn", `<textarea class="textarea" name="description" rows="3" placeholder="Mô tả đầu ra mong muốn (không bắt buộc)" maxlength="300"></textarea>`)}
        <div class="form-hint">${badge("DỮ LIỆU MẪU", "neutral")} Nhiệm vụ sẽ chỉ lưu trong phiên xem trước.</div>
      </form>`,
      footer: `<button type="button" class="btn btn-ghost" data-modal-cancel>Hủy</button><button type="submit" form="preview-task-form" class="btn btn-primary">${icon("plus")} Tạo nhiệm vụ</button>`,
      onMount: (dialog) => {
        closeModal(dialog);
        const form = dialog.querySelector("#preview-task-form");
        form?.addEventListener("submit", (event) => {
          event.preventDefault();
          if (!form.reportValidity()) return;
          const data = new FormData(form);
          const deadline = new Date(String(data.get("deadline")));
          if (deadline < new Date("2026-10-12T00:00:00")) { UI.toast("Vui lòng chọn hạn hoàn thành từ ngày hôm nay trở đi."); return; }
          tasks.unshift({
            id: `t${String(nextTaskId++).padStart(2, "0")}`, title: String(data.get("title")).trim(), eventId: String(data.get("eventId")), team: String(data.get("team")),
            assignee: String(data.get("assignee")), deadline: deadline.toISOString(), status: "dang_lam", priority: String(data.get("priority")), description: String(data.get("description") || "").trim()
          });
          UI.closeModal();
          UI.toast("Bản demo: đã thêm nhiệm vụ mẫu.");
          if (returnKey === "event-detail") { detailTab = "tasks"; refresh(root, "event-detail"); }
          else refresh(root, "tasks");
        });
      }
    });
  }

  window.previewScreens = Object.assign(window.previewScreens || {}, {
    dashboard: dashboardScreen,
    members: membersScreen,
    events: eventsScreen,
    "event-detail": eventDetailScreen,
    tasks: tasksScreen
  });
})();
