# CLB Manager - Khung du an (Flask)

Webapp noi bo quan ly Cau lac bo (CLB) voi AI Agent ho tro. Du an dung Flask;
tro ly co che do quy tac khi khong co API key va ket noi Claude khi cau hinh
key chung cua CLB. Khong luu API key trong repo.

## Cai dat

```bash
cd /home/phanquang/my-project
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # sua SECRET_KEY; dien AI_API_KEY neu dung Claude

flask --app run.py init-db        # tao database SQLite + 3 ban hoat dong
flask --app run.py create-cn      # tao tai khoan Chu nhiem dau tien (bootstrap BDH)

python run.py                     # chay server o http://127.0.0.1:5000
```

Truy cap `http://127.0.0.1:5000` se tu dong chuyen den trang dang nhap
(dung nhu yeu cau "khi dua link la vo trang nay").

## Cau truc du an

```
clb_webapp/
  run.py                  # entry point + CLI (init-db, create-cn)
  app/
    __init__.py           # app factory, dang ky blueprint, tao DB
    config.py              # cau hinh + cac hang so (chuc vu, trang thai...)
    models.py              # User, Ban, Event, Task, FundPeriod, ChatMessage,...
    permissions.py         # decorator @approved_required, @bdh_required, @role_required
    validators.py          # validate form dang ky (mssv, sdt, email, facebook, ngay sinh)
    routes/
      auth.py               # dang nhap, dang ky, cho duyet
      main.py               # trang Home
      member.py             # trang Member (loc/sap xep/xuat excel)
      event.py              # trang Event + task (xung phong, chi dinh, doi trang thai)
      funds.py               # trang Funds (thu/chi, danh sach dong quy, xuat excel)
      ai.py                 # trang AI chat (luu lich su)
      api.py                # JSON API /api/v1
      admin.py               # duyet thanh vien + chi dinh chuc vu + nhuong quyen
    services/               # nghiep vu quy, su kien, hoat dong, tro ly, de xuat AI
    migrations.py            # nang cap cot tien SQLite cu, co sao luu
    security.py              # CSRF token cho form quan trong
    templates/              # HTML (Jinja2), dung chung base.html + navbar
    static/css/style.css     # giao dien don gian, sach se
```

## Da lam theo dung yeu cau

- Dang nhap bang MSSV + mat khau; dang ky day du thong tin voi validate
  dinh dang (mssv, sdt, email, link facebook, ngay sinh).
- Luong duyet thanh vien: `pending -> approved / rejected` boi BDH.
- Phan cap chuc vu CN > PCN > TB, Thu ky/Thu quy > Thanh vien, gioi han so
  luong (1 CN, 2 PCN, 3 TB, 1 Thu ky/Thu quy), chi nguoi quyen cao hon moi
  duoc chi dinh xuong (xem `permissions.can_assign_role`).
- Co che **nhuong quyen**: BDH cu chi dinh lai chuc vu cua minh cho nguoi
  khac va tro thanh thanh vien thuong (`admin.nhuong_quyen`).
- Truong ban (TB) chi gan voi 1 ban cu the (`UserBan.is_truong_ban`); logic
  loc "TB chi quan ly thanh vien ban minh" da co ham `User.quan_ly_ban_ids()`
  san sang de dung trong cac view can gioi han theo ban.
- Trang Member: thanh vien thuong chi thay thong tin cong khai, BDH thay
  day du; tim kiem/sap xep theo ten, mssv, ban; xuat Excel (openpyxl).
- Trang Event: tao su kien (kiem tra trung ma), task con voi 5 trang thai
  dung dung rule (`dang_lam -> cho_duyet` chi user tu doi va chi khi noi
  dung nop thay doi; `lam_lai`/`hoan_thanh`/`huy` chi BDH doi, bat buoc
  nhan xet khi lam lai); task co nguoi phu trach tu luc tao.
- Trang Funds: quan ly theo ky, chi thu quy duoc sua, hien so du/tong
  thu/tong chi cua ky hien tai, danh sach dong quy, xuat Excel.
