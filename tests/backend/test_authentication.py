from unittest.mock import patch

from django.core import mail
from django.core.cache import cache
from django.test import override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from users.models import User

from .base import AuthenticatedAPITestCase


@override_settings(
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    DEFAULT_FROM_EMAIL="no-reply@example.com",
    FRONTEND_BASE_URL="https://hub.test",
    MAGIC_LINK_EXPIRY_SECONDS=600,
)
class AuthenticationEndpointsTests(AuthenticatedAPITestCase):
    def setUp(self):
        super().setUp()
        cache.clear()

    def tearDown(self):
        cache.clear()
        super().tearDown()

    def test_request_magic_link_sends_email_and_caches_tokens(self):
        url = reverse("authentication:request-magic-link")
        with patch("authentication.views.secrets.token_urlsafe", return_value="fixed-token"), patch(
            "authentication.views.random.randint",
            side_effect=[1, 2, 3, 4, 5, 6],
        ):
            response = self.client.post(url, {"email": "Student@example.com"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        body = response.json()
        self.assertTrue(body["success"])
        self.assertEqual(len(mail.outbox), 1)
        message = mail.outbox[0]
        self.assertIn("Magic Link: https://hub.test/auth/verify?token=fixed-token", message.body)
        self.assertIn("One-Time Code: 123456", message.body)

        self.assertEqual(cache.get("magic_token:fixed-token"), "student@example.com")
        self.assertEqual(cache.get("otp:student@example.com"), "123456")

    def test_request_magic_link_rejects_invalid_email(self):
        url = reverse("authentication:request-magic-link")
        response = self.client.post(url, {"email": "bad-email"})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.json())
        self.assertEqual(len(mail.outbox), 0)

    def test_verify_otp_issues_tokens_and_clears_cache(self):
        email = "learner@example.com"
        cache.set("otp:learner@example.com", "654321", timeout=600)

        url = reverse("authentication:verify-otp")
        response = self.client.post(url, {"email": email, "code": "654321"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        payload = response.json()
        self.assertIn("token", payload)
        self.assertIn("refresh_token", payload)
        self.assertIn("user", payload)
        self.assertIsNone(cache.get("otp:learner@example.com"))
        self.assertTrue(User.objects.filter(email=email).exists())

    def test_verify_otp_requires_matching_code(self):
        cache.set("otp:user@example.com", "111111", timeout=600)
        url = reverse("authentication:verify-otp")

        response = self.client.post(url, {"email": "user@example.com", "code": "222222"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(cache.get("otp:user@example.com"), "111111")

    def test_verify_magic_link_issues_tokens(self):
        cache.set("magic_token:abc123", "member@example.com", timeout=600)
        cache.set("otp:member@example.com", "999999", timeout=600)

        url = reverse("authentication:verify-magic-link")
        response = self.client.get(url, {"token": "abc123"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        payload = response.json()
        self.assertIn("token", payload)
        self.assertIn("refresh_token", payload)
        self.assertIsNone(cache.get("magic_token:abc123"))
        self.assertIsNone(cache.get("otp:member@example.com"))

    def test_verify_magic_link_handles_missing_token(self):
        url = reverse("authentication:verify-magic-link")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.json())

    def test_refresh_token_returns_new_access_token(self):
        user = self.create_student("refresh@example.com").user
        refresh = RefreshToken.for_user(user)

        url = reverse("authentication:refresh-token")
        response = self.client.post(url, {"refresh_token": str(refresh)})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        payload = response.json()
        self.assertIn("token", payload)
        self.assertIn("refresh_token", payload)

    def test_refresh_token_rejects_invalid_payload(self):
        url = reverse("authentication:refresh-token")
        response = self.client.post(url, {"refresh_token": "invalid"})

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn("error", response.json())

