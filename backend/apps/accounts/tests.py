from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

User = get_user_model()


class AuthFlowTests(APITestCase):
    def test_register_returns_tokens_and_user(self):
        response = self.client.post(
            "/api/auth/register/",
            {"email": "newuser@example.com", "password": "StrongPass123", "first_name": "New"},
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)
        self.assertEqual(response.data["user"]["email"], "newuser@example.com")

    def test_login_with_email(self):
        User.objects.create_user(
            username="loginuser@example.com",
            email="loginuser@example.com",
            password="StrongPass123",
        )
        response = self.client.post(
            "/api/auth/login/",
            {"email": "loginuser@example.com", "password": "StrongPass123"},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_login_with_wrong_password_fails(self):
        User.objects.create_user(
            username="loginuser2@example.com",
            email="loginuser2@example.com",
            password="StrongPass123",
        )
        response = self.client.post(
            "/api/auth/login/",
            {"email": "loginuser2@example.com", "password": "wrong"},
            format="json",
        )
        self.assertEqual(response.status_code, 401)

    def test_me_requires_authentication(self):
        response = self.client.get("/api/auth/me/")
        self.assertEqual(response.status_code, 401)

    def test_me_returns_current_user(self):
        user = User.objects.create_user(
            username="meuser@example.com", email="meuser@example.com", password="StrongPass123"
        )
        self.client.force_authenticate(user=user)
        response = self.client.get("/api/auth/me/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["email"], "meuser@example.com")

    def test_logout_blacklists_refresh_token(self):
        user = User.objects.create_user(
            username="logoutuser@example.com",
            email="logoutuser@example.com",
            password="StrongPass123",
        )
        login_response = self.client.post(
            "/api/auth/login/",
            {"email": "logoutuser@example.com", "password": "StrongPass123"},
            format="json",
        )
        refresh = login_response.data["refresh"]
        self.client.force_authenticate(user=user)
        logout_response = self.client.post("/api/auth/logout/", {"refresh": refresh}, format="json")
        self.assertEqual(logout_response.status_code, 205)

        refresh_response = self.client.post("/api/auth/refresh/", {"refresh": refresh}, format="json")
        self.assertEqual(refresh_response.status_code, 401)