- Trang AI: giao dien chat + luu lich su theo tung user.
- **Gui mail (SMTP) + canh bao deadline tu dong (scheduler)**: xem muc
  rieng "Cau hinh gui mail" ben duoi.

## Cau hinh gui mail (SMTP + Scheduler)

- `app/mail.py`: ham `send_email()` dung `smtplib` thuan. Mac dinh
  `MAIL_ENABLED=false` nen email chi duoc **in ra console** (de test khong
  can tai khoan that). Bat gui that bang cach set bien moi truong:
  ```
  MAIL_ENABLED=true
  MAIL_SERVER=smtp.gmail.com
  MAIL_PORT=587
  MAIL_USE_TLS=true
  MAIL_USERNAME=clb.example@gmail.com
  MAIL_PASSWORD=xxxx-xxxx-xxxx-xxxx   # App Password cua Gmail, KHONG dung mat khau thuong
  MAIL_DEFAULT_SENDER=clb.example@gmail.com
  ```
  (Neu dung mail server truong/to chuc thi doi MAIL_SERVER/MAIL_PORT tuong ung.)
- `app/scheduler.py`: dung APScheduler chay ngam trong tien trinh Flask,
  moi ngay luc 07:00 se quet cac task con `dang_lam`/`lam_lai` va gui mail
  canh bao neu deadline con dung `DEADLINE_WARNING_DAYS` (mac dinh 7) ngay
  nua. Duoc khoi dong tu dong trong `create_app()`.
  - Luu y khi trien khai that voi nhieu worker (gunicorn -w >1): scheduler
    se chay lap trong tung worker -> gui mail trung. Khi do nen tach
    thanh 1 cron job/tien trinh rieng hoac dung Celery beat.
- Da gan `send_email()` vao cac diem: duyet/tu choi thanh vien, giao/chi
  dinh task, nop san pham (bao BDH), BDH doi trang thai task (bao nguoi
  phu trach), va nut "Nhac dong quy" o trang Funds (thu quy bam de nhac
  thanh vien chua dong quy).

## AI Agent, de xuat va nhuong quyen

- Dien `AI_API_KEY` vao `.env` va de `AI_PROVIDER=anthropic` de chat goi
  Claude Messages API. `AI_MODEL` chon model. Neu khong co key, tro ly van
  tra loi bang intent va truy van ORM dinh san (`AI_PROVIDER=rules` co the
  ep che do nay). `python run.py` va `flask --app run.py run` deu doc `.env`.
- Du lieu gui toi AI duoc gioi han theo quyen nguoi hoi; khong gui email,
  SDT hay ngay sinh. Model chi co quyen doc ban tom tat, khong duoc nhan
  cong cu sua database. Loi API duoc thong bao, khong hien API key.
- BDH vao trang AI, mo muc "De xuat su kien hoac chia task", dien yeu cau
  va tao ban xem truoc. He thong luu `AIProposal` o trang thai `pending`;
  chua tao Event/Task. BDH kiem tra noi dung roi bam "Duyet va ap dung"
  hoac "Tu choi". Khi duyet, backend kiem tra lai quyen, thoi gian, ban,
  nguoi phu trach, sau do moi tao Event/Task va ghi audit log.
- Neu khong co API key, de xuat van dung duoc theo quy tac don gian de demo
  luong duyet. De AI sinh noi dung va phan chia task linh hoat, can key.
- Nut "Nhuong quyen" gui `target_id` qua form POST toi
  `/admin/roles/nhuong-quyen`; khong con dung JavaScript ghep URL.
- Form nhượng quyền, phân vai trò và duyệt đề xuất AI dùng CSRF token.
  API tạo/duyệt đề xuất AI cũng yêu cầu header `X-CSRF-Token` lấy từ
  phiên trang `/ai`. Hai người duyệt cùng một đề xuất chỉ có một lượt
  được thực thi.

## Da fix / hoan thien them theo yeu cau

