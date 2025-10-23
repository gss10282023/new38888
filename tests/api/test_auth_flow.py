from unittest.mock import patch

from django.core.cache import cache
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase


class AuthenticationFlowTests(APITestCase):
    def setUp(self):
        super().setUp()
        cache.clear()

    def tearDown(self):
        cache.clear()
        super().tearDown()

    def test_magic_link_and_profile_update_flow(self):
        request_url = reverse("authentication:request-magic-link")
        verify_url = reverse("authentication:verify-otp")
        me_url = reverse("users:me")

        with patch("authentication.views.secrets.token_urlsafe", return_value="flow-token"), patch(
            "authentication.views.random.randint",
            side_effect=[0, 1, 2, 3, 4, 5],
        ):
            response = self.client.post(request_url, {"email": "flow@example.com"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.client.post(
            verify_url,
            {"email": "flow@example.com", "code": "012345"},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        payload = response.json()
        access_token = payload["token"]

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")
        response = self.client.get(me_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.client.patch(
            me_url,
            {
                "track": "Global",
                "profile": {
                    "firstName": "Flow",
                    "areasOfInterest": ["Synthetic Biology"],
                },
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["track"], "Global")

