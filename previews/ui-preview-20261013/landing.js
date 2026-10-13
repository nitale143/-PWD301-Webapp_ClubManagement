(() => {
  "use strict";

  const UI = window.UI;
  const icon = (name) => UI.icon(name);

  const landingScreen = {
    title: "FIA · Cộng đồng an toàn thông tin",
    subtitle: "Cùng học, thực hành và xây dựng một không gian số an toàn hơn.",
    render: () => `
      <div class="reference-landing" id="landing-top">
        <header class="rl-header">
          <div class="rl-header-inner">
            <a class="rl-brand" href="#landing-top" data-landing-anchor aria-label="FIA — về đầu trang">
              <img class="fia-header-logo" src="assets/fia-club-logo.png" alt="">
              <span class="rl-brand-copy"><strong>FIA</strong><small>INFORMATION ASSURANCE</small></span>
            </a>
            <nav class="rl-nav" aria-label="Điều hướng trang giới thiệu">
              <a href="#rl-features" data-landing-anchor>Tính năng</a>
              <a href="#rl-activities" data-landing-anchor>Hoạt động</a>
              <a href="#rl-faq" data-landing-anchor>Hỏi đáp</a>
            </nav>
            <div class="rl-header-actions">
              <span class="rl-preview-chip"><span></span> PREVIEW · DỮ LIỆU MẪU</span>
              <a class="rl-login" href="#login" data-route="login">Đăng nhập</a>
              <a class="rl-button rl-button-small" href="#dashboard" data-route="dashboard">Vào workspace ${icon("arrow")}</a>
            </div>
            <a class="rl-mobile-workspace" href="#dashboard" data-route="dashboard" aria-label="Vào workspace">${icon("arrow")}</a>
          </div>
        </header>

        <div class="rl-main">
          <section class="rl-hero" aria-labelledby="rl-hero-title">
            <div class="rl-hero-inner rl-container">
              <div class="rl-hero-copy">
                <p class="rl-kicker"><span class="rl-kicker-line"></span> CÂU LẠC BỘ AN TOÀN THÔNG TIN · ĐẠI HỌC FPT</p>
                <h1 id="rl-hero-title">An toàn số,<br>vững vàng <em>cùng nhau.</em></h1>
                <p class="rl-hero-lede">FIA là nơi sinh viên cùng học về an toàn thông tin, rèn kỹ năng qua thực hành và kết nối với những người cũng tò mò về thế giới số.</p>
                <div class="rl-hero-actions">
                  <a class="rl-button" href="#register" data-route="register">Tham gia cùng FIA ${icon("arrow")}</a>
                  <a class="rl-text-link" href="#rl-workspace" data-landing-anchor>Xem không gian làm việc <span>${icon("arrow")}</span></a>
                </div>
                <div class="rl-hero-note"><span class="rl-note-mark">↳</span><span>Một cộng đồng sinh viên. Nhiều cách để bắt đầu.</span></div>
              </div>

              <div class="rl-hero-visual" aria-label="Minh họa workspace quản lý hoạt động FIA" role="img">
                <div class="rl-dot-field" aria-hidden="true"></div>
                <div class="rl-orb-halo" aria-hidden="true"><img src="assets/reference-orb.png" alt=""></div>
                <div class="rl-orbit rl-orbit-one" aria-hidden="true"></div>
                <div class="rl-orbit rl-orbit-two" aria-hidden="true"></div>
                <div class="rl-float-label rl-float-top"><span class="rl-float-icon">${icon("shield")}</span><span><strong>Học cùng nhau</strong><small>Thực hành có định hướng</small></span></div>
                <div class="rl-workspace-window">
                  <div class="rl-window-bar"><span class="rl-window-dots"><i></i><i></i><i></i></span><span>FIA WORKSPACE</span><span class="rl-window-status"><i></i> ĐANG HOẠT ĐỘNG</span></div>
                  <div class="rl-window-content">
                    <aside class="rl-window-sidebar" aria-hidden="true">
                      <span class="rl-window-logo">F<span>.</span></span>
                      <span class="rl-window-side-icon is-current">${icon("grid")}</span>
                      <span class="rl-window-side-icon">${icon("calendar")}</span>
                      <span class="rl-window-side-icon">${icon("users")}</span>
                      <span class="rl-window-side-icon">${icon("briefcase")}</span>
                    </aside>
                    <div class="rl-window-dashboard">
                      <div class="rl-window-greeting"><span><small>FIA · KHÔNG GIAN CÂU LẠC BỘ</small><strong>Chào bạn, Minh Anh</strong></span><span class="rl-user-mark">MA</span></div>
                      <div class="rl-window-section-title"><span><small>ĐIỀU ĐANG DIỄN RA</small><strong>Hoạt động sắp tới</strong></span><span class="rl-window-link">Xem lịch ${icon("arrow")}</span></div>
                      <article class="rl-event-preview">
                        <span class="rl-event-date"><strong>18</strong><small>THG 10</small></span>
                        <span class="rl-event-preview-copy"><small>SỰ KIỆN CỘNG ĐỒNG</small><strong>Ngày hội Chào Tân sinh viên FIA</strong><span>${icon("location")} Đại học FPT</span></span>
                        <span class="rl-event-arrow">${icon("arrow")}</span>
                      </article>
                      <div class="rl-window-section-title rl-window-task-title"><span><small>CÙNG CHUẨN BỊ</small><strong>Nhịp làm việc</strong></span><span class="rl-task-count">CÔNG VIỆC</span></div>
                      <div class="rl-window-task"><span class="rl-task-check">${icon("check")}</span><span><strong>Hoàn thiện kịch bản khai mạc</strong><small>Ban Nội dung · Gắn với sự kiện</small></span><span class="rl-task-state">ĐANG PHỐI HỢP</span></div>
                    </div>
                  </div>
                  <div class="rl-window-bottom"><span><i></i> Tất cả nội dung đều là dữ liệu minh họa</span><span>FIA · 2026</span></div>
                </div>
                <div class="rl-float-label rl-float-bottom"><span class="rl-float-icon rl-float-pink">${icon("calendar")}</span><span><small>HOẠT ĐỘNG TIẾP THEO</small><strong>Ngày hội FIA <b>· 18.10</b></strong></span></div>
              </div>
            </div>
            <div class="rl-hero-bottom rl-container"><span>HỌC TỪ CƠ BẢN</span><span class="rl-bottom-rule"></span><span>THỬ QUA THỰC HÀNH</span><span class="rl-bottom-rule"></span><span>TRƯỞNG THÀNH CÙNG CỘNG ĐỒNG</span><a href="#rl-topics" data-landing-anchor aria-label="Cuộn xuống khám phá">${icon("arrow")}</a></div>
          </section>

          <section class="rl-topics" id="rl-topics" aria-label="Các chủ đề của câu lạc bộ">
            <div class="rl-container rl-topics-inner"><span class="rl-topics-label">CÙNG KHÁM PHÁ</span><span>CTF <i>✳</i></span><span>CYBERSECURITY <i>✳</i></span><span>SECURITY RESEARCH <i>✳</i></span><span>WORKSHOP <i>✳</i></span><span>COMMUNITY <i>✳</i></span></div>
          </section>

          <section class="rl-section rl-features" id="rl-features" aria-labelledby="rl-features-title">
            <div class="rl-section-heading">
              <div><p class="rl-kicker">KHÔNG GIAN ĐỂ BẮT ĐẦU</p><h2 id="rl-features-title">Tò mò là đủ.<br><em>Cùng nhau đi xa hơn.</em></h2></div>
              <p>Không cần biết hết mọi thứ từ trước. FIA tạo không gian để bạn đặt câu hỏi, học bằng cách làm và tìm thấy những người đồng hành.</p>
            </div>
            <div class="rl-feature-grid">
              <article class="rl-feature-card"><span class="rl-feature-index">01</span><span class="rl-feature-icon">${icon("users")}</span><h3>Học trong cộng đồng</h3><p>Trao đổi kiến thức, chia sẻ điều vừa khám phá và cùng tháo gỡ những câu hỏi về an toàn thông tin.</p><a href="#register" data-route="register">Tìm người đồng hành ${icon("arrow")}</a></article>
              <article class="rl-feature-card rl-feature-card-accent"><span class="rl-feature-index">02</span><span class="rl-feature-icon">${icon("shield")}</span><h3>Thử bằng thực hành</h3><p>Khám phá CTF, workshop và các hoạt động chuyên môn trong nhịp độ phù hợp với hành trình của bạn.</p><a href="#rl-activities" data-landing-anchor>Xem hoạt động ${icon("arrow")}</a></article>
              <article class="rl-feature-card"><span class="rl-feature-index">03</span><span class="rl-feature-icon">${icon("grid")}</span><h3>Cùng vận hành FIA</h3><p>Một workspace chung giúp câu lạc bộ theo dõi sự kiện, đầu việc và những việc cần phối hợp.</p><a href="#dashboard" data-route="dashboard">Mở workspace ${icon("arrow")}</a></article>
            </div>
          </section>

          <section class="rl-workspace-section" id="rl-workspace" aria-labelledby="rl-workspace-title">
            <div class="rl-section rl-workspace-grid">
              <div class="rl-workspace-art" aria-hidden="true">
                <div class="rl-workspace-glow"></div>
                <div class="rl-workspace-card rl-workspace-card-back"><span class="rl-card-cap">FIA / EVENT FLOW</span><div class="rl-flow-line"><i></i><span>Ý tưởng hoạt động</span></div><div class="rl-flow-line"><i></i><span>Phân công phối hợp</span></div><div class="rl-flow-line"><i></i><span>Cùng nhìn lại</span></div><span class="rl-flow-connector"></span></div>
                <div class="rl-workspace-card rl-workspace-card-front"><div class="rl-card-topline"><span><small>FIA WORKSPACE</small><strong>Một nơi để phối hợp</strong></span><span class="rl-card-mark">${icon("grid")}</span></div><div class="rl-progress-row"><span class="rl-progress-symbol">${icon("calendar")}</span><span><strong>Sự kiện</strong><small>Lịch hoạt động và chi tiết chương trình</small></span><span class="rl-progress-arrow">${icon("arrow")}</span></div><div class="rl-progress-row"><span class="rl-progress-symbol rl-progress-pink">${icon("briefcase")}</span><span><strong>Công việc</strong><small>Đầu việc theo nhóm và sự kiện</small></span><span class="rl-progress-arrow">${icon("arrow")}</span></div><div class="rl-progress-row"><span class="rl-progress-symbol rl-progress-violet">${icon("users")}</span><span><strong>Cộng đồng</strong><small>Vai trò và hồ sơ thành viên</small></span><span class="rl-progress-arrow">${icon("arrow")}</span></div><div class="rl-card-foot"><span><i></i> Tất cả trong cùng một không gian</span><span>PREVIEW</span></div></div>
                <span class="rl-art-orbit-dot rl-art-orbit-dot-one"></span><span class="rl-art-orbit-dot rl-art-orbit-dot-two"></span>
              </div>
              <div class="rl-workspace-copy"><p class="rl-kicker">TỪ Ý TƯỞNG ĐẾN HOẠT ĐỘNG</p><h2 id="rl-workspace-title">Ít phân tán hơn.<br><em>Nhiều kết nối hơn.</em></h2><p>Workspace FIA gom những nhịp phối hợp thường ngày vào một chỗ: theo dõi hoạt động, làm việc cùng các ban và giữ mọi người trên cùng một trang.</p><ul class="rl-check-list"><li><span>${icon("check")}</span>Lịch sự kiện và thông tin chương trình</li><li><span>${icon("check")}</span>Đầu việc, người phụ trách và trạng thái</li><li><span>${icon("check")}</span>Thành viên, vai trò và vận hành câu lạc bộ</li></ul><a class="rl-button" href="#dashboard" data-route="dashboard">Khám phá workspace ${icon("arrow")}</a></div>
            </div>
          </section>

          <section class="rl-section rl-activities" id="rl-activities" aria-labelledby="rl-activities-title">
            <div class="rl-section-heading rl-events-heading"><div><p class="rl-kicker">LỊCH HOẠT ĐỘNG</p><h2 id="rl-activities-title">Sắp tới tại <em>FIA.</em></h2></div><a class="rl-text-link" href="#events" data-route="events">Xem tất cả sự kiện <span>${icon("arrow")}</span></a></div>
            <div class="rl-event-grid">
              <article class="rl-public-event"><div class="rl-public-event-art rl-event-art-coral"><span class="rl-event-art-label">FIA <b>· COMMUNITY</b></span><span class="rl-event-art-glyph">${icon("users")}</span><span class="rl-event-art-orbit"></span></div><div class="rl-public-event-body"><div class="rl-event-meta"><span>SỰ KIỆN CỘNG ĐỒNG</span><span>18 THG 10, 2026</span></div><h3>Ngày hội Chào Tân sinh viên FIA</h3><p>Gặp gỡ cộng đồng và khám phá các hoạt động của câu lạc bộ.</p><a href="#event-detail" data-route="event-detail">Xem chi tiết ${icon("arrow")}</a></div></article>
              <article class="rl-public-event"><div class="rl-public-event-art rl-event-art-purple"><span class="rl-event-art-label">FIA <b>· WORKSHOP</b></span><span class="rl-event-art-glyph">${icon("shield")}</span><span class="rl-event-art-orbit"></span></div><div class="rl-public-event-body"><div class="rl-event-meta"><span>WORKSHOP</span><span>22 THG 10, 2026</span></div><h3>An toàn thông tin cá nhân</h3><p>Cùng tìm hiểu các thói quen và nguyên tắc bảo vệ mình trên mạng.</p><a href="#events" data-route="events">Khám phá sự kiện ${icon("arrow")}</a></div></article>
              <article class="rl-public-event rl-event-cta"><div class="rl-event-cta-mark">${icon("sparkles")}</div><p class="rl-kicker">MỘT BƯỚC NHỎ ĐỂ BẮT ĐẦU</p><h3>Hoạt động tiếp theo có thể là nơi bạn tìm thấy cộng đồng của mình.</h3><a class="rl-button rl-button-outline" href="#events" data-route="events">Mở lịch FIA ${icon("arrow")}</a></article>
            </div>
            <p class="rl-data-note">Lịch hoạt động hiển thị dữ liệu mẫu trong bản preview.</p>
          </section>

          <section class="rl-faq-section" id="rl-faq" aria-labelledby="rl-faq-title">
            <div class="rl-section rl-faq-grid"><div><p class="rl-kicker">CÂU HỎI THƯỜNG GẶP</p><h2 id="rl-faq-title">Bạn đang<br><em>băn khoăn điều gì?</em></h2><p class="rl-faq-aside">Nếu câu hỏi của bạn chưa có ở đây, hãy ghé workspace để tìm hiểu thêm về FIA.</p><a class="rl-text-link" href="#dashboard" data-route="dashboard">Vào workspace <span>${icon("arrow")}</span></a></div><div class="rl-faq-list">
              <details><summary>Chưa có kinh nghiệm về an toàn thông tin có tham gia được không?<span>${icon("plus")}</span></summary><p>Có. Câu lạc bộ là nơi để bắt đầu học và thực hành cùng nhau. Bạn không cần biết hết mọi thứ trước khi tham gia.</p></details>
              <details><summary>FIA thường có những hoạt động nào?<span>${icon("plus")}</span></summary><p>Các hoạt động mẫu trong workspace gồm workshop, sinh hoạt chuyên môn, hoạt động cộng đồng và thử thách CTF.</p></details>
              <details><summary>Làm thế nào để biết lịch và tham gia một hoạt động?<span>${icon("plus")}</span></summary><p>Mở mục Sự kiện trong workspace để xem thông tin chương trình và luồng đăng ký mẫu.</p></details>
              <details><summary>Đây có phải website đăng ký chính thức không?<span>${icon("plus")}</span></summary><p>Đây là bản xem trước giao diện. Các thao tác đăng nhập, đăng ký và nội dung sự kiện dẫn tới những màn hình demo, chưa kết nối hệ thống thật.</p></details>
            </div></div>
          </section>

          <section class="rl-final-cta" aria-labelledby="rl-final-title"><div class="rl-final-orb" aria-hidden="true"></div><div class="rl-final-inner rl-container"><p class="rl-kicker">CỘNG ĐỒNG FIA ĐANG CHỜ BẠN</p><h2 id="rl-final-title">Cùng nhau làm<br><em>không gian số an toàn hơn.</em></h2><p>Bắt đầu bằng một câu hỏi, một hoạt động, hay một người bạn mới.</p><a class="rl-button" href="#register" data-route="register">Tìm hiểu cách tham gia ${icon("arrow")}</a></div></section>
        </div>

        <footer class="fia-footer" aria-label="Thông tin và liên kết FIA">
          <div class="rl-container">
            <div class="fia-footer-top">
              <div class="fia-footer-about">
                <a class="fia-footer-logo" href="#landing-top" data-landing-anchor aria-label="FIA — về đầu trang"><img class="fia-footer-emblem" src="assets/fia-club-logo.png" alt=""><span class="fia-footer-wordmark">FIA<span>.</span></span></a>
                <p>Cùng học, cùng thực hành.<br>Cùng xây dựng không gian số an toàn hơn. FIA kết nối những người trẻ đam mê an toàn thông tin tại Đại học FPT.</p>
                <div class="fia-footer-socials"><button type="button" data-footer-info="facebook" aria-label="Facebook của FIA"><svg viewBox="0 0 24 24" aria-hidden="true" fill="currentColor"><path d="M14 8h3V4h-3c-4 0-5 2-5 5v3H6v4h3v6h4v-6h3l1-4h-4V9c0-1 0-1 1-1Z"/></svg></button><button type="button" data-footer-info="instagram" aria-label="Instagram của FIA"><svg viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="2"><rect x="4" y="4" width="16" height="16" rx="5"/><circle cx="12" cy="12" r="4"/><circle cx="17" cy="7" r="1" fill="currentColor" stroke="none"/></svg></button></div>
              </div>
              <nav class="fia-footer-column" aria-label="Liên kết cộng đồng"><h3>CỘNG ĐỒNG</h3><a href="#rl-features" data-landing-anchor>Về FIA</a><a href="#rl-activities" data-landing-anchor>Hoạt động</a><a href="#events" data-route="events">Lịch sự kiện</a><a href="#rl-faq" data-landing-anchor>Câu hỏi thường gặp</a></nav>
              <nav class="fia-footer-column" aria-label="Liên kết workspace"><h3>WORKSPACE</h3><a href="#dashboard" data-route="dashboard">Tổng quan</a><a href="#members" data-route="members">Thành viên</a><a href="#tasks" data-route="tasks">Công việc</a><a href="#funds" data-route="funds">Quỹ câu lạc bộ</a><a href="#ai" data-route="ai">Trợ lý AI</a></nav>
              <nav class="fia-footer-column" aria-label="Liên kết tham gia"><h3>THAM GIA FIA</h3><a href="#register" data-route="register">Đăng ký thành viên</a><a href="#login" data-route="login">Đăng nhập</a><a href="#profile" data-route="profile">Hồ sơ cá nhân</a><a href="#approvals" data-route="approvals">Ban điều hành</a></nav>
            </div>
            <div class="fia-footer-bottom"><div class="fia-footer-copyright"><span>© 2026 FIA · Bản xem trước.</span><span>${icon("location")} Đại học FPT · Information Assurance</span></div><div class="fia-footer-meta"><button type="button" data-footer-info="privacy">Quyền riêng tư</button><button type="button" data-footer-info="preview">Thông tin preview</button></div></div>
          </div>
          <a class="fia-footer-up" href="#landing-top" data-landing-anchor aria-label="Về đầu trang">${icon("arrow")}</a>
        </footer>
      </div>`,
    bind: (root) => {
      root.querySelectorAll('[data-footer-info]').forEach(button => button.addEventListener('click', () => {
        const type = button.dataset.footerInfo;
        const titles = {facebook:'Facebook FIA',instagram:'Instagram FIA',privacy:'Quyền riêng tư trong preview',preview:'Về bản xem trước'};
        const text = type === 'facebook' || type === 'instagram'
          ? 'Liên kết chính thức của FIA chưa được cung cấp. Đây là vị trí minh họa; chưa mở mạng xã hội bên ngoài.'
          : 'Đây là bản thiết kế dùng dữ liệu mẫu. Các biểu mẫu chỉ minh họa giao diện, không gọi API AI, gửi email hay ghi dữ liệu CLB thật.';
        UI.modal({title:titles[type],body:`<p>${text}</p>`,footer:'<button class="btn btn-secondary" data-modal-close>Đóng</button>'});
      }));
      root.querySelectorAll("[data-landing-anchor]").forEach((link) => {
        link.addEventListener("click", (event) => {
          event.preventDefault();
          const target = root.querySelector(link.getAttribute("href"));
          if (!target) return;
          const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
          target.scrollIntoView({ behavior: reducedMotion ? "auto" : "smooth", block: "start" });
        });
      });
    }
  };

  window.previewScreens = Object.assign(window.previewScreens || {}, { landing: landingScreen });
})();
