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
| Trợ lý AI | Chat lưu lịch sử theo từng người; trả lời từ dữ liệu trong phạm vi được phép; đề xuất sự kiện/chia task để BDH xem trước và duyệt trước khi tạo thật. |
| Thông báo | Email khi duyệt thành viên, giao/duyệt task; nhắc deadline và kỳ quỹ qua lịch chạy nền. Mặc định chỉ in email ra terminal. |

### Luồng sử dụng cơ bản

1. Thành viên đăng ký tại `/register`; tài khoản ở trạng thái chờ.
2. Ban điều hành (BDH) duyệt hoặc từ chối tại trang **BDH**. Người được duyệt mới sử dụng các trang nội bộ.
3. BDH tạo sự kiện và phân công task. Thành viên đăng ký, điểm danh, nộp sản phẩm và đánh giá sự kiện theo trạng thái cho phép.
4. Thủ quỹ tạo khoản thu; thành viên gửi thông tin đóng quỹ; Thủ quỹ xác nhận để cập nhật số dư.
5. BDH có thể yêu cầu AI lập đề xuất. Đề xuất chỉ tạo dữ liệu thật sau khi người có quyền bấm **Duyệt và áp dụng**.

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
| `AI_PROVIDER` | `anthropic` hoặc `rules`. Nếu chọn Anthropic nhưng không có key, ứng dụng dùng quy tắc. |
| `AI_API_KEY`, `AI_MODEL` | API key chung do CLB quản lý và tên model cho Claude Messages API. |
| `MAIL_ENABLED` | Mặc định `false`: email chỉ in ra terminal. Đặt `true` khi đã cấu hình SMTP. |
| `MAIL_SERVER`, `MAIL_PORT`, `MAIL_USE_TLS`, `MAIL_USERNAME`, `MAIL_PASSWORD`, `MAIL_DEFAULT_SENDER` | Thông tin máy chủ gửi email. |

Không có ô nhập API key riêng cho từng thành viên. Với `AI_PROVIDER=rules`, trợ lý trả lời bằng truy vấn/quy tắc đã viết sẵn. Với `AI_PROVIDER=anthropic` và key hợp lệ, ứng dụng gọi Claude; model chỉ nhận dữ kiện đã lọc theo quyền và không được cấp công cụ tự ghi database. Tạo sự kiện/task từ đề xuất vẫn cần BDH duyệt. Luồng gọi API đã được kiểm thử bằng phản hồi giả lập; cần key thật để kiểm tra kết nối dịch vụ thực tế.

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

API tạo/duyệt đề xuất AI yêu cầu thêm header `X-CSRF-Token` gắn với phiên đăng nhập; token có trong trường ẩn `csrf_token` của trang `/ai` dành cho BDH. Form nhượng quyền, phân vai trò, tạo/duyệt đề xuất AI và các form nghiệp vụ mới trên trang Quỹ/Sự kiện cũng có CSRF token. Hai lượt duyệt đồng thời cùng một đề xuất hoặc giao dịch chờ được chặn ở bước cập nhật trạng thái.

Tệp nhập thành viên CSV/XLSX cần các cột `code,name,birth_date,email,phone,department_ids,password`. Việc nhập được hoàn tác toàn bộ nếu có dòng không hợp lệ.

### Nâng cấp database SQLite cũ

`db.create_all()` tạo **bảng còn thiếu** khi ứng dụng khởi động nhưng không sửa kiểu cột của bảng đã tồn tại. Nếu database cũ có `fund_transaction.so_tien` kiểu `FLOAT`, dừng webapp rồi chạy:

```bash
flask --app run.py migrate-money
```

Lệnh tạo file sao lưu `.bak-...` bên cạnh database (mặc định là `instance/clb.db.bak-...`), sau đó đổi cột sang `NUMERIC(14,2)` và giữ các giao dịch cũ. Nếu cột đã đúng kiểu, lệnh không thay đổi gì. Lệnh này **chỉ áp dụng cho SQLite**; chưa có migration tương ứng cho PostgreSQL. SQLite vẫn có giới hạn về lưu số thập phân; phép tính tiền trong Python dùng `Decimal`.

Giờ sự kiện và hạn task trong database là giờ địa phương của CLB (không gắn timezone). API nhận ISO datetime có offset sẽ đổi về `APP_TIMEZONE`; giá trị từ `datetime-local` được hiểu là giờ CLB. Thời điểm audit, đăng ký và thanh toán lưu theo UTC. Dữ liệu sự kiện cũ không bị tự động đổi giờ.

Để điện thoại quét mã QR điểm danh, mở web bằng địa chỉ mạng mà điện thoại truy cập được; QR sinh từ `127.0.0.1` sẽ chỉ hoạt động trên chính máy chạy web. Mã QR hết hạn sau 15 phút và có trang xác nhận trước khi điểm danh.

## Kiểm thử

Sau khi kích hoạt môi trường ảo:

```bash
python -m unittest discover -s tests -v
```

Các bài test dùng database tạm, không sửa `instance/clb.db`. Hiện có kiểm thử cho phân quyền, quỹ, đăng ký/danh sách chờ/điểm danh, đề xuất AI, CSRF, múi giờ và migration SQLite.

## Cấu trúc dự án

```text
.
├── run.py                 # Chạy ứng dụng; CLI init-db, create-cn, migrate-money
├── app/
│   ├── __init__.py        # App factory, blueprint và database
│   ├── config.py          # Cấu hình từ biến môi trường
│   ├── models.py          # Các bảng dữ liệu
│   ├── permissions.py     # Decorator phân quyền trang web
│   ├── security.py        # CSRF cho các form được bảo vệ
│   ├── migrations.py      # Nâng cấp cột tiền của SQLite cũ
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
- Avatar và minh chứng thanh toán lưu trên máy chạy web; cần chính sách lưu trữ/kiểm tra tệp phù hợp khi dùng thật.
- Chưa có migration PostgreSQL và chưa kiểm thử gọi Claude thật nếu chưa có `AI_API_KEY`.
