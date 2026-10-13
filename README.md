# CLB Manager

Ứng dụng web nội bộ để quản lý thành viên, sự kiện, công việc và quỹ câu lạc bộ. Dự án dùng **Python/Flask**, giao diện Jinja2 và SQLite mặc định. Trợ lý AI hỗ trợ tra cứu, lập đề xuất; khi chưa có API key, ứng dụng dùng chế độ quy tắc để nhóm vẫn chạy thử được luồng nghiệp vụ.

> Dự án hiện phù hợp để học tập và demo. Xem [Lưu ý trước khi triển khai thật](#lưu-ý-trước-khi-triển-khai-thật) nếu muốn dùng với dữ liệu thật.

## Bản thiết kế mới và backup web cũ

- Ứng dụng Flask ở thư mục gốc đã dùng giao diện FIA xanh lá/đen/trắng: landing công khai, sidebar theo vai trò, màn hình nghiệp vụ và AI Agent dùng dữ liệu, đăng nhập, lịch sử chat, tiến trình xử lý và các bước duyệt thật. Không dùng phiên đăng nhập demo hoặc câu trả lời mô phỏng của preview.
- Bố cục các màn đã được chuyển theo bản preview đã duyệt (không chỉ đổi theme): hero/dashboard, thẻ số liệu, bảng trong card, tab quỹ, lưới sự kiện, task kanban/list, hồ sơ, phê duyệt và các form/dialog. Các tệp `preview-*.css` là bộ thiết kế gốc dùng chung; `parity-*.css/js` nối với HTML và thao tác thật. Số liệu, trạng thái trống và các nút theo quyền có thể khác mẫu vì dùng database thật.
- Trang `/tasks` dùng dữ liệu thật trong phạm vi quyền: thành viên chỉ xem task của mình, trưởng ban xem task ban phụ trách và của mình, CN/PCN xem toàn bộ.
- Trang sự kiện thật có tab FIA và CTFtime. BDH bấm **Tạo sự kiện FIA** để lưu sự kiện tham gia CTF vào database; hệ thống xác minh thông tin từ nguồn trên server, giữ link nguồn, chuyển giờ theo múi giờ CLB và dùng mã duy nhất để chống trùng. Thao tác cần đăng nhập, quyền BDH và CSRF. Đây không phải đăng ký đội thi trên CTFtime.
- [Các bản UI/UX preview cũ](previews/README.md) được giữ để đối chiếu thiết kế. Dữ liệu CLB và các thao tác trong các thư mục này vẫn chỉ là demo, khác với ứng dụng Flask thật.
- [Backup mã nguồn web cũ](backups/club-management-before-ui-20261012-105648/README.md): snapshot trước khi thiết kế lại UI. Bản trên Git đã loại cấu hình bí mật, database, ảnh tải lên, Git nội bộ và tài liệu giải thích riêng. Backup đầy đủ vẫn lưu riêng ở máy chủ dự án, không đưa lên Git.

Các bản preview chạy riêng bằng `python3 preview_server.py --port 5082`; ứng dụng Flask thật tiếp tục dùng hướng dẫn dưới đây. Không triển khai preview thay cho ứng dụng thật.

### Mở giao diện mới chạy thật

```bash
cd /home/phanquang/my-project
source /home/phanquang/.virtualenvs/club-manager-group/bin/activate
SCHEDULER_ENABLED=false flask --app run.py run --host 0.0.0.0 --port 5000 --no-reload
```

Mở `http://127.0.0.1:5000` và đăng nhập bằng tài khoản CLB thật. Đường dẫn trên là môi trường Ubuntu của máy phát triển; trên máy khác dùng thư mục clone và virtualenv của mình. Với WSL, nếu Windows không truy cập localhost được, dùng IP Ubuntu từ `hostname -I`. Chỉ dùng development server trong môi trường tin cậy, không mở ra Internet.

`SCHEDULER_ENABLED=false` tắt lịch gửi mail nền khi thử giao diện; mặc định vẫn bật như trước. AI và SMTP đọc cấu hình bí mật của server, không đưa API key hoặc mật khẩu mail ra trình duyệt/Git. Truy vấn xác minh có thể trả lời bằng quy tắc; tác vụ dùng model phụ thuộc cấu hình provider, key, hạn mức và kết nối. Nháp mail/đề xuất vẫn phải qua quyền duyệt hiện có.

CTFtime sử dụng lịch Google công khai được nhúng trên trang calendar, không dùng JSON API bị giới hạn mục đích. Cache/lỗi nguồn được thông báo rõ. Xác nhận điều khoản tái sử dụng trước khi phát hành website công khai.

Kiểm tra backend bằng `python -m unittest discover -s tests -q` (database tạm). Để kiểm tra giao diện bằng trình duyệt, chạy `PYTHONPATH=. python tests/ui_fixture_server.py`, rồi chạy `node tests/test_live_ui.cjs` trong môi trường có Playwright và Edge; server test ở cổng 5090, tài khoản và database hoàn toàn tạm, không dùng dữ liệu CLB.

`node tests/test_visual_parity.cjs` kiểm tra 14 màn desktop/mobile, tab và dialog quỹ, quyền thanh toán thành viên, ảnh chụp và tài nguyên. Có thể cấu hình `FIA_SCREENSHOTS` cho thư mục ảnh test trên máy mình. Script này chỉ dùng server test ở cổng 5090, không chạy với database CLB thật.

Kiểm tra kết nối model thật tùy chọn: `PYTHONPATH=. python tests/provider_smoke.py`. Lệnh này dùng key riêng ở `.env` và có thể tính phí một yêu cầu ngắn; không gửi dữ liệu thành viên và không ghi database CLB. Không dùng các tài khoản test cho hệ thống thật.

## Chạy nhanh trên Ubuntu

Yêu cầu: Python 3, `venv` và Git. Nếu Ubuntu báo thiếu `venv`, cài thêm gói `python3-venv`.

```bash
git clone https://github.com/nitale143/-PWD301-Webapp_ClubManagement.git clb-webapp
cd clb-webapp

python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt

cp .env.example .env
```

Mở `.env`, thay `SECRET_KEY` bằng một chuỗi bí mật đủ dài. Có thể tạo chuỗi bằng:

```bash
python -c 'import secrets; print(secrets.token_hex(32))'
```

Khởi tạo dữ liệu và tạo tài khoản Chủ nhiệm đầu tiên:

```bash
flask --app run.py init-db
flask --app run.py create-cn
```

Sau đó chạy ứng dụng:

```bash
flask --app run.py run --host 127.0.0.1 --port 5000 --no-reload
```

Mở <http://127.0.0.1:5000>. Trang gốc chuyển tới trang đăng nhập. Dùng MSSV và mật khẩu vừa tạo bằng `create-cn`. Lệnh này chỉ cần chạy **một lần** cho database mới; tài khoản bootstrap có thông tin liên hệ mẫu, cần kiểm tra lại trước khi bật gửi email thật.

Database SQLite mặc định nằm tại `instance/clb.db`. Nếu đã có dữ liệu, **không xóa file này và không tạo lại tài khoản Chủ nhiệm**.

## Chức năng hiện có

| Nhóm | Chức năng |
| --- | --- |
| Tài khoản, thành viên | Đăng ký bằng MSSV, chờ BDH duyệt; tìm kiếm/lọc/sắp xếp thành viên, xem hồ sơ, xuất Excel, tải ảnh đại diện. |
| Phân quyền | Vai trò Chủ nhiệm, Phó chủ nhiệm, Trưởng ban, Thư ký/Thủ quỹ và Thành viên; chỉ định vai trò, nhượng quyền, giới hạn dữ liệu theo quyền. |
| Sự kiện, công việc | Tạo sự kiện, đặt sức chứa/hạn đăng ký, đăng ký hoặc vào danh sách chờ, hủy đăng ký, điểm danh QR hoặc thủ công, đánh giá; giao task và duyệt sản phẩm đã nộp. |
| Quỹ | Tạo khoản thu, ghi nhận tiền thành viên gửi, Thủ quỹ xác nhận/từ chối, tính đã đóng/còn thiếu, miễn/giảm qua API và xuất báo cáo. Phần quỹ theo kỳ cũ vẫn hiển thị riêng. |
| Trợ lý AI | Chat/API dùng chung luồng, lưu cuộc trò chuyện riêng để mở lại, đổi tên, lưu trữ và khôi phục; tải tối đa 40 tin nhắn/trang, ngữ cảnh model giới hạn 6 tin của chat đang chọn. Câu trả lời số liệu lấy trực tiếp từ database; đề xuất sự kiện/chia task và tạo nháp email để BDH duyệt trước khi thực hiện. Nhật ký token và giới hạn lượt gọi giúp kiểm soát tài khoản AI chung. |
| Thông báo | Email khi duyệt thành viên, giao/duyệt task; nhắc deadline và kỳ quỹ qua lịch chạy nền. Mặc định chỉ in email ra terminal. |

### Luồng sử dụng cơ bản

1. Thành viên đăng ký tại `/register`; tài khoản ở trạng thái chờ.
2. Ban điều hành (BDH) duyệt hoặc từ chối tại trang **BDH**. Người được duyệt mới sử dụng các trang nội bộ.
3. BDH tạo sự kiện và phân công task. Thành viên đăng ký, điểm danh, nộp sản phẩm và đánh giá sự kiện theo trạng thái cho phép.
4. Thủ quỹ tạo khoản thu; thành viên gửi thông tin đóng quỹ; Thủ quỹ xác nhận để cập nhật số dư.
5. BDH có thể yêu cầu AI lập đề xuất qua form hoặc chat. Ví dụ: `Đề xuất sự kiện: Workshop bảo mật | 2026-11-01 09:00 | 2026-11-01 11:00 | 1` (mã ban cuối là tùy chọn), hoặc `Chia task: 12 | 1 | 2026-11-01 08:00 | Chuẩn bị tài liệu; Kiểm tra thiết bị | python, mạng` (kỹ năng cuối là tùy chọn). Chat chỉ tạo **đề xuất**, không tạo sự kiện/task thật trước khi BDH bấm **Duyệt và áp dụng**. Thành viên có thể cập nhật kỹ năng, mức nhận task và ngày tạm ngừng nhận ở trang hồ sơ; người không có hồ sơ vẫn được tính mức mặc định 3 task đang làm.
6. Chủ nhiệm/Phó chủ nhiệm có thể lưu và sửa **mail mẫu dùng chung** ngay tại trang AI. Mẫu gồm tên, tiêu đề, nội dung và có thể dùng `{{ten}}`, `{{mssv}}`, `{{email}}`; mẫu chứa `{{mssv}}` chỉ dùng cho thành viên CLB. BDH có thể nói tự nhiên, ví dụ `Gửi mail mẫu nhắc đóng quỹ cho Nguyễn Văn A` hoặc `Dùng mẫu nhắc đóng quỹ gửi cho SV123`; hệ thống tìm tên mẫu/người nhận, điền biến và tạo bản nháp. Nếu thiếu hoặc trùng người nhận/mẫu, AI hỏi lại; không đoán rồi gửi. Có thể tạm ngừng mẫu mà không xóa bản nháp cũ.
7. Cách nhập cũ vẫn dùng được: `Gửi mail cho <MSSV hoặc họ tên>: <mục đích/nội dung>`. Với địa chỉ ngoài danh sách thành viên, Chủ nhiệm hoặc Phó chủ nhiệm có thể nhập `Gửi mail <địa chỉ email>: <mục đích/nội dung>`. Chatbot chỉ tạo bản nháp, **chưa gửi**. Người có quyền kiểm tra địa chỉ nhận, sửa tiêu đề/nội dung nếu cần, rồi bấm **Duyệt và gửi** hoặc **Từ chối**. Nếu gửi dở do tiến trình bị ngắt, BDH phải kiểm tra hộp thư đã gửi rồi đối soát thủ công; hệ thống không tự gửi lại. Người nhận trong CLB có tên trùng cần chọn bằng MSSV; nháp gửi tới email ngoài CLB chỉ Chủ nhiệm/Phó chủ nhiệm được duyệt.
8. BDH có thể nói tự nhiên, ví dụ `Tạo sự kiện Workshop bảo mật ngày 15/11/2026 09:00 đến 15/11/2026 11:00` hoặc `Giao task thiết kế poster cho SV123 trong sự kiện Workshop bảo mật ban Truyền thông hạn 14/11/2026 18:00`. Nếu thiếu sự kiện, ban, giờ hoặc tên việc, Agent hỏi lại; câu trả lời bổ sung được giữ tối đa 30 phút (`hủy` để bỏ). Mỗi task gắn **một ban**; yêu cầu mơ hồ như `cho 3 ban` không được tự chia hoặc thực thi. Sau khi đủ dữ kiện, Agent chỉ tạo đề xuất cho BDH duyệt; câu tự nhiên không đưa trực tiếp dữ liệu vào bảng sự kiện/task.
9. Trang Home và AI hiển thị **việc cần xử lý hôm nay** theo quyền của BDH khi mở trang. Chat nhận `Hôm nay cần xử lý gì?`, `Báo cáo tuần này`, `Báo cáo tháng này`. Báo cáo nêu khoảng ngày, phạm vi quyền và ID bản ghi nguồn. BDH có thể lưu một bản xem trước cố định rồi tải đúng bản đó ra Excel hoặc tạo nháp email gửi tới email hồ sơ của mình; email vẫn cần duyệt. Nếu chức vụ hoặc ban quản lý thay đổi, bản lưu có phạm vi quyền cũ sẽ không còn tải/gửi được. Số thu trong báo cáo chỉ tính `FundPayment` mới đã xác nhận, không cộng luồng quỹ kỳ cũ; task được đếm theo **hạn trong kỳ**, không ngụ ý hoàn thành trong kỳ vì chưa có thời điểm hoàn thành riêng.

Thời gian trong câu tự nhiên có thể đặt trước hoặc sau ngày: `tối 23:00 10/10`, `10/10 lúc 23h`, `23h30 ngày 10/10`, `ngày mai 11 giờ tối`. Nếu chỉ ghi ngày/tháng, hệ thống dùng **năm hiện tại theo giờ CLB**, không tự nhảy sang năm sau; câu trả lời tạo đề xuất nhắc lại ngày, giờ và năm đã hiểu để BDH kiểm tra. Nếu giờ/ngày không hợp lệ hoặc thông tin mâu thuẫn, Agent hỏi lại thay vì đoán. Các cách ghi ISO và ngày/tháng/năm trước đây vẫn dùng được. Việc hiểu thời gian không bỏ qua kiểm tra quyền, người nhận, ban, sự kiện và hạn task; đề xuất vẫn cần duyệt.

### Lịch sử theo cuộc trò chuyện

Trang AI có danh sách chat riêng cho từng tài khoản và nút **Chat mới**. Chat tự đặt tên theo câu hỏi đầu tiên nếu chưa đặt tên; menu **Tùy chọn** cho phép đổi tên hoặc lưu trữ, mục **Đã lưu trữ** cho phép mở lại và khôi phục. Lưu trữ chỉ ẩn khỏi danh sách đang dùng, không xóa dữ liệu. Danh sách tải 20 chat/trang; nội dung tải 40 tin/trang và có liên kết xem cũ hơn/mới hơn, không đưa toàn bộ lịch sử vào trang. Model chỉ nhận tối đa 6 tin của chat đang chọn; yêu cầu đang hỏi bổ sung cũng được tách theo chat. Giới hạn lượt nhắn vẫn tính chung theo tài khoản, không đặt lại khi tạo chat mới.

API `POST /api/v1/assistant` nhận thêm `conversation_id` và trả lại ID này. Client nên luôn gửi ID để các tab độc lập; bỏ ID thì dùng chat đang chọn trong phiên hoặc chat gần nhất (tương thích client cũ). Quản lý chat qua `GET/POST /api/v1/assistant/conversations`, đọc tin qua `GET /api/v1/assistant/conversations/<id>/messages?before=<id>` hoặc `?after=<id>`, đổi tên qua `PATCH /api/v1/assistant/conversations/<id>` với `title`, lưu trữ/khôi phục qua `POST /api/v1/assistant/conversations/<id>/archive` với `archived: true/false`. Các thao tác quản lý chat cần `X-CSRF-Token`; mọi truy cập được kiểm tra chủ sở hữu.

Phân trang giảm lượng tải và bộ nhớ trang, không tự giảm dung lượng SQLite: lịch sử vẫn được giữ để mở lại. Chưa có cơ chế tự xóa tin cũ.

### Độ tin cậy của AI Agent

Chat có JavaScript dùng **vòng lặp model chọn công cụ → backend kiểm tra và chạy → model đọc kết quả**. Mỗi lượt mặc định tối đa 3 lần lập kế hoạch; chỉ có các công cụ tra cứu/chuẩn bị bản nháp được cho phép. Model không được gửi SMTP, duyệt đề xuất hay ghi sự kiện/task thật. Câu trả lời cuối được ghép từ kết quả dịch vụ nghiệp vụ, không lấy phần văn bản model tự bịa làm số liệu. Model vẫn có thể chọn sai công cụ; khi thiếu dữ liệu hoặc phạm vi chưa hỗ trợ, hệ thống hỏi lại/báo giới hạn thay vì đoán.

Có thể hỏi nhiều mảng trong một câu, ví dụ `Tổng đã thu và các sự kiện sắp diễn ra`; các mệnh đề nghiệp vụ rõ ràng được tra cứu riêng. Chưa hỗ trợ mọi cách diễn đạt hoặc mọi bộ lọc: task theo ưu tiên/sự kiện, tổng thu theo kỳ và tình trạng quỹ theo tháng chưa được tự đoán hoặc bỏ bộ lọc. Các yêu cầu chưa hỗ trợ được báo rõ. Nếu quyền/ban quản lý thay đổi giữa lúc model xử lý, dừng lượt đó và yêu cầu gửi lại; kết quả đã lấy bằng quyền cũ không được trả như kết quả mới.

Khung **Tiến trình xử lý** nhận sự kiện trực tiếp từ `POST /ai/stream`: gọi model, chạy công cụ, kiểm tra và hoàn tất. Đây là nhật ký thao tác thực tế, **không phải suy nghĩ nội bộ của model**. Câu trả lời đã kiểm chứng được truyền theo đoạn sau khi lưu; không giả lập thời gian chờ. Nếu model lỗi, JSON không hợp lệ hoặc hết giới hạn sau khi đã tra cứu, giữ kết quả đã kiểm tra và báo lý do dừng; nếu chưa có kết quả hoặc không có key, dùng chế độ quy tắc dự phòng. Câu hỏi được lưu trước khi gọi model; nếu mạng ngắt, tải lại lịch sử và kiểm tra bản nháp trước khi gửi lại, vì ngắt trình duyệt không đảm bảo hủy tác vụ trên server.

`AI_AGENT_ENABLED=false` tắt vòng lặp model, giữ tra cứu quy tắc. API JSON tương thích cũ mặc định vẫn dùng luồng cũ; thêm `"agent": true` vào `POST /api/v1/assistant` để bật Agent và bắt buộc `X-CSRF-Token` cho mọi câu hỏi. Form không JavaScript cũng dùng luồng cũ. Không cần thêm bảng database cho vòng lặp: dùng hội thoại/tin nhắn, audit và thống kê AI hiện có; tiến trình hiển thị trực tiếp, audit chỉ lưu tên bước/công cụ an toàn.

Mặc định `AI_STRICT_FACTS=true`: câu hỏi tra cứu chưa được hỗ trợ không được chuyển cho model đoán dữ liệu. Có thể hỏi `Xem thông tin SV123`, `Task của SV123 đang làm là gì?` hoặc `Tóm tắt dữ liệu của tôi`; hệ thống tra cứu hồ sơ/task hiện tại theo quyền và trả ID nguồn. Câu hỏi lịch sử/ngày chưa hỗ trợ được báo rõ. Nếu đặt `AI_STRICT_FACTS=false`, phần chat sinh tự do được đánh dấu `unverified_draft` và không có cam kết đúng/lặp lại; bản nháp email/sự kiện vẫn cần duyệt trong cả hai chế độ.

Số liệu quỹ, việc trong ngày và báo cáo được tính bằng truy vấn database cố định, sắp xếp có thứ tự và lọc theo quyền; Gemini không được tự tạo con số. Báo cáo lưu bản chụp cùng các dòng nguồn để đối chiếu và giữ nguyên khi dữ liệu thay đổi sau đó. Lệnh tạo/sửa nghiệp vụ cần tham số hợp lệ và BDH duyệt trước khi ghi thật. Nếu dữ liệu thiếu hoặc tên người/ban/sự kiện mơ hồ, Agent hỏi lại thay vì đoán. Kiểm thử tự động so sánh kết quả lặp lại trên cùng dữ liệu và kiểm tra phân quyền.

**Không thể cam kết mọi câu trả lời AI đúng 100% hoặc mọi lần hỏi đều giống từng chữ**: nguồn dữ liệu có thể sai/thay đổi, và câu trả lời sinh tự do của mô hình có thể khác nhau. Cam kết thực tế là các **kết quả nghiệp vụ đã định nghĩa** lặp lại khi cùng câu hỏi, cùng phạm vi quyền, cùng mốc ngày và cùng trạng thái database; với báo cáo đã lưu, bản xuất và nháp email lấy từ đúng bản chụp đó. Câu hỏi ngoài tập truy vấn đã kiểm chứng chỉ nên coi là hỗ trợ, không phải bằng chứng quyết định nghiệp vụ.

Trang Quỹ/Sự kiện và API dùng chung dữ liệu nghiệp vụ mới. Riêng **quỹ theo kỳ kiểu cũ** (`FundPeriod`/`FundDue`/`FundTransaction`) là luồng độc lập, không tự đồng bộ với khoản thu và thanh toán mới (`FundCollection`/`FundPayment`).

## Phân quyền

| Vai trò | Phạm vi chính |
| --- | --- |
| Chủ nhiệm (`CN`) | Quản trị thành viên/vai trò, quản lý sự kiện và quỹ. |
| Phó chủ nhiệm (`PCN`) | Nghiệp vụ BDH và quản lý thành viên; không có quyền Thủ quỹ mặc định. |
| Trưởng ban (`TB`) | Một số nghiệp vụ BDH; quyền quản lý thành viên, task và đề xuất được giới hạn theo ban. |
| Thư ký/Thủ quỹ (`THUKY_THUQUY`) | Nghiệp vụ thu quỹ và các trang được cấp cho vai trò này. |
| Thành viên (`THANH_VIEN`) | Xem dữ liệu được phép, đăng ký sự kiện, nộp task và gửi thanh toán của mình. |

Hệ thống giới hạn số người giữ vai trò BDH: 1 Chủ nhiệm, 2 Phó chủ nhiệm, 3 Trưởng ban và 1 Thư ký/Thủ quỹ. Quyền cụ thể vẫn được kiểm tra tại từng route/service; không nên suy ra quyền chỉ từ việc thấy một nút trên giao diện.

## Cấu hình

Sao chép `.env.example` thành `.env` và chỉnh các giá trị cần thiết. **Không commit `.env` hoặc API key lên Git.**

| Biến | Ý nghĩa |
| --- | --- |
| `SECRET_KEY` | Khóa phiên Flask; bắt buộc thay giá trị mẫu trước khi dùng. |
| `DATABASE_URL` | Đường dẫn kết nối database; bỏ trống để dùng `instance/clb.db`. |
| `APP_TIMEZONE` | Múi giờ sự kiện và task; mặc định `Asia/Bangkok` (UTC+7). |
| `AI_PROVIDER` | `gemini` (mặc định), `anthropic` hoặc `rules`. Thiếu key tương ứng thì dùng chế độ quy tắc. |
| `GEMINI_API_KEY`, `GEMINI_MODEL` | API key Gemini chung do CLB quản lý và tên model (mặc định `gemini-3.5-flash-lite`). |
| `AI_API_KEY`, `AI_MODEL` | API key chung và tên model cho Claude Messages API khi chọn `anthropic`. |
| `AI_MAX_CALLS_PER_MINUTE`, `AI_DAILY_TOKEN_LIMIT`, `AI_CHAT_MESSAGES_PER_MINUTE` | Giới hạn mặc định lần lượt 12 lượt model/phút, 100.000 token/24 giờ và 20 tin chat/phút cho mỗi người. |
| `AI_STRICT_FACTS` | Mặc định `true`: câu hỏi tra cứu không được hỗ trợ nhận thông báo cố định thay vì câu trả lời model chưa kiểm chứng. |
| `AI_AGENT_ENABLED` | Mặc định `true`: chat trực tiếp dùng vòng lặp chọn công cụ khi có provider/key. Không bỏ kiểm tra quyền hoặc bước BDH duyệt. |
| `AI_AGENT_MAX_STEPS`, `AI_AGENT_MAX_SECONDS` | Mặc định 3 bước model và ngân sách 90 giây; bước được chặn trong khoảng 1–5. Ngân sách kiểm tra giữa các bước, không ngắt một lời gọi HTTP đang chạy; timeout/retry của provider vẫn áp dụng. |
| `MAIL_ENABLED` | Mặc định `false`: email chỉ in ra terminal. Đặt `true` khi đã cấu hình SMTP. |
| `MAIL_SERVER`, `MAIL_PORT`, `MAIL_USE_TLS`, `MAIL_USERNAME`, `MAIL_PASSWORD`, `MAIL_DEFAULT_SENDER` | Thông tin máy chủ gửi email. |

Để dùng Gemini, lấy key trong Google AI Studio rồi đặt riêng trong `.env` (không dán key vào mã nguồn hoặc Git):

```dotenv
AI_PROVIDER=gemini
GEMINI_API_KEY=your-private-key
GEMINI_MODEL=gemini-3.5-flash-lite
```

Khởi động lại webapp sau khi đổi `.env`. Không có ô nhập API key riêng cho từng thành viên. Số liệu của các truy vấn đã hỗ trợ được tính trực tiếp bằng code, dù chọn provider nào. Chat Agent có thể tốn thêm lượt model để chọn công cụ; đặt `AI_AGENT_ENABLED=false` nếu cần giảm chi phí. Với `gemini` hoặc `anthropic` và key hợp lệ, model cũng có thể soạn bản nháp có duyệt; nếu tắt `AI_STRICT_FACTS`, luồng chat cũ có thể viết sinh tự do được đánh dấu chưa kiểm chứng. Model nhận dữ kiện theo quyền, không được cấp công cụ tự ghi database; ngữ cảnh hội thoại chỉ gồm các tin người dùng, không lấy câu trả lời AI cũ làm bằng chứng. Danh sách sự kiện sắp tới là dữ liệu công khai trong CLB theo trang Event hiện tại; task của thành viên khác vẫn lọc theo ban của TB. Gemini dùng JSON có schema; backend vẫn kiểm tra tên công cụ, giá trị và quyền trước khi chạy. Khi provider tạm thời quá tải, ứng dụng thử lại một lần; Agent có thể chuyển sang truy vấn quy tắc và báo rõ. Truy vấn database không phụ thuộc kết nối Gemini. Trang AI hiển thị tổng lượt gọi, token và độ trễ 24 giờ, **không tự quy đổi thành chi phí tiền**.

Email duyệt/từ chối thành viên chỉ được gửi thật khi `MAIL_ENABLED=true` và cấu hình SMTP hợp lệ. Nếu SMTP chưa bật hoặc gửi lỗi, trạng thái duyệt vẫn được lưu và BDH sẽ thấy cảnh báo để thông báo thủ công; hãy xác nhận với thành viên trước khi coi thông báo là đã đến nơi. Ví dụ cấu hình:

```dotenv
MAIL_ENABLED=true
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=your-club@example.com
MAIL_PASSWORD=your-smtp-app-password
MAIL_DEFAULT_SENDER=your-club@example.com
```

Lịch chạy nền dùng múi giờ `APP_TIMEZONE`: kiểm tra task sắp tới hạn lúc 07:00 và nhắc BDH về kỳ quỹ sắp kết thúc lúc 07:05. Khi chạy nhiều web worker, mỗi worker có thể khởi động một lịch riêng và gửi email trùng; cần tách scheduler ra khỏi web process trước khi triển khai kiểu đó.

## API và dữ liệu

API JSON có tiền tố `/api/v1`, dùng **phiên đăng nhập web hiện có**. Chưa đăng nhập trả `401`; tài khoản chưa được duyệt hoặc không đủ quyền trả `403`. Các danh sách có `page` và `page_size` (tối đa 100 bản ghi/trang).

| Nhóm | Endpoint tiêu biểu |
| --- | --- |
| Thành viên | `GET/POST /api/v1/members`, `POST /api/v1/members/import`, `GET /api/v1/members/<id>/activity` |
| Quỹ | `GET/POST /api/v1/funds`, `GET /api/v1/funds/<id>/balances`, `POST /api/v1/funds/<id>/payments`, `POST /api/v1/payments/<id>/review` |
| Sự kiện | `GET/POST /api/v1/events`, `POST /api/v1/events/<id>/registrations`, `GET /api/v1/events/<id>/qr.png`, `POST /api/v1/attendance/checkin` |
| AI, báo cáo | `POST /api/v1/assistant`, `GET/POST /api/v1/assistant/proposals`, `GET /api/v1/dashboard`, `GET /api/v1/reports/funds.xlsx` |

Ví dụ body tạo khoản thu (gửi bằng tài khoản Chủ nhiệm hoặc Thủ quỹ):

```json
{
  "name": "Quỹ tháng 10",
  "type": "monthly",
  "amount": "100000.00",
  "start_date": "2026-10-01",
  "due_date": "2026-10-31",
  "applies_to_all": true,
  "status": "open"
}
```

API tạo/duyệt đề xuất AI yêu cầu thêm header `X-CSRF-Token` gắn với phiên đăng nhập; token có trong trường ẩn `csrf_token` của trang `/ai`. API chatbot `POST /api/v1/assistant` dùng chung nghiệp vụ với chat trên trang AI: lệnh tạo nháp email/đề xuất và câu trả lời bổ sung cho đề xuất cần header CSRF; câu hỏi tra cứu không thay đổi dữ liệu nghiệp vụ nhưng vẫn lưu tin nhắn vào lịch sử. Các API quản lý cuộc trò chuyện và form chat, duyệt/sửa/đối soát nháp email, nhượng quyền, phân vai trò, tạo/duyệt đề xuất AI và các form nghiệp vụ mới trên trang Quỹ/Sự kiện cũng có CSRF token. Hai lượt duyệt đồng thời cùng một đề xuất hoặc giao dịch chờ được chặn ở bước cập nhật trạng thái.

Tệp nhập thành viên CSV/XLSX cần các cột `code,name,birth_date,email,phone,department_ids,password`. Việc nhập được hoàn tác toàn bộ nếu có dòng không hợp lệ.

### Nâng cấp database SQLite cũ

`db.create_all()` tạo **bảng còn thiếu** khi ứng dụng khởi động nhưng không sửa kiểu cột của bảng đã tồn tại. Nếu database cũ có `fund_transaction.so_tien` kiểu `FLOAT`, dừng webapp rồi chạy:

```bash
flask --app run.py migrate-money
```

Lệnh tạo file sao lưu `.bak-...` bên cạnh database (mặc định là `instance/clb.db.bak-...`), sau đó đổi cột sang `NUMERIC(14,2)` và giữ các giao dịch cũ. Nếu cột đã đúng kiểu, lệnh không thay đổi gì. Lệnh này **chỉ áp dụng cho SQLite**; chưa có migration tương ứng cho PostgreSQL. SQLite vẫn có giới hạn về lưu số thập phân; phép tính tiền trong Python dùng `Decimal`.

Nếu đã dùng bản có nháp email trước khi thêm người nhận ngoài CLB, cũng dừng webapp rồi chạy:

```bash
flask --app run.py migrate-email-recipients
```

Lệnh sao lưu database thành `instance/clb.db.bak-email-...`, cho phép nháp không gắn tài khoản thành viên và giữ lại các nháp cũ. Chạy lại lệnh khi cột đã được nâng cấp sẽ không thay đổi dữ liệu.

Bản nâng cấp AI này thêm sáu bảng: `email_proposal` (nháp và trạng thái gửi), `email_template` (mail mẫu), `assistant_pending` (yêu cầu đang hỏi bổ sung), `ai_report_snapshot` (báo cáo đã lưu), `member_planning_profile` (kỹ năng, mức nhận task, ngày tạm ngừng) và `ai_usage_log` (lượt model, token, độ trễ; không lưu prompt/API key). Trước khi cập nhật code/khởi động app, dừng webapp và sao lưu `instance/clb.db` ra một tệp `.bak` riêng; `db.create_all()` sẽ tạo các bảng còn thiếu khi app chạy lại, nhưng **không đổi cấu trúc bảng cũ**. Nếu đã có bảng `email_proposal` phiên bản cũ, chạy lệnh `migrate-email-recipients` ở trên. PostgreSQL cần quy trình migration riêng cho môi trường triển khai thật.

Giờ sự kiện và hạn task trong database là giờ địa phương của CLB (không gắn timezone). API nhận ISO datetime có offset sẽ đổi về `APP_TIMEZONE`; giá trị từ `datetime-local` được hiểu là giờ CLB. Thời điểm audit, đăng ký và thanh toán lưu theo UTC. Dữ liệu sự kiện cũ không bị tự động đổi giờ.

Để điện thoại quét mã QR điểm danh, mở web bằng địa chỉ mạng mà điện thoại truy cập được; QR sinh từ `127.0.0.1` sẽ chỉ hoạt động trên chính máy chạy web. Mã QR hết hạn sau 15 phút và có trang xác nhận trước khi điểm danh.

### Nâng cấp lịch sử chat trên SQLite

Dừng webapp rồi khởi động lại với code mới. Trước `db.create_all()`, ứng dụng tự kiểm tra database SQLite và tạo bản sao lưu riêng `.bak-chat-...` (quyền `0600`) nếu cần nâng cấp. Migration thêm `chat_conversation`, `conversation_pending`, cột `chat_message.conversation_id` và các index; giữ nguyên ID, nội dung, thời gian của tin nhắn cũ, gom chúng thành **Lịch sử trước nâng cấp** cho từng tài khoản. Trạng thái đang hỏi bổ sung cũ được chuyển một lần; không khôi phục lại yêu cầu đã hủy/hoàn tất sau khi restart. Có thể kiểm tra lại bằng `flask --app run.py migrate-chats`; chạy lại không chuyển trùng. Nếu phát hiện schema/ràng buộc không hợp lệ, nâng cấp dừng và rollback, không xóa bảng chat cũ. PostgreSQL cần migration riêng trước khi chạy phiên bản mới.

## Kiểm thử

Sau khi kích hoạt môi trường ảo:

```bash
python -m unittest discover -s tests -v
```

Các bài test dùng database tạm, không sửa `instance/clb.db`. Hiện có kiểm thử cho phân quyền, quỹ, đăng ký/danh sách chờ/điểm danh, đề xuất AI qua form/chat, gợi ý task theo tải/kỹ năng, mail mẫu và nháp email/đối soát gửi dở, giới hạn AI, số liệu theo phạm vi quyền, CSRF, múi giờ và migration SQLite. `tests/test_agent_orchestrator.py` thêm vòng lặp công cụ, phản hồi nhiều bước, chặn JSON/công cụ không hợp lệ, bộ lọc không được bỏ, giới hạn bước/thời gian, đổi quyền giữa lượt, bản nháp chưa thực thi và lưu tin trước/sau luồng SSE. Test tự động mô phỏng Gemini/SMTP, không gửi email thật; không chứng minh chất lượng mọi quyết định của model thật hoặc khả năng gửi mail trên máy triển khai.

## Cấu trúc dự án

```text
.
├── run.py                 # Chạy ứng dụng; CLI init-db, create-cn, migrate-money, migrate-email-recipients, migrate-chats
├── app/
│   ├── __init__.py        # App factory, blueprint và database
│   ├── config.py          # Cấu hình từ biến môi trường
│   ├── models.py          # Các bảng dữ liệu
│   ├── permissions.py     # Decorator phân quyền trang web
│   ├── security.py        # CSRF cho các form được bảo vệ
│   ├── migrations.py      # Nâng cấp cột tiền và nháp email của SQLite cũ
│   ├── routes/            # Trang HTML và API JSON
│   ├── services/          # Nghiệp vụ quỹ, sự kiện, AI
│   ├── templates/         # Giao diện Jinja2
│   └── static/            # CSS, ảnh và avatar tải lên
├── tests/                 # Kiểm thử tự động
└── requirements.txt
```

## Lưu ý trước khi triển khai thật

- Thay `SECRET_KEY`, bảo vệ `.env`, cấu hình HTTPS và sao lưu database định kỳ.
- Đăng nhập chưa có giới hạn số lần thử; CSRF hiện tập trung ở các form nhạy cảm và form nghiệp vụ mới, chưa phủ toàn bộ form cũ.
- Scheduler chạy ngay trong tiến trình web; cần tách riêng nếu triển khai nhiều worker.
- Giới hạn lượt gọi model đang kết hợp nhật ký database với bộ đếm lỗi trong tiến trình; khi chạy nhiều worker cần một bộ giới hạn dùng chung (ví dụ Redis) và quy trình theo dõi chi phí của nhà cung cấp.
- Avatar và minh chứng thanh toán lưu trên máy chạy web; cần chính sách lưu trữ/kiểm tra tệp phù hợp khi dùng thật.
- Chưa có migration PostgreSQL; test tự động dùng dịch vụ AI/SMTP giả lập, nên cần kiểm tra tích hợp có kiểm soát trước khi triển khai công khai.
- Vì API key Gemini và mật khẩu ứng dụng email từng được chia sẻ trong chat, hãy đổi cả hai trước khi cho người khác truy cập webapp.
