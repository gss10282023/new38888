from datetime import date, timedelta
from io import BytesIO
from unittest.mock import patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from rest_framework import status

from PIL import Image

from events.models import Event, EventRegistration

from .base import AuthenticatedAPITestCase


def build_png_file(name: str = "event.png") -> SimpleUploadedFile:
    buffer = BytesIO()
    Image.new("RGB", (1, 1), color="white").save(buffer, format="PNG")
    buffer.seek(0)
    return SimpleUploadedFile(name, buffer.getvalue(), content_type="image/png")

class EventEndpointsTests(AuthenticatedAPITestCase):
    def setUp(self):
        super().setUp()
        self.admin = self.create_admin()
        self.student = self.create_student("attendee@example.com")

        self.event = Event.objects.create(
            title="Opening Ceremony",
            description="Welcome session",
            long_description="Detailed agenda",
            date=date.today() + timedelta(days=7),
            time="10:00",
            location="Sydney",
            type=Event.TYPE_IN_PERSON,
            register_link="https://events.example.com/register",
        )

    def test_list_events_supports_upcoming_filter(self):
        url = reverse("events:event-list")
        self.authenticate(self.student.user)

        response = self.client.get(url, {"upcoming": "true"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        payload = response.json()
        self.assertEqual(payload["count"], 1)

    def test_admin_can_create_event(self):
        url = reverse("events:event-list")
        payload = {
            "title": "Mentor Workshop",
            "description": "Mentor orientation",
            "longDescription": "Agenda and details",
            "date": (date.today() + timedelta(days=10)).isoformat(),
            "time": "14:00",
            "location": "Online",
            "type": Event.TYPE_VIRTUAL,
            "registerLink": "https://events.example.com/mentor",
        }

        self.authenticate(self.student.user)
        response = self.client.post(url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.authenticate(self.admin.user)
        response = self.client.post(url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        body = response.json()
        self.assertEqual(body["title"], "Mentor Workshop")

    def test_register_for_event(self):
        url = reverse("events:event-register", kwargs={"pk": self.event.pk})
        self.authenticate(self.student.user)

        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(
            EventRegistration.objects.filter(event=self.event, user=self.student.user).exists()
        )

        # Second registration should be rejected
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_event_cover(self):
        url = reverse("events:event-update-cover", kwargs={"pk": self.event.pk})
        payload = {"coverImage": build_png_file()}

        self.authenticate(self.admin.user)
        with patch("events.views.default_storage") as storage:
            storage.save.return_value = "events/covers/event.png"
            storage.url.return_value = "https://cdn.example.com/events/covers/event.png"
            response = self.client.put(url, payload, format="multipart")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.event.refresh_from_db()
        self.assertTrue(self.event.cover_image.endswith("event.png"))
