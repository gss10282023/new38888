from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from users.models import User, UserProfile


class UserAPITestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="user@example.com",
            username="user@example.com",
            password="testpass123",
        )
        UserProfile.objects.create(
            user=self.user,
            first_name="Test",
            last_name="User",
            areas_of_interest=["Biotech"],
        )
        self.client.force_authenticate(user=self.user)
        self.url = reverse("users:me")

    def test_get_current_user_returns_profile_information(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["email"], self.user.email)
        self.assertEqual(response.data["profile"]["firstName"], "Test")
        self.assertEqual(response.data["profile"]["areasOfInterest"], ["Biotech"])

    def test_update_profile_updates_track_and_profile_fields(self):
        payload = {
            "track": "AUS-NSW",
            "profile": {
                "firstName": "Jane",
                "lastName": "Doe",
                "areasOfInterest": ["AI & Biotech"],
                "availability": "Weekends preferred",
            },
        }

        response = self.client.put(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["track"], "AUS-NSW")
        self.assertEqual(response.data["profile"]["firstName"], "Jane")
        self.assertEqual(
            response.data["profile"]["areasOfInterest"], ["AI & Biotech"]
        )

        self.user.refresh_from_db()
        self.assertEqual(self.user.track, "AUS-NSW")
        self.assertEqual(self.user.first_name, "Jane")
        self.assertEqual(self.user.profile.availability, "Weekends preferred")

    def test_update_profile_rejects_invalid_payload(self):
        response = self.client.put(
            self.url, {"profile": "invalid"}, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