- **Ky quy theo lich hoc (Spring/Summer/Fall)**: thu quy tu mo ky moi qua
  form o trang Funds (`funds.period_new`), ky moi tu dong dong ky dang mo.
  Scheduler (`check_period_reminder` trong `app/scheduler.py`) moi ngay
  kiem tra neu ky hien tai con <= `PERIOD_REMINDER_DAYS` (mac dinh 30)
  ngay la het han thi tao Notification + gui mail nhac BDH nhap ky moi
  (chi nhac 1 lan/ky nho co `da_nhac_ky_moi`).
- **Tinh trang hoat dong theo ban + theo ky**: bang `MemberActivity`
  (user, ban, ky) duoc tinh lai trong `app/activity.py` moi khi mot Event
  duoc BDH bam "Ket thuc su kien" (`event.event_end`). Cong thuc: % =
  task hoan_thanh / tong task (khong tinh task 'huy'), trong pham vi 1 ky.
  Thanh vien duoc gan `ky_tham_gia_id` luc duyet (`admin.approve_user`) -
  ky do se KHONG duoc tinh %, tu ky ke tiep moi tinh.
- **Bo co che xung phong nhan task**: `Task.assignee_id` la bat buoc ngay
  luc tao (form tao task yeu cau MSSV nguoi phu trach); BDH van co the
  chi dinh lai qua `event.task_reassign`. Bang `TaskVolunteer` va truong
  `han_xung_phong` da bi go bo khoi model.
- **Upload avatar that**: `app/routes/profile.py` nhan file qua
  `request.files`, kiem tra duoi file hop le (`ALLOWED_AVATAR_EXTENSIONS`),
  gioi han dung luong qua `MAX_CONTENT_LENGTH` (3MB), luu vao
  `app/static/uploads/avatars/` (dung cho demo; khi len production that
  nen chuyen sang S3/Cloudinary). Click avatar tren navbar -> trang
  `/profile` xem thong tin + doi anh + xem % hoat dong + tinh trang dong quy.
- **Sua loi Jinja2 khi loc Member**: nguyen nhan la template goi
  `request.args.get('ban_id', type=int)` truc tiep trong Jinja - `int`
  khong ton tai trong Jinja globals (chi co dang filter `|int`) nen bi
  danh gia thanh Undefined, roi crash khi Werkzeug goi Undefined nhu mot
  ham de ep kieu. Fix: viec parse `ban_id`/`sort`/`q` chuyen het ve Python
  trong `member.py` (`_parse_filters()`), template chi nhan gia tri da xu
  ly san (`selected_ban_id`, `selected_sort`, `selected_q`).

## Ghi chu bao mat truoc khi dua vao dung that

- Doi `SECRET_KEY` trong `app/config.py` (hoac set bien moi truong).
- Xem xet gioi han so lan dang nhap sai (rate limiting) cho `/login`.
- Kiem tra lai toan bo permission cho tung route truoc khi trien khai that,
  day chi la khung ban dau.

## Backend nghiệp vụ mở rộng (Flask, giai đoạn 1)

Theo lựa chọn của nhóm, dự án tiếp tục dùng Flask và giữ nguyên HTML/CSS.
`create_app()` tự tạo các bảng mới khi khởi động; cơ sở dữ liệu SQLite hiện
có không bị xóa. Nên sao lưu `instance/clb.db` trước khi cập nhật ứng dụng.

Với database tạo từ phiên bản cũ, chạy một lần sau khi dừng webapp:

```bash
flask --app run.py migrate-money
```

Lệnh tự sao lưu `instance/clb.db` thành file `.bak-...`, rồi đổi
`fund_transaction.so_tien` từ `FLOAT` sang `NUMERIC(14,2)` mà giữ các
giao dịch. Nếu đã đúng kiểu thì lệnh không làm gì. Với PostgreSQL cần
migration riêng; SQLite vẫn có giới hạn về lưu số thập phân nên việc tính
tiền trong ứng dụng dùng `Decimal`.

