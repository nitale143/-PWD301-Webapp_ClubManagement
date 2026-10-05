# CLB Manager

Ứng dụng web nội bộ để quản lý thành viên, sự kiện, công việc và quỹ câu lạc bộ. Dự án dùng **Python/Flask**, giao diện Jinja2 và SQLite mặc định. Trợ lý AI hỗ trợ tra cứu, lập đề xuất; khi chưa có API key, ứng dụng dùng chế độ quy tắc để nhóm vẫn chạy thử được luồng nghiệp vụ.

> Dự án hiện phù hợp để học tập và demo. Xem [Lưu ý trước khi triển khai thật](#lưu-ý-trước-khi-triển-khai-thật) nếu muốn dùng với dữ liệu thật.

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
| Trợ lý AI | Chat/API dùng chung luồng, lưu ngữ cảnh gần đây theo từng người; câu trả lời số liệu lấy trực tiếp từ database; đề xuất sự kiện/chia task và tạo nháp email để BDH duyệt trước khi thực hiện. Nhật ký token và giới hạn lượt gọi giúp kiểm soát tài khoản AI chung. |
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

### Độ tin cậy của AI Agent

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
| `MAIL_ENABLED` | Mặc định `false`: email chỉ in ra terminal. Đặt `true` khi đã cấu hình SMTP. |
| `MAIL_SERVER`, `MAIL_PORT`, `MAIL_USE_TLS`, `MAIL_USERNAME`, `MAIL_PASSWORD`, `MAIL_DEFAULT_SENDER` | Thông tin máy chủ gửi email. |

Để dùng Gemini, lấy key trong Google AI Studio rồi đặt riêng trong `.env` (không dán key vào mã nguồn hoặc Git):

```dotenv
AI_PROVIDER=gemini
GEMINI_API_KEY=your-private-key
GEMINI_MODEL=gemini-3.5-flash-lite
```

Khởi động lại webapp sau khi đổi `.env`. Không có ô nhập API key riêng cho từng thành viên. Các truy vấn đã hỗ trợ trả dữ liệu trực tiếp bằng code, dù chọn provider nào. Với `gemini` hoặc `anthropic` và key hợp lệ, model soạn bản nháp có duyệt; nếu tắt `AI_STRICT_FACTS`, model cũng có thể viết chat sinh tự do được đánh dấu chưa kiểm chứng. Model nhận dữ kiện theo quyền, không được cấp công cụ tự ghi database; ngữ cảnh hội thoại chỉ gồm các tin người dùng, không lấy câu trả lời AI cũ làm bằng chứng. Danh sách sự kiện sắp tới là dữ liệu công khai trong CLB theo trang Event hiện tại; task của thành viên khác vẫn lọc theo ban của TB. Gemini dùng JSON có schema cho nháp email/đề xuất; backend kiểm tra giá trị trước khi lưu. Nếu Gemini tạm thời quá tải, ứng dụng thử lại một lần; chat mở nhận thông báo và hướng dẫn truy vấn, còn thao tác tạo đề xuất báo lỗi. Truy vấn database không phụ thuộc kết nối Gemini. Trang AI hiển thị tổng lượt gọi, token và độ trễ 24 giờ, **không tự quy đổi thành chi phí tiền**.

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

API tạo/duyệt đề xuất AI yêu cầu thêm header `X-CSRF-Token` gắn với phiên đăng nhập; token có trong trường ẩn `csrf_token` của trang `/ai` dành cho BDH. API chatbot `POST /api/v1/assistant` dùng chung nghiệp vụ với chat trên trang AI: lệnh tạo nháp email/đề xuất cũng yêu cầu header CSRF; câu hỏi tra cứu không tạo dữ liệu. Form chat, duyệt/sửa/đối soát nháp email, nhượng quyền, phân vai trò, tạo/duyệt đề xuất AI và các form nghiệp vụ mới trên trang Quỹ/Sự kiện cũng có CSRF token. Hai lượt duyệt đồng thời cùng một đề xuất hoặc giao dịch chờ được chặn ở bước cập nhật trạng thái.

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

## Kiểm thử

Sau khi kích hoạt môi trường ảo:

```bash
python -m unittest discover -s tests -v
```

Các bài test dùng database tạm, không sửa `instance/clb.db`. Hiện có kiểm thử cho phân quyền, quỹ, đăng ký/danh sách chờ/điểm danh, đề xuất AI qua form/chat, gợi ý task theo tải/kỹ năng, mail mẫu và nháp email/đối soát gửi dở, giới hạn AI, số liệu theo phạm vi quyền, CSRF, múi giờ và migration SQLite. Test tự động mô phỏng Gemini/SMTP, không gửi email thật.

## Cấu trúc dự án

```text
.
├── run.py                 # Chạy ứng dụng; CLI init-db, create-cn, migrate-money, migrate-email-recipients
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
