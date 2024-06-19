import unittest
from app.auth import register_user, authenticate_user

class TestAuth(unittest.TestCase):

    def test_register_user(self):
        response = register_user("testuser", "password123")
        self.assertEqual(response, "Registrazione completata")

    def test_authenticate_user(self):
        register_user("testuser", "password123")
        response = authenticate_user("testuser", "password123")
        self.assertEqual(response, "Autenticazione riuscita")

if __name__ == '__main__':
    unittest.main()