Các bảng mới lưu trạng thái thành viên, khoản thu và các lần thanh toán,
miễn/giảm, minh chứng, sự kiện chi tiết, đăng ký/danh sách chờ, điểm danh,
điểm hoạt động, cấu hình và audit log. Tiền của nghiệp vụ mới dùng `Numeric`
và `Decimal`. Trang quỹ theo kỳ cũ vẫn hoạt động độc lập để không làm vỡ UI.

API JSON tại `/api/v1` dùng phiên đăng nhập hiện có (`/login`); chưa đăng
nhập trả 401, chưa được duyệt trả 403. Danh sách hỗ trợ `page` và
`page_size` (tối đa 100). Các nhóm endpoint chính:

| Nhóm | Đường dẫn tiêu biểu |
| --- | --- |
| Thành viên | `GET/POST /members`, `POST /members/import`, `PATCH /members/<id>`, `POST /members/<id>/archive`, `GET /members/<id>/activity` |
| Quỹ | `POST /funds`, `PATCH /funds/<id>/status`, `GET /funds/<id>/balances`, `POST /funds/<id>/payments` |
| Thanh toán | `GET /payments`, `POST /payments/<id>/review`, `POST /payments/<id>/evidence` |
| Sự kiện | `POST /events`, `PATCH /events/<id>`, `POST /events/<id>/copy`, `POST /events/<id>/cancel` |
| Tham gia | `POST /events/<id>/registrations`, `POST /registrations/<id>/cancel`, `GET /events/<id>/qr.png`, `POST /attendance/checkin` |
| Thống kê và AI | `GET /dashboard`, `GET /reports/funds.xlsx`, `GET /reports/members.xlsx`, `POST /assistant`, `GET/POST /assistant/proposals`, `POST /assistant/proposals/<id>/review` |

Ví dụ tạo khoản thu khi đã đăng nhập bằng tài khoản Thủ quỹ hoặc Chủ nhiệm:

```json
POST /api/v1/funds
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

Chạy kiểm thử độc lập, không đụng tới `instance/clb.db`:

```bash
python -m unittest discover -s tests -v
```

Tệp nhập thành viên CSV/XLSX cần các cột `code,name,birth_date,email,phone,department_ids,password`;
`department_ids` là danh sách mã ban cách nhau bằng dấu phẩy. Nhập thất bại
ở bất kỳ dòng nào sẽ hoàn tác cả tệp. Mật khẩu chỉ được băm, không lưu nguyên văn.

Trang Quỹ hiển thị khoản thu mới, số đã đóng/còn thiếu và giao dịch chờ duyệt;
thành viên có thể gửi thanh toán, thủ quỹ có thể xác nhận. Phần quỹ theo kỳ
cũ vẫn hiện bên dưới. Trang Sự kiện dùng chung dữ liệu đăng ký/danh sách chờ,
điểm danh QR/thủ công và đánh giá; form tạo sự kiện có sức chứa, hạn đăng ký.
Mã QR dẫn tới trang xác nhận điểm danh, hết hạn sau 15 phút. Khi dùng điện
thoại quét QR, mở ứng dụng qua địa chỉ mạng truy cập được từ điện thoại,
không phải `127.0.0.1`.

Giờ sự kiện/task lưu dạng giờ địa phương của CLB (`APP_TIMEZONE`, mặc định
`Asia/Bangkok`). Giá trị ISO có múi giờ từ API được đổi về giờ CLB trước khi
lưu; `datetime-local` không có múi giờ được hiểu là giờ CLB. Các mốc audit,
đăng ký và thanh toán tiếp tục lưu UTC. Không tự đổi dữ liệu sự kiện cũ.

Bộ lọc/biểu đồ báo cáo nâng cao và migration cho PostgreSQL chưa nằm trong
bước này. Tích hợp Claude đã có kiểm thử giả lập phản hồi API; gọi dịch vụ
thật cần `AI_API_KEY` của CLB và chưa thể kiểm thử khi chưa có key.
