import tempfile
import unittest
from pathlib import Path
from flask import abort
from app import create_app, db
from app.services.export_security import safe_excel_row


class SecurityBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.app = create_app({"TESTING": True, "SECRET_KEY": "test-key", "AI_PROVIDER": "rules",
                               "MAIL_ENABLED": False, "SCHEDULER_ENABLED": False,
                               "SQLALCHEMY_DATABASE_URI": "sqlite:///" + str(Path(self.directory.name) / "test.db")})
        self.client = self.app.test_client()

    def tearDown(self):
        self.directory.cleanup()

    def test_security_headers_and_unique_nonce_match_template(self):
        first = self.client.get('/login')
        second = self.client.get('/login')
        self.assertEqual(first.headers['X-Content-Type-Options'], 'nosniff')
        self.assertEqual(first.headers['X-Frame-Options'], 'DENY')
        self.assertIn("frame-ancestors 'none'", first.headers['Content-Security-Policy'])
        self.assertNotIn("script-src 'self' 'unsafe-inline'", first.headers['Content-Security-Policy'])
        self.assertNotEqual(first.headers['Content-Security-Policy'], second.headers['Content-Security-Policy'])
        self.assertEqual(first.headers['Cache-Control'], 'private, no-store')

    def test_host_header_attack_rejected(self):
        response = self.client.get('/login', headers={'Host': 'attacker.example'})
        self.assertEqual(response.status_code, 400)

    def test_spreadsheet_formulas_remain_text(self):
        values = ['=HYPERLINK("bad")', ' +1', '\t=1', '-1', '@SUM(1)', 'Normal', 100]
        result = safe_excel_row(values)
        self.assertTrue(all(value.startswith("'") for value in result[:5]))
        self.assertEqual(result[5:], ['Normal', 100])

    def test_production_rejects_weak_secret_and_debug(self):
        for options in ({'SECRET_KEY': 'weak'}, {'SECRET_KEY': 'strong-value-'*4, 'DEBUG': True}):
            with self.assertRaises(RuntimeError):
                create_app({'APP_ENV': 'production', 'TESTING': False, 'SCHEDULER_ENABLED': False,
                            'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:', **options})

    def test_unauthenticated_avatar_access_rejected(self):
        for path in ('/static/uploads/avatars/user_1.png', '/static/./uploads/avatars/user_1.png',
                     '/static/%2e/uploads/avatars/user_1.png', '/static/js/../uploads/avatars/user_1.png'):
            self.assertEqual(self.client.get(path).status_code, 403, path)

    def test_stale_member_promoted_to_last_admin_cannot_be_archived(self):
        from datetime import date
        from app.models import User, MemberRecord
        from app.services.access import set_member_left_safely
        with self.app.app_context():
            for user_id, role in ((1, 'CN'), (2, 'THANH_VIEN')):
                db.session.add(User(id=user_id, mssv=f'TEST00{user_id}', ho_ten=f'Test {user_id}',
                                    password_hash='test-only', ngay_sinh=date(2003, 1, 1),
                                    sdt=f'090000000{user_id}', email=f'test{user_id}@example.test',
                                    status='approved', chuc_vu=role))
                db.session.add(MemberRecord(user_id=user_id, ngay_gia_nhap=date(2026, 1, 1)))
            db.session.commit()
            stale_member=db.session.get(User, 2)
            record=db.session.get(MemberRecord, 2)
            with db.engine.begin() as connection:
                connection.execute(db.update(User).where(User.id==1).values(chuc_vu='THANH_VIEN'))
                connection.execute(db.update(User).where(User.id==2).values(chuc_vu='CN'))
            self.assertEqual(stale_member.chuc_vu, 'THANH_VIEN')
            self.assertFalse(set_member_left_safely(stale_member, record))
            db.session.rollback()
            self.assertEqual(db.session.get(MemberRecord, 2).tinh_trang, 'active')

    def test_failed_csrf_is_json_for_api_without_echoing_token(self):
        response = self.client.post('/api/v1/assistant', json={'question': 'hi'}, headers={'X-CSRF-Token': 'sensitive-token'})
        self.assertEqual(response.status_code, 400)
        self.assertIsNotNone(response.json)
        self.assertNotIn('sensitive-token', response.get_data(as_text=True))

    def test_unhandled_error_does_not_disclose_details(self):
        @self.app.get('/failure-check')
        def failure():
            raise RuntimeError('password=secret-example sql-private-path')
        self.app.config['TESTING'] = False
        response = self.client.get('/failure-check')
        self.assertEqual(response.status_code, 500)
        self.assertNotIn('secret-example', response.get_data(as_text=True))

    def test_production_https_and_cookie_flags(self):
        self.app.config.update(APP_ENV='production', SESSION_COOKIE_SECURE=True, TESTING=False)
        self.assertEqual(self.client.get('/login').status_code, 400)
        response=self.client.get('/login', base_url='https://localhost')
        self.assertEqual(response.status_code, 200)
        self.assertIn('Strict-Transport-Security', response.headers)
        cookie=response.headers.get('Set-Cookie', '')
        self.assertIn('Secure', cookie)
        self.assertIn('HttpOnly', cookie)


if __name__ == '__main__':
    unittest.main()
