# CLB Manager - Khung du an (Flask)

Webapp noi bo quan ly Cau lac bo (CLB) voi AI Agent ho tro, xay theo yeu cau
trong `webapp_requirements.txt`. Day la **khung du an day du** (models,
routes, templates, permissions) da chay duoc, nhung mot so phan (gui mail
that, ket noi LLM that, sinh bao cao AI nang cao) con la **stub** de ban
tiep tuc phat trien.

## Cai dat

```bash
cd clb_webapp
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt

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
      admin.py               # duyet thanh vien + chi dinh chuc vu + nhuong quyen
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
  nhan xet khi lam lai); co che xung phong nhan task voi han xung phong.
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

## Con la STUB - can ban lam tiep

1. **Ket noi LLM that cho AI Agent** (`app/routes/ai.py -> generate_ai_reply`):
   da chot dung 1 API key CHUNG do CLB quan ly (cau hinh `AI_PROVIDER`,
   `AI_API_KEY`, `AI_MODEL` trong `app/config.py`, doc tu bien moi
   truong), khong cho tung user tu nhap key rieng. Hien tai van la stub
   (chua goi API that) vi chua co key - ban chi can dien `AI_API_KEY` va
   goi API model trong ham nay, truyen kem du lieu member/event/fund lam
   ngu canh.
2. **AI de xuat chia task + tu tao event sau khi BDH duyet**: can thiet ke
   luong "AI de xuat -> BDH bam duyet -> he thong tu thuc thi" (co the
   dung bang trung gian AIProposal luu de xuat cho toi khi duoc duyet).
3. Nut "Nhuong quyen" o `admin_roles.html` van dang dung mot doan JS don
   gian de gan user_id vao URL - nen thay bang mot form/route rieng cho
   gon hon truoc khi dung that.

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
