import unittest
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
from app import create_app, db

class UserModelCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app({
            'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
            'TESTING': True
        })
        self.client = self.app.test_client()
        with self.app.app_context():
            db.create_all()
            from app.models import User
        self.User = User

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_password_hashing(self):
        with self.app.app_context():
            from app.models import User
            u = User(username='testuser')
            u.set_password('testpassword')
            self.assertFalse(u.check_password('wrongpassword'))
            self.assertTrue(u.check_password('testpassword'))

    def test_login_logout(self):
        with self.app.app_context():
            from app.models import User
            u = User(username='testuser')
            u.set_password('testpassword')
            db.session.add(u)
            db.session.commit()

            response = self.client.post('/admin_login', data={
                'username': 'testuser',
                'password': 'testpassword'
            }, follow_redirects=True)
            self.assertEqual(response.status_code, 200)
            self.assertIn(b'Admin Dashboard', response.data)

            response = self.client.get('/logout', follow_redirects=True)
            self.assertEqual(response.status_code, 200)
            self.assertIn(b'Welcome', response.data)

    def test_dashboard_access(self):
        with self.app.app_context():
            from app.models import User
            u = User(username='testuser')
            u.set_password('testpassword')
            db.session.add(u)
            db.session.commit()

            response = self.client.get('/admin_dashboard', follow_redirects=True)
            self.assertIn(b'Please log in to access this page.', response.data)

            self.client.post('/admin_login', data={
                'username': 'testuser',
                'password': 'testpassword'
            }, follow_redirects=True)
            response = self.client.get('/admin_dashboard')
            self.assertEqual(response.status_code, 200)
            self.assertIn(b'Admin Dashboard', response.data)

if __name__ == '__main__':
    unittest.main()

class UserModelCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app({
            'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
            'TESTING': True
        })
        self.client = self.app.test_client()
        with self.app.app_context():
            db.create_all()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_password_hashing(self):
        with self.app.app_context():
            u = self.User(username='testuser')
            u.set_password('testpassword')
            self.assertFalse(u.check_password('wrongpassword'))
            self.assertTrue(u.check_password('testpassword'))

    def test_login_logout(self):
        with self.app.app_context():
            # Create a test user
            u = self.User(username='testuser')
            u.set_password('testpassword')
            db.session.add(u)
            db.session.commit()

            # Test login
            response = self.client.post('/admin_login', data={
                'username': 'testuser',
                'password': 'testpassword'
            }, follow_redirects=True)
            self.assertEqual(response.status_code, 200)
            self.assertIn(b'Admin Dashboard', response.data) # Assuming 'Admin Dashboard' is on the dashboard page

            # Test logout
            response = self.client.get('/logout', follow_redirects=True)
            self.assertEqual(response.status_code, 200)
            self.assertIn(b'Welcome', response.data) # Assuming 'Welcome' is on the welcome page after logout

    def test_dashboard_access(self):
        with self.app.app_context():
            # Create a test user
            u = self.User(username='testuser')
            u.set_password('testpassword')
            db.session.add(u)
            db.session.commit()

            # Try to access dashboard without login (should redirect)
            response = self.client.get('/admin_dashboard', follow_redirects=True)
            self.assertIn(b'Please log in to access this page.', response.data) # Assuming flash message for login required

            # Login and then access dashboard
            self.client.post('/admin_login', data={
                'username': 'testuser',
                'password': 'testpassword'
            }, follow_redirects=True)
            response = self.client.get('/admin_dashboard')
            self.assertEqual(response.status_code, 200)
            self.assertIn(b'Admin Dashboard', response.data)

if __name__ == '__main__':
    unittest.main()