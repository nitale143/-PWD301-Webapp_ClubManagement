"""
Entry point cua webapp CLB.
Chay: python run.py
Mac dinh chay o http://127.0.0.1:5000
"""
from datetime import date
from dotenv import load_dotenv
from app import create_app, db
from app.models import User, Ban
from app.migrations import migrate_legacy_money

load_dotenv()
app = create_app()


@app.cli.command("migrate-money")
def migrate_money():
    """Back up and upgrade legacy fund_transaction.so_tien FLOAT to NUMERIC."""
    if db.engine.url.get_backend_name() != "sqlite" or not db.engine.url.database:
        raise RuntimeError("Lệnh này chỉ hỗ trợ SQLite database trên đĩa.")
    backup = migrate_legacy_money(db.engine.url.database)
    print(f"Đã cập nhật cột tiền. Bản sao lưu: {backup}" if backup else "Cột tiền đã đúng kiểu; không cần cập nhật.")


@app.cli.command("init-db")
def init_db():
    """Tao database va seed du lieu ban dau (3 ban hoat dong).
    Chay: flask --app run.py init-db
    """
    db.create_all()
    if not Ban.query.first():
        for ten in ["Ky thuat", "Nhan su", "Truyen thong"]:
            db.session.add(Ban(ten_ban=ten))
        db.session.commit()
        print("Da tao 3 ban hoat dong mac dinh.")
    print("Database da san sang.")


@app.cli.command("create-cn")
def create_cn():
    """Tao tai khoan Chu nhiem dau tien (da duoc duyet san) de bootstrap he thong.
    Chay: flask --app run.py create-cn
    """
    mssv = input("MSSV: ").strip()
    if User.query.filter_by(mssv=mssv).first():
        print("MSSV nay da ton tai.")
        return
    ho_ten = input("Ho ten: ").strip()
    password = input("Mat khau: ").strip()

    user = User(
        mssv=mssv,
        ho_ten=ho_ten,
        ngay_sinh=date(2000, 1, 1),
        sdt="0000000000",
        email=f"{mssv}@example.com",
        facebook_link="https://facebook.com/placeholder",
        status="approved",
        chuc_vu="CN",
    )
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    print(f"Da tao Chu nhiem {ho_ten} ({mssv}). Dang nhap va cap nhat lai thong tin ca nhan sau.")


if __name__ == "__main__":
    app.run(debug=True)
