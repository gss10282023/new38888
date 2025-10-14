from django.core import mail
from django.core.cache import cache
from django.urls import reverse
from django.test import override_settings
from rest_framework import status
from rest_framework.test import APITestCase

from users.models import User


@override_settings(
    EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
    CACHES={'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'}},
    DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
    FRONTEND_BASE_URL='https://frontend.example.com',
    MAGIC_LINK_EXPIRY_SECONDS=600,
)
class MagicLinkAuthenticationTests(APITestCase):
    def setUp(self):
        super().setUp()
        cache.clear()
        mail.outbox = []
        self.email = 'student@example.com'
        self.magic_link_url = reverse('authentication:request-magic-link')
        self.verify_otp_url = reverse('authentication:verify-otp')
        self.verify_magic_url = reverse('authentication:verify-magic-link')
        self.refresh_url = reverse('authentication:refresh-token')

    def test_request_magic_link_stores_tokens_and_sends_email(self):
        response = self.client.post(
            self.magic_link_url,
            {'email': self.email},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertTrue(cache.get(f'otp:{self.email}'))
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('One-Time Code', mail.outbox[0].body)

    def test_verify_otp_creates_user_and_returns_tokens(self):
        cache.set(f'otp:{self.email}', '123456', timeout=600)

        response = self.client.post(
            self.verify_otp_url,
            {'email': self.email, 'code': '123456'},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('token', response.data)
        self.assertIn('refresh_token', response.data)
        self.assertTrue(User.objects.filter(email=self.email).exists())
        self.assertIsNone(cache.get(f'otp:{self.email}'))

    def test_verify_magic_link_issues_tokens(self):
        token = 'testtoken'
        cache.set(f'magic_token:{token}', self.email, timeout=600)

        response = self.client.get(self.verify_magic_url, {'token': token})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('token', response.data)
        self.assertIn('refresh_token', response.data)
        self.assertIsNone(cache.get(f'magic_token:{token}'))

    def test_refresh_token_returns_new_access_token(self):
        cache.set(f'otp:{self.email}', '123456', timeout=600)
        verify_response = self.client.post(
            self.verify_otp_url,
            {'email': self.email, 'code': '123456'},
            format='json',
        )
        refresh_token = verify_response.data['refresh_token']

        response = self.client.post(
            self.refresh_url,
            {'refresh_token': refresh_token},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('token', response.data)
        self.assertEqual(response.data['refresh_token'], refresh_token)

# Create your tests here.
